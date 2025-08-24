"""
VocalBorn Celery 應用配置

精簡的 Celery 應用配置，包含核心功能：
- Redis 訊息代理和結果儲存
- 任務路由和佇列設定
- 基本的重試和超時設定
"""

import logging
from celery import Celery
from celery.signals import worker_ready, worker_shutdown, worker_process_init, worker_process_shutdown, task_postrun
from src.shared.config.config import get_settings

logger = logging.getLogger(__name__)


def get_celery_settings():
    """獲取 Celery 配置設定"""
    settings = get_settings()
    
    return {
        # 訊息代理和結果儲存
        "broker_url": settings.redis_broker_url,
        "result_backend": settings.redis_backend_url,
        
        # 任務路由
        "task_routes": {
            "analyze_audio_task": {"queue": "ai_analysis"},
            "analyze_test_audio_task": {"queue": "ai_analysis"},
            "cleanup_expired_tasks": {"queue": "maintenance"},
            "health_check": {"queue": "health"},
        },
        
        # 佇列設定
        "task_default_queue": "ai_analysis",
        
        # 任務執行設定
        "task_acks_late": True,
        "task_reject_on_worker_lost": True,
        "task_time_limit": 1800,  # 30 分鐘
        "task_soft_time_limit": 1500,  # 25 分鐘
        
        # 重試設定
        "task_annotations": {
            "*": {
                "rate_limit": "10/m",
                "retry_policy": {
                    "max_retries": 3,
                    "interval_start": 60,
                    "interval_step": 60,
                    "interval_max": 300,
                }
            }
        },
        
        # 結果設定
        "result_expires": 3600,  # 1 小時
        "result_persistent": True,
        
        # Worker 設定（記憶體優化）
        "worker_max_tasks_per_child": 10,  # 處理10個任務後重啟 worker 進程（優化模型重複載入）

        # 監控和序列化
        "worker_send_task_events": True,
        "task_track_started": True,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "Asia/Taipei",
        "enable_utc": True,
        
        # 連線設定
        "broker_connection_retry": True,
        "broker_connection_retry_on_startup": True,
        "broker_connection_max_retries": 10,
    }


def create_celery_app():
    """建立並配置 Celery 應用實例"""
    celery_app = Celery("vocalborn_tasks")
    celery_app.config_from_object(get_celery_settings())
    celery_app.autodiscover_tasks(["celery_app.tasks"])
    return celery_app


# 建立全域 Celery 應用實例
app = create_celery_app()


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Worker 就緒事件處理器"""
    logger.info(f"Celery worker {sender.hostname} 已準備就緒")


@worker_process_init.connect
def worker_process_init_handler(sender=None, **kwargs):
    """Worker 進程初始化事件處理器 - 在每個 worker 子進程中執行"""
    import os
    process_id = os.getpid()
    logger.info(f"Worker 進程 {process_id} 初始化中，開始預載入模型")
    
    # 在每個 worker 子進程中預載入常用模型
    try:
        from celery_app.services.model_manager import preload_common_models
        preload_common_models()
        logger.info(f"Worker 進程 {process_id} 模型預載入完成")
    except Exception as e:
        logger.warning(f"Worker 進程 {process_id} 模型預載入失敗: {e}")


@worker_process_shutdown.connect
def worker_process_shutdown_handler(sender=None, **kwargs):
    """Worker 進程關閉事件處理器 - 在每個 worker 子進程中執行"""
    import os
    process_id = os.getpid()
    logger.info(f"Worker 進程 {process_id} 正在關閉，清理模型")
    
    # 清理當前進程的所有模型以釋放記憶體
    try:
        from celery_app.services.model_manager import cleanup_models
        cleanup_models()
        logger.info(f"Worker 進程 {process_id} 模型清理完成")
    except Exception as e:
        logger.warning(f"Worker 進程 {process_id} 模型清理失敗: {e}")


@worker_shutdown.connect  
def worker_shutdown_handler(sender=None, **kwargs):
    """Worker 關閉事件處理器"""
    logger.info(f"Celery worker {sender.hostname} 正在關閉")
    
    # 清理所有模型以釋放記憶體
    try:
        from celery_app.services.model_manager import cleanup_models
        cleanup_models()
        logger.info("模型清理完成")
    except Exception as e:
        logger.warning(f"模型清理失敗: {e}")
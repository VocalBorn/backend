"""
VocalBorn Celery 應用配置模組

這個模組實作 Celery 應用的核心配置，包括：
- Redis 訊息代理和結果儲存配置
- 任務路由和佇列設定
- 重試機制和超時設定
- 日誌配置
- 監控和錯誤處理
"""

import logging
from typing import Dict, Any, Optional, Union
from celery import Celery
from celery.signals import setup_logging, worker_ready, worker_shutdown
from src.shared.config.config import get_settings

# 載入環境變數
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

# 設定日誌記錄器
logger = logging.getLogger(__name__)


class CeleryConfig:
    """Celery 配置類別"""
    
    def __init__(self):
        """初始化 Celery 配置"""
        settings = get_settings()
        self.redis_host = settings.REDIS_HOST
        self.redis_port = settings.REDIS_PORT
        self.redis_db_broker = settings.REDIS_DB_BROKER
        self.redis_db_backend = settings.REDIS_DB_BACKEND
        self.redis_password = settings.REDIS_PASSWORD
        
        # 使用 settings 中的屬性直接獲取 URL
        self.broker_url = settings.redis_broker_url
        self.result_backend = settings.redis_backend_url
    
    def _build_redis_url(self, db: int) -> str:
        """建構 Redis 連線 URL
        
        Args:
            db: Redis 資料庫編號
            
        Returns:
            Redis 連線 URL
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{db}"
    
    def get_celery_settings(self) -> Dict[str, Any]:
        """獲取 Celery 配置設定
        
        Returns:
            Celery 配置字典
        """
        return {
            # 訊息代理和結果儲存
            "broker_url": self.broker_url,
            "result_backend": self.result_backend,
            
            # 佇列配置
            "task_routes": {
                "src.tasks.celery_tasks.analyze_audio_task": {"queue": "ai_analysis"},
                "src.tasks.celery_tasks.cleanup_expired_tasks": {"queue": "maintenance"},
                "src.tasks.celery_tasks.health_check": {"queue": "health"},
            },
            
            # 任務佇列定義（Redis 使用簡單字串即可）
            "task_queues": {
                "ai_analysis": {
                    "routing_key": "ai_analysis",
                },
                "maintenance": {
                    "routing_key": "maintenance", 
                },
                "health": {
                    "routing_key": "health",
                },
            },
            
            # 預設佇列設定
            "task_default_queue": "ai_analysis",
            "task_default_exchange": "tasks",
            "task_default_exchange_type": "direct",
            "task_default_routing_key": "ai_analysis",
            
            # 任務執行設定
            "task_acks_late": True,  # 任務完成後才確認，確保可靠性
            "task_reject_on_worker_lost": True,  # Worker 停止時拒絕任務
            "task_time_limit": 1800,  # 任務硬超時：30 分鐘
            "task_soft_time_limit": 1500,  # 任務軟超時：25 分鐘
            
            # 重試設定
            "task_annotations": {
                "*": {
                    "rate_limit": "10/m",  # 每分鐘最多 10 個任務
                    "retry_policy": {
                        "max_retries": 3,
                        "interval_start": 60,  # 首次重試延遲 60 秒
                        "interval_step": 60,   # 每次重試增加 60 秒
                        "interval_max": 300,   # 最大重試延遲 5 分鐘
                    }
                }
            },
            
            # 結果設定
            "result_expires": 3600,  # 結果過期時間：1 小時
            "result_persistent": True,  # 持久化結果
            "result_compression": "gzip",  # 結果壓縮
            
            # Worker 設定
            "worker_prefetch_multiplier": 1,  # 每次只預取一個任務，確保負載均衡
            "worker_max_tasks_per_child": 1000,  # Worker 處理 1000 個任務後重啟，防止記憶體洩漏
            "worker_disable_rate_limits": False,  # 啟用速率限制
            
            # 監控和日誌
            "worker_send_task_events": True,  # 傳送任務事件用於監控
            "task_send_sent_event": True,  # 傳送任務提交事件
            "task_track_started": True,  # 追蹤任務開始狀態
            
            # 序列化設定
            "task_serializer": "json",
            "result_serializer": "json",
            "accept_content": ["json"],  # 只接受 JSON 格式，提高安全性
            "timezone": "Asia/Taipei",
            "enable_utc": True,
            
            # 連線設定
            "broker_connection_retry": True,
            "broker_connection_retry_on_startup": True,
            "broker_connection_max_retries": 10,
        }


def create_celery_app() -> Celery:
    """建立並配置 Celery 應用實例
    
    Returns:
        配置完成的 Celery 應用實例
    """
    # 建立 Celery 應用
    celery_app = Celery("vocalborn_tasks")
    
    # 載入配置
    config = CeleryConfig()
    celery_app.config_from_object(config.get_celery_settings())
    
    # 自動探索任務模組
    celery_app.autodiscover_tasks([
        "src.tasks.celery_tasks",
    ])
    
    return celery_app


def setup_celery_logging(loglevel: Optional[Union[str, int]] = None, logfile: Optional[str] = None) -> None:
    """設定 Celery 日誌配置
    
    Args:
        loglevel: 日誌等級（字串或數值），預設為 INFO
        logfile: 日誌檔案路徑，預設輸出到控制台
    """
    # 處理不同類型的 loglevel 輸入
    if loglevel is None:
        settings = get_settings()
        log_level_str = settings.CELERY_LOG_LEVEL
        log_level_num = getattr(logging, log_level_str.upper())
    elif isinstance(loglevel, str):
        log_level_num = getattr(logging, loglevel.upper())
    elif isinstance(loglevel, int):
        log_level_num = loglevel
    else:
        # 預設使用 INFO
        log_level_num = logging.INFO
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(processName)s] %(message)s"
    
    # 設定根日誌記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_num)
    
    # 移除預設處理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 建立新的處理器
    if logfile:
        handler = logging.FileHandler(logfile)
    else:
        handler = logging.StreamHandler()
    
    # 設定格式器
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # 設定特定記錄器的等級
    logging.getLogger("celery").setLevel(log_level_num)
    logging.getLogger("src.tasks").setLevel(log_level_num)


# 建立全域 Celery 應用實例
app = create_celery_app()


@setup_logging.connect
def setup_celery_logging_signal(loglevel=None, logfile=None, format=None, colorize=None, **kwargs):
    """Celery 日誌設定信號處理器
    
    Args:
        loglevel: 日誌等級
        logfile: 日誌檔案
        format: 日誌格式（未使用）
        colorize: 是否彩色輸出（未使用）
        **kwargs: 其他參數（未使用）
    """
    setup_celery_logging(loglevel, logfile)


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Worker 就緒事件處理器
    
    Args:
        sender: 傳送者
        **kwargs: 其他參數（未使用）
    """
    logger.info(f"Celery worker {sender.hostname} 已準備就緒")
    
    # 執行健康檢查
    try:
        from .celery_tasks import health_check
        health_check.apply_async(queue="health")
        logger.info("已提交健康檢查任務")
    except Exception as exc:
        logger.error(f"提交健康檢查任務失敗: {exc}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Worker 關閉事件處理器
    
    Args:
        sender: 傳送者
        **kwargs: 其他參數（未使用）
    """
    logger.info(f"Celery worker {sender.hostname} 正在關閉")


def get_celery_app() -> Celery:
    """獲取 Celery 應用實例
    
    Returns:
        Celery 應用實例
    """
    return app


# 監控相關功能
class CeleryMonitor:
    """Celery 監控類別"""
    
    def __init__(self, celery_app: Celery):
        """初始化監控器
        
        Args:
            celery_app: Celery 應用實例
        """
        self.celery_app = celery_app
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """獲取 Worker 統計資訊
        
        Returns:
            Worker 統計資訊
        """
        try:
            inspect = self.celery_app.control.inspect()
            return {
                "active": inspect.active(),
                "scheduled": inspect.scheduled(),
                "reserved": inspect.reserved(),
                "stats": inspect.stats(),
            }
        except Exception as exc:
            logger.error(f"獲取 Worker 統計資訊失敗: {exc}")
            return {}
    
    def get_queue_length(self, queue_name: str = "ai_analysis") -> int:
        """獲取佇列長度（Redis 實作）
        
        Args:
            queue_name: 佇列名稱
            
        Returns:
            佇列中的任務數量
        """
        try:
            # 對於 Redis，我們使用 Celery 的 inspect 功能
            inspect = self.celery_app.control.inspect()
            
            # 獲取所有 worker 的保留任務和活躍任務
            active_tasks = inspect.active() or {}
            reserved_tasks = inspect.reserved() or {}
            scheduled_tasks = inspect.scheduled() or {}
            
            total_count = 0
            
            # 計算指定佇列的任務數量
            for worker_name in active_tasks:
                if worker_name in active_tasks:
                    for task in active_tasks[worker_name]:
                        if task.get('delivery_info', {}).get('routing_key') == queue_name:
                            total_count += 1
                            
                if worker_name in reserved_tasks:
                    for task in reserved_tasks[worker_name]:
                        if task.get('delivery_info', {}).get('routing_key') == queue_name:
                            total_count += 1
                            
                if worker_name in scheduled_tasks:
                    for task in scheduled_tasks[worker_name]:
                        if task.get('request', {}).get('delivery_info', {}).get('routing_key') == queue_name:
                            total_count += 1
            
            return total_count
        except Exception as exc:
            logger.warning(f"無法獲取佇列 {queue_name} 長度: {exc}")
            return -1
    
    def purge_queue(self, queue_name: str) -> int:
        """清空指定佇列（Redis 環境中實作有限）
        
        Args:
            queue_name: 佇列名稱
            
        Returns:
            清除的任務數量
        """
        try:
            # Redis 環境下的佇列清理比較複雜，暫時返回 0
            logger.warning(f"Redis 環境下暫不支援直接清空佇列 {queue_name}")
            return 0
        except Exception as exc:
            logger.error(f"清空佇列 {queue_name} 失敗: {exc}")
            return 0


# 建立全域監控器實例
monitor = CeleryMonitor(app)


if __name__ == "__main__":
    # 用於測試配置
    config = CeleryConfig()
    print("Celery 配置:")
    for key, value in config.get_celery_settings().items():
        print(f"  {key}: {value}")
    
    print(f"\n訊息代理 URL: {config.broker_url}")
    print(f"結果儲存 URL: {config.result_backend}")

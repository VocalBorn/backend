"""Celery 任務中的資料庫操作工具模組

提供 Celery 任務中常用的資料庫操作函數，統一處理資料庫連線和錯誤處理。
遵循 Celery 最佳實踐：
- 避免在 Celery 任務中直接使用同步資料庫連線
- 為每個資料庫操作創建新的連線會話
- 統一錯誤處理和日誌記錄
"""

import logging
import asyncio

from src.shared.database.database import get_session
from src.ai_analysis.services.task_management_service import (
    save_analysis_result_by_celery_id,
    update_task_status_by_celery_id
)
from src.ai_analysis.models import TaskStatus


logger = logging.getLogger(__name__)


def update_task_status_sync(celery_task_id: str, status: TaskStatus) -> None:
    """同步更新任務狀態到資料庫
    
    此函數專為 Celery 任務設計，建立獨立的資料庫連線會話。
    遵循 Celery 最佳實踐，避免跨進程共享資料庫連線。
    
    Args:
        celery_task_id: Celery 任務 ID
        status: 任務狀態
        
    Raises:
        Exception: 資料庫操作失敗時
    """
    try:
        db_session = next(get_session())
        try:
            # 使用新的事件循環執行非同步函數
            asyncio.run(update_task_status_by_celery_id(
                celery_task_id=celery_task_id,
                status=status,
                db_session=db_session
            ))
            logger.info(f"成功更新任務狀態: {celery_task_id} -> {status}")
        finally:
            db_session.close()
    except Exception as e:
        logger.error(f"更新任務狀態時發生錯誤: {e}")
        raise


def save_analysis_result_sync(
    celery_task_id: str,
    analysis_result: dict,
    analysis_model_version: str,
    processing_time_seconds: float
) -> None:
    """同步儲存分析結果到資料庫
    
    此函數專為 Celery 任務設計，建立獨立的資料庫連線會話。
    
    Args:
        celery_task_id: Celery 任務 ID
        analysis_result: 分析結果資料
        analysis_model_version: 分析模型版本
        processing_time_seconds: 處理時間（秒）
        
    Raises:
        Exception: 資料庫操作失敗時
    """
    try:
        db_session = next(get_session())
        try:
            asyncio.run(save_analysis_result_by_celery_id(
                celery_task_id=celery_task_id,
                analysis_result=analysis_result,
                analysis_model_version=analysis_model_version,
                processing_time_seconds=processing_time_seconds,
                db_session=db_session
            ))
            logger.info(f"成功儲存分析結果到資料庫: celery_id={celery_task_id}")
        finally:
            db_session.close()
    except Exception as e:
        logger.error(f"儲存分析結果到資料庫失敗: {e}")
        raise


def safe_update_task_status(celery_task_id: str, status: TaskStatus) -> None:
    """安全地更新任務狀態（不拋出異常）
    
    這個函數會捕獲所有異常，適合在異常處理區塊中使用。
    遵循 Celery 錯誤處理最佳實踐，避免在錯誤處理中再次拋出異常。
    
    Args:
        celery_task_id: Celery 任務 ID
        status: 任務狀態
    """
    try:
        update_task_status_sync(celery_task_id, status)
    except Exception as e:
        logger.error(f"更新任務狀態失敗（安全模式）: {e}")


__all__ = [
    "update_task_status_sync",
    "save_analysis_result_sync", 
    "safe_update_task_status"
]
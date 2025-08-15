"""
任務共用工具函數
"""

import logging
from celery import current_task

logger = logging.getLogger(__name__)


def update_progress(step: str, progress: int, **kwargs):
    """統一的進度更新函數"""
    current_task.update_state(
        state='PROGRESS',
        meta={
            'current_step': step,
            'progress': progress,
            **kwargs
        }
    )


def log_task_start(task_name: str, task_id: str, **kwargs):
    """記錄任務開始"""
    logger.info(f"開始執行 {task_name} 任務 {task_id}")
    if kwargs:
        logger.info(f"任務參數: {kwargs}")


def log_task_complete(task_name: str, task_id: str, result=None):
    """記錄任務完成"""
    logger.info(f"{task_name} 任務 {task_id} 執行完成")
    if result:
        logger.info(f"任務結果: {result}")


def log_task_error(task_name: str, task_id: str, error: Exception):
    """記錄任務錯誤"""
    logger.error(f"{task_name} 任務 {task_id} 執行失敗: {str(error)}", exc_info=True)
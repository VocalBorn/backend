"""Celery 服務模組

提供 AI 分析、檔案處理、任務管理等相關服務功能。
"""

from .analysis_audio.audio_analysis_service import compute_scores_and_feedback
from .file_utils import download_audio_file_to_temp, temporary_audio_files, FileProcessingError
from .task_utils import (
    get_db_session,
    update_task_status,
    create_analysis_result,
    find_ai_task_by_celery_id,
    TaskManagementError
)

__all__ = [
    # 分析服務
    "compute_scores_and_feedback",
    
    # 檔案處理服務
    "download_audio_file_to_temp",
    "temporary_audio_files", 
    "FileProcessingError",
    
    # 任務管理服務
    "get_db_session",
    "update_task_status",
    "create_analysis_result",
    "find_ai_task_by_celery_id",
    "TaskManagementError"
]
"""AI 音訊分析任務模組

處理用戶練習錄音與範例音檔的 AI 分析任務，包含完整的錯誤處理和資料庫操作。
"""

import logging
import time
import uuid
from typing import Optional

from celery import Task

from celery_app.app import app
from celery_app.services.file_utils import FileProcessingError
from celery_app.services.analysis_audio.audio_task_service import (
    AudioTaskServiceError,
    download_audio_files,
    perform_audio_analysis,
    create_analysis_summary
)
from src.ai_analysis.models import TaskStatus
from celery_app.services.db_operations import (
    update_task_status_sync,
    save_analysis_result_sync,
    safe_update_task_status
)


# 設定日誌
logger = logging.getLogger(__name__)


class AudioAnalysisError(Exception):
    """音訊分析任務自定義異常"""
    pass


class AudioAnalysisTask(Task):
    """音訊分析任務類別
    
    繼承 Celery Task 以提供更好的錯誤處理和任務狀態管理
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗時的處理"""
        logger.error(f"音訊分析任務失敗: {task_id}, 異常: {exc}")
        
        # 更新任務狀態為失敗
        safe_update_task_status(task_id, TaskStatus.FAILURE)
    
    def on_success(self, retval, task_id, args, kwargs):
        """任務成功時的處理"""
        logger.info(f"音訊分析任務成功完成: {task_id}")
        # 更新任務狀態為成功
        safe_update_task_status(task_id, TaskStatus.SUCCESS)


@app.task(
    bind=True,
    base=AudioAnalysisTask,
    name="analyze_audio_task",
    queue="ai_analysis",
    retry_policy={
        "max_retries": 3,
        "interval_start": 60,
        "interval_step": 60,
        "interval_max": 300,
    }
)
def analyze_audio_task(
    self,
    practice_record_id: str,
    sentence_id: str,
    user_audio_path: str,
    example_audio_path: str,
    analysis_params: Optional[dict] = None
) -> dict:
    """AI 音訊分析任務
    
    分析用戶練習錄音與範例音檔，產生評分和回饋建議。
    
    Args:
        practice_record_id: 練習記錄 ID
        sentence_id: 句子 ID
        user_audio_path: 用戶練習錄音的儲存路徑
        example_audio_path: 範例音檔的儲存路徑
        analysis_params: 分析參數（目前未使用，預留擴展）
    
    Returns:
        dict: 分析結果摘要
        
    Raises:
        AudioAnalysisError: 音訊分析相關錯誤
        ValueError: 參數驗證錯誤
        Exception: 其他未預期錯誤
    """
    start_time = time.time()
    task_id = None
    
    try:
        # 參數驗證
        if not practice_record_id or not sentence_id:
            raise ValueError("practice_record_id 和 sentence_id 不能為空")
        
        if not user_audio_path or not example_audio_path:
            raise ValueError("user_audio_path 和 example_audio_path 不能為空")
        
        logger.info(f"開始 AI 音訊分析任務: practice_record={practice_record_id}, sentence={sentence_id}")
        logger.info(f"音檔路徑 - 用戶: {user_audio_path}, 範例: {example_audio_path}")
        
        # 1. 下載音檔到暫存檔案
        user_temp_path, example_temp_path = download_audio_files(user_audio_path, example_audio_path)
        
        # 2. 執行 AI 分析
        analysis_result = perform_audio_analysis(example_temp_path, user_temp_path)
        
        # 3. 計算處理時間
        processing_time = time.time() - start_time
        
        # 4. 儲存分析結果到資料庫
        try:
            save_analysis_result_sync(
                celery_task_id=self.request.id,
                analysis_result=analysis_result,
                analysis_model_version="v1.1",  # 可以從設定檔或環境變數讀取
                processing_time_seconds=processing_time
            )
        except Exception as e:
            logger.error(f"儲存分析結果到資料庫失敗: {e}")
            # 即使儲存失敗，也要返回分析摘要
        
        # 5. 建立並返回分析摘要
        return create_analysis_summary(practice_record_id, sentence_id, analysis_result, processing_time)
        
    except (AudioAnalysisError, FileProcessingError, AudioTaskServiceError) as e:
        logger.error(f"音訊分析錯誤: {e}")
        # 更新任務狀態為失敗
        safe_update_task_status(self.request.id, TaskStatus.FAILURE)
        raise
        
    except ValueError as e:
        logger.error(f"參數驗證錯誤: {e}")
        # 更新任務狀態為失敗
        safe_update_task_status(self.request.id, TaskStatus.FAILURE)
        raise
        
    except Exception as e:
        logger.error(f"音訊分析任務發生未預期錯誤: {e}")
        # 更新任務狀態為失敗
        safe_update_task_status(self.request.id, TaskStatus.FAILURE)
        raise AudioAnalysisError(f"音訊分析過程發生錯誤: {e}")


__all__ = ["analyze_audio_task", "AudioAnalysisError"]
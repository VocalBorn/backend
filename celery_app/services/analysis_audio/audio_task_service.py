"""音訊分析任務服務模組

提供音訊分析任務所需的資料庫查詢和業務邏輯處理功能。
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class AudioTaskServiceError(Exception):
    """音訊任務服務自定義異常"""
    pass



def download_audio_files(user_audio_path: str, example_audio_path: str) -> Tuple[str, str]:
    """下載音檔到暫存檔案
    
    Args:
        user_audio_path: 用戶音檔在儲存服務中的路徑
        example_audio_path: 範例音檔在儲存服務中的路徑
        
    Returns:
        Tuple[str, str]: (用戶音檔本地暫存路徑, 範例音檔本地暫存路徑)
        
    Raises:
        AudioTaskServiceError: 當下載失敗時
    """
    from src.storage.audio_storage_service import get_practice_audio_storage_service, get_course_audio_storage_service
    from celery_app.services.file_utils import download_audio_file_to_temp
    
    logger.info("開始下載音檔到暫存檔案")
    
    try:
        # 初始化儲存服務
        practice_storage = get_practice_audio_storage_service()
        course_storage = get_course_audio_storage_service()
        
        # 下載音檔
        user_temp_path = download_audio_file_to_temp(practice_storage, user_audio_path)
        example_temp_path = download_audio_file_to_temp(course_storage, example_audio_path)
        
        logger.info("音檔下載完成")
        return user_temp_path, example_temp_path
        
    except Exception as e:
        logger.error(f"下載音檔時發生錯誤: {e}")
        raise AudioTaskServiceError(f"音檔下載失敗: {e}")


def perform_audio_analysis(example_audio_path: str, user_audio_path: str) -> dict:
    """執行 AI 音訊分析
    
    Args:
        example_audio_path: 範例音檔本地路徑
        user_audio_path: 用戶音檔本地路徑
        
    Returns:
        dict: 分析結果
        
    Raises:
        AudioTaskServiceError: 當分析失敗時
    """
    from celery_app.services.analysis_audio.audio_analysis_service import compute_scores_and_feedback
    from celery_app.services.file_utils import temporary_audio_files
    
    logger.info("開始執行 AI 音訊分析")
    
    try:
        # 使用上下文管理器確保檔案清理
        with temporary_audio_files(user_audio_path, example_audio_path):
            analysis_result = compute_scores_and_feedback(example_audio_path, user_audio_path)
            
        logger.info("AI 音訊分析完成")
        return analysis_result
        
    except Exception as e:
        logger.error(f"AI 音訊分析時發生錯誤: {e}")
        raise AudioTaskServiceError(f"AI 分析失敗: {e}")


def create_analysis_summary(
    practice_record_id: str, 
    sentence_id: str, 
    analysis_result: dict, 
    processing_time: float
) -> dict:
    """建立分析結果摘要
    
    Args:
        practice_record_id: 練習記錄 ID
        sentence_id: 句子 ID
        analysis_result: AI 分析結果
        processing_time: 處理時間（秒）
        
    Returns:
        dict: 分析結果摘要
    """
    summary = {
        "success": True,
        "practice_record_id": practice_record_id,
        "sentence_id": sentence_id,
        "processing_time": processing_time,
        "analysis_level": analysis_result.get("level"),
        "similarity_score": analysis_result.get("index", 0.0)
    }
    
    logger.info(f"分析摘要建立完成 - 處理時間: {processing_time:.2f} 秒")
    return summary


__all__ = [
    "AudioTaskServiceError",
    "download_audio_files", 
    "perform_audio_analysis",
    "create_analysis_summary"
]
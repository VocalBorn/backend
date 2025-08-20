"""音訊分析任務服務模組

提供音訊分析任務所需的資料庫查詢和業務邏輯處理功能。
"""

import logging
from typing import Tuple

from sqlmodel import Session, text
from src.shared.database.database import engine

logger = logging.getLogger(__name__)


class AudioTaskServiceError(Exception):
    """音訊任務服務自定義異常"""
    pass


def fetch_audio_paths(practice_record_id: str, sentence_id: str) -> Tuple[str, str]:
    """查詢練習記錄和句子的音檔路徑
    
    Args:
        practice_record_id: 練習記錄 ID
        sentence_id: 句子 ID
        
    Returns:
        Tuple[str, str]: (用戶音檔路徑, 範例音檔路徑)
        
    Raises:
        AudioTaskServiceError: 當查詢失敗或資料不存在時
    """
    logger.info(f"查詢音檔路徑 - practice_record: {practice_record_id}, sentence: {sentence_id}")
    
    try:
        with Session(engine) as session:
            # 查詢練習記錄的音檔路徑
            practice_result = session.exec(
                text("SELECT audio_path FROM practice_records WHERE practice_record_id = :id").params(id=practice_record_id)
            ).first()
            
            if not practice_result:
                raise AudioTaskServiceError(f"找不到練習記錄: {practice_record_id}")
            
            user_audio_path = practice_result[0]
            if not user_audio_path:
                raise AudioTaskServiceError(f"練習記錄缺少音檔路徑: {practice_record_id}")
            
            # 查詢句子的範例音檔路徑
            sentence_result = session.exec(
                text("SELECT example_audio_path FROM sentences WHERE sentence_id = :id").params(id=sentence_id)
            ).first()
            
            if not sentence_result:
                raise AudioTaskServiceError(f"找不到句子: {sentence_id}")
            
            example_audio_path = sentence_result[0]
            if not example_audio_path:
                raise AudioTaskServiceError(f"句子缺少範例音檔: {sentence_id}")
            
            logger.info(f"成功取得音檔路徑 - 用戶: {user_audio_path}, 範例: {example_audio_path}")
            return user_audio_path, example_audio_path
            
    except Exception as e:
        if isinstance(e, AudioTaskServiceError):
            raise
        logger.error(f"查詢音檔路徑時發生錯誤: {e}")
        raise AudioTaskServiceError(f"資料庫查詢失敗: {e}")


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
    from celery_app.services.analysis import compute_scores_and_feedback
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
    "fetch_audio_paths",
    "download_audio_files", 
    "perform_audio_analysis",
    "create_analysis_summary"
]
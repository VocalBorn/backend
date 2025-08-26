"""文字轉語音 Celery 任務模組

處理語句文字轉換為語音並儲存為範例音訊的非同步任務。
"""

import datetime
import logging
import os
import tempfile
import time
from typing import Optional

from celery import Task
from fastapi import UploadFile
from io import BytesIO

from celery_app.app import app
from celery_app.services.tts_service import sync_create_temporary_audio, TTSServiceError
from celery_app.services.db_operations import safe_update_task_status
from src.course.models import Sentence
from src.shared.database.database import get_sync_session
from src.storage.audio_storage_service import get_course_audio_storage_service

logger = logging.getLogger(__name__)


class TTSTaskError(Exception):
    """文字轉語音任務異常"""
    pass


class TextToSpeechTask(Task):
    """文字轉語音任務類別"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗時的處理"""
        logger.error(f"文字轉語音任務失敗: {task_id}, 異常: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """任務成功時的處理"""
        logger.info(f"文字轉語音任務成功完成: {task_id}")


@app.task(
    bind=True,
    base=TextToSpeechTask,
    name="generate_sentence_audio_task",
    queue="ai_analysis",
    retry_policy={
        "max_retries": 3,
        "interval_start": 30,
        "interval_step": 60,
        "interval_max": 300,
    }
)
def generate_sentence_audio_task(
    self,
    sentence_id: str,
    voice: str = "female",
    overwrite: bool = True
) -> dict:
    """為語句生成範例音訊的任務
    
    Args:
        sentence_id: 語句 ID
        voice: 語者選擇 ("female" 或 "male")
        overwrite: 是否覆蓋已存在的音訊檔案
        
    Returns:
        dict: 任務執行結果摘要
        
    Raises:
        TTSTaskError: 任務執行錯誤
    """
    start_time = time.time()
    temp_audio_path = None
    
    try:
        logger.info(f"開始文字轉語音任務: sentence_id={sentence_id}, voice={voice}")
        
        # 參數驗證
        if not sentence_id or not sentence_id.strip():
            raise TTSTaskError("sentence_id 不能為空")
        
        # 1. 查詢語句資料
        with get_sync_session() as session:
            sentence = session.get(Sentence, sentence_id)
            if not sentence:
                raise TTSTaskError(f"找不到語句: {sentence_id}")
            
            # 檢查是否已有音訊檔案且不覆蓋
            if sentence.example_audio_path and not overwrite:
                logger.info(f"語句已有範例音訊且未要求覆蓋: {sentence_id}")
                return {
                    "sentence_id": sentence_id,
                    "status": "skipped",
                    "message": "語句已有範例音訊",
                    "existing_audio_path": sentence.example_audio_path,
                    "processing_time": time.time() - start_time
                }
            
            # 取得語句內容和相關資訊
            text_content = sentence.content
            chapter_id = str(sentence.chapter_id)
            
            # 取得 situation_id（用作 course_id）
            chapter = session.get(sentence.chapter.__class__, sentence.chapter_id)
            if not chapter:
                raise TTSTaskError(f"找不到章節: {sentence.chapter_id}")
            
            situation_id = str(chapter.situation_id)
        
        # 2. 文字轉語音
        try:
            temp_audio_path = sync_create_temporary_audio(text_content, voice)
            logger.info(f"TTS 轉換完成: {temp_audio_path}")
        except TTSServiceError as e:
            raise TTSTaskError(f"文字轉語音失敗: {str(e)}")
        
        # 3. 上傳到儲存服務
        try:
            # 準備上傳檔案
            with open(temp_audio_path, "rb") as audio_file:
                file_content = audio_file.read()
            
            # 建立 UploadFile 類似物件
            upload_file = UploadFile(
                filename=f"{sentence_id}.mp3",
                file=BytesIO(file_content),
                size=len(file_content),
                headers={"content-type": "audio/mpeg"}
            )
            
            # 上傳檔案
            audio_storage_service = get_course_audio_storage_service()
            audio_path = audio_storage_service.upload_course_audio(
                file=upload_file,
                course_id=situation_id,
                chapter_id=chapter_id,
                sentence_id=sentence_id
            )
            
            logger.info(f"音訊檔案上傳成功: {audio_path}")
            
        except Exception as e:
            raise TTSTaskError(f"音訊檔案上傳失敗: {str(e)}")
        
        # 4. 更新資料庫
        try:
            with get_sync_session() as session:
                sentence = session.get(Sentence, sentence_id)
                if sentence:
                    sentence.example_audio_path = audio_path
                    sentence.example_audio_duration = None  # 未來可實作音訊時長偵測
                    sentence.example_file_size = len(file_content)
                    sentence.example_content_type = "audio/mpeg"
                    sentence.updated_at = datetime.datetime.now()
                    
                    session.add(sentence)
                    session.commit()
                    session.refresh(sentence)
                    
                    logger.info(f"語句音訊資訊更新完成: {sentence_id}")
        except Exception as e:
            logger.error(f"更新語句音訊資訊失敗: {e}")
            raise TTSTaskError(f"資料庫更新失敗: {str(e)}")
        
        # 5. 計算處理時間並返回結果
        processing_time = time.time() - start_time
        
        result = {
            "sentence_id": sentence_id,
            "status": "success",
            "message": "範例音訊生成成功",
            "audio_path": audio_path,
            "file_size": len(file_content),
            "content_type": "audio/mpeg",
            "voice": voice,
            "text_content": text_content[:100] + "..." if len(text_content) > 100 else text_content,
            "processing_time": processing_time
        }
        
        logger.info(f"文字轉語音任務完成: {result}")
        return result
        
    except TTSTaskError as e:
        logger.error(f"文字轉語音任務錯誤: {e}")
        raise
        
    except Exception as e:
        logger.error(f"文字轉語音任務發生未預期錯誤: {e}")
        raise TTSTaskError(f"任務執行過程發生錯誤: {str(e)}")
        
    finally:
        # 清理暫存檔案
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.debug(f"暫存檔案已清理: {temp_audio_path}")
            except Exception as e:
                logger.warning(f"暫存檔案清理失敗: {e}")


@app.task(
    bind=True,
    name="batch_generate_sentence_audio_task",
    queue="ai_analysis",
    retry_policy={
        "max_retries": 2,
        "interval_start": 60,
        "interval_step": 120,
        "interval_max": 600,
    }
)
def batch_generate_sentence_audio_task(
    self,
    sentence_ids: list[str],
    voice: str = "female",
    overwrite: bool = True
) -> dict:
    """批次為多個語句生成範例音訊的任務
    
    Args:
        sentence_ids: 語句 ID 列表
        voice: 語者選擇 ("female" 或 "male")
        overwrite: 是否覆蓋已存在的音訊檔案
        
    Returns:
        dict: 批次執行結果摘要
    """
    start_time = time.time()
    results = {
        "total": len(sentence_ids),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "details": [],
        "processing_time": 0
    }
    
    try:
        logger.info(f"開始批次文字轉語音任務: {len(sentence_ids)} 個語句")
        
        for sentence_id in sentence_ids:
            try:
                # 呼叫單一語句的任務
                result = generate_sentence_audio_task.apply(
                    args=[sentence_id, voice, overwrite],
                    ignore_result=False
                ).get()
                
                if result["status"] == "success":
                    results["success"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                
                results["details"].append(result)
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "sentence_id": sentence_id,
                    "status": "failed",
                    "error": str(e)
                })
                logger.error(f"語句 {sentence_id} 處理失敗: {e}")
        
        results["processing_time"] = time.time() - start_time
        logger.info(f"批次文字轉語音任務完成: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"批次文字轉語音任務發生錯誤: {e}")
        results["processing_time"] = time.time() - start_time
        results["error"] = str(e)
        return results


__all__ = ["generate_sentence_audio_task", "batch_generate_sentence_audio_task", "TTSTaskError"]
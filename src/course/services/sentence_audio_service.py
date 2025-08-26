from datetime import timedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from src.course.models import Sentence, Chapter
from src.storage.audio_storage_service import get_course_audio_storage_service
from celery_app.tasks.text_to_speech import generate_sentence_audio_task, batch_generate_sentence_audio_task


async def generate_sentence_example_audio(
    sentence_id: str,
    session: Session,
    voice: str = "female",
    overwrite: bool = True
) -> dict:
    """為語句生成範例音訊
    
    Args:
        sentence_id: 語句 ID
        voice: 語者選擇 ("female" 或 "male")
        overwrite: 是否覆蓋已存在的音訊檔案
        session: 資料庫會話
        
    Returns:
        dict: 任務執行結果
        
    Raises:
        HTTPException: 當語句不存在或任務啟動失敗時
    """
    # 確認語句存在
    sentence = session.get(Sentence, sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    # 檢查是否已有音訊檔案且不覆蓋
    if sentence.example_audio_path and not overwrite:
        return {
            "sentence_id": sentence_id,
            "status": "exists",
            "message": "語句已有範例音訊，如需重新生成請設定 overwrite=true",
            "existing_audio_path": sentence.example_audio_path
        }
    
    try:
        # 異步啟動任務
        task = generate_sentence_audio_task.delay(
            sentence_id=sentence_id,
            voice=voice,
            overwrite=overwrite
        )
        
        return {
            "sentence_id": sentence_id,
            "task_id": task.id,
            "status": "started",
            "message": "範例音訊生成任務已啟動",
            "voice": voice,
            "text_content": sentence.content[:100] + "..." if len(sentence.content) > 100 else sentence.content
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"啟動音訊生成任務失敗: {str(e)}"
        )


async def batch_generate_sentences_example_audio(
    chapter_id: str,
    session: Session,
    voice: str = "female",
    overwrite: bool = True
) -> dict:
    """為章節中的所有語句批次生成範例音訊
    
    Args:
        chapter_id: 章節 ID
        voice: 語者選擇 ("female" 或 "male")
        overwrite: 是否覆蓋已存在的音訊檔案
        session: 資料庫會話
        
    Returns:
        dict: 批次任務執行結果
        
    Raises:
        HTTPException: 當章節不存在或任務啟動失敗時
    """
    # 確認章節存在
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # 查詢章節中的所有語句
    query = select(Sentence).where(Sentence.chapter_id == chapter_id)
    sentences = session.exec(query).all()
    
    if not sentences:
        return {
            "chapter_id": chapter_id,
            "status": "empty",
            "message": "章節中沒有語句",
            "total": 0
        }
    
    # 過濾需要生成音訊的語句
    sentence_ids = []
    if overwrite:
        sentence_ids = [str(sentence.sentence_id) for sentence in sentences]
    else:
        sentence_ids = [
            str(sentence.sentence_id) 
            for sentence in sentences 
            if not sentence.example_audio_path
        ]
    
    if not sentence_ids:
        return {
            "chapter_id": chapter_id,
            "status": "all_exist",
            "message": "所有語句已有範例音訊，如需重新生成請設定 overwrite=true",
            "total": len(sentences),
            "existing": len(sentences)
        }
    
    try:
        # 異步啟動批次任務
        task = batch_generate_sentence_audio_task.delay(
            sentence_ids=sentence_ids,
            voice=voice,
            overwrite=overwrite
        )
        
        return {
            "chapter_id": chapter_id,
            "task_id": task.id,
            "status": "started",
            "message": "批次範例音訊生成任務已啟動",
            "total": len(sentences),
            "to_generate": len(sentence_ids),
            "voice": voice
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"啟動批次音訊生成任務失敗: {str(e)}"
        )


async def delete_sentence_example_audio(
    sentence_id: str,
    session: Session
) -> dict:
    """刪除語句範例音訊
    
    Args:
        sentence_id: 語句 ID
        session: 資料庫會話
        
    Returns:
        dict: 刪除操作結果
        
    Raises:
        HTTPException: 當語句不存在或刪除失敗時
    """
    # 確認語句存在
    sentence = session.get(Sentence, sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    # 檢查是否有範例音訊檔案
    if not sentence.example_audio_path:
        return {
            "sentence_id": sentence_id,
            "status": "no_audio",
            "message": "語句沒有範例音訊檔案"
        }
    
    try:
        # 獲取儲存服務並刪除檔案
        storage_service = get_course_audio_storage_service()
        storage_service.delete_file(sentence.example_audio_path)
        
        # 更新資料庫，清除音訊檔案相關欄位
        sentence.example_audio_path = None
        sentence.example_audio_duration = None
        sentence.example_file_size = None
        sentence.example_content_type = None
        
        session.add(sentence)
        session.commit()
        session.refresh(sentence)
        
        return {
            "sentence_id": sentence_id,
            "status": "deleted",
            "message": "範例音訊已成功刪除"
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"刪除範例音訊失敗: {str(e)}"
        )


async def get_sentence_audio_presigned_url(
    sentence_id: str,
    session: Session,
    expires_in: timedelta = timedelta(minutes=15)
) -> dict:
    """為語句範例音訊生成臨時聆聽網址
    
    Args:
        sentence_id: 語句 ID
        session: 資料庫會話
        expires_in: URL 過期時間，預設 15 分鐘
        
    Returns:
        dict: 包含預簽署 URL 和相關資訊的結果
        
    Raises:
        HTTPException: 當語句不存在或 URL 生成失敗時
    """
    # 確認語句存在
    sentence = session.get(Sentence, sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    # 檢查是否有範例音訊檔案
    if not sentence.example_audio_path:
        return {
            "sentence_id": sentence_id,
            "status": "no_audio",
            "message": "語句沒有範例音訊檔案",
            "url": None
        }
    
    try:
        # 獲取儲存服務並生成預簽署 URL
        storage_service = get_course_audio_storage_service()
        presigned_url = storage_service.get_presigned_url(
            object_name=sentence.example_audio_path,
            expires_in=expires_in
        )
        
        return {
            "sentence_id": sentence_id,
            "status": "success",
            "message": "臨時聆聽網址已生成",
            "url": presigned_url,
            "expires_in_minutes": expires_in.total_seconds() / 60,
            "audio_info": {
                "duration": sentence.example_audio_duration,
                "file_size": sentence.example_file_size,
                "content_type": sentence.example_content_type
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成音訊聆聽網址失敗: {str(e)}"
        )
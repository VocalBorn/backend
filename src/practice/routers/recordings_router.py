"""
練習錄音管理路由
處理練習會話中錄音檔案的上傳、查詢和刪除
"""

from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlmodel import Session, select, and_
import uuid

from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User
from src.practice.models import PracticeRecord, PracticeSession
from src.course.models import Sentence

from src.practice.schemas import (
    AudioUploadResponse,
    RecordingResponse,
    RecordingsListResponse,
    RecordUpdateRequest,
    PracticeRecordResponse,
    PracticeRecordListResponse
)

from src.practice.services.practice_service import (
    get_practice_session,
    get_practice_record_by_session_and_sentence,
    update_practice_audio_info,
    get_practice_session_records
)

from src.storage.practice_recording_service import practice_recording_service
from datetime import datetime, timedelta

router = APIRouter(
    prefix='/practice/sessions',
    tags=['practice-recordings']
)

def _create_recording_response(practice_record, user_id: str) -> RecordingResponse:
    """建立錄音回應，包含播放 URL（如果有錄音）"""
    stream_url = None
    stream_expires_at = None
    
    # 如果有錄音檔案，生成播放 URL
    if practice_record.audio_path:
        try:
            stream_url = practice_recording_service.get_practice_recording_url(
                str(practice_record.practice_record_id),
                user_id,
                expires_minutes=30
            )
            stream_expires_at = datetime.now() + timedelta(minutes=30)
        except Exception as e:
            # 生成 URL 失敗時記錄錯誤但不中斷流程
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"生成播放 URL 失敗: {str(e)}")
    
    return RecordingResponse(
        sentence_id=practice_record.sentence_id,
        audio_path=practice_record.audio_path,
        audio_duration=practice_record.audio_duration,
        file_size=practice_record.file_size,
        content_type=practice_record.content_type,
        recorded_at=practice_record.recorded_at,
        stream_url=stream_url,
        stream_expires_at=stream_expires_at
    )

@router.put(
    "/{practice_session_id}/recordings/{sentence_id}",
    response_model=AudioUploadResponse,
    summary="上傳/更新練習錄音",
    description="""
    需提供練習會話ID、句子ID及錄音檔案。如果錄音已存在則更新，不存在則建立（符合 PUT 冪等性原則）。
    支援的檔案格式：MP3、WAV、M4A、OGG、WebM、FLAC、AAC
    檔案大小限制：50MB
    
    ⚠️ 重要：確保一個練習會話裡面一句只會有一個錄音檔案。
    """
)
async def upload_or_update_recording(
    practice_session_id: uuid.UUID,
    sentence_id: uuid.UUID,
    audio_file: Annotated[UploadFile, File(description="音訊檔案")],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """上傳或更新練習錄音"""
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(
        practice_session_id, current_user.user_id, session
    )
    
    # 通過練習會話ID和句子ID獲取練習記錄
    practice_record = await get_practice_record_by_session_and_sentence(
        practice_session_id, sentence_id, current_user.user_id, session
    )
    
    # 如果已存在錄音檔案，需要先刪除舊檔案（MinIO 中）
    if practice_record.audio_path:
        try:
            # 從 audio_path 中提取檔案名來刪除
            # 這裡可以根據需要實現刪除舊檔案的邏輯
            pass
        except Exception as e:
            # 記錄警告但不中斷流程，因為可能是檔案已不存在
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"刪除舊錄音檔案失敗: {str(e)}")
    
    # 上傳新檔案
    upload_result = practice_recording_service.upload_practice_recording(
        user_id=str(current_user.user_id),
        practice_record_id=str(practice_record.practice_record_id),
        audio_file=audio_file,
        db_session=session
    )
    
    # 更新練習記錄的音訊資訊
    await update_practice_audio_info(
        practice_record_id=practice_record.practice_record_id,
        audio_path=upload_result["object_name"],
        audio_duration=None,  # TODO: 從音訊檔案中提取時長
        file_size=upload_result["file_size"],
        content_type=upload_result["content_type"],
        session=session
    )
    
    return AudioUploadResponse(
        recording_id=upload_result["recording_id"],
        object_name=upload_result["object_name"],
        file_size=upload_result["file_size"],
        content_type=upload_result["content_type"],
        status=upload_result["status"]
    )


@router.get(
    "/{practice_session_id}/recordings",
    response_model=RecordingsListResponse,
    summary="查詢會話所有錄音",
    description="""
    需提供練習會話ID，會回傳該會話的所有錄音檔案資訊。
    """
)
async def get_session_recordings(
    practice_session_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """查詢會話所有錄音"""
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(
        practice_session_id, current_user.user_id, session
    )
    
    # 查詢該會話的所有錄音記錄
    statement = (
        select(PracticeRecord)
        .where(
            and_(
                PracticeRecord.practice_session_id == practice_session_id,
                PracticeRecord.audio_path.isnot(None)
            )
        )
        .order_by(PracticeRecord.created_at)
    )
    
    practice_records = session.exec(statement).all()
    
    # 轉換為錄音回應格式，包含播放 URL
    recordings = []
    for record in practice_records:
        recording = _create_recording_response(record, str(current_user.user_id))
        recordings.append(recording)
    
    return RecordingsListResponse(
        practice_session_id=practice_session_id,
        recordings=recordings
    )


@router.get(
    "/{practice_session_id}/recordings/{sentence_id}",
    response_model=RecordingResponse,
    summary="查詢特定句子錄音",
    description="""
    需提供練習會話ID和句子ID，會回傳該句子的錄音檔案。
    """
)
async def get_sentence_recording(
    practice_session_id: uuid.UUID,
    sentence_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """查詢特定句子錄音"""
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(
        practice_session_id, current_user.user_id, session
    )
    
    # 通過練習會話ID和句子ID獲取練習記錄
    practice_record = await get_practice_record_by_session_and_sentence(
        practice_session_id, sentence_id, current_user.user_id, session
    )
    
    # 檢查是否有錄音檔案
    if not practice_record.audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="該句子尚未錄音"
        )
    
    return _create_recording_response(practice_record, str(current_user.user_id))



@router.delete(
    "/{practice_session_id}/recordings/{sentence_id}",
    summary="刪除練習錄音",
    description="""
    需提供練習會話ID和句子ID。會刪除該句子的錄音檔案並重置練習記錄狀態。
    """
)
async def delete_recording(
    practice_session_id: uuid.UUID,
    sentence_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """刪除練習錄音"""
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(
        practice_session_id, current_user.user_id, session
    )
    
    # 通過練習會話ID和句子ID獲取練習記錄
    practice_record = await get_practice_record_by_session_and_sentence(
        practice_session_id, sentence_id, current_user.user_id, session
    )
    
    # 檢查是否有錄音檔案
    if not practice_record.audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="該句子尚未錄音"
        )
    
    # 從儲存服務中刪除檔案
    try:
        practice_recording_service.delete_practice_recording(
            str(practice_record.practice_record_id),
            str(current_user.user_id),
            session
        )
    except Exception as e:
        # 記錄錯誤但繼續清理資料庫記錄
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"刪除錄音檔案失敗: {str(e)}")
    
    # 重置練習記錄
    from src.practice.models import PracticeRecordStatus
    from datetime import datetime
    
    practice_record.audio_path = None
    practice_record.audio_duration = None
    practice_record.file_size = None
    practice_record.content_type = None
    practice_record.record_status = PracticeRecordStatus.PENDING
    practice_record.recorded_at = None
    practice_record.updated_at = datetime.now()
    
    session.add(practice_record)
    session.commit()
    
    return {"message": "錄音檔案刪除成功", "success": True}


@router.get(
    "/{practice_session_id}/records",
    response_model=PracticeRecordListResponse,
    summary="查詢練習記錄",
    description="""
    需提供練習會話ID，會回傳該會話的所有練習記錄與對應句子ID與內容。
    """
)
async def get_session_records(
    practice_session_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """查詢練習記錄"""
    return await get_practice_session_records(
        practice_session_id, current_user.user_id, session
    )


@router.put(
    "/{practice_session_id}/records/{sentence_id}",
    response_model=PracticeRecordResponse,
    summary="更新練習記錄",
    description="""
    需提供練習會話ID和句子ID，會更新該句子的練習記錄狀態。
    """
)
async def update_record_status(
    practice_session_id: uuid.UUID,
    sentence_id: uuid.UUID,
    update_data: RecordUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """更新練習記錄狀態"""
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(
        practice_session_id, current_user.user_id, session
    )
    
    # 通過練習會話ID和句子ID獲取練習記錄
    practice_record = await get_practice_record_by_session_and_sentence(
        practice_session_id, sentence_id, current_user.user_id, session
    )
    
    # 更新狀態
    from datetime import datetime
    practice_record.record_status = update_data.record_status
    practice_record.updated_at = datetime.now()
    
    session.add(practice_record)
    session.commit()
    session.refresh(practice_record)
    
    # 取得相關資訊以返回完整回應
    from src.course.models import Chapter
    chapter = session.get(Chapter, practice_session.chapter_id)
    sentence = session.get(Sentence, practice_record.sentence_id)
    
    return PracticeRecordResponse(
        practice_record_id=practice_record.practice_record_id,
        practice_session_id=practice_record.practice_session_id,
        user_id=practice_session.user_id,
        chapter_id=practice_session.chapter_id,
        sentence_id=practice_record.sentence_id,
        audio_path=practice_record.audio_path,
        audio_duration=practice_record.audio_duration,
        file_size=practice_record.file_size,
        content_type=practice_record.content_type,
        record_status=practice_record.record_status,
        recorded_at=practice_record.recorded_at,
        created_at=practice_record.created_at,
        updated_at=practice_record.updated_at,
        chapter_name=chapter.chapter_name if chapter else "",
        sentence_content=sentence.content if sentence else "",
        sentence_name=sentence.sentence_name if sentence else ""
    )
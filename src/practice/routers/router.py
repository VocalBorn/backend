from typing import Annotated, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlmodel import Session
import uuid

from src.shared.database.database import get_session
from src.auth.services.permission_service import (
    get_current_user
)
from src.auth.models import User
from src.course.models import PracticeStatus

from src.practice.schemas import (
    PracticeRecordCreate,
    PracticeRecordUpdate,
    PracticeRecordResponse,
    PracticeRecordListResponse,
    PracticeStatsResponse,
    AudioUploadResponse
)

from src.practice.services.practice_service import (
    create_practice_record,
    get_practice_record,
    update_practice_record,
    list_user_practice_records,
    delete_practice_record,
    get_user_practice_stats,
    update_practice_audio_info
)


from src.storage.practice_recording_service import practice_recording_service

router = APIRouter(
    prefix='/practice',
    tags=['practice']
)

# ==================== 練習記錄相關端點 ====================

@router.post(
    "/start",
    response_model=PracticeRecordResponse,
    summary="開始練習",
    description="""
    開始新的練習階段。
    此端點會建立一筆練習記錄，用於追蹤練習進度。
    """
)
async def start_practice(
    practice_data: PracticeRecordCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    practice_record = await create_practice_record(
        practice_data, current_user.user_id, session
    )
    
    # 轉換為回應格式
    # 取得章節資訊
    from src.course.models import Chapter
    chapter = session.get(Chapter, practice_record.chapter_id)
    
    return PracticeRecordResponse(
        practice_record_id=practice_record.practice_record_id,
        user_id=practice_record.user_id,
        chapter_id=practice_record.chapter_id,
        sentence_id=practice_record.sentence_id,
        audio_path=practice_record.audio_path,
        audio_duration=practice_record.audio_duration,
        file_size=practice_record.file_size,
        content_type=practice_record.content_type,
        practice_status=practice_record.practice_status,
        begin_time=practice_record.begin_time,
        end_time=practice_record.end_time,
        created_at=practice_record.created_at,
        updated_at=practice_record.updated_at,
        chapter_name=chapter.chapter_name if chapter else None
    )


@router.post(
    "/upload/{practice_record_id}",
    response_model=AudioUploadResponse,
    summary="上傳練習錄音",
    description="""
    上傳練習錄音檔案。
    支援的檔案格式：MP3、WAV、M4A、OGG、WebM、FLAC、AAC
    檔案大小限制：50MB
    """
)
async def upload_practice_recording(
    practice_record_id: uuid.UUID,
    sentence_id: Annotated[uuid.UUID, Form(description="句子ID")],
    audio_file: Annotated[UploadFile, File(description="音訊檔案")],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # 驗證練習記錄是否存在且屬於當前用戶
    practice_record = await get_practice_record(practice_record_id, current_user.user_id, session)
    
    # 上傳檔案
    upload_result = practice_recording_service.upload_practice_recording(
        user_id=str(current_user.user_id),
        practice_record_id=str(practice_record_id),
        audio_file=audio_file,
        db_session=session
    )
    
    # 更新練習記錄的句子資訊
    await update_practice_audio_info(
        practice_record_id=practice_record_id,
        sentence_id=sentence_id,
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
    "/recordings",
    response_model=PracticeRecordListResponse,
    summary="取得練習記錄列表",
    description="""
    取得當前用戶的練習記錄列表，支援分頁和狀態篩選。
    """
)
async def list_practice_records(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 10,
    status: Optional[PracticeStatus] = None
):
    return await list_user_practice_records(
        user_id=current_user.user_id,
        session=session,
        skip=skip,
        limit=limit,
        status_filter=status
    )


@router.get(
    "/recordings/{practice_record_id}",
    response_model=PracticeRecordResponse,
    summary="取得練習記錄詳情",
    description="""
    根據練習記錄 ID 取得特定練習記錄的詳細資訊。
    """
)
async def get_practice_record_detail(
    practice_record_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    practice_record = await get_practice_record(practice_record_id, current_user.user_id, session)
    
    # 取得相關資訊
    from src.course.models import Chapter, Sentence
    chapter = session.get(Chapter, practice_record.chapter_id)
    sentence = session.get(Sentence, practice_record.sentence_id) if practice_record.sentence_id else None
    
    return PracticeRecordResponse(
        practice_record_id=practice_record.practice_record_id,
        user_id=practice_record.user_id,
        chapter_id=practice_record.chapter_id,
        sentence_id=practice_record.sentence_id,
        audio_path=practice_record.audio_path,
        audio_duration=practice_record.audio_duration,
        file_size=practice_record.file_size,
        content_type=practice_record.content_type,
        practice_status=practice_record.practice_status,
        begin_time=practice_record.begin_time,
        end_time=practice_record.end_time,
        created_at=practice_record.created_at,
        updated_at=practice_record.updated_at,
        chapter_name=chapter.chapter_name if chapter else None,
        sentence_content=sentence.content if sentence else None,
        sentence_name=sentence.sentence_name if sentence else None
    )


@router.patch(
    "/recordings/{practice_record_id}",
    response_model=PracticeRecordResponse,
    summary="更新練習記錄",
    description="""
    更新練習記錄的狀態或結束時間。
    """
)
async def update_practice_record_route(
    practice_record_id: uuid.UUID,
    update_data: PracticeRecordUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    practice_record = await update_practice_record(
        practice_record_id, update_data, current_user.user_id, session
    )
    
    # 取得相關資訊
    from src.course.models import Chapter, Sentence
    chapter = session.get(Chapter, practice_record.chapter_id)
    sentence = session.get(Sentence, practice_record.sentence_id) if practice_record.sentence_id else None
    
    return PracticeRecordResponse(
        practice_record_id=practice_record.practice_record_id,
        user_id=practice_record.user_id,
        chapter_id=practice_record.chapter_id,
        sentence_id=practice_record.sentence_id,
        audio_path=practice_record.audio_path,
        audio_duration=practice_record.audio_duration,
        file_size=practice_record.file_size,
        content_type=practice_record.content_type,
        practice_status=practice_record.practice_status,
        begin_time=practice_record.begin_time,
        end_time=practice_record.end_time,
        created_at=practice_record.created_at,
        updated_at=practice_record.updated_at,
        chapter_name=chapter.chapter_name if chapter else None,
        sentence_content=sentence.content if sentence else None,
        sentence_name=sentence.sentence_name if sentence else None
    )


@router.delete(
    "/recordings/{practice_record_id}",
    summary="刪除練習記錄",
    description="""
    刪除指定的練習記錄。
    """
)
async def delete_practice_record_route(
    practice_record_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    success = await delete_practice_record(practice_record_id, current_user.user_id, session)
    
    return {"message": "練習記錄刪除成功", "success": success}


@router.get(
    "/stats",
    response_model=PracticeStatsResponse,
    summary="取得練習統計",
    description="""
    取得當前用戶的練習統計資訊，包括總練習次數、時長、準確度等。
    """
)
async def get_practice_stats(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    return await get_user_practice_stats(current_user.user_id, session)



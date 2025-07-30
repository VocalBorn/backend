"""
練習會話管理路由
處理練習會話的 CRUD 操作
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func, and_, desc
import uuid

from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User
from src.practice.models import PracticeSession, PracticeRecord, PracticeSessionStatus, PracticeRecordStatus
from src.course.models import Chapter

from src.practice.schemas import (
    PracticeSessionCreate,
    PracticeSessionResponse,
    PracticeSessionListResponse
)

from src.practice.services.practice_service import (
    create_practice_session,
    get_practice_session,
    delete_practice_session,
    complete_practice_session
)

router = APIRouter(
    prefix='/practice/sessions',
    tags=['practice-sessions']
)

@router.post(
    "",
    response_model=PracticeSessionResponse,
    summary="開始新的練習會話",
    description="""
    開始新的練習會話。需提供 Chapter ID，會回傳練習會話詳情。
    此端點會建立一個練習會話，並為該章節的所有句子預建練習記錄。
    """
)
async def create_session(
    practice_data: PracticeSessionCreate,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> PracticeSessionResponse:
    """建立新的練習會話"""
    practice_session = await create_practice_session(
        practice_data, current_user.user_id, db_session
    )
    
    # 取得章節資訊
    chapter = db_session.get(Chapter, practice_session.chapter_id)
    
    # 統計進度資訊
    total_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        PracticeRecord.practice_session_id == practice_session.practice_session_id
    )
    total_sentences = db_session.exec(total_sentences_stmt).one()
    
    completed_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        and_(
            PracticeRecord.practice_session_id == practice_session.practice_session_id,
            PracticeRecord.record_status != PracticeRecordStatus.PENDING
        )
    )
    completed_sentences = db_session.exec(completed_sentences_stmt).one()
    
    pending_sentences = total_sentences - completed_sentences
    
    return PracticeSessionResponse(
        practice_session_id=practice_session.practice_session_id,
        user_id=practice_session.user_id,
        chapter_id=practice_session.chapter_id,
        session_status=practice_session.session_status,
        begin_time=practice_session.begin_time,
        end_time=practice_session.end_time,
        total_duration=practice_session.total_duration,
        created_at=practice_session.created_at,
        updated_at=practice_session.updated_at,
        chapter_name=chapter.chapter_name if chapter else None,
        total_sentences=total_sentences,
        completed_sentences=completed_sentences,
        pending_sentences=pending_sentences
    )


@router.get(
    "",
    response_model=PracticeSessionListResponse,
    summary="查詢用戶練習會話列表",
    description="""
    取得當前用戶的練習會話列表，可選參數 chapter_id 來篩選特定章節，支援分頁。
    """
)
async def list_sessions(
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 10,
    chapter_id: Optional[uuid.UUID] = None
):
    """查詢用戶練習會話列表"""
    # 建構查詢條件
    conditions = [PracticeSession.user_id == current_user.user_id]
    if chapter_id:
        conditions.append(PracticeSession.chapter_id == chapter_id)
    
    # 查詢總數
    count_statement = select(func.count(PracticeSession.practice_session_id)).where(
        and_(*conditions)
    )
    total = db_session.exec(count_statement).one()
    
    # 查詢會話列表，包含章節資訊
    statement = (
        select(PracticeSession, Chapter)
        .join(Chapter, PracticeSession.chapter_id == Chapter.chapter_id)
        .where(and_(*conditions))
        .order_by(desc(PracticeSession.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    results = db_session.exec(statement).all()
    
    # 轉換為回應格式
    practice_sessions = []
    for practice_session, chapter in results:
        # 統計每個會話的進度
        total_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
            PracticeRecord.practice_session_id == practice_session.practice_session_id
        )
        total_sentences = db_session.exec(total_sentences_stmt).one()
        
        completed_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
            and_(
                PracticeRecord.practice_session_id == practice_session.practice_session_id,
                PracticeRecord.record_status != PracticeRecordStatus.PENDING
            )
        )
        completed_sentences = db_session.exec(completed_sentences_stmt).one()
        
        pending_sentences = total_sentences - completed_sentences
        
        response = PracticeSessionResponse(
            practice_session_id=practice_session.practice_session_id,
            user_id=practice_session.user_id,
            chapter_id=practice_session.chapter_id,
            session_status=practice_session.session_status,
            begin_time=practice_session.begin_time,
            end_time=practice_session.end_time,
            total_duration=practice_session.total_duration,
            created_at=practice_session.created_at,
            updated_at=practice_session.updated_at,
            chapter_name=chapter.chapter_name,
            total_sentences=total_sentences,
            completed_sentences=completed_sentences,
            pending_sentences=pending_sentences
        )
        practice_sessions.append(response)
    
    return PracticeSessionListResponse(
        total=total,
        practice_sessions=practice_sessions
    )


@router.get(
    "/{practice_session_id}",
    response_model=PracticeSessionResponse,
    summary="查詢特定練習會話",
    description="""
    需提供練習會話ID，會回傳練習會話詳情。
    """
)
async def get_session_router(
    practice_session_id: uuid.UUID,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """查詢特定練習會話"""
    practice_session = await get_practice_session(
        practice_session_id, current_user.user_id, db_session
    )
    
    # 取得章節資訊
    chapter = db_session.get(Chapter, practice_session.chapter_id)
    
    # 統計進度資訊
    total_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        PracticeRecord.practice_session_id == practice_session.practice_session_id
    )
    total_sentences = db_session.exec(total_sentences_stmt).one()
    
    completed_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        and_(
            PracticeRecord.practice_session_id == practice_session.practice_session_id,
            PracticeRecord.record_status != PracticeRecordStatus.PENDING
        )
    )
    completed_sentences = db_session.exec(completed_sentences_stmt).one()
    
    pending_sentences = total_sentences - completed_sentences
    
    return PracticeSessionResponse(
        practice_session_id=practice_session.practice_session_id,
        user_id=practice_session.user_id,
        chapter_id=practice_session.chapter_id,
        session_status=practice_session.session_status,
        begin_time=practice_session.begin_time,
        end_time=practice_session.end_time,
        total_duration=practice_session.total_duration,
        created_at=practice_session.created_at,
        updated_at=practice_session.updated_at,
        chapter_name=chapter.chapter_name if chapter else None,
        total_sentences=total_sentences,
        completed_sentences=completed_sentences,
        pending_sentences=pending_sentences
    )


@router.delete(
    "/{practice_session_id}",
    summary="刪除練習會話",
    description="""
    需提供練習會話ID。此操作將會永久刪除整個練習會話及其所有相關的練習記錄和回饋。
    """
)
async def delete_session(
    practice_session_id: uuid.UUID,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """刪除練習會話"""
    success = await delete_practice_session(
        practice_session_id, current_user.user_id, db_session
    )
    
    return {"message": "練習會話刪除成功", "success": success}


@router.patch(
    "/{practice_session_id}/complete",
    response_model=PracticeSessionResponse,
    summary="完成練習會話",
    description="""
    將練習會話標記為已完成，設定結束時間並計算總時長。
    """
)
async def complete_session(
    practice_session_id: uuid.UUID,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """完成練習會話"""
    practice_session = await complete_practice_session(
      practice_session_id=practice_session_id,
      user_id=current_user.user_id,
      db_session=db_session
    )
    
    # 取得章節資訊
    chapter = db_session.get(Chapter, practice_session.chapter_id)
    
    # 統計進度資訊
    total_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        PracticeRecord.practice_session_id == practice_session.practice_session_id
    )
    total_sentences = db_session.exec(total_sentences_stmt).one()
    
    completed_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        and_(
            PracticeRecord.practice_session_id == practice_session.practice_session_id,
            PracticeRecord.record_status != PracticeRecordStatus.PENDING
        )
    )
    completed_sentences = db_session.exec(completed_sentences_stmt).one()
    
    pending_sentences = total_sentences - completed_sentences
    
    return PracticeSessionResponse(
        practice_session_id=practice_session.practice_session_id,
        user_id=practice_session.user_id,
        chapter_id=practice_session.chapter_id,
        session_status=practice_session.session_status,
        begin_time=practice_session.begin_time,
        end_time=practice_session.end_time,
        total_duration=practice_session.total_duration,
        created_at=practice_session.created_at,
        updated_at=practice_session.updated_at,
        chapter_name=chapter.chapter_name if chapter else None,
        total_sentences=total_sentences,
        completed_sentences=completed_sentences,
        pending_sentences=pending_sentences
    )
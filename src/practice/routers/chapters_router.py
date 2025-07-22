"""
章節相關練習查詢路由
處理章節與練習相關的查詢操作
"""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func, and_, desc
import uuid

from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User
from src.practice.models import PracticeSession, PracticeRecord, PracticeRecordStatus
from src.course.models import Chapter

from src.practice.schemas import (
    PracticeSessionListResponse,
    PracticeSessionResponse
)

router = APIRouter(
    prefix='/practice/chapters',
    tags=['practice-chapters']
)

@router.get(
    "/{chapter_id}/sessions",
    response_model=PracticeSessionListResponse,
    summary="查詢章節練習會話",
    description="""
    需提供章節ID，會回傳該章節的所有練習會話，支援分頁。
    """
)
async def get_chapter_sessions(
    chapter_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 10
):
    """查詢章節練習會話"""
    # 驗證章節是否存在
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的章節不存在"
        )
    
    # 建構查詢條件
    conditions = [
        PracticeSession.user_id == current_user.user_id,
        PracticeSession.chapter_id == chapter_id
    ]
    
    # 查詢總數
    count_statement = select(func.count(PracticeSession.practice_session_id)).where(
        and_(*conditions)
    )
    total = session.exec(count_statement).one()
    
    # 查詢會話列表
    statement = (
        select(PracticeSession)
        .where(and_(*conditions))
        .order_by(desc(PracticeSession.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    practice_sessions = session.exec(statement).all()
    
    # 轉換為回應格式
    session_responses = []
    for practice_session in practice_sessions:
        # 統計每個會話的進度
        total_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
            PracticeRecord.practice_session_id == practice_session.practice_session_id
        )
        total_sentences = session.exec(total_sentences_stmt).one()
        
        completed_sentences_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
            and_(
                PracticeRecord.practice_session_id == practice_session.practice_session_id,
                PracticeRecord.record_status != PracticeRecordStatus.PENDING
            )
        )
        completed_sentences = session.exec(completed_sentences_stmt).one()
        
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
        session_responses.append(response)
    
    return PracticeSessionListResponse(
        total=total,
        practice_sessions=session_responses
    )
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
import uuid

from src.shared.database.database import get_session
from src.auth.services.permission_service import (
    get_current_user,
    require_therapist,
    require_client_or_therapist
)
from src.auth.models import User

from src.practice.schemas import (
    PracticeFeedbackCreate,
    PracticeFeedbackUpdate,
    PracticeFeedbackResponse,
    PracticeFeedbackListResponse,
    TherapistPendingPracticeListResponse
)


from src.practice.services.feedback_service import (
    create_practice_feedback,
    get_practice_feedback,
    update_practice_feedback,
    list_therapist_pending_practices,
    list_practice_feedbacks,
    delete_practice_feedback
)


router = APIRouter(
    prefix='/practice/therapist',
    tags=['practice-therapist'],
)

# ==================== 治療師分析相關端點 ====================

@router.get(
    "/pending",
    response_model=TherapistPendingPracticeListResponse,
    summary="取得待分析練習列表",
    description="""
    取得治療師負責客戶的待分析練習列表。
    此端點僅限治療師使用。
    """
)
async def get_pending_practices_for_therapist(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)],
    skip: int = 0,
    limit: int = 10
):
    return await list_therapist_pending_practices(
        therapist_id=current_user.user_id,
        session=session,
        skip=skip,
        limit=limit
    )


@router.post(
    "/feedback/{practice_record_id}",
    response_model=PracticeFeedbackResponse,
    summary="提供練習回饋",
    description="""
    治療師對練習記錄提供專業分析和回饋。
    此端點僅限治療師使用。
    """
)
async def create_practice_feedback_route(
    practice_record_id: uuid.UUID,
    feedback_data: PracticeFeedbackCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)]
):
    feedback = await create_practice_feedback(
        practice_record_id, feedback_data, current_user.user_id, session
    )
    
    return PracticeFeedbackResponse(
        feedback_id=feedback.feedback_id,
        practice_record_id=feedback.practice_record_id,
        therapist_id=feedback.therapist_id,
        content=feedback.content,
        pronunciation_accuracy=feedback.pronunciation_accuracy,
        suggestions=feedback.suggestions,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        therapist_name=current_user.name
    )


@router.get(
    "/feedback/{practice_record_id}",
    response_model=PracticeFeedbackResponse,
    summary="取得練習回饋",
    description="""
    取得特定練習記錄的回饋內容。
    練習者和治療師都可以查看。
    """
)
async def get_practice_feedback_route(
    practice_record_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_client_or_therapist)]
):
    feedback = await get_practice_feedback(practice_record_id, current_user.user_id, session)
    
    # 取得治療師名稱
    therapist = session.get(User, feedback.therapist_id)
    therapist_name = therapist.name if therapist else None
    
    return PracticeFeedbackResponse(
        feedback_id=feedback.feedback_id,
        practice_record_id=feedback.practice_record_id,
        therapist_id=feedback.therapist_id,
        content=feedback.content,
        pronunciation_accuracy=feedback.pronunciation_accuracy,
        suggestions=feedback.suggestions,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        therapist_name=therapist_name
    )


@router.put(
    "/feedback/{feedback_id}",
    response_model=PracticeFeedbackResponse,
    summary="更新練習回饋",
    description="""
    更新練習回饋內容。
    此端點僅限原治療師使用。
    """
)
async def update_practice_feedback_route(
    feedback_id: uuid.UUID,
    update_data: PracticeFeedbackUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)]
):
    feedback = await update_practice_feedback(
        feedback_id, update_data, current_user.user_id, session
    )
    
    return PracticeFeedbackResponse(
        feedback_id=feedback.feedback_id,
        practice_record_id=feedback.practice_record_id,
        therapist_id=feedback.therapist_id,
        content=feedback.content,
        pronunciation_accuracy=feedback.pronunciation_accuracy,
        suggestions=feedback.suggestions,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        therapist_name=current_user.name
    )


@router.delete(
    "/feedback/{feedback_id}",
    summary="刪除練習回饋",
    description="""
    刪除練習回饋。
    此端點僅限原治療師使用。
    """
)
async def delete_practice_feedback_route(
    feedback_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)]
):
    success = await delete_practice_feedback(feedback_id, current_user.user_id, session)
    
    return {"message": "回饋刪除成功", "success": success}


@router.get(
    "/feedbacks",
    response_model=PracticeFeedbackListResponse,
    summary="取得回饋列表",
    description="""
    取得當前用戶收到的所有練習回饋列表。
    """
)
async def list_practice_feedbacks_route(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 10
):
    return await list_practice_feedbacks(
        user_id=current_user.user_id,
        session=session,
        skip=skip,
        limit=limit
    )
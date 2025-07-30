from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
import uuid

from src.shared.database.database import get_session
from src.auth.services.permission_service import (
    require_therapist
)
from src.auth.models import User

from src.practice.schemas import (
    TherapistPatientsOverviewListResponse,
    PatientPracticeListResponse,
    PatientPracticeSessionsResponse,
    PracticeSessionFeedbackCreate,
    PracticeSessionFeedbackUpdate,
    PracticeSessionFeedbackResponse
)


from src.practice.services.feedback_service import (
    delete_practice_feedback,
    create_session_feedback,
    get_session_feedbacks,
    update_session_feedbacks
)

from src.practice.services.therapist_patient_service import (
    get_therapist_patients_overview,
    get_patient_practice_records,
    get_patient_practice_sessions
)


router = APIRouter(
    prefix='/practice/therapist',
    tags=['practice-therapist']
)

# ==================== 治療師患者管理端點 ====================


@router.get(
    "/patients/overview",
    response_model=TherapistPatientsOverviewListResponse,
    summary="取得患者練習進度概覽",
    description="""
    取得所有患者的練習章節與進度概覽。
    這是一個新增的重點功能，讓治療師可以一次檢視所有患者的練習狀況。
    此端點僅限治療師使用。
    """
)
async def get_therapist_patients_overview_route(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)],
    skip: int = 0,
    limit: int = 20,
    search: str = None
):
    return await get_therapist_patients_overview(
        therapist_id=current_user.user_id,
        session=session,
        skip=skip,
        limit=limit,
        search=search
    )


@router.get(
    "/patients/{patient_id}/practices",
    response_model=PatientPracticeSessionsResponse,
    summary="取得患者練習會話記錄",
    description="""
    取得特定患者的練習會話記錄列表，按會話分組顯示，包含音訊播放功能。
    支援篩選特定練習會話或只顯示待回饋的語句。
    此端點僅限治療師使用，且只能查看指派給自己的患者。
    """
)
async def get_patient_practices_route(
    patient_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)],
    practice_session_id: uuid.UUID = None,
    pending_feedback_only: bool = False
):
    return await get_patient_practice_sessions(
        patient_id=patient_id,
        therapist_id=current_user.user_id,
        session=session,
        practice_session_id=practice_session_id,
        pending_feedback_only=pending_feedback_only
    )

# ==================== 治療師分析相關端點 ====================

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


# ==================== 會話回饋相關端點 ====================

@router.post(
    "/session/{practice_session_id}/feedback",
    response_model=PracticeSessionFeedbackResponse,
    summary="建立練習會話回饋",
    description="""
    治療師對整個練習會話提供回饋。
    針對患者的整體練習表現提供專業分析和建議。
    此端點僅限治療師使用，且只能對負責患者的練習進行回饋。
    """
)
async def create_session_feedback_route(
    practice_session_id: uuid.UUID,
    feedback_data: PracticeSessionFeedbackCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)]
):
    """建立練習會話回饋"""
    return await create_session_feedback(
        practice_session_id=practice_session_id,
        feedback_data=feedback_data,
        therapist_id=current_user.user_id,
        session=session
    )


@router.get(
    "/session/{practice_session_id}/feedback",
    response_model=PracticeSessionFeedbackResponse,
    summary="取得練習會話回饋",
    description="""
    取得特定練習會話的回饋內容。
    回傳該會話的整體回饋資訊。
    此端點僅限治療師使用，且只能查看負責患者的練習回饋。
    """
)
async def get_session_feedbacks_route(
    practice_session_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)]
):
    """取得練習會話回饋"""
    return await get_session_feedbacks(
        practice_session_id=practice_session_id,
        therapist_id=current_user.user_id,
        session=session
    )


@router.put(
    "/session/{practice_session_id}/feedback",
    response_model=PracticeSessionFeedbackResponse,
    summary="更新練習會話回饋",
    description="""
    更新練習會話的回饋內容。
    可以修改現有的整體回饋內容。
    此端點僅限原治療師使用。
    """
)
async def update_session_feedbacks_route(
    practice_session_id: uuid.UUID,
    feedback_data: PracticeSessionFeedbackUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_therapist)]
):
    """更新練習會話回饋"""
    return await update_session_feedbacks(
        practice_session_id=practice_session_id,
        feedback_data=feedback_data,
        therapist_id=current_user.user_id,
        session=session
    )

"""
患者回饋路由器
處理患者查看治療師回饋的API端點
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
import uuid
from datetime import datetime

from src.shared.database.database import get_session
from src.auth.services.permission_service import require_client
from src.auth.models import User
from src.practice.schemas.patient_feedback import (
    FeedbackFilters,
    PaginatedFeedbackListResponse,
    PatientFeedbackDetailResponse
)
from src.practice.services.patient_feedback_service import (
    get_patient_feedbacks,
    get_feedback_detail
)

router = APIRouter(
    prefix='/practice/patient',
    tags=['practice-patient-feedback']
)


@router.get(
    "/feedbacks",
    response_model=PaginatedFeedbackListResponse,
    summary="取得患者回饋列表",
    description="""
    取得患者的所有回饋列表，支援篩選和分頁。
    
    支援的篩選條件：
    - page: 頁碼 (預設: 1)
    - limit: 每頁數量 (預設: 10, 最大: 50)
    - chapter_id: 章節 ID 篩選 (可選)
    - therapist_id: 治療師 ID 篩選 (可選)
    - start_date: 開始日期篩選 (可選，ISO 格式)
    - end_date: 結束日期篩選 (可選，ISO 格式)
    
    此端點僅限患者使用，只能查看自己的回饋。
    """
)
async def get_patient_feedbacks_route(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_client)],
    page: int = Query(default=1, ge=1, description="頁碼"),
    limit: int = Query(default=10, ge=1, le=50, description="每頁數量"),
    chapter_id: Optional[uuid.UUID] = Query(default=None, description="章節 ID 篩選"),
    therapist_id: Optional[uuid.UUID] = Query(default=None, description="治療師 ID 篩選"),
    start_date: Optional[datetime] = Query(default=None, description="開始日期篩選"),
    end_date: Optional[datetime] = Query(default=None, description="結束日期篩選"),
):
    """取得患者回饋列表"""
    filters = FeedbackFilters(
        page=page,
        limit=limit,
        chapter_id=chapter_id,
        therapist_id=therapist_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return await get_patient_feedbacks(
        patient_id=current_user.user_id,
        filters=filters,
        session=session
    )


@router.get(
    "/feedbacks/{feedback_id}",
    response_model=PatientFeedbackDetailResponse,
    summary="取得回饋詳情",
    description="""
    取得特定回饋的詳細資訊。
    
    回應包含：
    - 治療師回饋內容和基本資訊
    - 練習記錄詳情（音訊檔案資訊）
    - 章節資訊
    
    此端點僅限患者使用，只能查看自己的回饋詳情。
    """
)
async def get_feedback_detail_route(
    feedback_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(require_client)]
):
    """取得回饋詳情"""
    return await get_feedback_detail(
        feedback_id=feedback_id,
        patient_id=current_user.user_id,
        session=session
    )
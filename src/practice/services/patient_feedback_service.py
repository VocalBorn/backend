"""
患者回饋服務
處理患者查看治療師回饋的功能
"""

import uuid
import logging
import math
from sqlmodel import Session, select, and_, desc, func
from fastapi import HTTPException, status

from src.practice.models import (
    PracticeSession, PracticeSessionFeedback, PracticeRecord
)
from src.course.models import Chapter, Sentence
from src.auth.models import User
from src.therapist.models import TherapistProfile
from src.practice.schemas.patient_feedback import (
    FeedbackFilters,
    PaginatedFeedbackListResponse,
    PatientFeedbackListItem,
    PatientFeedbackDetailResponse,
    PaginationInfo,
    TherapistInfo,
    ChapterInfo,
    TherapistFeedbackDetail,
    PracticeRecordDetail
)

logger = logging.getLogger(__name__)


async def get_patient_feedbacks(
    patient_id: uuid.UUID,
    filters: FeedbackFilters,
    session: Session
) -> PaginatedFeedbackListResponse:
    """
    取得患者的回饋列表，支援篩選和分頁
    
    Args:
        patient_id: 患者 ID
        filters: 篩選條件（章節、治療師、時間範圍等）
        session: 資料庫會話
        
    Returns:
        分頁的回饋列表回應
        
    Raises:
        HTTPException: 當查詢失敗時
    """
    try:
        # 構建基礎查詢
        base_query = (
            select(
                PracticeSessionFeedback,
                Chapter.chapter_name,
                User.name.label("therapist_name")
            )
            .join(PracticeSession, PracticeSessionFeedback.practice_session_id == PracticeSession.practice_session_id)
            .join(Chapter, PracticeSession.chapter_id == Chapter.chapter_id)
            .join(User, PracticeSessionFeedback.therapist_id == User.user_id)
            .where(PracticeSession.user_id == patient_id)
        )

        # 套用篩選條件
        if filters.chapter_id:
            base_query = base_query.where(PracticeSession.chapter_id == filters.chapter_id)
        
        if filters.therapist_id:
            base_query = base_query.where(PracticeSessionFeedback.therapist_id == filters.therapist_id)
        
        if filters.start_date:
            base_query = base_query.where(PracticeSessionFeedback.created_at >= filters.start_date)
        
        if filters.end_date:
            base_query = base_query.where(PracticeSessionFeedback.created_at <= filters.end_date)

        # 計算總數
        count_query = select(func.count()).select_from(
            select(PracticeSessionFeedback.session_feedback_id)
            .join(PracticeSession, PracticeSessionFeedback.practice_session_id == PracticeSession.practice_session_id)
            .where(PracticeSession.user_id == patient_id)
            .subquery()
        )
        
        total_items = session.exec(count_query).one()
        total_pages = math.ceil(total_items / filters.limit)

        # 套用排序和分頁
        query = (
            base_query
            .order_by(desc(PracticeSessionFeedback.created_at))
            .offset((filters.page - 1) * filters.limit)
            .limit(filters.limit)
        )

        results = session.exec(query).all()

        # 建立回應項目
        feedback_items = []
        for result in results:
            feedback, chapter_name, therapist_name = result

            feedback_items.append(PatientFeedbackListItem(
                session_feedback_id=feedback.session_feedback_id,
                practice_session_id=feedback.practice_session_id,
                chapter_name=chapter_name,
                therapist_name=therapist_name,
                content=feedback.content,
                created_at=feedback.created_at
            ))

        pagination = PaginationInfo(
            current_page=filters.page,
            per_page=filters.limit,
            total_items=total_items,
            total_pages=total_pages
        )

        logger.info(f"取得患者回饋列表成功: 患者 {patient_id}, 共 {total_items} 筆")

        return PaginatedFeedbackListResponse(
            feedbacks=feedback_items,
            pagination=pagination
        )

    except Exception as e:
        logger.error(f"取得患者回饋列表失敗: 患者 {patient_id}, 錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得回饋列表時發生錯誤"
        )


async def get_feedback_detail(
    feedback_id: uuid.UUID,
    patient_id: uuid.UUID,
    session: Session
) -> PatientFeedbackDetailResponse:
    """
    取得特定回饋的詳細資訊
    
    Args:
        feedback_id: 回饋 ID
        patient_id: 患者 ID（權限驗證）
        session: 資料庫會話
        
    Returns:
        詳細回饋資訊回應
        
    Raises:
        HTTPException: 當回饋不存在或無權限時
    """
    try:
        # 查詢回饋並驗證權限
        feedback_query = (
            select(PracticeSessionFeedback, PracticeSession)
            .join(PracticeSession, PracticeSessionFeedback.practice_session_id == PracticeSession.practice_session_id)
            .where(
                and_(
                    PracticeSessionFeedback.session_feedback_id == feedback_id,
                    PracticeSession.user_id == patient_id
                )
            )
        )
        
        feedback_result = session.exec(feedback_query).first()
        if not feedback_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="回饋不存在或無權限存取"
            )
        
        feedback, practice_session = feedback_result

        # 查詢章節資訊
        chapter = session.get(Chapter, practice_session.chapter_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="章節資料不存在"
            )

        # 查詢治療師資訊
        therapist = session.get(User, feedback.therapist_id)
        therapist_profile = session.get(TherapistProfile, feedback.therapist_id)
        
        if not therapist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="治療師資料不存在"
            )

        # 查詢練習記錄
        practice_records = session.exec(
            select(PracticeRecord, Sentence)
            .join(Sentence, PracticeRecord.sentence_id == Sentence.sentence_id)
            .where(PracticeRecord.practice_session_id == practice_session.practice_session_id)
            .order_by(PracticeRecord.created_at)
        ).all()

        # 建立回應
        therapist_specialties = []
        if therapist_profile and therapist_profile.specialization:
            if isinstance(therapist_profile.specialization, list):
                therapist_specialties = therapist_profile.specialization
            elif isinstance(therapist_profile.specialization, str):
                therapist_specialties = [s.strip() for s in therapist_profile.specialization.split(',') if s.strip()]

        response = PatientFeedbackDetailResponse(
            session_feedback_id=feedback.session_feedback_id,
            practice_session_id=feedback.practice_session_id,
            chapter=ChapterInfo(
                chapter_id=chapter.chapter_id,
                chapter_name=chapter.chapter_name,
                description=getattr(chapter, 'description', None)
            ),
            therapist=TherapistInfo(
                therapist_id=therapist.user_id,
                name=therapist.name,
                specialties=therapist_specialties,
                years_experience=getattr(therapist_profile, 'years_experience', None)
            ),
            therapist_feedback=TherapistFeedbackDetail(
                content=feedback.content,
                created_at=feedback.created_at
            ),
            practice_records=[
                PracticeRecordDetail(
                    practice_record_id=record.practice_record_id,
                    sentence_content=sentence.content,
                    audio_path=record.audio_path,
                    audio_duration=record.audio_duration,
                    recorded_at=record.recorded_at
                )
                for record, sentence in practice_records
            ]
        )

        logger.info(f"取得回饋詳情成功: 回饋 {feedback_id}, 患者 {patient_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得回饋詳情失敗: 回饋 {feedback_id}, 錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取得回饋詳情時發生錯誤"
        )
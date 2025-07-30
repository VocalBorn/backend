"""
練習回饋服務
處理治療師對練習記錄的分析和回饋功能
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select, and_, desc, func
from fastapi import HTTPException, status

from src.course.models import Sentence, Chapter
from src.practice.models import (
    PracticeRecord, PracticeRecordStatus, PracticeSession, PracticeSessionStatus, 
    PracticeFeedback, PracticeSessionFeedback
)
from src.auth.models import User
from src.practice.schemas import (
    PracticeSessionFeedbackCreate,
    PracticeSessionFeedbackUpdate,
    PracticeSessionFeedbackResponse
)

logger = logging.getLogger(__name__)

async def delete_practice_feedback(
    feedback_id: uuid.UUID,
    therapist_id: uuid.UUID,
    session: Session
) -> bool:
    """
    刪除練習回饋
    
    Args:
        feedback_id: 回饋ID
        therapist_id: 治療師ID
        session: 資料庫會話
        
    Returns:
        是否成功刪除
        
    Raises:
        HTTPException: 當回饋不存在或無權限時
    """
    feedback = session.get(PracticeFeedback, feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回饋不存在"
        )
    
    # 檢查權限：只有原治療師可以刪除
    if feedback.therapist_id != therapist_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限刪除此回饋"
        )
    
    # 更新對應的練習記錄狀態
    practice_record = session.get(PracticeRecord, feedback.practice_record_id)
    if practice_record:
        practice_record.record_status = PracticeRecordStatus.RECORDED
        practice_record.updated_at = datetime.now()
        session.add(practice_record)
    
    session.delete(feedback)
    session.commit()
    
    logger.info(f"刪除練習回饋成功: {feedback_id}")
    
    return True

# 新的會話回饋相關函數
async def create_session_feedback(
    practice_session_id: uuid.UUID,
    feedback_data: PracticeSessionFeedbackCreate,
    therapist_id: uuid.UUID,
    session: Session
) -> PracticeSessionFeedbackResponse:
    """
    建立練習會話回饋
    
    Args:
        practice_session_id: 練習會話ID
        feedback_data: 回饋資料
        therapist_id: 治療師ID
        session: 資料庫會話
        
    Returns:
        練習會話回饋回應
        
    Raises:
        HTTPException: 當練習會話不存在或已有回饋時
    """
    # 檢查練習會話是否存在並取得相關資訊
    practice_session = session.get(PracticeSession, practice_session_id)
    if not practice_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習會話不存在"
        )
    
    # 驗證治療師權限 - 確認該患者是治療師負責的
    from src.therapist.models import TherapistClient
    
    therapist_client = session.exec(
        select(TherapistClient).where(
            and_(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.client_id == practice_session.user_id,
                TherapistClient.is_active == True
            )
        )
    ).first()
    
    if not therapist_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限對此患者的練習進行回饋"
        )
    
    # 檢查是否已有回饋
    existing_feedback = session.exec(
        select(PracticeSessionFeedback).where(
            PracticeSessionFeedback.practice_session_id == practice_session_id
        )
    ).first()
    
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="該練習會話已有回饋，請使用更新功能"
        )
    
    # 建立回饋
    session_feedback = PracticeSessionFeedback(
        practice_session_id=practice_session_id,
        therapist_id=therapist_id,
        content=feedback_data.content
    )
    
    session.add(session_feedback)
    session.commit()
    session.refresh(session_feedback)
    
    # 取得相關資訊以建立回應
    therapist = session.get(User, therapist_id)
    patient = session.get(User, practice_session.user_id)
    chapter = session.get(Chapter, practice_session.chapter_id)
    
    logger.info(f"建立練習會話回饋成功: 會話 {practice_session_id}, 治療師 {therapist_id}")
    
    return PracticeSessionFeedbackResponse(
        session_feedback_id=session_feedback.session_feedback_id,
        practice_session_id=practice_session_id,
        therapist_id=therapist_id,
        therapist_name=therapist.name if therapist else "未知治療師",
        patient_id=practice_session.user_id,
        patient_name=patient.name if patient else "未知患者",
        chapter_id=practice_session.chapter_id,
        chapter_name=chapter.chapter_name if chapter else "未知章節",
        content=session_feedback.content,
        created_at=session_feedback.created_at,
        updated_at=session_feedback.updated_at
    )

async def get_session_feedbacks(
    practice_session_id: uuid.UUID,
    therapist_id: uuid.UUID,
    session: Session
) -> PracticeSessionFeedbackResponse:
    """
    取得練習會話回饋
    
    Args:
        practice_session_id: 練習會話ID
        therapist_id: 治療師ID
        session: 資料庫會話
        
    Returns:
        練習會話回饋回應
        
    Raises:
        HTTPException: 當練習會話不存在或無權限時
    """
    # 檢查練習會話是否存在
    practice_session = session.get(PracticeSession, practice_session_id)
    if not practice_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習會話不存在"
        )
    
    # 驗證治療師權限
    from src.therapist.models import TherapistClient
    
    therapist_client = session.exec(
        select(TherapistClient).where(
            and_(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.client_id == practice_session.user_id,
                TherapistClient.is_active == True
            )
        )
    ).first()
    
    if not therapist_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限查看此患者的練習回饋"
        )
    
    # 查詢該會話的回饋
    session_feedback = session.exec(
        select(PracticeSessionFeedback).where(
            PracticeSessionFeedback.practice_session_id == practice_session_id
        )
    ).first()
    
    if not session_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="該練習會話沒有回饋"
        )
    
    # 取得相關資訊
    therapist = session.get(User, session_feedback.therapist_id)
    patient = session.get(User, practice_session.user_id)
    chapter = session.get(Chapter, practice_session.chapter_id)
    
    return PracticeSessionFeedbackResponse(
        session_feedback_id=session_feedback.session_feedback_id,
        practice_session_id=practice_session_id,
        therapist_id=session_feedback.therapist_id,
        therapist_name=therapist.name if therapist else "未知治療師",
        patient_id=practice_session.user_id,
        patient_name=patient.name if patient else "未知患者",
        chapter_id=practice_session.chapter_id,
        chapter_name=chapter.chapter_name if chapter else "未知章節",
        content=session_feedback.content,
        created_at=session_feedback.created_at,
        updated_at=session_feedback.updated_at
    )

async def update_session_feedbacks(
    practice_session_id: uuid.UUID,
    feedback_data: PracticeSessionFeedbackUpdate,
    therapist_id: uuid.UUID,
    session: Session
) -> PracticeSessionFeedbackResponse:
    """
    更新練習會話回饋
    
    Args:
        practice_session_id: 練習會話ID
        feedback_data: 回饋更新資料
        therapist_id: 治療師ID
        session: 資料庫會話
        
    Returns:
        更新後的練習會話回饋回應
        
    Raises:
        HTTPException: 當練習會話不存在或無權限時
    """
    # 檢查練習會話是否存在
    practice_session = session.get(PracticeSession, practice_session_id)
    if not practice_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習會話不存在"
        )
    
    # 驗證治療師權限
    from src.therapist.models import TherapistClient
    
    therapist_client = session.exec(
        select(TherapistClient).where(
            and_(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.client_id == practice_session.user_id,
                TherapistClient.is_active == True
            )
        )
    ).first()
    
    if not therapist_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限更新此患者的練習回饋"
        )
    
    # 取得現有回饋
    session_feedback = session.exec(
        select(PracticeSessionFeedback).where(
            PracticeSessionFeedback.practice_session_id == practice_session_id
        )
    ).first()
    
    if not session_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="該練習會話沒有回饋"
        )
    
    # 檢查權限：只有原治療師可以更新
    if session_feedback.therapist_id != therapist_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限更新此回饋"
        )
    
    # 更新回饋
    session_feedback.content = feedback_data.content
    session_feedback.updated_at = datetime.now()
    
    session.add(session_feedback)
    session.commit()
    session.refresh(session_feedback)
    
    # 取得相關資訊以建立回應
    therapist = session.get(User, therapist_id)
    patient = session.get(User, practice_session.user_id)
    chapter = session.get(Chapter, practice_session.chapter_id)
    
    logger.info(f"更新練習會話回饋成功: 會話 {practice_session_id}, 治療師 {therapist_id}")
    
    return PracticeSessionFeedbackResponse(
        session_feedback_id=session_feedback.session_feedback_id,
        practice_session_id=practice_session_id,
        therapist_id=therapist_id,
        therapist_name=therapist.name if therapist else "未知治療師",
        patient_id=practice_session.user_id,
        patient_name=patient.name if patient else "未知患者",
        chapter_id=practice_session.chapter_id,
        chapter_name=chapter.chapter_name if chapter else "未知章節",
        content=session_feedback.content,
        created_at=session_feedback.created_at,
        updated_at=session_feedback.updated_at
    )

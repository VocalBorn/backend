"""
練習回饋服務
處理治療師對練習記錄的分析和回饋功能
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select, and_, desc, func
from fastapi import HTTPException, status

from src.course.models import PracticeRecord, PracticeStatus, Sentence, Chapter, PracticeFeedback
from src.auth.models import User, UserRole
from src.practice.schemas import (
    PracticeFeedbackCreate,
    PracticeFeedbackUpdate,
    PracticeFeedbackResponse,
    PracticeFeedbackListResponse,
    TherapistPendingPracticeResponse,
    TherapistPendingPracticeListResponse
)

logger = logging.getLogger(__name__)


async def create_practice_feedback(
    practice_record_id: uuid.UUID,
    feedback_data: PracticeFeedbackCreate,
    therapist_id: uuid.UUID,
    session: Session
) -> PracticeFeedback:
    """
    建立練習回饋
    
    Args:
        practice_record_id: 練習記錄ID
        feedback_data: 回饋資料
        therapist_id: 治療師ID
        session: 資料庫會話
        
    Returns:
        建立的回饋記錄
        
    Raises:
        HTTPException: 當練習記錄不存在或已有回饋時
    """
    # 檢查練習記錄是否存在
    practice_record = session.get(PracticeRecord, practice_record_id)
    if not practice_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習記錄不存在"
        )
    
    # 檢查是否已有回饋
    existing_feedback = session.exec(
        select(PracticeFeedback).where(
            PracticeFeedback.practice_record_id == practice_record_id
        )
    ).first()
    
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="該練習記錄已有回饋"
        )
    
    # 建立回饋
    feedback = PracticeFeedback(
        practice_record_id=practice_record_id,
        therapist_id=therapist_id,
        content=feedback_data.content,
        pronunciation_accuracy=feedback_data.pronunciation_accuracy,
        suggestions=feedback_data.suggestions
    )
    
    session.add(feedback)
    
    # 更新練習記錄狀態為已分析
    practice_record.practice_status = PracticeStatus.ANALYZED
    practice_record.updated_at = datetime.now()
    session.add(practice_record)
    
    session.commit()
    session.refresh(feedback)
    
    logger.info(f"建立練習回饋成功: 治療師 {therapist_id}, 練習記錄 {practice_record_id}")
    
    return feedback


async def get_practice_feedback(
    practice_record_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session
) -> PracticeFeedback:
    """
    取得練習回饋
    
    Args:
        practice_record_id: 練習記錄ID
        user_id: 用戶ID（可以是練習者或治療師）
        session: 資料庫會話
        
    Returns:
        回饋記錄
        
    Raises:
        HTTPException: 當回饋不存在或無權限時
    """
    # 查詢回饋及相關資訊
    statement = (
        select(PracticeFeedback, PracticeRecord, User)
        .join(PracticeRecord, PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id)
        .join(User, PracticeFeedback.therapist_id == User.user_id)
        .where(PracticeFeedback.practice_record_id == practice_record_id)
    )
    
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回饋不存在"
        )
    
    feedback, practice_record, therapist = result
    
    # 檢查權限：只有練習者本人或治療師可以查看
    if practice_record.user_id != user_id and feedback.therapist_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限查看此回饋"
        )
    
    return feedback


async def update_practice_feedback(
    feedback_id: uuid.UUID,
    update_data: PracticeFeedbackUpdate,
    therapist_id: uuid.UUID,
    session: Session
) -> PracticeFeedback:
    """
    更新練習回饋
    
    Args:
        feedback_id: 回饋ID
        update_data: 更新資料
        therapist_id: 治療師ID
        session: 資料庫會話
        
    Returns:
        更新後的回饋記錄
        
    Raises:
        HTTPException: 當回饋不存在或無權限時
    """
    feedback = session.get(PracticeFeedback, feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回饋不存在"
        )
    
    # 檢查權限：只有原治療師可以更新
    if feedback.therapist_id != therapist_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限更新此回饋"
        )
    
    # 更新欄位
    if update_data.content is not None:
        feedback.content = update_data.content
    
    if update_data.pronunciation_accuracy is not None:
        feedback.pronunciation_accuracy = update_data.pronunciation_accuracy
    
    if update_data.suggestions is not None:
        feedback.suggestions = update_data.suggestions
    
    feedback.updated_at = datetime.now()
    
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    
    logger.info(f"更新練習回饋成功: {feedback_id}")
    
    return feedback


async def list_therapist_pending_practices(
    therapist_id: uuid.UUID,
    session: Session,
    skip: int = 0,
    limit: int = 10
) -> TherapistPendingPracticeListResponse:
    """
    取得治療師待分析的練習列表
    
    Args:
        therapist_id: 治療師ID
        session: 資料庫會話
        skip: 跳過記錄數
        limit: 限制記錄數
        
    Returns:
        待分析練習列表回應
    """
    # 查詢治療師的客戶
    from src.therapist.models import TherapistClient
    
    client_ids_stmt = select(TherapistClient.client_id).where(
        TherapistClient.therapist_id == therapist_id
    )
    client_ids = session.exec(client_ids_stmt).all()
    
    if not client_ids:
        return TherapistPendingPracticeListResponse(
            total=0,
            pending_practices=[]
        )
    
    # 查詢待分析的練習記錄
    base_conditions = [
        PracticeRecord.user_id.in_(client_ids),
        PracticeRecord.practice_status == PracticeStatus.COMPLETED,
        ~select(PracticeFeedback.feedback_id).where(
            PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id
        ).exists()
    ]
    
    # 查詢總數
    count_statement = select(func.count(PracticeRecord.practice_record_id)).where(
        and_(*base_conditions)
    )
    total = session.exec(count_statement).one()
    
    # 查詢記錄，包含用戶、章節和句子資訊
    statement = (
        select(PracticeRecord, User, Chapter, Sentence)
        .join(User, PracticeRecord.user_id == User.user_id)
        .join(Chapter, PracticeRecord.chapter_id == Chapter.chapter_id)
        .outerjoin(Sentence, PracticeRecord.sentence_id == Sentence.sentence_id)
        .where(and_(*base_conditions))
        .order_by(desc(PracticeRecord.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    results = session.exec(statement).all()
    
    # 轉換為回應格式
    pending_practices = []
    current_time = datetime.now()
    
    for practice_record, user, chapter, sentence in results:
        days_since_practice = (current_time - practice_record.created_at).days
        
        response = TherapistPendingPracticeResponse(
            practice_record_id=practice_record.practice_record_id,
            user_id=practice_record.user_id,
            user_name=user.name,
            chapter_id=practice_record.chapter_id,
            chapter_name=chapter.chapter_name,
            sentence_id=practice_record.sentence_id,
            sentence_content=sentence.content if sentence else None,
            sentence_name=sentence.sentence_name if sentence else None,
            audio_path=practice_record.audio_path,
            audio_duration=practice_record.audio_duration,
            created_at=practice_record.created_at,
            days_since_practice=days_since_practice
        )
        pending_practices.append(response)
    
    return TherapistPendingPracticeListResponse(
        total=total,
        pending_practices=pending_practices
    )


async def list_practice_feedbacks(
    user_id: uuid.UUID,
    session: Session,
    skip: int = 0,
    limit: int = 10
) -> PracticeFeedbackListResponse:
    """
    取得用戶的練習回饋列表
    
    Args:
        user_id: 用戶ID
        session: 資料庫會話
        skip: 跳過記錄數
        limit: 限制記錄數
        
    Returns:
        回饋列表回應
    """
    # 查詢總數
    count_statement = (
        select(func.count(PracticeFeedback.feedback_id))
        .join(PracticeRecord, PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id)
        .where(PracticeRecord.user_id == user_id)
    )
    total = session.exec(count_statement).one()
    
    # 查詢回饋，包含治療師資訊
    statement = (
        select(PracticeFeedback, User)
        .join(PracticeRecord, PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id)
        .join(User, PracticeFeedback.therapist_id == User.user_id)
        .where(PracticeRecord.user_id == user_id)
        .order_by(desc(PracticeFeedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    results = session.exec(statement).all()
    
    # 轉換為回應格式
    feedbacks = []
    for feedback, therapist in results:
        response = PracticeFeedbackResponse(
            feedback_id=feedback.feedback_id,
            practice_record_id=feedback.practice_record_id,
            therapist_id=feedback.therapist_id,
            content=feedback.content,
            pronunciation_accuracy=feedback.pronunciation_accuracy,
            suggestions=feedback.suggestions,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            therapist_name=therapist.name
        )
        feedbacks.append(response)
    
    return PracticeFeedbackListResponse(
        total=total,
        feedbacks=feedbacks
    )


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
        practice_record.practice_status = PracticeStatus.COMPLETED
        practice_record.updated_at = datetime.now()
        session.add(practice_record)
    
    session.delete(feedback)
    session.commit()
    
    logger.info(f"刪除練習回饋成功: {feedback_id}")
    
    return True
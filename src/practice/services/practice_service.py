"""
練習服務
處理練習記錄的建立、查詢、更新和刪除操作
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Session, select, and_, desc, func
from fastapi import HTTPException, status

from src.course.models import PracticeRecord, PracticeStatus, Sentence, Chapter, PracticeFeedback
from src.practice.schemas import (
    PracticeRecordCreate,
    PracticeRecordUpdate,
    PracticeRecordResponse,
    PracticeRecordListResponse,
    PracticeStatsResponse
)

logger = logging.getLogger(__name__)


async def create_practice_record(
    practice_data: PracticeRecordCreate,
    user_id: uuid.UUID,
    session: Session
) -> PracticeRecord:
    """
    建立新的練習記錄
    
    Args:
        practice_data: 練習記錄建立資料
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        建立的練習記錄
        
    Raises:
        HTTPException: 當章節不存在時
    """
    # 檢查章節是否存在
    chapter = session.get(Chapter, practice_data.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的章節不存在"
        )
    
    # 建立練習記錄（句子在上傳錄音時才指定）
    practice_record = PracticeRecord(
        user_id=user_id,
        chapter_id=practice_data.chapter_id,
        sentence_id=None,  # 上傳錄音時才指定
        begin_time=practice_data.begin_time or datetime.now(),
        practice_status=PracticeStatus.IN_PROGRESS
    )
    
    session.add(practice_record)
    session.commit()
    session.refresh(practice_record)
    
    logger.info(f"建立練習記錄成功: 用戶 {user_id}, 章節 {practice_data.chapter_id}")
    
    return practice_record


async def get_practice_record(
    practice_record_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session
) -> PracticeRecord:
    """
    取得練習記錄詳情
    
    Args:
        practice_record_id: 練習記錄ID
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        練習記錄
        
    Raises:
        HTTPException: 當練習記錄不存在或無權限時
    """
    statement = select(PracticeRecord).where(
        and_(
            PracticeRecord.practice_record_id == practice_record_id,
            PracticeRecord.user_id == user_id
        )
    )
    practice_record = session.exec(statement).first()
    
    if not practice_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習記錄不存在或無權限查看"
        )
    
    return practice_record


async def update_practice_record(
    practice_record_id: uuid.UUID,
    update_data: PracticeRecordUpdate,
    user_id: uuid.UUID,
    session: Session
) -> PracticeRecord:
    """
    更新練習記錄
    
    Args:
        practice_record_id: 練習記錄ID
        update_data: 更新資料
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        更新後的練習記錄
        
    Raises:
        HTTPException: 當練習記錄不存在或無權限時
    """
    practice_record = await get_practice_record(practice_record_id, user_id, session)
    
    # 更新欄位
    if update_data.practice_status is not None:
        practice_record.practice_status = update_data.practice_status
    
    if update_data.end_time is not None:
        practice_record.end_time = update_data.end_time
    
    practice_record.updated_at = datetime.now()
    
    session.add(practice_record)
    session.commit()
    session.refresh(practice_record)
    
    logger.info(f"更新練習記錄成功: {practice_record_id}")
    
    return practice_record


async def list_user_practice_records(
    user_id: uuid.UUID,
    session: Session,
    skip: int = 0,
    limit: int = 10,
    status_filter: Optional[PracticeStatus] = None
) -> PracticeRecordListResponse:
    """
    取得用戶的練習記錄列表
    
    Args:
        user_id: 用戶ID
        session: 資料庫會話
        skip: 跳過記錄數
        limit: 限制記錄數
        status_filter: 狀態篩選
        
    Returns:
        練習記錄列表回應
    """
    # 建構查詢條件
    conditions = [PracticeRecord.user_id == user_id]
    if status_filter:
        conditions.append(PracticeRecord.practice_status == status_filter)
    
    # 查詢總數
    count_statement = select(func.count(PracticeRecord.practice_record_id)).where(
        and_(*conditions)
    )
    total = session.exec(count_statement).one()
    
    # 查詢記錄，包含章節和句子資訊
    statement = (
        select(PracticeRecord, Chapter, Sentence)
        .join(Chapter, PracticeRecord.chapter_id == Chapter.chapter_id)
        .outerjoin(Sentence, PracticeRecord.sentence_id == Sentence.sentence_id)
        .where(and_(*conditions))
        .order_by(desc(PracticeRecord.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    results = session.exec(statement).all()
    
    # 轉換為回應格式
    practice_records = []
    for practice_record, chapter, sentence in results:
        response = PracticeRecordResponse(
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
            chapter_name=chapter.chapter_name,
            sentence_content=sentence.content if sentence else None,
            sentence_name=sentence.sentence_name if sentence else None
        )
        practice_records.append(response)
    
    return PracticeRecordListResponse(
        total=total,
        practice_records=practice_records
    )


async def delete_practice_record(
    practice_record_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session
) -> bool:
    """
    刪除練習記錄
    
    Args:
        practice_record_id: 練習記錄ID
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        是否成功刪除
        
    Raises:
        HTTPException: 當練習記錄不存在或無權限時
    """
    practice_record = await get_practice_record(practice_record_id, user_id, session)
    
    session.delete(practice_record)
    session.commit()
    
    logger.info(f"刪除練習記錄成功: {practice_record_id}")
    
    return True


async def get_user_practice_stats(
    user_id: uuid.UUID,
    session: Session
) -> PracticeStatsResponse:
    """
    取得用戶練習統計
    
    Args:
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        練習統計回應
    """
    # 總練習次數
    total_practices_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        PracticeRecord.user_id == user_id
    )
    total_practices = session.exec(total_practices_stmt).one()
    
    # 總練習時長
    duration_stmt = select(func.sum(PracticeRecord.audio_duration)).where(
        and_(
            PracticeRecord.user_id == user_id,
            PracticeRecord.audio_duration.isnot(None)
        )
    )
    total_duration = session.exec(duration_stmt).one() or 0.0
    
    # 已完成的句子數（去重）
    completed_sentences_stmt = select(func.count(func.distinct(PracticeRecord.sentence_id))).where(
        and_(
            PracticeRecord.user_id == user_id,
            PracticeRecord.practice_status == PracticeStatus.COMPLETED
        )
    )
    completed_sentences = session.exec(completed_sentences_stmt).one()
    
    # 待回饋數量
    pending_feedback_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        and_(
            PracticeRecord.user_id == user_id,
            PracticeRecord.practice_status == PracticeStatus.COMPLETED,
            ~select(PracticeFeedback.feedback_id).where(
                PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id
            ).exists()
        )
    )
    pending_feedback = session.exec(pending_feedback_stmt).one()
    
    # 近期練習數（過去7天）
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_practices_stmt = select(func.count(PracticeRecord.practice_record_id)).where(
        and_(
            PracticeRecord.user_id == user_id,
            PracticeRecord.created_at >= seven_days_ago
        )
    )
    recent_practices = session.exec(recent_practices_stmt).one()
    
    # 平均準確度（從回饋中計算）
    avg_accuracy_stmt = select(func.avg(PracticeFeedback.pronunciation_accuracy)).join(
        PracticeRecord, PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id
    ).where(
        and_(
            PracticeRecord.user_id == user_id,
            PracticeFeedback.pronunciation_accuracy.isnot(None)
        )
    )
    average_accuracy = session.exec(avg_accuracy_stmt).one()
    
    return PracticeStatsResponse(
        total_practices=total_practices,
        total_duration=total_duration,
        average_accuracy=average_accuracy,
        completed_sentences=completed_sentences,
        pending_feedback=pending_feedback,
        recent_practices=recent_practices,
        # AI 分析相關統計 - 暫時設為預設值，等待 AI 分析功能完整實作
        total_ai_analyses=0,
        pending_ai_analyses=0,
        completed_ai_analyses=0,
        failed_ai_analyses=0,
        average_ai_processing_time=None
    )


async def update_practice_audio_info(
    practice_record_id: uuid.UUID,
    sentence_id: uuid.UUID,
    audio_path: str,
    audio_duration: Optional[float],
    file_size: int,
    content_type: str,
    session: Session
) -> PracticeRecord:
    """
    更新練習記錄的音訊資訊
    
    Args:
        practice_record_id: 練習記錄ID
        sentence_id: 句子ID
        audio_path: 音訊檔案路徑
        audio_duration: 音訊時長
        file_size: 檔案大小
        content_type: 檔案類型
        session: 資料庫會話
        
    Returns:
        更新後的練習記錄
        
    Raises:
        HTTPException: 當練習記錄不存在或句子不屬於該章節時
    """
    practice_record = session.get(PracticeRecord, practice_record_id)
    if not practice_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習記錄不存在"
        )
    
    # 驗證句子是否屬於該練習記錄的章節
    sentence = session.get(Sentence, sentence_id)
    if not sentence or sentence.chapter_id != practice_record.chapter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的句子不屬於該練習的章節"
        )
    
    practice_record.sentence_id = sentence_id
    practice_record.audio_path = audio_path
    practice_record.audio_duration = audio_duration
    practice_record.file_size = file_size
    practice_record.content_type = content_type
    practice_record.practice_status = PracticeStatus.COMPLETED
    practice_record.end_time = datetime.now()
    practice_record.updated_at = datetime.now()
    
    session.add(practice_record)
    session.commit()
    session.refresh(practice_record)
    
    logger.info(f"更新練習記錄音訊資訊成功: {practice_record_id}")
    
    return practice_record
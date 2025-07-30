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

from src.course.models import Sentence, Chapter, SpeakerRole
from src.practice.models import PracticeSession, PracticeRecord, PracticeSessionStatus, PracticeRecordStatus, PracticeFeedback
from src.practice.schemas import (
    PracticeRecordCreate,
    PracticeRecordUpdate,
    PracticeRecordResponse,
    PracticeRecordListResponse,
    PracticeStatsResponse
)

logger = logging.getLogger(__name__)


async def create_practice_session(
    practice_data: PracticeRecordCreate,  # 重用現有 schema，稍後會重新命名
    user_id: uuid.UUID,
    session: Session
) -> PracticeSession:
    """
    建立新的練習會話，同時為該章節的所有句子建立練習記錄
    
    Args:
        practice_data: 練習會話建立資料
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        建立的練習會話
        
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
    
    # 建立練習會話
    practice_session = PracticeSession(
        user_id=user_id,
        chapter_id=practice_data.chapter_id,
        begin_time=datetime.now(),
        session_status=PracticeSessionStatus.IN_PROGRESS
    )
    
    session.add(practice_session)
    session.commit()
    session.refresh(practice_session)
    
    # 取得該章節中，發話者為 client 的所有句子
    sentences_stmt = select(Sentence).where(
        and_(
            Sentence.chapter_id == practice_data.chapter_id,
            Sentence.speaker_role == SpeakerRole.SELF
        )
    )
    sentences = session.exec(sentences_stmt).all()
    
    # 為每個句子建立練習記錄
    practice_records = []
    for sentence in sentences:
        practice_record = PracticeRecord(
            practice_session_id=practice_session.practice_session_id,
            sentence_id=sentence.sentence_id,
            record_status=PracticeRecordStatus.PENDING
        )
        practice_records.append(practice_record)
        session.add(practice_record)
    
    session.commit()
    
    # 重新整理以取得完整的關聯資料
    session.refresh(practice_session)
    
    logger.info(f"建立練習會話成功: 用戶 {user_id}, 章節 {practice_data.chapter_id}, 包含 {len(practice_records)} 個句子")
    
    return practice_session


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
    # 通過 practice_session 來驗證使用者權限
    statement = (
        select(PracticeRecord)
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .where(
            and_(
                PracticeRecord.practice_record_id == practice_record_id,
                PracticeSession.user_id == user_id
            )
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
    
    # 更新欄位（需要調整為新的狀態欄位）
    if hasattr(update_data, 'record_status') and update_data.record_status is not None:
        practice_record.record_status = update_data.record_status
    
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
    status_filter: Optional[PracticeRecordStatus] = None,
    practice_session_id: Optional[uuid.UUID] = None
) -> PracticeRecordListResponse:
    """
    取得用戶的練習記錄列表
    
    Args:
        user_id: 用戶ID
        session: 資料庫會話
        skip: 跳過記錄數
        limit: 限制記錄數
        status_filter: 狀態篩選
        practice_session_id: 練習會話ID篩選（可選）
        
    Returns:
        練習記錄列表回應
    """
    # 建構查詢條件（通過 PracticeSession 過濾使用者）
    conditions = [PracticeSession.user_id == user_id]
    if status_filter:
        conditions.append(PracticeRecord.record_status == status_filter)
    if practice_session_id:
        conditions.append(PracticeSession.practice_session_id == practice_session_id)
    
    # 查詢總數
    count_statement = (
        select(func.count(PracticeRecord.practice_record_id))
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .where(and_(*conditions))
    )
    total = session.exec(count_statement).one()
    
    # 查詢記錄，包含會話、章節和句子資訊
    statement = (
        select(PracticeRecord, PracticeSession, Chapter, Sentence)
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .join(Chapter, PracticeSession.chapter_id == Chapter.chapter_id)
        .join(Sentence, PracticeRecord.sentence_id == Sentence.sentence_id)
        .where(and_(*conditions))
        .order_by(desc(PracticeRecord.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    results = session.exec(statement).all()
    
    # 轉換為回應格式
    practice_records = []
    for practice_record, practice_session, chapter, sentence in results:
        response = PracticeRecordResponse(
            practice_record_id=practice_record.practice_record_id,
            practice_session_id=practice_session.practice_session_id,
            user_id=practice_session.user_id,
            chapter_id=practice_session.chapter_id,
            sentence_id=practice_record.sentence_id,
            audio_path=practice_record.audio_path,
            audio_duration=practice_record.audio_duration,
            file_size=practice_record.file_size,
            content_type=practice_record.content_type,
            record_status=practice_record.record_status,
            recorded_at=practice_record.recorded_at,
            created_at=practice_record.created_at,
            updated_at=practice_record.updated_at,
            chapter_name=chapter.chapter_name,
            sentence_content=sentence.content,
            sentence_name=sentence.sentence_name
        )
        practice_records.append(response)
    
    return PracticeRecordListResponse(
        total=total,
        practice_records=practice_records
    )


async def list_practice_records_by_chapter(
    user_id: uuid.UUID,
    chapter_id: uuid.UUID,
    session: Session,
    skip: int = 0,
    limit: int = 10,
    status_filter: Optional[PracticeRecordStatus] = None
) -> PracticeRecordListResponse:
    """
    根據章節ID取得用戶的練習記錄列表
    
    Args:
        user_id: 用戶ID
        chapter_id: 章節ID
        session: 資料庫會話
        skip: 跳過記錄數
        limit: 限制記錄數
        status_filter: 狀態篩選
        
    Returns:
        練習記錄列表回應
    """
    # 建構查詢條件
    conditions = [
        PracticeSession.user_id == user_id,
        PracticeSession.chapter_id == chapter_id
    ]
    if status_filter:
        conditions.append(PracticeRecord.record_status == status_filter)
    
    # 查詢總數
    count_statement = (
        select(func.count(PracticeRecord.practice_record_id))
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .where(and_(*conditions))
    )
    total = session.exec(count_statement).one()
    
    # 查詢記錄，包含會話、章節和句子資訊
    statement = (
        select(PracticeRecord, PracticeSession, Chapter, Sentence)
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .join(Chapter, PracticeSession.chapter_id == Chapter.chapter_id)
        .join(Sentence, PracticeRecord.sentence_id == Sentence.sentence_id)
        .where(and_(*conditions))
        .order_by(desc(PracticeRecord.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    results = session.exec(statement).all()
    
    # 轉換為回應格式
    practice_records = []
    for practice_record, practice_session, chapter, sentence in results:
        response = PracticeRecordResponse(
            practice_record_id=practice_record.practice_record_id,
            practice_session_id=practice_record.practice_session_id,
            user_id=practice_session.user_id,
            chapter_id=practice_session.chapter_id,
            sentence_id=practice_record.sentence_id,
            audio_path=practice_record.audio_path,
            audio_duration=practice_record.audio_duration,
            file_size=practice_record.file_size,
            content_type=practice_record.content_type,
            record_status=practice_record.record_status,
            recorded_at=practice_record.recorded_at,
            created_at=practice_record.created_at,
            updated_at=practice_record.updated_at,
            chapter_name=chapter.chapter_name,
            sentence_content=sentence.content,
            sentence_name=sentence.sentence_name
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
    # 總練習次數（練習會話數）
    total_practices_stmt = select(func.count(PracticeSession.practice_session_id)).where(
        PracticeSession.user_id == user_id
    )
    total_practices = session.exec(total_practices_stmt).one()
    
    # 總練習時長（從錄音記錄統計）
    duration_stmt = (
        select(func.sum(PracticeRecord.audio_duration))
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeRecord.audio_duration.isnot(None)
            )
        )
    )
    total_duration = session.exec(duration_stmt).one() or 0.0
    
    # 已完成的句子數（已錄音的句子數）
    completed_sentences_stmt = (
        select(func.count(func.distinct(PracticeRecord.sentence_id)))
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeRecord.record_status.in_([PracticeRecordStatus.RECORDED, PracticeRecordStatus.AI_QUEUED, PracticeRecordStatus.AI_PROCESSING, PracticeRecordStatus.AI_ANALYZED, PracticeRecordStatus.ANALYZED])
            )
        )
    )
    completed_sentences = session.exec(completed_sentences_stmt).one()
    
    # 待回饋數量（已錄音但未有回饋的記錄）
    pending_feedback_stmt = (
        select(func.count(PracticeRecord.practice_record_id))
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeRecord.record_status.in_([PracticeRecordStatus.RECORDED, PracticeRecordStatus.AI_ANALYZED]),
                ~select(PracticeFeedback.feedback_id).where(
                    PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id
                ).exists()
            )
        )
    )
    pending_feedback = session.exec(pending_feedback_stmt).one()
    
    # 近期練習數（過去7天的練習會話數）
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_practices_stmt = select(func.count(PracticeSession.practice_session_id)).where(
        and_(
            PracticeSession.user_id == user_id,
            PracticeSession.created_at >= seven_days_ago
        )
    )
    recent_practices = session.exec(recent_practices_stmt).one()
    
    # 平均準確度（從回饋中計算）
    avg_accuracy_stmt = (
        select(func.avg(PracticeFeedback.pronunciation_accuracy))
        .join(PracticeRecord, PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id)
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeFeedback.pronunciation_accuracy.isnot(None)
            )
        )
    )
    average_accuracy = session.exec(avg_accuracy_stmt).one()
    
    return PracticeStatsResponse(
        total_practices=total_practices,
        total_duration=total_duration,
        average_accuracy=average_accuracy,
        completed_sentences=completed_sentences,
        pending_feedback=pending_feedback,
        recent_practices=recent_practices
    )


async def update_practice_audio_info(
    practice_record_id: uuid.UUID,
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
        audio_path: 音訊檔案路徑
        audio_duration: 音訊時長
        file_size: 檔案大小
        content_type: 檔案類型
        session: 資料庫會話
        
    Returns:
        更新後的練習記錄
        
    Raises:
        HTTPException: 當練習記錄不存在時
    """
    practice_record = session.get(PracticeRecord, practice_record_id)
    if not practice_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習記錄不存在"
        )
    
    # 更新音訊資訊
    practice_record.audio_path = audio_path
    practice_record.audio_duration = audio_duration
    practice_record.file_size = file_size
    practice_record.content_type = content_type
    practice_record.record_status = PracticeRecordStatus.RECORDED
    practice_record.recorded_at = datetime.now()
    practice_record.updated_at = datetime.now()
    
    session.add(practice_record)
    session.commit()
    session.refresh(practice_record)
    
    logger.info(f"更新練習記錄音訊資訊成功: {practice_record_id}")
    
    return practice_record



async def get_practice_session(
    practice_session_id: uuid.UUID,
    user_id: uuid.UUID,
    db_session: Session
) -> PracticeSession:
    """
    取得練習會話詳情
    
    Args:
        practice_session_id: 練習會話ID
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        練習會話
        
    Raises:
        HTTPException: 當練習會話不存在或無權限時
    """
    practice_session = db_session.exec(
        select(PracticeSession).where(
            and_(
                PracticeSession.practice_session_id == practice_session_id,
                PracticeSession.user_id == user_id
            )
        )
    ).first()
    
    if not practice_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="練習會話不存在或無權限查看"
        )
    
    return practice_session


async def complete_practice_session(
    practice_session_id: uuid.UUID,
    user_id: uuid.UUID,
    db_session: Session
) -> PracticeSession:
    """
    完成練習會話
    
    Args:
        practice_session_id: 練習會話ID
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        更新後的練習會話
    """

    practice_session = await get_practice_session(
        practice_session_id=practice_session_id,
        user_id=user_id,
        db_session=db_session
    )

    # 檢查是否有未完成的錄音
    pending_records_count = db_session.exec(
        select(func.count(PracticeRecord.practice_record_id)).where(
            and_(
                PracticeRecord.practice_session_id == practice_session_id,
                PracticeRecord.record_status == PracticeRecordStatus.PENDING
            )
        )
    ).one()
    
    if pending_records_count > 0:
        logger.warning(f"練習會話 {practice_session_id} 仍有 {pending_records_count} 個待錄音的句子")
    
    practice_session.session_status = PracticeSessionStatus.COMPLETED
    practice_session.end_time = datetime.now()
    
    # 計算總時長（如果有開始時間）
    if practice_session.begin_time:
        total_duration = (practice_session.end_time - practice_session.begin_time).total_seconds()
        practice_session.total_duration = int(total_duration)
    
    practice_session.updated_at = datetime.now()

    db_session.add(practice_session)
    db_session.commit()
    db_session.refresh(practice_session)

    logger.info(f"完成練習會話: {practice_session_id}")
    
    return practice_session


async def get_practice_session_records(
    practice_session_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session
) -> PracticeRecordListResponse:
    """
    取得練習會話的所有練習記錄
    
    Args:
        practice_session_id: 練習會話ID
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        練習記錄列表回應
        
    Raises:
        HTTPException: 當練習會話不存在或無權限時
    """
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(practice_session_id, user_id, session)
    
    # 查詢該會話的所有練習記錄，包含相關資訊
    statement = (
        select(PracticeRecord, PracticeSession, Chapter, Sentence)
        .join(PracticeSession, PracticeRecord.practice_session_id == PracticeSession.practice_session_id)
        .join(Chapter, PracticeSession.chapter_id == Chapter.chapter_id)
        .join(Sentence, PracticeRecord.sentence_id == Sentence.sentence_id)
        .where(PracticeRecord.practice_session_id == practice_session_id)
        .order_by(Sentence.start_time)  # 按句子順序排序
    )
    
    results = session.exec(statement).all()
    
    # 轉換為回應格式
    practice_records = []
    for practice_record, practice_session, chapter, sentence in results:
        response = PracticeRecordResponse(
            practice_record_id=practice_record.practice_record_id,
            practice_session_id=practice_session.practice_session_id,
            user_id=practice_session.user_id,
            chapter_id=practice_session.chapter_id,
            sentence_id=practice_record.sentence_id,
            audio_path=practice_record.audio_path,
            audio_duration=practice_record.audio_duration,
            file_size=practice_record.file_size,
            content_type=practice_record.content_type,
            record_status=practice_record.record_status,
            recorded_at=practice_record.recorded_at,
            created_at=practice_record.created_at,
            updated_at=practice_record.updated_at,
            chapter_name=chapter.chapter_name,
            sentence_content=sentence.content,
            sentence_name=sentence.sentence_name
        )
        practice_records.append(response)
    
    return PracticeRecordListResponse(
        total=len(practice_records),
        practice_records=practice_records
    )


async def delete_practice_session(
    practice_session_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session
) -> bool:
    """
    刪除練習會話及其所有相關記錄
    
    Args:
        practice_session_id: 練習會話ID
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        是否成功刪除
        
    Raises:
        HTTPException: 當練習會話不存在或無權限時
    """
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(practice_session_id, user_id, session)
    
    # 刪除相關的回饋記錄
    feedback_stmt = (
        select(PracticeFeedback)
        .join(PracticeRecord, PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id)
        .where(PracticeRecord.practice_session_id == practice_session_id)
    )
    feedbacks = session.exec(feedback_stmt).all()
    for feedback in feedbacks:
        session.delete(feedback)
    
    # 刪除練習記錄
    records_stmt = select(PracticeRecord).where(
        PracticeRecord.practice_session_id == practice_session_id
    )
    records = session.exec(records_stmt).all()
    for record in records:
        session.delete(record)
    
    # 刪除練習會話
    session.delete(practice_session)
    session.commit()
    
    logger.info(f"刪除練習會話成功: {practice_session_id}, 包含 {len(records)} 個練習記錄")
    
    return True


async def get_practice_record_by_session_and_sentence(
    practice_session_id: uuid.UUID,
    sentence_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session
) -> PracticeRecord:
    """
    通過練習會話ID和句子ID獲取練習記錄
    
    Args:
        practice_session_id: 練習會話ID
        sentence_id: 句子ID
        user_id: 用戶ID
        session: 資料庫會話
        
    Returns:
        練習記錄
        
    Raises:
        HTTPException: 當練習記錄不存在或無權限時
    """
    # 驗證練習會話存在且屬於當前用戶
    practice_session = await get_practice_session(practice_session_id, user_id, session)
    
    # 查找對應的練習記錄
    statement = select(PracticeRecord).where(
        and_(
            PracticeRecord.practice_session_id == practice_session_id,
            PracticeRecord.sentence_id == sentence_id
        )
    )
    practice_record = session.exec(statement).first()
    
    if not practice_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的練習記錄不存在"
        )
    
    return practice_record
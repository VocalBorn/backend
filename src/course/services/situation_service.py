import datetime
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select

from src.course.models import Situation
from src.course.schemas import SituationCreate, SituationUpdate, SituationListResponse, SituationResponse

async def create_situation(
    situation_data: SituationCreate,
    session: Session
) -> SituationResponse:
    """建立新情境"""
    situation = Situation(
        situation_name=situation_data.situation_name,
        description=situation_data.description,
        location=situation_data.location
    )
    
    session.add(situation)
    session.commit()
    session.refresh(situation)
    
    return SituationResponse(
        situation_id=situation.situation_id,
        situation_name=situation.situation_name,
        description=situation.description,
        location=situation.location,
        created_at=situation.created_at,
        updated_at=situation.updated_at
    )

async def get_situation(
    situation_id: str,
    session: Session
) -> SituationResponse:
    """取得特定情境"""
    situation = session.get(Situation, situation_id)
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    
    return SituationResponse(
        situation_id=situation.situation_id,
        situation_name=situation.situation_name,
        description=situation.description,
        location=situation.location,
        created_at=situation.created_at,
        updated_at=situation.updated_at
    )

async def list_situations(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None
) -> SituationListResponse:
    """取得情境列表"""
    query = select(Situation)
    
    if search:
        query = query.where(Situation.situation_name.contains(search))
    
    total = len(session.exec(query).all())
    situations = session.exec(query.offset(skip).limit(limit)).all()
    
    return SituationListResponse(
        total=total,
        situations=[
            SituationResponse(
                situation_id=situation.situation_id,
                situation_name=situation.situation_name,
                description=situation.description,
                location=situation.location,
                created_at=situation.created_at,
                updated_at=situation.updated_at
            )
            for situation in situations
        ]
    )

async def update_situation(
    situation_id: str,
    situation_data: SituationUpdate,
    session: Session
) -> SituationResponse:
    """更新情境"""
    situation = session.get(Situation, situation_id)
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    
    if situation_data.situation_name is not None:
        situation.situation_name = situation_data.situation_name
    if situation_data.description is not None:
        situation.description = situation_data.description
    if situation_data.location is not None:
        situation.location = situation_data.location
    
    situation.updated_at = datetime.datetime.now()
    session.add(situation)
    session.commit()
    session.refresh(situation)
    
    return SituationResponse(
        situation_id=situation.situation_id,
        situation_name=situation.situation_name,
        description=situation.description,
        location=situation.location,
        created_at=situation.created_at,
        updated_at=situation.updated_at
    )

async def delete_situation(
    situation_id: str,
    session: Session
):
    """刪除情境及其相關資料
    
    Args:
        situation_id: 要刪除的情境 ID
        session: 資料庫會話
        
    Raises:
        HTTPException: 當情境不存在時拋出 404 錯誤
        HTTPException: 當情境有關聯章節時拋出 400 錯誤
    """
    from src.course.services.deletion_utils import (
        get_practice_sessions_by_chapter_id,
        get_practice_records_by_sentence_id,
        delete_practice_sessions_and_related_data,
        delete_practice_records_and_related_data
    )
    
    situation = session.get(Situation, situation_id)
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    
    # 檢查是否有關聯的章節
    if situation.chapters and len(situation.chapters) > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete situation with existing chapters"
        )
    
    try:
        # 1. 遍歷所有章節，處理相關資料
        for chapter in situation.chapters:
            # 1.1. 取得章節的練習會話 ID 
            practice_session_ids = await get_practice_sessions_by_chapter_id(
                chapter.chapter_id, session
            )
            
            # 1.2. 刪除練習會話及其相關資料
            if practice_session_ids:
                await delete_practice_sessions_and_related_data(practice_session_ids, session)
            
            # 1.3. 處理可能存在的孤立練習記錄（針對該章節的句子）
            sentence_practice_record_ids = []
            for sentence in chapter.sentences:
                sentence_records = await get_practice_records_by_sentence_id(
                    sentence.sentence_id, session
                )
                sentence_practice_record_ids.extend(sentence_records)
            
            # 1.4. 刪除孤立的練習記錄
            if sentence_practice_record_ids:
                await delete_practice_records_and_related_data(sentence_practice_record_ids, session)
            
            # 1.5. 刪除章節的所有語句
            for sentence in chapter.sentences:
                session.delete(sentence)
            
            # 1.6. 刪除章節
            session.delete(chapter)
        
        # 2. 刪除情境本身
        session.delete(situation)
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"刪除情境失敗: {str(e)}"
        )

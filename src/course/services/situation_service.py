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
    """刪除情境"""
    situation = session.get(Situation, situation_id)
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    
    if situation.chapters:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete situation with existing chapters"
        )
    
    session.delete(situation)
    session.commit()

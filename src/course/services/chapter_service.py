import datetime
from typing import Optional, List
from fastapi import HTTPException
from sqlmodel import Session, select

from src.course.models import Chapter, Situation
from src.course.schemas import (
    ChapterCreate,
    ChapterUpdate,
    ChapterReorder,
    ChapterListResponse,
    ChapterResponse
)

async def create_chapter(
    situation_id: int,
    chapter_data: ChapterCreate,
    session: Session
) -> ChapterResponse:
    """建立新章節"""
    # 確認情境存在
    situation = session.get(Situation, situation_id)
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    
    chapter = Chapter(
        situation_id=situation_id,
        chapter_name=chapter_data.chapter_name,
        description=chapter_data.description,
        sequence_number=chapter_data.sequence_number,
        video_url=chapter_data.video_url
    )
    
    session.add(chapter)
    session.commit()
    session.refresh(chapter)
    
    return ChapterResponse(
        chapter_id=chapter.chapter_id,
        situation_id=chapter.situation_id,
        chapter_name=chapter.chapter_name,
        description=chapter.description,
        sequence_number=chapter.sequence_number,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
        video_url=chapter.video_url
    )

async def get_chapter(
    chapter_id: int,
    session: Session
) -> ChapterResponse:
    """取得特定章節"""
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    return ChapterResponse(
        chapter_id=chapter.chapter_id,
        situation_id=chapter.situation_id,
        chapter_name=chapter.chapter_name,
        description=chapter.description,
        sequence_number=chapter.sequence_number,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
        video_url=chapter.video_url
    )

async def list_chapters(
    session: Session,
    situation_id: int,
    skip: int = 0,
    limit: int = 10
) -> ChapterListResponse:
    """取得章節列表"""
    query = select(Chapter).where(Chapter.situation_id == situation_id).order_by(Chapter.sequence_number)
    
    total = len(session.exec(query).all())
    chapters = session.exec(query.offset(skip).limit(limit)).all()
    
    return ChapterListResponse(
        total=total,
        chapters=[
            ChapterResponse(
                chapter_id=chapter.chapter_id,
                situation_id=chapter.situation_id,
                chapter_name=chapter.chapter_name,
                description=chapter.description,
                sequence_number=chapter.sequence_number,
                created_at=chapter.created_at,
                updated_at=chapter.updated_at,
                video_url=chapter.video_url
            )
            for chapter in chapters
        ]
    )

async def update_chapter(
    chapter_id: int,
    chapter_data: ChapterUpdate,
    session: Session
) -> ChapterResponse:
    """更新章節"""
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if chapter_data.chapter_name is not None:
        chapter.chapter_name = chapter_data.chapter_name
    if chapter_data.description is not None:
        chapter.description = chapter_data.description
    if chapter_data.sequence_number is not None:
        chapter.sequence_number = chapter_data.sequence_number
    if chapter_data.video_url is not None:
        chapter.video_url = chapter_data.video_url
    
    chapter.updated_at = datetime.datetime.now()
    session.add(chapter)
    session.commit()
    session.refresh(chapter)
    
    return ChapterResponse(
        chapter_id=chapter.chapter_id,
        situation_id=chapter.situation_id,
        chapter_name=chapter.chapter_name,
        description=chapter.description,
        sequence_number=chapter.sequence_number,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
        video_url=chapter.video_url
    )

async def delete_chapter(
    chapter_id: int,
    session: Session
):
    """刪除章節"""
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if chapter.sentences:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete chapter with existing sentences"
        )
    
    session.delete(chapter)
    session.commit()

async def reorder_chapters(
    situation_id: int,
    reorder_data: ChapterReorder,
    session: Session
):
    """重新排序章節"""
    # 確認情境存在
    situation = session.get(Situation, situation_id)
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    
    # 取得所有要重新排序的章節
    chapter_ids = [order.chapter_id for order in reorder_data.chapter_orders]
    chapters = session.exec(
        select(Chapter).where(
            Chapter.chapter_id.in_(chapter_ids),
            Chapter.situation_id == situation_id
        )
    ).all()
    
    # 確認所有章節都存在且屬於同一情境
    if len(chapters) != len(chapter_ids):
        raise HTTPException(status_code=400, detail="Invalid chapter IDs provided")
    
    # 更新序號
    for order in reorder_data.chapter_orders:
        chapter = next(c for c in chapters if c.chapter_id == order.chapter_id)
        chapter.sequence_number = order.sequence_number
        chapter.updated_at = datetime.datetime.now()
        session.add(chapter)
    
    session.commit()

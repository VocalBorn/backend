import datetime
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select

from src.course.models import Sentence, Chapter
from src.course.schemas import (
    SentenceCreate,
    SentenceUpdate,
    SentenceListResponse,
    SentenceResponse
)

async def create_sentence(
    chapter_id: str,
    sentence_data: SentenceCreate,
    session: Session
) -> SentenceResponse:
    """建立新語句"""
    # 確認章節存在
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    sentence = Sentence(
        chapter_id=chapter_id,
        sentence_name=sentence_data.sentence_name,
        speaker_role=sentence_data.speaker_role,
        role_description=sentence_data.role_description,
        content=sentence_data.content,
        start_time=sentence_data.start_time,
        end_time=sentence_data.end_time
    )
    
    session.add(sentence)
    session.commit()
    session.refresh(sentence)
    
    return SentenceResponse(
        sentence_id=sentence.sentence_id,
        chapter_id=sentence.chapter_id,
        sentence_name=sentence.sentence_name,
        speaker_role=sentence.speaker_role,
        content=sentence.content,
        created_at=sentence.created_at,
        role_description=sentence.role_description,
        updated_at=sentence.updated_at,
        start_time=sentence.start_time,
        end_time=sentence.end_time
    )

async def get_sentence(
    sentence_id: str,
    session: Session
) -> SentenceResponse:
    """取得特定語句"""
    sentence = session.get(Sentence, sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    return SentenceResponse(
        sentence_id=sentence.sentence_id,
        chapter_id=sentence.chapter_id,
        sentence_name=sentence.sentence_name,
        speaker_role=sentence.speaker_role,
        content=sentence.content,
        created_at=sentence.created_at,
        role_description=sentence.role_description,
        updated_at=sentence.updated_at,
        start_time=sentence.start_time,
        end_time=sentence.end_time
    )

async def list_sentences(
    session: Session,
    chapter_id: str,
    skip: int = 0,
    limit: int = 10
) -> SentenceListResponse:
    """取得語句列表"""
    query = select(Sentence).where(Sentence.chapter_id == chapter_id)
    
    total = len(session.exec(query).all())
    sentences = session.exec(query.offset(skip).limit(limit)).all()
    
    return SentenceListResponse(
        total=total,
        sentences=[
            SentenceResponse(
                sentence_id=sentence.sentence_id,
                chapter_id=sentence.chapter_id,
                sentence_name=sentence.sentence_name,
                speaker_role=sentence.speaker_role,
                content=sentence.content,
                created_at=sentence.created_at,
                role_description=sentence.role_description,
                updated_at=sentence.updated_at,
                start_time=sentence.start_time,
                end_time=sentence.end_time
            )
            for sentence in sentences
        ]
    )

async def update_sentence(
    sentence_id: str,
    sentence_data: SentenceUpdate,
    session: Session
) -> SentenceResponse:
    """更新語句"""
    sentence = session.get(Sentence, sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    if sentence_data.sentence_name is not None:
        sentence.sentence_name = sentence_data.sentence_name
    if sentence_data.speaker_role is not None:
        sentence.speaker_role = sentence_data.speaker_role
    if sentence_data.content is not None:
        sentence.content = sentence_data.content
    if sentence_data.start_time is not None:
        sentence.start_time = sentence_data.start_time
    if sentence_data.end_time is not None:
        sentence.end_time = sentence_data.end_time
    
    sentence.updated_at = datetime.datetime.now()
    session.add(sentence)
    session.commit()
    session.refresh(sentence)
    
    return SentenceResponse(
        sentence_id=sentence.sentence_id,
        chapter_id=sentence.chapter_id,
        sentence_name=sentence.sentence_name,
        speaker_role=sentence.speaker_role,
        content=sentence.content,
        created_at=sentence.created_at,
        role_description=sentence.role_description,
        updated_at=sentence.updated_at,
        start_time=sentence.start_time,
        end_time=sentence.end_time
    )

async def delete_sentence(
    sentence_id: str,
    session: Session
):
    """刪除語句"""
    sentence = session.get(Sentence, sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    session.delete(sentence)
    session.commit()

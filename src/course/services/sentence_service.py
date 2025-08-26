import datetime
from typing import Optional
from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from src.course.models import Sentence, Chapter
from src.course.schemas import (
    SentenceCreate,
    SentenceUpdate,
    SentenceListResponse,
    SentenceResponse,
    SentenceAudioUploadResponse
)
from src.storage.audio_storage_service import AudioStorageService

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
        end_time=sentence.end_time,
        example_audio_path=sentence.example_audio_path,
        example_audio_duration=sentence.example_audio_duration,
        example_file_size=sentence.example_file_size,
        example_content_type=sentence.example_content_type
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
        end_time=sentence.end_time,
        example_audio_path=sentence.example_audio_path,
        example_audio_duration=sentence.example_audio_duration,
        example_file_size=sentence.example_file_size,
        example_content_type=sentence.example_content_type
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
                end_time=sentence.end_time,
                example_audio_path=sentence.example_audio_path,
                example_audio_duration=sentence.example_audio_duration,
                example_file_size=sentence.example_file_size,
                example_content_type=sentence.example_content_type
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
    if sentence_data.example_audio_path is not None:
        sentence.example_audio_path = sentence_data.example_audio_path
    if sentence_data.example_audio_duration is not None:
        sentence.example_audio_duration = sentence_data.example_audio_duration
    if sentence_data.example_file_size is not None:
        sentence.example_file_size = sentence_data.example_file_size
    if sentence_data.example_content_type is not None:
        sentence.example_content_type = sentence_data.example_content_type
    
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
        end_time=sentence.end_time,
        example_audio_path=sentence.example_audio_path,
        example_audio_duration=sentence.example_audio_duration,
        example_file_size=sentence.example_file_size,
        example_content_type=sentence.example_content_type
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

async def upload_sentence_example_audio(
    sentence_id: str,
    file: UploadFile,
    audio_storage_service: AudioStorageService,
    session: Session
) -> SentenceAudioUploadResponse:
    """為語句上傳範例音訊"""
    # 確認語句存在並取得相關資訊
    sentence = session.get(Sentence, sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    # 取得章節和情境資訊以構建音訊路徑
    chapter = session.get(Chapter, sentence.chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    try:
        # 使用音訊儲存服務上傳檔案
        audio_path = audio_storage_service.upload_course_audio(
            file=file,
            course_id=str(chapter.situation_id),  # 使用 situation_id 作為 course_id
            chapter_id=str(sentence.chapter_id),
            sentence_id=str(sentence.sentence_id)
        )
        
        # 更新語句的音訊資訊
        sentence.example_audio_path = audio_path
        sentence.example_audio_duration = None  # 可在後續版本中實作音訊時長解析
        sentence.example_file_size = file.size
        sentence.example_content_type = file.content_type
        sentence.updated_at = datetime.datetime.now()
        
        session.add(sentence)
        session.commit()
        session.refresh(sentence)
        
        return SentenceAudioUploadResponse(
            sentence_id=sentence.sentence_id,
            audio_path=audio_path,
            audio_duration=sentence.example_audio_duration,
            file_size=sentence.example_file_size,
            content_type=sentence.example_content_type,
            message="範例音訊上傳成功"
        )
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"音訊上傳失敗: {str(e)}"
        )


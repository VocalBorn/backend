from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database import get_session
from src.course.schemas import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    ChapterCreate,
    ChapterUpdate,
    ChapterReorder,
    ChapterResponse,
    ChapterListResponse,
    SentenceCreate,
    SentenceUpdate,
    SentenceResponse,
    SentenceListResponse
)
from src.course.services.course_service import (
    create_course,
    get_course,
    list_courses,
    update_course,
    delete_course
)
from src.course.services.chapter_service import (
    create_chapter,
    get_chapter,
    list_chapters,
    update_chapter,
    delete_chapter,
    reorder_chapters
)
from src.course.services.sentence_service import (
    create_sentence,
    get_sentence,
    list_sentences,
    update_sentence,
    delete_sentence
)

router = APIRouter(
    prefix='/course',
    tags=['courses']
)

# 課程相關路由
@router.get('/list', response_model=CourseListResponse)
async def list_courses_route(
    session: Annotated[Session, Depends(get_session)],
    skip: int = 0,
    limit: int = 10,
    search: str = None
):
    return await list_courses(session=session, skip=skip, limit=limit, search=search)

@router.get('/{course_id}', response_model=CourseResponse)
async def get_course_route(
    course_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    return await get_course(course_id, session)

@router.post('/create', response_model=CourseResponse)
async def create_course_route(
    course_data: CourseCreate,
    session: Annotated[Session, Depends(get_session)]
):
    return await create_course(course_data, session)

@router.patch('/{course_id}', response_model=CourseResponse)
async def update_course_route(
    course_id: int,
    course_data: CourseUpdate,
    session: Annotated[Session, Depends(get_session)]
):
    return await update_course(course_id, course_data, session)

@router.delete('/{course_id}')
async def delete_course_route(
    course_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    return await delete_course(course_id, session)

# 章節相關路由
@router.get('/{course_id}/chapter/list', response_model=ChapterListResponse)
async def list_chapters_route(
    course_id: int,
    session: Annotated[Session, Depends(get_session)],
    skip: int = 0,
    limit: int = 10
):
    return await list_chapters(session=session, course_id=course_id, skip=skip, limit=limit)

@router.get('/chapter/{chapter_id}', response_model=ChapterResponse)
async def get_chapter_route(
    chapter_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    return await get_chapter(chapter_id, session)

@router.post('/{course_id}/chapter/create', response_model=ChapterResponse)
async def create_chapter_route(
    course_id: int,
    chapter_data: ChapterCreate,
    session: Annotated[Session, Depends(get_session)]
):
    return await create_chapter(course_id, chapter_data, session)

@router.patch('/chapter/{chapter_id}', response_model=ChapterResponse)
async def update_chapter_route(
    chapter_id: int,
    chapter_data: ChapterUpdate,
    session: Annotated[Session, Depends(get_session)]
):
    return await update_chapter(chapter_id, chapter_data, session)

@router.delete('/chapter/{chapter_id}')
async def delete_chapter_route(
    chapter_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    return await delete_chapter(chapter_id, session)

@router.patch('/{course_id}/chapter/reorder')
async def reorder_chapters_route(
    course_id: int,
    reorder_data: ChapterReorder,
    session: Annotated[Session, Depends(get_session)]
):
    return await reorder_chapters(course_id, reorder_data, session)

# 語句相關路由
@router.get('/chapter/{chapter_id}/sentence/list', response_model=SentenceListResponse)
async def list_sentences_route(
    chapter_id: int,
    session: Annotated[Session, Depends(get_session)],
    skip: int = 0,
    limit: int = 10
):
    return await list_sentences(session=session, chapter_id=chapter_id, skip=skip, limit=limit)

@router.get('/sentence/{sentence_id}', response_model=SentenceResponse)
async def get_sentence_route(
    sentence_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    return await get_sentence(sentence_id, session)

@router.post('/chapter/{chapter_id}/sentence/create', response_model=SentenceResponse)
async def create_sentence_route(
    chapter_id: int,
    sentence_data: SentenceCreate,
    session: Annotated[Session, Depends(get_session)]
):
    return await create_sentence(chapter_id, sentence_data, session)

@router.patch('/sentence/{sentence_id}', response_model=SentenceResponse)
async def update_sentence_route(
    sentence_id: int,
    sentence_data: SentenceUpdate,
    session: Annotated[Session, Depends(get_session)]
):
    return await update_sentence(sentence_id, sentence_data, session)

@router.delete('/sentence/{sentence_id}')
async def delete_sentence_route(
    sentence_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    return await delete_sentence(sentence_id, session)

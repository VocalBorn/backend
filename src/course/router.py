from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.shared.database.database import get_session
from src.auth.services.jwt_service import verify_token
from src.auth.services.permission_service import (
    RequireViewCourses,
    RequireEditCourses,
    get_current_user
)

from src.course.schemas import (
    SituationCreate,
    SituationUpdate,
    SituationResponse,
    SituationListResponse,
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
from src.course.services.situation_service import (
    create_situation,
    get_situation,
    list_situations,
    update_situation,
    delete_situation
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
    prefix='/situations',
    tags=['situations']
)

@router.get(
    '/list', 
    response_model=SituationListResponse,
    summary="取得情境列表",
    description="""
    取得所有情境的列表，支援分頁和搜尋功能。
    此端點需要檢視課程權限。
    """
)
async def list_situations_route(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireViewCourses)],
    skip: int = 0,
    limit: int = 10,
    search: str = None
):
    return await list_situations(session=session, skip=skip, limit=limit, search=search)

@router.get(
    '/{situation_id}', 
    response_model=SituationResponse,
    summary="取得特定情境詳情",
    description="""
    根據情境 ID 取得特定情境的詳細資訊。
    此端點需要檢視課程權限。
    """
)
async def get_situation_route(
    situation_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireViewCourses)]
):
    return await get_situation(situation_id, session)

@router.post(
    '/create', 
    response_model=SituationResponse,
    summary="新增情境",
    description="""
    新增一個新的情境。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def create_situation_route(
    situation_data: SituationCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await create_situation(situation_data, session)

@router.patch(
    '/{situation_id}', 
    response_model=SituationResponse,
    summary="更新情境",
    description="""
    更新指定情境的資訊。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def update_situation_route(
    situation_id: str,
    situation_data: SituationUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await update_situation(situation_id, situation_data, session)

@router.delete(
    '/{situation_id}',
    summary="刪除情境",
    description="""
    刪除指定的情境。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def delete_situation_route(
    situation_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await delete_situation(situation_id, session)

# 章節相關路由
@router.get(
    '/{situation_id}/chapter/list', 
    response_model=ChapterListResponse,
    summary="取得章節列表",
    description="""
    取得指定情境下的所有章節列表，支援分頁。
    此端點需要檢視課程權限。
    """
)
async def list_chapters_route(
    situation_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireViewCourses)],
    skip: int = 0,
    limit: int = 10
):
    return await list_chapters(session=session, situation_id=situation_id, skip=skip, limit=limit)

@router.get(
    '/chapter/{chapter_id}', 
    response_model=ChapterResponse,
    summary="取得章節詳情",
    description="""
    根據章節 ID 取得特定章節的詳細資訊。
    此端點需要檢視課程權限。
    """
)
async def get_chapter_route(
    chapter_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireViewCourses)]
):
    return await get_chapter(chapter_id, session)

@router.post(
    '/{situation_id}/chapter/create', 
    response_model=ChapterResponse,
    summary="新增章節",
    description="""
    在指定情境下新增一個新的章節。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def create_chapter_route(
    situation_id: str,
    chapter_data: ChapterCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await create_chapter(situation_id, chapter_data, session)

@router.patch(
    '/chapter/{chapter_id}', 
    response_model=ChapterResponse,
    summary="更新章節",
    description="""
    更新指定章節的資訊。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def update_chapter_route(
    chapter_id: str,
    chapter_data: ChapterUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await update_chapter(chapter_id, chapter_data, session)

@router.delete(
    '/chapter/{chapter_id}',
    summary="刪除章節",
    description="""
    刪除指定的章節。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def delete_chapter_route(
    chapter_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await delete_chapter(chapter_id, session)

@router.patch(
    '/{situation_id}/chapter/reorder',
    summary="重新排序章節",
    description="""
    重新排序指定情境下的章節。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def reorder_chapters_route(
    situation_id: str,
    reorder_data: ChapterReorder,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await reorder_chapters(situation_id, reorder_data, session)

# 語句相關路由
@router.get(
    '/chapters/{chapter_id}/sentences', 
    response_model=SentenceListResponse,
    summary="取得語句列表",
    description="""
    取得指定章節下的所有語句列表，支援分頁。
    此端點需要檢視課程權限。
    """
)
async def list_sentences_route(
    chapter_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireViewCourses)],
    skip: int = 0,
    limit: int = 10
):
    return await list_sentences(session=session, chapter_id=chapter_id, skip=skip, limit=limit)

@router.get(
    '/sentence/{sentence_id}', 
    response_model=SentenceResponse,
    summary="取得語句詳情",
    description="""
    根據語句 ID 取得特定語句的詳細資訊。
    此端點需要檢視課程權限。
    """
)
async def get_sentence_route(
    sentence_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireViewCourses)]
):
    return await get_sentence(sentence_id, session)

@router.post(
    '/chapters/{chapter_id}/sentences', 
    response_model=SentenceResponse,
    summary="新增語句",
    description="""
    在指定章節下新增一個新的語句。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def create_sentence_route(
    chapter_id: str,
    sentence_data: SentenceCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await create_sentence(chapter_id, sentence_data, session)

@router.patch(
    '/sentence/{sentence_id}', 
    response_model=SentenceResponse,
    summary="更新語句",
    description="""
    更新指定語句的資訊。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def update_sentence_route(
    sentence_id: str,
    sentence_data: SentenceUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await update_sentence(sentence_id, sentence_data, session)

@router.delete(
    '/sentence/{sentence_id}',
    summary="刪除語句",
    description="""
    刪除指定的語句。
    此端點僅限於擁有編輯課程權限的管理員使用。
    """
)
async def delete_sentence_route(
    sentence_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated["User", Depends(RequireEditCourses)]
):
    return await delete_sentence(sentence_id, session)
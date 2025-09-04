"""
患者進度追蹤路由
提供練習進度統計和課程完成度查詢 API
"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User
from src.practice.schemas.progress import (
    RecentPracticeResponse,
    TotalSessionsResponse,
    CourseProgressResponse,
    UserProgressOverviewResponse
)
from src.practice.services.progress_service import (
    get_recent_practice_stats,
    get_total_practice_sessions,
    get_course_progress,
    get_user_progress_overview
)

# 設定日誌
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/practice/progress',
    tags=['practice-progress']
)


@router.get(
    "/recent",
    response_model=RecentPracticeResponse,
    summary="查詢近期練習統計",
    description="""
    取得使用者近期的練習統計資料，包含每日練習次數和完成情況。
    可指定統計天數，預設為7天。
    """
)
async def get_recent_practice(
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: Annotated[int, Query(description="統計天數", ge=1, le=30)] = 7
) -> RecentPracticeResponse:
    """查詢使用者近期練習統計"""
    try:
        return await get_recent_practice_stats(
            user_id=current_user.user_id,
            db_session=db_session,
            days=days
        )
    except Exception as e:
        logger.error(f"查詢近期練習統計失敗 - 使用者: {current_user.user_id}, 錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢近期練習統計失敗"
        )


@router.get(
    "/total-sessions",
    response_model=TotalSessionsResponse,
    summary="查詢總練習會話統計",
    description="""
    取得使用者所有練習會話的數量統計，包含各種狀態的會話數量。
    """
)
async def get_total_sessions(
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> TotalSessionsResponse:
    """查詢使用者總練習會話統計"""
    try:
        return await get_total_practice_sessions(
            user_id=current_user.user_id,
            db_session=db_session
        )
    except Exception as e:
        logger.error(f"查詢總練習會話統計失敗 - 使用者: {current_user.user_id}, 錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢總練習會話統計失敗"
        )


@router.get(
    "/courses",
    response_model=CourseProgressResponse,
    summary="查詢課程進度統計",
    description="""
    取得使用者的課程進度統計，包含總課程數、已完成課程數及完成百分比。
    課程完成度以是否有完成該章節的練習會話為準。
    """
)
async def get_courses_progress(
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> CourseProgressResponse:
    """查詢使用者課程進度統計"""
    try:
        return await get_course_progress(
            user_id=current_user.user_id,
            db_session=db_session
        )
    except Exception as e:
        logger.error(f"查詢課程進度統計失敗 - 使用者: {current_user.user_id}, 錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢課程進度統計失敗"
        )


@router.get(
    "/overview",
    response_model=UserProgressOverviewResponse,
    summary="查詢使用者進度總覽",
    description="""
    取得使用者的完整進度總覽，包含近期練習、總會話統計和課程進度。
    可指定近期統計的天數，預設為7天。
    """
)
async def get_progress_overview(
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    recent_days: Annotated[int, Query(description="近期統計天數", ge=1, le=30)] = 7
) -> UserProgressOverviewResponse:
    """查詢使用者進度總覽"""
    try:
        return await get_user_progress_overview(
            user_id=current_user.user_id,
            db_session=db_session,
            recent_days=recent_days
        )
    except Exception as e:
        logger.error(f"查詢使用者進度總覽失敗 - 使用者: {current_user.user_id}, 錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢使用者進度總覽失敗"
        )
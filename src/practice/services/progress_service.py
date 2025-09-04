"""
患者進度追蹤服務
提供練習進度統計和課程完成度查詢功能
"""

import datetime
import logging
from typing import List, Optional
import uuid
from sqlmodel import Session, select, func, and_, desc, distinct

from src.practice.models import PracticeSession, PracticeSessionStatus
from src.course.models import Chapter
from src.practice.schemas.progress import (
    DailyPracticeStats,
    RecentPracticeResponse,
    TotalSessionsResponse,
    CourseProgressResponse,
    UserProgressOverviewResponse
)

logger = logging.getLogger(__name__)


async def get_recent_practice_stats(
    user_id: uuid.UUID,
    db_session: Session,
    days: int = 7
) -> RecentPracticeResponse:
    """
    取得使用者近期練習統計資料

    Args:
        user_id: 使用者ID
        db_session: 資料庫會話
        days: 統計天數，預設7天

    Returns:
        RecentPracticeResponse: 近期練習統計資料

    Raises:
        Exception: 當資料庫查詢失敗時
    """
    try:
        # 計算開始日期
        start_date = datetime.date.today() - datetime.timedelta(days=days)
        
        # 查詢近期的練習會話
        statement = (
            select(PracticeSession)
            .where(
                and_(
                    PracticeSession.user_id == user_id,
                    func.date(PracticeSession.created_at) >= start_date
                )
            )
            .order_by(desc(PracticeSession.created_at))
        )
        
        sessions = db_session.exec(statement).all()
        
        # 統計總數據
        total_sessions = len(sessions)
        completed_sessions = sum(
            1 for session in sessions 
            if session.session_status == PracticeSessionStatus.COMPLETED
        )
        total_duration = sum(
            session.total_duration or 0 for session in sessions
            if session.session_status == PracticeSessionStatus.COMPLETED
        )
        
        # 建立每日統計
        daily_stats_dict = {}
        for session in sessions:
            session_date = session.created_at.date()
            if session_date not in daily_stats_dict:
                daily_stats_dict[session_date] = {
                    'session_count': 0,
                    'completed_sessions': 0,
                    'total_duration': 0
                }
            
            daily_stats_dict[session_date]['session_count'] += 1
            if session.session_status == PracticeSessionStatus.COMPLETED:
                daily_stats_dict[session_date]['completed_sessions'] += 1
                daily_stats_dict[session_date]['total_duration'] += (session.total_duration or 0)
        
        # 轉換為回應格式
        daily_stats = [
            DailyPracticeStats(
                date=date,
                session_count=stats['session_count'],
                completed_sessions=stats['completed_sessions'],
                total_duration=stats['total_duration'] if stats['total_duration'] > 0 else None
            )
            for date, stats in sorted(daily_stats_dict.items(), reverse=True)
        ]
        
        return RecentPracticeResponse(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            total_duration=total_duration if total_duration > 0 else None,
            daily_stats=daily_stats
        )
        
    except Exception as e:
        logger.error(f"查詢近期練習統計失敗 - 使用者ID: {user_id}, 錯誤: {e}")
        raise


async def get_total_practice_sessions(
    user_id: uuid.UUID,
    db_session: Session
) -> TotalSessionsResponse:
    """
    取得使用者總練習會話統計

    Args:
        user_id: 使用者ID
        db_session: 資料庫會話

    Returns:
        TotalSessionsResponse: 總練習會話統計

    Raises:
        Exception: 當資料庫查詢失敗時
    """
    try:
        # 查詢各種狀態的會話數量
        total_stmt = select(func.count(PracticeSession.practice_session_id)).where(
            PracticeSession.user_id == user_id
        )
        total_sessions = db_session.exec(total_stmt).one()
        
        completed_stmt = select(func.count(PracticeSession.practice_session_id)).where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeSession.session_status == PracticeSessionStatus.COMPLETED
            )
        )
        completed_sessions = db_session.exec(completed_stmt).one()
        
        in_progress_stmt = select(func.count(PracticeSession.practice_session_id)).where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeSession.session_status == PracticeSessionStatus.IN_PROGRESS
            )
        )
        in_progress_sessions = db_session.exec(in_progress_stmt).one()
        
        abandoned_stmt = select(func.count(PracticeSession.practice_session_id)).where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeSession.session_status == PracticeSessionStatus.ABANDONED
            )
        )
        abandoned_sessions = db_session.exec(abandoned_stmt).one()
        
        return TotalSessionsResponse(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            in_progress_sessions=in_progress_sessions,
            abandoned_sessions=abandoned_sessions
        )
        
    except Exception as e:
        logger.error(f"查詢總練習會話統計失敗 - 使用者ID: {user_id}, 錯誤: {e}")
        raise


async def get_course_progress(
    user_id: uuid.UUID,
    db_session: Session
) -> CourseProgressResponse:
    """
    取得使用者課程進度統計

    Args:
        user_id: 使用者ID
        db_session: 資料庫會話

    Returns:
        CourseProgressResponse: 課程進度統計

    Raises:
        Exception: 當資料庫查詢失敗時
    """
    try:
        # 查詢總課程數（章節數）
        total_courses_stmt = select(func.count(Chapter.chapter_id))
        total_courses = db_session.exec(total_courses_stmt).one()
        
        # 查詢使用者已完成的課程數
        # 當使用者對某個章節有至少一個已完成的練習會話時，視為該課程已完成
        completed_courses_stmt = (
            select(func.count(distinct(PracticeSession.chapter_id)))
            .where(
                and_(
                    PracticeSession.user_id == user_id,
                    PracticeSession.session_status == PracticeSessionStatus.COMPLETED
                )
            )
        )
        completed_courses = db_session.exec(completed_courses_stmt).one()
        
        # 計算完成百分比
        completion_percentage = (
            (completed_courses / total_courses * 100.0) 
            if total_courses > 0 else 0.0
        )
        
        return CourseProgressResponse(
            total_courses=total_courses,
            completed_courses=completed_courses,
            completion_percentage=round(completion_percentage, 2)
        )
        
    except Exception as e:
        logger.error(f"查詢課程進度統計失敗 - 使用者ID: {user_id}, 錯誤: {e}")
        raise


async def get_user_progress_overview(
    user_id: uuid.UUID,
    db_session: Session,
    recent_days: int = 7
) -> UserProgressOverviewResponse:
    """
    取得使用者進度總覽

    Args:
        user_id: 使用者ID
        db_session: 資料庫會話
        recent_days: 近期統計天數，預設7天

    Returns:
        UserProgressOverviewResponse: 使用者進度總覽

    Raises:
        Exception: 當資料庫查詢失敗時
    """
    try:
        # 並行查詢各項統計資料
        recent_practice = await get_recent_practice_stats(user_id, db_session, recent_days)
        total_sessions = await get_total_practice_sessions(user_id, db_session)
        course_progress = await get_course_progress(user_id, db_session)
        
        return UserProgressOverviewResponse(
            recent_practice=recent_practice,
            total_sessions=total_sessions,
            course_progress=course_progress
        )
        
    except Exception as e:
        logger.error(f"查詢使用者進度總覽失敗 - 使用者ID: {user_id}, 錯誤: {e}")
        raise
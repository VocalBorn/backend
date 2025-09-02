import datetime
import math
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select, and_, func, desc

from src.auth.models import Account, User
from src.checkin.models import DailyCheckIn
from src.checkin.schemas import (
    CheckInResponse,
    CheckInStatusResponse, 
    CheckInHistoryItem,
    CheckInHistoryResponse,
    CheckInStatisticsResponse
)


def _get_user_by_email(session: Session, email: str) -> User:
    """透過 email 取得使用者資料"""
    account = session.exec(
        select(Account).where(Account.email == email)
    ).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail="使用者不存在"
        )

    user = session.exec(
        select(User).where(User.account_id == account.account_id)
    ).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="使用者資料不存在"
        )
    
    return user


async def check_today_checkin_status(user_email: str, session: Session) -> CheckInStatusResponse:
    """檢查使用者今日簽到狀態
    
    Args:
        user_email: 使用者電子郵件
        session: 資料庫連線 session
        
    Returns:
        CheckInStatusResponse: 今日簽到狀態回應
    """
    user = _get_user_by_email(session, user_email)
    today = datetime.date.today()
    
    checkin_record = session.exec(
        select(DailyCheckIn).where(
            and_(
                DailyCheckIn.user_id == user.user_id,
                DailyCheckIn.checkin_date == today
            )
        )
    ).first()
    
    if checkin_record:
        return CheckInStatusResponse(
            has_checked_in_today=True,
            checkin_time=checkin_record.checkin_time,
            message="您今日已完成簽到"
        )
    else:
        return CheckInStatusResponse(
            has_checked_in_today=False,
            message="您今日尚未簽到"
        )


async def perform_daily_checkin(user_email: str, session: Session) -> CheckInResponse:
    """執行每日簽到
    
    Args:
        user_email: 使用者電子郵件
        session: 資料庫連線 session
        
    Returns:
        CheckInResponse: 簽到結果回應
        
    Raises:
        HTTPException: 當使用者今日已簽到時
    """
    user = _get_user_by_email(session, user_email)
    today = datetime.date.today()
    now = datetime.datetime.now()
    
    # 檢查今日是否已簽到
    existing_checkin = session.exec(
        select(DailyCheckIn).where(
            and_(
                DailyCheckIn.user_id == user.user_id,
                DailyCheckIn.checkin_date == today
            )
        )
    ).first()
    
    if existing_checkin:
        raise HTTPException(
            status_code=400,
            detail="您今日已完成簽到"
        )
    
    # 建立簽到記錄
    new_checkin = DailyCheckIn(
        user_id=user.user_id,
        checkin_date=today,
        checkin_time=now
    )
    
    session.add(new_checkin)
    session.commit()
    session.refresh(new_checkin)
    
    return CheckInResponse(
        success=True,
        message="簽到成功！",
        checkin_id=new_checkin.checkin_id,
        checkin_time=new_checkin.checkin_time
    )


async def get_checkin_history(
    user_email: str, 
    session: Session, 
    limit: int = 30, 
    offset: int = 0
) -> CheckInHistoryResponse:
    """取得使用者簽到歷史記錄
    
    Args:
        user_email: 使用者電子郵件
        session: 資料庫連線 session
        limit: 每頁筆數
        offset: 偏移量
        
    Returns:
        CheckInHistoryResponse: 簽到歷史記錄回應
    """
    user = _get_user_by_email(session, user_email)
    
    # 查詢總筆數
    total_count = session.exec(
        select(func.count(DailyCheckIn.checkin_id)).where(
            DailyCheckIn.user_id == user.user_id
        )
    ).one()
    
    # 查詢分頁資料
    checkin_records = session.exec(
        select(DailyCheckIn)
        .where(DailyCheckIn.user_id == user.user_id)
        .order_by(desc(DailyCheckIn.checkin_date))
        .offset(offset)
        .limit(limit)
    ).all()
    
    history_items = [
        CheckInHistoryItem(
            checkin_id=record.checkin_id,
            checkin_date=record.checkin_date,
            checkin_time=record.checkin_time
        )
        for record in checkin_records
    ]
    
    total_pages = math.ceil(total_count / limit) if limit > 0 else 1
    current_page = (offset // limit) + 1 if limit > 0 else 1
    
    return CheckInHistoryResponse(
        total_count=total_count,
        checkin_records=history_items,
        current_page=current_page,
        total_pages=total_pages
    )


async def get_checkin_statistics(user_email: str, session: Session) -> CheckInStatisticsResponse:
    """取得使用者簽到統計資料
    
    Args:
        user_email: 使用者電子郵件
        session: 資料庫連線 session
        
    Returns:
        CheckInStatisticsResponse: 簽到統計資料回應
    """
    user = _get_user_by_email(session, user_email)
    
    # 查詢總簽到天數
    total_checkin_days = session.exec(
        select(func.count(DailyCheckIn.checkin_id)).where(
            DailyCheckIn.user_id == user.user_id
        )
    ).one()
    
    # 查詢本月簽到天數
    today = datetime.date.today()
    first_day_of_month = today.replace(day=1)
    this_month_checkins = session.exec(
        select(func.count(DailyCheckIn.checkin_id)).where(
            and_(
                DailyCheckIn.user_id == user.user_id,
                DailyCheckIn.checkin_date >= first_day_of_month
            )
        )
    ).one()
    
    # 查詢最後簽到日期
    last_checkin = session.exec(
        select(DailyCheckIn)
        .where(DailyCheckIn.user_id == user.user_id)
        .order_by(desc(DailyCheckIn.checkin_date))
        .limit(1)
    ).first()
    
    last_checkin_date = last_checkin.checkin_date if last_checkin else None
    
    # 計算當前連續簽到天數和最長連續簽到天數
    current_streak, longest_streak = _calculate_streak_stats(user.user_id, session)
    
    return CheckInStatisticsResponse(
        total_checkin_days=total_checkin_days,
        current_streak=current_streak,
        longest_streak=longest_streak,
        this_month_checkins=this_month_checkins,
        last_checkin_date=last_checkin_date
    )


def _calculate_streak_stats(user_id: str, session: Session) -> tuple[int, int]:
    """計算連續簽到統計
    
    Args:
        user_id: 使用者 ID
        session: 資料庫連線 session
        
    Returns:
        tuple[int, int]: (當前連續簽到天數, 最長連續簽到天數)
    """
    # 查詢所有簽到記錄，按日期降序排列
    all_checkins = session.exec(
        select(DailyCheckIn.checkin_date)
        .where(DailyCheckIn.user_id == user_id)
        .order_by(desc(DailyCheckIn.checkin_date))
    ).all()
    
    if not all_checkins:
        return 0, 0
    
    # 計算當前連續簽到天數（從今天往前算）
    current_streak = 0
    today = datetime.date.today()
    expected_date = today
    
    for checkin_date in all_checkins:
        if checkin_date == expected_date:
            current_streak += 1
            expected_date = expected_date - datetime.timedelta(days=1)
        else:
            break
    
    # 計算最長連續簽到天數
    longest_streak = 0
    current_temp_streak = 0
    prev_date = None
    
    # 按日期升序重新排列來計算最長連續
    sorted_dates = sorted(all_checkins, reverse=False)
    
    for checkin_date in sorted_dates:
        if prev_date is None:
            current_temp_streak = 1
        elif checkin_date == prev_date + datetime.timedelta(days=1):
            current_temp_streak += 1
        else:
            longest_streak = max(longest_streak, current_temp_streak)
            current_temp_streak = 1
        
        prev_date = checkin_date
    
    # 確保最後一段連續也被計算到
    longest_streak = max(longest_streak, current_temp_streak)
    
    return current_streak, longest_streak
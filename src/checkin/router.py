from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.auth.services.jwt_service import verify_token
from src.shared.database.database import get_session
from src.checkin.schemas import (
    CheckInResponse,
    CheckInStatusResponse,
    CheckInHistoryResponse,
    CheckInStatisticsResponse
)
from src.checkin.services.checkin_service import (
    check_today_checkin_status,
    perform_daily_checkin,
    get_checkin_history,
    get_checkin_statistics
)

router = APIRouter(
    prefix='/checkin',
    tags=['checkin'],
    dependencies=[],
)


@router.post(
    '/daily',
    response_model=CheckInResponse,
    summary="每日簽到",
    description="""
    執行每日簽到功能。每個使用者每天只能簽到一次。
    需要用戶登入後才能使用此功能。
    """
)
async def daily_checkin(
    email: Annotated[str, Depends(verify_token)],
    session: Annotated[Session, Depends(get_session)]
) -> CheckInResponse:
    """執行每日簽到"""
    return await perform_daily_checkin(email, session)


@router.get(
    '/status',
    response_model=CheckInStatusResponse,
    summary="查詢今日簽到狀態",
    description="""
    查詢當前使用者今日是否已完成簽到。
    需要用戶登入後才能使用此功能。
    """
)
async def checkin_status(
    email: Annotated[str, Depends(verify_token)],
    session: Annotated[Session, Depends(get_session)]
) -> CheckInStatusResponse:
    """查詢今日簽到狀態"""
    return await check_today_checkin_status(email, session)


@router.get(
    '/history',
    response_model=CheckInHistoryResponse,
    summary="查詢簽到歷史記錄",
    description="""
    查詢使用者的簽到歷史記錄，支援分頁查詢。
    預設回傳最近 30 筆記錄，按簽到日期降序排列。
    需要用戶登入後才能使用此功能。
    """
)
async def checkin_history(
    email: Annotated[str, Depends(verify_token)],
    session: Annotated[Session, Depends(get_session)],
    limit: int = Query(default=30, description="每頁筆數", ge=1, le=100),
    offset: int = Query(default=0, description="偏移量", ge=0)
) -> CheckInHistoryResponse:
    """查詢簽到歷史記錄"""
    return await get_checkin_history(email, session, limit, offset)


@router.get(
    '/statistics',
    response_model=CheckInStatisticsResponse,
    summary="查詢簽到統計資料",
    description="""
    查詢使用者的簽到統計資料，包含：
    - 總簽到天數
    - 當前連續簽到天數
    - 最長連續簽到天數
    - 本月簽到天數
    - 最後簽到日期
    需要用戶登入後才能使用此功能。
    """
)
async def checkin_statistics(
    email: Annotated[str, Depends(verify_token)],
    session: Annotated[Session, Depends(get_session)]
) -> CheckInStatisticsResponse:
    """查詢簽到統計資料"""
    return await get_checkin_statistics(email, session)
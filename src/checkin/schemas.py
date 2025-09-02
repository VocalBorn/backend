import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel


class CheckInResponse(BaseModel):
    """簽到成功回應"""
    success: bool
    message: str
    checkin_id: uuid.UUID
    checkin_time: datetime.datetime


class CheckInStatusResponse(BaseModel):
    """今日簽到狀態回應"""
    has_checked_in_today: bool
    checkin_time: Optional[datetime.datetime] = None
    message: str


class CheckInHistoryItem(BaseModel):
    """單筆簽到記錄"""
    checkin_id: uuid.UUID
    checkin_date: datetime.date
    checkin_time: datetime.datetime


class CheckInHistoryResponse(BaseModel):
    """簽到歷史記錄回應"""
    total_count: int
    checkin_records: List[CheckInHistoryItem]
    current_page: int
    total_pages: int


class CheckInStatisticsResponse(BaseModel):
    """簽到統計資料回應"""
    total_checkin_days: int
    current_streak: int  # 當前連續簽到天數
    longest_streak: int  # 最長連續簽到天數
    this_month_checkins: int  # 本月簽到天數
    last_checkin_date: Optional[datetime.date] = None
import datetime
import uuid
from sqlmodel import Field, SQLModel, UniqueConstraint


class DailyCheckIn(SQLModel, table=True):
    """每日簽到記錄表"""
    __tablename__ = "daily_checkins"
    
    checkin_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    checkin_date: datetime.date = Field(nullable=False)
    checkin_time: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # 確保每個使用者每天只能簽到一次
    __table_args__ = (
        UniqueConstraint('user_id', 'checkin_date', name='unique_user_daily_checkin'),
    )
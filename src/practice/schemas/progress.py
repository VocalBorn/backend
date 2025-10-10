"""
患者進度追蹤相關 Schema 定義
"""

import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DailyPracticeStats(BaseModel):
    """每日練習統計"""
    date: datetime.date
    session_count: int
    completed_sessions: int
    total_duration: Optional[int] = None  # 總時長（秒）
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-01-15",
                "session_count": 3,
                "completed_sessions": 2,
                "total_duration": 1200
            }
        }
    )


class RecentPracticeResponse(BaseModel):
    """近期練習統計回應"""
    total_sessions: int
    completed_sessions: int
    total_duration: Optional[int] = None  # 總時長（秒）
    daily_stats: List[DailyPracticeStats]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_sessions": 15,
                "completed_sessions": 12,
                "total_duration": 7200,
                "daily_stats": [
                    {
                        "date": "2025-01-15",
                        "session_count": 3,
                        "completed_sessions": 2,
                        "total_duration": 1200
                    }
                ]
            }
        }
    )


class TotalSessionsResponse(BaseModel):
    """總練習會話數量回應"""
    total_sessions: int
    completed_sessions: int
    in_progress_sessions: int
    abandoned_sessions: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_sessions": 50,
                "completed_sessions": 42,
                "in_progress_sessions": 3,
                "abandoned_sessions": 5
            }
        }
    )


class CourseProgressResponse(BaseModel):
    """課程進度統計回應"""
    total_courses: int
    completed_courses: int
    completion_percentage: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_courses": 20,
                "completed_courses": 12,
                "completion_percentage": 60.0
            }
        }
    )


class UserProgressOverviewResponse(BaseModel):
    """使用者進度總覽回應"""
    recent_practice: RecentPracticeResponse
    total_sessions: TotalSessionsResponse
    course_progress: CourseProgressResponse
    avg_accuracy_last_30_days: Optional[float] = None  # 最近30天AI分析平均準確度 (0-100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recent_practice": {
                    "total_sessions": 15,
                    "completed_sessions": 12,
                    "total_duration": 7200,
                    "daily_stats": []
                },
                "total_sessions": {
                    "total_sessions": 50,
                    "completed_sessions": 42,
                    "in_progress_sessions": 3,
                    "abandoned_sessions": 5
                },
                "course_progress": {
                    "total_courses": 20,
                    "completed_courses": 12,
                    "completion_percentage": 60.0
                },
                "avg_accuracy_last_30_days": 85.5
            }
        }
    )
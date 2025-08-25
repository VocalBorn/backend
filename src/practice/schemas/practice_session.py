from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from src.practice.models import PracticeSessionStatus

# PracticeSession Schemas
class PracticeSessionCreate(BaseModel):
    """練習會話建立請求"""
    chapter_id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chapter_id": "550e8400-e29b-41d4-a716-446655440003"
            }
        }
    )

class PracticeSessionResponse(BaseModel):
    """練習會話回應"""
    practice_session_id: UUID
    user_id: UUID
    chapter_id: UUID
    session_status: PracticeSessionStatus
    begin_time: Optional[datetime]
    end_time: Optional[datetime]
    total_duration: Optional[int]
    created_at: datetime
    updated_at: datetime
    # 包含章節基本資訊
    chapter_name: Optional[str] = None
    # 進度統計
    total_sentences: int = 0
    completed_sentences: int = 0
    pending_sentences: int = 0
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440005",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "session_status": "in_progress",
                "begin_time": "2025-07-14T10:00:00.000Z",
                "end_time": None,
                "total_duration": None,
                "created_at": "2025-07-14T10:00:00.000Z",
                "updated_at": "2025-07-14T10:00:00.000Z",
                "chapter_name": "第一章：基本對話",
                "total_sentences": 5,
                "completed_sentences": 2,
                "pending_sentences": 3
            }
        }
    )

class PracticeSessionListResponse(BaseModel):
    """練習會話列表回應"""
    total: int
    practice_sessions: List[PracticeSessionResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 3,
                "practice_sessions": [{
                    "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                    "user_id": "550e8400-e29b-41d4-a716-446655440005",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "session_status": "completed",
                    "begin_time": "2025-07-14T10:00:00.000Z",
                    "end_time": "2025-07-14T10:30:00.000Z",
                    "total_duration": 1800,
                    "created_at": "2025-07-14T10:00:00.000Z",
                    "updated_at": "2025-07-14T10:30:00.000Z",
                    "chapter_name": "第一章：基本對話",
                    "total_sentences": 5,
                    "completed_sentences": 5,
                    "pending_sentences": 0
                }]
            }
        }
    )


class AIAnalysisTriggerResponse(BaseModel):
    """AI 分析任務觸發回應"""
    message: str
    practice_session_id: UUID
    tasks_created: int
    task_ids: List[UUID]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "成功觸發 AI 分析任務",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "tasks_created": 3,
                "task_ids": [
                    "550e8400-e29b-41d4-a716-446655440010",
                    "550e8400-e29b-41d4-a716-446655440011", 
                    "550e8400-e29b-41d4-a716-446655440012"
                ]
            }
        }
    )

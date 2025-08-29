from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class FeedbackFilters(BaseModel):
    """回饋篩選條件"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)
    chapter_id: Optional[UUID] = None
    therapist_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PaginationInfo(BaseModel):
    """分頁資訊"""
    current_page: int
    per_page: int
    total_items: int
    total_pages: int


class TherapistInfo(BaseModel):
    """治療師資訊"""
    therapist_id: UUID
    name: str
    specialties: List[str] = []
    years_experience: Optional[int] = None


class ChapterInfo(BaseModel):
    """章節資訊"""
    chapter_id: UUID
    chapter_name: str
    description: Optional[str] = None


class TherapistFeedbackDetail(BaseModel):
    """治療師回饋詳情"""
    content: str
    created_at: datetime


class PracticeRecordDetail(BaseModel):
    """練習記錄詳情"""
    practice_record_id: UUID
    sentence_content: str
    audio_path: Optional[str] = None
    audio_duration: Optional[float] = None
    recorded_at: Optional[datetime] = None


class PatientFeedbackListItem(BaseModel):
    """患者回饋列表項目"""
    session_feedback_id: UUID
    practice_session_id: UUID
    chapter_name: str
    therapist_name: str
    content: str
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_feedback_id": "550e8400-e29b-41d4-a716-446655440010",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "chapter_name": "基本對話",
                "therapist_name": "張治療師",
                "content": "整體表現良好，發音清晰度有明顯改善。",
                "created_at": "2025-07-30T14:30:00.000Z"
            }
        }
    )


class PaginatedFeedbackListResponse(BaseModel):
    """分頁回饋列表回應"""
    feedbacks: List[PatientFeedbackListItem]
    pagination: PaginationInfo

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feedbacks": [
                    {
                        "session_feedback_id": "550e8400-e29b-41d4-a716-446655440010",
                        "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                        "chapter_name": "基本對話",
                        "therapist_name": "張治療師",
                        "content": "整體表現良好，發音清晰度有明顯改善。",
                        "created_at": "2025-07-30T14:30:00.000Z"
                    }
                ],
                "pagination": {
                    "current_page": 1,
                    "per_page": 10,
                    "total_items": 25,
                    "total_pages": 3
                }
            }
        }
    )


class PatientFeedbackDetailResponse(BaseModel):
    """患者回饋詳情回應"""
    session_feedback_id: UUID
    practice_session_id: UUID
    chapter: ChapterInfo
    therapist: TherapistInfo
    therapist_feedback: TherapistFeedbackDetail
    practice_records: List[PracticeRecordDetail]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_feedback_id": "550e8400-e29b-41d4-a716-446655440010",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "chapter": {
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "chapter_name": "基本對話",
                    "description": "日常對話練習"
                },
                "therapist": {
                    "therapist_id": "550e8400-e29b-41d4-a716-446655440007",
                    "name": "張治療師",
                    "specialties": ["發音矯正", "語調訓練"],
                    "years_experience": 5
                },
                "therapist_feedback": {
                    "content": "整體表現良好，發音清晰度有明顯改善。建議在語調變化上多加練習。",
                    "created_at": "2025-07-30T14:30:00.000Z"
                },
                "practice_records": [
                    {
                        "practice_record_id": "550e8400-e29b-41d4-a716-446655440003",
                        "sentence_content": "你好，很高興見到你",
                        "audio_path": "/audio/path",
                        "audio_duration": 3.5,
                        "recorded_at": "2025-07-30T13:45:00.000Z"
                    }
                ]
            }
        }
    )
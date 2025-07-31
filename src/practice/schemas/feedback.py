from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

# PracticeFeedback Schemas
class PracticeFeedbackCreate(BaseModel):
    content: str
    pronunciation_accuracy: Optional[float] = None
    suggestions: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "發音清晰，但語調需要調整",
                "pronunciation_accuracy": 85.5,
                "suggestions": "建議多練習語調的起伏變化",
            }
        }
    )

class PracticeFeedbackUpdate(BaseModel):
    content: Optional[str] = None
    pronunciation_accuracy: Optional[float] = None
    suggestions: Optional[str] = None
    based_on_ai_analysis: Optional[bool] = None
    ai_analysis_reviewed: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "發音有明顯改善",
                "pronunciation_accuracy": 90.0,
                "suggestions": "繼續保持練習頻率",
                "ai_analysis_reviewed": True
            }
        }
    )

class PracticeFeedbackResponse(BaseModel):
    feedback_id: UUID
    practice_record_id: UUID
    therapist_id: UUID
    content: str
    pronunciation_accuracy: Optional[float]
    suggestions: Optional[str]
    created_at: datetime
    updated_at: datetime
    # 治療師基本資訊
    therapist_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feedback_id": "550e8400-e29b-41d4-a716-446655440006",
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "therapist_id": "550e8400-e29b-41d4-a716-446655440007",
                "content": "發音清晰，但語調需要調整",
                "pronunciation_accuracy": 85.5,
                "suggestions": "建議多練習語調的起伏變化",
                "created_at": "2025-05-01T06:15:00.000000",
                "updated_at": "2025-05-01T06:15:00.000000",
                "therapist_name": "張治療師"
            }
        }
    )

# 練習會話回饋相關 Schemas
class PracticeSessionFeedbackCreate(BaseModel):
    """練習會話回饋建立請求"""
    content: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "整體表現不錯，發音清晰度有明顯改善。建議在語調變化上多加練習，特別是疑問句的語調上揚。繼續保持練習頻率，相信會有更好的進步。"
            }
        }
    )

class PracticeSessionFeedbackUpdate(BaseModel):
    """練習會話回饋更新請求"""
    content: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "經過這次練習，發音準確度有顯著提升。語速控制得當，語調自然流暢。建議繼續練習類似的對話情境，鞏固學習成果。"
            }
        }
    )

class PracticeSessionFeedbackResponse(BaseModel):
    """練習會話回饋回應"""
    session_feedback_id: UUID
    practice_session_id: UUID
    therapist_id: UUID
    therapist_name: str
    patient_id: UUID
    patient_name: str
    chapter_id: UUID
    chapter_name: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_feedback_id": "550e8400-e29b-41d4-a716-446655440010",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "therapist_id": "550e8400-e29b-41d4-a716-446655440007",
                "therapist_name": "張治療師",
                "patient_id": "550e8400-e29b-41d4-a716-446655440005",
                "patient_name": "王小明",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "chapter_name": "基本對話",
                "content": "整體表現不錯，發音清晰度有明顯改善。建議在語調變化上多加練習，特別是疑問句的語調上揚。",
                "created_at": "2025-07-30T14:30:00.000Z",
                "updated_at": "2025-07-30T14:30:00.000Z"
            }
        }
    )

# 向後相容的舊 Schemas（棄用但保留）
class SentenceFeedbackItem(BaseModel):
    """單一語句回饋項目（棄用）"""
    sentence_id: UUID
    content: str
    pronunciation_accuracy: Optional[float] = None
    suggestions: Optional[str] = None

class SessionFeedbackCreate(BaseModel):
    """練習會話批量回饋建立請求（棄用）"""
    feedbacks: List[SentenceFeedbackItem]

class SessionFeedbackItemResponse(BaseModel):
    """練習會話單一語句回饋回應（棄用）"""
    feedback_id: UUID
    practice_record_id: UUID
    sentence_id: UUID
    sentence_content: str
    sentence_name: str
    content: str
    pronunciation_accuracy: Optional[float]
    suggestions: Optional[str]
    created_at: datetime
    updated_at: datetime

class SessionFeedbackResponse(BaseModel):
    """練習會話批量回饋回應（棄用）"""
    practice_session_id: UUID
    therapist_id: UUID
    therapist_name: str
    patient_id: UUID
    patient_name: str
    chapter_id: UUID
    chapter_name: str
    feedbacks: List[SessionFeedbackItemResponse]
    created_at: datetime

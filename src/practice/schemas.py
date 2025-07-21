from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from src.course.models import PracticeStatus, AIAnalysisQueueStatus, AIAnalysisPriority

# 錄音上傳相關 Schemas
class AudioUploadRequest(BaseModel):
    """音訊上傳請求參數"""
    sentence_id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003"
            }
        }
    )

class AudioUploadResponse(BaseModel):
    """音訊上傳回應"""
    recording_id: str
    object_name: str
    file_size: int
    content_type: str
    status: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recording_id": "550e8400-e29b-41d4-a716-446655440008",
                "object_name": "practice_recordings/user123/recording456.mp3",
                "file_size": 1024000,
                "content_type": "audio/mpeg",
                "status": "uploaded"
            }
        }
    )

# PracticeRecord Schemas
class PracticeRecordCreate(BaseModel):
    chapter_id: UUID
    begin_time: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chapter_id": "550e8400-e29b-41d4-a716-446655440003",
                "begin_time": "2025-07-14T10:00:00.000Z"
            }
        }
    )

class PracticeRecordUpdate(BaseModel):
    practice_status: Optional[PracticeStatus] = None
    end_time: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_status": "completed",
                "end_time": "2025-05-01T06:10:30.000000"
            }
        }
    )

class PracticeRecordResponse(BaseModel):
    practice_record_id: UUID
    user_id: UUID
    chapter_id: UUID
    sentence_id: Optional[UUID] = None
    audio_path: Optional[str]
    audio_duration: Optional[float]
    file_size: Optional[int]
    content_type: Optional[str]
    practice_status: PracticeStatus
    begin_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # 包含章節基本資訊
    chapter_name: Optional[str] = None
    # 包含句子基本資訊（如果已指定）
    sentence_content: Optional[str] = None
    sentence_name: Optional[str] = None
    
    # AI 分析相關資訊
    ai_analysis_status: Optional[AIAnalysisQueueStatus] = None
    ai_analysis_available: bool = False
    ai_queue_position: Optional[int] = None
    ai_estimated_wait_time: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "user_id": "550e8400-e29b-41d4-a716-446655440005",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "audio_path": "/storage/audio/user_recording_123.mp3",
                "audio_duration": 30.5,
                "file_size": 1024000,
                "content_type": "audio/mpeg",
                "practice_status": "completed",
                "begin_time": "2025-05-01T06:10:00.000000",
                "end_time": "2025-05-01T06:10:30.000000",
                "created_at": "2025-05-01T06:10:30.000000",
                "updated_at": "2025-05-01T06:10:30.000000",
                "chapter_name": "第一章：基本對話",
                "sentence_content": "我想要一份牛肉麵，不要太辣",
                "sentence_name": "基本點餐對話"
            }
        }
    )

# PracticeFeedback Schemas
class PracticeFeedbackCreate(BaseModel):
    content: str
    pronunciation_accuracy: Optional[float] = None
    suggestions: Optional[str] = None
    based_on_ai_analysis: bool = False
    ai_analysis_reviewed: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "發音清晰，但語調需要調整",
                "pronunciation_accuracy": 85.5,
                "suggestions": "建議多練習語調的起伏變化",
                "based_on_ai_analysis": True,
                "ai_analysis_reviewed": True
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
    based_on_ai_analysis: bool = False
    ai_analysis_reviewed: bool = False
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

# 練習統計相關 Schemas
class PracticeStatsResponse(BaseModel):
    total_practices: int
    total_duration: float  # 總練習時長（秒）
    average_accuracy: Optional[float]  # 平均準確度
    completed_sentences: int  # 已完成的句子數
    pending_feedback: int  # 待回饋數量
    recent_practices: int  # 近期練習數（過去7天）
    
    # AI 分析相關統計
    total_ai_analyses: int  # 總 AI 分析數
    pending_ai_analyses: int  # 待 AI 分析數
    completed_ai_analyses: int  # 已完成 AI 分析數
    failed_ai_analyses: int  # 失敗的 AI 分析數
    average_ai_processing_time: Optional[float] = None  # 平均 AI 處理時間

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_practices": 25,
                "total_duration": 1200.5,
                "average_accuracy": 88.5,
                "completed_sentences": 15,
                "pending_feedback": 3,
                "recent_practices": 8
            }
        }
    )

# List Response Schemas
class PracticeRecordListResponse(BaseModel):
    total: int
    practice_records: List[PracticeRecordResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "practice_records": [{
                    "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                    "user_id": "550e8400-e29b-41d4-a716-446655440005",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                    "audio_path": "/storage/audio/user_recording_123.mp3",
                    "audio_duration": 30.5,
                    "file_size": 1024000,
                    "content_type": "audio/mpeg",
                    "practice_status": "completed",
                    "begin_time": "2025-05-01T06:10:00.000000",
                    "end_time": "2025-05-01T06:10:30.000000",
                    "created_at": "2025-05-01T06:10:30.000000",
                    "updated_at": "2025-05-01T06:10:30.000000",
                    "chapter_name": "第一章：基本對話",
                    "sentence_content": "我想要一份牛肉麵，不要太辣",
                    "sentence_name": "基本點餐對話"
                }]
            }
        }
    )

class PracticeFeedbackListResponse(BaseModel):
    total: int
    feedbacks: List[PracticeFeedbackResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "feedbacks": [{
                    "feedback_id": "550e8400-e29b-41d4-a716-446655440006",
                    "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                    "therapist_id": "550e8400-e29b-41d4-a716-446655440007",
                    "content": "發音清晰，但語調需要調整",
                    "pronunciation_accuracy": 85.5,
                    "suggestions": "建議多練習語調的起伏變化",
                    "created_at": "2025-05-01T06:15:00.000000",
                    "updated_at": "2025-05-01T06:15:00.000000",
                    "therapist_name": "張治療師"
                }]
            }
        }
    )

# 治療師專用 Schemas
class TherapistPendingPracticeResponse(BaseModel):
    """治療師待分析練習回應"""
    practice_record_id: UUID
    user_id: UUID
    user_name: str
    chapter_id: UUID
    chapter_name: str
    sentence_id: Optional[UUID] = None
    sentence_content: Optional[str] = None
    sentence_name: Optional[str] = None
    audio_path: Optional[str]
    audio_duration: Optional[float]
    created_at: datetime
    days_since_practice: int  # 練習後經過天數

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "user_id": "550e8400-e29b-41d4-a716-446655440005",
                "user_name": "王小明",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "chapter_name": "第一章：基本對話",
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "sentence_content": "我想要一份牛肉麵，不要太辣",
                "sentence_name": "基本點餐對話",
                "audio_path": "/storage/audio/user_recording_123.mp3",
                "audio_duration": 30.5,
                "created_at": "2025-05-01T06:10:30.000000",
                "days_since_practice": 2
            }
        }
    )

class TherapistPendingPracticeListResponse(BaseModel):
    total: int
    pending_practices: List[TherapistPendingPracticeResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 5,
                "pending_practices": [{
                    "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                    "user_id": "550e8400-e29b-41d4-a716-446655440005",
                    "user_name": "王小明",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "chapter_name": "第一章：基本對話",
                    "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                    "sentence_content": "我想要一份牛肉麵，不要太辣",
                    "sentence_name": "基本點餐對話",
                    "audio_path": "/storage/audio/user_recording_123.mp3",
                    "audio_duration": 30.5,
                    "created_at": "2025-05-01T06:10:30.000000",
                    "days_since_practice": 2
                }]
            }
        }
    )
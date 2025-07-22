from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from src.practice.models import PracticeSessionStatus, PracticeRecordStatus

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

# === 會話記錄管理 Schemas ===
class RecordUpdateRequest(BaseModel):
    """練習記錄更新請求"""
    record_status: PracticeRecordStatus

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "record_status": "recorded"
            }
        }
    )

# === 會話錄音管理 Schemas ===
class RecordingResponse(BaseModel):
    """錄音檔案回應"""
    sentence_id: UUID
    audio_path: Optional[str]
    audio_duration: Optional[float]
    file_size: Optional[int]
    content_type: Optional[str]
    recorded_at: Optional[datetime]
    stream_url: Optional[str] = None  # 可播放的URL（如果有錄音）
    stream_expires_at: Optional[datetime] = None  # URL過期時間

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "audio_path": "/storage/audio/user_recording_123.mp3",
                "audio_duration": 30.5,
                "file_size": 1024000,
                "content_type": "audio/mpeg",
                "recorded_at": "2025-07-22T10:15:30.000Z",
                "stream_url": "https://minio.example.com/practice-recordings/presigned-url...",
                "stream_expires_at": "2025-07-22T11:15:30.000Z"
            }
        }
    )

class RecordingsListResponse(BaseModel):
    """會話所有錄音列表回應"""
    practice_session_id: UUID
    recordings: List[RecordingResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "recordings": [
                    {
                        "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                        "audio_path": "/storage/audio/user_recording_123.mp3",
                        "audio_duration": 30.5,
                        "file_size": 1024000,
                        "content_type": "audio/mpeg",
                        "recorded_at": "2025-07-22T10:15:30.000Z",
                        "stream_url": "https://minio.example.com/practice-recordings/presigned-url?expires=1642865730",
                        "stream_expires_at": "2025-07-22T11:15:30.000Z"
                    },
                    {
                        "sentence_id": "550e8400-e29b-41d4-a716-446655440004",
                        "audio_path": "null",
                        "audio_duration": "null",
                        "file_size": "null",
                        "content_type": "null",
                        "recorded_at": "null",
                        "stream_url": "null",
                        "stream_expires_at": "null"
                    }
                ]
            }
        }
    )


# PracticeRecord Schemas - 重新命名原有的為向後相容
PracticeRecordCreate = PracticeSessionCreate  # 向後相容性別名

class PracticeRecordUpdate(BaseModel):
    """練習記錄更新請求"""
    record_status: Optional[PracticeRecordStatus] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "record_status": "recorded"
            }
        }
    )

class PracticeRecordResponse(BaseModel):
    """練習記錄回應"""
    practice_record_id: UUID
    practice_session_id: UUID
    user_id: UUID
    chapter_id: UUID
    sentence_id: UUID  # 新結構中必須有句子ID
    audio_path: Optional[str]
    audio_duration: Optional[float]
    file_size: Optional[int]
    content_type: Optional[str]
    record_status: PracticeRecordStatus
    recorded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # 包含章節基本資訊
    chapter_name: Optional[str] = None
    # 包含句子基本資訊（必須有，確保不為空）
    sentence_content: str  # 改為必填，確保不為空
    sentence_name: str  # 改為必填，確保不為空
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440005",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "audio_path": "/storage/audio/user_recording_123.mp3",
                "audio_duration": 30.5,
                "file_size": 1024000,
                "content_type": "audio/mpeg",
                "record_status": "recorded",
                "recorded_at": "2025-05-01T06:10:30.000000",
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
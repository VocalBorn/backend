from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from src.practice.models import PracticeRecordStatus
from .practice_session import PracticeSessionCreate

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

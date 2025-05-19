from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID

from src.course.models import SpeakerRole

# Situation Schemas
class SituationCreate(BaseModel):
    situation_name: str
    description: Optional[str] = None
    location: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "situation_name": "餐廳用餐",
                "description": "在餐廳點餐、用餐和結帳的對話情境",
                "location": "餐廳"
            }
        }

class SituationUpdate(BaseModel):
    situation_name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "situation_name": "高級餐廳用餐",
                "description": "在高級餐廳點餐、用餐和結帳的對話情境",
                "location": "高級餐廳"
            }
        }

class SituationResponse(BaseModel):
    situation_id: UUID
    situation_name: str
    description: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "situation_id": "550e8400-e29b-41d4-a716-446655440000",
                "situation_name": "餐廳用餐",
                "description": "在餐廳點餐、用餐和結帳的對話情境",
                "location": "餐廳",
                "created_at": "2025-05-01T06:03:56.458985",
                "updated_at": "2025-05-01T06:03:56.459284"
            }
        }

# Chapter Schemas
class ChapterCreate(BaseModel):
    chapter_name: str
    description: Optional[str] = None
    sequence_number: int
    video_url: Optional[str] = None
    video_path: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_name": "餐廳點餐",
                "description": "學習在餐廳用餐時的常用對話，包含點餐、詢問菜品和結帳等情境",
                "sequence_number": 1,
                "video_url": "https://example.com/videos/restaurant_order.mp4",
            }
        }

class ChapterUpdate(BaseModel):
    chapter_name: Optional[str] = None
    description: Optional[str] = None
    sequence_number: Optional[int] = None
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    video_duration: Optional[float] = None
    video_format: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_name": "餐廳進階對話",
                "description": "學習更進階的餐廳對話，包含特殊需求和處理問題的情境",
                "sequence_number": 2,
                "video_url": "https://example.com/videos/restaurant_advanced.mp4",
            }
        }

class ChapterOrder(BaseModel):
    chapter_id: UUID
    sequence_number: int

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
                "sequence_number": 2
            }
        }

class ChapterReorder(BaseModel):
    chapter_orders: List[ChapterOrder]

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_orders": [
                    {"chapter_id": "550e8400-e29b-41d4-a716-446655440001", "sequence_number": 2},
                    {"chapter_id": "550e8400-e29b-41d4-a716-446655440002", "sequence_number": 1}
                ]
            }
        }

class ChapterResponse(BaseModel):
    chapter_id: UUID
    situation_id: UUID
    chapter_name: str
    description: Optional[str]
    sequence_number: int
    video_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
                "situation_id": "550e8400-e29b-41d4-a716-446655440000",
                "chapter_name": "餐廳點餐",
                "description": "學習在餐廳用餐時的常用對話，包含點餐、詢問菜品和結帳等情境",
                "sequence_number": 1,
                "video_url": "https://example.com/videos/restaurant_order.mp4",
                "created_at": "2025-05-01T06:04:16.148321",
                "updated_at": "2025-05-01T06:04:16.148463"
            }
        }

# Sentence Schemas
class SentenceCreate(BaseModel):
    sentence_name: str
    speaker_role: SpeakerRole
    role_description: Optional[str] = None
    content: str
    start_time: Optional[float] = None  # 在影片中的開始時間（秒）
    end_time: Optional[float] = None    # 在影片中的結束時間（秒）

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_name": "基本點餐對話",
                "speaker_role": "self",
                "role_description": "客人",
                "content": "我想要一份牛肉麵，不要太辣",
                "start_time": 10.5,
                "end_time": 15.2
            }
        }

class SentenceUpdate(BaseModel):
    sentence_name: Optional[str] = None
    speaker_role: Optional[SpeakerRole] = None
    role_description: Optional[str] = None
    content: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_name": "修改後的點餐對話",
                "speaker_role": "self",
                "role_description": "客人",
                "content": "請給我一份牛肉麵，小辣",
                "start_time": 11.0,
                "end_time": 16.0
            }
        }

class SentenceResponse(BaseModel):
    sentence_id: UUID
    chapter_id: UUID
    sentence_name: str
    speaker_role: SpeakerRole
    role_description: Optional[str]
    content: str
    start_time: Optional[float]
    end_time: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
                "sentence_name": "基本點餐對話",
                "speaker_role": "self",
                "role_description": "客人",
                "content": "我想要一份牛肉麵，不要太辣",
                "start_time": 10.5,
                "end_time": 15.2,
                "created_at": "2025-05-01T06:05:16.517760",
                "updated_at": "2025-05-01T06:05:16.518057"
            }
        }

# PracticeRecord Schemas
class PracticeRecordCreate(BaseModel):
    sentence_id: UUID
    audio_path: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "audio_path": "/storage/audio/user_recording_123.mp3"
            }
        }

class PracticeRecordResponse(BaseModel):
    practice_record_id: UUID
    user_id: UUID
    sentence_id: UUID
    begin_time: datetime
    end_time: Optional[datetime]
    audio_path: Optional[str]
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "user_id": "550e8400-e29b-41d4-a716-446655440005",
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "begin_time": "2025-05-01T06:10:00.000000",
                "end_time": "2025-05-01T06:10:30.000000",
                "audio_path": "/storage/audio/user_recording_123.mp3",
                "created_at": "2025-05-01T06:10:30.000000"
            }
        }

# List Response Schemas
class SituationListResponse(BaseModel):
    total: int
    situations: List[SituationResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "situations": [{
                    "situation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "situation_name": "餐廳用餐",
                    "description": "在餐廳點餐、用餐和結帳的對話情境",
                    "location": "餐廳",
                    "created_at": "2025-05-01T06:03:56.458985",
                    "updated_at": "2025-05-01T06:03:56.459284"
                }]
            }
        }

class ChapterListResponse(BaseModel):
    total: int
    chapters: List[ChapterResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "chapters": [{
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
                    "situation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "chapter_name": "餐廳點餐",
                    "description": "學習在餐廳用餐時的常用對話，包含點餐、詢問菜品和結帳等情境",
                    "sequence_number": 1,
                    "video_url": "https://example.com/videos/restaurant_order.mp4",
                    "video_duration": 120.5,
                    "video_format": "mp4",
                    "created_at": "2025-05-01T06:04:16.148321",
                    "updated_at": "2025-05-01T06:04:16.148463"
                }]
            }
        }

class SentenceListResponse(BaseModel):
    total: int
    sentences: List[SentenceResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "sentences": [{
                    "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
                    "sentence_name": "基本點餐對話",
                    "speaker_role": "self",
                    "role_description": "客人",
                    "content": "我想要一份牛肉麵，不要太辣",
                    "start_time": 10.5,
                    "end_time": 15.2,
                    "created_at": "2025-05-01T06:05:16.517760",
                    "updated_at": "2025-05-01T06:05:16.518057"
                }]
            }
        }

class PracticeRecordListResponse(BaseModel):
    total: int
    practice_records: List[PracticeRecordResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "practice_records": [{
                    "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                    "user_id": "550e8400-e29b-41d4-a716-446655440005",
                    "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                    "score": 85.5,
                    "begin_time": "2025-05-01T06:10:00.000000",
                    "end_time": "2025-05-01T06:10:30.000000",
                    "audio_path": "/storage/audio/user_recording_123.mp3",
                    "created_at": "2025-05-01T06:10:30.000000"
                }]
            }
        }


from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from src.course.models import SpeakerRole

# Course Schemas
class CourseCreate(BaseModel):
    course_name: str
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "course_name": "日常生活會話練習",
                "description": "透過真實場景模擬，練習日常生活中的常用對話，提升溝通能力"
            }
        }

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "course_name": "進階會話練習",
                "description": "針對進階程度學習者的日常對話練習"
            }
        }

class CourseResponse(BaseModel):
    course_id: int
    course_name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "course_id": 1,
                "course_name": "日常生活會話練習",
                "description": "透過真實場景模擬，練習日常生活中的常用對話，提升溝通能力",
                "created_at": "2025-05-01T06:03:56.458985",
                "updated_at": "2025-05-01T06:03:56.459284"
            }
        }

# Chapter Schemas
class ChapterCreate(BaseModel):
    chapter_name: str
    description: Optional[str] = None
    sequence_number: int

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_name": "餐廳點餐",
                "description": "學習在餐廳用餐時的常用對話，包含點餐、詢問菜品和結帳等情境",
                "sequence_number": 1
            }
        }

class ChapterUpdate(BaseModel):
    chapter_name: Optional[str] = None
    description: Optional[str] = None
    sequence_number: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_name": "餐廳進階對話",
                "description": "學習更進階的餐廳對話，包含特殊需求和處理問題的情境",
                "sequence_number": 2
            }
        }

class ChapterOrder(BaseModel):
    chapter_id: int
    sequence_number: int

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": 1,
                "sequence_number": 2
            }
        }

class ChapterReorder(BaseModel):
    chapter_orders: List[ChapterOrder]

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_orders": [
                    {"chapter_id": 1, "sequence_number": 2},
                    {"chapter_id": 2, "sequence_number": 1}
                ]
            }
        }

class ChapterResponse(BaseModel):
    chapter_id: int
    course_id: int
    chapter_name: str
    description: Optional[str]
    sequence_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": 1,
                "course_id": 1,
                "chapter_name": "餐廳點餐",
                "description": "學習在餐廳用餐時的常用對話，包含點餐、詢問菜品和結帳等情境",
                "sequence_number": 1,
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

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_name": "基本點餐對話",
                "speaker_role": "self",
                "role_description": "客人",
                "content": "我想要一份牛肉麵，不要太辣"
            }
        }

class SentenceUpdate(BaseModel):
    sentence_name: Optional[str] = None
    speaker_role: Optional[SpeakerRole] = None
    role_description: Optional[str] = None
    content: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_name": "修改後的點餐對話",
                "speaker_role": "self",
                "role_description": "客人",
                "content": "請給我一份牛肉麵，小辣"
            }
        }

class SentenceResponse(BaseModel):
    sentence_id: int
    chapter_id: int
    sentence_name: str
    speaker_role: SpeakerRole
    role_description: Optional[str]
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "sentence_id": 1,
                "chapter_id": 1,
                "sentence_name": "基本點餐對話",
                "speaker_role": "self",
                "role_description": "客人",
                "content": "我想要一份牛肉麵，不要太辣",
                "created_at": "2025-05-01T06:05:16.517760",
                "updated_at": "2025-05-01T06:05:16.518057"
            }
        }

# List Response Schemas
class CourseListResponse(BaseModel):
    total: int
    courses: List[CourseResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "courses": [{
                    "course_id": 1,
                    "course_name": "日常生活會話練習",
                    "description": "透過真實場景模擬，練習日常生活中的常用對話，提升溝通能力",
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
                    "chapter_id": 1,
                    "course_id": 1,
                    "chapter_name": "餐廳點餐",
                    "description": "學習在餐廳用餐時的常用對話，包含點餐、詢問菜品和結帳等情境",
                    "sequence_number": 1,
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
                    "sentence_id": 1,
                    "chapter_id": 1,
                    "sentence_name": "基本點餐對話",
                    "speaker_role": "self",
                    "role_description": "客人",
                    "content": "我想要一份牛肉麵，不要太辣",
                    "created_at": "2025-05-01T06:05:16.517760",
                    "updated_at": "2025-05-01T06:05:16.518057"
                }]
            }
        }

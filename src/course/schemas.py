from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Course Schemas
class CourseCreate(BaseModel):
    course_name: str
    description: Optional[str] = None

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    description: Optional[str] = None

class CourseResponse(BaseModel):
    course_id: int
    course_name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

# Chapter Schemas
class ChapterCreate(BaseModel):
    chapter_name: str
    description: Optional[str] = None
    sequence_number: int

class ChapterUpdate(BaseModel):
    chapter_name: Optional[str] = None
    description: Optional[str] = None
    sequence_number: Optional[int] = None

class ChapterOrder(BaseModel):
    chapter_id: int
    sequence_number: int

class ChapterReorder(BaseModel):
    chapter_orders: List[ChapterOrder]

class ChapterResponse(BaseModel):
    chapter_id: int
    course_id: int
    chapter_name: str
    description: Optional[str]
    sequence_number: int
    created_at: datetime
    updated_at: datetime

# Sentence Schemas
class SentenceCreate(BaseModel):
    sentence_name: str
    speaker_role: str
    content: str

class SentenceUpdate(BaseModel):
    sentence_name: Optional[str] = None
    speaker_role: Optional[str] = None
    content: Optional[str] = None

class SentenceResponse(BaseModel):
    sentence_id: int
    chapter_id: int
    sentence_name: str
    speaker_role: str
    content: str
    created_at: datetime
    updated_at: datetime

# List Response Schemas
class CourseListResponse(BaseModel):
    total: int
    courses: List[CourseResponse]

class ChapterListResponse(BaseModel):
    total: int
    chapters: List[ChapterResponse]

class SentenceListResponse(BaseModel):
    total: int
    sentences: List[SentenceResponse]

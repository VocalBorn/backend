from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from src.practice.models import PracticeRecordStatus

# 治療師患者管理相關 Schemas
class PatientSessionProgress(BaseModel):
    """患者練習會話進度"""
    practice_session_id: UUID
    chapter_id: UUID
    chapter_name: str
    session_status: str
    begin_time: Optional[datetime]
    end_time: Optional[datetime]
    total_duration: Optional[int]  # 練習時長（秒）
    total_sentences: int
    completed_sentences: int
    completion_rate: float
    pending_feedback: int
    practice_date: datetime  # 練習日期（使用 begin_time）

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "chapter_name": "基本對話",
                "session_status": "completed",
                "begin_time": "2025-07-20T14:00:00Z",
                "end_time": "2025-07-20T14:30:00Z",
                "total_duration": 1800,
                "total_sentences": 20,
                "completed_sentences": 18,
                "completion_rate": 90.0,
                "pending_feedback": 2,
                "practice_date": "2025-07-20T14:00:00Z"
            }
        }
    )

class TherapistPatientOverviewResponse(BaseModel):
    """治療師患者進度概覽回應"""
    patient_id: UUID
    patient_name: str
    last_practice_date: Optional[datetime]
    total_practice_sessions: int
    completed_practice_sessions: int
    session_progress: List[PatientSessionProgress]
    total_pending_feedback: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440005",
                "patient_name": "王小明",
                "last_practice_date": "2025-07-20T14:30:00Z",
                "total_practice_sessions": 25,
                "completed_practice_sessions": 23,
                "session_progress": [{
                    "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "chapter_name": "基本對話",
                    "session_status": "completed",
                    "begin_time": "2025-07-20T14:00:00Z",
                    "end_time": "2025-07-20T14:30:00Z",
                    "total_duration": 1800,
                    "total_sentences": 20,
                    "completed_sentences": 18,
                    "completion_rate": 90.0,
                    "pending_feedback": 2,
                    "practice_date": "2025-07-20T14:00:00Z"
                }],
                "total_pending_feedback": 3
            }
        }
    )

class TherapistPatientsOverviewListResponse(BaseModel):
    """治療師所有患者概覽列表"""
    total: int
    patients_overview: List[TherapistPatientOverviewResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 15,
                "patients_overview": [{
                    "patient_id": "550e8400-e29b-41d4-a716-446655440005",
                    "patient_name": "王小明",
                    "last_practice_date": "2025-07-20T14:30:00Z",
                    "total_practice_sessions": 25,
                    "completed_practice_sessions": 23,
                    "session_progress": [],
                    "total_pending_feedback": 3
                }]
            }
        }
    )

class PatientPracticeRecordResponse(BaseModel):
    """患者練習記錄回應（含音訊）"""
    practice_record_id: UUID
    practice_session_id: UUID
    chapter_id: UUID
    chapter_name: str
    sentence_id: UUID
    sentence_content: str
    sentence_name: str
    record_status: PracticeRecordStatus
    audio_path: Optional[str]
    audio_duration: Optional[float]
    audio_stream_url: Optional[str]
    audio_stream_expires_at: Optional[datetime]
    recorded_at: Optional[datetime]
    has_feedback: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "chapter_name": "基本對話",
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                "sentence_content": "我想要一份牛肉麵，不要太辣",
                "sentence_name": "基本點餐對話",
                "record_status": "recorded",
                "audio_path": "/storage/audio/recording.mp3",
                "audio_duration": 30.5,
                "audio_stream_url": "https://presigned-url...",
                "audio_stream_expires_at": "2025-07-23T15:30:00Z",
                "recorded_at": "2025-07-20T14:30:00Z",
                "has_feedback": False
            }
        }
    )

class PatientPracticeListResponse(BaseModel):
    """患者練習列表回應"""
    patient_info: dict
    total: int
    practice_records: List[PatientPracticeRecordResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_info": {
                    "patient_id": "550e8400-e29b-41d4-a716-446655440005",
                    "patient_name": "王小明"
                },
                "total": 50,
                "practice_records": [{
                    "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                    "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "chapter_name": "基本對話",
                    "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                    "sentence_content": "我想要一份牛肉麵，不要太辣",
                    "sentence_name": "基本點餐對話",
                    "record_status": "recorded",
                    "audio_path": "/storage/audio/recording.mp3",
                    "audio_duration": 30.5,
                    "audio_stream_url": "https://presigned-url...",
                    "audio_stream_expires_at": "2025-07-23T15:30:00Z",
                    "recorded_at": "2025-07-20T14:30:00Z",
                    "has_feedback": False
                }]
            }
        }
    )

# 新版練習會話分組相關 Schemas
class PracticeSessionGroup(BaseModel):
    """單一練習會話的資料結構"""
    practice_session_id: UUID
    chapter_id: UUID
    chapter_name: str
    session_status: str
    begin_time: Optional[datetime]
    end_time: Optional[datetime]
    total_sentences: int
    pending_feedback_count: int
    practice_records: List[PatientPracticeRecordResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                "chapter_name": "基本對話",
                "session_status": "completed",
                "begin_time": "2025-07-20T14:00:00Z",
                "end_time": "2025-07-20T14:30:00Z",
                "total_sentences": 10,
                "pending_feedback_count": 3,
                "practice_records": [{
                    "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                    "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "chapter_name": "基本對話",
                    "sentence_id": "550e8400-e29b-41d4-a716-446655440003",
                    "sentence_content": "我想要一份牛肉麵，不要太辣",
                    "sentence_name": "基本點餐對話",
                    "record_status": "recorded",
                    "audio_path": "/storage/audio/recording.mp3",
                    "audio_duration": 30.5,
                    "audio_stream_url": "https://presigned-url...",
                    "audio_stream_expires_at": "2025-07-23T15:30:00Z",
                    "recorded_at": "2025-07-20T14:30:00Z",
                    "has_feedback": False
                }]
            }
        }
    )

class PatientPracticeSessionsResponse(BaseModel):
    """患者練習會話列表回應（按會話分組）"""
    patient_info: dict
    total_sessions: int
    practice_sessions: List[PracticeSessionGroup]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_info": {
                    "patient_id": "550e8400-e29b-41d4-a716-446655440005",
                    "patient_name": "王小明"
                },
                "total_sessions": 3,
                "practice_sessions": [{
                    "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                    "chapter_id": "550e8400-e29b-41d4-a716-446655440002",
                    "chapter_name": "基本對話",
                    "session_status": "completed",
                    "begin_time": "2025-07-20T14:00:00Z",
                    "end_time": "2025-07-20T14:30:00Z",
                    "total_sentences": 10,
                    "pending_feedback_count": 3,
                    "practice_records": []
                }]
            }
        }
    )

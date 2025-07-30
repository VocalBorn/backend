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

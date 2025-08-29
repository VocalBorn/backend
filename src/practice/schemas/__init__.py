"""
Practice Schemas
"""
from .audio import AudioUploadRequest, AudioUploadResponse
from .feedback import (
    PracticeFeedbackCreate,
    PracticeFeedbackResponse,
    PracticeFeedbackUpdate,
    PracticeSessionFeedbackCreate,
    PracticeSessionFeedbackResponse,
    PracticeSessionFeedbackUpdate,
    SentenceFeedbackItem,
    SessionFeedbackCreate,
    SessionFeedbackItemResponse,
    SessionFeedbackResponse,
)
from .practice_record import (
    PracticeRecordCreate,
    PracticeRecordListResponse,
    PracticeRecordResponse,
    PracticeRecordUpdate,
    RecordingsListResponse,
    RecordingResponse,
    RecordUpdateRequest,
)
from .practice_session import (
    PracticeSessionCreate,
    PracticeSessionListResponse,
    PracticeSessionResponse,
    AIAnalysisTriggerResponse,
)
from .stats import PracticeStatsResponse
from .therapist import (
    PatientPracticeListResponse,
    PatientPracticeRecordResponse,
    PatientPracticeSessionsResponse,
    PatientSessionProgress,
    PracticeSessionGroup,
    TherapistPatientOverviewResponse,
    TherapistPatientsOverviewListResponse,
)
from .patient_feedback import (
    FeedbackFilters,
    PaginatedFeedbackListResponse,
    PatientFeedbackDetailResponse,
    PatientFeedbackListItem,
    PaginationInfo,
    TherapistInfo,
    ChapterInfo,
    TherapistFeedbackDetail,
    PracticeRecordDetail
)

__all__ = [
    # Audio
    "AudioUploadRequest",
    "AudioUploadResponse",
    # Feedback
    "PracticeFeedbackCreate",
    "PracticeFeedbackUpdate",
    "PracticeFeedbackResponse",
    "PracticeSessionFeedbackCreate",
    "PracticeSessionFeedbackUpdate",
    "PracticeSessionFeedbackResponse",
    "SentenceFeedbackItem",
    "SessionFeedbackCreate",
    "SessionFeedbackItemResponse",
    "SessionFeedbackResponse",
    # Practice Record
    "RecordUpdateRequest",
    "RecordingResponse",
    "RecordingsListResponse",
    "PracticeRecordCreate",
    "PracticeRecordUpdate",
    "PracticeRecordResponse",
    "PracticeRecordListResponse",
    # Practice Session
    "PracticeSessionCreate",
    "PracticeSessionResponse",
    "PracticeSessionListResponse",
    "AIAnalysisTriggerResponse",
    # Stats
    "PracticeStatsResponse",
    # Therapist
    "PatientSessionProgress",
    "TherapistPatientOverviewResponse",
    "TherapistPatientsOverviewListResponse",
    "PatientPracticeRecordResponse",
    "PatientPracticeListResponse",
    "PracticeSessionGroup",
    "PatientPracticeSessionsResponse",
    # Patient Feedback
    "FeedbackFilters",
    "PaginatedFeedbackListResponse", 
    "PatientFeedbackDetailResponse",
    "PatientFeedbackListItem",
    "PaginationInfo",
    "TherapistInfo",
    "ChapterInfo", 
    "TherapistFeedbackDetail",
    "PracticeRecordDetail",
]

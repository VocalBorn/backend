
import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException

from src.practice.services.therapist_patient_service import (
    get_therapist_patients_overview,
    get_patient_practice_sessions,
    get_patient_practice_records,
)
from src.auth.models import User, UserRole
from src.therapist.models import TherapistClient
from src.practice.models import PracticeSession, PracticeRecord, PracticeFeedback, PracticeRecordStatus, PracticeSessionStatus
from src.course.models import Chapter, Sentence

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def mock_audio_service():
    with patch('src.practice.services.therapist_patient_service.PracticeRecordingService') as mock:
        mock.return_value.get_presigned_url = AsyncMock(return_value=("http://some.url", "some_date"))
        yield mock

@pytest.mark.asyncio
async def test_get_therapist_patients_overview_success(mock_session):
    therapist_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    mock_patient = User(user_id=patient_id, name="Test Patient", role=UserRole.CLIENT)
    
    # 建立 mock 統計結果
    mock_stats = MagicMock()
    mock_stats.total_sentences = 10
    mock_stats.completed_sentences = 8
    mock_stats.pending_feedback = 2
    
    # 設定多個 exec 調用的回傳值
    mock_session.exec.return_value.one.side_effect = [1]  # total count
    mock_session.exec.return_value.all.side_effect = [
        [mock_patient],  # patients
        [(PracticeSession(user_id=patient_id, chapter_id=uuid.uuid4(), session_status=PracticeSessionStatus.COMPLETED), Chapter(chapter_name="Test Chapter"))]  # sessions
    ]
    mock_session.exec.return_value.first.return_value = mock_stats  # stats
    
    result = await get_therapist_patients_overview(therapist_id, mock_session)

    assert result.total == 1
    assert len(result.patients_overview) == 1
    assert result.patients_overview[0].patient_id == patient_id

@pytest.mark.asyncio
async def test_get_patient_practice_sessions_success(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    session_id = uuid.uuid4()
    chapter_id = uuid.uuid4()

    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=patient_id, is_active=True)
    mock_patient = User(user_id=patient_id, name="Test Patient")
    mock_session_obj = PracticeSession(practice_session_id=session_id, user_id=patient_id, chapter_id=chapter_id, session_status=PracticeSessionStatus.COMPLETED)
    mock_chapter = Chapter(chapter_id=chapter_id, chapter_name="Chapter 1")
    mock_record = PracticeRecord(practice_session_id=session_id, sentence_id=uuid.uuid4(), record_status=PracticeRecordStatus.RECORDED)
    mock_sentence = Sentence(content="Hello", sentence_name="Greeting")

    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, mock_patient, Chapter(chapter_name="Test Chapter")]
    mock_session.exec.return_value.all.side_effect = [[(mock_session_obj, mock_chapter)], [(mock_record, mock_sentence)]]
    mock_session.exec.return_value.one.return_value = 0

    result = await get_patient_practice_sessions(patient_id, therapist_id, mock_session)

    assert result.total_sessions == 1
    assert len(result.practice_sessions) == 1
    assert result.practice_sessions[0].practice_session_id == session_id

@pytest.mark.asyncio
async def test_get_patient_practice_records_success(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=patient_id, is_active=True)
    mock_patient = User(user_id=patient_id, name="Test Patient")
    mock_record = MagicMock(
        practice_record_id=uuid.uuid4(),
        practice_session_id=uuid.uuid4(),
        sentence_id=uuid.uuid4(),
        record_status=PracticeRecordStatus.RECORDED,
        audio_path="some/path",
        audio_duration=10.0,
        file_size=100,
        content_type="audio/mpeg",
        recorded_at=datetime.now(),
        feedback=None
    )
    mock_record.practice_session = MagicMock(chapter_id=uuid.uuid4())
    mock_record.sentence = MagicMock(content="Hello", sentence_name="Greeting")
    mock_record.practice_record_id = str(mock_record.practice_record_id)
    mock_record.practice_session_id = str(mock_record.practice_session_id)
    mock_record.sentence_id = str(mock_record.sentence_id)
    mock_record.record_status = mock_record.record_status.value
    mock_record.recorded_at = datetime.now()
    mock_record.audio_stream_expires_at = datetime.now()
    mock_record.has_feedback = False
    mock_record.practice_session.chapter_id = str(mock_record.practice_session.chapter_id)
    mock_record.sentence.content = "Hello"
    mock_record.sentence.sentence_name = "Greeting"
    mock_record.audio_path = "some/path"
    mock_record.audio_duration = 10.0
    mock_record.file_size = 100
    mock_record.content_type = "audio/mpeg"
    mock_record.recorded_at = datetime.now()

    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, mock_patient, Chapter(chapter_name="Test Chapter")]
    mock_session.exec.return_value.one.return_value = 1
    mock_session.exec.return_value.all.return_value = [mock_record]
    mock_audio_service.return_value.get_presigned_url.return_value = ("http://some.url", datetime.now())

    result = await get_patient_practice_records(patient_id, therapist_id, mock_session)

    assert result.total == 1
    assert len(result.practice_records) == 1

@pytest.mark.asyncio
async def test_get_therapist_patients_overview_no_patients(mock_session):
    therapist_id = uuid.uuid4()
    
    mock_session.exec.return_value.one.return_value = 0  # 沒有患者
    mock_session.exec.return_value.all.return_value = []  # 空列表

    result = await get_therapist_patients_overview(therapist_id, mock_session)

    assert result.total == 0
    assert len(result.patients_overview) == 0

@pytest.mark.asyncio
async def test_get_patient_practice_sessions_unauthorized(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_session.exec.return_value.first.return_value = None  # 沒有治療師-患者關係

    with pytest.raises(HTTPException) as exc_info:
        await get_patient_practice_sessions(patient_id, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test_get_patient_practice_sessions_inactive_relationship(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    # 服務查詢 is_active=True，當關係是非活躍時，查詢會返回None
    mock_session.exec.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_patient_practice_sessions(patient_id, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 403
    assert "治療師無權查看此患者的練習記錄" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_patient_practice_sessions_patient_not_found(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=patient_id, is_active=True)
    mock_session.exec.return_value.first.side_effect = [
        mock_therapist_client,  # 治療師關係存在
        None  # 患者不存在
    ]

    with pytest.raises(HTTPException) as exc_info:
        await get_patient_practice_sessions(patient_id, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 404
    assert "找不到指定的患者" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_patient_practice_sessions_no_sessions(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=patient_id, is_active=True)
    mock_patient = User(user_id=patient_id, name="Test Patient")

    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, mock_patient, Chapter()]
    mock_session.exec.return_value.all.side_effect = [[], []]  # 沒有會話和記錄
    mock_session.exec.return_value.one.return_value = 0

    result = await get_patient_practice_sessions(patient_id, therapist_id, mock_session)

    assert result.total_sessions == 0
    assert len(result.practice_sessions) == 0

@pytest.mark.asyncio
async def test_get_patient_practice_records_unauthorized(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_session.exec.return_value.first.return_value = None  # 沒有治療師-患者關係

    with pytest.raises(HTTPException) as exc_info:
        await get_patient_practice_records(patient_id, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 403
    assert "治療師無權查看此患者的練習記錄" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_patient_practice_records_no_records(mock_session, mock_audio_service):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=patient_id, is_active=True)
    mock_patient = User(user_id=patient_id, name="Test Patient")

    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, mock_patient, Chapter()]
    mock_session.exec.return_value.one.return_value = 0  # 沒有記錄
    mock_session.exec.return_value.all.return_value = []

    result = await get_patient_practice_records(patient_id, therapist_id, mock_session)

    assert result.total == 0
    assert len(result.practice_records) == 0

@pytest.mark.asyncio
async def test_get_patient_practice_records_audio_service_error(mock_session):
    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=patient_id, is_active=True)
    mock_patient = User(user_id=patient_id, name="Test Patient")
    
    # 建立實際的Mock對象而非MagicMock，避免Pydantic驗證錯誤
    from src.practice.models import PracticeRecord, PracticeRecordStatus
    from src.course.models import Sentence, Chapter
    
    mock_chapter = Chapter(chapter_id=uuid.uuid4(), title="Test Chapter")
    mock_sentence = Sentence(sentence_id=uuid.uuid4(), content="Hello", sentence_name="Greeting")
    mock_record = PracticeRecord(
        practice_record_id=uuid.uuid4(),
        practice_session_id=uuid.uuid4(), 
        sentence_id=mock_sentence.sentence_id,
        record_status=PracticeRecordStatus.RECORDED,
        audio_path="some/path",
        recorded_at=datetime.now()
    )
    mock_record.sentence = mock_sentence

    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, mock_patient, mock_chapter]
    mock_session.exec.return_value.one.return_value = 1
    mock_session.exec.return_value.all.return_value = [mock_record]

    # 模擬音頻服務錯誤，服務應該優雅處理而不拋出異常
    with patch('src.practice.services.therapist_patient_service.PracticeRecordingService') as mock_audio_service:
        mock_audio_service.return_value.get_presigned_url.side_effect = Exception("Storage error")

        # 服務應該正常返回，但音頻URL為None
        result = await get_patient_practice_records(patient_id, therapist_id, mock_session)
        
        assert result is not None
        assert result.total_records == 1
        # 音頻URL應該為None因為服務錯誤被優雅處理
        assert result.practice_records[0].audio_stream_url is None

@pytest.mark.asyncio
async def test_get_therapist_patients_overview_database_error(mock_session):
    therapist_id = uuid.uuid4()
    
    mock_session.exec.side_effect = Exception("Database connection error")

    with pytest.raises(Exception) as exc_info:
        await get_therapist_patients_overview(therapist_id, mock_session)
    
    assert "Database connection error" in str(exc_info.value)

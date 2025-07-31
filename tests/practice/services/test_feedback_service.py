import uuid
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.practice.services.feedback_service import (
    delete_practice_feedback,
    create_session_feedback,
    get_session_feedbacks,
    update_session_feedbacks,
)
from src.practice.models import (
    PracticeFeedback,
    PracticeRecord,
    PracticeRecordStatus,
    PracticeSession,
    PracticeSessionFeedback,
)
from src.auth.models import User
from src.course.models import Chapter
from src.therapist.models import TherapistClient
from src.practice.schemas import (
    PracticeSessionFeedbackCreate,
    PracticeSessionFeedbackUpdate,
)

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.mark.asyncio
async def test_delete_practice_feedback_success(mock_session):
    feedback_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    practice_record_id = uuid.uuid4()

    mock_feedback = PracticeFeedback(
        feedback_id=feedback_id,
        therapist_id=therapist_id,
        practice_record_id=practice_record_id,
        content="Test feedback"
    )
    mock_record = PracticeRecord(
        practice_record_id=practice_record_id,
        record_status=PracticeRecordStatus.ANALYZED
    )

    mock_session.get.side_effect = [mock_feedback, mock_record]

    result = await delete_practice_feedback(feedback_id, therapist_id, mock_session)

    assert result is True
    assert mock_record.record_status == PracticeRecordStatus.RECORDED
    mock_session.delete.assert_called_once_with(mock_feedback)
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_session_feedback_success(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    chapter_id = uuid.uuid4()
    feedback_data = PracticeSessionFeedbackCreate(content="Great session!")

    mock_session_obj = PracticeSession(
        practice_session_id=practice_session_id,
        user_id=user_id,
        chapter_id=chapter_id
    )
    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=user_id, is_active=True)
    mock_therapist = User(user_id=therapist_id, name="Dr. Therapist")
    mock_patient = User(user_id=user_id, name="John Doe")
    mock_chapter = Chapter(chapter_id=chapter_id, chapter_name="Chapter 1")

    mock_session.get.side_effect = [mock_session_obj, mock_therapist, mock_patient, mock_chapter]
    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, None]

    result = await create_session_feedback(practice_session_id, feedback_data, therapist_id, mock_session)

    assert result.content == feedback_data.content
    assert result.therapist_id == therapist_id
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_session_feedbacks_success(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    chapter_id = uuid.uuid4()
    feedback_id = uuid.uuid4()

    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id, chapter_id=uuid.uuid4())
    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=user_id, is_active=True)
    mock_feedback = PracticeSessionFeedback(session_feedback_id=feedback_id, practice_session_id=practice_session_id, therapist_id=therapist_id, content="Feedback")
    mock_therapist = User(user_id=therapist_id, name="Dr. Therapist")
    mock_patient = User(user_id=user_id, name="John Doe")
    mock_chapter = Chapter(chapter_id=chapter_id, chapter_name="Chapter 1")

    mock_session.get.side_effect = [mock_session_obj, mock_therapist, mock_patient, mock_chapter]
    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, mock_feedback]

    result = await get_session_feedbacks(practice_session_id, therapist_id, mock_session)

    assert result.session_feedback_id == feedback_id
    assert result.therapist_id == therapist_id

@pytest.mark.asyncio
async def test_update_session_feedbacks_success(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    feedback_id = uuid.uuid4()
    feedback_data = PracticeSessionFeedbackUpdate(content="Updated feedback")

    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id, chapter_id=uuid.uuid4())
    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=user_id, is_active=True)
    mock_feedback = PracticeSessionFeedback(session_feedback_id=feedback_id, practice_session_id=practice_session_id, therapist_id=therapist_id, content="Original feedback")
    
    mock_therapist = User(user_id=therapist_id, name="Dr. Therapist")
    mock_patient = User(user_id=user_id, name="John Doe")
    mock_chapter = Chapter(chapter_id=uuid.uuid4(), chapter_name="Chapter 1")
    mock_session_obj.chapter_id = mock_chapter.chapter_id

    mock_session.get.side_effect = [mock_session_obj, mock_therapist, mock_patient, mock_chapter]
    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, mock_feedback]

    result = await update_session_feedbacks(practice_session_id, feedback_data, therapist_id, mock_session)

    assert result.content == feedback_data.content
    assert mock_feedback.content == feedback_data.content
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_practice_feedback_not_found(mock_session):
    feedback_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await delete_practice_feedback(feedback_id, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_delete_practice_feedback_unauthorized(mock_session):
    feedback_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    different_therapist_id = uuid.uuid4()

    mock_feedback = PracticeFeedback(
        feedback_id=feedback_id,
        therapist_id=different_therapist_id,  # 不同的治療師
        practice_record_id=uuid.uuid4(),
        content="Test feedback"
    )

    mock_session.get.return_value = mock_feedback

    with pytest.raises(HTTPException) as exc_info:
        await delete_practice_feedback(feedback_id, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test_create_session_feedback_session_not_found(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    feedback_data = PracticeSessionFeedbackCreate(content="Test feedback")

    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await create_session_feedback(practice_session_id, feedback_data, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_create_session_feedback_unauthorized_therapist(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    feedback_data = PracticeSessionFeedbackCreate(content="Test feedback")

    mock_session_obj = PracticeSession(
        practice_session_id=practice_session_id,
        user_id=user_id,
        chapter_id=uuid.uuid4()
    )

    mock_session.get.return_value = mock_session_obj
    mock_session.exec.return_value.first.return_value = None  # 沒有治療師-患者關係

    with pytest.raises(HTTPException) as exc_info:
        await create_session_feedback(practice_session_id, feedback_data, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test_get_session_feedbacks_not_found(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id, chapter_id=uuid.uuid4())
    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=user_id, is_active=True)

    mock_session.get.side_effect = [mock_session_obj, User(), User(), Chapter()]
    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, None]  # 沒有回饋

    with pytest.raises(HTTPException) as exc_info:
        await get_session_feedbacks(practice_session_id, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_update_session_feedbacks_not_found(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    feedback_data = PracticeSessionFeedbackUpdate(content="Updated feedback")

    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id, chapter_id=uuid.uuid4())
    mock_therapist_client = TherapistClient(therapist_id=therapist_id, client_id=user_id, is_active=True)

    mock_session.get.side_effect = [mock_session_obj, User(), User(), Chapter()]
    mock_session.exec.return_value.first.side_effect = [mock_therapist_client, None]  # 沒有回饋

    with pytest.raises(HTTPException) as exc_info:
        await update_session_feedbacks(practice_session_id, feedback_data, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio  
async def test_create_session_feedback_inactive_therapist_client(mock_session):
    practice_session_id = uuid.uuid4()
    therapist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    feedback_data = PracticeSessionFeedbackCreate(content="Test feedback")

    mock_session_obj = PracticeSession(
        practice_session_id=practice_session_id,
        user_id=user_id,
        chapter_id=uuid.uuid4()
    )
    
    # 設定 get 調用回傳練習會話
    mock_session.get.return_value = mock_session_obj
    
    # 設定 exec 調用，第一次查詢 TherapistClient 時回傳 None (因為是 is_active=False 會被過濾掉)
    mock_session.exec.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await create_session_feedback(practice_session_id, feedback_data, therapist_id, mock_session)
    
    assert exc_info.value.status_code == 403
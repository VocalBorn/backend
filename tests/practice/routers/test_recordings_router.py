import uuid
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile, HTTPException, status

from src.main import app
from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_current_user():
    return User(user_id=uuid.uuid4(), name="testuser", email="test@example.com", role="client")

@patch('src.practice.routers.recordings_router.get_practice_session', new_callable=AsyncMock)
@patch('src.practice.routers.recordings_router.get_practice_record_by_session_and_sentence', new_callable=AsyncMock)
@patch('src.practice.routers.recordings_router.practice_recording_service.upload_practice_recording')
@patch('src.practice.routers.recordings_router.update_practice_audio_info', new_callable=AsyncMock)
def test_upload_or_update_recording_success(mock_update_audio, mock_upload, mock_get_record, mock_get_session, mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    session_id = uuid.uuid4()
    sentence_id = uuid.uuid4()
    mock_get_record.return_value.audio_path = None
    mock_upload.return_value = {
        "recording_id": "123",
        "object_name": "tests/test.mp3",
        "file_size": 100,
        "content_type": "audio/mpeg",
        "status": "uploaded"
    }

    with open("tests/test.mp3", "wb") as f:
        f.write(b"test data")

    with open("tests/test.mp3", "rb") as f:
        response = client.put(
            f"/practice/sessions/{session_id}/recordings/{sentence_id}",
            files={"audio_file": ("test.mp3", f, "audio/mpeg")}
        )

    assert response.status_code == 200
    assert response.json()['status'] == 'uploaded'
    app.dependency_overrides = {}

@patch('src.practice.routers.recordings_router.get_practice_session', new_callable=AsyncMock)
@patch('src.practice.routers.recordings_router.get_practice_record_by_session_and_sentence', new_callable=AsyncMock)
def test_upload_recording_session_not_found(mock_get_record, mock_get_session, mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    session_id = uuid.uuid4()
    sentence_id = uuid.uuid4()
    
    # 設定 mock 讓 get_practice_session 拋出 404 錯誤
    mock_get_session.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="練習會話不存在或無權限"
    )

    with open("tests/test.mp3", "wb") as f:
        f.write(b"test data")

    with open("tests/test.mp3", "rb") as f:
        response = client.put(
            f"/practice/sessions/{session_id}/recordings/{sentence_id}",
            files={"audio_file": ("test.mp3", f, "audio/mpeg")}
        )

    assert response.status_code == 404
    app.dependency_overrides = {}

@patch('src.practice.routers.recordings_router.get_practice_session', new_callable=AsyncMock) 
@patch('src.practice.routers.recordings_router.get_practice_record_by_session_and_sentence', new_callable=AsyncMock)
def test_upload_recording_invalid_file_type(mock_get_record, mock_get_session, mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    session_id = uuid.uuid4()
    sentence_id = uuid.uuid4()
    mock_get_record.return_value.audio_path = None

    with open("tests/test.txt", "wb") as f:
        f.write(b"test data")

    with open("tests/test.txt", "rb") as f:
        response = client.put(
            f"/practice/sessions/{session_id}/recordings/{sentence_id}",
            files={"audio_file": ("test.txt", f, "text/plain")}
        )

    assert response.status_code == 400
    app.dependency_overrides = {}

def test_upload_recording_no_file(mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    session_id = uuid.uuid4()
    sentence_id = uuid.uuid4()

    response = client.put(f"/practice/sessions/{session_id}/recordings/{sentence_id}")

    assert response.status_code == 422
    app.dependency_overrides = {}

def test_upload_recording_invalid_uuid_format(mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    invalid_session_id = "invalid-uuid"
    sentence_id = uuid.uuid4()

    with open("tests/test.mp3", "wb") as f:
        f.write(b"test data")

    with open("tests/test.mp3", "rb") as f:
        response = client.put(
            f"/practice/sessions/{invalid_session_id}/recordings/{sentence_id}",
            files={"audio_file": ("test.mp3", f, "audio/mpeg")}
        )

    assert response.status_code == 422
    app.dependency_overrides = {}
from datetime import datetime
import uuid
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from src.main import app
from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User
from src.course.models import Chapter
from src.practice.schemas import PracticeSessionCreate

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_current_user():
    return User(user_id=uuid.uuid4(), name="testuser", email="test@example.com", role="client")

@patch('src.practice.routers.sessions_router.create_practice_session', new_callable=AsyncMock)
def test_create_session_success(mock_create_session, mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    chapter_id = uuid.uuid4()
    practice_data = {"chapter_id": str(chapter_id)}
    mock_create_session.return_value = MagicMock()
    mock_create_session.return_value.practice_session_id = uuid.uuid4()
    mock_create_session.return_value.user_id = uuid.uuid4()
    mock_create_session.return_value.chapter_id = chapter_id
    mock_create_session.return_value.session_status = 'in_progress'
    mock_create_session.return_value.begin_time = None
    mock_create_session.return_value.end_time = None
    mock_create_session.return_value.total_duration = None
    mock_create_session.return_value.created_at = datetime.now()
    mock_create_session.return_value.updated_at = datetime.now()

    mock_db_session.get.return_value = Chapter(chapter_id=chapter_id, chapter_name="Test Chapter")
    mock_db_session.exec.return_value.one.return_value = 0

    response = client.post("/practice/sessions", json=practice_data)

    assert response.status_code == 200
    app.dependency_overrides = {}

@patch('src.practice.routers.sessions_router.create_practice_session', new_callable=AsyncMock)
def test_create_session_chapter_not_found(mock_create_session, mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    chapter_id = uuid.uuid4()
    practice_data = {"chapter_id": str(chapter_id)}
    
    # 設定 mock 讓 create_practice_session 拋出 404 錯誤
    mock_create_session.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="指定的章節不存在"
    )

    response = client.post("/practice/sessions", json=practice_data)

    assert response.status_code == 404
    app.dependency_overrides = {}

def test_create_session_invalid_chapter_id(mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    practice_data = {"chapter_id": "invalid-uuid"}

    response = client.post("/practice/sessions", json=practice_data)

    assert response.status_code == 422
    app.dependency_overrides = {}

def test_create_session_empty_data(mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post("/practice/sessions", json={})

    assert response.status_code == 422
    app.dependency_overrides = {}

@patch('src.practice.routers.sessions_router.create_practice_session', new_callable=AsyncMock)
def test_create_session_duplicate_in_progress(mock_create_session, mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    chapter_id = uuid.uuid4()
    practice_data = {"chapter_id": str(chapter_id)}
    
    # 設定 mock 讓 create_practice_session 拋出 400 錯誤
    mock_create_session.side_effect = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="該章節已有進行中的練習會話"
    )

    response = client.post("/practice/sessions", json=practice_data)

    assert response.status_code == 400
    app.dependency_overrides = {}

def test_create_session_no_authentication():
    chapter_id = uuid.uuid4()
    practice_data = {"chapter_id": str(chapter_id)}

    response = client.post("/practice/sessions", json=practice_data)

    assert response.status_code in [401, 403]

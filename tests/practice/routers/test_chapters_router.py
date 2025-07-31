import uuid
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User
from src.course.models import Chapter

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_current_user():
    return User(user_id=uuid.uuid4(), name="testuser", email="test@example.com", role="client")

def test_get_chapter_sessions_success(mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    chapter_id = uuid.uuid4()
    mock_db_session.get.return_value = Chapter(chapter_id=chapter_id, chapter_name="Test Chapter")
    mock_db_session.exec.return_value.one.return_value = 0
    mock_db_session.exec.return_value.all.return_value = []

    response = client.get(f"/practice/chapters/{chapter_id}/sessions")

    assert response.status_code == 200
    assert response.json() == {'total': 0, 'practice_sessions': []}

    # Clean up overrides
    app.dependency_overrides = {}

def test_get_chapter_sessions_chapter_not_found(mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    chapter_id = uuid.uuid4()
    mock_db_session.get.return_value = None

    response = client.get(f"/practice/chapters/{chapter_id}/sessions")

    assert response.status_code == 404
    app.dependency_overrides = {}

def test_get_chapter_sessions_invalid_uuid(mock_db_session, mock_current_user):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    invalid_chapter_id = "invalid-uuid"

    response = client.get(f"/practice/chapters/{invalid_chapter_id}/sessions")

    assert response.status_code == 422
    app.dependency_overrides = {}

def test_get_chapter_sessions_no_authentication():
    chapter_id = uuid.uuid4()

    response = client.get(f"/practice/chapters/{chapter_id}/sessions")

    assert response.status_code in [401, 403]
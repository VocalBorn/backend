import uuid
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.shared.database.database import get_session
from src.auth.services.permission_service import require_therapist
from src.auth.models import User

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_current_therapist():
    return User(user_id=uuid.uuid4(), name="testtherapist", email="therapist@example.com", role="therapist")

@patch('src.practice.routers.therapist_router.get_therapist_patients_overview', new_callable=AsyncMock)
def test_get_therapist_patients_overview_route_success(mock_get_overview, mock_db_session, mock_current_therapist):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[require_therapist] = lambda: mock_current_therapist

    mock_get_overview.return_value = {"total": 0, "patients_overview": []}
    response = client.get("/practice/therapist/patients/overview")
    assert response.status_code == 200
    assert response.json() == {"total": 0, "patients_overview": []}
    app.dependency_overrides = {}

@patch('src.practice.routers.therapist_router.get_therapist_patients_overview', new_callable=AsyncMock)
def test_get_therapist_patients_overview_service_error(mock_get_overview, mock_db_session, mock_current_therapist):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[require_therapist] = lambda: mock_current_therapist

    mock_get_overview.side_effect = ValueError("Database error")
    
    response = client.get("/practice/therapist/patients/overview")
    # 因為路由沒有錯誤處理，會返回 500
    assert response.status_code == 500
    app.dependency_overrides = {}

def test_get_therapist_patients_overview_no_therapist_auth():
    response = client.get("/practice/therapist/patients/overview")
    assert response.status_code in [401, 403]

@patch('src.practice.routers.therapist_router.get_therapist_patients_overview', new_callable=AsyncMock)
def test_get_therapist_patients_overview_empty_result(mock_get_overview, mock_db_session, mock_current_therapist):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    app.dependency_overrides[require_therapist] = lambda: mock_current_therapist

    mock_get_overview.return_value = {"total": 0, "patients_overview": []}
    
    response = client.get("/practice/therapist/patients/overview")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert len(response.json()["patients_overview"]) == 0
    app.dependency_overrides = {}

@patch('src.practice.routers.therapist_router.get_therapist_patients_overview', new_callable=AsyncMock)
def test_get_therapist_patients_overview_invalid_therapist(mock_get_overview, mock_db_session):
    """測試非治療師角色無法存取"""
    from fastapi import HTTPException
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    # require_therapist 應該在角色驗證失敗時拋出錯誤
    def mock_require_therapist():
        raise HTTPException(status_code=403, detail="需要治療師權限")
    
    app.dependency_overrides[require_therapist] = mock_require_therapist

    response = client.get("/practice/therapist/patients/overview")
    assert response.status_code == 403
    app.dependency_overrides = {}
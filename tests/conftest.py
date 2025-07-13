"""
測試配置檔案 - 提供共用的 fixtures
"""

import pytest
from unittest.mock import Mock
from sqlmodel import Session
from datetime import datetime
import uuid

from src.auth.models import UserRole
from src.auth.schemas import RegisterRequest, LoginRequest, UpdateUserRequest, Gender


@pytest.fixture
def mock_db_session():
    """Mock 資料庫會話"""
    session = Mock(spec=Session)
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.refresh = Mock()
    session.flush = Mock()
    session.exec = Mock()
    return session


@pytest.fixture
def sample_account():
    """範例帳號資料 - 使用 Mock 物件避免 SQLAlchemy 關聯問題"""
    account = Mock()
    account.account_id = uuid.uuid4()
    account.email = "test@example.com"
    account.password = "$2b$12$hashed_password_here"  # bcrypt hashed password
    account.is_verified = True
    account.created_at = datetime.now()
    account.updated_at = datetime.now()
    return account


@pytest.fixture
def sample_user():
    """範例用戶資料 - 使用 Mock 物件避免 SQLAlchemy 關聯問題"""
    account_id = uuid.uuid4()
    user = Mock()
    user.user_id = uuid.uuid4()
    user.account_id = account_id
    user.name = "測試用戶"
    user.gender = "male"
    user.age = 25
    user.phone = "0912345678"
    user.role = UserRole.CLIENT
    user.created_at = datetime.now()
    user.updated_at = datetime.now()
    return user


@pytest.fixture
def register_request():
    """註冊請求資料"""
    return RegisterRequest(
        email="newuser@example.com",
        password="StrongP@ssw0rd123",
        name="新用戶",
        gender=Gender.MALE,
        age=30
    )


@pytest.fixture
def login_request():
    """登入請求資料"""
    return LoginRequest(
        email="test@example.com",
        password="StrongP@ssw0rd123"
    )


@pytest.fixture
def update_user_request():
    """更新用戶請求資料"""
    return UpdateUserRequest(
        name="更新後的名字",
        age=26,
        phone="0987654321",
        gender=Gender.FEMALE
    )


@pytest.fixture
def unverified_account():
    """未驗證的帳號 - 使用 Mock 物件避免 SQLAlchemy 關聯問題"""
    account = Mock()
    account.account_id = uuid.uuid4()
    account.email = "unverified@example.com"
    account.password = "$2b$12$hashed_password_here"
    account.is_verified = False
    account.created_at = datetime.now()
    account.updated_at = datetime.now()
    return account

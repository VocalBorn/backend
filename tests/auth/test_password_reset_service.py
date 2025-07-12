"""
Password Reset Service 單元測試
測試 src.auth.services.password_reset_service 中的密碼重設功能
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from pydantic import EmailStr

# 導入 course.models 和 therapist.models 以解決 SQLAlchemy 的依賴問題
import src.course.models
import src.therapist.models

from src.auth.services.password_reset_service import (
    forgot_password,
    reset_password
)
from src.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest


class TestForgotPassword:
    """忘記密碼功能測試類別"""

    @pytest.fixture
    def mock_account(self):
        """Mock Account 物件"""
        account = Mock()
        account.account_id = "account-123"
        account.email = "test@example.com"
        return account

    @pytest.fixture
    def mock_verification(self):
        """Mock EmailVerification 物件"""
        verification = Mock()
        verification.account_id = "account-123"
        verification.token = "test-token"
        verification.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        verification.is_used = False
        return verification

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.exec.return_value.first.return_value = None
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def forgot_password_request(self):
        """忘記密碼請求"""
        return ForgotPasswordRequest(email="test@example.com")

    @pytest.mark.asyncio
    async def test_forgot_password_success(self, mock_db_session, mock_account, forgot_password_request):
        """測試成功發送重設密碼郵件"""
        # Arrange
        mock_db_session.exec.return_value.first.side_effect = [mock_account, None]
        
        with patch('src.auth.services.password_reset_service.generate_verification_token') as mock_generate_token,             patch('src.auth.services.password_reset_service.EmailService') as MockEmailService,             patch('src.auth.services.password_reset_service.datetime') as mock_datetime:
            
            mock_generate_token.return_value = "reset-token-123"
            mock_email_service = AsyncMock()
            MockEmailService.return_value = mock_email_service
            
            # Mock datetime.now()
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act
            result = await forgot_password(forgot_password_request, mock_db_session)
            
            # Assert
            assert result["message"] == "如果此電子郵件存在於系統中，您將收到重設密碼的郵件"
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_email_service.send_password_reset_email.assert_called_once_with(
                "test@example.com", 
                "reset-token-123"
            )

    @pytest.mark.asyncio
    async def test_forgot_password_account_not_found(self, mock_db_session, forgot_password_request):
        """測試帳號不存在的情況"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act
        result = await forgot_password(forgot_password_request, mock_db_session)
        
        # Assert
        assert result["message"] == "如果此電子郵件存在於系統中，您將收到重設密碼的郵件"
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_forgot_password_invalidates_existing_token(self, mock_db_session, mock_account, forgot_password_request, mock_verification):
        """測試現有未過期的 token 會被設為無效"""
        # Arrange
        # 第一次查詢回傳帳號，第二次查詢回傳現有的驗證記錄
        mock_db_session.exec.return_value.first.side_effect = [mock_account, mock_verification]
        
        with patch('src.auth.services.password_reset_service.generate_verification_token') as mock_generate_token,             patch('src.auth.services.password_reset_service.EmailService') as MockEmailService,             patch('src.auth.services.password_reset_service.datetime') as mock_datetime:
            
            mock_generate_token.return_value = "new-token-456"
            mock_email_service = AsyncMock()
            MockEmailService.return_value = mock_email_service
            
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act
            result = await forgot_password(forgot_password_request, mock_db_session)
            
            # Assert
            assert mock_verification.is_used is True
            assert mock_db_session.add.call_count == 2  # 舊的和新的驗證記錄
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_forgot_password_token_generation(self, mock_db_session, mock_account, forgot_password_request):
        """測試 Token 生成和設定"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = mock_account
        
        with patch('src.auth.services.password_reset_service.generate_verification_token') as mock_generate_token,             patch('src.auth.services.password_reset_service.EmailService') as MockEmailService,             patch('src.auth.services.password_reset_service.datetime') as mock_datetime:
            
            mock_generate_token.return_value = "generated-token"
            mock_email_service = AsyncMock()
            MockEmailService.return_value = mock_email_service
            
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            expected_expiry = mock_now + timedelta(hours=1)
            
            # Act
            await forgot_password(forgot_password_request, mock_db_session)
            
            # Assert
            added_object = mock_db_session.add.call_args[0][0]
            assert added_object.account_id == "account-123"
            assert added_object.token == "generated-token"
            assert added_object.expiry == expected_expiry

    @pytest.mark.asyncio
    async def test_forgot_password_email_service_error(self, mock_db_session, mock_account, forgot_password_request):
        """測試郵件服務錯誤處理"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = mock_account
        
        with patch('src.auth.services.password_reset_service.generate_verification_token') as mock_generate_token,             patch('src.auth.services.password_reset_service.EmailService') as MockEmailService,             patch('src.auth.services.password_reset_service.datetime') as mock_datetime:
            
            mock_generate_token.return_value = "test-token"
            mock_email_service = AsyncMock()
            mock_email_service.send_password_reset_email.side_effect = Exception("郵件服務錯誤")
            MockEmailService.return_value = mock_email_service
            
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act & Assert
            with pytest.raises(Exception, match="郵件服務錯誤"):
                await forgot_password(forgot_password_request, mock_db_session)


class TestResetPassword:
    """重設密碼功能測試類別"""

    @pytest.fixture
    def mock_verification(self):
        """Mock EmailVerification 物件"""
        verification = Mock()
        verification.account_id = "account-123"
        verification.token = "reset-token"
        verification.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        verification.is_used = False
        return verification

    @pytest.fixture
    def mock_account(self):
        """Mock Account 物件"""
        account = Mock()
        account.account_id = "account-123"
        account.email = "test@example.com"
        account.password = "old_hashed_password"
        return account

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.exec.return_value.first.return_value = None
        session.get.return_value = None
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def reset_password_request(self):
        """重設密碼請求"""
        return ResetPasswordRequest(
            token="reset-token",
            password="New!password123"
        )

    @pytest.mark.asyncio
    async def test_reset_password_success(self, mock_db_session, mock_verification, mock_account, reset_password_request):
        """測試成功重設密碼"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = mock_verification
        mock_db_session.get.return_value = mock_account
        
        with patch('src.auth.services.password_reset_service.get_password_hash') as mock_hash:
            mock_hash.return_value = "new_hashed_password"
            
            # Act
            result = await reset_password(reset_password_request, mock_db_session)
            
            # Assert
            assert result["message"] == "密碼重設成功"
            assert mock_account.password == "new_hashed_password"
            assert mock_verification.is_used is True
            assert mock_db_session.add.call_count == 2  # account 和 verification
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, mock_db_session, reset_password_request):
        """測試無效的 token"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(reset_password_request, mock_db_session)
        
        assert exc_info.value.status_code == 400
        assert "無效或過期的重設密碼連結" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self, mock_db_session, reset_password_request):
        """測試過期的 token"""
        # Arrange
        expired_verification = Mock()
        expired_verification.token = "reset-token"
        expired_verification.expiry = datetime.now(timezone.utc) - timedelta(hours=1)  # 已過期
        expired_verification.is_used = False
        
        mock_db_session.exec.return_value.first.return_value = None  # 查詢會過濾掉過期的
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(reset_password_request, mock_db_session)
        
        assert exc_info.value.status_code == 400
        assert "無效或過期的重設密碼連結" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_used_token(self, mock_db_session, reset_password_request):
        """測試已使用的 token"""
        # Arrange
        used_verification = Mock()
        used_verification.token = "reset-token"
        used_verification.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        used_verification.is_used = True
        
        mock_db_session.exec.return_value.first.return_value = None  # 查詢會過濾掉已使用的
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(reset_password_request, mock_db_session)
        
        assert exc_info.value.status_code == 400
        assert "無效或過期的重設密碼連結" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_account_not_found(self, mock_db_session, mock_verification, reset_password_request):
        """測試找不到對應的帳號"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = mock_verification
        mock_db_session.get.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(reset_password_request, mock_db_session)
        
        assert exc_info.value.status_code == 400
        assert "找不到對應的帳號" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_token_validation_query(self, mock_db_session, reset_password_request):
        """測試 token 驗證的查詢條件"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None
        
        with patch('src.auth.services.password_reset_service.datetime') as mock_datetime:
            
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act & Assert
            with pytest.raises(HTTPException):
                await reset_password(reset_password_request, mock_db_session)

    @pytest.mark.asyncio
    async def test_reset_password_hash_function_called(self, mock_db_session, mock_verification, mock_account, reset_password_request):
        """測試密碼雜湊函數被正確調用"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = mock_verification
        mock_db_session.get.return_value = mock_account
        
        with patch('src.auth.services.password_reset_service.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_new_password"
            
            # Act
            await reset_password(reset_password_request, mock_db_session)
            
            # Assert
            mock_hash.assert_called_once_with("New!password123")

    @pytest.mark.asyncio
    async def test_reset_password_multiple_valid_tokens(self, mock_db_session, mock_account, reset_password_request):
        """測試多個有效 token 的情況（應該使用查詢到的第一個）"""
        # Arrange
        verification1 = Mock()
        verification1.account_id = "account-123"
        verification1.is_used = False
        
        mock_db_session.exec.return_value.first.return_value = verification1
        mock_db_session.get.return_value = mock_account
        
        with patch('src.auth.services.password_reset_service.get_password_hash') as mock_hash:
            mock_hash.return_value = "new_hashed_password"
            
            # Act
            result = await reset_password(reset_password_request, mock_db_session)
            
            # Assert
            assert result["message"] == "密碼重設成功"
            assert verification1.is_used is True

    
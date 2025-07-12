"""
Account Service 單元測試
測試 src.auth.services.account_service 中的所有函數
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.auth.services.account_service import (
    register,
    login,
    update_user,
    update_password,
    get_user_profile,
    _create_account_and_user
)
from src.auth.models import UserRole
from src.auth.schemas import LoginResponse, UserResponse


class TestAccountService:
    """Account Service 測試類別"""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_db_session, register_request):
        """測試成功註冊用戶"""
        # Arrange - 模擬資料庫查詢結果為空（用戶不存在）
        mock_db_session.exec.return_value.first.return_value = None
        
        with patch('src.auth.services.account_service.generate_verification_token') as mock_gen_token, \
             patch('src.auth.services.account_service.send_verification_email') as mock_send_email, \
             patch('src.auth.services.account_service._create_account_and_user') as mock_create, \
             patch('src.auth.services.account_service.EmailVerification') as mock_email_verification:
            
            # 模擬建立的用戶
            mock_user = Mock()
            mock_user.name = register_request.name
            mock_user.role = UserRole.CLIENT
            mock_user.account_id = "test_account_id"
            mock_create.return_value = mock_user
            
            # 模擬 EmailVerification
            mock_verification = Mock()
            mock_email_verification.return_value = mock_verification
            
            mock_gen_token.return_value = "test_token_123"
            mock_send_email.return_value = None

            # Act
            result = await register(register_request, mock_db_session)

            # Assert
            assert result.name == register_request.name
            assert result.role == UserRole.CLIENT
            mock_create.assert_called_once()
            assert mock_db_session.add.call_count >= 1  # EmailVerification
            mock_db_session.commit.assert_called_once()
            mock_send_email.assert_called_once_with(register_request.email, "test_token_123")

    @pytest.mark.asyncio
    async def test_register_email_already_exists(self, mock_db_session, register_request, sample_account):
        """測試註冊時電子郵件已存在"""
        # Arrange - 模擬資料庫查詢結果返回現有帳號
        mock_db_session.exec.return_value.first.return_value = sample_account

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register(register_request, mock_db_session)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_email_send_failure(self, mock_db_session, register_request):
        """測試註冊時郵件發送失敗（不應影響註冊流程）"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None
        
        with patch('src.auth.services.account_service.generate_verification_token') as mock_gen_token, \
             patch('src.auth.services.account_service.send_verification_email') as mock_send_email, \
             patch('src.auth.services.account_service._create_account_and_user') as mock_create, \
             patch('src.auth.services.account_service.EmailVerification') as mock_email_verification, \
             patch('builtins.print') as mock_print:
            
            # 模擬建立的用戶
            mock_user = Mock()
            mock_user.name = register_request.name
            mock_user.account_id = "test_account_id"
            mock_create.return_value = mock_user
            
            # 模擬 EmailVerification
            mock_verification = Mock()
            mock_email_verification.return_value = mock_verification
            
            mock_gen_token.return_value = "test_token_123"
            mock_send_email.side_effect = Exception("郵件服務錯誤")

            # Act
            result = await register(register_request, mock_db_session)

            # Assert - 即使郵件發送失敗，註冊仍應成功
            assert result.name == register_request.name
            mock_db_session.commit.assert_called_once()
            mock_print.assert_called_once()  # 確認錯誤被記錄

    @pytest.mark.asyncio
    async def test_register_database_error(self, mock_db_session, register_request):
        """測試註冊時資料庫錯誤"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None
        mock_db_session.commit.side_effect = Exception("資料庫連線失敗")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register(register_request, mock_db_session)

        assert exc_info.value.status_code == 500
        assert "Failed to register user" in exc_info.value.detail
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_success(self, mock_db_session, login_request, sample_account):
        """測試成功登入"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = sample_account
        
        with patch('src.auth.services.account_service.verify_password') as mock_verify, \
             patch('src.auth.services.account_service.create_access_token') as mock_create_token:
            
            mock_verify.return_value = True
            mock_create_token.return_value = "test_jwt_token"

            # Act
            result = await login(login_request, mock_db_session)

            # Assert
            assert isinstance(result, LoginResponse)
            assert result.access_token == "test_jwt_token"
            assert result.token_type == "bearer"
            mock_verify.assert_called_once_with(login_request.password, sample_account.password)

    @pytest.mark.asyncio
    async def test_login_account_not_found(self, mock_db_session, login_request):
        """測試登入時帳號不存在"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(login_request, mock_db_session)

        assert exc_info.value.status_code == 401
        assert "帳號或密碼錯誤" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_db_session, login_request, sample_account):
        """測試登入時密碼錯誤"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = sample_account
        
        with patch('src.auth.services.account_service.verify_password') as mock_verify:
            mock_verify.return_value = False

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await login(login_request, mock_db_session)

            assert exc_info.value.status_code == 401
            assert "帳號或密碼錯誤" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_unverified_account(self, mock_db_session, login_request, unverified_account):
        """測試登入時帳號未驗證"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = unverified_account
        
        with patch('src.auth.services.account_service.verify_password') as mock_verify:
            mock_verify.return_value = True

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await login(login_request, mock_db_session)

            assert exc_info.value.status_code == 401
            assert "請先驗證您的電子郵件" in exc_info.value.detail

    def test_create_account_and_user_success(self, mock_db_session):
        """測試成功建立帳號和用戶"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None  # 用戶不存在
        
        with patch('src.auth.services.account_service.get_password_hash') as mock_hash, \
             patch('src.auth.services.account_service.Account') as mock_account_class, \
             patch('src.auth.services.account_service.User') as mock_user_class, \
             patch('src.auth.services.account_service.select') as mock_select:
            
            mock_hash.return_value = "hashed_password"
            
            # Mock select query
            mock_select.return_value = Mock()
            
            # 模擬 Account 建立
            mock_account = Mock()
            mock_account.account_id = "test_account_id"
            mock_account_class.return_value = mock_account
            
            # 模擬 User 建立
            mock_user = Mock()
            mock_user.name = "測試用戶"
            mock_user.gender = "male"
            mock_user.age = 25
            mock_user.role = UserRole.CLIENT
            mock_user_class.return_value = mock_user

            # Act
            result = _create_account_and_user(
                session=mock_db_session,
                email="test@example.com",
                password="password123",
                name="測試用戶",
                gender="male",
                age=25
            )

            # Assert
            assert result.name == "測試用戶"
            assert result.gender == "male"
            assert result.age == 25
            assert result.role == UserRole.CLIENT
            assert mock_db_session.add.call_count == 2  # Account + User
            assert mock_db_session.flush.call_count == 2

    def test_create_account_and_user_email_exists(self, mock_db_session, sample_account):
        """測試建立帳號時電子郵件已存在"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = sample_account

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            _create_account_and_user(
                session=mock_db_session,
                email="test@example.com",
                password="password123",
                name="測試用戶",
                gender="male",
                age=25
            )

        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_db_session, update_user_request, sample_account, sample_user):
        """測試成功更新用戶資料"""
        # Arrange
        mock_db_session.exec.return_value.first.side_effect = [sample_account, sample_user, sample_account]
        
        # Act
        result = await update_user("test@example.com", update_user_request, mock_db_session)

        # Assert
        assert isinstance(result, UserResponse)
        assert result.name == update_user_request.name
        assert result.age == update_user_request.age
        assert result.phone == update_user_request.phone
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_account_not_found(self, mock_db_session, update_user_request):
        """測試更新用戶時帳號不存在"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_user("nonexistent@example.com", update_user_request, mock_db_session)

        assert exc_info.value.status_code == 404
        assert "使用者不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, mock_db_session, update_user_request, sample_account):
        """測試更新用戶時用戶資料不存在"""
        # Arrange
        mock_db_session.exec.return_value.first.side_effect = [sample_account, None]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_user("test@example.com", update_user_request, mock_db_session)

        assert exc_info.value.status_code == 404
        assert "使用者資料不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_user_database_error(self, mock_db_session, update_user_request, sample_account, sample_user):
        """測試更新用戶時資料庫錯誤"""
        # Arrange
        mock_db_session.exec.return_value.first.side_effect = [sample_account, sample_user]
        mock_db_session.commit.side_effect = Exception("資料庫更新失敗")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_user("test@example.com", update_user_request, mock_db_session)

        assert exc_info.value.status_code == 500
        assert "更新使用者資料失敗" in exc_info.value.detail
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_password_success(self, mock_db_session, sample_account):
        """測試成功更新密碼"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = sample_account
        
        with patch('src.auth.services.account_service.verify_password') as mock_verify, \
             patch('src.auth.services.account_service.get_password_hash') as mock_hash:
            
            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"

            # Act
            result = await update_password("test@example.com", "old_password", "new_password", mock_db_session)

            # Assert
            assert result["message"] == "密碼已更新成功"
            # 檢查函數被正確調用
            mock_verify.assert_called_once_with("old_password", "$2b$12$hashed_password_here")
            mock_hash.assert_called_once_with("new_password")
            # 檢查 account 的 password 是否被更新為新的 hash
            assert sample_account.password == "new_hashed_password"
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_password_account_not_found(self, mock_db_session):
        """測試更新密碼時帳號不存在"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_password("nonexistent@example.com", "old_password", "new_password", mock_db_session)

        assert exc_info.value.status_code == 404
        assert "使用者不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_password_wrong_old_password(self, mock_db_session, sample_account):
        """測試更新密碼時舊密碼錯誤"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = sample_account
        
        with patch('src.auth.services.account_service.verify_password') as mock_verify:
            mock_verify.return_value = False

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await update_password("test@example.com", "wrong_password", "new_password", mock_db_session)

            assert exc_info.value.status_code == 401
            assert "舊密碼錯誤" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_password_database_error(self, mock_db_session, sample_account):
        """測試更新密碼時資料庫錯誤"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = sample_account
        mock_db_session.commit.side_effect = Exception("資料庫更新失敗")
        
        with patch('src.auth.services.account_service.verify_password') as mock_verify, \
             patch('src.auth.services.account_service.get_password_hash') as mock_hash:
            
            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await update_password("test@example.com", "old_password", "new_password", mock_db_session)

            assert exc_info.value.status_code == 500
            assert "更新密碼失敗" in exc_info.value.detail
            mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, mock_db_session, sample_account, sample_user):
        """測試成功取得用戶資料"""
        # Arrange
        # 模擬 JOIN 查詢結果
        mock_result = Mock()
        mock_result.User = sample_user
        mock_result.email = sample_account.email
        mock_db_session.exec.return_value.first.side_effect = [sample_account, mock_result]

        # Act
        result = await get_user_profile("test@example.com", mock_db_session)

        # Assert
        assert isinstance(result, UserResponse)
        assert result.user_id == sample_user.user_id
        assert result.name == sample_user.name
        assert result.email == sample_account.email
        assert result.role == sample_user.role

    @pytest.mark.asyncio
    async def test_get_user_profile_account_not_found(self, mock_db_session):
        """測試取得用戶資料時帳號不存在"""
        # Arrange
        mock_db_session.exec.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_profile("nonexistent@example.com", mock_db_session)

        assert exc_info.value.status_code == 404
        assert "使用者不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_user_profile_user_data_not_found(self, mock_db_session, sample_account):
        """測試取得用戶資料時用戶資料不存在"""
        # Arrange
        mock_db_session.exec.return_value.first.side_effect = [sample_account, None]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_profile("test@example.com", mock_db_session)

        assert exc_info.value.status_code == 404
        assert "使用者資料不存在" in exc_info.value.detail
"""
Email Verification Service 單元測試
測試 src.auth.services.email_verification_service 中的所有函數
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, ANY
from fastapi import HTTPException
from datetime import datetime, timedelta

import src.course.models
import src.therapist.models

from src.auth.services.email_verification_service import (
    generate_verification_token,
    send_verification_email,
    verify_email,
    resend_verification
)


class TestEmailVerificationService:
    """Email Verification Service 測試類別"""

    def test_generate_verification_token(self):
        """測試生成驗證 Token"""
        # Act
        token = generate_verification_token()
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 10  # secrets.token_urlsafe(32) 應該產生長度合理的 token
        
        # 測試每次生成的 token 都不同
        token2 = generate_verification_token()
        assert token != token2

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self):
        """測試成功發送驗證郵件"""
        # Arrange
        test_email = "test@example.com"
        test_token = "test_token_123"
        
        with patch('src.auth.services.email_verification_service.EmailService') as mock_email_service_class, \
             patch('src.auth.services.email_verification_service.TypeAdapter') as mock_type_adapter, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            # Mock EmailService 實例
            mock_email_service = Mock()
            mock_email_service.send_verification_email = AsyncMock()
            mock_email_service_class.return_value = mock_email_service
            
            # Mock TypeAdapter
            mock_adapter = Mock()
            mock_adapter.validate_python.return_value = test_email
            mock_type_adapter.return_value = mock_adapter
            
            # Act
            await send_verification_email(test_email, test_token)
            
            # Assert
            mock_email_service.send_verification_email.assert_called_once_with(test_email, test_token)
            mock_logging.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_email_failure(self):
        """測試發送驗證郵件失敗"""
        # Arrange
        test_email = "test@example.com"
        test_token = "test_token_123"
        
        with patch('src.auth.services.email_verification_service.EmailService') as mock_email_service_class, \
             patch('src.auth.services.email_verification_service.TypeAdapter') as mock_type_adapter, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            mock_email_service = Mock()
            mock_email_service.send_verification_email = AsyncMock(side_effect=Exception("郵件服務錯誤"))
            mock_email_service_class.return_value = mock_email_service
            
            mock_adapter = Mock()
            mock_adapter.validate_python.return_value = test_email
            mock_type_adapter.return_value = mock_adapter
            
            # Act & Assert
            with pytest.raises(Exception, match="郵件服務錯誤"):
                await send_verification_email(test_email, test_token)
                
            mock_logging.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_success(self, mock_db_session):
        """測試成功驗證電子郵件"""
        # Arrange
        test_token = "valid_token_123"
        
        # Mock EmailVerification
        mock_verification = Mock()
        mock_verification.account_id = "test_account_id"
        mock_verification.is_used = False
        mock_verification.expiry = datetime.now() + timedelta(hours=1)  # 未過期
        
        # Mock Account
        mock_account = Mock()
        mock_account.email = "test@example.com"
        mock_account.is_verified = False
        
        # 設定 session.exec 的回傳值
        mock_db_session.exec.return_value.first.return_value = mock_verification
        mock_db_session.get.return_value = mock_account
        
        with patch('src.auth.services.email_verification_service.select') as mock_select, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            mock_select.return_value = Mock()
            
            # Act
            result = await verify_email(test_token, mock_db_session)
            
            # Assert
            assert result["message"] == "電子郵件驗證成功"
            assert mock_verification.is_used == True
            assert mock_account.is_verified == True
            mock_db_session.add.assert_called()
            mock_db_session.commit.assert_called_once()
            mock_logging.info.assert_called()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, mock_db_session):
        """測試使用無效 Token 驗證"""
        # Arrange
        test_token = "invalid_token"
        mock_db_session.exec.return_value.first.return_value = None
        
        with patch('src.auth.services.email_verification_service.select') as mock_select, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            mock_select.return_value = Mock()
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await verify_email(test_token, mock_db_session)
            
            assert exc_info.value.status_code == 400
            assert "無效或過期的驗證碼" in exc_info.value.detail
            mock_logging.warning.assert_called()

    @pytest.mark.asyncio
    async def test_verify_email_expired_token(self, mock_db_session):
        """測試使用過期 Token 驗證"""
        # Arrange
        test_token = "expired_token"
        # 因為 verify_email 中的查詢會過濾掉過期的 token，所以查詢結果應為 None
        mock_db_session.exec.return_value.first.return_value = None
        
        with patch('src.auth.services.email_verification_service.select') as mock_select, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            mock_select.return_value = Mock()
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await verify_email(test_token, mock_db_session)
            
            assert exc_info.value.status_code == 400
            assert "無效或過期的驗證碼" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_email_account_not_found(self, mock_db_session):
        """測試驗證時找不到對應帳號"""
        # Arrange
        test_token = "valid_token"
        
        mock_verification = Mock()
        mock_verification.account_id = "nonexistent_account_id"
        mock_verification.is_used = False
        mock_verification.expiry = datetime.now() + timedelta(hours=1)
        
        mock_db_session.exec.return_value.first.return_value = mock_verification
        mock_db_session.get.return_value = None  # 找不到帳號
        
        with patch('src.auth.services.email_verification_service.select') as mock_select, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            mock_select.return_value = Mock()
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await verify_email(test_token, mock_db_session)
            
            assert exc_info.value.status_code == 400
            assert "找不到對應的帳號" in exc_info.value.detail
            mock_logging.error.assert_called()

    @pytest.mark.asyncio
    async def test_resend_verification_success(self, mock_db_session):
        """測試成功重新發送驗證郵件"""
        # Arrange
        test_email = "test@example.com"
        
        mock_account = Mock()
        mock_account.account_id = "test_account_id"
        mock_account.email = test_email
        mock_account.is_verified = False
        
        # 模擬第一次查詢找到帳號，第二次查詢找不到有效 token
        mock_db_session.exec.return_value.first.side_effect = [mock_account, None]
        
        with patch('src.auth.services.email_verification_service.generate_verification_token') as mock_gen_token, \
             patch('src.auth.services.email_verification_service.send_verification_email') as mock_send_email, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:

            mock_gen_token.return_value = "new_token_123"
            mock_send_email.return_value = None

            # Act
            result = await resend_verification(test_email, mock_db_session)
            
            # Assert
            assert result["message"] == "驗證郵件已重新發送"
            mock_db_session.add.assert_called_once()
            
            # 驗證傳遞給 add 的物件是否正確
            added_object = mock_db_session.add.call_args[0][0]
            assert added_object.account_id == "test_account_id"
            assert added_object.token == "new_token_123"

            mock_db_session.commit.assert_called_once()
            mock_send_email.assert_called_once_with(test_email, "new_token_123")
            mock_logging.info.assert_called()

    @pytest.mark.asyncio
    async def test_resend_verification_invalid_account(self, mock_db_session):
        """測試重新發送驗證郵件到無效帳號"""
        # Arrange
        test_email = "invalid@example.com"
        mock_db_session.exec.return_value.first.return_value = None
        
        with patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await resend_verification(test_email, mock_db_session)
            
            assert exc_info.value.status_code == 400
            assert "無效的請求" in exc_info.value.detail
            mock_logging.warning.assert_called()

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(self, mock_db_session):
        """測試重新發送驗證郵件到已驗證帳號"""
        # Arrange
        test_email = "verified@example.com"
        
        mock_account = Mock()
        mock_account.is_verified = True  # 已驗證
        
        mock_db_session.exec.return_value.first.return_value = mock_account
        
        with patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await resend_verification(test_email, mock_db_session)
            
            assert exc_info.value.status_code == 400
            assert "無效的請求" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_resend_verification_active_token_exists(self, mock_db_session):
        """測試重新發送驗證郵件時已有有效驗證碼"""
        # Arrange
        test_email = "test@example.com"
        
        mock_account = Mock()
        mock_account.account_id = "test_account_id"
        mock_account.is_verified = False
        
        mock_active_verification = Mock()
        
        # 第一次查詢找到帳號，第二次查詢找到有效驗證碼
        mock_db_session.exec.return_value.first.side_effect = [mock_account, mock_active_verification]
        
        with patch('src.auth.services.email_verification_service.logging') as mock_logging:
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await resend_verification(test_email, mock_db_session)
            
            assert exc_info.value.status_code == 400
            assert "已有一個有效的驗證碼" in exc_info.value.detail
            mock_logging.info.assert_called()

    @pytest.mark.asyncio
    async def test_resend_verification_email_send_failure(self, mock_db_session):
        """測試重新發送驗證郵件時郵件發送失敗"""
        # Arrange
        test_email = "test@example.com"
        
        mock_account = Mock()
        mock_account.account_id = "test_account_id"
        mock_account.is_verified = False
        
        # 模擬第一次查詢找到帳號，第二次查詢找不到有效 token
        mock_db_session.exec.return_value.first.side_effect = [mock_account, None]
        
        with patch('src.auth.services.email_verification_service.generate_verification_token') as mock_gen_token, \
             patch('src.auth.services.email_verification_service.send_verification_email') as mock_send_email, \
             patch('src.auth.services.email_verification_service.logging') as mock_logging:

            mock_gen_token.return_value = "new_token_123"
            mock_send_email.side_effect = Exception("郵件服務錯誤")

            # Act & Assert
            with pytest.raises(Exception, match="郵件服務錯誤"):
                await resend_verification(test_email, mock_db_session)
            
            mock_db_session.rollback.assert_called_once()
            mock_logging.error.assert_called()

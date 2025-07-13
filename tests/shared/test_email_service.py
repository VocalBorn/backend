"""
Email Service 單元測試
測試 src.shared.services.email_service 中的 EmailService 類別和相關功能
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from fastapi import HTTPException
import asyncio
import httpx
from pydantic import EmailStr

from src.shared.services.email_service import (
    EmailService,
    EmailTemplates
)


class TestEmailTemplates:
    """Email Templates 測試類別"""

    def test_verification_email_template(self):
        """測試驗證郵件模板"""
        # Arrange
        verification_url = "https://example.com/verify/token123"
        
        # Act
        html_content = EmailTemplates.verification_email(verification_url)
        
        # Assert
        assert isinstance(html_content, str)
        assert verification_url in html_content
        assert "驗證您的電子郵件" in html_content
        assert "VocalBorn" in html_content
        assert "24 小時後失效" in html_content
        assert "<!DOCTYPE html>" in html_content

    def test_reset_password_email_template(self):
        """測試重設密碼郵件模板"""
        # Arrange
        reset_url = "https://example.com/reset/token456"
        
        # Act
        html_content = EmailTemplates.reset_password_email(reset_url)
        
        # Assert
        assert isinstance(html_content, str)
        assert reset_url in html_content
        assert "重設密碼請求" in html_content
        assert "VocalBorn" in html_content
        assert "1 小時後失效" in html_content
        assert "安全提醒" in html_content
        assert "<!DOCTYPE html>" in html_content

    def test_verification_email_template_escaping(self):
        """測試驗證郵件模板的特殊字符處理"""
        # Arrange
        verification_url = "https://example.com/verify?token=abc&redirect=home"
        
        # Act
        html_content = EmailTemplates.verification_email(verification_url)
        
        # Assert
        assert verification_url in html_content
        # URL 應該在兩處出現（按鈕和文字）
        assert html_content.count(verification_url) >= 2

    def test_reset_password_email_template_escaping(self):
        """測試重設密碼郵件模板的特殊字符處理"""
        # Arrange
        reset_url = "https://example.com/reset?token=xyz&user=123"
        
        # Act
        html_content = EmailTemplates.reset_password_email(reset_url)
        
        # Assert
        assert reset_url in html_content
        assert html_content.count(reset_url) >= 2


class TestEmailService:
    """Email Service 測試類別"""

    @pytest.fixture
    def mock_environment(self):
        """Mock 環境變數"""
        return {
            'EMAIL_SERVICE_HOST': 'localhost',
            'EMAIL_SERVICE_PORT': '8080',
            'BASE_URL': 'https://example.com'
        }

    @pytest.fixture
    def email_service(self, mock_environment):
        """建立 EmailService 實例"""
        with patch.dict('os.environ', mock_environment):
            return EmailService()

    def test_init_success(self, mock_environment):
        """測試成功初始化 EmailService"""
        # Act
        with patch.dict('os.environ', mock_environment):
            service = EmailService()
        
        # Assert
        assert service.service_host == "localhost"
        assert service.service_port == "8080"
        assert service.base_url == "http://localhost:8080"
        assert service.connect_timeout == 5.0
        assert service.read_timeout == 10.0
        assert service.max_retries == 2

    def test_init_missing_host(self):
        """測試缺少 EMAIL_SERVICE_HOST 環境變數"""
        # Arrange
        env = {'EMAIL_SERVICE_PORT': '8080'}
        
        # Act & Assert
        with patch.dict('os.environ', env, clear=True):
            with pytest.raises(ValueError, match="未設定郵件服務"):
                EmailService()

    def test_init_missing_port(self):
        """測試缺少 EMAIL_SERVICE_PORT 環境變數"""
        # Arrange
        env = {'EMAIL_SERVICE_HOST': 'localhost'}
        
        # Act & Assert
        with patch.dict('os.environ', env, clear=True):
            with pytest.raises(ValueError, match="未設定郵件服務"):
                EmailService()

    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service):
        """測試成功發送電子郵件"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        subject = "測試主旨"
        html_content = "<p>測試內容</p>"
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            await email_service.send_email(test_email, subject, html_content)
            
            # Assert
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            
            # 驗證 URL
            assert call_args[0][0] == "http://localhost:8080/send-email"
            
            # 驗證 payload
            payload = call_args[1]['json']
            assert payload['to'] == ["test@example.com"]
            assert payload['subject'] == subject
            assert payload['body'] == html_content

    @pytest.mark.asyncio
    async def test_send_email_server_error(self, email_service):
        """測試郵件服務器錯誤"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "伺服器內部錯誤"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await email_service.send_email(test_email, "主旨", "內容")
            
            assert exc_info.value.status_code == 500
            assert "郵件服務錯誤" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_send_email_connection_error_with_retry(self, email_service):
        """測試連線錯誤與重試機制"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        
        with patch('httpx.AsyncClient') as mock_client_class, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            mock_client = AsyncMock()
            # 前兩次連線失敗，第三次成功
            mock_client.post.side_effect = [
                Exception("連線失敗"),
                Exception("連線失敗"),
                Mock(status_code=200)
            ]
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            await email_service.send_email(test_email, "主旨", "內容")
            
            # Assert
            assert mock_client.post.call_count == 3
            assert mock_sleep.call_count == 2  # 重試前的延遲

    @pytest.mark.asyncio
    async def test_send_email_max_retries_exceeded(self, email_service):
        """測試超過最大重試次數"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        
        with patch('httpx.AsyncClient') as mock_client_class, \
             patch('asyncio.sleep', new_callable=AsyncMock):
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("連線失敗")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await email_service.send_email(test_email, "主旨", "內容")
            
            assert exc_info.value.status_code == 500
            assert "郵件服務連接失敗" in exc_info.value.detail
            assert mock_client.post.call_count == 3  # 原始 + 2 次重試

    @pytest.mark.asyncio
    async def test_send_email_timeout_error(self, email_service):
        """測試超時錯誤"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = asyncio.TimeoutError()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await email_service.send_email(test_email, "主旨", "內容")
            
            assert exc_info.value.status_code == 500
            assert "發送郵件超時" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_send_email_unexpected_error(self, email_service):
        """測試未預期的錯誤"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("未預期錯誤")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await email_service.send_email(test_email, "主旨", "內容")
            
            assert exc_info.value.status_code == 500
            assert "發送郵件時發生錯誤" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_send_verification_email(self, email_service):
        """測試發送驗證郵件"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        test_token = "verification_token_123"
        
        with patch.object(email_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # Act
            await email_service.send_verification_email(test_email, test_token)
            
            # Assert
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args['to_email'] == test_email
            assert call_args['subject'] == "驗證您的電子郵件"
            assert test_token in call_args['html_content']
            assert "verify_email.html" in call_args['html_content']

    @pytest.mark.asyncio
    async def test_send_verification_email_custom_base_url(self, email_service):
        """測試使用自定義 base URL 發送驗證郵件"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        test_token = "verification_token_123"
        custom_base_url = "https://custom.example.com"
        
        with patch.object(email_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # Act
            await email_service.send_verification_email(test_email, test_token, custom_base_url)
            
            # Assert
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert custom_base_url in call_args['html_content']

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, email_service):
        """測試發送重設密碼郵件"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        test_token = "reset_token_456"
        
        with patch.object(email_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # Act
            await email_service.send_password_reset_email(test_email, test_token)
            
            # Assert
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args['to_email'] == test_email
            assert call_args['subject'] == "重設您的密碼"
            assert test_token in call_args['html_content']
            assert "/user/reset-password/" in call_args['html_content']

    @pytest.mark.asyncio
    async def test_send_password_reset_email_custom_base_url(self, email_service):
        """測試使用自定義 base URL 發送重設密碼郵件"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        test_token = "reset_token_456"
        custom_base_url = "https://custom.example.com"
        
        with patch.object(email_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # Act
            await email_service.send_password_reset_email(test_email, test_token, custom_base_url)
            
            # Assert
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert custom_base_url in call_args['html_content']

    @pytest.mark.asyncio
    async def test_retry_delay_increases(self, email_service):
        """測試重試延遲時間遞增"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        
        with patch('httpx.AsyncClient') as mock_client_class, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [
                Exception("連線失敗"),
                Exception("連線失敗"),
                Mock(status_code=200)
            ]
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            await email_service.send_email(test_email, "主旨", "內容")
            
            # Assert
            # 檢查延遲時間遞增：第一次重試延遲1秒，第二次重試延遲2秒
            mock_sleep.assert_has_calls([call(1), call(2)])

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, email_service):
        """測試超時配置正確設定"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = Mock(status_code=200)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            await email_service.send_email(test_email, "主旨", "內容")
            
            # Assert
            # 檢查 AsyncClient 是否使用正確的超時配置
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            
            timeout_config = call_kwargs['timeout']
            assert timeout_config.connect == 5.0
            assert timeout_config.read == 10.0
            assert timeout_config.write == 10.0

    @pytest.mark.asyncio
    async def test_custom_headers_support(self, email_service):
        """測試自定義標頭支援（雖然當前實作未使用）"""
        # Arrange
        test_email: EmailStr = "test@example.com"
        custom_headers = {"X-Custom-Header": "test-value"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = Mock(status_code=200)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            await email_service.send_email(
                test_email, 
                "主旨", 
                "內容", 
                custom_headers=custom_headers
            )
            
            # Assert - 目前實作中自定義標頭未被使用，但不應影響功能
            mock_client.post.assert_called_once()

    def test_base_url_construction(self, mock_environment):
        """測試 base URL 構建"""
        # Act
        with patch.dict('os.environ', mock_environment):
            service = EmailService()
        
        # Assert
        expected_base_url = f"http://{mock_environment['EMAIL_SERVICE_HOST']}:{mock_environment['EMAIL_SERVICE_PORT']}"
        assert service.base_url == expected_base_url
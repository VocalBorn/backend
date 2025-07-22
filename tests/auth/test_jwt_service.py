"""
JWT Service 單元測試
測試 src.auth.services.jwt_service 中的所有函數
"""

import pytest
import time
from datetime import timezone
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
from jose import jwt

from src.auth.services.jwt_service import (
    create_access_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM
)


class TestJwtService:
    """JWT Service 測試類別"""
    
    @pytest.fixture(autouse=True)
    def patch_secret_key(self, monkeypatch):
        """Automatically patch SECRET_KEY for all tests in this class."""
        monkeypatch.setattr(
            'src.auth.services.jwt_service.SECRET_KEY',
            'a_super_secret_key_for_testing'
        )

    def test_create_access_token_with_custom_expiry(self):
        """測試建立 Token 使用自定義過期時間"""
        # Arrange
        test_data = {"sub": "test@example.com"}
        custom_expires = timedelta(hours=2)
        mock_secret = "test_secret_key_for_testing"
        
        with patch('src.auth.services.jwt_service.datetime') as mock_datetime, \
             patch('src.auth.services.jwt_service.SECRET_KEY', mock_secret):
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act
            token = create_access_token(test_data, custom_expires)
            
            # Assert
            assert isinstance(token, str)
            assert len(token) > 50  # JWT token 應該有合理的長度
            
            # 解碼並驗證內容
            decoded = jwt.decode(token, mock_secret, algorithms=[ALGORITHM], options={"verify_exp": False})
            assert decoded["sub"] == "test@example.com"
            
            # 驗證過期時間
            expected_exp = mock_now + custom_expires
            assert decoded["exp"] == expected_exp.timestamp()

    def test_create_access_token_with_default_expiry(self):
        """測試建立 Token 使用預設過期時間"""
        # Arrange
        test_data = {"sub": "test@example.com", "role": "user"}
        
        with patch('src.auth.services.jwt_service.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act
            token = create_access_token(test_data)
            
            # Assert
            decoded = jwt.decode(token, 'a_super_secret_key_for_testing', algorithms=[ALGORITHM], options={"verify_exp": False})
            assert decoded["sub"] == "test@example.com"
            assert decoded["role"] == "user"
            
            # 驗證預設過期時間（15分鐘）
            expected_exp = mock_now + timedelta(minutes=15)
            assert decoded["exp"] == expected_exp.timestamp()

    def test_create_access_token_preserves_original_data(self):
        """測試建立 Token 不會修改原始資料"""
        # Arrange
        original_data = {"sub": "test@example.com", "role": "admin"}
        data_copy = original_data.copy()
        
        # Act
        create_access_token(original_data, timedelta(hours=1))
        
        # Assert - 原始資料不應被修改
        assert original_data == data_copy

    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """測試成功驗證 Token"""
        # Arrange
        test_email = "test@example.com"
        test_data = {"sub": test_email}
        
        # 建立有效的 token
        token = create_access_token(test_data, timedelta(hours=1))
        
        # Mock HTTPAuthorizationCredentials
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act
        result = await verify_token(mock_credentials)
        
        # Assert
        assert result == test_email

    @pytest.mark.asyncio
    async def test_verify_token_missing_subject(self):
        """測試驗證沒有 subject 的 Token"""
        # Arrange
        test_data = {"role": "user"}  # 沒有 "sub" 欄位
        token = create_access_token(test_data, timedelta(hours=1))
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "無效的認證憑證" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_expired(self):
        """測試驗證過期的 Token"""
        # Arrange
        test_data = {"sub": "test@example.com"}
        
        with patch('src.auth.services.jwt_service.datetime') as mock_datetime:
            # 設定 token 建立時間為過去
            past_time = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = past_time
            
            # 建立一個會立即過期的 token
            token = create_access_token(test_data, timedelta(seconds=1))
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "無效的認證憑證" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_invalid_signature(self):
        """測試驗證錯誤簽名的 Token"""
        # Arrange
        test_data = {"sub": "test@example.com"}
        
        # 使用錯誤的 SECRET_KEY 建立 token
        wrong_secret = "wrong_secret_key"
        token = jwt.encode(test_data, wrong_secret, algorithm=ALGORITHM)
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "無效的認證憑證" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_malformed_token(self):
        """測試驗證格式錯誤的 Token"""
        # Arrange
        malformed_token = "not.a.valid.jwt.token"
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = malformed_token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "無效的認證憑證" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_empty_token(self):
        """測試驗證空的 Token"""
        # Arrange
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = ""
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "無效的認證憑證" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_none_subject(self):
        """測試驗證 subject 為 None 的 Token"""
        # Arrange
        test_data = {"sub": None}
        token = create_access_token(test_data, timedelta(hours=1))
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "無效的認證憑證" in exc_info.value.detail

    def test_token_algorithm_consistency(self):
        """測試 Token 演算法一致性"""
        # Arrange
        test_data = {"sub": "test@example.com"}
        
        # Act
        token = create_access_token(test_data, timedelta(hours=1))
        
        # Assert - 確保可以用相同的演算法解碼
        decoded = jwt.decode(token, 'a_super_secret_key_for_testing', algorithms=[ALGORITHM])
        assert decoded["sub"] == "test@example.com"

    def test_multiple_tokens_are_different(self):
        """測試相同資料產生的 Token 具有不同時間戳"""
        # Arrange
        test_data = {"sub": "test@example.com"}
        
        with patch('src.auth.services.jwt_service.datetime') as mock_datetime:
            mock_now1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_now2 = datetime(2025, 1, 1, 12, 0, 1, tzinfo=timezone.utc)
            mock_datetime.now.side_effect = [mock_now1, mock_now2]

            # Act
            token1 = create_access_token(test_data, timedelta(hours=1))
            token2 = create_access_token(test_data, timedelta(hours=1))
        
        # Assert - Token 應該不同（因為時間戳不同）
        assert token1 != token2

    @pytest.mark.asyncio
    async def test_verify_token_with_additional_claims(self):
        """測試驗證包含額外聲明的 Token"""
        # Arrange
        test_data = {
            "sub": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
            "custom_field": "custom_value"
        }
        
        token = create_access_token(test_data, timedelta(hours=1))
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act
        result = await verify_token(mock_credentials)
        
        # Assert - 只回傳 subject，但不會因額外聲明而失敗
        assert result == "test@example.com"
        
        # 驗證 token 中確實包含額外聲明
        decoded = jwt.decode(token, 'a_super_secret_key_for_testing', algorithms=[ALGORITHM])
        assert decoded["role"] == "admin"
        assert decoded["permissions"] == ["read", "write"]
        assert decoded["custom_field"] == "custom_value"

    @pytest.mark.parametrize("invalid_subject", [
        "",  # 空字串
        "   ",  # 只有空格
        123,  # 數字
        [],  # 列表
        {},  # 字典
    ])
    @pytest.mark.asyncio
    async def test_verify_token_invalid_subject_types(self, invalid_subject):
        """測試驗證包含無效 subject 類型的 Token"""
        # Arrange
        test_data = {"sub": invalid_subject}
        token = create_access_token(test_data, timedelta(hours=1))
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "無效的認證憑證" in exc_info.value.detail
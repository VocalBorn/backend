"""
Password Service 單元測試
測試 src.auth.services.password_service 中的所有函數
"""

import pytest
from unittest.mock import patch
import bcrypt

from src.auth.services.password_service import (
    get_password_hash,
    verify_password
)


class TestPasswordService:
    """Password Service 測試類別"""

    def test_get_password_hash_basic(self):
        """測試基本密碼雜湊功能"""
        # Arrange
        password = "test_password_123"
        
        # Act
        hashed = get_password_hash(password)
        
        # Assert
        assert isinstance(hashed, str)
        assert len(hashed) > 20  # bcrypt hash 應該有合理的長度
        assert hashed != password  # Hash 不應該等於原始密碼
        assert hashed.startswith("$2b$")  # bcrypt hash 的格式

    def test_get_password_hash_different_for_same_password(self):
        """測試相同密碼產生不同的 Hash（因為 salt）"""
        # Arrange
        password = "test_password_123"
        
        # Act
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Assert
        assert hash1 != hash2  # 每次 hash 都應該不同（因為隨機 salt）

    def test_get_password_hash_unicode_password(self):
        """測試包含 Unicode 字符的密碼"""
        # Arrange
        password = "密碼測試123!@#"
        
        # Act
        hashed = get_password_hash(password)
        
        # Assert
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_get_password_hash_empty_password(self):
        """測試空密碼"""
        # Arrange
        password = ""
        
        # Act
        hashed = get_password_hash(password)
        
        # Assert
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_get_password_hash_long_password(self):
        """測試很長的密碼"""
        # Arrange
        password = "a" * 1000  # 1000 個字符的密碼
        
        # Act & Assert
        with pytest.raises(ValueError, match="Password must not exceed 72 bytes for bcrypt."):
            get_password_hash(password)

    @pytest.mark.parametrize("password", [
        "simple",
        "Complex_P@ssw0rd!",
        "123456789",
        "!@#$%^&*()",
        "Ω≈ç√∫˜µ≤≥÷",  # 特殊 Unicode 字符
        "   spaces   ",
        "\n\t\r",  # 控制字符
    ])
    def test_get_password_hash_various_passwords(self, password):
        """測試各種不同類型的密碼"""
        # Act
        hashed = get_password_hash(password)
        
        # Assert
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """測試驗證正確密碼"""
        # Arrange
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Act
        result = verify_password(password, hashed)
        
        # Assert
        assert result is True

    def test_verify_password_incorrect(self):
        """測試驗證錯誤密碼"""
        # Arrange
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(correct_password)
        
        # Act
        result = verify_password(wrong_password, hashed)
        
        # Assert
        assert result is False

    def test_verify_password_empty_passwords(self):
        """測試空密碼驗證"""
        # Arrange
        empty_password = ""
        hashed = get_password_hash(empty_password)
        
        # Act
        result_correct = verify_password("", hashed)
        result_incorrect = verify_password("not_empty", hashed)
        
        # Assert
        assert result_correct is True
        assert result_incorrect is False

    def test_verify_password_unicode(self):
        """測試 Unicode 密碼驗證"""
        # Arrange
        password = "測試密碼123!@#"
        hashed = get_password_hash(password)
        
        # Act
        result_correct = verify_password(password, hashed)
        result_incorrect = verify_password("測試密碼123!@", hashed)
        
        # Assert
        assert result_correct is True
        assert result_incorrect is False

    def test_verify_password_case_sensitive(self):
        """測試密碼大小寫敏感性"""
        # Arrange
        password = "TestPassword"
        hashed = get_password_hash(password)
        
        # Act
        result_correct = verify_password("TestPassword", hashed)
        result_wrong_case = verify_password("testpassword", hashed)
        
        # Assert
        assert result_correct is True
        assert result_wrong_case is False

    

    def test_verify_password_with_string_hash(self):
        """測試使用 string 類型的 Hash 進行驗證"""
        # Arrange
        password = "test_password"
        string_hash = get_password_hash(password)  # 這會回傳 string
        
        # Act
        result = verify_password(password, string_hash)
        
        # Assert
        assert result is True

    def test_verify_password_invalid_hash_format(self):
        """測試無效的 Hash 格式"""
        # Arrange
        password = "test_password"
        invalid_hash = "not_a_valid_hash"
        
        # Act & Assert
        # bcrypt 會拋出 ValueError 當 hash 格式無效
        with pytest.raises(ValueError):
            verify_password(password, invalid_hash)

    def test_verify_password_empty_hash(self):
        """測試空 Hash"""
        # Arrange
        password = "test_password"
        empty_hash = ""
        
        # Act & Assert
        with pytest.raises(ValueError):
            verify_password(password, empty_hash)

    def test_password_hash_and_verify_integration(self):
        """測試密碼雜湊和驗證的整合
        注意：bcrypt 只驗證前 72 bytes，超過會 raise ValueError
        """
        # Arrange
        passwords = [
            "simple",
            "Complex_P@ssw0rd!",
            "密碼測試123",
            "   spaces   ",
            "very_long_password_" * 10  # 這個密碼超過 72 bytes
        ]

        for password in passwords:
            if len(password.encode('utf-8')) > 72:
                # 超過 bcrypt 限制，應該 raise ValueError
                with pytest.raises(ValueError):
                    get_password_hash(password)
                continue
            # Act
            hashed = get_password_hash(password)

            # Assert
            assert verify_password(password, hashed) is True
            assert verify_password(password + "_wrong", hashed) is False

    @patch('src.auth.services.password_service.bcrypt.gensalt')
    @patch('src.auth.services.password_service.bcrypt.hashpw')
    def test_get_password_hash_uses_bcrypt_correctly(self, mock_hashpw, mock_gensalt):
        """測試 get_password_hash 正確使用 bcrypt"""
        # Arrange
        password = "test_password"
        mock_salt = b"mock_salt"
        mock_hash = b"mock_hash"
        
        mock_gensalt.return_value = mock_salt
        mock_hashpw.return_value = mock_hash
        
        # Act
        result = get_password_hash(password)
        
        # Assert
        mock_gensalt.assert_called_once()
        mock_hashpw.assert_called_once_with(password.encode('utf-8'), mock_salt)
        assert result == mock_hash.decode('utf-8')

    @patch('src.auth.services.password_service.bcrypt.checkpw')
    def test_verify_password_uses_bcrypt_correctly(self, mock_checkpw):
        """測試 verify_password 正確使用 bcrypt"""
        # Arrange
        password = "test_password"
        hashed = "$2b$12$mock_hash"
        mock_checkpw.return_value = True
        
        # Act
        result = verify_password(password, hashed)
        
        # Assert
        mock_checkpw.assert_called_once_with(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )
        assert result is True

    def test_verify_password_handles_none_hash(self):
        """測試處理 None Hash 的情況"""
        # Arrange
        password = "test_password"
        
        # Act & Assert
        assert verify_password(password, None) is False

    def test_password_complexity_preserved(self):
        """測試複雜密碼的完整性保持"""
        # Arrange
        complex_passwords = [
            "Aa1!",  # 最小複雜度
            "ThisIsAVeryLongPasswordWithNumbers123AndSpecialChars!@#",
            "密碼WithMixed語言123!",
            "🔐🔑Password123!",  # 包含 emoji
        ]
        
        for password in complex_passwords:
            # Act
            hashed = get_password_hash(password)
            
            # Assert
            assert verify_password(password, hashed) is True
            
            # 測試相似但不同的密碼
            if len(password) > 1:
                wrong_password = password[:-1]  # 去掉最後一個字符
                assert verify_password(wrong_password, hashed) is False
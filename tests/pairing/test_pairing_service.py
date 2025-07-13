"""
Pairing Service 單元測試
測試 src.pairing.services.pairing_service 中的配對相關功能
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from fastapi import HTTPException

from src.pairing.services.pairing_service import (
    _generate_token_code,
    generate_pairing_token,
    validate_token,
    use_token,
    get_therapist_tokens,
    revoke_token,
    get_active_tokens_count,
    TOKEN_CHARSET,
    TOKEN_LENGTH
)
from src.pairing.schemas import PairingTokenCreate

from src.pairing.models import PairingToken


class TestGenerateTokenCode:
    """生成 Token 代碼功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.exec.return_value.first.return_value = None  # 沒有重複的 token
        return session

    def test_generate_token_code_success(self, mock_db_session):
        """測試成功生成 token 代碼"""
        # Act
        token_code = _generate_token_code(mock_db_session)
        
        # Assert
        assert isinstance(token_code, str)
        assert len(token_code) == TOKEN_LENGTH
        assert all(c in TOKEN_CHARSET for c in token_code)

    def test_generate_token_code_unique_check(self, mock_db_session):
        """測試 token 代碼唯一性檢查"""
        # Arrange
        existing_token = Mock()
        existing_token.token_code = "EXISTING1"
        
        # 第一次查詢返回現有 token，第二次返回 None
        mock_db_session.exec.return_value.first.side_effect = [existing_token, None]
        
        with patch('src.pairing.services.pairing_service.random.choices') as mock_choices:
            # 第一次生成重複的，第二次生成唯一的
            mock_choices.side_effect = [
                list("EXISTING1"),
                list("NEWTOKEN1")
            ]
            
            # Act
            token_code = _generate_token_code(mock_db_session)
            
            # Assert
            assert token_code == "NEWTOKEN1"
            assert mock_db_session.exec.call_count == 2

    def test_generate_token_code_max_attempts_exceeded(self, mock_db_session):
        """測試超過最大嘗試次數"""
        # Arrange
        existing_token = Mock()
        mock_db_session.exec.return_value.first.return_value = existing_token  # 總是返回重複
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            _generate_token_code(mock_db_session)
        
        assert exc_info.value.status_code == 500
        assert "無法生成唯一的token代碼" in exc_info.value.detail

    def test_token_charset_validity(self):
        """測試 token 字符集不包含容易混淆的字符"""
        # Assert
        assert "0" not in TOKEN_CHARSET  # 數字 0
        assert "O" not in TOKEN_CHARSET  # 字母 O
        assert "1" not in TOKEN_CHARSET  # 數字 1
        assert "I" not in TOKEN_CHARSET  # 字母 I
        assert "l" not in TOKEN_CHARSET  # 小寫 l
        
        # 確保包含其他有效字符
        assert "A" in TOKEN_CHARSET
        assert "2" in TOKEN_CHARSET
        assert "9" in TOKEN_CHARSET


class TestGeneratePairingToken:
    """生成配對 Token 功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.exec.return_value.first.return_value = None
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        return session

    @pytest.fixture
    def mock_therapist(self):
        """Mock 治療師用戶"""
        therapist = Mock()
        therapist.user_id = uuid4()
        therapist.role = "THERAPIST"
        therapist.name = "Dr. Smith"
        return therapist

    @pytest.fixture
    def token_create_data(self):
        """Token 建立資料"""
        return PairingTokenCreate(
            expires_in_hours=24,
            max_uses=5
        )

    @pytest.fixture
    def mock_token(self):
        """Mock PairingToken 物件"""
        token = Mock()
        token.token_id = uuid4()
        token.token_code = "ABCD1234"
        token.created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        token.expires_at = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        token.max_uses = 5
        token.current_uses = 0
        token.is_used = False
        return token

    def test_generate_pairing_token_success(
        self, 
        mock_db_session, 
        mock_therapist, 
        token_create_data, 
        mock_token
    ):
        """測試成功生成配對 token"""
        # Arrange
        therapist_id = mock_therapist.user_id
        base_url = "https://example.com"
        
        # 第一次查詢返回治療師，後續查詢用於 token 代碼生成
        mock_db_session.exec.return_value.first.side_effect = [mock_therapist, None]
        
        with patch('src.pairing.services.pairing_service._generate_token_code') as mock_generate, \
             patch('src.pairing.services.pairing_service.PairingToken') as MockToken, \
             patch('src.pairing.services.pairing_service.datetime') as mock_datetime:
            
            mock_generate.return_value = "ABCD1234"
            MockToken.return_value = mock_token
            
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act
            result = generate_pairing_token(mock_db_session, therapist_id, token_create_data, base_url)
            
            # Assert
            assert result.token_code == "ABCD1234"
            assert result.qr_data == "https://example.com/pair/ABCD1234"
            assert result.max_uses == 5
            assert result.current_uses == 0
            assert not result.is_used
            
            mock_db_session.add.assert_called_once_with(mock_token)
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(mock_token)

    def test_generate_pairing_token_therapist_not_found(
        self, 
        mock_db_session, 
        token_create_data
    ):
        """測試治療師不存在"""
        # Arrange
        therapist_id = uuid4()
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            generate_pairing_token(mock_db_session, therapist_id, token_create_data)
        
        assert exc_info.value.status_code == 404
        assert "治療師不存在" in exc_info.value.detail

    def test_generate_pairing_token_default_base_url(
        self, 
        mock_db_session, 
        mock_therapist, 
        token_create_data, 
        mock_token
    ):
        """測試使用預設 base URL"""
        # Arrange
        therapist_id = mock_therapist.user_id
        mock_db_session.exec.return_value.first.side_effect = [mock_therapist, None]
        
        with patch('src.pairing.services.pairing_service._generate_token_code') as mock_generate, \
             patch('src.pairing.services.pairing_service.PairingToken') as MockToken, \
             patch('src.pairing.services.pairing_service.datetime'), \
             patch('os.getenv') as mock_getenv:
            
            mock_generate.return_value = "TEST1234"
            MockToken.return_value = mock_token
            mock_getenv.return_value = "http://localhost:8000"
            
            # Act（不提供 base_url 參數）
            result = generate_pairing_token(mock_db_session, therapist_id, token_create_data)
            
            # Assert
            assert result.qr_data == "http://localhost:8000/pair/TEST1234"

    def test_generate_pairing_token_expiry_calculation(
        self, 
        mock_db_session, 
        mock_therapist, 
        mock_token
    ):
        """測試過期時間計算"""
        # Arrange
        therapist_id = mock_therapist.user_id
        token_data = PairingTokenCreate(expires_in_hours=48, max_uses=1)
        mock_db_session.exec.return_value.first.side_effect = [mock_therapist, None]
        
        with patch('src.pairing.services.pairing_service._generate_token_code') as mock_generate, \
             patch('src.pairing.services.pairing_service.PairingToken') as MockToken, \
             patch('src.pairing.services.pairing_service.datetime') as mock_datetime:
            
            mock_generate.return_value = "EXPIRES1"
            MockToken.return_value = mock_token
            
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            expected_expiry = mock_now + timedelta(hours=48)
            
            # Act
            generate_pairing_token(mock_db_session, therapist_id, token_data)
            
            # Assert
            MockToken.assert_called_once()
            call_kwargs = MockToken.call_args[1]
            assert call_kwargs['expires_at'] == expected_expiry


class TestValidateToken:
    """驗證 Token 功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        return session

    @pytest.fixture
    def mock_valid_token(self):
        """Mock 有效的 Token"""
        token = Mock()
        token.token_code = "VALID123"
        token.therapist_id = uuid4()
        token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token.max_uses = 5
        token.current_uses = 2
        return token

    @pytest.fixture
    def mock_therapist(self):
        """Mock 治療師"""
        therapist = Mock()
        therapist.user_id = uuid4()
        therapist.name = "Dr. Johnson"
        return therapist

    def test_validate_token_success(
        self, 
        mock_db_session, 
        mock_valid_token, 
        mock_therapist
    ):
        """測試成功驗證 token"""
        # Arrange
        token_code = "VALID123"
        # 第一次查詢返回 token，第二次查詢返回治療師
        mock_db_session.exec.return_value.first.side_effect = [mock_valid_token, mock_therapist]
        
        # Act
        result = validate_token(mock_db_session, token_code)
        
        # Assert
        assert result.is_valid is True
        assert result.token_code == "VALID123"
        assert result.therapist_name == "Dr. Johnson"
        assert result.remaining_uses == 3  # 5 - 2

    def test_validate_token_not_found(self, mock_db_session):
        """測試 token 不存在"""
        # Arrange
        token_code = "NOTFOUND"
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act
        result = validate_token(mock_db_session, token_code)
        
        # Assert
        assert result.is_valid is False
        assert result.token_code is None
        assert result.therapist_name is None

    def test_validate_token_expired(self, mock_db_session):
        """測試過期的 token"""
        # Arrange
        token_code = "EXPIRED1"
        expired_token = Mock()
        expired_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # 已過期
        mock_db_session.exec.return_value.first.return_value = expired_token
        
        # Act
        result = validate_token(mock_db_session, token_code)
        
        # Assert
        assert result.is_valid is False

    def test_validate_token_max_uses_reached(self, mock_db_session):
        """測試使用次數已達上限"""
        # Arrange
        token_code = "MAXUSED1"
        max_used_token = Mock()
        max_used_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        max_used_token.max_uses = 3
        max_used_token.current_uses = 3  # 已達上限
        mock_db_session.exec.return_value.first.return_value = max_used_token
        
        # Act
        result = validate_token(mock_db_session, token_code)
        
        # Assert
        assert result.is_valid is False

    def test_validate_token_no_therapist_info(
        self, 
        mock_db_session, 
        mock_valid_token
    ):
        """測試找不到治療師資訊"""
        # Arrange
        token_code = "VALID123"
        # 第一次查詢返回 token，第二次查詢治療師返回 None
        mock_db_session.exec.return_value.first.side_effect = [mock_valid_token, None]
        
        # Act
        result = validate_token(mock_db_session, token_code)
        
        # Assert
        assert result.is_valid is True
        assert result.therapist_name is None  # 找不到治療師但 token 仍有效


class TestUseToken:
    """使用 Token 進行配對功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def mock_client(self):
        """Mock 客戶用戶"""
        client = Mock()
        client.user_id = uuid4()
        client.role = "CLIENT"
        client.name = "John Doe"
        return client

    @pytest.fixture
    def mock_therapist(self):
        """Mock 治療師用戶"""
        therapist = Mock()
        therapist.user_id = uuid4()
        therapist.role = "THERAPIST"
        therapist.name = "Dr. Smith"
        return therapist

    @pytest.fixture
    def mock_valid_token(self, mock_therapist):
        """Mock 有效的 Token"""
        token = Mock()
        token.token_id = uuid4()
        token.token_code = "PAIR1234"
        token.therapist_id = mock_therapist.user_id
        token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token.max_uses = 5
        token.current_uses = 0
        token.used_by_client_id = None
        token.used_at = None
        return token

    @pytest.mark.asyncio
    async def test_use_token_success(
        self, 
        mock_db_session, 
        mock_client, 
        mock_therapist, 
        mock_valid_token
    ):
        """測試成功使用 token 進行配對"""
        # Arrange
        token_code = "PAIR1234"
        client_id = mock_client.user_id
        
        # 查詢順序：客戶、token、檢查現有配對關係、治療師
        mock_db_session.exec.return_value.first.side_effect = [
            mock_client,      # 查詢客戶
            mock_valid_token, # 查詢 token
            None,             # 檢查現有配對關係
            mock_therapist    # 查詢治療師
        ]
        
        with patch('src.pairing.services.pairing_service.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act
            result = use_token(mock_db_session, token_code, client_id)
            
            # Assert
            assert result.success is True
            assert result.message == "配對成功"
            assert result.therapist_name == "Dr. Smith"
            assert result.therapist_id == mock_therapist.user_id
            
            # 檢查 token 狀態更新
            assert mock_valid_token.current_uses == 1
            assert mock_valid_token.used_by_client_id == client_id
            assert mock_valid_token.used_at == mock_now
            
            # 檢查資料庫操作
            assert mock_db_session.add.call_count == 2  # pairing 和 token
            mock_db_session.commit.assert_called_once()

    def test_use_token_client_not_found(self, mock_db_session):
        """測試客戶不存在"""
        # Arrange
        token_code = "PAIR1234"
        client_id = uuid4()
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_token(mock_db_session, token_code, client_id)
        
        assert exc_info.value.status_code == 404
        assert "客戶不存在" in exc_info.value.detail

    def test_use_token_token_not_found(self, mock_db_session, mock_client):
        """測試 token 不存在"""
        # Arrange
        token_code = "NOTFOUND"
        client_id = mock_client.user_id
        
        # 第一次查詢返回客戶，第二次查詢 token 返回 None
        mock_db_session.exec.return_value.first.side_effect = [mock_client, None]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_token(mock_db_session, token_code, client_id)
        
        assert exc_info.value.status_code == 404
        assert "Token不存在" in exc_info.value.detail

    def test_use_token_expired(self, mock_db_session, mock_client):
        """測試使用過期的 token"""
        # Arrange
        token_code = "EXPIRED1"
        client_id = mock_client.user_id
        
        expired_token = Mock()
        expired_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        mock_db_session.exec.return_value.first.side_effect = [mock_client, expired_token]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_token(mock_db_session, token_code, client_id)
        
        assert exc_info.value.status_code == 400
        assert "Token已過期" in exc_info.value.detail

    def test_use_token_max_uses_reached(self, mock_db_session, mock_client):
        """測試使用次數已達上限"""
        # Arrange
        token_code = "MAXUSED1"
        client_id = mock_client.user_id
        
        max_used_token = Mock()
        max_used_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        max_used_token.max_uses = 3
        max_used_token.current_uses = 3
        
        mock_db_session.exec.return_value.first.side_effect = [mock_client, max_used_token]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_token(mock_db_session, token_code, client_id)
        
        assert exc_info.value.status_code == 400
        assert "Token使用次數已達上限" in exc_info.value.detail

    def test_use_token_already_paired(
        self, 
        mock_db_session, 
        mock_client, 
        mock_valid_token
    ):
        """測試客戶已與治療師配對"""
        # Arrange
        token_code = "PAIR1234"
        client_id = mock_client.user_id
        
        existing_pairing = Mock()
        existing_pairing.is_active = True
        
        # 查詢順序：客戶、token、現有配對關係
        mock_db_session.exec.return_value.first.side_effect = [
            mock_client,        # 查詢客戶
            mock_valid_token,   # 查詢 token
            existing_pairing    # 找到現有配對關係
        ]
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_token(mock_db_session, token_code, client_id)
        
        assert exc_info.value.status_code == 400
        assert "您已經與此治療師配對" in exc_info.value.detail

    def test_use_token_max_uses_becomes_used(
        self, 
        mock_db_session, 
        mock_client, 
        mock_therapist
    ):
        """測試當使用次數達到上限時 token 被標記為已使用"""
        # Arrange
        token_code = "LASTUSE1"
        client_id = mock_client.user_id
        
        # 創建一個即將達到最大使用次數的 token
        almost_max_token = Mock()
        almost_max_token.token_id = uuid4()
        almost_max_token.token_code = token_code
        almost_max_token.therapist_id = mock_therapist.user_id
        almost_max_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        almost_max_token.max_uses = 3
        almost_max_token.current_uses = 2  # 使用這一次後就會達到上限
        almost_max_token.used_by_client_id = None
        almost_max_token.used_at = None
        
        mock_db_session.exec.return_value.first.side_effect = [
            mock_client,        # 查詢客戶
            almost_max_token,   # 查詢 token
            None,               # 檢查現有配對關係
            mock_therapist      # 查詢治療師
        ]
        
        with patch('src.pairing.services.pairing_service.datetime') as mock_datetime:
            
            mock_now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            # Act
            result = use_token(mock_db_session, token_code, client_id)
            
            # Assert
            assert result.success is True
            assert almost_max_token.current_uses == 3  # 增加到 3
            assert almost_max_token.is_used is True    # 標記為已使用


class TestGetTherapistTokens:
    """取得治療師 Token 列表功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        return session

    @pytest.fixture
    def mock_therapist(self):
        """Mock 治療師用戶"""
        therapist = Mock()
        therapist.user_id = uuid4()
        therapist.role = "THERAPIST"
        return therapist

    @pytest.fixture
    def mock_tokens(self):
        """Mock Token 列表"""
        tokens = []
        for i in range(3):
            token = Mock()
            token.token_id = uuid4()
            token.token_code = f"TOKEN{i+1}"
            token.created_at = datetime(2025, 1, i+1, 12, 0, 0, tzinfo=timezone.utc)
            token.expires_at = datetime(2025, 1, i+2, 12, 0, 0, tzinfo=timezone.utc)
            token.max_uses = 5
            token.current_uses = i
            token.is_used = False
            tokens.append(token)
        return tokens

    def test_get_therapist_tokens_success(
        self, 
        mock_db_session, 
        mock_therapist, 
        mock_tokens
    ):
        """測試成功取得治療師 token 列表"""
        # Arrange
        therapist_id = mock_therapist.user_id
        
        # 第一次查詢返回治療師，第二次查詢返回 tokens
        mock_db_session.exec.return_value.first.return_value = mock_therapist
        mock_db_session.exec.return_value.all.return_value = mock_tokens
        
        # Act
        result = get_therapist_tokens(mock_db_session, therapist_id)
        
        # Assert
        assert result.total_count == 3
        assert len(result.tokens) == 3
        assert result.tokens[0].token_code == "TOKEN1"
        assert result.tokens[1].token_code == "TOKEN2"
        assert result.tokens[2].token_code == "TOKEN3"

    def test_get_therapist_tokens_therapist_not_found(self, mock_db_session):
        """測試治療師不存在"""
        # Arrange
        therapist_id = uuid4()
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_therapist_tokens(mock_db_session, therapist_id)
        
        assert exc_info.value.status_code == 404
        assert "治療師不存在" in exc_info.value.detail

    def test_get_therapist_tokens_empty_list(self, mock_db_session, mock_therapist):
        """測試空的 token 列表"""
        # Arrange
        therapist_id = mock_therapist.user_id
        
        mock_db_session.exec.return_value.first.return_value = mock_therapist
        mock_db_session.exec.return_value.all.return_value = []
        
        # Act
        result = get_therapist_tokens(mock_db_session, therapist_id)
        
        # Assert
        assert result.total_count == 0
        assert len(result.tokens) == 0


class TestRevokeToken:
    """撤銷 Token 功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def mock_token(self):
        """Mock Token 物件"""
        token = Mock()
        token.token_id = uuid4()
        token.therapist_id = uuid4()
        token.max_uses = 5
        token.current_uses = 2
        token.is_used = False
        return token

    def test_revoke_token_success(self, mock_db_session, mock_token):
        """測試成功撤銷 token"""
        # Arrange
        token_id = mock_token.token_id
        therapist_id = mock_token.therapist_id
        mock_db_session.exec.return_value.first.return_value = mock_token
        
        # Act
        result = revoke_token(mock_db_session, token_id, therapist_id)
        
        # Assert
        assert result is True
        assert mock_token.is_used is True
        assert mock_token.current_uses == mock_token.max_uses
        mock_db_session.add.assert_called_once_with(mock_token)
        mock_db_session.commit.assert_called_once()

    def test_revoke_token_not_found(self, mock_db_session):
        """測試撤銷不存在的 token"""
        # Arrange
        token_id = uuid4()
        therapist_id = uuid4()
        mock_db_session.exec.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            revoke_token(mock_db_session, token_id, therapist_id)
        
        assert exc_info.value.status_code == 404
        assert "Token不存在" in exc_info.value.detail

    def test_revoke_token_wrong_therapist(self, mock_db_session):
        """測試撤銷其他治療師的 token"""
        # Arrange
        token_id = uuid4()
        wrong_therapist_id = uuid4()
        mock_db_session.exec.return_value.first.return_value = None  # 找不到符合條件的 token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            revoke_token(mock_db_session, token_id, wrong_therapist_id)
        
        assert exc_info.value.status_code == 404
        assert "Token不存在" in exc_info.value.detail


class TestGetActiveTokensCount:
    """取得有效 Token 數量功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        return session

    def test_get_active_tokens_count_success(self, mock_db_session):
        """測試成功取得有效 token 數量"""
        # Arrange
        therapist_id = uuid4()
        
        # 創建一些 mock tokens
        active_token1 = Mock()
        active_token1.current_uses = 2
        active_token1.max_uses = 5
        
        active_token2 = Mock()
        active_token2.current_uses = 0
        active_token2.max_uses = 3
        
        max_used_token = Mock()
        max_used_token.current_uses = 5
        max_used_token.max_uses = 5  # 已達上限，不算有效
        
        mock_tokens = [active_token1, active_token2, max_used_token]
        mock_db_session.exec.return_value.all.return_value = mock_tokens
        
        # Act
        result = get_active_tokens_count(mock_db_session, therapist_id)
        
        # Assert
        assert result == 2  # 只有兩個有效的 token

    def test_get_active_tokens_count_no_active_tokens(self, mock_db_session):
        """測試沒有有效 token"""
        # Arrange
        therapist_id = uuid4()
        mock_db_session.exec.return_value.all.return_value = []
        
        # Act
        result = get_active_tokens_count(mock_db_session, therapist_id)
        
        # Assert
        assert result == 0

    def test_get_active_tokens_count_all_max_used(self, mock_db_session):
        """測試所有 token 都已達使用上限"""
        # Arrange
        therapist_id = uuid4()
        
        max_used_token1 = Mock()
        max_used_token1.current_uses = 3
        max_used_token1.max_uses = 3
        
        max_used_token2 = Mock()
        max_used_token2.current_uses = 1
        max_used_token2.max_uses = 1
        
        mock_tokens = [max_used_token1, max_used_token2]
        mock_db_session.exec.return_value.all.return_value = mock_tokens
        
        # Act
        result = get_active_tokens_count(mock_db_session, therapist_id)
        
        # Assert
        assert result == 0
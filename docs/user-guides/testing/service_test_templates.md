# 服務測試模板

這個文件提供函數式和類別式服務的標準測試模板，確保測試品質的一致性。

## 函數式服務測試模板

### 基本 CRUD 服務測試

```python
"""
函數式服務測試範例 - CRUD 操作
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException
from sqlmodel import Session

from src.your_module.services import (
    create_item,
    get_item_by_id,
    update_item,
    delete_item
)
from src.your_module.models import Item
from src.your_module.schemas import ItemCreate, ItemUpdate


class TestItemCRUDServices:
    """測試 Item CRUD 服務"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock(spec=Session)
        return session
    
    @pytest.fixture
    def sample_item_data(self):
        """測試用的 Item 資料"""
        return ItemCreate(
            name="測試項目",
            description="這是一個測試項目",
            is_active=True
        )
    
    @pytest.fixture
    def existing_item(self):
        """現有的 Item 實例"""
        return Item(
            id=1,
            name="現有項目",
            description="現有項目描述",
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_create_item_success(self, mock_db_session, sample_item_data):
        """測試成功建立項目"""
        # Arrange
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        # Act
        result = await create_item(sample_item_data, mock_db_session)
        
        # Assert
        assert result.name == sample_item_data.name
        assert result.description == sample_item_data.description
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_item_by_id_success(self, mock_db_session, existing_item):
        """測試成功取得項目"""
        # Arrange
        mock_db_session.get.return_value = existing_item
        
        # Act
        result = await get_item_by_id(1, mock_db_session)
        
        # Assert
        assert result == existing_item
        mock_db_session.get.assert_called_once_with(Item, 1)
    
    @pytest.mark.asyncio
    async def test_get_item_by_id_not_found(self, mock_db_session):
        """測試取得不存在的項目"""
        # Arrange
        mock_db_session.get.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_item_by_id(999, mock_db_session)
        
        assert exc_info.value.status_code == 404
        assert "不存在" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_item_success(self, mock_db_session, existing_item):
        """測試成功更新項目"""
        # Arrange
        mock_db_session.get.return_value = existing_item
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        update_data = ItemUpdate(name="更新後的名稱")
        
        # Act
        result = await update_item(1, update_data, mock_db_session)
        
        # Assert
        assert result.name == "更新後的名稱"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_item_success(self, mock_db_session, existing_item):
        """測試成功刪除項目"""
        # Arrange
        mock_db_session.get.return_value = existing_item
        mock_db_session.delete = Mock()
        mock_db_session.commit = Mock()
        
        # Act
        result = await delete_item(1, mock_db_session)
        
        # Assert
        assert result is True
        mock_db_session.delete.assert_called_once_with(existing_item)
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_db_session, sample_item_data):
        """測試資料庫錯誤處理"""
        # Arrange
        mock_db_session.commit.side_effect = Exception("資料庫連線失敗")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_item(sample_item_data, mock_db_session)
        
        assert exc_info.value.status_code == 500
```

### 驗證服務測試模板

```python
"""
函數式驗證服務測試範例
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.your_module.services import validate_email, validate_password_strength


class TestValidationServices:
    """測試驗證服務"""
    
    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", True),
        ("test.email+tag@domain.co.uk", True),
        ("invalid-email", False),
        ("@domain.com", False),
        ("user@", False),
    ])
    @pytest.mark.asyncio
    async def test_validate_email(self, email, expected):
        """測試電子郵件驗證"""
        # Act
        result = await validate_email(email)
        
        # Assert
        assert result == expected
    
    @pytest.mark.parametrize("password,expected_valid", [
        ("StrongP@ssw0rd", True),
        ("weak", False),
        ("12345678", False),
        ("NoNumbers!", False),
        ("nonumbersorspecial", False),
    ])
    @pytest.mark.asyncio
    async def test_validate_password_strength(self, password, expected_valid):
        """測試密碼強度驗證"""
        # Act & Assert
        if expected_valid:
            result = await validate_password_strength(password)
            assert result is True
        else:
            with pytest.raises(HTTPException) as exc_info:
                await validate_password_strength(password)
            assert exc_info.value.status_code == 400
```

## 類別式服務測試模板

### 基本類別式服務測試

```python
"""
類別式服務測試範例
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from src.your_module.services import EmailService, StorageService
from src.your_module.exceptions import ServiceError


class TestEmailService:
    """測試電子郵件服務"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock 配置"""
        return {
            "EMAIL_SERVICE_HOST": "localhost",
            "EMAIL_SERVICE_PORT": "8080",
            "BASE_URL": "http://localhost:3000"
        }
    
    @pytest.fixture
    def email_service(self, mock_config):
        """建立 EmailService 實例"""
        with patch.dict('os.environ', mock_config):
            return EmailService()
    
    @pytest.mark.asyncio
    async def test_init_success(self, mock_config):
        """測試成功初始化"""
        with patch.dict('os.environ', mock_config):
            service = EmailService()
            assert service.service_host == "localhost"
            assert service.service_port == "8080"
            assert service.base_url == "http://localhost:8080"
    
    def test_init_missing_config(self):
        """測試缺少配置時初始化失敗"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="未設定郵件服務"):
                EmailService()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_send_email_success(self, mock_post, email_service):
        """測試成功發送電子郵件"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Act
        await email_service.send_email(
            to_email="test@example.com",
            subject="測試主旨",
            html_content="<p>測試內容</p>"
        )
        
        # Assert
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['to'] == ["test@example.com"]
        assert call_args[1]['json']['subject'] == "測試主旨"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_send_email_server_error(self, mock_post, email_service):
        """測試郵件服務器錯誤"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "伺服器內部錯誤"}
        mock_post.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await email_service.send_email(
                to_email="test@example.com",
                subject="測試主旨",
                html_content="<p>測試內容</p>"
            )
        
        assert exc_info.value.status_code == 500
        assert "伺服器內部錯誤" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_send_email_with_retry(self, mock_post, email_service):
        """測試重試機制"""
        # Arrange
        from httpx import ConnectError
        mock_post.side_effect = [
            ConnectError("連線失敗"),  # 第一次失敗
            ConnectError("連線失敗"),  # 第二次失敗
            Mock(status_code=200)      # 第三次成功
        ]
        
        # Act
        await email_service.send_email(
            to_email="test@example.com",
            subject="測試主旨",
            html_content="<p>測試內容</p>"
        )
        
        # Assert
        assert mock_post.call_count == 3  # 重試了 2 次
    
    @pytest.mark.asyncio
    async def test_send_verification_email(self, email_service):
        """測試發送驗證郵件"""
        with patch.object(email_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # Act
            await email_service.send_verification_email(
                to_email="test@example.com",
                token="test_token_123"
            )
            
            # Assert
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args['to_email'] == "test@example.com"
            assert call_args['subject'] == "驗證您的電子郵件"
            assert "test_token_123" in call_args['html_content']
```

### 有狀態服務測試模板

```python
"""
有狀態服務測試範例
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import UploadFile
import io

from src.storage.storage_service import StorageService, StorageServiceError


class TestStorageService:
    """測試儲存服務"""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Mock MinIO 客戶端"""
        client = Mock()
        client.bucket_exists.return_value = True
        client.put_object.return_value = None
        client.get_presigned_url.return_value = "https://example.com/file.jpg"
        return client
    
    @pytest.fixture
    def storage_service(self, mock_minio_client):
        """建立 StorageService 實例"""
        with patch('src.storage.storage_service.Minio', return_value=mock_minio_client):
            with patch.dict('os.environ', {
                'MINIO_ENDPOINT': 'localhost:9000',
                'MINIO_ACCESS_KEY': 'test_key',
                'MINIO_SECRET_KEY': 'test_secret',
                'MINIO_SECURE': 'false'
            }):
                return StorageService("test-bucket")
    
    @pytest.fixture
    def sample_file(self):
        """建立測試檔案"""
        content = b"test file content"
        file = io.BytesIO(content)
        return UploadFile(
            filename="test.jpg",
            file=file,
            size=len(content),
            headers={"content-type": "image/jpeg"}
        )
    
    def test_init_success(self, storage_service):
        """測試成功初始化"""
        assert storage_service.bucket_name == "test-bucket"
        assert storage_service.client is not None
    
    def test_init_missing_endpoint(self):
        """測試缺少端點配置"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(StorageServiceError, match="MINIO_ENDPOINT"):
                StorageService("test-bucket")
    
    def test_upload_file_success(self, storage_service, sample_file, mock_minio_client):
        """測試成功上傳檔案"""
        # Act
        result = storage_service.upload_file(sample_file, "test/file.jpg")
        
        # Assert
        assert result == "test/file.jpg"
        mock_minio_client.put_object.assert_called_once()
        
        call_args = mock_minio_client.put_object.call_args[1]
        assert call_args['bucket_name'] == "test-bucket"
        assert call_args['object_name'] == "test/file.jpg"
    
    def test_upload_file_invalid_type(self, storage_service):
        """測試上傳不支援的檔案類型"""
        # Arrange
        invalid_file = UploadFile(
            filename="test.exe",
            file=io.BytesIO(b"test"),
            size=4,
            headers={"content-type": "application/octet-stream"}
        )
        
        # Act & Assert
        with pytest.raises(StorageServiceError, match="不支援的檔案類型"):
            storage_service.upload_file(invalid_file, "test/file.exe")
    
    def test_get_presigned_url_success(self, storage_service, mock_minio_client):
        """測試成功生成預簽署 URL"""
        # Act
        result = storage_service.get_presigned_url("test/file.jpg")
        
        # Assert
        assert result == "https://example.com/file.jpg"
        mock_minio_client.get_presigned_url.assert_called_once()
    
    def test_file_exists_true(self, storage_service, mock_minio_client):
        """測試檔案存在檢查回傳 True"""
        # Arrange
        mock_minio_client.stat_object.return_value = Mock()
        
        # Act
        result = storage_service.file_exists("test/file.jpg")
        
        # Assert
        assert result is True
        mock_minio_client.stat_object.assert_called_once_with("test-bucket", "test/file.jpg")
    
    def test_service_state_persistence(self, storage_service):
        """測試服務狀態持久性"""
        # 測試多次操作後狀態仍然正確
        original_bucket = storage_service.bucket_name
        original_client = storage_service.client
        
        # 執行一些操作
        storage_service.file_exists("test1.jpg")
        storage_service.file_exists("test2.jpg")
        
        # 驗證狀態未改變
        assert storage_service.bucket_name == original_bucket
        assert storage_service.client == original_client
```

## 測試組織最佳實踐

### 1. 測試檔案命名規範
```
tests/
├── test_functional_services.py    # 函數式服務測試
├── test_class_services.py         # 類別式服務測試
└── conftest.py                     # 共用 fixtures
```

### 2. Fixture 組織
```python
# conftest.py
@pytest.fixture
def mock_db_session():
    """通用資料庫會話 mock"""
    pass

@pytest.fixture  
def mock_current_user():
    """通用當前用戶 mock"""
    pass
```

### 3. 參數化測試
```python
@pytest.mark.parametrize("input_data,expected_result,should_raise", [
    (valid_data, expected_success, False),
    (invalid_data, None, True),
])
def test_service_with_various_inputs(input_data, expected_result, should_raise):
    """使用參數化測試多種輸入情況"""
    pass
```

### 4. 異步測試標記
```python
# 所有異步函數測試都要加上這個標記
@pytest.mark.asyncio
async def test_async_service():
    pass
```

### 5. 錯誤測試模式
```python
# 測試預期的異常
with pytest.raises(HTTPException) as exc_info:
    await service_function()

assert exc_info.value.status_code == 400
assert "預期錯誤訊息" in str(exc_info.value.detail)
```
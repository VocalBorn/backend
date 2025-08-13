import logging
from datetime import timedelta
from typing import Optional
from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error
from src.shared.config.config import get_settings

logger = logging.getLogger(__name__)

# 允許的檔案類型
ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png", 
    "image/gif",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

# 檔案大小限制（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


class StorageServiceError(Exception):
    """儲存服務自定義異常"""
    pass


class StorageService:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client: Optional[Minio] = None
        self._initialize_client()
        self._ensure_bucket_exists()
    
    def _initialize_client(self):
        """初始化 MinIO 客戶端"""
        try:
            # 從配置系統獲取 MinIO 設定
            settings = get_settings()
            endpoint = settings.MINIO_ENDPOINT
            access_key = settings.MINIO_ACCESS_KEY
            secret_key = settings.MINIO_SECRET_KEY
            secure = settings.MINIO_SECURE
            
            if not endpoint:
                raise StorageServiceError("MINIO_ENDPOINT 環境變數未設定")
            
            self._client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            logger.info(f"MinIO 客戶端初始化成功，連接到 {endpoint}")
            
        except Exception as e:
            logger.error(f"MinIO 客戶端初始化失敗: {e}")
            raise StorageServiceError(f"MinIO 客戶端初始化失敗: {e}")
    
    @property
    def client(self) -> Minio:
        """取得 MinIO 客戶端"""
        if self._client is None:
            raise StorageServiceError("MinIO 客戶端未初始化")
        return self._client

    def _ensure_bucket_exists(self):
        """確保桶存在，如果不存在則建立"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"已建立桶: {self.bucket_name}")
            else:
                logger.debug(f"桶已存在: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"S3 錯誤 - 無法建立或驗證桶 '{self.bucket_name}': {e}")
            raise StorageServiceError(f"無法建立或驗證桶 '{self.bucket_name}': {e}")
        except Exception as e:
            logger.error(f"未預期的錯誤 - 檢查/建立桶 '{self.bucket_name}': {e}")
            raise StorageServiceError(f"檢查/建立桶時發生未預期錯誤: {e}")
    
    def _validate_file(self, file: UploadFile) -> None:
        """驗證檔案"""
        # 檢查檔案大小
        if file.size and file.size > MAX_FILE_SIZE:
            raise StorageServiceError(f"檔案大小超過限制 ({MAX_FILE_SIZE / (1024*1024):.1f}MB)")
        
        # 檢查檔案類型
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise StorageServiceError(f"不支援的檔案類型: {file.content_type}")
        
        # 檢查檔案名稱
        if not file.filename:
            raise StorageServiceError("檔案名稱不能為空")
        
        logger.debug(f"檔案驗證通過: {file.filename}, 大小: {file.size}, 類型: {file.content_type}")

    def upload_file(
        self,
        file: UploadFile,
        object_name: str,
    ) -> str:
        """上傳檔案到指定的桶並返回物件名稱"""
        try:
            # 驗證檔案
            self._validate_file(file)
            
            # 重置檔案指針到開頭
            file.file.seek(0)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file.file,
                length=file.size,
                content_type=file.content_type
            )
            
            logger.info(f"檔案上傳成功: {object_name} 到桶 {self.bucket_name}")
            return object_name
            
        except StorageServiceError:
            # 重新拋出我們的自定義異常
            raise
        except S3Error as e:
            logger.error(f"S3 錯誤 - 檔案上傳失敗: {e}")
            raise StorageServiceError(f"檔案上傳失敗: {e}")
        except Exception as e:
            logger.error(f"未預期的錯誤 - 檔案上傳: {e}")
            raise StorageServiceError(f"檔案上傳時發生未預期錯誤: {e}")

    def get_presigned_url(
        self,
        object_name: str,
        expires_in: timedelta = timedelta(minutes=15)
    ) -> str:
        """生成短期有效的預簽署 URL 用於查看物件"""
        try:
            url = self.client.get_presigned_url(
                "GET",
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires_in
            )
            logger.debug(f"生成預簽署 URL: {object_name}, 有效期: {expires_in}")
            return url
            
        except S3Error as e:
            logger.error(f"S3 錯誤 - 生成預簽署 URL 失敗: {e}")
            raise StorageServiceError(f"生成預簽署 URL 失敗: {e}")
        except Exception as e:
            logger.error(f"未預期的錯誤 - 生成預簽署 URL: {e}")
            raise StorageServiceError(f"生成預簽署 URL 時發生未預期錯誤: {e}")
    
    def delete_file(self, object_name: str) -> bool:
        """刪除檔案"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"檔案刪除成功: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"S3 錯誤 - 刪除檔案失敗: {e}")
            raise StorageServiceError(f"刪除檔案失敗: {e}")
        except Exception as e:
            logger.error(f"未預期的錯誤 - 刪除檔案: {e}")
            raise StorageServiceError(f"刪除檔案時發生未預期錯誤: {e}")
    
    def file_exists(self, object_name: str) -> bool:
        """檢查檔案是否存在"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
        except Exception as e:
            logger.error(f"檢查檔案存在性時發生錯誤: {e}")
            return False

# 工廠函數用於建立儲存服務實例
def create_storage_service(bucket_name: str) -> StorageService:
    """建立儲存服務實例的工廠函數"""
    return StorageService(bucket_name=bucket_name)


# 延遲初始化的儲存服務實例
def get_verification_storage_service() -> StorageService:
    """取得驗證文件儲存服務實例"""
    settings = get_settings()
    bucket_name = settings.MINIO_BUCKET_NAME or 'verification-documents'
    return create_storage_service(bucket_name)

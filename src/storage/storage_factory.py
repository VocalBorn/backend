"""
儲存服務工廠模組
提供統一的儲存服務創建和管理接口
"""

import logging
from enum import Enum
from typing import Dict, Type
from .storage_service import StorageService
from .audio_storage_service import AudioStorageService
from src.shared.config.config import get_settings

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """儲存類型枚舉"""
    DOCUMENT = "document"           # 文件儲存（PDF、Word、圖片等）
    AUDIO = "audio"                 # 音訊檔案儲存
    VIDEO = "video"                 # 視訊檔案儲存（未來擴展）
    IMAGE = "image"                 # 圖片檔案儲存（未來擴展）


class StoragePurpose(Enum):
    """儲存用途枚舉"""
    VERIFICATION = "verification"           # 驗證文件
    PRACTICE_RECORDING = "practice_recording"  # 練習錄音
    COURSE_AUDIO = "course_audio"          # 課程音訊
    USER_AVATAR = "user_avatar"            # 用戶頭像
    COURSE_MATERIAL = "course_material"    # 課程材料


class StorageServiceFactory:
    """儲存服務工廠"""
    
    # 儲存服務類型映射
    _service_classes: Dict[StorageType, Type[StorageService]] = {
        StorageType.DOCUMENT: StorageService,
        StorageType.AUDIO: AudioStorageService,
        # 未來可以添加更多類型
        # StorageType.VIDEO: VideoStorageService,
        # StorageType.IMAGE: ImageStorageService,
    }
    
    # 桶名稱配置映射
    _bucket_config_map: Dict[StoragePurpose, str] = {
        StoragePurpose.VERIFICATION: 'MINIO_BUCKET_NAME',
        StoragePurpose.PRACTICE_RECORDING: 'PRACTICE_AUDIO_BUCKET_NAME',
        StoragePurpose.COURSE_AUDIO: 'COURSE_AUDIO_BUCKET_NAME',
        StoragePurpose.USER_AVATAR: 'USER_AVATAR_BUCKET_NAME',
        StoragePurpose.COURSE_MATERIAL: 'COURSE_MATERIAL_BUCKET_NAME',
    }
    
    # 預設桶名稱
    _default_bucket_names: Dict[StoragePurpose, str] = {
        StoragePurpose.VERIFICATION: 'verification-documents',
        StoragePurpose.PRACTICE_RECORDING: 'practice-recordings',
        StoragePurpose.COURSE_AUDIO: 'course-audio',
        StoragePurpose.USER_AVATAR: 'user-avatars',
        StoragePurpose.COURSE_MATERIAL: 'course-materials',
    }
    
    @classmethod
    def create_service(
        self,
        storage_type: StorageType,
        storage_purpose: StoragePurpose
    ) -> StorageService:
        """
        創建儲存服務實例
        
        Args:
            storage_type: 儲存類型
            storage_purpose: 儲存用途
            
        Returns:
            對應的儲存服務實例
        """
        # 取得服務類別
        service_class = self._service_classes.get(storage_type)
        if not service_class:
            raise ValueError(f"不支援的儲存類型: {storage_type}")
        
        # 取得桶名稱
        bucket_name = self._get_bucket_name(storage_purpose)
        
        # 創建服務實例
        service = service_class(bucket_name)
        
        logger.info(f"創建儲存服務: {storage_type.value}/{storage_purpose.value} -> {bucket_name}")
        return service
    
    @classmethod
    def _get_bucket_name(cls, purpose: StoragePurpose) -> str:
        """取得桶名稱"""
        settings = get_settings()
        
        # 根據用途直接從配置系統取得桶名稱
        if purpose == StoragePurpose.VERIFICATION:
            return settings.MINIO_BUCKET_NAME or cls._default_bucket_names[purpose]
        elif purpose == StoragePurpose.PRACTICE_RECORDING:
            return settings.PRACTICE_AUDIO_BUCKET_NAME
        elif purpose == StoragePurpose.COURSE_AUDIO:
            return settings.COURSE_AUDIO_BUCKET_NAME
        else:
            # 對於其他用途，使用預設值
            return cls._default_bucket_names.get(purpose, 'default-bucket')


# 便利函數
def get_verification_storage() -> StorageService:
    """取得驗證文件儲存服務"""
    return StorageServiceFactory.create_service(
        StorageType.DOCUMENT, 
        StoragePurpose.VERIFICATION
    )


def get_practice_recording_storage() -> AudioStorageService:
    """取得練習錄音儲存服務"""
    return StorageServiceFactory.create_service(
        StorageType.AUDIO, 
        StoragePurpose.PRACTICE_RECORDING
    )


def get_course_audio_storage() -> AudioStorageService:
    """取得課程音訊儲存服務"""
    return StorageServiceFactory.create_service(
        StorageType.AUDIO, 
        StoragePurpose.COURSE_AUDIO
    )


def get_user_avatar_storage() -> StorageService:
    """取得用戶頭像儲存服務"""
    return StorageServiceFactory.create_service(
        StorageType.IMAGE, 
        StoragePurpose.USER_AVATAR
    )


def get_course_material_storage() -> StorageService:
    """取得課程材料儲存服務"""
    return StorageServiceFactory.create_service(
        StorageType.DOCUMENT, 
        StoragePurpose.COURSE_MATERIAL
    )

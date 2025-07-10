"""
儲存模組
提供統一的檔案儲存服務，支援多種檔案類型和儲存用途
"""

from .storage_service import StorageService, StorageServiceError
from .audio_storage_service import AudioStorageService
from .storage_factory import (
    StorageServiceFactory,
    StorageType,
    StoragePurpose,
    get_verification_storage,
    get_practice_recording_storage,
    get_course_audio_storage,
    get_user_avatar_storage,
    get_course_material_storage,
)
from .practice_recording_service import PracticeRecordingService, practice_recording_service

__all__ = [
    # 核心服務類別
    "StorageService",
    "AudioStorageService",
    "PracticeRecordingService",
    
    # 異常類型
    "StorageServiceError",
    
    # 工廠和枚舉
    "StorageServiceFactory",
    "StorageType",
    "StoragePurpose",
    
    # 便利函數
    "get_verification_storage",
    "get_practice_recording_storage",
    "get_course_audio_storage",
    "get_user_avatar_storage",
    "get_course_material_storage",
    
    # 服務實例
    "practice_recording_service",
]
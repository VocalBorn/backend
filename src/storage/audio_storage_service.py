import logging
from fastapi import UploadFile
from .storage_service import StorageService, StorageServiceError
from src.shared.config.config import get_settings

logger = logging.getLogger(__name__)

# 音訊檔案允許的類型
AUDIO_MIME_TYPES = [
    "audio/mpeg",       # MP3
    "audio/wav",        # WAV
    "audio/mp4",        # M4A
    "audio/ogg",        # OGG
    "audio/webm",       # WebM Audio
    "audio/flac",       # FLAC
    "audio/aac",        # AAC
]

# 音訊檔案大小限制（50MB）
MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024


class AudioStorageService(StorageService):
    """音訊檔案儲存服務"""
    
    def __init__(self, bucket_name: str):
        super().__init__(bucket_name)
        self.allowed_mime_types = AUDIO_MIME_TYPES
        self.max_file_size = MAX_AUDIO_FILE_SIZE
    
    def _validate_file(self, file: UploadFile) -> None:
        """驗證音訊檔案"""
        # 檢查檔案大小
        if file.size and file.size > self.max_file_size:
            raise StorageServiceError(
                f"音訊檔案大小超過限制 ({self.max_file_size / (1024*1024):.1f}MB)"
            )
        
        # 檢查檔案類型
        if file.content_type not in self.allowed_mime_types:
            raise StorageServiceError(f"不支援的音訊檔案類型: {file.content_type}")
        
        # 檢查檔案名稱
        if not file.filename:
            raise StorageServiceError("音訊檔案名稱不能為空")
        
        # 檢查檔案副檔名
        audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac', '.aac']
        if not any(file.filename.lower().endswith(ext) for ext in audio_extensions):
            raise StorageServiceError("音訊檔案副檔名不正確")
        
        logger.debug(f"音訊檔案驗證通過: {file.filename}, 大小: {file.size}, 類型: {file.content_type}")
    
    def upload_practice_audio(
        self, 
        file: UploadFile, 
        user_id: str, 
        practice_session_id: str
    ) -> str:
        """上傳練習錄音檔案"""
        file_extension = file.filename.split('.')[-1].lower()
        object_name = f"practice_recordings/{user_id}/{practice_session_id}.{file_extension}"
        
        return self.upload_file(file, object_name)
    
    def upload_course_audio(
        self, 
        file: UploadFile, 
        course_id: str, 
        chapter_id: str,
        sentence_id: str
    ) -> str:
        """上傳課程音訊檔案"""
        file_extension = file.filename.split('.')[-1].lower()
        object_name = f"course_audio/{course_id}/{chapter_id}/{sentence_id}.{file_extension}"
        
        return self.upload_file(file, object_name)


# 工廠函數
def get_practice_audio_storage_service() -> AudioStorageService:
    """取得練習錄音儲存服務"""
    settings = get_settings()
    bucket_name = settings.PRACTICE_AUDIO_BUCKET_NAME
    return AudioStorageService(bucket_name)


def get_course_audio_storage_service() -> AudioStorageService:
    """取得課程音訊儲存服務"""
    settings = get_settings()
    bucket_name = settings.COURSE_AUDIO_BUCKET_NAME
    return AudioStorageService(bucket_name)

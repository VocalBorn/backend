"""
儲存模組使用範例
展示如何使用不同的儲存服務
"""

from fastapi import UploadFile
from sqlmodel import Session

# 方法一：使用便利函數（推薦）
from src.storage import (
    get_verification_storage,
    get_practice_recording_storage,
    StorageServiceError
)

# 方法二：使用工廠模式
from src.storage import StorageServiceFactory, StorageType, StoragePurpose

# 方法三：使用特定服務類別
from src.storage import practice_recording_service


def upload_verification_document_example(file: UploadFile) -> str:
    """上傳驗證文件範例"""
    try:
        # 使用便利函數
        storage = get_verification_storage()
        object_name = f"documents/{file.filename}"
        return storage.upload_file(file, object_name)
    except StorageServiceError as e:
        print(f"上傳失敗: {e}")
        raise


def upload_practice_recording_example(audio_file: UploadFile, user_id: str) -> str:
    """上傳練習錄音範例"""
    try:
        # 使用音訊專用服務
        audio_storage = get_practice_recording_storage()
        return audio_storage.upload_practice_audio(audio_file, user_id, "session_123")
    except StorageServiceError as e:
        print(f"音訊上傳失敗: {e}")
        raise


def upload_course_audio_example(audio_file: UploadFile) -> str:
    """上傳課程音訊範例"""
    try:
        # 使用工廠模式
        storage = StorageServiceFactory.create_service(
            StorageType.AUDIO,
            StoragePurpose.COURSE_AUDIO
        )
        object_name = f"courses/chapter1/sentence1.mp3"
        return storage.upload_file(audio_file, object_name)
    except StorageServiceError as e:
        print(f"課程音訊上傳失敗: {e}")
        raise


def upload_practice_with_service_example(
    audio_file: UploadFile, 
    user_id: str, 
    sentence_id: str,
    db_session: Session
) -> dict:
    """使用練習錄音服務上傳範例"""
    try:
        # 使用高級服務（包含業務邏輯）
        return practice_recording_service.upload_practice_recording(
            user_id, sentence_id, audio_file, db_session
        )
    except Exception as e:
        print(f"練習錄音服務上傳失敗: {e}")
        raise


def get_file_url_example(object_name: str) -> str:
    """取得檔案 URL 範例"""
    try:
        storage = get_verification_storage()
        return storage.get_presigned_url(object_name)
    except StorageServiceError as e:
        print(f"取得 URL 失敗: {e}")
        raise


def delete_file_example(object_name: str) -> bool:
    """刪除檔案範例"""
    try:
        storage = get_verification_storage()
        return storage.delete_file(object_name)
    except StorageServiceError as e:
        print(f"刪除檔案失敗: {e}")
        raise


def check_file_exists_example(object_name: str) -> bool:
    """檢查檔案是否存在範例"""
    try:
        storage = get_verification_storage()
        return storage.file_exists(object_name)
    except StorageServiceError as e:
        print(f"檢查檔案失敗: {e}")
        return False


# 使用建議：
# 1. 對於簡單的檔案操作，使用便利函數（如 get_verification_storage()）
# 2. 對於需要特定驗證的檔案類型，使用對應的服務類別
# 3. 對於複雜的業務邏輯，使用高級服務（如 practice_recording_service）
# 4. 對於動態儲存類型選擇，使用工廠模式
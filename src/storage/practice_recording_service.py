"""
練習錄音服務
處理用戶練習錄音的上傳、儲存和管理
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlmodel import Session

from .storage_factory import get_practice_recording_storage
from .storage_service import StorageServiceError

logger = logging.getLogger(__name__)


class PracticeRecordingService:
    """練習錄音服務"""
    
    def __init__(self):
        self.storage_service = get_practice_recording_storage()
    
    def upload_practice_recording(
        self,
        user_id: str,
        practice_record_id: str,
        audio_file: UploadFile,
        db_session: Session
    ) -> dict:
        """
        上傳練習錄音
        
        Args:
            user_id: 用戶ID
            practice_record_id: 練習記錄ID
            audio_file: 音訊檔案
            db_session: 資料庫會話
            
        Returns:
            包含錄音資訊的字典
        """
        try:
            # 使用練習記錄ID作為檔案標識
            recording_id = practice_record_id
            
            # 上傳檔案
            object_name = self.storage_service.upload_practice_audio(
                audio_file, user_id, recording_id
            )
            
            # 將錄音資訊存入資料庫
            from src.practice.models import PracticeRecord
            from datetime import datetime
            import uuid as uuid_module
            
            # 更新現有的練習記錄
            practice_record = db_session.get(PracticeRecord, uuid_module.UUID(practice_record_id))
            if practice_record:
                # 更新現有記錄
                practice_record.audio_path = object_name
                practice_record.file_size = audio_file.size
                practice_record.content_type = audio_file.content_type
                practice_record.updated_at = datetime.now()
                
                db_session.add(practice_record)
                db_session.commit()
            else:
                # 這種情況不應該發生，因為應該先建立練習記錄
                logger.error(f"練習記錄不存在: {practice_record_id}")
                raise StorageServiceError(f"練習記錄不存在: {practice_record_id}")
            
            logger.info(f"練習錄音上傳成功: 用戶 {user_id}, 練習記錄 {practice_record_id}, 檔案 {object_name}")
            
            return {
                "recording_id": recording_id,
                "object_name": object_name,
                "file_size": audio_file.size,
                "content_type": audio_file.content_type,
                "status": "uploaded"
            }
            
        except StorageServiceError as e:
            logger.error(f"練習錄音上傳失敗: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"練習錄音上傳失敗: {str(e)}"
            )
        except Exception as e:
            logger.error(f"練習錄音上傳時發生未預期錯誤: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="練習錄音上傳時發生未預期錯誤"
            )
    
    def get_practice_recording_url(
        self,
        recording_id: str,
        user_id: str,
        expires_minutes: int = 30
    ) -> str:
        """
        取得練習錄音的播放 URL
        
        Args:
            recording_id: 錄音ID
            user_id: 用戶ID
            expires_minutes: URL有效期（分鐘）
            
        Returns:
            預簽署的播放URL
        """
        try:
            # 構建物件名稱
            object_name = f"practice_recordings/{user_id}/{recording_id}.mp3"  # 假設是MP3格式
            
            # 生成預簽署URL
            url = self.storage_service.get_presigned_url(
                object_name,
                expires_in=timedelta(minutes=expires_minutes)
            )
            
            return url
            
        except StorageServiceError as e:
            logger.error(f"取得練習錄音URL失敗: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"取得練習錄音URL失敗: {str(e)}"
            )
    
    def delete_practice_recording(
        self,
        recording_id: str,
        user_id: str,
        db_session: Session
    ) -> bool:
        """
        刪除練習錄音
        
        Args:
            recording_id: 錄音ID
            user_id: 用戶ID
            db_session: 資料庫會話
            
        Returns:
            是否成功刪除
        """
        try:
            # 構建物件名稱
            object_name = f"practice_recordings/{user_id}/{recording_id}.mp3"
            
            # 刪除檔案
            success = self.storage_service.delete_file(object_name)
            
            if success:
                # 這裡可以從資料庫中刪除記錄
                # db_session.delete(recording_record)
                # db_session.commit()
                logger.info(f"練習錄音刪除成功: {recording_id}")
            
            return success
            
        except StorageServiceError as e:
            logger.error(f"刪除練習錄音失敗: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"刪除練習錄音失敗: {str(e)}"
            )
    
    async def get_presigned_url(
        self,
        audio_path: str,
        expires_minutes: int = 30
    ) -> Tuple[str, datetime]:
        """
        取得音訊檔案的預簽署 URL
        
        Args:
            audio_path: 音訊檔案路徑
            expires_minutes: URL有效期（分鐘）
            
        Returns:
            包含 URL 和過期時間的 tuple
        """
        try:
            # 生成預簽署URL
            url = self.storage_service.get_presigned_url(
                audio_path,
                expires_in=timedelta(minutes=expires_minutes)
            )
            
            # 計算過期時間
            expires_at = datetime.now() + timedelta(minutes=expires_minutes)
            
            return url, expires_at
            
        except StorageServiceError as e:
            logger.error(f"取得音訊預簽署URL失敗: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"取得音訊預簽署URL失敗: {str(e)}"
            )


# 單例實例
practice_recording_service = PracticeRecordingService()
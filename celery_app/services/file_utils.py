"""檔案處理工具服務

提供音檔下載、暫存檔案管理等檔案處理相關功能。
"""

import logging
import os
import tempfile
from contextlib import contextmanager
from typing import Generator, List

from src.storage.audio_storage_service import AudioStorageService

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """檔案處理自定義異常"""
    pass


@contextmanager
def temporary_audio_files(*file_paths) -> Generator[List[str], None, None]:
    """暫存音檔檔案上下文管理器，確保檔案在使用後被清理
    
    Args:
        *file_paths: 需要管理的暫存檔案路徑
        
    Yields:
        List[str]: 暫存檔案路徑列表
    """
    temp_files = []
    try:
        for file_path in file_paths:
            if file_path:
                temp_files.append(file_path)
        yield temp_files
    finally:
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"已清理暫存檔案: {temp_file}")
            except Exception as e:
                logger.warning(f"清理暫存檔案失敗: {temp_file}, 錯誤: {e}")


def download_audio_file_to_temp(storage_service: AudioStorageService, audio_path: str) -> str:
    """從儲存服務下載音檔到暫存檔案
    
    Args:
        storage_service: 儲存服務實例
        audio_path: 音檔在儲存服務中的路徑
        
    Returns:
        str: 暫存檔案的本地路徑
        
    Raises:
        FileProcessingError: 當檔案下載失敗時
    """
    try:
        # 建立暫存檔案
        file_extension = os.path.splitext(audio_path)[1] or '.mp3'
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_extension)
        
        try:
            # 直接嘗試下載檔案（如果不存在會拋出異常）
            with os.fdopen(temp_fd, 'wb') as temp_file:
                response = storage_service.client.get_object(
                    storage_service.bucket_name,
                    audio_path
                )
                
                # 檢查是否成功取得資料
                data_written = False
                for data in response.stream(32*1024):
                    temp_file.write(data)
                    data_written = True
                response.close()
                
                # 如果沒有寫入任何資料，表示檔案可能為空
                if not data_written:
                    raise FileProcessingError(f"音檔為空或下載失敗: {audio_path}")
            
            # 檢查下載的檔案大小
            if os.path.getsize(temp_path) == 0:
                raise FileProcessingError(f"下載的音檔為空: {audio_path}")
            
            logger.debug(f"音檔下載完成: {audio_path} -> {temp_path}, 大小: {os.path.getsize(temp_path)} bytes")
            return temp_path
            
        except Exception as e:
            # 如果下載失敗，清理暫存檔案
            try:
                if 'temp_fd' in locals():
                    os.close(temp_fd)
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
                
            # 根據錯誤類型提供更具體的錯誤訊息
            if "NoSuchKey" in str(e) or "NoSuchObject" in str(e):
                raise FileProcessingError(f"音檔不存在: {audio_path}")
            elif "AccessDenied" in str(e):
                raise FileProcessingError(f"音檔存取被拒絕: {audio_path}")
            else:
                raise FileProcessingError(f"下載音檔失敗: {audio_path}, 錯誤: {e}")
            
    except Exception as e:
        if isinstance(e, FileProcessingError):
            raise
        logger.error(f"音檔下載過程發生錯誤: {e}")
        raise FileProcessingError(f"音檔下載過程發生未預期錯誤: {e}")


__all__ = ["temporary_audio_files", "download_audio_file_to_temp", "FileProcessingError"]
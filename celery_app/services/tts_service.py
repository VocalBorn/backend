"""文字轉語音服務模組

使用 Edge TTS 提供高品質的台灣中文語音合成功能。
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional
import edge_tts
from pathlib import Path

logger = logging.getLogger(__name__)

# 支援的語者配置
SUPPORTED_VOICES = {
    "female": "zh-TW-HsiaoChenNeural",  # 台灣女聲
    "male": "zh-TW-YunJheNeural"       # 台灣男聲
}

class TTSServiceError(Exception):
    """TTS 服務異常類"""
    pass


class TTSService:
    """文字轉語音服務"""
    
    def __init__(
        self, 
        default_voice: str = "female",
        rate: int = 0,
        pitch: int = 0
    ):
        """初始化 TTS 服務
        
        Args:
            default_voice: 預設語者 ("female" 或 "male")
            rate: 語速調整 (-50 到 50)
            pitch: 音調調整 (-20 到 20)
        """
        if default_voice not in SUPPORTED_VOICES:
            raise TTSServiceError(f"不支援的語者: {default_voice}")
            
        self.voice = SUPPORTED_VOICES[default_voice]
        self.rate = max(-50, min(50, rate))
        self.pitch = max(-20, min(20, pitch))
        
        logger.info(f"TTS 服務初始化完成 - 語者: {self.voice}, 語速: {self.rate}, 音調: {self.pitch}")
    
    def _get_rate_str(self, rate: int) -> str:
        """取得語速字串格式"""
        return f"{'+' if rate >= 0 else ''}{rate}%"
    
    def _get_pitch_str(self, pitch: int) -> str:
        """取得音調字串格式"""
        return f"{'+' if pitch >= 0 else ''}{pitch}Hz"
    
    async def text_to_speech(self, text: str, output_path: str) -> str:
        """將文字轉換為語音檔案
        
        Args:
            text: 要轉換的文字內容
            output_path: 輸出檔案路徑
            
        Returns:
            str: 輸出檔案路徑
            
        Raises:
            TTSServiceError: TTS 轉換失敗
        """
        if not text or not text.strip():
            raise TTSServiceError("文字內容不能為空")
            
        try:
            # 建立 Edge TTS 通訊物件
            communicate = edge_tts.Communicate(
                text=text.strip(),
                voice=self.voice,
                rate=self._get_rate_str(self.rate),
                pitch=self._get_pitch_str(self.pitch)
            )
            
            # 確保輸出目錄存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 執行語音合成並儲存
            await communicate.save(output_path)
            
            # 驗證檔案是否成功產生
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise TTSServiceError("語音檔案生成失敗")
            
            file_size = os.path.getsize(output_path)
            logger.info(f"TTS 轉換成功: {text[:50]}... -> {output_path} ({file_size} bytes)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"TTS 轉換失敗: {e}")
            # 清理可能產生的不完整檔案
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            raise TTSServiceError(f"語音合成失敗: {str(e)}")
    
    async def create_temporary_audio(self, text: str) -> str:
        """建立暫存語音檔案
        
        Args:
            text: 要轉換的文字內容
            
        Returns:
            str: 暫存檔案路徑
        """
        # 建立暫存檔案
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            await self.text_to_speech(text, temp_path)
            return temp_path
        except Exception:
            # 發生錯誤時清理暫存檔案
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise


def create_tts_service(voice: str = "female") -> TTSService:
    """建立 TTS 服務實例的工廠函數
    
    Args:
        voice: 語者選擇 ("female" 或 "male")
        
    Returns:
        TTSService: TTS 服務實例
    """
    return TTSService(default_voice=voice)


# 同步包裝函數，供 Celery 任務使用
def sync_text_to_speech(text: str, output_path: str, voice: str = "female") -> str:
    """同步版本的文字轉語音函數
    
    Args:
        text: 要轉換的文字內容
        output_path: 輸出檔案路徑
        voice: 語者選擇
        
    Returns:
        str: 輸出檔案路徑
    """
    tts_service = create_tts_service(voice)
    return asyncio.run(tts_service.text_to_speech(text, output_path))


def sync_create_temporary_audio(text: str, voice: str = "female") -> str:
    """同步版本的暫存語音檔案建立函數
    
    Args:
        text: 要轉換的文字內容
        voice: 語者選擇
        
    Returns:
        str: 暫存檔案路徑
    """
    tts_service = create_tts_service(voice)
    return asyncio.run(tts_service.create_temporary_audio(text))
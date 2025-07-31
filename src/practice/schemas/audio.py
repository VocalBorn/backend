from pydantic import BaseModel, ConfigDict
from uuid import UUID

# 錄音上傳相關 Schemas
class AudioUploadRequest(BaseModel):
    """音訊上傳請求參數"""
    sentence_id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sentence_id": "550e8400-e29b-41d4-a716-446655440003"
            }
        }
    )

class AudioUploadResponse(BaseModel):
    """音訊上傳回應"""
    recording_id: str
    object_name: str
    file_size: int
    content_type: str
    status: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recording_id": "550e8400-e29b-41d4-a716-446655440008",
                "object_name": "practice_recordings/user123/recording456.mp3",
                "file_size": 1024000,
                "content_type": "audio/mpeg",
                "status": "uploaded"
            }
        }
    )

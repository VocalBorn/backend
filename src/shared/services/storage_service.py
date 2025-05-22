from datetime import timedelta
import os
import uuid
from fastapi import UploadFile
from minio import Minio

minio_client = Minio(
  endpoint=os.getenv("MINIO_ENDPOINT"),
  access_key=os.getenv("MINIO_ACCESS_KEY"),
  secret_key=os.getenv("MINIO_SECRET_KEY"),
  secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
)

class StorageService:
  def __init__(self, minio_client: Minio):
    self.client = minio_client
    self.bucket_name = os.getenv("MINIO_BUCKET_NAME")

  async def save_file(self, user_id: uuid.UUID, file_data: UploadFile):
    file_id = uuid.uuid4()
    path = f"{user_id}/{file_id}"
    
    # 使用服務帳號存儲檔案
    self.client.put_object(
        self.bucket_name,
        path,
        file_data.file,
        file_data.size
    )
    
    return file_id
    
  async def get_file_url(self, user_id: uuid.UUID, file_id: uuid.UUID):
    path = f"{user_id}/{file_id}.mp3"
    
    # 產生臨時訪問URL
    url = self.client.get_presigned_url(
        "GET",
        self.bucket_name,
        path,
        expires=timedelta(minutes=15)
    )
    
    return url
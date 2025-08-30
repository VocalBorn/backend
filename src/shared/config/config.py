"""
FastAPI 配置管理模組

使用 Pydantic Settings 進行環境變數管理和配置驗證
參考 FastAPI 官方最佳實踐和 full-stack-fastapi-template
"""

from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用程式配置設定類別
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 忽略額外的環境變數
    )
    
    # 應用程式基本設定
    APP_NAME: str = "VocalBorn API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = Field(default=False, description="啟用除錯模式")
    
    # 伺服器設定
    HOST: str = Field(default="0.0.0.0", description="伺服器主機")
    PORT: int = Field(default=8000, description="伺服器埠號")
    BASE_URL: Optional[str] = Field(default=None, description="應用程式基礎 URL")
    
    # 安全設定
    SECRET_KEY: str = Field(default="test-secret-key-do-not-use-in-production", description="應用程式密鑰", min_length=5)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="存取令牌過期時間（分鐘）")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="刷新令牌過期時間（天）")
    
    # 資料庫設定
    DB_ADDRESS: str = Field(default="localhost", description="資料庫主機地址")
    DB_PORT: int = Field(default=5432, description="資料庫埠號")
    DB_USER: str = Field(default="postgres", description="資料庫使用者名稱")
    DB_PASSWORD: str = Field(default="password", description="資料庫密碼")
    DB_NAME: str = Field(default="test_db", description="資料庫名稱")
    
    # Redis 設定
    REDIS_HOST: str = Field(default="localhost", description="Redis 主機")
    REDIS_PORT: int = Field(default=6379, description="Redis 埠號")
    REDIS_DB_BROKER: int = Field(default=0, description="Celery Broker 資料庫")
    REDIS_DB_BACKEND: int = Field(default=1, description="Celery Backend 資料庫")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis 密碼")
    
    # Celery 設定
    CELERY_LOG_LEVEL: str = Field(default="INFO", description="Celery 日誌級別")
    CELERY_WORKER_CONCURRENCY: int = Field(default=4, description="Celery Worker 並發數")
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = Field(default=1000, description="Worker 最大任務數")
    
    # 電子郵件設定
    EMAIL_SERVICE_HOST: Optional[str] = Field(default=None, description="電子郵件服務主機")
    EMAIL_SERVICE_PORT: Optional[int] = Field(default=None, description="電子郵件服務埠號")
    EMAIL_USE_TLS: bool = Field(default=True, description="使用 TLS 加密")
    EMAIL_USERNAME: Optional[str] = Field(default=None, description="電子郵件使用者名稱")
    EMAIL_PASSWORD: Optional[str] = Field(default=None, description="電子郵件密碼")
    EMAIL_FROM: Optional[str] = Field(default=None, description="寄件者電子郵件")
    
    # MinIO 物件儲存設定
    MINIO_ENDPOINT: Optional[str] = Field(default=None, description="MinIO 端點")
    MINIO_ACCESS_KEY: Optional[str] = Field(default=None, description="MinIO 存取金鑰")
    MINIO_SECRET_KEY: Optional[str] = Field(default=None, description="MinIO 秘密金鑰")
    MINIO_BUCKET_NAME: Optional[str] = Field(default="vocalborn-verifications", description="MinIO 儲存桶名稱")
    MINIO_SECURE: bool = Field(default=True, description="使用 HTTPS 連接 MinIO")
    
    # 音訊儲存設定
    PRACTICE_AUDIO_BUCKET_NAME: str = Field(default="practice-recordings", description="練習音訊儲存桶名稱")
    COURSE_AUDIO_BUCKET_NAME: str = Field(default="course-audio", description="課程音訊儲存桶名稱")
    
    # AI 分析服務設定
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="AI 服務 Gemini API 金鑰")
    
    # 日誌設定
    LOG_LEVEL: str = Field(default="INFO", description="日誌級別")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日誌格式"
    )
    
    # CORS 設定
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="允許的來源"
    )
    
    @field_validator("DEBUG")
    @classmethod
    def validate_debug(cls, v, info):
        """在生產環境中禁用除錯模式"""
        if hasattr(info, 'data') and info.data.get("ENVIRONMENT") == "production" and v:
            raise ValueError("生產環境中不能啟用除錯模式")
        return v
    
    @property
    def database_url(self) -> str:
        """建構資料庫 URL"""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_ADDRESS}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def redis_broker_url(self) -> str:
        """建構 Redis Broker URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_BROKER}"
    
    @property
    def redis_backend_url(self) -> str:
        """建構 Redis Backend URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_BACKEND}"
    
    @property
    def is_development(self) -> bool:
        """檢查是否為開發環境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """檢查是否為生產環境"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_test(self) -> bool:
        """檢查是否為測試環境"""
        return self.ENVIRONMENT == "test"


@lru_cache()
def get_settings() -> Settings:
    """取得應用程式設定
    
    使用 lru_cache 確保設定只被載入一次，提高效能
    
    Returns:
        Settings: 應用程式設定實例
    """
    return Settings()


# 匯出預設設定實例（用於非依賴注入場景）
settings = get_settings()

import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel, JSON, Column
from sqlalchemy import Text
import uuid



class TaskStatus(str, Enum):
    """AI 分析任務狀態枚舉"""
    PENDING = "pending"         # 等待中
    PROCESSING = "processing"   # 處理中  
    SUCCESS = "success"         # 成功完成
    FAILURE = "failure"         # 失敗
    RETRY = "retry"            # 重試中


class AIAnalysisTask(SQLModel, table=True):
    """AI 分析任務追蹤表"""
    __tablename__ = "ai_analysis_tasks"

    # 基礎資訊
    task_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    celery_task_id: Optional[str] = Field(default=None, unique=True, index=True)
    
    # 關聯資訊
    user_id: uuid.UUID = Field(foreign_key="users.user_id", index=True)
    
    # 任務狀態（簡化狀態管理）
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    
    # 任務配置
    task_type: str = Field(default="audio_analysis", max_length=50)
    task_params: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 執行資訊
    worker_name: Optional[str] = Field(default=None, max_length=100)
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    
    # 進度追蹤
    progress: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = Field(default=None, max_length=100)
    
    # 錯誤處理
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    # 時間戳記
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, index=True)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    practice_record: "PracticeRecord" = Relationship(back_populates="ai_analysis_task")
    user: "User" = Relationship()
    ai_analysis_result: Optional["AIAnalysisResult"] = Relationship(
        back_populates="ai_analysis_task", 
        sa_relationship_kwargs={"uselist": False}
    )


class AIAnalysisResult(SQLModel, table=True):
    """AI 分析結果表"""
    __tablename__ = "ai_analysis_results"

    # 基礎資訊
    result_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="ai_analysis_tasks.task_id", unique=True, index=True)
    
    # AI 分析結果（完整 JSON）
    analysis_result: dict = Field(sa_column=Column(JSON))
    
    # 元資料
    analysis_model_version: Optional[str] = Field(default=None, max_length=50)
    processing_time_seconds: Optional[float] = None
    
    # 時間戳記
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, index=True)

    # Relationships
    ai_analysis_task: AIAnalysisTask = Relationship(back_populates="ai_analysis_result")
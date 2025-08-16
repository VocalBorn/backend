import datetime
import uuid
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel, JSON, Column

if TYPE_CHECKING:
    from src.auth.models import User
    from src.practice.models import PracticeRecord



class TaskStatus(str, Enum):
    """AI 分析任務狀態枚舉
    
    用於追蹤 AI 分析任務的執行狀態。
    
    Attributes:
        PENDING: 任務已建立，等待執行
        PROCESSING: 任務正在執行中
        COMPLETED: 任務執行完成（包含成功和失敗）
        CANCELLED: 任務已被取消
    """
    PENDING = "pending"         # 等待中
    PROCESSING = "processing"   # 處理中  
    COMPLETED = "completed"     # 完成（成功或失敗都算完成）
    CANCELLED = "cancelled"     # 已取消


class AIAnalysisTask(SQLModel, table=True):
    """AI 分析任務追蹤表
    
    用於追蹤 AI 音訊分析任務的狀態和相關資訊，採用簡化設計原則，
    只儲存業務邏輯必需的資訊，執行細節由 Celery/Flower 管理。
    
    Attributes:
        task_id: 任務的唯一識別碼，作為主鍵
        celery_task_id: Celery 任務 ID，用於追蹤執行狀態
        user_id: 發起任務的使用者 ID，建立外鍵關聯
        status: 任務當前狀態，使用 TaskStatus 枚舉
        task_type: 任務類型，預設為音訊分析
        task_params: 任務參數的 JSON 配置，可選
        created_at: 任務建立時間，使用 UTC 時間
    """
    __tablename__ = "ai_analysis_tasks"

    # 核心識別資訊
    task_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    celery_task_id: Optional[str] = Field(default=None, unique=True, index=True)
    
    # 業務關聯
    user_id: uuid.UUID = Field(foreign_key="users.user_id", index=True)
    
    # 簡化的狀態管理
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    
    # 基本配置（如果需要持久化的話）
    task_type: str = Field(default="audio_analysis", max_length=50)
    task_params: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # 時間戳記
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, nullable=False, index=True)

    # Relationships
    practice_record: Optional["PracticeRecord"] = Relationship(back_populates="ai_analysis_task")
    user: "User" = Relationship(back_populates="ai_analysis_tasks")
    ai_analysis_result: Optional["AIAnalysisResult"] = Relationship(
        back_populates="ai_analysis_task", 
        sa_relationship_kwargs={"uselist": False}
    )


class AIAnalysisResult(SQLModel, table=True):
    """AI 分析結果表
    
    儲存 AI 分析任務的完整結果資料，與 AIAnalysisTask 建立一對一關係。
    
    Attributes:
        result_id: 結果記錄的唯一識別碼，作為主鍵
        task_id: 關聯的分析任務 ID，建立外鍵約束
        analysis_result: AI 分析的完整結果，以 JSON 格式儲存
        analysis_model_version: 執行分析的 AI 模型版本號
        processing_time_seconds: 分析處理耗時（秒）
        created_at: 結果建立時間，使用 UTC 時間
    """
    __tablename__ = "ai_analysis_results"

    # 基礎資訊
    result_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="ai_analysis_tasks.task_id", unique=True, index=True)
    
    # AI 分析結果
    analysis_result: dict = Field(sa_column=Column(JSON))
    
    # 元資料
    analysis_model_version: Optional[str] = Field(default=None, max_length=50)
    processing_time_seconds: Optional[float] = None
    
    # 時間戳記
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False, index=True)

    # Relationships
    ai_analysis_task: AIAnalysisTask = Relationship(back_populates="ai_analysis_result")
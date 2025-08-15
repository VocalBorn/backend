import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
import uuid

from src.course.models import Chapter, Sentence
from src.ai_analysis.models import AIAnalysisTask

class PracticeSessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"    # 進行中
    COMPLETED = "completed"        # 已完成
    PAUSED = "paused"             # 暫停
    ABANDONED = "abandoned"        # 放棄

class PracticeRecordStatus(str, Enum):
    PENDING = "pending"            # 待錄音
    RECORDED = "recorded"          # 已錄音
    AI_QUEUED = "ai_queued"        # AI 分析排隊中
    AI_PROCESSING = "ai_processing"  # AI 分析處理中
    AI_ANALYZED = "ai_analyzed"    # AI 分析完成
    ANALYZED = "analyzed"          # 人工分析完成（最終狀態）

class PracticeSession(SQLModel, table=True):
    """練習會話表 - 代表使用者對某章節的一次完整練習"""
    __tablename__ = "practice_sessions"

    practice_session_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id")
    chapter_id: uuid.UUID = Field(foreign_key="chapters.chapter_id")
    session_status: PracticeSessionStatus = Field(default=PracticeSessionStatus.IN_PROGRESS)
    
    
    # 會話時間資訊
    begin_time: Optional[datetime.datetime] = None  # 練習開始時間
    end_time: Optional[datetime.datetime] = None    # 練習結束時間
    total_duration: Optional[int] = None            # 總練習時長（秒）
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="practice_sessions")
    chapter: Chapter = Relationship(back_populates="practice_sessions")
    practice_records: List["PracticeRecord"] = Relationship(back_populates="practice_session")
    session_feedbacks: List["PracticeSessionFeedback"] = Relationship(back_populates="practice_session")

class PracticeRecord(SQLModel, table=True):
    """練習記錄表 - 代表練習會話中單個句子的錄音記錄"""
    __tablename__ = "practice_records"

    practice_record_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    practice_session_id: uuid.UUID = Field(foreign_key="practice_sessions.practice_session_id")
    sentence_id: uuid.UUID = Field(foreign_key="sentences.sentence_id")  # 必須指定句子
    record_status: PracticeRecordStatus = Field(default=PracticeRecordStatus.PENDING)
    
    # AI 任務追蹤欄位
    ai_task_id: Optional[uuid.UUID] = Field(default=None, foreign_key="ai_analysis_tasks.task_id")
    ai_analysis_status: Optional[str] = Field(default="pending", max_length=20)  # pending, queued, processing, completed, failed
    
    # 音訊檔案資訊
    audio_path: Optional[str] = None
    audio_duration: Optional[float] = None  # 音訊時長（秒）
    file_size: Optional[int] = None         # 檔案大小（bytes）
    content_type: Optional[str] = None      # 檔案類型
    
    # 錄音時間
    recorded_at: Optional[datetime.datetime] = None  # 錄音時間
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    practice_session: PracticeSession = Relationship(back_populates="practice_records")
    sentence: Sentence = Relationship(back_populates="practice_records")
    feedback: Optional["PracticeFeedback"] = Relationship(back_populates="practice_record")
    ai_analysis_task: Optional[AIAnalysisTask] = Relationship(
        back_populates="practice_record",
        sa_relationship_kwargs={"uselist": False}
    )


# 待刪除、棄用
class PracticeFeedback(SQLModel, table=True): 
    """練習回饋表"""
    __tablename__ = "practice_feedbacks"

    feedback_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    practice_record_id: uuid.UUID = Field(foreign_key="practice_records.practice_record_id", unique=True)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id")
    
    # 回饋內容
    content: str  # 回饋內容
    pronunciation_accuracy: Optional[float] = None  # 發音準確度評分 (0-100)
    suggestions: Optional[str] = None  # 改進建議
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    practice_record: PracticeRecord = Relationship(back_populates="feedback")
    therapist: "User" = Relationship()

class PracticeSessionFeedback(SQLModel, table=True):
    """練習會話回饋表"""
    __tablename__ = "practice_session_feedbacks"

    session_feedback_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    practice_session_id: uuid.UUID = Field(foreign_key="practice_sessions.practice_session_id")
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id")
    
    # 回饋內容
    content: str  # 回饋內容
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    practice_session: PracticeSession = Relationship(back_populates="session_feedbacks")
    therapist: "User" = Relationship()

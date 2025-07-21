import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
import uuid

class SpeakerRole(str, Enum):
    SELF = "self"      # 自己
    OTHER = "other"    # 對方

class Situation(SQLModel, table=True):
    """情境表"""
    __tablename__ = "situations"

    situation_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    situation_name: str = Field(index=True)
    description: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    chapters: List["Chapter"] = Relationship(back_populates="situation")

class Chapter(SQLModel, table=True):
    """章節表"""
    __tablename__ = "chapters"

    chapter_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    situation_id: uuid.UUID = Field(foreign_key="situations.situation_id")
    chapter_name: str = Field(index=True)
    description: Optional[str] = None
    sequence_number: int
    video_url: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    situation: Situation = Relationship(back_populates="chapters")
    sentences: List["Sentence"] = Relationship(back_populates="chapter")
    practice_records: List["PracticeRecord"] = Relationship(back_populates="chapter")

class Sentence(SQLModel, table=True):
    """語句表"""
    __tablename__ = "sentences"

    sentence_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    chapter_id: uuid.UUID = Field(foreign_key="chapters.chapter_id")
    sentence_name: str = Field(index=True)
    speaker_role: SpeakerRole
    role_description: Optional[str] = None
    content: str
    start_time: Optional[float] = None  # 在影片中的開始時間（秒）
    end_time: Optional[float] = None    # 在影片中的結束時間（秒）
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    chapter: Chapter = Relationship(back_populates="sentences")
    practice_records: List["PracticeRecord"] = Relationship(back_populates="sentence")

class PracticeStatus(str, Enum):
    IN_PROGRESS = "in_progress"    # 進行中
    COMPLETED = "completed"        # 已完成
    AI_QUEUED = "ai_queued"        # AI 分析排隊中
    AI_PROCESSING = "ai_processing"  # AI 分析處理中
    AI_ANALYZED = "ai_analyzed"    # AI 分析完成
    ANALYZED = "analyzed"          # 人工分析完成（最終狀態）

class PracticeRecord(SQLModel, table=True):
    """練習記錄表"""
    __tablename__ = "practice_records"

    practice_record_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id")
    chapter_id: uuid.UUID = Field(foreign_key="chapters.chapter_id")  # 練習的章節
    sentence_id: Optional[uuid.UUID] = Field(foreign_key="sentences.sentence_id", default=None)  # 錄音的句子，上傳時指定
    audio_path: Optional[str] = None
    audio_duration: Optional[float] = None  # 音訊時長（秒）
    file_size: Optional[int] = None         # 檔案大小（bytes）
    content_type: Optional[str] = None      # 檔案類型
    practice_status: PracticeStatus = Field(default=PracticeStatus.IN_PROGRESS)
    begin_time: Optional[datetime.datetime] = None  # 練習開始時間
    end_time: Optional[datetime.datetime] = None    # 練習結束時間
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="practice_records")
    chapter: Chapter = Relationship(back_populates="practice_records")  # 關聯到章節
    sentence: Optional[Sentence] = Relationship()  # 關聯到句子，可為空
    feedback: Optional["PracticeFeedback"] = Relationship(back_populates="practice_record")
    ai_analysis_queue: Optional["AIAnalysisQueue"] = Relationship(back_populates="practice_record")
    ai_analysis_result: Optional["AIAnalysisResult"] = Relationship(back_populates="practice_record")

class AIAnalysisQueueStatus(str, Enum):
    PENDING = "pending"      # 等待中
    PROCESSING = "processing"  # 處理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失敗
    CANCELLED = "cancelled"  # 已取消

class AIAnalysisPriority(str, Enum):
    LOW = "low"         # 低優先級
    NORMAL = "normal"   # 一般優先級
    HIGH = "high"       # 高優先級
    URGENT = "urgent"   # 緊急優先級

class AIAnalysisQueue(SQLModel, table=True):
    """AI 分析排隊表"""
    __tablename__ = "ai_analysis_queue"

    queue_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    practice_record_id: uuid.UUID = Field(foreign_key="practice_records.practice_record_id", unique=True)
    priority: AIAnalysisPriority = Field(default=AIAnalysisPriority.NORMAL)
    status: AIAnalysisQueueStatus = Field(default=AIAnalysisQueueStatus.PENDING)
    
    # 排隊和處理資訊
    queued_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    
    # 估算和實際處理時間
    estimated_duration: Optional[int] = None  # 預估處理時間（秒）
    actual_duration: Optional[int] = None     # 實際處理時間（秒）
    
    # 錯誤資訊
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    # 處理者資訊
    worker_id: Optional[str] = None
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    practice_record: PracticeRecord = Relationship(back_populates="ai_analysis_queue")
    ai_analysis_result: Optional["AIAnalysisResult"] = Relationship(back_populates="queue_record")

class AIAnalysisResult(SQLModel, table=True):
    """AI 分析結果表"""
    __tablename__ = "ai_analysis_results"

    result_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    queue_id: uuid.UUID = Field(foreign_key="ai_analysis_queue.queue_id", unique=True)
    practice_record_id: uuid.UUID = Field(foreign_key="practice_records.practice_record_id", unique=True)
    
    # AI 分析結果
    ai_model_version: str  # AI 模型版本
    pronunciation_accuracy: Optional[float] = None  # 發音準確度 (0-100)
    fluency_score: Optional[float] = None           # 流暢度評分 (0-100)
    rhythm_score: Optional[float] = None            # 節奏評分 (0-100)
    tone_score: Optional[float] = None              # 語調評分 (0-100)
    overall_score: Optional[float] = None           # 整體評分 (0-100)
    
    # 詳細分析結果（JSON 格式）
    detailed_analysis: Optional[str] = None  # 詳細分析結果（JSON 字串）
    phoneme_analysis: Optional[str] = None   # 音素分析結果（JSON 字串）
    word_analysis: Optional[str] = None      # 詞彙分析結果（JSON 字串）
    
    # AI 生成的建議
    ai_suggestions: Optional[str] = None
    improvement_areas: Optional[str] = None  # 需要改進的領域
    
    # 置信度和可靠性
    confidence_score: Optional[float] = None  # AI 分析置信度 (0-100)
    reliability_score: Optional[float] = None  # 結果可靠性 (0-100)
    
    # 處理資訊
    processing_time: Optional[float] = None  # 處理時間（秒）
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    queue_record: AIAnalysisQueue = Relationship(back_populates="ai_analysis_result")
    practice_record: PracticeRecord = Relationship(back_populates="ai_analysis_result")

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
    
    # 是否基於 AI 分析結果
    based_on_ai_analysis: bool = Field(default=False)
    ai_analysis_reviewed: bool = Field(default=False)  # 是否已審查 AI 分析
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    practice_record: PracticeRecord = Relationship(back_populates="feedback")
    therapist: "User" = Relationship()

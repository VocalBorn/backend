from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from src.course.models import AIAnalysisQueueStatus, AIAnalysisPriority

# AI 分析排隊相關 Schemas
class AIAnalysisQueueCreate(BaseModel):
    """建立 AI 分析排隊請求"""
    practice_record_id: UUID
    priority: AIAnalysisPriority = AIAnalysisPriority.NORMAL

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "priority": "normal"
            }
        }
    )

class AIAnalysisQueueResponse(BaseModel):
    """AI 分析排隊回應"""
    queue_id: UUID
    practice_record_id: UUID
    priority: AIAnalysisPriority
    status: AIAnalysisQueueStatus
    
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    
    position_in_queue: Optional[int] = None  # 排隊位置
    estimated_wait_time: Optional[int] = None  # 預估等待時間（秒）
    
    error_message: Optional[str] = None
    retry_count: int = 0
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queue_id": "550e8400-e29b-41d4-a716-446655440008",
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "priority": "normal",
                "status": "pending",
                "queued_at": "2025-07-14T10:00:00.000Z",
                "position_in_queue": 3,
                "estimated_wait_time": 180,
                "retry_count": 0,
                "created_at": "2025-07-14T10:00:00.000Z",
                "updated_at": "2025-07-14T10:00:00.000Z"
            }
        }
    )

class AIAnalysisQueueUpdate(BaseModel):
    """更新 AI 分析排隊請求"""
    priority: Optional[AIAnalysisPriority] = None
    status: Optional[AIAnalysisQueueStatus] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "priority": "high",
                "status": "processing"
            }
        }
    )

# AI 分析結果相關 Schemas
class AIAnalysisResultCreate(BaseModel):
    """建立 AI 分析結果"""
    queue_id: UUID
    practice_record_id: UUID
    ai_model_version: str
    
    pronunciation_accuracy: Optional[float] = None
    fluency_score: Optional[float] = None
    rhythm_score: Optional[float] = None
    tone_score: Optional[float] = None
    overall_score: Optional[float] = None
    
    detailed_analysis: Optional[Dict[str, Any]] = None
    phoneme_analysis: Optional[Dict[str, Any]] = None
    word_analysis: Optional[Dict[str, Any]] = None
    
    ai_suggestions: Optional[str] = None
    improvement_areas: Optional[List[str]] = None
    
    confidence_score: Optional[float] = None
    reliability_score: Optional[float] = None
    processing_time: Optional[float] = None

class AIAnalysisResultResponse(BaseModel):
    """AI 分析結果回應"""
    result_id: UUID
    queue_id: UUID
    practice_record_id: UUID
    
    ai_model_version: str
    pronunciation_accuracy: Optional[float] = None
    fluency_score: Optional[float] = None
    rhythm_score: Optional[float] = None
    tone_score: Optional[float] = None
    overall_score: Optional[float] = None
    
    detailed_analysis: Optional[Dict[str, Any]] = None
    phoneme_analysis: Optional[Dict[str, Any]] = None
    word_analysis: Optional[Dict[str, Any]] = None
    
    ai_suggestions: Optional[str] = None
    improvement_areas: Optional[List[str]] = None
    
    confidence_score: Optional[float] = None
    reliability_score: Optional[float] = None
    processing_time: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440009",
                "queue_id": "550e8400-e29b-41d4-a716-446655440008",
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "ai_model_version": "VocalBorn-AI-v1.2.0",
                "pronunciation_accuracy": 85.5,
                "fluency_score": 78.2,
                "rhythm_score": 82.1,
                "tone_score": 76.8,
                "overall_score": 80.6,
                "ai_suggestions": "發音整體不錯，建議加強語調的變化",
                "improvement_areas": ["語調變化", "停頓節奏"],
                "confidence_score": 92.3,
                "reliability_score": 88.7,
                "processing_time": 45.2,
                "created_at": "2025-07-14T10:05:00.000Z",
                "updated_at": "2025-07-14T10:05:00.000Z"
            }
        }
    )

# 排隊管理相關 Schemas
class QueueStatusResponse(BaseModel):
    """排隊狀態回應"""
    total_pending: int
    total_processing: int
    average_wait_time: Optional[int] = None  # 平均等待時間（秒）
    estimated_processing_time: Optional[int] = None  # 預估處理時間（秒）
    
    queue_health: str  # "healthy", "busy", "overloaded"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_pending": 15,
                "total_processing": 3,
                "average_wait_time": 240,
                "estimated_processing_time": 60,
                "queue_health": "busy"
            }
        }
    )

class UserQueueStatusResponse(BaseModel):
    """用戶排隊狀態回應"""
    user_id: UUID
    pending_analyses: List[AIAnalysisQueueResponse]
    processing_analyses: List[AIAnalysisQueueResponse]
    total_pending: int
    total_processing: int
    next_estimated_completion: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440005",
                "pending_analyses": [],
                "processing_analyses": [],
                "total_pending": 2,
                "total_processing": 1,
                "next_estimated_completion": "2025-07-14T10:15:00.000Z"
            }
        }
    )

# 綜合分析結果 Schemas
class CombinedAnalysisResponse(BaseModel):
    """綜合分析結果回應（AI + 人工）"""
    practice_record_id: UUID
    
    # AI 分析結果
    ai_analysis: Optional[AIAnalysisResultResponse] = None
    ai_analysis_available: bool = False
    
    # 人工分析結果
    human_feedback: Optional[Dict[str, Any]] = None  # 從 PracticeFeedback 來的資料
    human_feedback_available: bool = False
    
    # 綜合評分
    combined_score: Optional[float] = None
    final_recommendations: Optional[str] = None
    
    analysis_status: str  # "ai_only", "human_only", "combined", "pending"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_record_id": "550e8400-e29b-41d4-a716-446655440004",
                "ai_analysis_available": True,
                "human_feedback_available": True,
                "combined_score": 83.2,
                "final_recommendations": "AI 分析顯示發音準確度良好，治療師建議加強語調練習",
                "analysis_status": "combined"
            }
        }
    )

# 批量操作相關 Schemas
class BatchAnalysisRequest(BaseModel):
    """批量分析請求"""
    practice_record_ids: List[UUID]
    priority: AIAnalysisPriority = AIAnalysisPriority.NORMAL
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_record_ids": [
                    "550e8400-e29b-41d4-a716-446655440004",
                    "550e8400-e29b-41d4-a716-446655440005"
                ],
                "priority": "normal"
            }
        }
    )

class BatchAnalysisResponse(BaseModel):
    """批量分析回應"""
    total_requested: int
    successfully_queued: int
    failed_to_queue: int
    queue_records: List[AIAnalysisQueueResponse]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_requested": 5,
                "successfully_queued": 4,
                "failed_to_queue": 1,
                "queue_records": []
            }
        }
    )

# 統計相關 Schemas
class AIAnalysisStatsResponse(BaseModel):
    """AI 分析統計回應"""
    user_id: UUID
    
    total_ai_analyses: int
    successful_analyses: int
    failed_analyses: int
    
    average_processing_time: Optional[float] = None
    average_accuracy_score: Optional[float] = None
    average_overall_score: Optional[float] = None
    
    most_common_improvements: List[str] = []
    
    analyses_this_week: int
    analyses_this_month: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440005",
                "total_ai_analyses": 25,
                "successful_analyses": 23,
                "failed_analyses": 2,
                "average_processing_time": 42.5,
                "average_accuracy_score": 82.3,
                "average_overall_score": 79.8,
                "most_common_improvements": ["語調變化", "停頓節奏", "發音清晰度"],
                "analyses_this_week": 5,
                "analyses_this_month": 18
            }
        }
    )

# List Response Schemas
class AIAnalysisQueueListResponse(BaseModel):
    """AI 分析排隊列表回應"""
    total: int
    queue_items: List[AIAnalysisQueueResponse]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 8,
                "queue_items": []
            }
        }
    )

class AIAnalysisResultListResponse(BaseModel):
    """AI 分析結果列表回應"""
    total: int
    results: List[AIAnalysisResultResponse]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 12,
                "results": []
            }
        }
    )
"""AI 分析相關的 Pydantic Schema 定義

用於驗證 AI 分析相關的請求和回應資料格式。
"""

import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class AIAnalysisTriggerRequest(BaseModel):
    """手動觸發 AI 分析請求
    
    用於手動觸發特定練習會話的 AI 分析任務。
    """
    # 可以在未來擴展其他參數，例如分析參數配置
    pass

    model_config = ConfigDict(
        json_schema_extra={
            "example": {}
        }
    )


class AIAnalysisTriggerResponse(BaseModel):
    """AI 分析任務觸發回應"""
    message: str
    practice_session_id: UUID
    tasks_created: int
    task_ids: List[UUID]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "成功觸發 AI 分析任務",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "tasks_created": 3,
                "task_ids": [
                    "550e8400-e29b-41d4-a716-446655440010",
                    "550e8400-e29b-41d4-a716-446655440011", 
                    "550e8400-e29b-41d4-a716-446655440012"
                ]
            }
        }
    )


class AIAnalysisResultResponse(BaseModel):
    """AI 分析結果回應
    
    用於回傳練習會話的 AI 分析結果資料。
    """
    result_id: UUID
    task_id: UUID
    analysis_result: Dict[str, Any]
    analysis_model_version: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    created_at: datetime.datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440020",
                "task_id": "550e8400-e29b-41d4-a716-446655440010",
                "analysis_result": {
                    "pronunciation_score": 85.5,
                    "fluency_score": 78.2,
                    "accuracy_percentage": 92.1,
                    "feedback": "整體表現良好，建議加強語調練習"
                },
                "analysis_model_version": "v1.2.0",
                "processing_time_seconds": 3.45,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class SessionAIAnalysisResultsResponse(BaseModel):
    """練習會話 AI 分析結果回應
    
    包含指定練習會話的所有 AI 分析結果，按最新時間排序。
    """
    practice_session_id: UUID
    total_results: int
    results: List[AIAnalysisResultResponse] = []
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "total_results": 3,
                "results": [
                    {
                        "result_id": "550e8400-e29b-41d4-a716-446655440020",
                        "task_id": "550e8400-e29b-41d4-a716-446655440010",
                        "analysis_result": {
                            "pronunciation_score": 85.5,
                            "fluency_score": 78.2,
                            "accuracy_percentage": 92.1,
                            "feedback": "整體表現良好，建議加強語調練習"
                        },
                        "analysis_model_version": "v1.2.0",
                        "processing_time_seconds": 3.45,
                        "created_at": "2024-01-15T10:30:00Z"
                    },
                    {
                        "result_id": "550e8400-e29b-41d4-a716-446655440021",
                        "task_id": "550e8400-e29b-41d4-a716-446655440011",
                        "analysis_result": {
                            "pronunciation_score": 82.1,
                            "fluency_score": 75.8,
                            "accuracy_percentage": 89.3,
                            "feedback": "發音清晰，可再加強流暢度"
                        },
                        "analysis_model_version": "v1.2.0",
                        "processing_time_seconds": 2.89,
                        "created_at": "2024-01-15T10:25:00Z"
                    }
                ]
            }
        }
    )
"""AI 分析相關的 Pydantic Schema 定義

用於驗證 AI 分析相關的請求和回應資料格式。
"""

from typing import List
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
from typing import Optional
from pydantic import BaseModel, ConfigDict

# 練習統計相關 Schemas
class PracticeStatsResponse(BaseModel):
    total_practices: int
    total_duration: float  # 總練習時長（秒）
    average_accuracy: Optional[float]  # 平均準確度
    completed_sentences: int  # 已完成的句子數
    pending_feedback: int  # 待回饋數量
    recent_practices: int  # 近期練習數（過去7天）
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_practices": 25,
                "total_duration": 1200.5,
                "average_accuracy": 88.5,
                "completed_sentences": 15,
                "pending_feedback": 3,
                "recent_practices": 8
            }
        }
    )

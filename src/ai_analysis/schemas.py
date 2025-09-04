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
    支援重複觸發分析（會自動清除舊的分析結果）。
    """
    # 可以在未來擴展其他參數，例如分析參數配置
    force_reanalysis: bool = False  # 預設為 False，向後兼容
    analysis_params: Optional[Dict[str, Any]] = None  # 可選的分析參數

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "force_reanalysis": True,
                "analysis_params": {
                    "quality": "high",
                    "detailed_feedback": True
                }
            }
        }
    )


class AIAnalysisTriggerResponse(BaseModel):
    """AI 分析任務觸發回應"""
    message: str
    practice_session_id: UUID
    tasks_created: int
    task_ids: List[UUID]
    previous_tasks_deleted: Optional[int] = 0  # 被刪除的舊任務數量
    is_reanalysis: bool = False  # 是否為重新分析
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "已清除 2 個舊任務並重新觸發 3 個 AI 分析任務",
                "practice_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "tasks_created": 3,
                "task_ids": [
                    "550e8400-e29b-41d4-a716-446655440010",
                    "550e8400-e29b-41d4-a716-446655440011", 
                    "550e8400-e29b-41d4-a716-446655440012"
                ],
                "previous_tasks_deleted": 2,
                "is_reanalysis": True
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


class AIAnalysisResultWithSentenceResponse(BaseModel):
    """包含句子 ID 的 AI 分析結果回應
    
    用於回傳練習會話的 AI 分析結果資料，包含對應的句子 ID。
    """
    result_id: UUID
    task_id: UUID
    sentence_id: UUID
    analysis_result: Dict[str, Any]
    analysis_model_version: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    created_at: datetime.datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "cb525cc3-7577-443d-a606-c1b887a4fe02",
                "task_id": "7bfe5566-646f-4e8f-aa79-e8beea5612a1",
                "sentence_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "analysis_result": {
                    "similarity": {
                        "emb": 0.6940064549446106,
                        "wer": 0,
                        "txt_ref": "好的,我想要一份特餐。",
                        "txt_sam": "好的我要一份特差"
                    },
                    "clarity_ref": {
                        "snr": 39.5557861328125,
                        "hnr": 0,
                        "entropy": 13.092965126037598,
                        "conf": 0.427827858647708,
                        "stoi": 0.9999999999999999
                    },
                    "clarity_sam": {
                        "snr": 28.97469711303711,
                        "hnr": 0,
                        "entropy": 12.927165031433105,
                        "conf": 0.34627757284357097,
                        "stoi": 0.9999999999999997
                    },
                    "index": 0.6700844012461471,
                    "level": 2,
                    "suggestions": "受測者的發音屬中等程度，建議進行音量清晰度練習、口腔肌群訓練以及母音子音精確發音練習。"
                },
                "analysis_model_version": "v1.1",
                "processing_time_seconds": 16.262873888015747,
                "created_at": "2025-09-04T15:12:38.480743"
            }
        }
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "cb525cc3-7577-443d-a606-c1b887a4fe02",
                "task_id": "7bfe5566-646f-4e8f-aa79-e8beea5612a1",
                "analysis_result": {
                    "similarity": {
                        "emb": 0.6940064549446106,
                        "wer": 0,
                        "txt_ref": "好的,我想要一份特餐。",
                        "txt_sam": "好的我要一份特差"
                    },
                    "clarity_ref": {
                        "snr": 39.5557861328125,
                        "hnr": 0,
                        "entropy": 13.092965126037598,
                        "conf": 0.427827858647708,
                        "stoi": 0.9999999999999999
                    },
                    "clarity_sam": {
                        "snr": 28.97469711303711,
                        "hnr": 0,
                        "entropy": 12.927165031433105,
                        "conf": 0.34627757284357097,
                        "stoi": 0.9999999999999997
                    },
                    "index": 0.6700844012461471,
                    "level": 2,
                    "suggestions": "受測者的發音屬中等程度，建議進行音量清晰度練習、口腔肌群訓練以及母音子音精確發音練習。"
                },
                "analysis_model_version": "v1.1",
                "processing_time_seconds": 16.262873888015747,
                "created_at": "2025-09-04T15:12:38.480743"
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


class SessionAIAnalysisResultsWithSentenceResponse(BaseModel):
    """包含句子 ID 的練習會話 AI 分析結果回應
    
    包含指定練習會話的所有 AI 分析結果（含句子 ID），按最新時間排序。
    """
    practice_session_id: UUID
    total_results: int
    results: List[AIAnalysisResultWithSentenceResponse] = []
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_session_id": "c1362405-0da6-40a3-9852-2f5bf38bdf69",
                "total_results": 2,
                "results": [
                    {
                        "result_id": "cb525cc3-7577-443d-a606-c1b887a4fe02",
                        "task_id": "7bfe5566-646f-4e8f-aa79-e8beea5612a1",
                        "sentence_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "analysis_result": {
                            "similarity": {
                                "emb": 0.6940064549446106,
                                "wer": 0,
                                "txt_ref": "好的,我想要一份特餐。",
                                "txt_sam": "好的我要一份特差"
                            },
                            "index": 0.6700844012461471,
                            "level": 2,
                            "suggestions": "受測者的發音屬中等程度，建議進行音量清晰度練習、口腔肌群訓練以及母音子音精確發音練習。"
                        },
                        "analysis_model_version": "v1.1",
                        "processing_time_seconds": 16.262873888015747,
                        "created_at": "2025-09-04T15:12:38.480743"
                    }
                ]
            }
        }
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_session_id": "c1362405-0da6-40a3-9852-2f5bf38bdf69",
                "total_results": 2,
                "results": [
                    {
                        "result_id": "cb525cc3-7577-443d-a606-c1b887a4fe02",
                        "task_id": "7bfe5566-646f-4e8f-aa79-e8beea5612a1",
                        "analysis_result": {
                            "similarity": {
                                "emb": -0.5071844100952149,
                                "wer": -4,
                                "txt_ref": "請問今天的特餐是什麼?",
                                "txt_sam": "请 ち religion saying自帅乘 Whilstfin"
                            },
                            "clarity_ref": {
                                "snr": 39.34138488769531,
                                "hnr": 0,
                                "entropy": 13.370769500732422,
                                "conf": 0.4080105228990415,
                                "stoi": 1.0000000000000002
                            },
                            "clarity_sam": {
                                "snr": 30.722883224487305,
                                "hnr": 0,
                                "entropy": 13.571340560913086,
                                "conf": 0.008733270776599045,
                                "stoi": 0.9999999999999998
                            },
                            "index": -0.08330349673179316,
                            "level": 5,
                            "suggestions": "根據提供的結果顯示，受測者的發音存在明顯問題，建議進行口腔肌肉訓練、最小對比練習以及模仿練習等訓練。"
                        },
                        "analysis_model_version": "v1.1",
                        "processing_time_seconds": 26.194589853286743,
                        "created_at": "2025-09-04T15:12:44.079713"
                    },
                    {
                        "result_id": "bab270a7-aec9-4665-a1e6-07b915714b58",
                        "task_id": "e98692d8-5768-4099-967e-9948d4e78189",
                        "analysis_result": {
                            "similarity": {
                                "emb": 0.6940064549446106,
                                "wer": 0,
                                "txt_ref": "好的,我想要一份特餐。",
                                "txt_sam": "好的我要一份特差"
                            },
                            "clarity_ref": {
                                "snr": 39.5557861328125,
                                "hnr": 0,
                                "entropy": 13.092965126037598,
                                "conf": 0.427827858647708,
                                "stoi": 0.9999999999999999
                            },
                            "clarity_sam": {
                                "snr": 28.97469711303711,
                                "hnr": 0,
                                "entropy": 12.927165031433105,
                                "conf": 0.34627757284357097,
                                "stoi": 0.9999999999999997
                            },
                            "index": 0.6700844012461471,
                            "level": 2,
                            "suggestions": "受測者的發音屬中等程度，建議進行音量清晰度練習、口腔肌群訓練以及母音子音精確發音練習。"
                        },
                        "analysis_model_version": "v1.1",
                        "processing_time_seconds": 16.262873888015747,
                        "created_at": "2025-09-04T15:12:38.480743"
                    }
                ]
            }
        }
    )
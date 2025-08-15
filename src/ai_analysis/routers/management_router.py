"""
VocalBorn 系統管理 API

提供透過 HTTP API 管理 Celery 任務系統的介面，取代 CLI 操作
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Annotated
from datetime import datetime
from sqlmodel import Session

from src.shared.database.database import get_session
from src.auth.services.permission_service import RequireAdmin
from src.auth.models import User

from celery_app.tasks import test_task
from celery_app.app import app

management_router = APIRouter(
    prefix="/celery/management",
    tags=["系統管理"]
)


@management_router.get(
    "/status",
    response_model=Dict[str, Any],
)
async def get_system_status(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """取得系統狀態"""
    #TODO: 使用Flower API 來進行管理




@management_router.post(
    "/tasks/test",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "測試任務已提交",
            "content": {
                "application/json": {
                    "example": {
                        "message": "測試任務已提交",
                        "task_id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
                        "status": "submitted",
                        "test_message": "Hello from API!"
                    }
                }
            }
        }
    }
)
async def submit_test_task(
    message: str = "Hello from API!",
    session: Annotated[Session, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(RequireAdmin)] = None
) -> Dict[str, Any]:
    """提交測試任務"""
    try:
        task = test_task.apply_async(
            args=[message],
            queue='ai_analysis'
        )
        
        return {
            "message": "測試任務已提交",
            "task_id": task.id,
            "status": "submitted",
            "test_message": message
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"測試任務提交失敗: {str(exc)}")


@management_router.get(
    "/tasks/{task_id}",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "任務狀態資訊",
            "content": {
                "application/json": {
                    "examples": {
                        "completed": {
                            "summary": "任務完成",
                            "value": {
                                "task_id": "c3d4e5f6-g7h8-9012-cdef-345678901234",
                                "status": "SUCCESS",
                                "ready": True,
                                "timestamp": "2025-08-14T03:39:28.571815",
                                "result": {
                                    "task_id": "c3d4e5f6-g7h8-9012-cdef-345678901234",
                                    "message": "Hello from API!",
                                    "timestamp": "2025-08-14T03:39:12.289216",
                                    "status": "completed"
                                }
                            }
                        },
                        "progress": {
                            "summary": "任務進行中",
                            "value": {
                                "task_id": "c3d4e5f6-g7h8-9012-cdef-345678901234",
                                "status": "PENDING",
                                "ready": False,
                                "timestamp": "2025-08-14T03:39:28.571815"
                            }
                        },
                        "failed": {
                            "summary": "任務失敗",
                            "value": {
                                "task_id": "c3d4e5f6-g7h8-9012-cdef-345678901234",
                                "status": "FAILURE",
                                "ready": True,
                                "timestamp": "2025-08-14T03:39:28.571815",
                                "error": "Processing failed due to invalid input"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_task_status(
    task_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """取得任務狀態"""
    try:
        result = app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "timestamp": datetime.now().isoformat()
        }
        
        if result.status == 'PROGRESS':
            response["progress"] = result.info
        elif result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = result.info
        
        return response
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"無法取得任務狀態: {str(exc)}")
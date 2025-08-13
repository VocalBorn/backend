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
from ..celery_app import app, monitor
from ..celery_tasks import health_check, cleanup_expired_tasks, test_task

management_router = APIRouter(
    prefix="/celery/management",
    tags=["系統管理"]
)


@management_router.get("/status")
async def get_system_status(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """取得系統狀態"""
    try:
        # Worker 狀態
        worker_stats = {}
        try:
            stats = monitor.get_worker_stats()
            worker_stats = {
                "active_workers": len(stats.get('active', {})),
                "workers": stats.get('active', {}),
                "available": True
            }
        except Exception as exc:
            worker_stats = {
                "active_workers": 0,
                "workers": {},
                "available": False,
                "error": str(exc)
            }
        
        # 佇列狀態
        queue_status = {}
        queues = ['ai_analysis', 'maintenance', 'health']
        for queue in queues:
            try:
                length = monitor.get_queue_length(queue)
                queue_status[queue] = {
                    "pending_tasks": length,
                    "available": True
                }
            except Exception as exc:
                queue_status[queue] = {
                    "pending_tasks": 0,
                    "available": False,
                    "error": str(exc)
                }
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "workers": worker_stats,
            "queues": queue_status,
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"無法取得系統狀態: {str(exc)}")


@management_router.post("/health-check")
async def run_health_check(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """執行系統健康檢查"""
    try:
        # 提交健康檢查任務
        task = health_check.apply_async(queue='health')
        
        return {
            "message": "健康檢查已啟動",
            "task_id": task.id,
            "status": "submitted"
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"健康檢查提交失敗: {str(exc)}")


@management_router.get("/health-check/{task_id}")
async def get_health_check_result(
    task_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """取得健康檢查結果"""
    try:
        result = app.AsyncResult(task_id)
        
        if not result.ready():
            return {
                "task_id": task_id,
                "status": result.status,
                "ready": False,
                "info": result.info if result.status == 'PROGRESS' else None
            }
        
        if result.successful():
            return {
                "task_id": task_id,
                "status": "completed",
                "ready": True,
                "result": result.result
            }
        else:
            return {
                "task_id": task_id,
                "status": "failed",
                "ready": True,
                "error": result.info
            }
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"無法取得健康檢查結果: {str(exc)}")


@management_router.post("/tasks/test")
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


@management_router.get("/tasks/{task_id}")
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


@management_router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    terminate: bool = False,
    session: Annotated[Session, Depends(get_session)] = None,
    current_user: Annotated[User, Depends(RequireAdmin)] = None
) -> Dict[str, Any]:
    """取消任務"""
    try:
        app.control.revoke(task_id, terminate=terminate)
        
        return {
            "message": f"任務已{'強制終止' if terminate else '標記為取消'}",
            "task_id": task_id,
            "terminated": terminate,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(exc)}")


@management_router.post("/cleanup")
async def run_cleanup(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """執行過期任務清理"""
    try:
        task = cleanup_expired_tasks.apply_async(queue='maintenance')
        
        return {
            "message": "清理任務已啟動",
            "task_id": task.id,
            "status": "submitted"
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"清理任務提交失敗: {str(exc)}")


@management_router.delete("/queues/{queue_name}")
async def purge_queue(
    queue_name: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """清空指定佇列"""
    try:
        # 安全檢查：只允許清空特定佇列
        allowed_queues = ['ai_analysis', 'maintenance', 'health']
        if queue_name not in allowed_queues:
            raise HTTPException(
                status_code=400, 
                detail=f"不允許清空佇列 '{queue_name}'。允許的佇列: {allowed_queues}"
            )
        
        count = monitor.purge_queue(queue_name)
        
        return {
            "message": f"佇列 '{queue_name}' 已清空",
            "queue_name": queue_name,
            "purged_tasks": count,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"清空佇列失敗: {str(exc)}")


@management_router.get("/queues")
async def list_queues(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """列出所有佇列及其狀態"""
    try:
        queues = ['ai_analysis', 'maintenance', 'health']
        queue_info = {}
        
        for queue in queues:
            try:
                length = monitor.get_queue_length(queue)
                queue_info[queue] = {
                    "pending_tasks": length,
                    "available": True
                }
            except Exception as exc:
                queue_info[queue] = {
                    "pending_tasks": 0,
                    "available": False,
                    "error": str(exc)
                }
        
        return {
            "queues": queue_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"無法列出佇列: {str(exc)}")


@management_router.get("/workers")
async def list_workers(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(RequireAdmin)]
) -> Dict[str, Any]:
    """列出所有 Worker 及其狀態"""
    try:
        stats = monitor.get_worker_stats()
        
        return {
            "workers": stats.get('active', {}),
            "active_count": len(stats.get('active', {})),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"無法列出 Worker: {str(exc)}")
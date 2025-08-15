"""
健康檢查任務

檢查系統各組件的健康狀態，包括資料庫連線等。
"""

from typing import Dict, Any
from datetime import datetime

from src.shared.database.database import engine
from sqlmodel import Session

from ..app import app
from .utils import log_task_start, log_task_complete, log_task_error


@app.task(bind=True)
def health_check(self) -> Dict[str, Any]:
    """健康檢查任務
    
    Args:
        self: Celery 任務實例
        
    Returns:
        健康檢查結果字典
        
    Raises:
        Exception: 健康檢查失敗時
    """
    task_id = self.request.id
    log_task_start("健康檢查", task_id)
    
    try:
        checks = {}
        
        # 檢查資料庫連線
        try:
            with Session(engine) as db:
                db.exec("SELECT 1").first()
            checks["database"] = "ok"
        except Exception as db_exc:
            checks["database"] = f"error: {str(db_exc)}"
        
        # 可以添加更多檢查項目
        # 例如：Redis 連線、外部服務連線等
        
        # 判斷整體狀態
        overall_status = "healthy" if all(
            status == "ok" for status in checks.values()
        ) else "unhealthy"
        
        result = {
            "task_id": task_id,
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }
        
        log_task_complete("健康檢查", task_id, f"狀態: {overall_status}")
        return result
        
    except Exception as exc:
        log_task_error("健康檢查", task_id, exc)
        raise exc
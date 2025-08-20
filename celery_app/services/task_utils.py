"""任務管理工具服務

提供 AI 分析任務的狀態管理、結果建立等相關功能。
"""

import logging
import uuid
from contextlib import contextmanager
from typing import Optional

from sqlmodel import Session, select

from src.ai_analysis.models import AIAnalysisResult, AIAnalysisTask, TaskStatus
from src.shared.database.database import engine

logger = logging.getLogger(__name__)


class TaskManagementError(Exception):
    """任務管理自定義異常"""
    pass


@contextmanager
def get_db_session():
    """資料庫會話上下文管理器
    
    Yields:
        Session: SQLModel 資料庫會話
        
    Raises:
        Exception: 資料庫操作錯誤時
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def update_task_status(
    session: Session,
    task_id: uuid.UUID,
    status: TaskStatus,
    error_message: Optional[str] = None
) -> None:
    """更新 AI 分析任務狀態
    
    Args:
        session: 資料庫會話
        task_id: 任務 ID
        status: 新的任務狀態
        error_message: 錯誤訊息（可選）
        
    Raises:
        TaskManagementError: 任務狀態更新失敗時
    """
    try:
        task = session.get(AIAnalysisTask, task_id)
        if task:
            task.status = status
            session.add(task)
            session.commit()
            logger.info(f"任務狀態已更新: {task_id} -> {status}")
            
            if error_message:
                logger.error(f"任務 {task_id} 錯誤: {error_message}")
        else:
            raise TaskManagementError(f"找不到任務: {task_id}")
            
    except Exception as e:
        logger.error(f"更新任務狀態失敗: {task_id}, 錯誤: {e}")
        session.rollback()
        raise TaskManagementError(f"任務狀態更新失敗: {e}")


def create_analysis_result(
    session: Session,
    task_id: uuid.UUID,
    analysis_result: dict,
    processing_time: float,
    model_version: str = "v1.0"
) -> None:
    """建立 AI 分析結果記錄
    
    Args:
        session: 資料庫會話
        task_id: 任務 ID
        analysis_result: 分析結果資料
        processing_time: 處理時間（秒）
        model_version: 模型版本號
        
    Raises:
        TaskManagementError: 分析結果建立失敗時
    """
    try:
        result = AIAnalysisResult(
            task_id=task_id,
            analysis_result=analysis_result,
            analysis_model_version=model_version,
            processing_time_seconds=processing_time
        )
        session.add(result)
        session.commit()
        logger.info(f"分析結果已建立: {task_id}")
        
    except Exception as e:
        logger.error(f"建立分析結果失敗: {task_id}, 錯誤: {e}")
        session.rollback()
        raise TaskManagementError(f"分析結果建立失敗: {e}")


def find_ai_task_by_celery_id(session: Session, celery_task_id: str) -> Optional[AIAnalysisTask]:
    """根據 Celery 任務 ID 查詢 AI 分析任務
    
    Args:
        session: 資料庫會話
        celery_task_id: Celery 任務 ID
        
    Returns:
        Optional[AIAnalysisTask]: AI 分析任務物件，如果找不到則返回 None
    """
    try:
        statement = select(AIAnalysisTask).where(
            AIAnalysisTask.celery_task_id == celery_task_id
        )
        return session.exec(statement).first()
    except Exception as e:
        logger.error(f"查詢 AI 任務失敗: {celery_task_id}, 錯誤: {e}")
        return None


__all__ = [
    "get_db_session", 
    "update_task_status", 
    "create_analysis_result", 
    "find_ai_task_by_celery_id",
    "TaskManagementError"
]
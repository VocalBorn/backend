"""AI 分析任務管理服務

提供 AI 分析任務的資料庫操作和狀態管理功能。
"""

import logging
import uuid
from typing import Optional

from sqlmodel import Session, select

from src.ai_analysis.models import AIAnalysisTask, AIAnalysisResult, TaskStatus


logger = logging.getLogger(__name__)


class TaskManagementServiceError(Exception):
    """任務管理服務自定義異常"""
    pass


async def create_task_record(
    user_id: uuid.UUID,
    db_session: Session,
    task_type: str = "audio_analysis",
    task_params: dict = None
) -> AIAnalysisTask:
    """在資料庫中建立新的 AI 分析任務記錄
    
    Args:
        user_id: 使用者 ID
        task_type: 任務類型
        task_params: 任務參數
        db_session: 資料庫會話
        
    Returns:
        AIAnalysisTask: 建立的任務記錄
        
    Raises:
        TaskManagementServiceError: 建立任務記錄失敗時拋出
    """
    try:
        analysis_task = AIAnalysisTask(
            user_id=user_id,
            task_type=task_type,
            task_params=task_params,
            status=TaskStatus.PENDING
        )
        
        db_session.add(analysis_task)
        db_session.commit()
        db_session.refresh(analysis_task)
        
        logger.info(f"成功建立 AI 分析任務記錄: {analysis_task.task_id}")
        return analysis_task
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"建立任務記錄失敗: {e}")
        raise TaskManagementServiceError(f"建立任務記錄失敗: {str(e)}")


async def update_task_status(
    task_id: uuid.UUID,
    status: TaskStatus,
    celery_task_id: str = None,
    db_session: Session = None
) -> AIAnalysisTask:
    """更新 AI 分析任務狀態
    
    Args:
        task_id: 任務 ID
        status: 新的任務狀態
        celery_task_id: Celery 任務 ID（可選）
        db_session: 資料庫會話
        
    Returns:
        AIAnalysisTask: 更新後的任務記錄
        
    Raises:
        TaskManagementServiceError: 更新失敗時拋出
    """
    try:
        analysis_task = db_session.get(AIAnalysisTask, task_id)
        if not analysis_task:
            raise TaskManagementServiceError(f"找不到任務 ID: {task_id}")
        
        analysis_task.status = status
        if celery_task_id:
            analysis_task.celery_task_id = celery_task_id
        
        db_session.add(analysis_task)
        db_session.commit()
        db_session.refresh(analysis_task)
        
        logger.info(f"成功更新任務狀態: {task_id} -> {status}")
        return analysis_task
        
    except Exception as e:
        if db_session:
            db_session.rollback()
        logger.error(f"更新任務狀態失敗: {e}")
        raise TaskManagementServiceError(f"更新任務狀態失敗: {str(e)}")


async def update_task_status_by_celery_id(
    celery_task_id: str,
    status: TaskStatus,
    db_session: Session
) -> Optional[AIAnalysisTask]:
    """透過 Celery 任務 ID 更新任務狀態
    
    Args:
        celery_task_id: Celery 任務 ID
        status: 新的任務狀態
        db_session: 資料庫會話
        
    Returns:
        Optional[AIAnalysisTask]: 更新後的任務記錄，如果找不到則返回 None
        
    Raises:
        TaskManagementServiceError: 更新失敗時拋出
    """
    try:
        stmt = select(AIAnalysisTask).where(AIAnalysisTask.celery_task_id == celery_task_id)
        analysis_task = db_session.exec(stmt).first()
        
        if not analysis_task:
            logger.warning(f"找不到 Celery 任務 ID: {celery_task_id}")
            return None
        
        analysis_task.status = status
        db_session.add(analysis_task)
        db_session.commit()
        db_session.refresh(analysis_task)
        
        logger.info(f"成功透過 Celery ID 更新任務狀態: {celery_task_id} -> {status}")
        return analysis_task
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"透過 Celery ID 更新任務狀態失敗: {e}")
        raise TaskManagementServiceError(f"更新任務狀態失敗: {str(e)}")


async def save_analysis_result(
    task_id: uuid.UUID,
    analysis_result: dict,
    analysis_model_version: str = None,
    processing_time_seconds: float = None,
    db_session: Session = None
) -> AIAnalysisResult:
    """儲存 AI 分析結果到資料庫
    
    Args:
        task_id: 關聯的任務 ID
        analysis_result: 分析結果字典
        analysis_model_version: AI 模型版本
        processing_time_seconds: 處理耗時（秒）
        db_session: 資料庫會話
        
    Returns:
        AIAnalysisResult: 儲存的分析結果記錄
        
    Raises:
        TaskManagementServiceError: 儲存失敗時拋出
    """
    try:
        # 檢查任務是否存在
        analysis_task = db_session.get(AIAnalysisTask, task_id)
        if not analysis_task:
            raise TaskManagementServiceError(f"找不到任務 ID: {task_id}")
        
        # 建立分析結果記錄
        analysis_result_record = AIAnalysisResult(
            task_id=task_id,
            analysis_result=analysis_result,
            analysis_model_version=analysis_model_version,
            processing_time_seconds=processing_time_seconds
        )
        
        db_session.add(analysis_result_record)

        # 同時更新任務狀態為成功
        analysis_task.status = TaskStatus.SUCCESS
        db_session.add(analysis_task)
        
        db_session.commit()
        db_session.refresh(analysis_result_record)
        
        logger.info(f"成功儲存分析結果: task_id={task_id}, result_id={analysis_result_record.result_id}")
        return analysis_result_record
        
    except Exception as e:
        if db_session:
            db_session.rollback()
        logger.error(f"儲存分析結果失敗: {e}")
        raise TaskManagementServiceError(f"儲存分析結果失敗: {str(e)}")


async def save_analysis_result_by_celery_id(
    celery_task_id: str,
    analysis_result: dict,
    analysis_model_version: str = None,
    processing_time_seconds: float = None,
    db_session: Session = None
) -> Optional[AIAnalysisResult]:
    """透過 Celery 任務 ID 儲存分析結果
    
    Args:
        celery_task_id: Celery 任務 ID
        analysis_result: 分析結果字典
        analysis_model_version: AI 模型版本
        processing_time_seconds: 處理耗時（秒）
        db_session: 資料庫會話
        
    Returns:
        Optional[AIAnalysisResult]: 儲存的分析結果記錄，如果找不到任務則返回 None
        
    Raises:
        TaskManagementServiceError: 儲存失敗時拋出
    """
    try:
        # 透過 Celery ID 查詢任務
        stmt = select(AIAnalysisTask).where(AIAnalysisTask.celery_task_id == celery_task_id)
        analysis_task = db_session.exec(stmt).first()
        
        if not analysis_task:
            logger.warning(f"找不到 Celery 任務 ID: {celery_task_id}")
            return None
        
        # 使用已找到的任務 ID 儲存結果
        return await save_analysis_result(
            task_id=analysis_task.task_id,
            analysis_result=analysis_result,
            analysis_model_version=analysis_model_version,
            processing_time_seconds=processing_time_seconds,
            db_session=db_session
        )
        
    except Exception as e:
        logger.error(f"透過 Celery ID 儲存分析結果失敗: {e}")
        raise TaskManagementServiceError(f"儲存分析結果失敗: {str(e)}")


async def get_task_by_celery_id(
    celery_task_id: str,
    db_session: Session
) -> Optional[AIAnalysisTask]:
    """透過 Celery 任務 ID 查詢任務
    
    Args:
        celery_task_id: Celery 任務 ID
        db_session: 資料庫會話
        
    Returns:
        Optional[AIAnalysisTask]: 查詢到的任務記錄，如果找不到則返回 None
    """
    try:
        stmt = select(AIAnalysisTask).where(AIAnalysisTask.celery_task_id == celery_task_id)
        return db_session.exec(stmt).first()
        
    except Exception as e:
        logger.error(f"透過 Celery ID 查詢任務失敗: {e}")
        return None


__all__ = [
    "create_task_record",
    "update_task_status",
    "update_task_status_by_celery_id", 
    "save_analysis_result",
    "save_analysis_result_by_celery_id",
    "get_task_by_celery_id",
    "TaskManagementServiceError"
]
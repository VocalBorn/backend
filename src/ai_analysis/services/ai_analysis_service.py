"""AI 分析任務服務

提供 AI 分析任務的核心業務邏輯，包括任務建立、提交和狀態管理。
"""

import logging
import uuid
from typing import List, Optional, Tuple

from sqlmodel import Session, select

from src.ai_analysis.models import AIAnalysisTask, AIAnalysisResult, TaskStatus
from src.ai_analysis.services.task_management_service import (
    create_task_record
)
from src.practice.models import PracticeRecord, PracticeSession
from celery_app.tasks.analyze_audio import analyze_audio_task


logger = logging.getLogger(__name__)


class AIAnalysisServiceError(Exception):
    """AI 分析服務自定義異常"""
    pass


async def create_analysis_tasks_for_session(
    practice_session_id: uuid.UUID,
    user_id: uuid.UUID,
    db_session: Session
) -> List[AIAnalysisTask]:
    """為完成的練習會話建立所有 AI 分析任務
    
    Args:
        practice_session_id: 練習會話 ID
        user_id: 使用者 ID
        db_session: 資料庫會話
        
    Returns:
        List[AIAnalysisTask]: 建立的分析任務清單
        
    Raises:
        AIAnalysisServiceError: AI 分析服務相關錯誤
    """
    try:
        logger.info(f"開始為會話 {practice_session_id} 建立 AI 分析任務")
        
        # 查詢該會話下所有已完成的練習記錄
        stmt = select(PracticeRecord).where(
            PracticeRecord.practice_session_id == practice_session_id,
            PracticeRecord.audio_path.is_not(None)  # 確保有音訊檔案
        )
        practice_records = db_session.exec(stmt).all()
        
        if not practice_records:
            logger.warning(f"會話 {practice_session_id} 沒有找到有音訊檔案的練習記錄")
            return []
        
        created_tasks = []
        
        # 為每個練習記錄建立 AI 分析任務
        for practice_record in practice_records:
            try:
                analysis_task = await submit_audio_analysis_task(
                    practice_record_id=practice_record.practice_record_id,
                    sentence_id=practice_record.sentence_id,
                    user_id=user_id,
                    db_session=db_session
                )
                created_tasks.append(analysis_task)
                
            except Exception as e:
                logger.error(f"為練習記錄 {practice_record.practice_record_id} 建立分析任務失敗: {e}")
                # 繼續處理其他記錄，不中斷整個流程
                continue
        
        logger.info(f"成功為會話 {practice_session_id} 建立了 {len(created_tasks)} 個 AI 分析任務")
        return created_tasks
        
    except Exception as e:
        logger.error(f"建立會話 {practice_session_id} 的 AI 分析任務失敗: {e}")
        raise AIAnalysisServiceError(f"建立 AI 分析任務失敗: {str(e)}")


async def submit_audio_analysis_task(
    practice_record_id: uuid.UUID,
    sentence_id: uuid.UUID,
    user_id: uuid.UUID,
    db_session: Session,
    analysis_params: dict = None
) -> AIAnalysisTask:
    """提交音訊分析任務到 Celery
    
    Args:
        practice_record_id: 練習記錄 ID
        sentence_id: 句子 ID
        user_id: 使用者 ID
        db_session: 資料庫會話
        analysis_params: 分析參數（可選）
        
    Returns:
        AIAnalysisTask: 建立的分析任務記錄
        
    Raises:
        AIAnalysisServiceError: AI 分析服務相關錯誤
    """
    try:
        logger.info(f"開始提交音訊分析任務: practice_record={practice_record_id}")
        
        # 1. 在資料庫中建立任務記錄
        analysis_task = await create_task_record(
            user_id=user_id,
            db_session=db_session,
            task_type="audio_analysis",
            task_params={
                "practice_record_id": str(practice_record_id),
                "sentence_id": str(sentence_id),
                "analysis_params": analysis_params or {}
            }
        )
        
        # 2. 提交 Celery 任務
        celery_task = analyze_audio_task.delay(
            practice_record_id=str(practice_record_id),
            sentence_id=str(sentence_id),
            analysis_params=analysis_params
        )
        
        # 3. 更新任務記錄的 Celery ID 和狀態
        analysis_task.celery_task_id = celery_task.id
        analysis_task.status = TaskStatus.PROCESSING
        db_session.add(analysis_task)
        db_session.commit()
        db_session.refresh(analysis_task)
        
        logger.info(f"成功提交音訊分析任務: task_id={analysis_task.task_id}, celery_id={celery_task.id}")
        return analysis_task
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"提交音訊分析任務失敗: {e}")
        raise AIAnalysisServiceError(f"提交分析任務失敗: {str(e)}")


async def get_analysis_task_status(
    task_id: uuid.UUID,
    db_session: Session
) -> AIAnalysisTask:
    """查詢 AI 分析任務狀態
    
    Args:
        task_id: 任務 ID
        db_session: 資料庫會話
        
    Returns:
        AIAnalysisTask: 分析任務記錄
        
    Raises:
        AIAnalysisServiceError: 任務不存在時拋出異常
    """
    analysis_task = db_session.get(AIAnalysisTask, task_id)
    if not analysis_task:
        raise AIAnalysisServiceError(f"找不到任務 ID: {task_id}")
    
    return analysis_task


async def get_user_analysis_tasks(
    user_id: uuid.UUID,
    db_session: Session,
    status: TaskStatus = None,
    limit: int = 50,
    offset: int = 0
) -> List[AIAnalysisTask]:
    """查詢使用者的 AI 分析任務清單
    
    Args:
        user_id: 使用者 ID
        db_session: 資料庫會話
        status: 篩選特定狀態的任務（可選）
        limit: 回傳筆數限制
        offset: 查詢偏移量
        
    Returns:
        List[AIAnalysisTask]: 分析任務清單
    """
    stmt = select(AIAnalysisTask).where(AIAnalysisTask.user_id == user_id)
    
    if status:
        stmt = stmt.where(AIAnalysisTask.status == status)
    
    stmt = stmt.offset(offset).limit(limit).order_by(AIAnalysisTask.created_at.desc())
    
    return db_session.exec(stmt).all()


async def get_session_ai_analysis_results(
    practice_session_id: uuid.UUID,
    user_id: uuid.UUID,
    db_session: Session
) -> Tuple[int, List[AIAnalysisResult]]:
    """取得練習會話的 AI 分析結果
    
    查詢指定練習會話的所有 AI 分析結果，並回傳總數和所有的分析結果。
    
    Args:
        practice_session_id: 練習會話 ID
        user_id: 使用者 ID，用於權限驗證
        db_session: 資料庫會話
        
    Returns:
        Tuple[int, List[AIAnalysisResult]]: (總結果數量, 所有的分析結果)
        
    Raises:
        AIAnalysisServiceError: 會話不存在或無權限存取時拋出異常
    """
    try:
        logger.info(f"開始查詢會話 {practice_session_id} 的 AI 分析結果")
        
        # 1. 驗證練習會話存在且屬於當前使用者
        practice_session = db_session.get(PracticeSession, practice_session_id)
        if not practice_session:
            raise AIAnalysisServiceError(f"找不到練習會話: {practice_session_id}")
        
        if practice_session.user_id != user_id:
            raise AIAnalysisServiceError("無權限存取此練習會話")
        
        # 2. 查詢該會話下所有的練習記錄
        practice_records_stmt = select(PracticeRecord).where(
            PracticeRecord.practice_session_id == practice_session_id
        )
        practice_records = db_session.exec(practice_records_stmt).all()
        
        if not practice_records:
            logger.info(f"會話 {practice_session_id} 沒有練習記錄")
            return 0, []
        
        # 3. 取得這些練習記錄相關的 AI 分析任務
        practice_record_ids = [record.practice_record_id for record in practice_records]
        
        # 查詢相關的 AI 分析任務（透過 task_params 中的 practice_record_id）
        tasks_stmt = select(AIAnalysisTask).where(
            AIAnalysisTask.user_id == user_id,
            AIAnalysisTask.status == TaskStatus.SUCCESS
        )
        all_tasks = db_session.exec(tasks_stmt).all()
        
        # 篩選與這個會話相關的任務
        session_tasks = []
        for task in all_tasks:
            if (task.task_params and 
                task.task_params.get("practice_record_id") and
                uuid.UUID(task.task_params["practice_record_id"]) in practice_record_ids):
                session_tasks.append(task)
        
        if not session_tasks:
            logger.info(f"會話 {practice_session_id} 沒有成功的 AI 分析任務")
            return 0, []
        
        # 4. 查詢這些任務的分析結果
        task_ids = [task.task_id for task in session_tasks]
        results_stmt = select(AIAnalysisResult).where(
            AIAnalysisResult.task_id.in_(task_ids)
        ).order_by(AIAnalysisResult.created_at.desc())
        
        results = db_session.exec(results_stmt).all()
        
        if not results:
            logger.info(f"會話 {practice_session_id} 沒有 AI 分析結果")
            return len(session_tasks), []
        
        # 5. 回傳總數和所有結果（已按時間降序排列）
        logger.info(f"會話 {practice_session_id} 共有 {len(results)} 個 AI 分析結果")
        return len(results), results
        
    except AIAnalysisServiceError:
        # 重新拋出業務邏輯異常
        raise
    except Exception as e:
        logger.error(f"查詢會話 {practice_session_id} 的 AI 分析結果失敗: {e}")
        raise AIAnalysisServiceError(f"查詢 AI 分析結果失敗: {str(e)}")


__all__ = [
    "create_analysis_tasks_for_session",
    "submit_audio_analysis_task", 
    "get_analysis_task_status",
    "get_user_analysis_tasks",
    "get_session_ai_analysis_results",
    "AIAnalysisServiceError"
]
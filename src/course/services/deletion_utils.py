"""
刪除操作輔助工具模組

提供處理課程相關資料刪除時的外鍵約束清理功能
"""
import uuid
from typing import List
from sqlmodel import Session, select
from src.practice.models import PracticeSession, PracticeRecord, PracticeFeedback, PracticeSessionFeedback
from src.ai_analysis.models import AIAnalysisTask, AIAnalysisResult


async def delete_practice_records_and_related_data(
    practice_record_ids: List[uuid.UUID], 
    session: Session
) -> None:
    """刪除練習記錄及其相關資料
    
    Args:
        practice_record_ids: 要刪除的練習記錄 ID 列表
        session: 資料庫會話
    """
    if not practice_record_ids:
        return
    
    # 1. 查詢所有 AI 分析任務，並篩選與這些 practice_record 相關的任務
    ai_tasks = session.exec(select(AIAnalysisTask)).all()
    
    # 篩選出與這些 practice_record 相關的任務
    related_task_ids = []
    practice_record_str_ids = [str(record_id) for record_id in practice_record_ids]
    
    for task in ai_tasks:
        if task.task_params:
            try:
                # 檢查 task_params 中是否包含相關的 practice_record_id
                if isinstance(task.task_params, dict):
                    # 如果是字典，直接查找鍵值
                    if 'practice_record_id' in task.task_params:
                        if str(task.task_params['practice_record_id']) in practice_record_str_ids:
                            related_task_ids.append(task.task_id)
                else:
                    # 如果不是字典，轉為字符串搜尋
                    task_params_str = str(task.task_params)
                    if any(record_id_str in task_params_str for record_id_str in practice_record_str_ids):
                        related_task_ids.append(task.task_id)
            except Exception:
                # 如果處理 task_params 時出錯，跳過該任務
                continue
    
    if related_task_ids:
        # 刪除 AI 分析結果
        ai_results = session.exec(
            select(AIAnalysisResult).where(
                AIAnalysisResult.task_id.in_(related_task_ids)
            )
        ).all()
        for result in ai_results:
            session.delete(result)
        
        # 刪除 AI 分析任務
        for task_id in related_task_ids:
            task = session.get(AIAnalysisTask, task_id)
            if task:
                session.delete(task)
    
    # 2. 刪除練習回饋
    practice_feedbacks = session.exec(
        select(PracticeFeedback).where(
            PracticeFeedback.practice_record_id.in_(practice_record_ids)
        )
    ).all()
    for feedback in practice_feedbacks:
        session.delete(feedback)
    
    # 3. 刪除練習記錄
    practice_records = session.exec(
        select(PracticeRecord).where(
            PracticeRecord.practice_record_id.in_(practice_record_ids)
        )
    ).all()
    for record in practice_records:
        session.delete(record)
    
    # 確保在刪除記錄後立即提交，避免外鍵約束問題
    session.flush()


async def delete_practice_sessions_and_related_data(
    practice_session_ids: List[uuid.UUID], 
    session: Session
) -> None:
    """刪除練習會話及其相關資料
    
    Args:
        practice_session_ids: 要刪除的練習會話 ID 列表
        session: 資料庫會話
    """
    if not practice_session_ids:
        return
    
    # 1. 取得所有相關的練習記錄 ID
    practice_records = session.exec(
        select(PracticeRecord).where(
            PracticeRecord.practice_session_id.in_(practice_session_ids)
        )
    ).all()
    
    practice_record_ids = [record.practice_record_id for record in practice_records]
    
    # 2. 刪除練習記錄及其相關資料
    if practice_record_ids:
        await delete_practice_records_and_related_data(practice_record_ids, session)
    
    # 3. 刪除練習會話回饋
    session_feedbacks = session.exec(
        select(PracticeSessionFeedback).where(
            PracticeSessionFeedback.practice_session_id.in_(practice_session_ids)
        )
    ).all()
    for feedback in session_feedbacks:
        session.delete(feedback)
    
    # 4. 刪除練習會話
    practice_sessions = session.exec(
        select(PracticeSession).where(
            PracticeSession.practice_session_id.in_(practice_session_ids)
        )
    ).all()
    for session_obj in practice_sessions:
        session.delete(session_obj)


async def get_practice_sessions_by_chapter_id(
    chapter_id: uuid.UUID, 
    session: Session
) -> List[uuid.UUID]:
    """取得特定章節的所有練習會話 ID
    
    Args:
        chapter_id: 章節 ID
        session: 資料庫會話
        
    Returns:
        練習會話 ID 列表
    """
    practice_sessions = session.exec(
        select(PracticeSession).where(PracticeSession.chapter_id == chapter_id)
    ).all()
    
    return [session_obj.practice_session_id for session_obj in practice_sessions]


async def get_practice_records_by_sentence_id(
    sentence_id: uuid.UUID, 
    session: Session
) -> List[uuid.UUID]:
    """取得特定語句的所有練習記錄 ID
    
    Args:
        sentence_id: 語句 ID
        session: 資料庫會話
        
    Returns:
        練習記錄 ID 列表
    """
    practice_records = session.exec(
        select(PracticeRecord).where(PracticeRecord.sentence_id == sentence_id)
    ).all()
    
    return [record.practice_record_id for record in practice_records]
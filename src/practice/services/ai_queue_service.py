"""
AI 分析排隊管理服務
處理 AI 分析請求的排隊、優先級管理和狀態追蹤
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlmodel import Session, select, and_, desc, func, asc, or_
from fastapi import HTTPException, status

from src.course.models import (
    PracticeRecord, PracticeStatus, 
    AIAnalysisQueue, AIAnalysisQueueStatus, AIAnalysisPriority,
    AIAnalysisResult
)
from src.practice.ai_schemas import (
    AIAnalysisQueueCreate,
    AIAnalysisQueueResponse,
    AIAnalysisQueueUpdate,
    AIAnalysisQueueListResponse,
    QueueStatusResponse,
    UserQueueStatusResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse
)

logger = logging.getLogger(__name__)

# 優先級權重（數字越小優先級越高）
PRIORITY_WEIGHTS = {
    AIAnalysisPriority.URGENT: 1,
    AIAnalysisPriority.HIGH: 2,
    AIAnalysisPriority.NORMAL: 3,
    AIAnalysisPriority.LOW: 4
}

class AIQueueManager:
    """AI 分析排隊管理器"""
    
    def __init__(self):
        self.max_concurrent_processing = 5  # 最大並行處理數
        self.default_estimated_duration = 60  # 預設處理時間（秒）
        self.max_retries = 3
    
    async def add_to_queue(
        self,
        practice_record_id: uuid.UUID,
        priority: AIAnalysisPriority,
        session: Session
    ) -> AIAnalysisQueue:
        """
        將練習記錄添加到 AI 分析排隊
        
        Args:
            practice_record_id: 練習記錄ID
            priority: 優先級
            session: 資料庫會話
            
        Returns:
            創建的排隊記錄
            
        Raises:
            HTTPException: 當練習記錄不存在或已在排隊中時
        """
        # 檢查練習記錄是否存在
        practice_record = session.get(PracticeRecord, practice_record_id)
        if not practice_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="練習記錄不存在"
            )
        
        # 檢查是否已在排隊中
        existing_queue = session.exec(
            select(AIAnalysisQueue).where(
                AIAnalysisQueue.practice_record_id == practice_record_id
            )
        ).first()
        
        if existing_queue:
            if existing_queue.status in [AIAnalysisQueueStatus.PENDING, AIAnalysisQueueStatus.PROCESSING]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="該練習記錄已在 AI 分析排隊中"
                )
            # 如果之前失敗或取消，可以重新排隊
            elif existing_queue.status in [AIAnalysisQueueStatus.FAILED, AIAnalysisQueueStatus.CANCELLED]:
                existing_queue.status = AIAnalysisQueueStatus.PENDING
                existing_queue.priority = priority
                existing_queue.queued_at = datetime.now()
                existing_queue.retry_count += 1
                existing_queue.error_message = None
                existing_queue.updated_at = datetime.now()
                
                session.add(existing_queue)
                session.commit()
                session.refresh(existing_queue)
                
                logger.info(f"重新排隊 AI 分析: {practice_record_id}")
                return existing_queue
        
        # 創建新的排隊記錄
        queue_record = AIAnalysisQueue(
            practice_record_id=practice_record_id,
            priority=priority,
            status=AIAnalysisQueueStatus.PENDING,
            estimated_duration=self.default_estimated_duration
        )
        
        session.add(queue_record)
        
        # 更新練習記錄狀態
        practice_record.practice_status = PracticeStatus.AI_QUEUED
        practice_record.updated_at = datetime.now()
        session.add(practice_record)
        
        session.commit()
        session.refresh(queue_record)
        
        logger.info(f"添加到 AI 分析排隊: {practice_record_id}, 優先級: {priority}")
        
        return queue_record
    
    async def start_processing(
        self,
        queue_id: uuid.UUID,
        session: Session
    ) -> AIAnalysisQueue:
        """
        開始處理分析請求
        
        Args:
            queue_id: 排隊記錄ID
            session: 資料庫會話
            
        Returns:
            更新後的排隊記錄
        """
        queue_record = session.get(AIAnalysisQueue, queue_id)
        if not queue_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="排隊記錄不存在"
            )
        
        # 更新狀態為處理中
        queue_record.status = AIAnalysisQueueStatus.PROCESSING
        queue_record.started_at = datetime.now()
        queue_record.updated_at = datetime.now()
        
        # 更新對應的練習記錄狀態
        practice_record = session.get(PracticeRecord, queue_record.practice_record_id)
        if practice_record:
            practice_record.practice_status = PracticeStatus.AI_PROCESSING
            practice_record.updated_at = datetime.now()
            session.add(practice_record)
        
        session.add(queue_record)
        session.commit()
        session.refresh(queue_record)
        
        logger.info(f"開始處理 AI 分析: {queue_record.queue_id}")
        
        return queue_record
    
    async def mark_completed(
        self,
        queue_id: uuid.UUID,
        session: Session,
        processing_time: Optional[float] = None
    ) -> AIAnalysisQueue:
        """
        標記 AI 分析為完成
        
        Args:
            queue_id: 排隊記錄ID
            session: 資料庫會話
            processing_time: 實際處理時間（秒）
            
        Returns:
            更新後的排隊記錄
            
        Raises:
            HTTPException: 當排隊記錄不存在時
        """
        queue_record = session.get(AIAnalysisQueue, queue_id)
        if not queue_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="排隊記錄不存在"
            )
        
        # 更新排隊記錄
        queue_record.status = AIAnalysisQueueStatus.COMPLETED
        queue_record.completed_at = datetime.now()
        queue_record.updated_at = datetime.now()
        
        if processing_time:
            queue_record.actual_duration = int(processing_time)
        elif queue_record.started_at:
            duration = (datetime.now() - queue_record.started_at).total_seconds()
            queue_record.actual_duration = int(duration)
        
        # 更新練習記錄狀態
        practice_record = session.get(PracticeRecord, queue_record.practice_record_id)
        if practice_record:
            practice_record.practice_status = PracticeStatus.AI_ANALYZED
            practice_record.updated_at = datetime.now()
            session.add(practice_record)
        
        session.add(queue_record)
        session.commit()
        session.refresh(queue_record)
        
        logger.info(f"AI 分析完成: {queue_id}")
        
        return queue_record
    
    async def mark_failed(
        self,
        queue_id: uuid.UUID,
        error_message: str,
        session: Session,
        should_retry: bool = True
    ) -> AIAnalysisQueue:
        """
        標記 AI 分析為失敗
        
        Args:
            queue_id: 排隊記錄ID
            error_message: 錯誤訊息
            session: 資料庫會話
            should_retry: 是否應該重試
            
        Returns:
            更新後的排隊記錄
            
        Raises:
            HTTPException: 當排隊記錄不存在時
        """
        queue_record = session.get(AIAnalysisQueue, queue_id)
        if not queue_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="排隊記錄不存在"
            )
        
        queue_record.error_message = error_message
        queue_record.updated_at = datetime.now()
        
        if should_retry and queue_record.retry_count < queue_record.max_retries:
            # 重試：回到待處理狀態
            queue_record.status = AIAnalysisQueueStatus.PENDING
            queue_record.retry_count += 1
            queue_record.worker_id = None
            queue_record.started_at = None
            queue_record.queued_at = datetime.now()  # 重新排隊
            
            # 重設練習記錄狀態
            practice_record = session.get(PracticeRecord, queue_record.practice_record_id)
            if practice_record:
                practice_record.practice_status = PracticeStatus.AI_QUEUED
                practice_record.updated_at = datetime.now()
                session.add(practice_record)
            
            logger.warning(f"AI 分析失敗，準備重試: {queue_id}, 重試次數: {queue_record.retry_count}")
        else:
            # 達到最大重試次數，標記為失敗
            queue_record.status = AIAnalysisQueueStatus.FAILED
            queue_record.completed_at = datetime.now()
            
            # 重設練習記錄狀態為已完成，等待人工分析
            practice_record = session.get(PracticeRecord, queue_record.practice_record_id)
            if practice_record:
                practice_record.practice_status = PracticeStatus.COMPLETED
                practice_record.updated_at = datetime.now()
                session.add(practice_record)
            
            logger.error(f"AI 分析最終失敗: {queue_id}, 錯誤: {error_message}")
        
        session.add(queue_record)
        session.commit()
        session.refresh(queue_record)
        
        return queue_record
    
    async def cancel_analysis(
        self,
        queue_id: uuid.UUID,
        session: Session
    ) -> AIAnalysisQueue:
        """
        取消 AI 分析
        
        Args:
            queue_id: 排隊記錄ID
            session: 資料庫會話
            
        Returns:
            更新後的排隊記錄
            
        Raises:
            HTTPException: 當排隊記錄不存在或無法取消時
        """
        queue_record = session.get(AIAnalysisQueue, queue_id)
        if not queue_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="排隊記錄不存在"
            )
        
        if queue_record.status not in [AIAnalysisQueueStatus.PENDING, AIAnalysisQueueStatus.PROCESSING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無法取消已完成或失敗的分析"
            )
        
        queue_record.status = AIAnalysisQueueStatus.CANCELLED
        queue_record.completed_at = datetime.now()
        queue_record.updated_at = datetime.now()
        
        # 重設練習記錄狀態
        practice_record = session.get(PracticeRecord, queue_record.practice_record_id)
        if practice_record:
            practice_record.practice_status = PracticeStatus.COMPLETED
            practice_record.updated_at = datetime.now()
            session.add(practice_record)
        
        session.add(queue_record)
        session.commit()
        session.refresh(queue_record)
        
        logger.info(f"取消 AI 分析: {queue_id}")
        
        return queue_record
    
    async def get_queue_status(
        self,
        session: Session
    ) -> QueueStatusResponse:
        """
        取得排隊狀態總覽
        
        Args:
            session: 資料庫會話
            
        Returns:
            排隊狀態回應
        """
        # 統計各狀態的數量
        pending_count = session.exec(
            select(func.count(AIAnalysisQueue.queue_id)).where(
                AIAnalysisQueue.status == AIAnalysisQueueStatus.PENDING
            )
        ).one()
        
        processing_count = session.exec(
            select(func.count(AIAnalysisQueue.queue_id)).where(
                AIAnalysisQueue.status == AIAnalysisQueueStatus.PROCESSING
            )
        ).one()
        
        # 計算平均等待時間
        avg_processing_time = session.exec(
            select(func.avg(AIAnalysisQueue.actual_duration)).where(
                and_(
                    AIAnalysisQueue.status == AIAnalysisQueueStatus.COMPLETED,
                    AIAnalysisQueue.actual_duration.isnot(None)
                )
            )
        ).one()
        
        # 計算平均等待時間（基於最近完成的任務）
        recent_completed = session.exec(
            select(AIAnalysisQueue.actual_duration).where(
                and_(
                    AIAnalysisQueue.status == AIAnalysisQueueStatus.COMPLETED,
                    AIAnalysisQueue.actual_duration.isnot(None),
                    AIAnalysisQueue.completed_at >= datetime.now() - timedelta(hours=24)
                )
            ).order_by(desc(AIAnalysisQueue.completed_at)).limit(10)
        ).all()
        
        estimated_processing_time = int(avg_processing_time) if avg_processing_time else self.default_estimated_duration
        
        # 計算平均等待時間
        if recent_completed:
            avg_recent_time = sum(recent_completed) / len(recent_completed)
            estimated_wait_time = int(avg_recent_time * pending_count / max(self.max_concurrent_processing, 1))
        else:
            estimated_wait_time = int(estimated_processing_time * pending_count / max(self.max_concurrent_processing, 1))
        
        # 判斷排隊健康狀態
        if pending_count <= 5:
            queue_health = "healthy"
        elif pending_count <= 20:
            queue_health = "busy"
        else:
            queue_health = "overloaded"
        
        return QueueStatusResponse(
            total_pending=pending_count,
            total_processing=processing_count,
            average_wait_time=estimated_wait_time,
            estimated_processing_time=estimated_processing_time,
            queue_health=queue_health
        )
    
    async def get_user_queue_status(
        self,
        user_id: uuid.UUID,
        session: Session
    ) -> UserQueueStatusResponse:
        """
        取得用戶的排隊狀態
        
        Args:
            user_id: 用戶ID
            session: 資料庫會話
            
        Returns:
            用戶排隊狀態回應
        """
        # 查詢用戶的排隊記錄
        statement = (
            select(AIAnalysisQueue, PracticeRecord)
            .join(PracticeRecord, AIAnalysisQueue.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisQueue.status.in_([AIAnalysisQueueStatus.PENDING, AIAnalysisQueueStatus.PROCESSING])
                )
            )
            .order_by(asc(AIAnalysisQueue.queued_at))
        )
        
        results = session.exec(statement).all()
        
        pending_analyses = []
        processing_analyses = []
        
        for queue_record, practice_record in results:
            # 計算排隊位置
            position = await self._calculate_queue_position(queue_record, session)
            
            # 計算預估等待時間
            estimated_wait = await self._calculate_estimated_wait_time(queue_record, session)
            
            queue_response = AIAnalysisQueueResponse(
                queue_id=queue_record.queue_id,
                practice_record_id=queue_record.practice_record_id,
                priority=queue_record.priority,
                status=queue_record.status,
                queued_at=queue_record.queued_at,
                started_at=queue_record.started_at,
                completed_at=queue_record.completed_at,
                estimated_duration=queue_record.estimated_duration,
                actual_duration=queue_record.actual_duration,
                position_in_queue=position,
                estimated_wait_time=estimated_wait,
                error_message=queue_record.error_message,
                retry_count=queue_record.retry_count,
                created_at=queue_record.created_at,
                updated_at=queue_record.updated_at
            )
            
            if queue_record.status == AIAnalysisQueueStatus.PENDING:
                pending_analyses.append(queue_response)
            elif queue_record.status == AIAnalysisQueueStatus.PROCESSING:
                processing_analyses.append(queue_response)
        
        # 計算下一個預估完成時間
        next_completion = None
        if pending_analyses:
            first_pending = pending_analyses[0]
            if first_pending.estimated_wait_time:
                next_completion = datetime.now() + timedelta(seconds=first_pending.estimated_wait_time)
        
        return UserQueueStatusResponse(
            user_id=user_id,
            pending_analyses=pending_analyses,
            processing_analyses=processing_analyses,
            total_pending=len(pending_analyses),
            total_processing=len(processing_analyses),
            next_estimated_completion=next_completion
        )
    
    async def _calculate_queue_position(
        self,
        queue_record: AIAnalysisQueue,
        session: Session
    ) -> Optional[int]:
        """
        計算排隊位置
        
        Args:
            queue_record: 排隊記錄
            session: 資料庫會話
            
        Returns:
            排隊位置（1-based）
        """
        if queue_record.status != AIAnalysisQueueStatus.PENDING:
            return None
        
        # 計算在此記錄之前的待處理記錄數
        count = session.exec(
            select(func.count(AIAnalysisQueue.queue_id)).where(
                and_(
                    AIAnalysisQueue.status == AIAnalysisQueueStatus.PENDING,
                    or_(
                        func.case(
                            (AIAnalysisQueue.priority == AIAnalysisPriority.URGENT, 1),
                            (AIAnalysisQueue.priority == AIAnalysisPriority.HIGH, 2),
                            (AIAnalysisQueue.priority == AIAnalysisPriority.NORMAL, 3),
                            (AIAnalysisQueue.priority == AIAnalysisPriority.LOW, 4),
                            else_=5
                        ) < func.case(
                            (queue_record.priority == AIAnalysisPriority.URGENT, 1),
                            (queue_record.priority == AIAnalysisPriority.HIGH, 2),
                            (queue_record.priority == AIAnalysisPriority.NORMAL, 3),
                            (queue_record.priority == AIAnalysisPriority.LOW, 4),
                            else_=5
                        ),
                        and_(
                            func.case(
                                (AIAnalysisQueue.priority == AIAnalysisPriority.URGENT, 1),
                                (AIAnalysisQueue.priority == AIAnalysisPriority.HIGH, 2),
                                (AIAnalysisQueue.priority == AIAnalysisPriority.NORMAL, 3),
                                (AIAnalysisQueue.priority == AIAnalysisPriority.LOW, 4),
                                else_=5
                            ) == func.case(
                                (queue_record.priority == AIAnalysisPriority.URGENT, 1),
                                (queue_record.priority == AIAnalysisPriority.HIGH, 2),
                                (queue_record.priority == AIAnalysisPriority.NORMAL, 3),
                                (queue_record.priority == AIAnalysisPriority.LOW, 4),
                                else_=5
                            ),
                            AIAnalysisQueue.queued_at < queue_record.queued_at
                        )
                    )
                )
            )
        ).one()
        
        return count + 1
    
    async def _calculate_estimated_wait_time(
        self,
        queue_record: AIAnalysisQueue,
        session: Session
    ) -> Optional[int]:
        """
        計算預估等待時間
        
        Args:
            queue_record: 排隊記錄
            session: Resource 會話
            
        Returns:
            預估等待時間（秒）
        """
        if queue_record.status != AIAnalysisQueueStatus.PENDING:
            return None
        
        position = await self._calculate_queue_position(queue_record, session)
        if not position:
            return None
        
        # 取得平均處理時間
        avg_processing_time = session.exec(
            select(func.avg(AIAnalysisQueue.actual_duration)).where(
                and_(
                    AIAnalysisQueue.status == AIAnalysisQueueStatus.COMPLETED,
                    AIAnalysisQueue.actual_duration.isnot(None),
                    AIAnalysisQueue.completed_at >= datetime.now() - timedelta(hours=24)
                )
            )
        ).one()
        
        processing_time = int(avg_processing_time) if avg_processing_time else self.default_estimated_duration
        
        # 計算等待時間：(排隊位置 - 1) * 平均處理時間 / 並行處理數
        wait_time = max(0, (position - 1) * processing_time // self.max_concurrent_processing)
        
        return wait_time


# 單例實例
ai_queue_manager = AIQueueManager()
"""AI 分析任務手動觸發路由

提供手動觸發 AI 分析任務的端點，主要用於：
1. 對先前沒有 AI 分析任務的完成練習會話進行分析
2. 為選擇跳過自動 AI 分析的用戶提供手動觸發選項
"""

import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_

from src.shared.database.database import get_session
from src.auth.services.permission_service import get_current_user
from src.auth.models import User
from src.practice.models import PracticeSession, PracticeSessionStatus
from src.ai_analysis.models import AIAnalysisTask
from src.ai_analysis.services.ai_analysis_service import (
    create_analysis_tasks_for_session,
    AIAnalysisServiceError
)
from src.ai_analysis.schemas import (
    AIAnalysisTriggerRequest,
    AIAnalysisTriggerResponse
)

# 設定日誌
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/ai-analysis',
    tags=['ai-analysis']
)


@router.post(
    "/trigger/{practice_session_id}",
    response_model=AIAnalysisTriggerResponse,
    summary="手動觸發 AI 分析任務",
    description="""
    為指定的練習會話手動觸發 AI 分析任務。
    
    主要用途：
    - 為先前沒有 AI 分析任務的已完成練習會話進行分析
    - 為選擇跳過自動 AI 分析的用戶提供手動觸發機會
    
    注意事項：
    - 僅能對已完成的練習會話觸發分析
    - 僅能對屬於當前用戶的會話進行操作  
    - 如果會話已有 AI 分析任務，將回傳錯誤
    """
)
async def trigger_ai_analysis_router(
    practice_session_id: uuid.UUID,
    trigger_request: AIAnalysisTriggerRequest,
    db_session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> AIAnalysisTriggerResponse:
    """手動觸發 AI 分析任務"""
    
    try:
        # 1. 驗證練習會話存在且屬於當前用戶
        practice_session = db_session.get(PracticeSession, practice_session_id)
        if not practice_session:
            logger.warning(f"練習會話不存在: {practice_session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到指定的練習會話"
            )
            
        if practice_session.user_id != current_user.user_id:
            logger.warning(
                f"用戶 {current_user.user_id} 嘗試存取不屬於自己的會話 {practice_session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權限存取此練習會話"
            )
        
        # 2. 檢查會話狀態是否為已完成
        if practice_session.session_status != PracticeSessionStatus.COMPLETED:
            logger.warning(f"嘗試對未完成的會話觸發 AI 分析: {practice_session_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能對已完成的練習會話觸發 AI 分析"
            )
        
        # 3. 檢查是否已有 AI 分析任務（避免重複觸發）
        # 查詢該用戶的所有AI分析任務，然後在Python中過濾
        existing_tasks_stmt = select(AIAnalysisTask).where(
            AIAnalysisTask.user_id == current_user.user_id
        )
        existing_tasks = db_session.exec(existing_tasks_stmt).all()
        
        # 檢查是否有關聯到此會話的任務
        session_tasks = []
        for task in existing_tasks:
            if (task.task_params and 
                task.task_params.get("practice_session_id") == str(practice_session_id)):
                session_tasks.append(task)
        
        if session_tasks:
            logger.warning(f"會話 {practice_session_id} 已有 {len(session_tasks)} 個 AI 分析任務")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"此練習會話已有 {len(session_tasks)} 個 AI 分析任務，無需重複觸發"
            )
        
        # 4. 觸發 AI 分析任務
        logger.info(f"開始為會話 {practice_session_id} 手動觸發 AI 分析任務")
        
        created_tasks = await create_analysis_tasks_for_session(
            practice_session_id=practice_session_id,
            user_id=current_user.user_id,
            db_session=db_session
        )
        
        if not created_tasks:
            logger.warning(f"會話 {practice_session_id} 沒有可分析的音訊記錄")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此練習會話沒有可分析的音訊記錄"
            )
        
        # 5. 回傳結果
        task_ids = [task.task_id for task in created_tasks]
        
        logger.info(f"成功為會話 {practice_session_id} 建立 {len(created_tasks)} 個 AI 分析任務")
        
        return AIAnalysisTriggerResponse(
            message=f"成功觸發 {len(created_tasks)} 個 AI 分析任務",
            practice_session_id=practice_session_id,
            tasks_created=len(created_tasks),
            task_ids=task_ids
        )
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
        
    except AIAnalysisServiceError as e:
        logger.error(f"AI 分析服務錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 分析服務錯誤: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"觸發 AI 分析任務時發生未預期錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="觸發 AI 分析任務時發生系統錯誤"
        )
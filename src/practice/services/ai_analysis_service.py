"""
AI 分析服務
處理語音分析的核心邏輯，包括與 AI 模型的交互和結果處理
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status

from src.course.models import (
    PracticeRecord, AIAnalysisQueue, AIAnalysisResult,
    AIAnalysisQueueStatus, PracticeStatus
)
from src.practice.ai_schemas import (
    AIAnalysisResultCreate,
    AIAnalysisResultResponse,
    AIAnalysisStatsResponse
)
from src.practice.services.ai_queue_service import ai_queue_manager

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """AI 分析服務"""
    
    def __init__(self):
        self.model_version = "VocalBorn-AI-v1.0.0"  # 當前 AI 模型版本
        self.default_timeout = 300  # 預設超時時間（秒）
        self.confidence_threshold = 0.7  # 置信度閾值
    
    async def analyze_audio(
        self,
        practice_record_id: uuid.UUID,
        audio_file_path: str,
        session: Session
    ) -> AIAnalysisResult:
        """
        分析音訊檔案（主要分析邏輯）
        
        Args:
            practice_record_id: 練習記錄ID
            audio_file_path: 音訊檔案路徑
            session: 資料庫會話
            
        Returns:
            AI 分析結果
            
        Raises:
            HTTPException: 當分析失敗時
        """
        # 取得排隊記錄
        queue_record = session.exec(
            select(AIAnalysisQueue).where(
                AIAnalysisQueue.practice_record_id == practice_record_id
            )
        ).first()
        
        if not queue_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到對應的排隊記錄"
            )
        
        try:
            start_time = datetime.now()
            
            # 開始處理
            await ai_queue_manager.start_processing(queue_record.queue_id, session)
            
            # 執行 AI 分析（這裡是框架，實際 AI 服務需要替換）
            analysis_result = await self._perform_ai_analysis(
                audio_file_path,
                practice_record_id,
                session
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # 創建分析結果記錄
            ai_result = AIAnalysisResult(
                queue_id=queue_record.queue_id,
                practice_record_id=practice_record_id,
                ai_model_version=self.model_version,
                pronunciation_accuracy=analysis_result.get("pronunciation_accuracy"),
                fluency_score=analysis_result.get("fluency_score"),
                rhythm_score=analysis_result.get("rhythm_score"),
                tone_score=analysis_result.get("tone_score"),
                overall_score=analysis_result.get("overall_score"),
                detailed_analysis=json.dumps(analysis_result.get("detailed_analysis", {})),
                phoneme_analysis=json.dumps(analysis_result.get("phoneme_analysis", {})),
                word_analysis=json.dumps(analysis_result.get("word_analysis", {})),
                ai_suggestions=analysis_result.get("ai_suggestions"),
                improvement_areas=json.dumps(analysis_result.get("improvement_areas", [])),
                confidence_score=analysis_result.get("confidence_score"),
                reliability_score=analysis_result.get("reliability_score"),
                processing_time=processing_time
            )
            
            session.add(ai_result)
            
            # 標記排隊記錄為完成
            await ai_queue_manager.mark_completed(
                queue_record.queue_id,
                session,
                processing_time
            )
            
            session.commit()
            session.refresh(ai_result)
            
            logger.info(f"AI 分析完成: {practice_record_id}")
            
            return ai_result
            
        except Exception as e:
            logger.error(f"AI 分析失敗: {practice_record_id}, 錯誤: {str(e)}")
            
            # 標記排隊記錄為失敗
            await ai_queue_manager.mark_failed(
                queue_record.queue_id,
                str(e),
                session
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI 分析失敗: {str(e)}"
            )
    
    async def _perform_ai_analysis(
        self,
        audio_file_path: str,
        practice_record_id: uuid.UUID,
        session: Session
    ) -> Dict[str, Any]:
        """
        執行實際的 AI 分析（框架方法，需要根據實際 AI 服務實現）
        
        Args:
            audio_file_path: 音訊檔案路徑
            practice_record_id: 練習記錄ID
            session: 資料庫會話
            
        Returns:
            分析結果字典
        """
        # 取得練習記錄和句子資訊
        practice_record = session.get(PracticeRecord, practice_record_id)
        if not practice_record:
            raise ValueError("練習記錄不存在")
        
        # 取得句子內容
        sentence = practice_record.sentence
        target_text = sentence.content if sentence else ""
        
        # TODO: 這裡需要替換為實際的 AI 分析邏輯
        # 例如：調用語音識別 API、發音評估 API 等
        
        # 模擬 AI 分析結果（實際使用時需要替換）
        mock_result = await self._mock_ai_analysis(
            audio_file_path,
            target_text,
            practice_record.audio_duration or 0
        )
        
        return mock_result
    
    async def _mock_ai_analysis(
        self,
        audio_file_path: str,
        target_text: str,
        audio_duration: float
    ) -> Dict[str, Any]:
        """
        模擬 AI 分析結果（開發階段使用）
        
        Args:
            audio_file_path: 音訊檔案路徑
            target_text: 目標文字
            audio_duration: 音訊時長
            
        Returns:
            模擬的分析結果
        """
        import random
        import time
        
        # 模擬處理時間
        await asyncio.sleep(random.uniform(2, 5))
        
        # 模擬分析結果
        pronunciation_accuracy = random.uniform(70, 95)
        fluency_score = random.uniform(65, 90)
        rhythm_score = random.uniform(60, 88)
        tone_score = random.uniform(68, 92)
        
        overall_score = (pronunciation_accuracy + fluency_score + rhythm_score + tone_score) / 4
        
        # 模擬詳細分析
        detailed_analysis = {
            "speech_rate": random.uniform(120, 180),  # 語速（詞/分鐘）
            "pause_count": random.randint(1, 5),      # 停頓次數
            "volume_level": random.uniform(0.6, 0.9),  # 音量水平
            "clarity_score": random.uniform(0.7, 0.95)  # 清晰度
        }
        
        # 模擬音素分析
        phoneme_analysis = {
            "total_phonemes": len(target_text.replace(" ", "")),
            "correct_phonemes": random.randint(
                int(len(target_text.replace(" ", "")) * 0.7),
                len(target_text.replace(" ", ""))
            ),
            "problem_phonemes": ["zh", "ch", "sh"] if random.random() > 0.5 else []
        }
        
        # 模擬詞彙分析
        words = target_text.split()
        word_analysis = {
            "total_words": len(words),
            "correct_words": random.randint(max(1, int(len(words) * 0.8)), len(words)),
            "difficult_words": random.sample(words, min(2, len(words))) if len(words) > 1 else []
        }
        
        # 生成建議
        suggestions = []
        improvement_areas = []
        
        if pronunciation_accuracy < 80:
            suggestions.append("建議多練習發音準確性")
            improvement_areas.append("發音準確性")
        
        if fluency_score < 75:
            suggestions.append("建議增強語音流暢度")
            improvement_areas.append("語音流暢度")
        
        if rhythm_score < 70:
            suggestions.append("注意語音節奏和停頓")
            improvement_areas.append("語音節奏")
        
        if tone_score < 75:
            suggestions.append("改善語調變化")
            improvement_areas.append("語調變化")
        
        if not suggestions:
            suggestions.append("整體表現良好，繼續保持")
        
        return {
            "pronunciation_accuracy": round(pronunciation_accuracy, 1),
            "fluency_score": round(fluency_score, 1),
            "rhythm_score": round(rhythm_score, 1),
            "tone_score": round(tone_score, 1),
            "overall_score": round(overall_score, 1),
            "detailed_analysis": detailed_analysis,
            "phoneme_analysis": phoneme_analysis,
            "word_analysis": word_analysis,
            "ai_suggestions": " ".join(suggestions),
            "improvement_areas": improvement_areas,
            "confidence_score": random.uniform(85, 98),
            "reliability_score": random.uniform(82, 95)
        }
    
    async def get_analysis_result(
        self,
        practice_record_id: uuid.UUID,
        session: Session
    ) -> Optional[AIAnalysisResultResponse]:
        """
        取得 AI 分析結果
        
        Args:
            practice_record_id: 練習記錄ID
            session: 資料庫會話
            
        Returns:
            AI 分析結果回應，如果不存在則返回 None
        """
        ai_result = session.exec(
            select(AIAnalysisResult).where(
                AIAnalysisResult.practice_record_id == practice_record_id
            )
        ).first()
        
        if not ai_result:
            return None
        
        # 解析 JSON 字段
        detailed_analysis = None
        phoneme_analysis = None
        word_analysis = None
        improvement_areas = None
        
        try:
            if ai_result.detailed_analysis:
                detailed_analysis = json.loads(ai_result.detailed_analysis)
            if ai_result.phoneme_analysis:
                phoneme_analysis = json.loads(ai_result.phoneme_analysis)
            if ai_result.word_analysis:
                word_analysis = json.loads(ai_result.word_analysis)
            if ai_result.improvement_areas:
                improvement_areas = json.loads(ai_result.improvement_areas)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失敗: {e}")
        
        return AIAnalysisResultResponse(
            result_id=ai_result.result_id,
            queue_id=ai_result.queue_id,
            practice_record_id=ai_result.practice_record_id,
            ai_model_version=ai_result.ai_model_version,
            pronunciation_accuracy=ai_result.pronunciation_accuracy,
            fluency_score=ai_result.fluency_score,
            rhythm_score=ai_result.rhythm_score,
            tone_score=ai_result.tone_score,
            overall_score=ai_result.overall_score,
            detailed_analysis=detailed_analysis,
            phoneme_analysis=phoneme_analysis,
            word_analysis=word_analysis,
            ai_suggestions=ai_result.ai_suggestions,
            improvement_areas=improvement_areas,
            confidence_score=ai_result.confidence_score,
            reliability_score=ai_result.reliability_score,
            processing_time=ai_result.processing_time,
            created_at=ai_result.created_at,
            updated_at=ai_result.updated_at
        )
    
    async def get_user_ai_stats(
        self,
        user_id: uuid.UUID,
        session: Session
    ) -> AIAnalysisStatsResponse:
        """
        取得用戶的 AI 分析統計
        
        Args:
            user_id: 用戶ID
            session: 資料庫會話
            
        Returns:
            AI 分析統計回應
        """
        from sqlmodel import func
        
        # 查詢用戶的 AI 分析記錄
        base_query = (
            select(AIAnalysisResult)
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(PracticeRecord.user_id == user_id)
        )
        
        # 總分析數
        total_analyses = session.exec(
            select(func.count(AIAnalysisResult.result_id))
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(PracticeRecord.user_id == user_id)
        ).one()
        
        # 成功分析數（基於置信度）
        successful_analyses = session.exec(
            select(func.count(AIAnalysisResult.result_id))
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisResult.confidence_score >= self.confidence_threshold * 100
                )
            )
        ).one()
        
        # 失敗分析數
        failed_analyses = session.exec(
            select(func.count(AIAnalysisQueue.queue_id))
            .join(PracticeRecord, AIAnalysisQueue.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisQueue.status == AIAnalysisQueueStatus.FAILED
                )
            )
        ).one()
        
        # 平均處理時間
        avg_processing_time = session.exec(
            select(func.avg(AIAnalysisResult.processing_time))
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisResult.processing_time.isnot(None)
                )
            )
        ).one()
        
        # 平均準確度分數
        avg_accuracy = session.exec(
            select(func.avg(AIAnalysisResult.pronunciation_accuracy))
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisResult.pronunciation_accuracy.isnot(None)
                )
            )
        ).one()
        
        # 平均整體分數
        avg_overall = session.exec(
            select(func.avg(AIAnalysisResult.overall_score))
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisResult.overall_score.isnot(None)
                )
            )
        ).one()
        
        # 最常見的改進領域
        improvement_areas_raw = session.exec(
            select(AIAnalysisResult.improvement_areas)
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisResult.improvement_areas.isnot(None)
                )
            )
        ).all()
        
        # 統計改進領域
        area_counts = {}
        for areas_json in improvement_areas_raw:
            try:
                if areas_json:
                    areas = json.loads(areas_json)
                    for area in areas:
                        area_counts[area] = area_counts.get(area, 0) + 1
            except json.JSONDecodeError:
                continue
        
        # 取得最常見的改進領域
        most_common_improvements = sorted(
            area_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        most_common_improvements = [area for area, count in most_common_improvements]
        
        # 本週分析數
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        analyses_this_week = session.exec(
            select(func.count(AIAnalysisResult.result_id))
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisResult.created_at >= week_ago
                )
            )
        ).one()
        
        # 本月分析數
        month_ago = datetime.now() - timedelta(days=30)
        analyses_this_month = session.exec(
            select(func.count(AIAnalysisResult.result_id))
            .join(PracticeRecord, AIAnalysisResult.practice_record_id == PracticeRecord.practice_record_id)
            .where(
                and_(
                    PracticeRecord.user_id == user_id,
                    AIAnalysisResult.created_at >= month_ago
                )
            )
        ).one()
        
        return AIAnalysisStatsResponse(
            user_id=user_id,
            total_ai_analyses=total_analyses,
            successful_analyses=successful_analyses,
            failed_analyses=failed_analyses,
            average_processing_time=avg_processing_time,
            average_accuracy_score=avg_accuracy,
            average_overall_score=avg_overall,
            most_common_improvements=most_common_improvements,
            analyses_this_week=analyses_this_week,
            analyses_this_month=analyses_this_month
        )
    
    async def reprocess_analysis(
        self,
        practice_record_id: uuid.UUID,
        session: Session
    ) -> AIAnalysisQueue:
        """
        重新處理 AI 分析
        
        Args:
            practice_record_id: 練習記錄ID
            session: 資料庫會話
            
        Returns:
            新的排隊記錄
        """
        # 刪除現有的分析結果
        existing_result = session.exec(
            select(AIAnalysisResult).where(
                AIAnalysisResult.practice_record_id == practice_record_id
            )
        ).first()
        
        if existing_result:
            session.delete(existing_result)
        
        # 重新加入排隊
        from src.course.models import AIAnalysisPriority
        
        queue_record = await ai_queue_manager.add_to_queue(
            practice_record_id,
            AIAnalysisPriority.HIGH,  # 重新處理使用高優先級
            session
        )
        
        logger.info(f"重新處理 AI 分析: {practice_record_id}")
        
        return queue_record
    
    async def process_analysis_directly(
        self,
        practice_record_id: uuid.UUID,
        session: Session
    ) -> Dict[str, Any]:
        """
        直接處理 AI 分析（同步）
        
        Args:
            practice_record_id: 練習記錄ID
            session: 資料庫會話
            
        Returns:
            分析結果
        """
        try:
            # 先加入排隊（用於記錄和狀態追蹤）
            from src.course.models import AIAnalysisPriority
            queue_record = await ai_queue_manager.add_to_queue(
                practice_record_id,
                AIAnalysisPriority.NORMAL,
                session
            )
            
            # 直接執行分析
            practice_record = session.get(PracticeRecord, practice_record_id)
            if not practice_record:
                return {
                    "success": False,
                    "error": "練習記錄不存在",
                    "practice_record_id": str(practice_record_id)
                }
            
            # 執行 AI 分析
            ai_result = await self.analyze_audio(
                practice_record_id,
                practice_record.audio_path or "",
                session
            )
            
            logger.info(f"AI 分析完成: {practice_record_id}, 結果 ID: {ai_result.result_id}")
            
            return {
                "success": True,
                "result_id": str(ai_result.result_id),
                "practice_record_id": str(practice_record_id),
                "queue_id": str(queue_record.queue_id),
                "overall_score": ai_result.overall_score,
                "processing_time": ai_result.processing_time
            }
            
        except Exception as e:
            logger.error(f"AI 分析失敗: {practice_record_id}, 錯誤: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "practice_record_id": str(practice_record_id)
            }


# 需要導入 asyncio
import asyncio

# 單例實例
ai_analysis_service = AIAnalysisService()
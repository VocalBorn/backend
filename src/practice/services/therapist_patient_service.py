"""
治療師患者管理服務

此模組提供治療師查詢和管理患者練習相關的服務功能。
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict
from uuid import UUID
from sqlmodel import Session, select, and_, or_, func, case
from sqlalchemy.orm import selectinload

from src.auth.models import User, UserRole
from src.course.models import Chapter, Sentence
from src.practice.models import PracticeSession, PracticeRecord, PracticeFeedback, PracticeRecordStatus, PracticeSessionStatus, PracticeSessionFeedback
from src.ai_analysis.models import AIAnalysisTask, AIAnalysisResult, TaskStatus
from src.practice.schemas import (
    TherapistPatientOverviewResponse,
    TherapistPatientsOverviewListResponse,
    PatientSessionProgress,
    PatientPracticeRecordResponse,
    PatientPracticeListResponse,
    PracticeSessionGroup,
    PatientPracticeSessionsResponse
)
from src.therapist.models import TherapistClient
from src.storage.practice_recording_service import PracticeRecordingService


async def get_patient_avg_accuracy_last_30_days(
    patient_id: UUID,
    session: Session
) -> Optional[float]:
    """
    計算患者最近30天的AI分析平均準確度

    Args:
        patient_id: 患者ID
        session: 資料庫會話

    Returns:
        Optional[float]: 平均準確度（0-100分數格式），如果沒有資料則回傳None
    """
    from datetime import datetime, timedelta

    # 計算30天前的日期
    thirty_days_ago = datetime.now() - timedelta(days=30)

    try:
        # 查詢最近30天患者的練習會話及其相關AI分析結果
        # 1. 先找出最近30天的練習會話
        practice_sessions_query = (
            select(PracticeSession.practice_session_id)
            .where(
                and_(
                    PracticeSession.user_id == patient_id,
                    PracticeSession.session_status == PracticeSessionStatus.COMPLETED,
                    PracticeSession.begin_time >= thirty_days_ago
                )
            )
        )

        practice_session_ids = session.exec(practice_sessions_query).all()

        if not practice_session_ids:
            return None

        # 2. 找出這些會話的練習記錄
        practice_records_query = (
            select(PracticeRecord.practice_record_id)
            .where(
                PracticeRecord.practice_session_id.in_(practice_session_ids)
            )
        )

        practice_record_ids = session.exec(practice_records_query).all()

        if not practice_record_ids:
            return None

        # 3. 查詢相關的成功AI分析任務和結果
        ai_tasks_query = (
            select(AIAnalysisTask, AIAnalysisResult)
            .join(AIAnalysisResult, AIAnalysisTask.task_id == AIAnalysisResult.task_id)
            .where(
                and_(
                    AIAnalysisTask.user_id == patient_id,
                    AIAnalysisTask.status == TaskStatus.SUCCESS
                )
            )
        )

        ai_results = session.exec(ai_tasks_query).all()

        if not ai_results:
            return None

        # 4. 篩選與最近30天練習記錄相關的AI分析結果
        valid_accuracy_scores = []

        for task, result in ai_results:
            # 檢查task_params中的practice_record_id是否在我們的列表中
            if (task.task_params and
                task.task_params.get("practice_record_id")):
                try:
                    task_practice_record_id = UUID(task.task_params["practice_record_id"])
                    if task_practice_record_id in practice_record_ids:
                        # 從分析結果中提取index值（綜合評分指標）
                        analysis_data = result.analysis_result
                        if isinstance(analysis_data, dict) and "index" in analysis_data:
                            index_score = float(analysis_data["index"])
                            # 轉換為百分比格式
                            accuracy_percentage = index_score * 100
                            valid_accuracy_scores.append(accuracy_percentage)
                except (ValueError, TypeError, KeyError):
                    continue

        # 5. 計算平均準確度
        if valid_accuracy_scores:
            avg_accuracy = sum(valid_accuracy_scores) / len(valid_accuracy_scores)
            return round(avg_accuracy, 1)  # 保留一位小數

        return None

    except Exception as e:
        # 記錄錯誤但不中斷主要流程
        print(f"計算患者 {patient_id} 的AI分析平均準確度時發生錯誤: {e}")
        return None


async def get_therapist_patients_overview(
    therapist_id: UUID,
    session: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None
) -> TherapistPatientsOverviewListResponse:
    """
    取得治療師所有患者的練習會話進度概覽
    
    Args:
        therapist_id: 治療師ID
        session: 資料庫會話
        skip: 略過記錄數
        limit: 限制記錄數
        search: 患者姓名搜尋關鍵字
        
    Returns:
        TherapistPatientsOverviewListResponse: 患者概覽列表回應
    """
    # 取得患者基本資料
    base_query = (
        select(User)
        .join(TherapistClient, User.user_id == TherapistClient.client_id)
        .where(
            and_(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.is_active == True,
                User.role == UserRole.CLIENT
            )
        )
    )
    
    # 添加搜尋條件
    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.where(User.name.ilike(search_pattern))
    
    # 計算總數
    count_query = select(func.count()).select_from(base_query.subquery())
    total = session.exec(count_query).one()
    
    # 取得分頁資料
    patients = session.exec(
        base_query
        .offset(skip)
        .limit(limit)
        .order_by(User.name)
    ).all()
    
    overview_responses = []
    
    for patient in patients:
        # 取得患者的練習會話列表
        practice_sessions_query = (
            select(PracticeSession, Chapter)
            .join(Chapter, PracticeSession.chapter_id == Chapter.chapter_id)
            .where(
                and_(
                    PracticeSession.user_id == patient.user_id,
                    PracticeSession.session_status == PracticeSessionStatus.COMPLETED
                )
            )
            .order_by(PracticeSession.begin_time.desc())
        )
        
        session_results = session.exec(practice_sessions_query).all()
        
        session_progress = []
        sessions_pending_feedback = 0
        total_feedback_completed = 0
        
        # 直接使用資料庫中的 session_status，因為查詢已經篩選了 COMPLETED 狀態
        completed_sessions = len(session_results)
        
        for practice_session, chapter in session_results:
            # 統計該會話的練習記錄（保留語句統計以計算完成率）
            session_stats_query = (
                select(
                    func.count(PracticeRecord.practice_record_id).label("total_sentences"),
                    func.count(
                        case(
                            (PracticeRecord.record_status.in_([
                                PracticeRecordStatus.RECORDED,
                                PracticeRecordStatus.AI_ANALYZED,
                                PracticeRecordStatus.ANALYZED
                            ]), 1),
                            else_=None
                        )
                    ).label("completed_sentences")
                )
                .select_from(PracticeRecord)
                .where(PracticeRecord.practice_session_id == practice_session.practice_session_id)
            )
            
            stats_result = session.exec(session_stats_query).first()
            
            # 檢查該會話是否已有治療師回饋
            has_feedback = session.exec(
                select(func.count(PracticeSessionFeedback.session_feedback_id))
                .where(PracticeSessionFeedback.practice_session_id == practice_session.practice_session_id)
            ).one() > 0
            
            feedback_status = "completed" if has_feedback else "pending"
            
            if has_feedback:
                total_feedback_completed += 1
            else:
                sessions_pending_feedback += 1
            
            if stats_result:
                completion_rate = (
                    (stats_result.completed_sentences / stats_result.total_sentences * 100) 
                    if stats_result.total_sentences > 0 else 0.0
                )
                
                session_progress.append(
                    PatientSessionProgress(
                        practice_session_id=practice_session.practice_session_id,
                        chapter_id=chapter.chapter_id,
                        chapter_name=chapter.chapter_name,
                        session_status=practice_session.session_status.value,
                        begin_time=practice_session.begin_time,
                        end_time=practice_session.end_time,
                        total_duration=practice_session.total_duration,
                        total_sentences=stats_result.total_sentences,
                        completed_sentences=stats_result.completed_sentences,
                        completion_rate=completion_rate,
                        has_therapist_feedback=has_feedback,
                        feedback_status=feedback_status,
                        practice_date=practice_session.begin_time or practice_session.created_at
                    )
                )
        
        # 取得患者最後練習時間
        last_practice_date = session_results[0][0].begin_time if session_results else None

        # 計算患者最近30天AI分析平均準確度
        avg_accuracy_last_30_days = await get_patient_avg_accuracy_last_30_days(
            patient_id=patient.user_id,
            session=session
        )

        overview_responses.append(
            TherapistPatientOverviewResponse(
                patient_id=patient.user_id,
                patient_name=patient.name,
                last_practice_date=last_practice_date,
                total_practice_sessions=len(session_results),
                completed_practice_sessions=completed_sessions,
                session_progress=session_progress,
                sessions_pending_feedback=sessions_pending_feedback,
                total_feedback_completed=total_feedback_completed,
                avg_accuracy_last_30_days=avg_accuracy_last_30_days
            )
        )
    
    return TherapistPatientsOverviewListResponse(
        total=total,
        patients_overview=overview_responses
    )


async def get_patient_practice_sessions(
    patient_id: UUID,
    therapist_id: UUID,
    session: Session,
    practice_session_id: Optional[UUID] = None,
    pending_feedback_only: bool = False
) -> PatientPracticeSessionsResponse:
    """
    取得患者的練習會話記錄列表（按會話分組）
    
    Args:
        patient_id: 患者ID
        therapist_id: 治療師ID（用於權限檢查）
        session: 資料庫會話
        practice_session_id: 特定練習會話ID篩選（可選）
        pending_feedback_only: 只顯示待回饋的語句
        
    Returns:
        PatientPracticeSessionsResponse: 患者練習會話列表回應
    """
    # 權限檢查：確認治療師與患者的配對關係
    therapist_client_check = session.exec(
        select(TherapistClient)
        .where(
            and_(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.client_id == patient_id,
                TherapistClient.is_active == True
            )
        )
    ).first()
    
    if not therapist_client_check:
        raise ValueError("治療師無權查看此患者的練習記錄")
    
    # 取得患者資訊
    patient = session.exec(
        select(User).where(User.user_id == patient_id)
    ).first()
    
    if not patient:
        raise ValueError("找不到指定的患者")
    
    # 建立練習會話查詢條件
    session_conditions = [
        PracticeSession.user_id == patient_id,
        PracticeSession.session_status == PracticeSessionStatus.COMPLETED  # 只顯示已完成的練習會話
    ]
    
    # 如果指定了特定會話ID，添加篩選條件
    if practice_session_id:
        session_conditions.append(PracticeSession.practice_session_id == practice_session_id)
    
    # 查詢練習會話
    practice_sessions_query = (
        select(PracticeSession, Chapter)
        .join(Chapter, PracticeSession.chapter_id == Chapter.chapter_id)
        .where(and_(*session_conditions))
        .order_by(PracticeSession.begin_time.desc())
    )
    
    session_results = session.exec(practice_sessions_query).all()
    
    if not session_results:
        return PatientPracticeSessionsResponse(
            patient_info={
                "patient_id": str(patient.user_id),
                "patient_name": patient.name
            },
            total_sessions=0,
            practice_sessions=[]
        )
    
    # 初始化音訊服務
    audio_service = PracticeRecordingService()
    
    # 為每個會話組裝資料
    practice_session_groups = []
    
    for practice_session, chapter in session_results:
        # 建立練習記錄查詢條件
        record_conditions = [
            PracticeRecord.practice_session_id == practice_session.practice_session_id
        ]
        
        # 如果只要待回饋的語句，添加篩選條件
        if pending_feedback_only:
            record_conditions.extend([
                PracticeRecord.record_status == PracticeRecordStatus.RECORDED,
                ~select(PracticeFeedback.feedback_id).where(
                    PracticeFeedback.practice_record_id == PracticeRecord.practice_record_id
                ).exists()
            ])
        
        # 查詢該會話的練習記錄
        practice_records_query = (
            select(PracticeRecord, Sentence)
            .join(Sentence, PracticeRecord.sentence_id == Sentence.sentence_id)
            .where(and_(*record_conditions))
            .order_by(Sentence.start_time.asc().nullslast())
        )
        
        record_results = session.exec(practice_records_query).all()
        
        # 如果啟用了待回饋篩選且沒有找到任何記錄，跳過這個會話
        if pending_feedback_only and not record_results:
            continue
        
        # 建構練習記錄回應
        practice_record_responses = []
        pending_feedback_count = 0
        
        for practice_record, sentence in record_results:
            # 檢查是否有回饋
            has_feedback = session.exec(
                select(func.count(PracticeFeedback.feedback_id))
                .where(PracticeFeedback.practice_record_id == practice_record.practice_record_id)
            ).one() > 0
            
            if not has_feedback and practice_record.record_status == PracticeRecordStatus.RECORDED:
                pending_feedback_count += 1
            
            # 生成音訊播放URL（如果有音訊）
            audio_stream_url = None
            audio_stream_expires_at = None
            
            if practice_record.audio_path:
                try:
                    stream_url, expires_at = await audio_service.get_presigned_url(practice_record.audio_path)
                    audio_stream_url = stream_url
                    audio_stream_expires_at = expires_at
                except Exception:
                    # 音訊URL生成失敗時，優雅處理
                    pass
            
            practice_record_responses.append(
                PatientPracticeRecordResponse(
                    practice_record_id=practice_record.practice_record_id,
                    practice_session_id=practice_record.practice_session_id,
                    chapter_id=chapter.chapter_id,
                    chapter_name=chapter.chapter_name,
                    sentence_id=practice_record.sentence_id,
                    sentence_content=sentence.content,
                    sentence_name=sentence.sentence_name,
                    record_status=practice_record.record_status,
                    audio_path=practice_record.audio_path,
                    audio_duration=practice_record.audio_duration,
                    audio_stream_url=audio_stream_url,
                    audio_stream_expires_at=audio_stream_expires_at,
                    recorded_at=practice_record.recorded_at,
                    has_feedback=has_feedback
                )
            )
        
        # 建立會話分組
        practice_session_groups.append(
            PracticeSessionGroup(
                practice_session_id=practice_session.practice_session_id,
                chapter_id=chapter.chapter_id,
                chapter_name=chapter.chapter_name,
                session_status=practice_session.session_status.value,
                begin_time=practice_session.begin_time,
                end_time=practice_session.end_time,
                total_sentences=len(practice_record_responses),
                pending_feedback_count=pending_feedback_count,
                practice_records=practice_record_responses
            )
        )
    
    return PatientPracticeSessionsResponse(
        patient_info={
            "patient_id": str(patient.user_id),
            "patient_name": patient.name
        },
        total_sessions=len(practice_session_groups),
        practice_sessions=practice_session_groups
    )


async def get_patient_practice_records(
    patient_id: UUID,
    therapist_id: UUID,
    session: Session,
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    chapter_id: Optional[UUID] = None
) -> PatientPracticeListResponse:
    """
    取得患者的練習記錄列表（包含音訊播放功能）
    
    此函數保留作為向後相容，建議使用 get_patient_practice_sessions
    
    Args:
        patient_id: 患者ID
        therapist_id: 治療師ID（用於權限檢查）
        session: 資料庫會話
        skip: 略過記錄數
        limit: 限制記錄數
        status_filter: 狀態篩選 ("all", "pending", "recorded", "analyzed")
        chapter_id: 特定章節篩選
        
    Returns:
        PatientPracticeListResponse: 患者練習列表回應
    """
    # 權限檢查：確認治療師與患者的配對關係
    therapist_client_check = session.exec(
        select(TherapistClient)
        .where(
            and_(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.client_id == patient_id,
                TherapistClient.is_active == True
            )
        )
    ).first()
    
    if not therapist_client_check:
        raise ValueError("治療師無權查看此患者的練習記錄")
    
    # 取得患者資訊
    patient = session.exec(
        select(User).where(User.user_id == patient_id)
    ).first()
    
    if not patient:
        raise ValueError("找不到指定的患者")
    
    # 建立查詢
    base_query = (
        select(PracticeRecord)
        .join(PracticeSession)
        .join(Chapter)
        .join(Sentence)
        .where(
            and_(
                PracticeSession.user_id == patient_id,
                PracticeSession.session_status == PracticeSessionStatus.COMPLETED  # 只顯示已完成的練習會話
            )
        )
        .options(
            selectinload(PracticeRecord.practice_session),
            selectinload(PracticeRecord.sentence)
        )
    )
    
    # 狀態篩選
    if status_filter and status_filter != "all":
        if status_filter == "pending":
            base_query = base_query.where(PracticeRecord.record_status == PracticeRecordStatus.PENDING)
        elif status_filter == "recorded":
            base_query = base_query.where(PracticeRecord.record_status == PracticeRecordStatus.RECORDED)
        elif status_filter == "analyzed":
            base_query = base_query.where(PracticeRecord.record_status.in_([
                PracticeRecordStatus.AI_ANALYZED,
                PracticeRecordStatus.ANALYZED
            ]))
    
    # 章節篩選
    if chapter_id:
        base_query = base_query.where(Chapter.chapter_id == chapter_id)
    
    # 計算總數
    count_query = select(func.count()).select_from(base_query.subquery())
    total = session.exec(count_query).one()
    
    # 取得分頁資料
    practice_records = session.exec(
        base_query
        .offset(skip)
        .limit(limit)
        .order_by(PracticeRecord.created_at.desc())
    ).all()
    
    # 初始化音訊服務
    audio_service = PracticeRecordingService()
    
    # 建構回應資料
    record_responses = []
    for record in practice_records:
        # 取得章節名稱
        chapter = session.exec(
            select(Chapter).where(Chapter.chapter_id == record.practice_session.chapter_id)
        ).first()
        
        # 檢查是否有回饋
        has_feedback = session.exec(
            select(func.count(PracticeFeedback.feedback_id))
            .where(PracticeFeedback.practice_record_id == record.practice_record_id)
        ).one() > 0
        
        # 生成音訊播放URL（如果有音訊）
        audio_stream_url = None
        audio_stream_expires_at = None
        
        if record.audio_path:
            try:
                stream_url, expires_at = await audio_service.get_presigned_url(record.audio_path)
                audio_stream_url = stream_url
                audio_stream_expires_at = expires_at
            except Exception:
                # 音訊URL生成失敗時，優雅處理
                pass
        
        record_responses.append(
            PatientPracticeRecordResponse(
                practice_record_id=record.practice_record_id,
                practice_session_id=record.practice_session_id,
                chapter_id=chapter.chapter_id if chapter else record.practice_session.chapter_id,
                chapter_name=chapter.chapter_name if chapter else "",
                sentence_id=record.sentence_id,
                sentence_content=record.sentence.content,
                sentence_name=record.sentence.sentence_name,
                record_status=record.record_status,
                audio_path=record.audio_path,
                audio_duration=record.audio_duration,
                audio_stream_url=audio_stream_url,
                audio_stream_expires_at=audio_stream_expires_at,
                recorded_at=record.recorded_at,
                has_feedback=has_feedback
            )
        )
    
    return PatientPracticeListResponse(
        patient_info={
            "patient_id": str(patient.user_id),
            "patient_name": patient.name
        },
        total=total,
        practice_records=record_responses
    )
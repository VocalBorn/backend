"""
練習會話回饋服務測試
測試以 PracticeSessionFeedback 為主的新回饋功能
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import Session

from src.practice.services.feedback_service import (
    create_session_feedback,
    get_session_feedbacks,
    update_session_feedbacks
)
from src.practice.schemas import (
    PracticeSessionFeedbackCreate,
    PracticeSessionFeedbackUpdate,
    PracticeSessionFeedbackResponse
)
from src.practice.models import (
    PracticeSession,
    PracticeSessionFeedback,
    PracticeSessionStatus
)
from src.auth.models import User
from src.course.models import Chapter
from src.therapist.models import TherapistClient


class TestSessionFeedbackService:
    """練習會話回饋服務測試類"""

    @pytest.fixture
    def mock_session(self):
        """模擬資料庫會話"""
        session = MagicMock(spec=Session)
        return session

    @pytest.fixture
    def sample_practice_session(self):
        """範例練習會話"""
        return PracticeSession(
            practice_session_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            chapter_id=uuid.uuid4(),
            session_status=PracticeSessionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def sample_therapist(self):
        """範例治療師"""
        return User(
            user_id=uuid.uuid4(),
            name="張治療師",
            email="therapist@example.com"
        )

    @pytest.fixture
    def sample_patient(self):
        """範例患者"""
        return User(
            user_id=uuid.uuid4(),
            name="王小明",
            email="patient@example.com"
        )

    @pytest.fixture
    def sample_chapter(self):
        """範例章節"""
        return Chapter(
            chapter_id=uuid.uuid4(),
            chapter_name="基本對話",
            situation_id=uuid.uuid4()
        )

    @pytest.fixture
    def sample_therapist_client(self, sample_therapist, sample_patient):
        """範例治療師-患者關係"""
        return TherapistClient(
            therapist_id=sample_therapist.user_id,
            client_id=sample_patient.user_id,
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_create_session_feedback_success(
        self,
        mock_session,
        sample_practice_session,
        sample_therapist,
        sample_patient,
        sample_chapter,
        sample_therapist_client
    ):
        """測試成功建立會話回饋"""
        # 設定
        feedback_data = PracticeSessionFeedbackCreate(
            content="整體表現不錯，發音清晰度有明顯改善。"
        )
        
        # 模擬資料庫查詢
        mock_session.get.side_effect = [
            sample_practice_session,  # 第一次：取得練習會話
            sample_therapist,         # 第二次：取得治療師
            sample_patient,           # 第三次：取得患者  
            sample_chapter            # 第四次：取得章節
        ]
        
        mock_session.exec.side_effect = [
            MagicMock(first=MagicMock(return_value=sample_therapist_client)),  # 檢查治療師權限
            MagicMock(first=MagicMock(return_value=None))  # 檢查現有回饋
        ]
        
        # 模擬新建立的回饋
        new_feedback = PracticeSessionFeedback(
            session_feedback_id=uuid.uuid4(),
            practice_session_id=sample_practice_session.practice_session_id,
            therapist_id=sample_therapist.user_id,
            content=feedback_data.content,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_session.refresh.return_value = None
        
        # 執行
        result = await create_session_feedback(
            practice_session_id=sample_practice_session.practice_session_id,
            feedback_data=feedback_data,
            therapist_id=sample_therapist.user_id,
            session=mock_session
        )
        
        # 驗證
        assert isinstance(result, PracticeSessionFeedbackResponse)
        assert result.practice_session_id == sample_practice_session.practice_session_id
        assert result.therapist_id == sample_therapist.user_id
        assert result.therapist_name == sample_therapist.name
        assert result.patient_name == sample_patient.name
        assert result.chapter_name == sample_chapter.chapter_name
        assert result.content == feedback_data.content
        
        # 驗證資料庫操作
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_feedback_already_exists(
        self,
        mock_session,
        sample_practice_session,
        sample_therapist,
        sample_therapist_client
    ):
        """測試建立回饋時已存在回饋"""
        from fastapi import HTTPException
        
        # 設定
        feedback_data = PracticeSessionFeedbackCreate(
            content="測試回饋內容"
        )
        
        # 模擬現有回饋
        existing_feedback = PracticeSessionFeedback(
            session_feedback_id=uuid.uuid4(),
            practice_session_id=sample_practice_session.practice_session_id,
            therapist_id=sample_therapist.user_id,
            content="現有回饋"
        )
        
        # 模擬資料庫查詢
        mock_session.get.return_value = sample_practice_session
        mock_session.exec.side_effect = [
            MagicMock(first=MagicMock(return_value=sample_therapist_client)),  # 檢查治療師權限
            MagicMock(first=MagicMock(return_value=existing_feedback))  # 檢查現有回饋
        ]
        
        # 執行並驗證異常
        with pytest.raises(HTTPException) as exc_info:
            await create_session_feedback(
                practice_session_id=sample_practice_session.practice_session_id,
                feedback_data=feedback_data,
                therapist_id=sample_therapist.user_id,
                session=mock_session
            )
        
        assert exc_info.value.status_code == 400
        assert "已有回饋" in exc_info.value.detail

    async def test_get_session_feedbacks_success(
        self,
        mock_session,
        sample_practice_session,
        sample_therapist,
        sample_patient,
        sample_chapter,
        sample_therapist_client
    ):
        """測試成功取得會話回饋"""
        # 設定現有回饋
        existing_feedback = PracticeSessionFeedback(
            session_feedback_id=uuid.uuid4(),
            practice_session_id=sample_practice_session.practice_session_id,
            therapist_id=sample_therapist.user_id,
            content="現有的回饋內容",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 模擬資料庫查詢
        mock_session.get.side_effect = [
            sample_practice_session,  # 取得練習會話
            sample_therapist,         # 取得治療師
            sample_patient,           # 取得患者
            sample_chapter            # 取得章節
        ]
        
        mock_session.exec.side_effect = [
            MagicMock(first=MagicMock(return_value=sample_therapist_client)),  # 檢查治療師權限
            MagicMock(first=MagicMock(return_value=existing_feedback))  # 取得回饋
        ]
        
        # 執行
        result = await get_session_feedbacks(
            practice_session_id=sample_practice_session.practice_session_id,
            therapist_id=sample_therapist.user_id,
            session=mock_session
        )
        
        # 驗證
        assert isinstance(result, PracticeSessionFeedbackResponse)
        assert result.session_feedback_id == existing_feedback.session_feedback_id
        assert result.content == existing_feedback.content
        assert result.therapist_name == sample_therapist.name

    async def test_update_session_feedbacks_success(
        self,
        mock_session,
        sample_practice_session,
        sample_therapist,
        sample_patient,
        sample_chapter,
        sample_therapist_client
    ):
        """測試成功更新會話回饋"""
        # 設定
        update_data = PracticeSessionFeedbackUpdate(
            content="更新後的回饋內容"
        )
        
        # 設定現有回饋
        existing_feedback = PracticeSessionFeedback(
            session_feedback_id=uuid.uuid4(),
            practice_session_id=sample_practice_session.practice_session_id,
            therapist_id=sample_therapist.user_id,
            content="原始回饋內容",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 模擬資料庫查詢
        mock_session.get.side_effect = [
            sample_practice_session,  # 取得練習會話
            sample_therapist,         # 取得治療師
            sample_patient,           # 取得患者
            sample_chapter            # 取得章節
        ]
        
        mock_session.exec.side_effect = [
            MagicMock(first=MagicMock(return_value=sample_therapist_client)),  # 檢查治療師權限
            MagicMock(first=MagicMock(return_value=existing_feedback))  # 取得現有回饋
        ]
        
        # 執行
        result = await update_session_feedbacks(
            practice_session_id=sample_practice_session.practice_session_id,
            feedback_data=update_data,
            therapist_id=sample_therapist.user_id,
            session=mock_session
        )
        
        # 驗證
        assert isinstance(result, PracticeSessionFeedbackResponse)
        assert result.content == update_data.content
        
        # 驗證資料庫操作
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    async def test_unauthorized_access(
        self,
        mock_session,
        sample_practice_session
    ):
        """測試無權限訪問"""
        from fastapi import HTTPException
        
        # 設定
        unauthorized_therapist_id = uuid.uuid4()
        feedback_data = PracticeSessionFeedbackCreate(
            content="測試回饋內容"
        )
        
        # 模擬資料庫查詢 - 沒有治療師-患者關係
        mock_session.get.return_value = sample_practice_session
        mock_session.exec.return_value = MagicMock(first=MagicMock(return_value=None))
        
        # 執行並驗證異常
        with pytest.raises(HTTPException) as exc_info:
            await create_session_feedback(
                practice_session_id=sample_practice_session.practice_session_id,
                feedback_data=feedback_data,
                therapist_id=unauthorized_therapist_id,
                session=mock_session
            )
        
        assert exc_info.value.status_code == 403
        assert "無權限" in exc_info.value.detail

"""
測試工具函數
提供常用的Mock設置和測試輔助函數
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock
from typing import Optional, Any, List

from src.practice.models import (
    PracticeSession, 
    PracticeRecord, 
    PracticeSessionFeedback,
    PracticeSessionStatus,
    PracticeRecordStatus
)
from src.auth.models import User, UserRole
from src.therapist.models import TherapistClient
from src.course.models import Chapter, Sentence


class MockQueryBuilder:
    """構建複雜的Mock查詢回應"""
    
    def __init__(self):
        self.query_responses = []
    
    def add_response(self, result: Any) -> 'MockQueryBuilder':
        """添加查詢回應"""
        mock_query = MagicMock()
        if result is None:
            mock_query.first.return_value = None
        elif isinstance(result, list):
            mock_query.all.return_value = result
            mock_query.first.return_value = result[0] if result else None
        else:
            mock_query.first.return_value = result
            mock_query.all.return_value = [result]
        
        self.query_responses.append(mock_query)
        return self
    
    def build(self) -> List[MagicMock]:
        """建構所有Mock查詢回應"""
        return self.query_responses


def create_mock_session() -> MagicMock:
    """建立標準的Mock Session"""
    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.delete = MagicMock()
    return mock_session


def setup_session_mock_for_get(mock_session: MagicMock, get_results: List[Any]) -> None:
    """設置Session.get的Mock回應"""
    mock_session.get.side_effect = get_results


def setup_session_mock_for_exec(mock_session: MagicMock, exec_results: List[Any]) -> None:
    """設置Session.exec的Mock回應"""
    builder = MockQueryBuilder()
    for result in exec_results:
        builder.add_response(result)
    
    mock_session.exec.side_effect = builder.build()


def create_sample_user(
    user_id: Optional[uuid.UUID] = None,
    role: UserRole = UserRole.CLIENT,
    name: str = "測試用戶"
) -> User:
    """建立範例用戶"""
    return User(
        user_id=user_id or uuid.uuid4(),
        name=name,
        role=role,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_sample_therapist(
    therapist_id: Optional[uuid.UUID] = None,
    name: str = "張治療師"
) -> User:
    """建立範例治療師"""
    return create_sample_user(
        user_id=therapist_id,
        role=UserRole.THERAPIST,
        name=name
    )


def create_sample_client(
    client_id: Optional[uuid.UUID] = None,
    name: str = "李患者"
) -> User:
    """建立範例患者"""
    return create_sample_user(
        user_id=client_id,
        role=UserRole.CLIENT,
        name=name
    )


def create_sample_practice_session(
    practice_session_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    chapter_id: Optional[uuid.UUID] = None,
    status: PracticeSessionStatus = PracticeSessionStatus.IN_PROGRESS
) -> PracticeSession:
    """建立範例練習會話"""
    return PracticeSession(
        practice_session_id=practice_session_id or uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        chapter_id=chapter_id or uuid.uuid4(),
        session_status=status,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_sample_practice_record(
    practice_record_id: Optional[uuid.UUID] = None,
    practice_session_id: Optional[uuid.UUID] = None,
    sentence_id: Optional[uuid.UUID] = None,
    status: PracticeRecordStatus = PracticeRecordStatus.PENDING
) -> PracticeRecord:
    """建立範例練習記錄"""
    return PracticeRecord(
        practice_record_id=practice_record_id or uuid.uuid4(),
        practice_session_id=practice_session_id or uuid.uuid4(),
        sentence_id=sentence_id or uuid.uuid4(),
        record_status=status,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_sample_therapist_client_relationship(
    therapist_id: Optional[uuid.UUID] = None,
    client_id: Optional[uuid.UUID] = None,
    is_active: bool = True
) -> TherapistClient:
    """建立範例治療師-患者關係"""
    return TherapistClient(
        therapist_id=therapist_id or uuid.uuid4(),
        client_id=client_id or uuid.uuid4(),
        is_active=is_active,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_sample_chapter(
    chapter_id: Optional[uuid.UUID] = None,
    title: str = "測試章節"
) -> Chapter:
    """建立範例章節"""
    return Chapter(
        chapter_id=chapter_id or uuid.uuid4(),
        title=title,
        description="測試章節描述",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_sample_feedback(
    feedback_id: Optional[uuid.UUID] = None,
    practice_session_id: Optional[uuid.UUID] = None,
    therapist_id: Optional[uuid.UUID] = None,
    content: str = "測試回饋內容"
) -> PracticeSessionFeedback:
    """建立範例練習會話回饋"""
    return PracticeSessionFeedback(
        feedback_id=feedback_id or uuid.uuid4(),
        practice_session_id=practice_session_id or uuid.uuid4(),
        therapist_id=therapist_id or uuid.uuid4(),
        content=content,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


# 權限測試相關的Mock設置函數
def setup_unauthorized_access_mock(mock_session: MagicMock, target_user_id: uuid.UUID, different_user_id: uuid.UUID) -> None:
    """設置無權限存取的Mock（用戶ID不匹配）"""
    mock_practice_session = create_sample_practice_session(user_id=different_user_id)
    mock_record = create_sample_practice_record()
    mock_record.practice_session = mock_practice_session
    
    setup_session_mock_for_exec(mock_session, [mock_record])


def setup_not_found_mock(mock_session: MagicMock) -> None:
    """設置資源不存在的Mock"""
    setup_session_mock_for_exec(mock_session, [None])


def setup_therapist_client_relationship_mock(
    mock_session: MagicMock, 
    therapist_id: uuid.UUID, 
    client_id: uuid.UUID,
    is_active: bool = True
) -> None:
    """設置治療師-患者關係的Mock"""
    relationship = create_sample_therapist_client_relationship(
        therapist_id=therapist_id,
        client_id=client_id,
        is_active=is_active
    )
    setup_session_mock_for_exec(mock_session, [relationship])


# 錯誤場景的Mock設置
def setup_database_error_mock(mock_session: MagicMock, operation: str = "commit") -> None:
    """設置資料庫錯誤的Mock"""
    if operation == "commit":
        mock_session.commit.side_effect = Exception("Database commit error")
    elif operation == "get":
        mock_session.get.side_effect = Exception("Database get error")
    elif operation == "exec":
        mock_session.exec.side_effect = Exception("Database exec error")
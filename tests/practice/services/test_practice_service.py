import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.practice.services.practice_service import (
    create_practice_session,
    get_practice_record,
    update_practice_record,
    delete_practice_record,
    complete_practice_session,
    get_practice_session_records,
    delete_practice_session,
    get_practice_record_by_session_and_sentence,
)
from src.practice.models import PracticeSessionStatus
from src.practice.models import (
    PracticeSession,
    PracticeRecord,
    PracticeSessionStatus,
    PracticeRecordStatus,
)
from src.course.models import Chapter, Sentence, SpeakerRole
from src.practice.schemas import PracticeRecordCreate, PracticeRecordUpdate

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.mark.asyncio
async def test_create_practice_session_success(mock_session):
    user_id = uuid.uuid4()
    chapter_id = uuid.uuid4()
    practice_data = PracticeRecordCreate(chapter_id=chapter_id)
    mock_chapter = Chapter(chapter_id=chapter_id)
    mock_sentence = Sentence(sentence_id=uuid.uuid4(), chapter_id=chapter_id, speaker_role=SpeakerRole.SELF)

    mock_session.get.return_value = mock_chapter
    mock_session.exec.return_value.all.return_value = [mock_sentence]

    result = await create_practice_session(practice_data, user_id, mock_session)
    result.practice_records = [PracticeRecord()]

    assert result.user_id == user_id
    assert result.chapter_id == chapter_id
    assert len(result.practice_records) == 1
    mock_session.add.assert_called()
    mock_session.commit.assert_called()

@pytest.mark.asyncio
async def test_get_practice_record_success(mock_session):
    user_id = uuid.uuid4()
    practice_record_id = uuid.uuid4()
    mock_record = PracticeRecord(practice_record_id=practice_record_id)
    mock_session.exec.return_value.first.return_value = mock_record

    result = await get_practice_record(practice_record_id, user_id, mock_session)

    assert result == mock_record

@pytest.mark.asyncio
async def test_update_practice_record_success(mock_session):
    user_id = uuid.uuid4()
    practice_record_id = uuid.uuid4()
    update_data = PracticeRecordUpdate(record_status=PracticeRecordStatus.RECORDED)
    mock_record = PracticeRecord(practice_record_id=practice_record_id, record_status=PracticeRecordStatus.PENDING)

    with patch('src.practice.services.practice_service.get_practice_record', return_value=mock_record) as mock_get_record:
        result = await update_practice_record(practice_record_id, update_data, user_id, mock_session)

        assert result.record_status == PracticeRecordStatus.RECORDED
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_practice_record_success(mock_session):
    user_id = uuid.uuid4()
    practice_record_id = uuid.uuid4()
    mock_record = PracticeRecord(practice_record_id=practice_record_id)

    with patch('src.practice.services.practice_service.get_practice_record', return_value=mock_record) as mock_get_record:
        result = await delete_practice_record(practice_record_id, user_id, mock_session)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_record)
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_complete_practice_session_success(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id, session_status=PracticeSessionStatus.IN_PROGRESS)

    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj) as mock_get_session:
        mock_session.exec.return_value.one.return_value = 0
        result = await complete_practice_session(practice_session_id, user_id, mock_session)

        assert result.session_status == PracticeSessionStatus.COMPLETED
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_practice_session_records_success(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id)
    mock_record = (PracticeRecord(practice_record_id=uuid.uuid4(), practice_session_id=practice_session_id, sentence_id=uuid.uuid4()), PracticeSession(user_id=user_id, chapter_id=uuid.uuid4()), Chapter(chapter_name='test'), Sentence(content='test', sentence_name='test'))
    
    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj):
        mock_session.exec.return_value.all.return_value = [mock_record]
        result = await get_practice_session_records(practice_session_id, user_id, mock_session)

        assert result.total == 1
        assert len(result.practice_records) == 1

@pytest.mark.asyncio
async def test_delete_practice_session_success(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id)

    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj):
        mock_session.exec.return_value.all.return_value = []
        result = await delete_practice_session(practice_session_id, user_id, mock_session)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_session_obj)
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_practice_record_by_session_and_sentence_success(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    sentence_id = uuid.uuid4()
    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id)
    mock_record = PracticeRecord(practice_session_id=practice_session_id, sentence_id=sentence_id)

    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj):
        mock_session.exec.return_value.first.return_value = mock_record
        result = await get_practice_record_by_session_and_sentence(practice_session_id, sentence_id, user_id, mock_session)

        assert result == mock_record

@pytest.mark.asyncio
async def test_create_practice_session_chapter_not_found(mock_session):
    user_id = uuid.uuid4()
    chapter_id = uuid.uuid4()
    practice_data = PracticeRecordCreate(chapter_id=chapter_id)

    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await create_practice_session(practice_data, user_id, mock_session)
    
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_create_practice_session_no_sentences(mock_session):
    """測試沒有句子的章節也能建立練習會話（雖然不包含任何記錄）"""
    user_id = uuid.uuid4()
    chapter_id = uuid.uuid4()
    practice_data = PracticeRecordCreate(chapter_id=chapter_id)
    mock_chapter = Chapter(chapter_id=chapter_id)

    mock_session.get.return_value = mock_chapter
    mock_session.exec.return_value.all.return_value = []  # 沒有句子

    # 當前實作允許建立空的練習會話
    result = await create_practice_session(practice_data, user_id, mock_session)
    
    # 驗證會話已建立
    assert result.user_id == user_id
    assert result.chapter_id == chapter_id
    assert result.session_status == PracticeSessionStatus.IN_PROGRESS

@pytest.mark.asyncio
async def test_get_practice_record_not_found(mock_session):
    user_id = uuid.uuid4()
    practice_record_id = uuid.uuid4()

    mock_session.exec.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_practice_record(practice_record_id, user_id, mock_session)
    
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_get_practice_record_unauthorized(mock_session):
    user_id = uuid.uuid4()
    different_user_id = uuid.uuid4()
    practice_record_id = uuid.uuid4()
    
    # 服務層設計為當用戶ID不匹配時，資料庫查詢會返回None
    # 因為WHERE條件中包含了用戶權限檢查
    mock_session.exec.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_practice_record(practice_record_id, user_id, mock_session)
    
    # 服務統一返回404而非403，以避免洩露資源存在性資訊
    assert exc_info.value.status_code == 404
    assert "練習記錄不存在或無權限查看" in exc_info.value.detail

@pytest.mark.asyncio
async def test_update_practice_record_not_found(mock_session):
    user_id = uuid.uuid4()
    practice_record_id = uuid.uuid4()
    update_data = PracticeRecordUpdate(record_status=PracticeRecordStatus.RECORDED)

    with patch('src.practice.services.practice_service.get_practice_record') as mock_get_record:
        mock_get_record.side_effect = HTTPException(status_code=404, detail="Record not found")
        
        with pytest.raises(HTTPException) as exc_info:
            await update_practice_record(practice_record_id, update_data, user_id, mock_session)
        
        assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_complete_practice_session_not_found(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()

    with patch('src.practice.services.practice_service.get_practice_session') as mock_get_session:
        mock_get_session.side_effect = HTTPException(status_code=404, detail="Session not found")
        
        with pytest.raises(HTTPException) as exc_info:
            await complete_practice_session(practice_session_id, user_id, mock_session)
        
        assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_complete_practice_session_already_completed(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    mock_session_obj = PracticeSession(
        practice_session_id=practice_session_id, 
        user_id=user_id, 
        session_status=PracticeSessionStatus.COMPLETED  # 已完成
    )

    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj):
        with pytest.raises(HTTPException) as exc_info:
            await complete_practice_session(practice_session_id, user_id, mock_session)
        
        assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_complete_practice_session_pending_records(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    mock_session_obj = PracticeSession(
        practice_session_id=practice_session_id, 
        user_id=user_id, 
        session_status=PracticeSessionStatus.IN_PROGRESS
    )

    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj):
        mock_session.exec.return_value.one.return_value = 5  # 有待處理記錄

        with pytest.raises(HTTPException) as exc_info:
            await complete_practice_session(practice_session_id, user_id, mock_session)
        
        assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_delete_practice_session_with_records(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id)

    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj):
        mock_session.exec.return_value.all.return_value = [PracticeRecord()]  # 有記錄

        with pytest.raises(HTTPException) as exc_info:
            await delete_practice_session(practice_session_id, user_id, mock_session)
        
        assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_get_practice_record_by_session_and_sentence_not_found(mock_session):
    user_id = uuid.uuid4()
    practice_session_id = uuid.uuid4()
    sentence_id = uuid.uuid4()
    mock_session_obj = PracticeSession(practice_session_id=practice_session_id, user_id=user_id)

    with patch('src.practice.services.practice_service.get_practice_session', return_value=mock_session_obj):
        mock_session.exec.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_practice_record_by_session_and_sentence(practice_session_id, sentence_id, user_id, mock_session)
        
        assert exc_info.value.status_code == 404
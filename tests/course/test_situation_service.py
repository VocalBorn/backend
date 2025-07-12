"""
Situation Service 單元測試
測試 src.course.services.situation_service 中的情境相關功能
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from fastapi import HTTPException
import uuid

from src.course.services.situation_service import (
    create_situation,
    get_situation,
    list_situations,
    update_situation,
    delete_situation
)
from src.course.schemas import SituationCreate, SituationUpdate


class TestCreateSituation:
    """建立情境功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        return session

    @pytest.fixture
    def situation_create_data(self):
        """情境建立資料"""
        return SituationCreate(
            situation_name="餐廳點餐",
            description="在餐廳與服務員進行點餐對話",
            location="餐廳"
        )

    @pytest.fixture
    def mock_situation(self):
        """Mock Situation 物件"""
        situation = Mock()
        situation.situation_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        situation.situation_name = "餐廳點餐"
        situation.description = "在餐廳與服務員進行點餐對話"
        situation.location = "餐廳"
        situation.created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        situation.updated_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        return situation

    @pytest.mark.asyncio
    async def test_create_situation_success(
        self, 
        mock_db_session, 
        situation_create_data, 
        mock_situation
    ):
        """測試成功建立情境"""
        # Arrange
        with patch('src.course.services.situation_service.Situation') as MockSituation:
            MockSituation.return_value = mock_situation
            
            # Act
            result = await create_situation(situation_create_data, mock_db_session)
            
            # Assert
            assert result.situation_id == uuid.UUID("11111111-1111-1111-1111-111111111111")
            assert result.situation_name == "餐廳點餐"
            assert result.description == "在餐廳與服務員進行點餐對話"
            assert result.location == "餐廳"
            
            MockSituation.assert_called_once_with(
                situation_name="餐廳點餐",
                description="在餐廳與服務員進行點餐對話",
                location="餐廳"
            )
            mock_db_session.add.assert_called_once_with(mock_situation)
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(mock_situation)

    @pytest.mark.asyncio
    async def test_create_situation_minimal_data(self, mock_db_session):
        """測試使用最少資料建立情境"""
        # Arrange
        minimal_data = SituationCreate(
            situation_name="簡單情境",
            description="簡單描述"
        )
        
        mock_situation = Mock()
        mock_situation.situation_id = "22222222-2222-2222-2222-222222222222"
        mock_situation.situation_name = "簡單情境"
        mock_situation.description = "簡單描述"
        mock_situation.location = None
        mock_situation.created_at = datetime.now(timezone.utc)
        mock_situation.updated_at = datetime.now(timezone.utc)
        
        with patch('src.course.services.situation_service.Situation') as MockSituation:
            MockSituation.return_value = mock_situation
            
            # Act
            result = await create_situation(minimal_data, mock_db_session)
            
            # Assert
            assert result.situation_name == "簡單情境"
            assert result.description == "簡單描述"
            assert result.location is None

    @pytest.mark.asyncio
    async def test_create_situation_database_error(
        self, 
        mock_db_session, 
        situation_create_data
    ):
        """測試資料庫錯誤處理"""
        # Arrange
        mock_db_session.commit.side_effect = Exception("Database error")
        
        with patch('src.course.services.situation_service.Situation') as MockSituation:
            MockSituation.return_value = Mock()
            
            # Act & Assert
            with pytest.raises(Exception, match="Database error"):
                await create_situation(situation_create_data, mock_db_session)


class TestGetSituation:
    """取得情境功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        return session

    @pytest.fixture
    def mock_situation(self):
        """Mock Situation 物件"""
        situation = Mock()
        situation.situation_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
        situation.situation_name = "醫院掛號"
        situation.description = "在醫院櫃台進行掛號對話"
        situation.location = "醫院"
        situation.created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        situation.updated_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        return situation

    @pytest.mark.asyncio
    async def test_get_situation_success(self, mock_db_session, mock_situation):
        """測試成功取得情境"""
        # Arrange
        situation_id = "situation-123"
        mock_db_session.get.return_value = mock_situation
        
        # Act
        result = await get_situation(situation_id, mock_db_session)
        
        # Assert
        assert result.situation_id == uuid.UUID("33333333-3333-3333-3333-333333333333")
        assert result.situation_name == "醫院掛號"
        assert result.description == "在醫院櫃台進行掛號對話"
        assert result.location == "醫院"
        mock_db_session.get.assert_called_once()
        called_args = mock_db_session.get.call_args[0]
        assert called_args[1] == situation_id

    @pytest.mark.asyncio
    async def test_get_situation_not_found(self, mock_db_session):
        """測試情境不存在"""
        # Arrange
        situation_id = "nonexistent-id"
        mock_db_session.get.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_situation(situation_id, mock_db_session)
        
        assert exc_info.value.status_code == 404
        assert "Situation not found" in exc_info.value.detail


class TestListSituations:
    """取得情境列表功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        return session

    @pytest.fixture
    def mock_situations(self):
        """Mock Situation 物件列表"""
        situations = []
        for i in range(3):
            situation = Mock()
            situation.situation_id = uuid.UUID(f"{i+1:08d}-0000-0000-0000-000000000000")
            situation.situation_name = f"情境 {i+1}"
            situation.description = f"描述 {i+1}"
            situation.location = f"地點 {i+1}"
            situation.created_at = datetime(2025, 1, i+1, 12, 0, 0, tzinfo=timezone.utc)
            situation.updated_at = datetime(2025, 1, i+1, 12, 0, 0, tzinfo=timezone.utc)
            situations.append(situation)
        return situations

    @pytest.mark.asyncio
    async def test_list_situations_default_params(
        self, 
        mock_db_session, 
        mock_situations
    ):
        """測試使用預設參數取得情境列表"""
        # Arrange
        mock_db_session.exec.return_value.all.return_value = mock_situations
        
        # Act
        result = await list_situations(mock_db_session)
        
        # Assert
        assert result.total == 3
        assert len(result.situations) == 3
        assert result.situations[0].situation_name == "情境 1"
        assert result.situations[1].situation_name == "情境 2"
        assert result.situations[2].situation_name == "情境 3"

    @pytest.mark.asyncio
    async def test_list_situations_with_pagination(
        self, 
        mock_db_session, 
        mock_situations
    ):
        """測試使用分頁參數取得情境列表"""
        # Arrange
        paginated_situations = mock_situations[:2]  # 只返回前兩個
        mock_db_session.exec.return_value.all.return_value = mock_situations  # 總數
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value = mock_query
        mock_db_session.exec.side_effect = [
            Mock(all=Mock(return_value=mock_situations)),  # 總數查詢
            Mock(all=Mock(return_value=paginated_situations))  # 分頁查詢
        ]
        
        with patch('src.course.services.situation_service.select', return_value=mock_query):
            # Act
            result = await list_situations(mock_db_session, skip=0, limit=2)
            
            # Assert
            assert result.total == 3
            assert len(result.situations) == 2

    @pytest.mark.asyncio
    async def test_list_situations_with_search(
        self, 
        mock_db_session, 
        mock_situations
    ):
        """測試使用搜尋參數取得情境列表"""
        # Arrange
        filtered_situations = [mock_situations[0]]  # 只返回第一個
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.offset.return_value.limit.return_value = mock_query
        
        mock_db_session.exec.side_effect = [
            Mock(all=Mock(return_value=filtered_situations)),  # 總數查詢
            Mock(all=Mock(return_value=filtered_situations))   # 分頁查詢
        ]
        
        with patch('src.course.services.situation_service.select', return_value=mock_query):
            # Act
            result = await list_situations(mock_db_session, search="情境 1")
            
            # Assert
            assert result.total == 1
            assert len(result.situations) == 1
            assert result.situations[0].situation_name == "情境 1"

    @pytest.mark.asyncio
    async def test_list_situations_empty_result(self, mock_db_session):
        """測試空結果列表"""
        # Arrange
        mock_db_session.exec.return_value.all.return_value = []
        
        # Act
        result = await list_situations(mock_db_session)
        
        # Assert
        assert result.total == 0
        assert len(result.situations) == 0


class TestUpdateSituation:
    """更新情境功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        return session

    @pytest.fixture
    def mock_situation(self):
        """Mock Situation 物件"""
        situation = Mock()
        situation.situation_id = "44444444-4444-4444-4444-444444444444"
        situation.situation_name = "原始名稱"
        situation.description = "原始描述"
        situation.location = "原始地點"
        situation.created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        situation.updated_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        return situation

    @pytest.fixture
    def situation_update_data(self):
        """情境更新資料"""
        return SituationUpdate(
            situation_name="更新的名稱",
            description="更新的描述",
            location="更新的地點"
        )

    @pytest.mark.asyncio
    async def test_update_situation_success(
        self, 
        mock_db_session, 
        mock_situation, 
        situation_update_data
    ):
        """測試成功更新情境"""
        # Arrange
        situation_id = "44444444-4444-4444-4444-444444444444"
        mock_db_session.get.return_value = mock_situation
        
        with patch('src.course.services.situation_service.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            
            # Act
            result = await update_situation(situation_id, situation_update_data, mock_db_session)
            
            # Assert
            assert mock_situation.situation_name == "更新的名稱"
            assert mock_situation.description == "更新的描述"
            assert mock_situation.location == "更新的地點"
            assert mock_situation.updated_at == mock_now
            
            assert result.situation_name == "更新的名稱"
            assert result.description == "更新的描述"
            assert result.location == "更新的地點"
            
            mock_db_session.add.assert_called_once_with(mock_situation)
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(mock_situation)

    @pytest.mark.asyncio
    async def test_update_situation_partial_update(
        self, 
        mock_db_session, 
        mock_situation
    ):
        """測試部分更新情境"""
        # Arrange
        situation_id = "situation-123"
        partial_update = SituationUpdate(situation_name="只更新名稱")
        mock_db_session.get.return_value = mock_situation
        
        with patch('src.course.services.situation_service.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            
            # Act
            result = await update_situation(situation_id, partial_update, mock_db_session)
            
            # Assert
            assert mock_situation.situation_name == "只更新名稱"
            assert mock_situation.description == "原始描述"  # 沒有更新
            assert mock_situation.location == "原始地點"      # 沒有更新
            assert result.situation_name == "只更新名稱"

    @pytest.mark.asyncio
    async def test_update_situation_not_found(self, mock_db_session):
        """測試更新不存在的情境"""
        # Arrange
        situation_id = "55555555-5555-5555-5555-555555555555"
        update_data = SituationUpdate(situation_name="新名稱")
        mock_db_session.get.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_situation(situation_id, update_data, mock_db_session)
        
        assert exc_info.value.status_code == 404
        assert "Situation not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_situation_no_changes(
        self, 
        mock_db_session, 
        mock_situation
    ):
        """測試沒有任何更新的情況"""
        # Arrange
        situation_id = "44444444-4444-4444-4444-444444444444"
        empty_update = SituationUpdate()  # 所有欄位都是 None
        mock_db_session.get.return_value = mock_situation
        
        with patch('src.course.services.situation_service.datetime') as mock_datetime:
            mock_now = datetime(2025, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            
            # Act
            result = await update_situation(situation_id, empty_update, mock_db_session)
            
            # Assert
            # 即使沒有更新，updated_at 還是會被設定
            assert mock_situation.updated_at == mock_now
            assert result.situation_name == "原始名稱"


class TestDeleteSituation:
    """刪除情境功能測試類別"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫會話"""
        session = Mock()
        session.delete = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def mock_situation(self):
        """Mock Situation 物件"""
        situation = Mock()
        situation.situation_id = "situation-123"
        situation.chapters = []  # 沒有關聯的章節
        return situation

    @pytest.fixture
    def mock_situation_with_chapters(self):
        """Mock 有章節的 Situation 物件"""
        situation = Mock()
        situation.situation_id = "situation-456"
        situation.chapters = [Mock(), Mock()]  # 有關聯的章節
        return situation

    @pytest.mark.asyncio
    async def test_delete_situation_success(
        self, 
        mock_db_session, 
        mock_situation
    ):
        """測試成功刪除情境"""
        # Arrange
        situation_id = "44444444-4444-4444-4444-444444444444"
        mock_db_session.get.return_value = mock_situation
        
        # Act
        await delete_situation(situation_id, mock_db_session)
        
        # Assert
        mock_db_session.delete.assert_called_once_with(mock_situation)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_situation_not_found(self, mock_db_session):
        """測試刪除不存在的情境"""
        # Arrange
        situation_id = "nonexistent-id"
        mock_db_session.get.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_situation(situation_id, mock_db_session)
        
        assert exc_info.value.status_code == 404
        assert "Situation not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_situation_with_chapters(
        self, 
        mock_db_session, 
        mock_situation_with_chapters
    ):
        """測試刪除有章節的情境"""
        # Arrange
        situation_id = "situation-456"
        mock_db_session.get.return_value = mock_situation_with_chapters
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_situation(situation_id, mock_db_session)
        
        assert exc_info.value.status_code == 400
        assert "Cannot delete situation with existing chapters" in exc_info.value.detail
        
        # 確保沒有執行刪除操作
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_situation_database_error(
        self, 
        mock_db_session, 
        mock_situation
    ):
        """測試刪除時資料庫錯誤"""
        # Arrange
        situation_id = "situation-123"
        mock_db_session.get.return_value = mock_situation
        mock_db_session.commit.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await delete_situation(situation_id, mock_db_session)
        
        # 確保已經調用了刪除，但提交失敗
        mock_db_session.delete.assert_called_once_with(mock_situation)

    @pytest.mark.asyncio
    async def test_delete_situation_empty_chapters_list(
        self, 
        mock_db_session
    ):
        """測試章節列表為空的情境刪除"""
        # Arrange
        situation_id = "66666666-6666-6666-6666-666666666666"
        situation_with_empty_chapters = Mock()
        situation_with_empty_chapters.situation_id = situation_id
        situation_with_empty_chapters.chapters = []  # 明確設為空列表
        mock_db_session.get.return_value = situation_with_empty_chapters
        
        # Act
        await delete_situation(situation_id, mock_db_session)
        
        # Assert
        mock_db_session.delete.assert_called_once_with(situation_with_empty_chapters)
        mock_db_session.commit.assert_called_once()

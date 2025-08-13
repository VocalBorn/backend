# 練習功能模組程式碼檢視報告

## 整體評估

練習功能模組架構設計良好，遵循 FastAPI 最佳實踐，具有清晰的分層結構。模組包含完整的練習會話管理、音訊錄音處理和治療師回饋功能。

**總體評分：7.5/10**

## 詳細分析結果

### 🔴 **關鍵問題（Critical）**

#### 1. 檔案長度超過專案限制
**問題位置**：
- `src/practice/services/practice_service.py` (754 行)
- `src/practice/services/therapist_patient_service.py` (515 行)

**影響**：違反專案 300 行限制，影響程式碼可維護性

**建議拆分**：
```
practice_service.py → 
├── session_management_service.py (會話管理)
├── record_management_service.py (記錄管理)  
└── statistics_service.py (統計功能)

therapist_patient_service.py →
├── patient_management_service.py (患者管理)
└── patient_query_service.py (查詢服務)
```

#### 2. 錯誤處理不一致
**問題位置**：`src/practice/services/therapist_patient_service.py:218, 402`
```python
# 使用 ValueError 而非 HTTPException
if not therapist_client_check:
    raise ValueError("治療師無權查看此患者的練習記錄")
```

**建議統一**：
```python
if not therapist_client_check:
    raise HTTPException(
        status_code=403,
        detail="治療師無權查看此患者的練習記錄"
    )
```

#### 3. 音訊檔案安全驗證不足
**問題位置**：`src/practice/routers/recordings_router.py:126`
```python
audio_duration=None,  # TODO: 從音訊檔案中提取時長
```

**建議實現**：
```python
def validate_audio_file(audio_path: str) -> Dict[str, Any]:
    """驗證音訊檔案安全性和格式"""
    if not audio_path or '..' in audio_path:
        raise HTTPException(status_code=400, detail="音訊路徑無效")
    
    if not audio_path.startswith('practice_recordings/'):
        raise HTTPException(status_code=400, detail="音訊路徑格式錯誤")
    
    # 提取音訊時長和格式
    try:
        import librosa
        duration = librosa.get_duration(filename=audio_path)
        return {"duration": duration, "valid": True}
    except Exception:
        raise HTTPException(status_code=400, detail="音訊檔案無效")
```

### 🟡 **主要問題（Major）**

#### 4. 資料庫查詢效能問題
**問題位置**：`sessions_router.py` 多處重複查詢統計資訊
```python
# 每個會話都執行兩次查詢統計句子數量
for practice_session, chapter in results:
    total_sentences_stmt = select(func.count(...))
    completed_sentences_stmt = select(func.count(...))
```

**建議優化**：
```python
def get_sessions_with_statistics(user_id: UUID, session: Session):
    """使用單次查詢取得會話和統計資料"""
    return session.exec(
        select(
            PracticeSession,
            Chapter,
            func.count(PracticeRecord.practice_record_id).label("total"),
            func.count(
                case((PracticeRecord.record_status != PracticeRecordStatus.PENDING, 1))
            ).label("completed")
        )
        .join(Chapter)
        .left_join(PracticeRecord)
        .where(PracticeSession.user_id == user_id)
        .group_by(PracticeSession.practice_session_id, Chapter.chapter_id)
    ).all()
```

#### 5. 測試覆蓋率不足
**缺失的測試**：
- `practice_service.py` 的測試覆蓋
- `therapist_patient_service.py` 的測試
- 路由層的整合測試

**建議新增測試結構**：
```
tests/practice/services/
├── test_practice_service.py        ❌ (需新增)
├── test_therapist_patient_service.py ❌ (需新增)
└── test_feedback_service.py        ✅ (已存在)

tests/practice/routers/
├── test_sessions_router.py         ❌ (需新增)
├── test_recordings_router.py       ❌ (需新增)
├── test_chapters_router.py         ❌ (需新增)
└── test_therapist_router.py        ❌ (需新增)
```

### 🟢 **次要問題（Minor）**

#### 6. 別名設定說明不清楚
**問題位置**：`src/practice/schemas/practice_record.py:86`
```python
PracticeRecordCreate = PracticeSessionCreate  # 向後相容性別名
```

**建議改進**：
```python
# 向後相容性別名，計畫於 v2.0 版本棄用
# TODO: 在下一個主要版本中移除此別名
PracticeRecordCreate = PracticeSessionCreate
```

#### 7. 棄用標記不清楚
**問題**：模型中有「待刪除、棄用」標記但沒有清理時程

**建議**：建立清楚的棄用計畫和遷移時程表

## 安全性評估

### ✅ **安全措施良好**
1. **權限控制完善**：所有端點都有適當的用戶驗證
2. **資料隔離**：通過 `user_id` 確保用戶只能存取自己的資料
3. **治療師權限驗證**：治療師只能查看指派患者的資料

### ⚠️ **安全性改進建議**
1. **音訊檔案驗證**：需要實現檔案格式和大小限制
2. **路徑遍歷保護**：加強檔案路徑驗證
3. **資料清理**：對用戶輸入進行適當的清理和驗證

## 效能考量

### 現有問題
1. **重複統計查詢**：會話列表載入時執行多次統計查詢
2. **音訊處理負載**：缺少音訊檔案壓縮和優化
3. **缺少快取機制**：頻繁查詢的統計資料沒有快取

### 改進建議
```python
# 1. 新增快取機制
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_session_statistics(session_id: UUID) -> Dict[str, int]:
    """快取會話統計資料"""
    pass

# 2. 批次載入優化
def batch_load_sessions_with_stats(user_id: UUID, session: Session):
    """批次載入會話和統計資料"""
    pass
```

## 符合專案開發指南

### ✅ **遵循指南**
- 繁體中文註釋：所有註釋和文件都使用繁體中文
- Router 命名慣例：路由函數正確使用 `_router` 後綴
- 函數式服務設計：大部分服務採用函數式設計
- 錯誤處理原則：遵循專案錯誤處理標準

### ❌ **不符合項目**
- 檔案長度超限：多個服務檔案超過 300 行限制
- 棄用標記不清楚：模型中有「待刪除、棄用」標記但沒有清理時程

## 立即行動建議

### 🚨 **緊急處理（48小時內）**
1. **拆分過長的服務檔案**以符合 300 行限制
2. **統一錯誤處理機制**，使用 HTTPException 替代 ValueError
3. **實現音訊檔案安全驗證**，包含格式和時長檢查

### 📝 **短期改進（1-2週）**
1. **優化資料庫查詢效能**，減少重複統計查詢
2. **增加測試覆蓋率**，特別是核心服務層
3. **清理棄用程式碼**，建立明確的遷移計畫

### 🎯 **中期優化（1個月）**
1. **實現快取機制**以提升查詢效能
2. **完善 API 文件範例**
3. **添加音訊處理優化功能**
4. **建立完整的整合測試套件**

## 特別建議

### 音訊處理改進
```python
# 建議新增音訊處理服務
class AudioProcessingService:
    @staticmethod
    def validate_audio_format(file_path: str) -> bool:
        """驗證音訊格式"""
        pass
    
    @staticmethod
    def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
        """提取音訊元資料"""
        pass
    
    @staticmethod
    def compress_audio_if_needed(file_path: str) -> str:
        """壓縮音訊檔案（如需要）"""
        pass
```

### 效能監控
```python
# 建議新增效能監控
import time
from functools import wraps

def monitor_performance(func):
    """監控函數執行效能"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # 記錄超過1秒的操作
            logger.warning(f"{func.__name__} 執行時間: {execution_time:.2f}秒")
        
        return result
    return wrapper
```

## 總結

練習功能模組整體設計優良，功能完整，安全性考量充分。主要問題集中在檔案結構和效能優化方面。建議按優先級分階段進行改進，確保系統的可維護性和效能表現。

該模組是平台的核心功能之一，建議優先處理關鍵問題，特別是檔案拆分和安全驗證，以提升系統的穩定性和安全性。

---
*檢視日期：2025-08-12*
*檢視人員：Code Reviewer Agent*
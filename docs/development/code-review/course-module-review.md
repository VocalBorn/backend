# 課程模組程式碼審查報告

## 整體架構評估

**良好方面：**
- 模組結構清晰，遵循 FastAPI 最佳實踐
- 採用函數式設計模式，符合專案指導原則
- 權限控制完善，使用 `RequireViewCourses` 和 `RequireEditCourses`
- 型別註解完整，符合專案標準

**總體評分：7.5/10**

## 發現的問題（按嚴重程度分類）

### 🔴 **關鍵問題（Critical）**

#### 1. 型別不一致問題
**問題位置**：`src/course/services/chapter_service.py:16, 50`
```python
async def create_chapter(situation_id: int, ...)  # 定義為 int
async def get_chapter(chapter_id: int, ...)      # 定義為 int
```
**影響**：模型中定義為 `uuid.UUID`，會導致型別錯誤

**建議修正**：
```python
async def create_chapter(
    situation_id: str,  # 改為 str
    chapter_data: ChapterCreate,
    session: Session
) -> ChapterResponse:
```

#### 2. 路由器命名不符合專案規範
**問題位置**：`src/course/router.py:51`
```python
router = APIRouter(prefix='/situations', tags=['situations'])
```
**建議修正**：
```python
situation_router = APIRouter(
    prefix='/situations',
    tags=['situations']
)
```

### 🟡 **主要問題（Major）**

#### 3. 效能問題：N+1 查詢
**問題位置**：`src/course/services/situation_service.py:63`
```python
total = len(session.exec(query).all())
```
**影響**：執行兩次查詢計算總數，影響效能

**建議改進**：
```python
from sqlmodel import func

async def list_situations(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None
) -> SituationListResponse:
    query = select(Situation)
    
    if search:
        query = query.where(Situation.situation_name.contains(search))
    
    # 使用單一查詢獲取總數
    total_query = select(func.count(Situation.situation_id))
    if search:
        total_query = total_query.where(Situation.situation_name.contains(search))
    
    total = session.exec(total_query).one()
    situations = session.exec(query.offset(skip).limit(limit)).all()
    
    return SituationListResponse(total=total, situations=[...])
```

#### 4. 缺少輸入驗證
- UUID 字串參數沒有驗證格式
- 序號重複檢查缺失
- 時間範圍驗證不足（start_time > end_time）

**建議新增**：
```python
from uuid import UUID
from fastapi import HTTPException

def validate_uuid(uuid_string: str) -> UUID:
    """驗證並轉換 UUID 字串"""
    try:
        return UUID(uuid_string)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

def validate_time_range(start_time: float, end_time: float) -> None:
    """驗證時間範圍"""
    if start_time >= end_time:
        raise HTTPException(
            status_code=400, 
            detail="開始時間必須小於結束時間"
        )
```

#### 5. 錯誤處理不完整
**問題**：資料庫異常處理不夠詳細，缺少統一的錯誤訊息格式

**建議改進**：
```python
from src.shared.exceptions import DatabaseError, ValidationError

async def create_situation(
    situation_data: SituationCreate,
    session: Session
) -> SituationResponse:
    try:
        # ... 建立邏輯
        session.commit()
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logging.error(f"建立情境失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="建立情境時發生錯誤，請稍後再試"
        )
```

### 🟢 **次要問題（Minor）**

#### 6. 測試覆蓋不足
- 只有 `situation_service` 有測試
- 缺少 `chapter_service` 和 `sentence_service` 的測試
- 缺少路由器層級的整合測試

**建議新增測試結構**：
```
tests/course/
├── test_situation_service.py ✅ (已存在)
├── test_chapter_service.py   ❌ (需新增)
├── test_sentence_service.py  ❌ (需新增)
└── test_course_router.py     ❌ (需新增)
```

#### 7. 文件字串不完整
**問題**：服務函數缺少完整的 Google 風格文件字串

**建議改進**：
```python
async def create_chapter(
    situation_id: str,
    chapter_data: ChapterCreate,
    session: Session
) -> ChapterResponse:
    """建立新的章節
    
    Args:
        situation_id: 情境 ID
        chapter_data: 章節建立資料
        session: 資料庫會話
        
    Returns:
        ChapterResponse: 建立的章節資訊
        
    Raises:
        HTTPException: 當情境不存在或建立失敗時
        ValidationError: 當輸入資料驗證失敗時
    """
```

## 安全性評估

### ✅ **良好實踐**
- 權限控制完善
- 使用參數化查詢防止 SQL 注入
- 外鍵約束確保資料完整性

### ⚠️ **需改進**
- 缺少輸入清理和驗證
- 沒有速率限制保護
- 敏感操作缺少額外驗證

## 效能考量

### 現有問題
1. 列表查詢使用兩次資料庫訪問
2. 缺少索引策略說明
3. 沒有快取機制
4. 分頁查詢可能效能低下

### 改進建議
```python
# 1. 新增快取機制
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_cached_situation(situation_id: str) -> SituationResponse:
    """快取情境資料"""
    pass

# 2. 優化索引
# 在模型中新增索引
class Situation(SQLModel, table=True):
    situation_name: str = Field(index=True)  # 新增索引
    sequence: int = Field(index=True)        # 新增索引
```

## 符合性評估

### ✅ **符合 CLAUDE.md 規範**
- 使用繁體中文註解
- 函數式設計模式
- 檔案行數控制（最大 320 行）
- 型別註解（部分需修正）

### ❌ **需改進項目**
- 路由器命名規範
- 完整的文件字串格式
- 測試覆蓋率

## 立即行動建議

### 🚨 **緊急處理（24小時內）**
1. **修正型別不一致問題**：統一使用 `str` 或 `UUID` 型別
2. **修正路由器命名**：使用 `situation_router` 命名

### 📝 **短期改進（1-2週）**
1. **新增輸入驗證**：UUID 格式、時間範圍等驗證
2. **完善測試覆蓋**：新增缺失的測試檔案
3. **改善錯誤處理**：統一異常處理機制

### 🎯 **中期優化（1個月）**
1. **效能優化**：查詢優化、新增快取機制
2. **完善文件**：新增完整的 Google 風格文件字串
3. **安全增強**：新增速率限制和輸入清理

## 總結

課程模組的基礎架構良好，遵循了專案的設計原則，但在型別一致性、效能優化和測試覆蓋方面需要改進。建議優先修正關鍵問題，然後逐步完善功能和效能。整體而言，這是一個結構清晰但需要精進的模組。

---
*檢視日期：2025-08-12*
*檢視人員：Code Reviewer Agent*
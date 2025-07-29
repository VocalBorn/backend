# CLAUDE.md

**重要：在此專案中工作時，請一律使用繁體中文進行回應和說明。**

**注意: 確保調整資料結構時，與該資料庫結構有關的服務是否已正確進行處理。**

## 開發指南
### 開發流程
1. **計畫**: 請先對新功能開發或修正進行詳細計畫，如有需要可使用Context 7 MCP 去檢索資料，並將計畫記錄至 docs/plan/{計畫名稱}.md
2. **開發**：開發時應確保函數命名、程式碼結構等符合業界最佳實踐，並確保程式碼單檔案不超過 300 行原則，避免過度複雜的函數和類別。
3. **測試**：開發完成後，請不要嘗試啟動伺服器，通常伺服器會自行手動啟動，有需要的話可以請求協助。
4. **總結**：在開發完成後，請將該次開發的總結以 Git commit 的方式記錄。

### Git Commit 原則
請根據使用 Git 的最佳實踐去撰寫 commit 訊息。以下是一些常用的 commit 類型：
- `feat:` - 新功能
- `fix:` - 錯誤修復
- `test:` - 測試相關變更
- `refactor:` - 程式碼重構（不改變功能）
- `style:` - 程式碼格式調整（不影響邏輯）
- `docs:` - 文件更新
- `chore:` - 建置流程、工具等維護性變更
- `perf:` - 效能改善
- `ci:` - 持續整合設定變更

### Router 函數命名
⚠️ 尾巴的 `_router` 是 FastAPI 的路由器命名慣例，請確保在定義路由器時使用此後綴。

### 程式碼品質標準
#### 型別註解
- 所有函數參數和回傳值都必須有型別註解
- 複雜型別使用 typing 模組中的型別

```python
from typing import List, Optional, Dict, Any

async def create_user(
    user_data: UserCreate, 
    db: Session
) -> UserResponse:
    """建立新用戶"""
    # 實作內容
```

#### 文件字串規範
- 所有公開函數和類別都必須有文件字串
- 使用 Google 風格的文件字串格式
- 包含參數說明、回傳值說明和異常說明

```python
async def upload_file(file: UploadFile, bucket_name: str) -> FileInfo:
    """上傳檔案到指定的儲存桶

    Args:
        file: 要上傳的檔案物件
        bucket_name: 目標儲存桶名稱

    Returns:
        FileInfo: 包含檔案資訊的物件

    Raises:
        StorageError: 當檔案上傳失敗時
        ValidationError: 當檔案格式不正確時
    """
```

#### 除錯工具
- 使用 pdb 或 ipdb 進行除錯
- 在開發環境啟用詳細的錯誤追蹤
- 使用 FastAPI 的自動 API 文件進行 API 測試

## 常用開發指令
### 開發伺服器
```bash
# 執行開發伺服器（通常不需要使用）
uv run fastapi dev src/main.py
```

### 資料庫操作
請在使用 Alembic 進行資料庫操作時，請先 `cd alembic` 進入 alembic 目錄後，再使用以下指令：
```bash
# 套用資料庫遷移
uv run alembic upgrade head

# 建立新的遷移檔案（在模型變更後）
uv run alembic revision --autogenerate -m "描述"

# 檢查目前資料庫版本
uv run alembic current

# 查看遷移歷史
uv run alembic history

# 回退到上一個版本
uv run alembic downgrade -1

# 回退到特定版本
uv run alembic downgrade <版本號>

# 預覽將生成的 SQL（不執行）
uv run alembic upgrade head --sql
```

### 套件管理
```bash
# 新增生產相依套件
uv add package-name

# 新增開發相依套件
uv add --dev package-name

# 移除套件
uv remove package-name

# 更新套件
uv update

# 檢視已安裝套件
uv pip list
```

### 測試
```bash
# 執行所有測試
uv run pytest

# 執行特定測試檔案
uv run pytest tests/test_auth.py

# 執行測試並顯示覆蓋率（需安裝 pytest-cov）
uv run pytest --cov=src
```

## 架構概覽

這是一個基於 **FastAPI 的 REST API**，用於 VocalBorn 語言治療學習平台。該應用程式服務三種使用者類型：客戶（尋求治療者）、治療師（服務提供者）和管理員。

專案使用 **uv** 進行套件管理，提供更快速的相依性解析和安裝。

### 技術堆疊
- **Python 3.13.0** 搭配 **FastAPI**
- **SQLModel**（基於 SQLAlchemy）作為 ORM
- **PostgreSQL** 資料庫搭配 **Alembic** 遷移
- **MinIO**（S3 相容）用於檔案儲存
- **JWT** 認證搭配角色權限控制
- **uv** 套件管理工具


### 外部服務
- **MinIO**：用於文件、音訊錄音和媒體檔案的檔案儲存
- **電子郵件服務**：用於驗證和密碼重設郵件的外部 HTTP API
- **PostgreSQL**：主要資料庫

### 儲存模組
應用程式使用模組化儲存系統，支援多種檔案類型：
- **文件儲存**：用於驗證文件的 PDF、Word、圖片
- **音訊儲存**：用於練習錄音和課程音訊的 MP3、WAV、M4A
- **可擴展設計**：容易新增新的儲存類型（影片、圖片等）


## 開發指導原則

### 資料庫變更
所有資料庫結構修改都必須透過 Alembic 遷移進行（指令請見上面 **資料庫操作** ）：
1. 修改程式碼中的 SQLModel 定義（並檢查 env.py 是否有導入模型）
2. 產生遷移
3. 檢查產生的遷移檔案（在 alembic/versions/ 目錄下）確保正確性
4. 套用變更


### 服務設計指導原則

#### 設計模式選擇

**使用函數式設計（預設選擇）**：
- 簡單的 CRUD 操作
- 無狀態的業務邏輯處理
- 資料驗證和轉換
- 單純的輸入輸出處理

**使用類別式設計（特殊情況）**：
- 需要維護連線狀態（如資料庫連線、外部服務連線）
- 複雜的配置管理
- 需要繼承和多態
- 封裝複雜狀態的服務


#### 測試指導原則

**函數式服務測試**：
```python
@pytest.mark.asyncio
async def test_service_function():
    # 準備測試資料
    mock_db = Mock()
    test_data = create_test_data()
    
    # 執行測試
    result = await service_function(test_data, mock_db)
    
    # 驗證結果
    assert result.status == "success"
```

**類別式服務測試**：
```python
def test_service_class():
    # 建立服務實例
    service = ServiceClass(mock_dependency)
    
    # 執行測試
    result = service.service_method(test_data)
    
    # 驗證結果
    assert result.is_valid()
```

## 應用程式領域
應用程式遵循模組化路由器架構，在認證、業務邏輯和資料存取層之間有清楚的關注點分離。
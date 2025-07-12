# CLAUDE.md

本文件為 Claude Code (claude.ai/code) 在此程式碼庫中工作時提供指導。

## 開發指南

### 測試指導原則

### Git Commit 原則

#### Conventional Commits 規範
使用以下格式進行 commit：
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

#### Commit 類型
- `feat:` - 新功能
- `fix:` - 錯誤修復
- `test:` - 測試相關變更
- `refactor:` - 程式碼重構（不改變功能）
- `style:` - 程式碼格式調整（不影響邏輯）
- `docs:` - 文件更新
- `chore:` - 建置流程、工具等維護性變更
- `perf:` - 效能改善
- `ci:` - 持續整合設定變更

#### Commit 範例
```bash
feat(auth): 新增雙因子認證功能
fix(storage): 修復檔案上傳失敗的問題
test(course): 新增課程內容驗證測試
refactor(database): 重構資料庫連線管理
docs(api): 更新 API 文件和範例
```

#### 分支管理策略
- `main` - 主要分支，隨時可部署的穩定版本
- `develop` - 開發分支，整合各功能分支
- `feature/*` - 功能分支，例如 `feature/user-authentication`
- `fix/*` - 錯誤修復分支，例如 `fix/login-validation`
- `refactor/*` - 重構分支，例如 `refactor/storage-service`

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

### 開發流程

#### 功能開發流程
1. **建立功能分支**：從 `develop` 分支建立新的功能分支
2. **編寫測試**：先寫測試，再實作功能（TDD 方式）
3. **實作功能**：按照設計文件實作功能
4. **執行測試**：確保所有測試通過
5. **程式碼檢查**：執行 linting 和型別檢查
6. **建立 Pull Request**：向 `develop` 分支提交 PR
7. **程式碼審查**：等待同事審查並處理回饋
8. **合併分支**：審查通過後合併到 `develop`

#### 發布流程
1. **建立發布分支**：從 `develop` 建立 `release/*` 分支
2. **最終測試**：執行完整的測試套件
3. **版本標記**：更新版本號並建立 git tag
4. **合併到主分支**：將發布分支合併到 `main`
5. **部署**：將 `main` 分支部署到生產環境

### 除錯和日誌

#### 日誌標準
- 使用 Python logging 模組
- 設定適當的日誌級別（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 在關鍵操作點加入日誌記錄

```python
import logging

logger = logging.getLogger(__name__)

async def process_payment(payment_data: PaymentData):
    logger.info(f"開始處理付款，訂單 ID: {payment_data.order_id}")
    try:
        # 處理邏輯
        logger.info(f"付款處理成功，訂單 ID: {payment_data.order_id}")
    except PaymentError as e:
        logger.error(f"付款處理失敗，訂單 ID: {payment_data.order_id}，錯誤: {e}")
        raise
```

#### 除錯工具
- 使用 pdb 或 ipdb 進行除錯
- 在開發環境啟用詳細的錯誤追蹤
- 使用 FastAPI 的自動 API 文件進行 API 測試

## 語言指導原則

**重要：在此專案中工作時，請一律使用繁體中文進行回應和說明。**

所有的回應、錯誤訊息、說明文字和註解都應該使用繁體中文，以確保與團隊的溝通一致性。

## 常用開發指令

### 環境設定
```bash
# 建立虛擬環境
python -m venv venv

# 進入虛擬環境
source venv/bin/activate  

# 安裝相依套件
pip install -r requirements.txt

# 新增套件後更新 requirements
pip freeze > requirements.txt
```

### 開發伺服器
```bash
# 執行開發伺服器
fastapi dev src/main.py
```

### 資料庫操作
```bash
# 套用資料庫遷移
alembic upgrade head

# 建立新的遷移檔案（在模型變更後）
alembic revision --autogenerate -m "描述"

# 檢查目前資料庫版本
alembic current

# 查看遷移歷史
alembic history

# 回退到上一個版本
alembic downgrade -1
```

### Docker
```bash
# 執行容器化應用程式
docker run -d -p 5001:5000 vocalborn_backend
```

## 架構概覽

這是一個基於 **FastAPI 的 REST API**，用於 VocalBorn 語言治療學習平台。該應用程式服務三種使用者類型：客戶（尋求治療者）、治療師（服務提供者）和管理員。

### 技術堆疊
- **Python 3.13.0** 搭配 **FastAPI**
- **SQLModel**（基於 SQLAlchemy）作為 ORM
- **PostgreSQL** 資料庫搭配 **Alembic** 遷移
- **MinIO**（S3 相容）用於檔案儲存
- **JWT** 認證搭配角色權限控制

### 核心應用程式結構

```
src/
├── main.py              # 應用程式進入點
├── auth/                # 認證與使用者管理
├── therapist/           # 治療師註冊與驗證
├── course/              # 課程內容與練習階段
├── pairing/             # 治療師-客戶配對系統
├── verification/        # 文件驗證工作流程
├── chat/                # 聊天功能
├── storage/             # 檔案儲存服務
│   ├── storage_service.py      # 基礎儲存服務
│   ├── audio_storage_service.py # 音訊檔案儲存
│   ├── storage_factory.py      # 儲存服務工廠
│   └── practice_recording_service.py # 練習錄音邏輯
└── shared/              # 共用工具
    ├── config/          # 環境配置
    ├── database/        # 資料庫連線設定
    ├── services/        # 電子郵件與其他服務
    └── schemas/         # 共用 schema 定義
```

### 資料庫架構

應用程式使用關聯式資料庫，包含以下主要實體：
- **使用者系統**：`accounts`、`users`、`email_verifications`
- **治療師工作流程**：`therapist_profiles`、`therapist_applications`、`uploaded_documents`
- **課程內容**：`situations`、`chapters`、`sentences`、`practice_records`
- **配對系統**：`pairing_tokens`、`therapist_clients`

### 外部服務
- **MinIO**：用於文件、音訊錄音和媒體檔案的檔案儲存
- **電子郵件服務**：用於驗證和密碼重設郵件的外部 HTTP API
- **PostgreSQL**：主要資料庫

### 儲存模組
應用程式使用模組化儲存系統，支援多種檔案類型：
- **文件儲存**：用於驗證文件的 PDF、Word、圖片
- **音訊儲存**：用於練習錄音和課程音訊的 MP3、WAV、M4A
- **可擴展設計**：容易新增新的儲存類型（影片、圖片等）

儲存服務按用途組織：
- `get_verification_storage()` - 文件驗證檔案
- `get_practice_recording_storage()` - 使用者練習錄音
- `get_course_audio_storage()` - 課程音訊內容
- `practice_recording_service` - 高階練習錄音操作

### 測試
**未完成**

## 開發指導原則

### 資料庫變更
所有資料庫結構修改都必須透過 Alembic 遷移進行：
1. 修改程式碼中的 SQLModel 定義
2. 產生遷移：`alembic revision --autogenerate -m "描述"`
3. 檢查產生的遷移檔案
4. 套用變更：`alembic upgrade head`

### 環境配置
- 從 Notion 載入 `.env` 檔案（如 README 中指定）
- 配置透過 `src/shared/config/config.py` 管理
- 資料庫連線設定位於 `src/shared/database/database.py`

### 服務設計指導原則

#### 設計模式選擇

**使用函數式設計（預設選擇）**：
- 簡單的 CRUD 操作
- 無狀態的業務邏輯處理
- 資料驗證和轉換
- 單純的輸入輸出處理

```python
# ✅ 函數式設計範例
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """建立新用戶"""
    # 驗證資料
    # 建立用戶
    # 返回結果
    
async def validate_email(email: str) -> bool:
    """驗證電子郵件格式"""
    # 純粹的驗證邏輯
```

**使用類別式設計（特殊情況）**：
- 需要維護連線狀態（如資料庫連線、外部服務連線）
- 複雜的配置管理
- 需要繼承和多態
- 封裝複雜狀態的服務

```python
# ✅ 類別式設計範例
class StorageService:
    """檔案儲存服務 - 需要維護 MinIO 客戶端連線"""
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client = self._initialize_client()
    
class EmailService:
    """電子郵件服務 - 複雜的重試邏輯和配置管理"""
    def __init__(self, config: EmailConfig):
        self.config = config
        self.retry_strategy = RetryStrategy()
```

#### 錯誤處理標準

**函數式服務**：
```python
async def service_function(data: InputData) -> OutputData:
    try:
        # 業務邏輯
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="資料庫操作失敗")
```

**類別式服務**：
```python
class ServiceClass:
    def service_method(self, data: InputData) -> OutputData:
        try:
            # 業務邏輯
            return result
        except ServiceSpecificError as e:
            logger.error(f"服務錯誤: {e}")
            raise ServiceError(f"操作失敗: {e}")
```

#### 相依性注入

**函數式服務 - 使用 FastAPI Depends**：
```python
async def service_function(
    data: InputData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 業務邏輯
```

**類別式服務 - 建構子注入**：
```python
class ServiceClass:
    def __init__(self, dependency: DependencyType):
        self.dependency = dependency

# 使用工廠函數
def get_service() -> ServiceClass:
    return ServiceClass(get_dependency())
```

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

### Commit 慣例
使用傳統 commit 格式：
- `feat:` - 新功能
- `fix:` - 錯誤修復
- `test:` - 測試變更
- `refactor:` - 程式碼重構
- `style:` - 格式調整
- `docs:` - 文件更新
- `chore:` - 建置流程、工具等

## 應用程式領域

VocalBorn 透過以下方式連接語言治療師與客戶：
1. **使用者註冊**：所有使用者類型的電子郵件驗證工作流程
2. **治療師驗證**：文件上傳和管理員審核流程
3. **課程結構**：階層式內容（情境 → 章節 → 句子）
4. **練習階段**：音訊錄音和回饋系統
5. **配對系統**：基於權杖的治療師-客戶配對
6. **文件管理**：安全的檔案儲存和檢索

應用程式遵循模組化路由器架構，在認證、業務邏輯和資料存取層之間有清楚的關注點分離。
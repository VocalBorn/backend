# CLAUDE.md

**重要：在此專案中工作時，請一律使用繁體中文進行回應和說明。**

**注意: 確保調整資料結構時，與該資料庫結構有關的服務是否已正確進行處理。**


## 架構概覽
這是一個基於 **FastAPI 的 REST API**，用於 VocalBorn 語言治療學習平台。該應用程式服務三種使用者類型：客戶（尋求治療者）、治療師（服務提供者）和管理員。

專案使用 **uv** 進行套件管理，提供更快速的相依性解析和安裝。
執行 Python 檔案時，請完全使用 **uv** 執行：


### Git Commit 原則
請根據使用 Git 的最佳實踐去撰寫 commit 訊息。以下是一些常用的 commit 類型：

### Router 函數命名
⚠️ 尾巴的 `_router` 是 FastAPI 的路由器命名慣例，請確保在定義路由器時使用此後綴。

### 程式碼品質標準
#### 型別註解
- 所有函數參數和回傳值都必須有型別註解
- 複雜型別使用 typing 模組中的型別


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

```

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



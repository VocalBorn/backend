# 後端 Backend
Python 版本為 3.13.0

專案使用 [uv](https://github.com/astral-sh/uv) 進行套件管理，提供更快速的相依性解析和安裝。

## ⚠️ 重要：請務必去 Notion 中載入最新的 .env 檔案

## 環境設定

### 安裝 uv
```bash
# macOS 使用 Homebrew 安裝（推薦）
brew install uv

# 或使用 curl 安裝
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 初始化專案環境
```bash
# 同步並安裝所有相依套件
uv sync

# 或進入虛擬環境
uv shell
```

### 啟動開發伺服器
```bash
uv run fastapi dev src/main.py
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
### 如何執行docker
```bash
# 建立 Docker 映像檔
docker build -t vocalborn_backend .

# 執行 Docker 容器
docker run -d -p 5001:5000 vocalborn_backend
```
## 編輯Draw.io 檔案
在VSCode中安裝Draw.io Integration套件，並開啟drawio檔案

## 資料庫版本控制
使用 Alembic 進行資料庫版本控制。本專案完全依賴 Alembic 來管理資料庫結構的變更，以確保所有變更都被正確追蹤和版本控制。

### 新開發環境設置
1. 確保已正確設定 `.env` 檔案中的資料庫連接資訊
2. 執行遷移以建立資料庫結構：
```bash
uv run alembic upgrade head
```

### 資料庫變更流程
當需要修改資料庫結構時（如新增表格、修改欄位等），請遵循以下步驟：

1. 在程式碼中修改 SQLModel 模型定義（models.py），並檢查 env.py 是否有導入模型
2. 生成新的遷移檔：
```bash
uv run alembic revision --autogenerate -m "描述變更內容"
```
3. 檢查生成的遷移檔案（在 alembic/versions/ 目錄下）確保正確性
4. 應用變更：
```bash
uv run alembic upgrade head
```

### 常用指令參考
```bash
# 查看目前版本
uv run alembic current

# 檢視遷移歷史
uv run alembic history

# 回滾到上一個版本
uv run alembic downgrade -1

# 回滾到特定版本
uv run alembic downgrade <版本號>

# 預覽將生成的 SQL（不執行）
uv run alembic upgrade head --sql
```

### 注意事項
- 所有資料庫結構變更都必須通過 Alembic 遷移來進行
- 遷移檔案應該被加入版本控制系統
- 建議在提交程式碼前先在本地測試遷移是否能正常運作

## 測試
```bash
# 執行所有測試
uv run pytest

# 執行特定測試檔案
uv run pytest tests/test_auth.py

# 執行測試並顯示覆蓋率（需安裝 pytest-cov）
uv run pytest --cov=src
```

## 程式碼品質檢查
```bash
# 程式碼格式化（需先安裝 black）
uv add --dev black
uv run black src/

# 型別檢查（需先安裝 mypy）
uv add --dev mypy
uv run mypy src/

# 程式碼風格檢查（需先安裝 flake8）
uv add --dev flake8
uv run flake8 src/
```

## Conventional Commits：
- feat: 新功能
- fix: 修復 bug
- test: 新增或修正測試
- refactor: 程式碼重構，不改變外部行為
- style: 不影響程式碼含義的變化（如格式化）
- docs: 文件相關變更
- chore: 其他變更（如建構過程、輔助工具等）
## 參考來源
- [FastAPI](https://fastapi.tiangolo.com/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [fastapi-sqlmodel](https://github.com/anthonycepeda/fastapi-sqlmodel)

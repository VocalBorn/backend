# 後端 Backend
Python 版本為 3.13.0
## ⚠️ 重要：請務必去 Notion 中載入最新的 .env 檔案

## 環境設定
### 建立虛擬環境
```
python -m venv venv
```
或使用 VSCode 的虛擬環境
### 安裝套件
```
pip install -r requirements.txt
```
### 啟動開發伺服器
```
fastapi dev src/main.py
```
### 如何將新增的套件加入 requirements.txt
```
pip freeze > requirements.txt
```
### 如何執行docker
```
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
alembic upgrade head
```

### 資料庫變更流程
當需要修改資料庫結構時（如新增表格、修改欄位等），請遵循以下步驟：

1. 在程式碼中修改 SQLModel 模型定義（models.py），並檢查 env.py 是否有導入模型
2. 生成新的遷移檔：
```bash
alembic revision --autogenerate -m "描述變更內容"
```
3. 檢查生成的遷移檔案（在 alembic/versions/ 目錄下）確保正確性
4. 應用變更：
```bash
alembic upgrade head
```

### 常用指令參考
```bash
# 查看目前版本
alembic current

# 檢視遷移歷史
alembic history

# 回滾到上一個版本
alembic downgrade -1

# 回滾到特定版本
alembic downgrade <版本號>

# 預覽將生成的 SQL（不執行）
alembic upgrade head --sql
```

### 注意事項
- 所有資料庫結構變更都必須通過 Alembic 遷移來進行
- 遷移檔案應該被加入版本控制系統
- 建議在提交程式碼前先在本地測試遷移是否能正常運作

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

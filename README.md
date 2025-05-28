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
使用 Alembic 進行資料庫版本控制，請參考以下指令：
### 初始化 Alembic
```
alembic init alembic
```
### 建立新的遷移檔
```
alembic revision --autogenerate -m "描述"
```
### 執行遷移
```
alembic upgrade head
```
### 回滾遷移
```
alembic downgrade -1
```
### 查看目前版本
```
alembic current
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
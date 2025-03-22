# 後端 Backend
Python 版本為 3.13.0
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
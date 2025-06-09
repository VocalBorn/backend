from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.auth.admin_router import router as admin_router
from src.course.router import router as course_router

# 系統啟動時建立資料庫連線
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

api_description = """
## VocalBorn 語音復健學習系統 API

這是一個專為語音復健設計的學習系統，提供完整的用戶管理、課程管理和學習進度追蹤功能。

### 主要功能

* **用戶管理**: 註冊、登入、個人資料管理
* **權限系統**: 管理員、語言治療師、一般用戶三種角色
* **課程管理**: 情境、章節、語句的完整管理
* **學習追蹤**: 練習記錄和進度追蹤

"""

app = FastAPI(
    title="VocalBorn API",
    description=api_description,
    version="1.0.0",
    contact={
        "name": "VocalBorn 開發團隊",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "開發環境"
        },
        {
            "url": "https://api.vocalborn.com",
            "description": "生產環境"
        }
    ],
    tags_metadata=[
        {
            "name": "users",
            "description": "用戶認證和個人資料管理相關操作",
        },
        {
            "name": "管理員",
            "description": "管理員專用功能，包含用戶管理和權限控制",
        },
        {
            "name": "situations",
            "description": "學習情境、章節和語句的管理",
        }
    ],
    lifespan=lifespan
)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(course_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return 'Hello, World!'


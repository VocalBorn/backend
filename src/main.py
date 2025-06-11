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



app = FastAPI(
    title="VocalBorn API",
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
            "url": "https://api-vocalborn.r0930514.work",
            "description": "生產環境"
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


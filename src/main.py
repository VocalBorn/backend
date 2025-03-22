from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.auth import router as auth_router
from src.database import create_db_and_tables

# 系統啟動時建立資料庫連線
@asynccontextmanager
async def lifespan(app: FastAPI):
  create_db_and_tables()
  yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router.router)

@app.get('/')
def root():
  return 'Hello, World!'

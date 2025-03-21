from contextlib import asynccontextmanager
from fastapi import FastAPI

from .auth import router
from src.database import Database
db = Database()

# 系統啟動時建立資料庫連線
@asynccontextmanager
async def lifespan(app: FastAPI):
  db.create_db_and_tables()
  yield
  db.engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(router.router)

@app.get('/')
def root():
  return 'Hello, World!'

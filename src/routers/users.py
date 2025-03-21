from fastapi import APIRouter

from src.utils.database import Database

router = APIRouter(
  prefix='/user',
  tags=['users'], 
  dependencies=[],
)

# 註冊
@router.post('/register')
async def register():
  return 'Register'

# 登入
@router.post('/login')
async def login():
  return 'Login'



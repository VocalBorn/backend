from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.auth.schemas import RegisterRequest
from src.auth.service import account_register
from src.database import get_session

router = APIRouter(
  prefix='/user',
  tags=['users'], 
  dependencies=[],
)

# 註冊
@router.post('/register')
async def register(
  request: RegisterRequest, 
  session: Annotated[Session, Depends(get_session)]
):
  return await account_register(request, session)

# 登入
@router.post('/login')
async def login():
  return 'Login'



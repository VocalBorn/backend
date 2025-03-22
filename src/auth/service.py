import os
from fastapi import HTTPException
from sqlmodel import Session, select
from src.auth.models import Account, User
from src.auth.schemas import RegisterRequest

# Global variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

async def account_register(request: RegisterRequest, session: Session) -> Account:
  existing_user = session.exec(select(Account).where(Account.email == request.email)).first()    
  if existing_user:
    raise HTTPException(
      status_code=400,
      detail="Email already registered"
    )
  # Create new account and user in a transaction
  try:
    # Create new account
    new_account = Account(email=request.email, password=request.password)
    session.add(new_account)
    session.flush()  # Flush to get the account_id without committing
    
    # Create new user
    new_user = User(
      account_id=new_account.account_id,
      name=request.name,
      gender=request.gender,
      age=request.age,
    )
    session.add(new_user)
    
    # Commit the transaction
    session.commit()
    session.refresh(new_user)
    return new_user
  except Exception as e:
    session.rollback()
    raise HTTPException(
      status_code=500,
      detail=f"Failed to register user: {str(e)}"
    )

import datetime
from typing import Optional, List
import uuid
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

class EmailVerification(SQLModel, table=True):
    __tablename__ = "email_verifications"
    verification_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    account_id: uuid.UUID = Field(foreign_key="accounts.account_id", nullable=False)
    token: str = Field(nullable=False, unique=True)
    expiry: datetime.datetime = Field(nullable=False)
    is_used: bool = Field(default=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    account: "Account" = Relationship(back_populates="verifications")

class Account(SQLModel, table=True):
    __tablename__ = "accounts"
    account_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, max_length=255)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    is_verified: bool = Field(default=False)
    user: Optional["User"] = Relationship(back_populates="account")
    verifications: List[EmailVerification] = Relationship(back_populates="account")
  
class User(SQLModel, table=True):
  __tablename__ = "users"
  user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
  account_id: uuid.UUID = Field(foreign_key="accounts.account_id", nullable=False, unique=True)
  name: str = Field(nullable=False, max_length=100)
  gender: Optional[str] = Field(max_length=10)
  age: Optional[int] = Field(default=None)
  phone: Optional[str] = Field(max_length=20)
  created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
  updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
  account: Optional[Account] = Relationship(back_populates="user")

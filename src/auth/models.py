import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
import uuid
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from src.practice.models import PracticeRecord, PracticeSession
from src.therapist.models import TherapistProfile, TherapistClient

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"
    THERAPIST = "therapist"

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
    role: UserRole = Field(default=UserRole.CLIENT, nullable=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    account: Account = Relationship(back_populates="user")
    practice_sessions: List["PracticeSession"] = Relationship(back_populates="user")
    # 治療師檔案（僅治療師角色有此關聯）
    therapist_profile: Optional["TherapistProfile"] = Relationship(back_populates="user")
    # 治療師的客戶列表
    assigned_clients: List["TherapistClient"] = Relationship(
        back_populates="therapist",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.therapist_id]"}
    )
    # 客戶的治療師列表
    assigned_therapists: List["TherapistClient"] = Relationship(
        back_populates="client",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.client_id]"}
    )
    # 用戶常用詞彙
    user_words: List["UserWord"] = Relationship(back_populates="user")


class UserWord(SQLModel, table=True):
    """使用者常用詞彙表"""
    __tablename__ = "user_words"
    
    word_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id")
    content: str = Field(nullable=False)
    location: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    user: "User" = Relationship(back_populates="user_words")

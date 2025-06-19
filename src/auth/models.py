import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
import uuid
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from src.course.models import PracticeRecord

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"
    THERAPIST = "therapist"

class PairingRequestStatus(str, Enum):
    PENDING = "pending"      # 待處理
    ACCEPTED = "accepted"    # 已接受
    REJECTED = "rejected"    # 已拒絕
    EXPIRED = "expired"      # 已過期

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
    practice_records: List["PracticeRecord"] = Relationship(back_populates="user")
    # 用戶常用詞彙
    user_words: List["UserWord"] = Relationship(back_populates="user")
    # 配對請求相關
    sent_pairing_requests: List["PairingRequest"] = Relationship(
        back_populates="requester",
        sa_relationship_kwargs={"foreign_keys": "[PairingRequest.requester_id]"}
    )
    received_pairing_requests: List["PairingRequest"] = Relationship(
        back_populates="target",
        sa_relationship_kwargs={"foreign_keys": "[PairingRequest.target_id]"}
    )
    # 如果用戶是治療師，則有客戶列表
    clients: List["TherapistClient"] = Relationship(
        back_populates="therapist",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.therapist_id]"}
    )
    # 如果用戶是客戶，則有治療師列表
    therapists: List["TherapistClient"] = Relationship(
        back_populates="client",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.client_id]"}
    )

# class TherapistClient(SQLModel, table=True):
#     """治療師和客戶的多對多關係表"""
#     __tablename__ = "therapist_clients"
    
#     id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
#     therapist_id: uuid.UUID = Field(foreign_key="users.user_id")
#     client_id: uuid.UUID = Field(foreign_key="users.user_id")
#     created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
#     # Relationships
#     therapist: "User" = Relationship(
#         back_populates="clients", 
#         sa_relationship_kwargs={"primaryjoin": "User.user_id==TherapistClient.therapist_id"}
#     )
#     client: "User" = Relationship(
#         back_populates="therapists", 
#         sa_relationship_kwargs={"primaryjoin": "User.user_id==TherapistClient.client_id"}
#     )

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

class PairingRequest(SQLModel, table=True):
    """配對請求表"""
    __tablename__ = "pairing_requests"
    
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    requester_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)  # 發起者
    target_id: Optional[uuid.UUID] = Field(foreign_key="users.user_id", default=None)  # 目標用戶（可為空）
    token: str = Field(nullable=False, unique=True, index=True)  # 配對token
    status: PairingRequestStatus = Field(default=PairingRequestStatus.PENDING)
    expires_at: datetime.datetime = Field(nullable=False)  # token過期時間
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    requester: "User" = Relationship(
        back_populates="sent_pairing_requests",
        sa_relationship_kwargs={"foreign_keys": "[PairingRequest.requester_id]"}
    )
    target: Optional["User"] = Relationship(
        back_populates="received_pairing_requests",
        sa_relationship_kwargs={"foreign_keys": "[PairingRequest.target_id]"}
    )

class TherapistClient(SQLModel, table=True):
    """治療師和客戶的多對多關係表"""
    __tablename__ = "therapist_clients"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    client_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    paired_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    is_active: bool = Field(default=True)  # 是否為活躍關係
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # 確保同一對治療師-客戶只能配對一次
    __table_args__ = (UniqueConstraint('therapist_id', 'client_id', name='unique_therapist_client'),)
    
    # Relationships
    therapist: "User" = Relationship(
        back_populates="clients",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.therapist_id]"}
    )
    client: "User" = Relationship(
        back_populates="therapists",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.client_id]"}
    )

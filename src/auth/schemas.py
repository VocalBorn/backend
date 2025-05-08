from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from datetime import datetime

from src.auth.models import UserRole

def validate_password_rules(password: str) -> str:
    """
    驗證密碼是否符合規則：
    - 至少包含一個大寫字母
    - 至少包含一個小寫字母
    - 至少包含一個數字
    - 至少包含一個特殊字符
    """
    if not any(c.isupper() for c in password):
        raise ValueError('密碼必須包含至少一個大寫字母')
    if not any(c.islower() for c in password):
        raise ValueError('密碼必須包含至少一個小寫字母')
    if not any(c.isdigit() for c in password):
        raise ValueError('密碼必須包含至少一個數字')
    if not any(c in '!@#$%^&*()' for c in password):
        raise ValueError('密碼必須包含至少一個特殊字符(!@#$%^&*())')
    return password

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=100)
    gender: Gender
    age: int = Field(..., ge=0, le=150)

    @field_validator('password', mode='before')
    def validate_password(cls, password: str):
        return validate_password_rules(password)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)

    @field_validator('password', mode='before')
    def validate_password(cls, password: str):
        return validate_password_rules(password)

class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[Gender] = None

class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password', mode='before')
    def validate_password(cls, password: str):
        return validate_password_rules(password)

class AccountCreate(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "example@gmail.com",
                "password": "your-password"
            }
        }

class AccountLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "example@gmail.com",
                "password": "your-password"
            }
        }

class AccountResponse(BaseModel):
    account_id: UUID
    email: str
    created_at: datetime
    updated_at: datetime
    is_verified: bool

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "example@gmail.com",
                "created_at": "2025-05-01T06:03:56.458985",
                "updated_at": "2025-05-01T06:03:56.459284",
                "is_verified": True
            }
        }

class UserCreate(BaseModel):
    name: str
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.CLIENT

    class Config:
        json_schema_extra = {
            "example": {
                "name": "王小明",
                "gender": "男",
                "age": 25,
                "phone": "0912345678",
                "role": "client"
            }
        }

class UserUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "王大明",
                "gender": "男",
                "age": 26,
                "phone": "0912345678",
                "role": "client"
            }
        }

class UserResponse(BaseModel):
    user_id: UUID
    account_id: UUID
    name: str
    gender: Optional[str]
    age: Optional[int]
    phone: Optional[str]
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "王小明",
                "gender": "男",
                "age": 25,
                "phone": "0912345678",
                "role": "client",
                "created_at": "2025-05-01T06:03:56.458985",
                "updated_at": "2025-05-01T06:03:56.459284"
            }
        }

class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "users": [{
                    "user_id": "550e8400-e29b-41d4-a716-446655440001",
                    "account_id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "王小明",
                    "gender": "男",
                    "age": 25,
                    "phone": "0912345678",
                    "role": "client",
                    "created_at": "2025-05-01T06:03:56.458985",
                    "updated_at": "2025-05-01T06:03:56.459284"
                }]
            }
        }

class TherapistClientCreate(BaseModel):
    client_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "550e8400-e29b-41d4-a716-446655440002"
            }
        }

class TherapistClientResponse(BaseModel):
    id: UUID
    therapist_id: UUID
    client_id: UUID
    created_at: datetime
    
    # 包含用戶基本信息，便於前端直接使用
    client_info: Optional[Dict[str, Any]] = None
    therapist_info: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "therapist_id": "550e8400-e29b-41d4-a716-446655440001",
                "client_id": "550e8400-e29b-41d4-a716-446655440002",
                "created_at": "2025-05-01T06:03:56.458985",
                "client_info": {
                    "name": "林小華",
                    "gender": "女",
                    "age": 30
                },
                "therapist_info": {
                    "name": "陳醫師",
                    "gender": "男"
                }
            }
        }

class TherapistClientListResponse(BaseModel):
    total: int
    therapist_clients: List[TherapistClientResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "therapist_clients": [{
                    "id": "550e8400-e29b-41d4-a716-446655440003",
                    "therapist_id": "550e8400-e29b-41d4-a716-446655440001",
                    "client_id": "550e8400-e29b-41d4-a716-446655440002",
                    "created_at": "2025-05-01T06:03:56.458985",
                    "client_info": {
                        "name": "林小華",
                        "gender": "女",
                        "age": 30
                    },
                    "therapist_info": {
                        "name": "陳醫師",
                        "gender": "男"
                    }
                }]
            }
        }

class UserWordCreate(BaseModel):
    content: str
    location: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "content": "餐廳",
                "location": "台北市信義區"
            }
        }

class UserWordUpdate(BaseModel):
    content: Optional[str] = None
    location: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "content": "高級餐廳",
                "location": "台北市信義區101大樓"
            }
        }

class UserWordResponse(BaseModel):
    word_id: UUID
    user_id: UUID
    content: str
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "word_id": "550e8400-e29b-41d4-a716-446655440004",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "content": "餐廳",
                "location": "台北市信義區",
                "created_at": "2025-05-01T06:03:56.458985",
                "updated_at": "2025-05-01T06:03:56.459284"
            }
        }

class UserWordListResponse(BaseModel):
    total: int
    user_words: List[UserWordResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "user_words": [{
                    "word_id": "550e8400-e29b-41d4-a716-446655440004",
                    "user_id": "550e8400-e29b-41d4-a716-446655440001",
                    "content": "餐廳",
                    "location": "台北市信義區",
                    "created_at": "2025-05-01T06:03:56.458985",
                    "updated_at": "2025-05-01T06:03:56.459284"
                }]
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

class EmailVerificationCreate(BaseModel):
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "example@gmail.com"
            }
        }

class EmailVerificationConfirm(BaseModel):
    token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "123456"
            }
        }

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

# 管理員相關 Schema
class UpdateUserRoleRequest(BaseModel):
    role: UserRole
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "therapist"
            }
        }

class DeleteUserRequest(BaseModel):
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "password": "admin_password"
            }
        }

class PermissionResponse(BaseModel):
    role: UserRole
    permissions: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "client",
                "permissions": [
                    "view_courses",
                    "view_practice_records",
                    "create_practice_records",
                    "chat_with_therapist"
                ]
            }
        }

class UserStatsResponse(BaseModel):
    total_users: int
    clients: int
    therapists: int
    admins: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 100,
                "clients": 80,
                "therapists": 15,
                "admins": 5
            }
        }

# 治療師檔案相關 Schema
class TherapistProfileCreate(BaseModel):
    license_number: str = Field(..., min_length=5, max_length=50)
    specialization: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=1000)
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "license_number": "TH123456",
                "specialization": "語言治療",
                "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
                "years_experience": 5,
                "education": "國立陽明交通大學語言治療學系碩士"
            }
        }

class TherapistProfileUpdate(BaseModel):
    license_number: Optional[str] = Field(None, min_length=5, max_length=50)
    specialization: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=1000)
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "specialization": "兒童語言治療",
                "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
                "years_experience": 6
            }
        }

class TherapistProfileResponse(BaseModel):
    profile_id: UUID
    user_id: UUID
    license_number: str
    specialization: Optional[str]
    bio: Optional[str]
    years_experience: Optional[int]
    education: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440005",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "license_number": "TH123456",
                "specialization": "語言治療",
                "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
                "years_experience": 5,
                "education": "國立陽明交通大學語言治療學系碩士",
                "created_at": "2025-05-01T06:03:56.458985",
                "updated_at": "2025-05-01T06:03:56.459284"
            }
        }

# 增強的用戶回應 Schema，包含治療師檔案
class UserWithProfileResponse(BaseModel):
    user_id: UUID
    account_id: UUID
    name: str
    gender: Optional[str]
    age: Optional[int]
    phone: Optional[str]
    role: UserRole
    created_at: datetime
    updated_at: datetime
    therapist_profile: Optional[TherapistProfileResponse] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "account_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "陳醫師",
                "gender": "男",
                "age": 35,
                "phone": "0912345678",
                "role": "therapist",
                "created_at": "2025-05-01T06:03:56.458985",
                "updated_at": "2025-05-01T06:03:56.459284",
                "therapist_profile": {
                    "profile_id": "550e8400-e29b-41d4-a716-446655440005",
                    "user_id": "550e8400-e29b-41d4-a716-446655440001",
                    "license_number": "TH123456",
                    "specialization": "語言治療",
                    "bio": "專精於兒童語言發展治療。",
                    "years_experience": 5,
                    "education": "國立陽明交通大學語言治療學系碩士",
                    "created_at": "2025-05-01T06:03:56.458985",
                    "updated_at": "2025-05-01T06:03:56.459284"
                }
            }
        }

# 治療師申請成為治療師的 Schema
class TherapistApplicationRequest(BaseModel):
    license_number: str = Field(..., min_length=5, max_length=50)
    specialization: str = Field(..., min_length=2, max_length=200)
    bio: str = Field(..., min_length=10, max_length=1000)
    years_experience: int = Field(..., ge=0, le=50)
    education: str = Field(..., min_length=5, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "license_number": "TH123456",
                "specialization": "語言治療",
                "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
                "years_experience": 5,
                "education": "國立陽明交通大學語言治療學系碩士"
            }
        }

from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

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
        if not any(c.isupper() for c in password):
            raise ValueError('密碼必須包含至少一個大寫字母')
        if not any(c.islower() for c in password):
            raise ValueError('密碼必須包含至少一個小寫字母')
        if not any(c.isdigit() for c in password):
            raise ValueError('密碼必須包含至少一個數字')
        if not any(c in '!@#$%^&*()' for c in password):
            raise ValueError('密碼必須包含至少一個特殊字符(!@#$%^&*())')
        return password

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
        if not any(c.isupper() for c in password):
            raise ValueError('密碼必須包含至少一個大寫字母')
        if not any(c.islower() for c in password):
            raise ValueError('密碼必須包含至少一個小寫字母')
        if not any(c.isdigit() for c in password):
            raise ValueError('密碼必須包含至少一個數字')
        if not any(c in '!@#$%^&*()' for c in password):
            raise ValueError('密碼必須包含至少一個特殊字符(!@#$%^&*())')
        return password
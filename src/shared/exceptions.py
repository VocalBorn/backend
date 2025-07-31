"""
統一異常處理
提供一致的錯誤處理機制
"""

from fastapi import HTTPException, status
from typing import Optional


class ServiceException(HTTPException):
    """
    服務層統一異常基類
    
    提供一致的錯誤處理，確保錯誤訊息和狀態碼的一致性
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)


class NotFoundError(ServiceException):
    """資源不存在異常"""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class UnauthorizedError(ServiceException):
    """未授權異常"""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(ServiceException):
    """權限不足異常"""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationError(ServiceException):
    """資料驗證異常"""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ConflictError(ServiceException):
    """資源衝突異常"""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_409_CONFLICT)


class DatabaseError(ServiceException):
    """資料庫操作異常"""
    
    def __init__(self, message: str = "資料庫操作失敗"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


# 便利函數：根據情境選擇適當的異常類型
def raise_not_found(message: str) -> None:
    """拋出404異常"""
    raise NotFoundError(message)


def raise_forbidden(message: str) -> None:
    """拋出403異常"""
    raise ForbiddenError(message)


def raise_unauthorized(message: str) -> None:
    """拋出401異常"""
    raise UnauthorizedError(message)


def raise_validation_error(message: str) -> None:
    """拋出422異常"""
    raise ValidationError(message)


def raise_conflict(message: str) -> None:
    """拋出409異常"""
    raise ConflictError(message)


def raise_database_error(message: str = "資料庫操作失敗") -> None:
    """拋出500異常"""
    raise DatabaseError(message)
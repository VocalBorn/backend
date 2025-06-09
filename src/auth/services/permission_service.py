from typing import List, Optional, TYPE_CHECKING
from fastapi import HTTPException, Depends
from sqlmodel import Session, select
from functools import wraps

from src.auth.models import UserRole, Account
from src.auth.services.jwt_service import verify_token
from src.shared.database.database import get_session

if TYPE_CHECKING:
    from src.auth.models import User


class Permission:
    """權限定義類"""
    
    # 課程相關權限
    VIEW_COURSES = "view_courses"           # 檢視課程
    EDIT_COURSES = "edit_courses"           # 編輯課程
    DELETE_COURSES = "delete_courses"       # 刪除課程
    CREATE_COURSES = "create_courses"       # 創建課程
    
    # 練習記錄權限
    VIEW_PRACTICE_RECORDS = "view_practice_records"     # 檢視練習記錄
    CREATE_PRACTICE_RECORDS = "create_practice_records" # 創建練習記錄
    
    # 用戶管理權限
    MANAGE_USERS = "manage_users"                       # 管理用戶
    VIEW_ALL_USERS = "view_all_users"                   # 檢視所有用戶


class RolePermissions:
    """角色權限映射"""
    
    # 一般使用者權限：檢視課程且與語言治療師溝通
    CLIENT_PERMISSIONS = [
        Permission.VIEW_COURSES,
        Permission.VIEW_PRACTICE_RECORDS,
        Permission.CREATE_PRACTICE_RECORDS,
    ]
    
    # 語言治療師權限：檢視課程且與使用者溝通
    THERAPIST_PERMISSIONS = [
        Permission.VIEW_COURSES,
        Permission.VIEW_PRACTICE_RECORDS,
    ]
    
    # 管理員權限：對課程進行編輯
    ADMIN_PERMISSIONS = [
        Permission.VIEW_COURSES,
        Permission.EDIT_COURSES,
        Permission.DELETE_COURSES,
        Permission.CREATE_COURSES,
        Permission.VIEW_PRACTICE_RECORDS,
        Permission.MANAGE_USERS,
        Permission.VIEW_ALL_USERS,
    ]
    
    @classmethod
    def get_permissions_by_role(cls, role: UserRole) -> List[str]:
        """根據角色獲取權限列表"""
        role_mapping = {
            UserRole.CLIENT: cls.CLIENT_PERMISSIONS,
            UserRole.THERAPIST: cls.THERAPIST_PERMISSIONS,
            UserRole.ADMIN: cls.ADMIN_PERMISSIONS,
        }
        return role_mapping.get(role, [])


async def get_current_user(
    email: str = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """取得當前用戶"""
    from src.auth.models import User
    
    account = session.exec(
        select(Account).where(Account.email == email)
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=404,
            detail="用戶不存在"
        )
    
    user = session.exec(
        select(User).where(User.account_id == account.account_id)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用戶資料不存在"
        )
    
    return user


def check_permission(required_permission: str):
    """檢查用戶是否有指定權限的裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 從 kwargs 中獲取 current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="需要登入"
                )
            
            user_permissions = RolePermissions.get_permissions_by_role(current_user.role)
            
            if required_permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="權限不足"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """需要特定權限的依賴項"""
    async def permission_checker(current_user = Depends(get_current_user)):
        user_permissions = RolePermissions.get_permissions_by_role(current_user.role)
        
        if permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail="權限不足"
            )
        
        return current_user
    
    return permission_checker


def require_role(required_roles: List[UserRole]):
    """需要特定角色的依賴項"""
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail="角色權限不足"
            )
        
        return current_user
    
    return role_checker


# 常用的權限檢查依賴項
RequireViewCourses = require_permission(Permission.VIEW_COURSES)
RequireEditCourses = require_permission(Permission.EDIT_COURSES)
RequireManageUsers = require_permission(Permission.MANAGE_USERS)

# 常用的角色檢查依賴項
RequireAdmin = require_role([UserRole.ADMIN])
RequireTherapist = require_role([UserRole.THERAPIST])
RequireAdminOrTherapist = require_role([UserRole.ADMIN, UserRole.THERAPIST])

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import UUID

from src.auth.models import User, UserRole
from src.auth.schemas import (
    UserResponse, 
    UserListResponse, 
    UpdateUserRoleRequest,
    PermissionResponse,
    UserStatsResponse
)
from src.auth.services.admin_service import (
    get_all_users,
    update_user_role,
    get_users_by_role,
    get_therapists,
    get_clients,
    promote_to_therapist,
    promote_to_admin,
    demote_to_client
)
from src.auth.services.permission_service import (
    RequireAdmin,
    RequireManageUsers,
    RolePermissions,
    get_current_user
)
from src.shared.database.database import get_session

router = APIRouter(prefix="/admin", tags=["管理員"])

@router.get("/users", response_model=UserListResponse)
async def get_users_list(
    current_user: User = Depends(RequireManageUsers),
    session: Session = Depends(get_session)
):
    """取得所有用戶列表（僅管理員）"""
    users = await get_all_users(session)
    return UserListResponse(
        total=len(users),
        users=users
    )

@router.get("/users/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(RequireAdmin),
    session: Session = Depends(get_session)
):
    """取得用戶統計資訊"""
    all_users = await get_all_users(session)
    
    stats = {
        "total_users": len(all_users),
        "clients": len([u for u in all_users if u.role == UserRole.CLIENT]),
        "therapists": len([u for u in all_users if u.role == UserRole.THERAPIST]),
        "admins": len([u for u in all_users if u.role == UserRole.ADMIN])
    }
    
    return UserStatsResponse(**stats)

@router.get("/users/therapists", response_model=List[UserResponse])
async def get_therapists_list(
    current_user: User = Depends(RequireManageUsers),
    session: Session = Depends(get_session)
):
    """取得所有語言治療師列表"""
    return await get_therapists(session)

@router.get("/users/clients", response_model=List[UserResponse])
async def get_clients_list(
    current_user: User = Depends(RequireManageUsers),
    session: Session = Depends(get_session)
):
    """取得所有一般用戶列表"""
    return await get_clients(session)

@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role_endpoint(
    user_id: UUID,
    request: UpdateUserRoleRequest,
    current_user: User = Depends(RequireAdmin),
    session: Session = Depends(get_session)
):
    """更新用戶角色（僅管理員）"""
    # 防止管理員修改自己的角色
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="不能修改自己的角色"
        )
    
    return await update_user_role(str(user_id), request.role, session)

@router.post("/users/{user_id}/promote-to-therapist", response_model=UserResponse)
async def promote_user_to_therapist(
    user_id: UUID,
    current_user: User = Depends(RequireAdmin),
    session: Session = Depends(get_session)
):
    """提升用戶為語言治療師"""
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="不能修改自己的角色"
        )
    
    return await promote_to_therapist(str(user_id), session)

@router.post("/users/{user_id}/promote-to-admin", response_model=UserResponse)
async def promote_user_to_admin(
    user_id: UUID,
    current_user: User = Depends(RequireAdmin),
    session: Session = Depends(get_session)
):
    """提升用戶為管理員"""
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="不能修改自己的角色"
        )
    
    return await promote_to_admin(str(user_id), session)

@router.post("/users/{user_id}/demote-to-client", response_model=UserResponse)
async def demote_user_to_client(
    user_id: UUID,
    current_user: User = Depends(RequireAdmin),
    session: Session = Depends(get_session)
):
    """降級用戶為一般用戶"""
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="不能修改自己的角色"
        )
    
    return await demote_to_client(str(user_id), session)

@router.get("/permissions/{role}", response_model=PermissionResponse)
async def get_role_permissions(
    role: UserRole,
    current_user: User = Depends(RequireAdmin)
):
    """取得指定角色的權限列表"""
    permissions = RolePermissions.get_permissions_by_role(role)
    return PermissionResponse(
        role=role,
        permissions=permissions
    )

@router.get("/my-permissions", response_model=PermissionResponse)
async def get_my_permissions(
    current_user: User = Depends(get_current_user)
):
    """取得當前用戶的權限列表"""
    permissions = RolePermissions.get_permissions_by_role(current_user.role)
    return PermissionResponse(
        role=current_user.role,
        permissions=permissions
    )

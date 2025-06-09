from typing import List, Optional
from fastapi import HTTPException
from sqlmodel import Session, select
from datetime import datetime

from src.auth.models import UserRole, Account
from src.auth.schemas import UserResponse

async def get_all_users(session: Session) -> List[UserResponse]:
    """取得所有用戶列表"""
    from src.auth.models import User
    try:
        users = session.exec(select(User)).all()
        return [
            UserResponse(
                user_id=user.user_id,
                account_id=user.account_id,
                name=user.name,
                gender=user.gender,
                age=user.age,
                phone=user.phone,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"取得用戶列表失敗: {str(e)}"
        )

async def update_user_role(
    user_id: str, 
    new_role: UserRole, 
    session: Session
) -> UserResponse:
    """更新用戶角色"""
    from src.auth.models import User
    try:
        # 查找用戶
        user = session.exec(
            select(User).where(User.user_id == user_id)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用戶不存在"
            )
        
        # 更新角色
        user.role = new_role
        user.updated_at = datetime.now()
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return UserResponse(
            user_id=user.user_id,
            account_id=user.account_id,
            name=user.name,
            gender=user.gender,
            age=user.age,
            phone=user.phone,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"更新用戶角色失敗: {str(e)}"
        )

async def get_users_by_role(role: UserRole, session: Session) -> List[UserResponse]:
    """根據角色取得用戶列表"""
    from src.auth.models import User 
    try:
        users = session.exec(
            select(User).where(User.role == role)
        ).all()
        
        return [
            UserResponse(
                user_id=user.user_id,
                account_id=user.account_id,
                name=user.name,
                gender=user.gender,
                age=user.age,
                phone=user.phone,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"取得角色用戶列表失敗: {str(e)}"
        )

async def get_therapists(session: Session) -> List[UserResponse]:
    """取得所有語言治療師"""
    return await get_users_by_role(UserRole.THERAPIST, session)

async def get_clients(session: Session) -> List[UserResponse]:
    """取得所有一般用戶"""
    return await get_users_by_role(UserRole.CLIENT, session)

async def promote_to_therapist(user_id: str, session: Session) -> UserResponse:
    """將用戶提升為語言治療師"""
    return await update_user_role(user_id, UserRole.THERAPIST, session)

async def promote_to_admin(user_id: str, session: Session) -> UserResponse:
    """將用戶提升為管理員"""
    return await update_user_role(user_id, UserRole.ADMIN, session)

async def demote_to_client(user_id: str, session: Session) -> UserResponse:
    """將用戶降級為一般用戶"""
    return await update_user_role(user_id, UserRole.CLIENT, session)

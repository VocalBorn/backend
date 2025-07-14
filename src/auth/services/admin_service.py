from typing import List, Optional
from fastapi import HTTPException
from sqlmodel import Session, select
from datetime import datetime
from uuid import UUID

from src.auth.models import UserRole, Account, User
from src.auth.schemas import UserResponse
from src.auth.services.password_service import verify_password
from src.therapist.services import therapist_service
from src.therapist.schemas import TherapistClientResponse

async def get_all_users(session: Session) -> List[UserResponse]:
    """取得所有用戶列表"""
    from src.auth.models import User, Account
    try:
        # 使用 JOIN 操作將 User 和 Account 表聯結
        users = session.exec(
            select(User, Account.email).join(Account, User.account_id == Account.account_id)
        ).all()

        return [
            UserResponse(
                user_id=user.User.user_id,
                account_id=user.User.account_id,
                name=user.User.name,
                gender=user.User.gender,
                age=user.User.age,
                phone=user.User.phone,
                email=user.email,  # 從 Account 表中獲取 email
                role=user.User.role,
                created_at=user.User.created_at,
                updated_at=user.User.updated_at
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

        # 獲取 email
        account = session.exec(
            select(Account).where(Account.account_id == user.account_id)
        ).first()
        email = account.email if account else None

        return UserResponse(
            user_id=user.user_id,
            account_id=user.account_id,
            name=user.name,
            gender=user.gender,
            age=user.age,
            phone=user.phone,
            email=email,  # 新增 email 欄位
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
    from src.auth.models import User, Account
    try:
        # 使用 JOIN 操作將 User 和 Account 表聯結
        users = session.exec(
            select(User, Account.email).join(Account, User.account_id == Account.account_id).where(User.role == role)
        ).all()

        return [
            UserResponse(
                user_id=user.User.user_id,
                account_id=user.User.account_id,
                name=user.User.name,
                gender=user.User.gender,
                age=user.User.age,
                phone=user.User.phone,
                email=user.email,  # 從 Account 表中獲取 email
                role=user.User.role,
                created_at=user.User.created_at,
                updated_at=user.User.updated_at
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

async def delete_user(user_id: str, admin_password: str, admin_user: User, session: Session) -> UserResponse:
    """刪除用戶帳號（包含相關資料）"""
    from src.auth.models import UserWord, EmailVerification
    from src.therapist.models import TherapistClient, TherapistProfile
    from src.verification.models import TherapistApplication
    from src.verification.models import UploadedDocument

    
    try:
        # 驗證管理員密碼
        admin_account = session.exec(
            select(Account).where(Account.account_id == admin_user.account_id)
        ).first()
        
        if not admin_account or not verify_password(admin_password, admin_account.password):
            raise HTTPException(
                status_code=401,
                detail="管理員密碼驗證失敗"
            )
        
        # 查找用戶
        user = session.exec(
            select(User).where(User.user_id == user_id)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用戶不存在"
            )
        
        # 刪除相關的治療師-客戶關係（作為治療師）
        therapist_client_relations_as_therapist = session.exec(
            select(TherapistClient).where(TherapistClient.therapist_id == user_id)
        ).all()
        for relation in therapist_client_relations_as_therapist:
            session.delete(relation)
        
        # 刪除相關的治療師-客戶關係（作為客戶）
        therapist_client_relations_as_client = session.exec(
            select(TherapistClient).where(TherapistClient.client_id == user_id)
        ).all()
        for relation in therapist_client_relations_as_client:
            session.delete(relation)
        
        # 刪除治療師檔案（如果存在）
        therapist_profile = session.exec(
            select(TherapistProfile).where(TherapistProfile.user_id == user_id)
        ).first()
        if therapist_profile:
            session.delete(therapist_profile)
        
        # 刪除用戶常用詞彙
        user_words = session.exec(
            select(UserWord).where(UserWord.user_id == user_id)
        ).all()
        for word in user_words:
            session.delete(word)
        
        # 刪除郵件驗證記錄
        email_verifications = session.exec(
            select(EmailVerification).where(EmailVerification.account_id == user.account_id)
        ).all()
        for verification in email_verifications:
            session.delete(verification)
        
        # 刪除治療師申請資料
        therapist_applications = session.exec(
            select(TherapistApplication).where(TherapistApplication.user_id == user_id)
        ).all()
        for application in therapist_applications:
            # 先刪除相關的上傳文件
            uploaded_documents = session.exec(
                select(UploadedDocument).where(UploadedDocument.application_id == application.id)
            ).all()
            for doc in uploaded_documents:
                session.delete(doc)
            # 再刪除申請本身
            session.delete(application)

        session.flush()

        # 保存用戶信息以便返回
        # 獲取 email
        account_to_delete = session.exec(
            select(Account).where(Account.account_id == user.account_id)
        ).first()
        email_to_return = account_to_delete.email if account_to_delete else None

        user_response = UserResponse(
            user_id=user.user_id,
            account_id=user.account_id,
            name=user.name,
            gender=user.gender,
            age=user.age,
            phone=user.phone,
            email=email_to_return,  # 新增 email 欄位
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        # 刪除用戶
        session.delete(user)
        
        # 最後刪除帳號
        account = session.exec(
            select(Account).where(Account.account_id == user.account_id)
        ).first()
        if account:
            session.delete(account)
        
        session.commit()
        return user_response
        
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"刪除用戶失敗: {str(e)}"
        )

async def get_therapist_clients_by_id(therapist_id: UUID, session: Session) -> List[TherapistClientResponse]:
    """管理員取得指定治療師的客戶列表"""
    try:
        # 驗證治療師是否存在
        therapist = session.exec(
            select(User).where(User.user_id == therapist_id)
        ).first()
        
        if not therapist:
            raise HTTPException(
                status_code=404,
                detail="治療師不存在"
            )
        
        # 驗證該用戶是否為治療師
        if therapist.role != UserRole.THERAPIST:
            raise HTTPException(
                status_code=400,
                detail="指定的用戶不是治療師"
            )
        
        # 獲取治療師的客戶關係列表
        therapist_clients = therapist_service.get_therapist_clients(session, therapist_id)
        
        # 組合客戶詳細資訊
        result = []
        for tc in therapist_clients:
            # 查詢客戶資訊
            client = session.exec(
                select(User).where(User.user_id == tc.client_id)
            ).first()
            
            client_info = None
            if client:
                client_info = {
                    "name": client.name,
                    "gender": client.gender,
                    "age": client.age,
                    "phone": client.phone,
                    "role": client.role
                }
            
            # 創建 TherapistClientResponse
            response = TherapistClientResponse(
                id=tc.id,
                therapist_id=tc.therapist_id,
                client_id=tc.client_id,
                created_at=tc.created_at,
                client_info=client_info
            )
            result.append(response)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"取得治療師客戶列表失敗: {str(e)}"
        )

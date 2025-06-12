from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from src.auth.models import User, UserRole, TherapistProfile, TherapistClient
from src.auth.schemas import (
    TherapistProfileCreate, 
    TherapistProfileUpdate, 
    TherapistProfileResponse,
    TherapistApplicationRequest
)


class TherapistService:
    """治療師相關服務"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_therapist_profile(
        self, 
        user_id: UUID, 
        profile_data: TherapistProfileCreate
    ) -> TherapistProfile:
        """建立治療師檔案"""
        
        # 驗證用戶存在且為治療師角色
        user = self.session.exec(
            select(User).where(User.user_id == user_id)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用戶不存在"
            )
        
        if user.role != UserRole.THERAPIST:
            raise HTTPException(
                status_code=400,
                detail="只有治療師角色才能建立治療師檔案"
            )
        
        # 檢查是否已有檔案
        existing_profile = self.session.exec(
            select(TherapistProfile).where(TherapistProfile.user_id == user_id)
        ).first()
        
        if existing_profile:
            raise HTTPException(
                status_code=400,
                detail="該用戶已有治療師檔案"
            )
        
        # 檢查執照號碼是否重複
        existing_license = self.session.exec(
            select(TherapistProfile).where(
                TherapistProfile.license_number == profile_data.license_number
            )
        ).first()
        
        if existing_license:
            raise HTTPException(
                status_code=400,
                detail="執照號碼已存在"
            )
        
        # 建立檔案
        profile = TherapistProfile(
            user_id=user_id,
            license_number=profile_data.license_number,
            specialization=profile_data.specialization,
            bio=profile_data.bio,
            years_experience=profile_data.years_experience,
            education=profile_data.education,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        
        return profile
    
    def get_therapist_profile(self, user_id: UUID) -> Optional[TherapistProfile]:
        """取得治療師檔案"""
        return self.session.exec(
            select(TherapistProfile).where(TherapistProfile.user_id == user_id)
        ).first()
    
    def update_therapist_profile(
        self, 
        user_id: UUID, 
        profile_data: TherapistProfileUpdate
    ) -> TherapistProfile:
        """更新治療師檔案"""
        
        profile = self.get_therapist_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="治療師檔案不存在"
            )
        
        # 檢查執照號碼是否重複（排除自己）
        if profile_data.license_number:
            existing_license = self.session.exec(
                select(TherapistProfile).where(
                    TherapistProfile.license_number == profile_data.license_number,
                    TherapistProfile.user_id != user_id
                )
            ).first()
            
            if existing_license:
                raise HTTPException(
                    status_code=400,
                    detail="執照號碼已存在"
                )
        
        # 更新檔案
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.now()
        
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        
        return profile
    
    def delete_therapist_profile(self, user_id: UUID) -> bool:
        """刪除治療師檔案"""
        
        profile = self.get_therapist_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="治療師檔案不存在"
            )
        
        self.session.delete(profile)
        self.session.commit()
        
        return True
    
    def assign_client_to_therapist(
        self, 
        therapist_id: UUID, 
        client_id: UUID,
        notes: Optional[str] = None
    ) -> TherapistClient:
        """指派客戶給治療師"""
        
        # 驗證治療師
        therapist = self.session.exec(
            select(User).where(
                User.user_id == therapist_id,
                User.role == UserRole.THERAPIST
            )
        ).first()
        
        if not therapist:
            raise HTTPException(
                status_code=404,
                detail="治療師不存在"
            )
        
        # 驗證客戶
        client = self.session.exec(
            select(User).where(
                User.user_id == client_id,
                User.role == UserRole.CLIENT
            )
        ).first()
        
        if not client:
            raise HTTPException(
                status_code=404,
                detail="客戶不存在"
            )
        
        # 檢查是否已指派
        existing_assignment = self.session.exec(
            select(TherapistClient).where(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.client_id == client_id,
                TherapistClient.is_active == True
            )
        ).first()
        
        if existing_assignment:
            raise HTTPException(
                status_code=400,
                detail="該客戶已指派給此治療師"
            )
        
        # 建立指派關係
        assignment = TherapistClient(
            therapist_id=therapist_id,
            client_id=client_id,
            assigned_date=datetime.now(),
            is_active=True,
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        
        return assignment
    
    def get_therapist_clients(self, therapist_id: UUID) -> List[TherapistClient]:
        """取得治療師的客戶列表"""
        return self.session.exec(
            select(TherapistClient).where(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.is_active == True
            )
        ).all()
    
    def get_client_therapists(self, client_id: UUID) -> List[TherapistClient]:
        """取得客戶的治療師列表"""
        return self.session.exec(
            select(TherapistClient).where(
                TherapistClient.client_id == client_id,
                TherapistClient.is_active == True
            )
        ).all()
    
    def unassign_client_from_therapist(
        self, 
        therapist_id: UUID, 
        client_id: UUID
    ) -> bool:
        """取消客戶與治療師的指派關係"""
        
        assignment = self.session.exec(
            select(TherapistClient).where(
                TherapistClient.therapist_id == therapist_id,
                TherapistClient.client_id == client_id,
                TherapistClient.is_active == True
            )
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=404,
                detail="指派關係不存在"
            )
        
        assignment.is_active = False
        assignment.updated_at = datetime.now()
        
        self.session.add(assignment)
        self.session.commit()
        
        return True
    
    def apply_to_be_therapist(
        self, 
        user_id: UUID, 
        application_data: TherapistApplicationRequest
    ) -> TherapistProfile:
        """申請成為治療師（建立檔案但不改變角色）"""
        
        # 驗證用戶存在
        user = self.session.exec(
            select(User).where(User.user_id == user_id)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用戶不存在"
            )
        
        # 檢查是否已有檔案
        existing_profile = self.get_therapist_profile(user_id)
        if existing_profile:
            raise HTTPException(
                status_code=400,
                detail="該用戶已有治療師檔案"
            )
        
        # 檢查執照號碼是否重複
        existing_license = self.session.exec(
            select(TherapistProfile).where(
                TherapistProfile.license_number == application_data.license_number
            )
        ).first()
        
        if existing_license:
            raise HTTPException(
                status_code=400,
                detail="執照號碼已存在"
            )
        
        # 建立治療師檔案（但不改變用戶角色，需管理員審核）
        profile = TherapistProfile(
            user_id=user_id,
            license_number=application_data.license_number,
            specialization=application_data.specialization,
            bio=application_data.bio,
            years_experience=application_data.years_experience,
            education=application_data.education,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        
        return profile
    
    def get_all_therapists(self) -> List[User]:
        """取得所有治療師"""
        return self.session.exec(
            select(User).where(User.role == UserRole.THERAPIST)
        ).all()

from enum import Enum
import uuid
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import List, Optional

# --- Enums ---

class ApplicationStatus(str, Enum):
    PENDING = "pending"          # 待處理：使用者已提交申請，等待管理員審核
    ACTION_REQUIRED = "action_required" # 需補件：部分文件被拒，需使用者重新上傳
    APPROVED = "approved"        # 已批准：所有文件審核通過
    REJECTED = "rejected"        # 已拒絕：申請被管理員拒絕

class DocumentType(str, Enum):
    ID_CARD_FRONT = "id_card_front"        # 身分證正面
    ID_CARD_BACK = "id_card_back"          # 身分證反面
    THERAPIST_CERTIFICATE = "therapist_certificate" # 語言治療師證明文件

# --- Tables ---

class UploadedDocument(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    application_id: uuid.UUID = Field(foreign_key="therapistapplication.id")
    application: "TherapistApplication" = Relationship(back_populates="documents")

    document_type: DocumentType
    file_object_name: str = Field(index=True, unique=True) # 在 MinIO 中的唯一物件名
    
    created_at: datetime = Field(default_factory=datetime.now)


class TherapistApplication(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", index=True) # 假設您的使用者表叫做 'user'

    status: ApplicationStatus = Field(default=ApplicationStatus.PENDING)
    
    # 關聯到所有上傳的文件
    documents: List["UploadedDocument"] = Relationship(back_populates="application")

    # 管理員審核資訊
    rejection_reason: Optional[str] = None
    reviewed_by_id: Optional[uuid.UUID] = Field(foreign_key="users.user_id")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

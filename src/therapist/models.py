import datetime
from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.auth.models import User

class TherapistProfile(SQLModel, table=True):
    """治療師檔案表"""
    __tablename__ = "therapist_profiles"
    
    profile_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", unique=True, nullable=False)
    license_number: str = Field(nullable=False, unique=True, max_length=50)
    specialization: Optional[str] = Field(default=None, max_length=200)
    bio: Optional[str] = Field(default=None, max_length=1000)
    years_experience: Optional[int] = Field(default=None)
    education: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    user: "User" = Relationship(back_populates="therapist_profile")

class TherapistClient(SQLModel, table=True):
    """治療師和客戶的多對多關係表"""
    __tablename__ = "therapist_clients"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    client_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    assigned_date: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    notes: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    therapist: "User" = Relationship(
        back_populates="assigned_clients",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.therapist_id]"}
    )
    client: "User" = Relationship(
        back_populates="assigned_therapists",
        sa_relationship_kwargs={"foreign_keys": "[TherapistClient.client_id]"}
    )

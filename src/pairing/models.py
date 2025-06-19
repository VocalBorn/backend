import datetime
from typing import Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.auth.models import User

class PairingToken(SQLModel, table=True):
    """配對Token表"""
    __tablename__ = "pairing_tokens"
    
    token_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    token_code: str = Field(nullable=False, unique=True, max_length=12)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    expires_at: datetime.datetime = Field(nullable=False)
    is_used: bool = Field(default=False)
    used_by_client_id: Optional[uuid.UUID] = Field(foreign_key="users.user_id", default=None)
    used_at: Optional[datetime.datetime] = Field(default=None)
    max_uses: int = Field(default=1, nullable=False)
    current_uses: int = Field(default=0, nullable=False)
    
    # Relationships
    therapist: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PairingToken.therapist_id]"}
    )
    used_by_client: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PairingToken.used_by_client_id]"}
    )

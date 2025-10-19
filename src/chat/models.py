import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.auth.models import User

class MessageStatus(str, Enum):
    """訊息狀態枚舉"""
    SENT = "sent"           # 已發送
    DELIVERED = "delivered" # 已送達
    READ = "read"          # 已讀取

class MessageType(str, Enum):
    """訊息類型枚舉"""
    TEXT = "text"       # 純文字訊息
    IMAGE = "image"     # 圖片訊息
    AUDIO = "audio"     # 語音訊息
    FILE = "file"       # 檔案訊息

class ChatRoom(SQLModel, table=True):
    """聊天室表

    代表治療師與患者之間的一對一聊天室。
    每對治療師-患者關係只會有一個聊天室。
    """
    __tablename__ = "chat_rooms"

    room_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    last_message_at: Optional[datetime.datetime] = Field(default=None)

    # Relationships
    messages: List["ChatMessage"] = Relationship(
        back_populates="room",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    client: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ChatRoom.client_id]"}
    )
    therapist: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ChatRoom.therapist_id]"}
    )

class ChatMessage(SQLModel, table=True):
    """聊天訊息表

    儲存聊天室中的所有訊息，包括文字、圖片、語音等類型。
    """
    __tablename__ = "chat_messages"

    message_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(foreign_key="chat_rooms.room_id", nullable=False)
    sender_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    content: str = Field(nullable=False)
    message_type: MessageType = Field(default=MessageType.TEXT, nullable=False)
    status: MessageStatus = Field(default=MessageStatus.SENT, nullable=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    delivered_at: Optional[datetime.datetime] = Field(default=None)
    read_at: Optional[datetime.datetime] = Field(default=None)

    # 檔案相關欄位（用於圖片、語音、檔案類型的訊息）
    file_url: Optional[str] = Field(default=None, max_length=500)
    file_size: Optional[int] = Field(default=None)  # 檔案大小（bytes）
    file_name: Optional[str] = Field(default=None, max_length=255)

    # 是否已被刪除（軟刪除）
    is_deleted: bool = Field(default=False, nullable=False)
    deleted_at: Optional[datetime.datetime] = Field(default=None)

    # Relationships
    room: ChatRoom = Relationship(back_populates="messages")
    sender: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ChatMessage.sender_id]"}
    )

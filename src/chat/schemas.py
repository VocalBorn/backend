import datetime
from typing import Optional, List
import uuid
from pydantic import BaseModel, Field

from src.chat.models import MessageStatus, MessageType

# ========== 聊天室相關 Schemas ==========

class ChatRoomBase(BaseModel):
    """聊天室基礎 Schema"""
    pass

class ChatRoomCreate(ChatRoomBase):
    """建立聊天室請求 Schema"""
    therapist_id: uuid.UUID = Field(..., description="治療師 ID")

class ChatRoomResponse(BaseModel):
    """聊天室回應 Schema"""
    room_id: uuid.UUID
    client_id: uuid.UUID
    therapist_id: uuid.UUID
    client_name: str
    therapist_name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool
    last_message_at: Optional[datetime.datetime] = None
    unread_count: Optional[int] = 0  # 未讀訊息數量

class ChatRoomListResponse(BaseModel):
    """聊天室列表回應 Schema"""
    rooms: List[ChatRoomResponse]
    total_count: int

# ========== 訊息相關 Schemas ==========

class MessageBase(BaseModel):
    """訊息基礎 Schema"""
    content: str = Field(..., min_length=1, max_length=5000, description="訊息內容")
    message_type: MessageType = Field(default=MessageType.TEXT, description="訊息類型")

class MessageCreate(MessageBase):
    """建立訊息請求 Schema（REST API 用）"""
    pass

class MessageResponse(BaseModel):
    """訊息回應 Schema"""
    message_id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    content: str
    message_type: MessageType
    status: MessageStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    delivered_at: Optional[datetime.datetime] = None
    read_at: Optional[datetime.datetime] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    is_deleted: bool

class MessageListResponse(BaseModel):
    """訊息列表回應 Schema"""
    messages: List[MessageResponse]
    total_count: int
    has_more: bool  # 是否還有更多訊息

class MessageHistoryQuery(BaseModel):
    """訊息歷史查詢參數 Schema"""
    limit: int = Field(default=50, ge=1, le=100, description="每頁訊息數量")
    offset: int = Field(default=0, ge=0, description="偏移量")
    before_message_id: Optional[uuid.UUID] = Field(default=None, description="在此訊息之前的訊息（分頁用）")

class MarkAsReadRequest(BaseModel):
    """標記訊息為已讀請求 Schema"""
    message_ids: List[uuid.UUID] = Field(..., min_length=1, description="要標記為已讀的訊息 ID 列表")

class MarkAsReadResponse(BaseModel):
    """標記訊息為已讀回應 Schema"""
    success: bool
    marked_count: int
    message: str

# ========== WebSocket 相關 Schemas ==========

class WebSocketMessageType(str):
    """WebSocket 訊息類型常數"""
    # 客戶端發送
    SEND_MESSAGE = "send_message"           # 發送訊息
    MARK_AS_READ = "mark_as_read"           # 標記為已讀
    TYPING_START = "typing_start"           # 開始輸入
    TYPING_STOP = "typing_stop"             # 停止輸入

    # 伺服器發送
    NEW_MESSAGE = "new_message"             # 新訊息通知
    MESSAGE_DELIVERED = "message_delivered" # 訊息已送達通知
    MESSAGE_READ = "message_read"           # 訊息已讀通知
    USER_TYPING = "user_typing"             # 對方正在輸入通知
    USER_STOP_TYPING = "user_stop_typing"   # 對方停止輸入通知
    ERROR = "error"                         # 錯誤訊息
    CONNECTION_ACK = "connection_ack"       # 連線確認

class WSMessageBase(BaseModel):
    """WebSocket 訊息基礎 Schema"""
    type: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

class WSSendMessage(WSMessageBase):
    """WebSocket 發送訊息 Schema（客戶端 -> 伺服器）"""
    type: str = WebSocketMessageType.SEND_MESSAGE
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: MessageType = MessageType.TEXT
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None

class WSNewMessage(WSMessageBase):
    """WebSocket 新訊息通知 Schema（伺服器 -> 客戶端）"""
    type: str = WebSocketMessageType.NEW_MESSAGE
    message: MessageResponse

class WSMarkAsRead(WSMessageBase):
    """WebSocket 標記已讀 Schema（客戶端 -> 伺服器）"""
    type: str = WebSocketMessageType.MARK_AS_READ
    message_ids: List[uuid.UUID]

class WSMessageRead(WSMessageBase):
    """WebSocket 訊息已讀通知 Schema（伺服器 -> 客戶端）"""
    type: str = WebSocketMessageType.MESSAGE_READ
    message_ids: List[uuid.UUID]
    read_at: datetime.datetime

class WSMessageDelivered(WSMessageBase):
    """WebSocket 訊息送達通知 Schema（伺服器 -> 客戶端）"""
    type: str = WebSocketMessageType.MESSAGE_DELIVERED
    message_id: uuid.UUID
    delivered_at: datetime.datetime

class WSTypingNotification(WSMessageBase):
    """WebSocket 輸入狀態通知 Schema"""
    type: str  # typing_start 或 typing_stop
    user_id: uuid.UUID
    user_name: str

class WSError(WSMessageBase):
    """WebSocket 錯誤訊息 Schema"""
    type: str = WebSocketMessageType.ERROR
    error_code: str
    message: str

class WSConnectionAck(WSMessageBase):
    """WebSocket 連線確認 Schema"""
    type: str = WebSocketMessageType.CONNECTION_ACK
    room_id: uuid.UUID
    user_id: uuid.UUID
    message: str = "已成功連線至聊天室"

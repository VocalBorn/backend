"""聊天服務模組

提供聊天室管理、訊息處理和 WebSocket 連線管理等功能。
"""

from src.chat.services.chat_service import (
    get_or_create_chat_room,
    get_user_chat_rooms,
    get_chat_room_by_id,
    check_room_access_permission,
)

from src.chat.services.message_service import (
    create_message,
    get_room_messages,
    mark_messages_as_read,
    mark_message_as_delivered,
    get_unread_count,
)

from src.chat.services.websocket_service import (
    WebSocketManager,
    ws_manager,
)

__all__ = [
    # Chat service
    "get_or_create_chat_room",
    "get_user_chat_rooms",
    "get_chat_room_by_id",
    "check_room_access_permission",

    # Message service
    "create_message",
    "get_room_messages",
    "mark_messages_as_read",
    "mark_message_as_delivered",
    "get_unread_count",

    # WebSocket service
    "WebSocketManager",
    "ws_manager",
]

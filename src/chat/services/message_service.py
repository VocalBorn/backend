"""訊息處理服務

提供訊息的建立、查詢、狀態更新等功能。
"""

import datetime
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlmodel import Session, select, desc, and_

from src.auth.models import User
from src.chat.models import ChatRoom, ChatMessage, MessageStatus, MessageType
from src.chat.schemas import MessageResponse, MessageListResponse


async def create_message(
    session: Session,
    room_id: uuid.UUID,
    sender_id: uuid.UUID,
    content: str,
    message_type: MessageType = MessageType.TEXT,
    file_url: Optional[str] = None,
    file_size: Optional[int] = None,
    file_name: Optional[str] = None
) -> MessageResponse:
    """建立新訊息

    Args:
        session: 資料庫 Session
        room_id: 聊天室 ID
        sender_id: 發送者 ID
        content: 訊息內容
        message_type: 訊息類型
        file_url: 檔案 URL（可選）
        file_size: 檔案大小（可選）
        file_name: 檔案名稱（可選）

    Returns:
        MessageResponse: 建立的訊息

    Raises:
        HTTPException: 當聊天室不存在或發送者無權限時
    """
    # 驗證聊天室存在且發送者有權限
    room = session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )

    if not room.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="聊天室已停用"
        )

    if sender_id not in [room.client_id, room.therapist_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限在此聊天室發送訊息"
        )

    # 建立訊息
    new_message = ChatMessage(
        room_id=room_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
        status=MessageStatus.SENT,
        file_url=file_url,
        file_size=file_size,
        file_name=file_name,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )

    session.add(new_message)

    # 更新聊天室的最後訊息時間
    room.last_message_at = datetime.datetime.now()
    room.updated_at = datetime.datetime.now()
    session.add(room)

    session.commit()
    session.refresh(new_message)

    # 取得發送者資訊
    sender = session.get(User, sender_id)

    return MessageResponse(
        message_id=new_message.message_id,
        room_id=new_message.room_id,
        sender_id=new_message.sender_id,
        sender_name=sender.name if sender else "未知使用者",
        content=new_message.content,
        message_type=new_message.message_type,
        status=new_message.status,
        created_at=new_message.created_at,
        updated_at=new_message.updated_at,
        delivered_at=new_message.delivered_at,
        read_at=new_message.read_at,
        file_url=new_message.file_url,
        file_size=new_message.file_size,
        file_name=new_message.file_name,
        is_deleted=new_message.is_deleted
    )


async def get_room_messages(
    session: Session,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    before_message_id: Optional[uuid.UUID] = None
) -> MessageListResponse:
    """取得聊天室的訊息歷史

    Args:
        session: 資料庫 Session
        room_id: 聊天室 ID
        user_id: 請求者 ID（用於權限檢查）
        limit: 每頁訊息數量
        offset: 偏移量
        before_message_id: 在此訊息之前的訊息（用於分頁）

    Returns:
        MessageListResponse: 訊息列表及相關資訊

    Raises:
        HTTPException: 當聊天室不存在或無權限存取時
    """
    # 驗證聊天室和權限
    room = session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )

    if user_id not in [room.client_id, room.therapist_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限存取此聊天室的訊息"
        )

    # 建立查詢
    stmt = select(ChatMessage).where(
        and_(
            ChatMessage.room_id == room_id,
            ChatMessage.is_deleted == False
        )
    )

    # 如果指定了 before_message_id，則查詢該訊息之前的訊息
    if before_message_id:
        before_message = session.get(ChatMessage, before_message_id)
        if before_message:
            stmt = stmt.where(ChatMessage.created_at < before_message.created_at)

    # 按建立時間降序排序（最新的在前）
    stmt = stmt.order_by(desc(ChatMessage.created_at))

    # 套用分頁
    stmt = stmt.offset(offset).limit(limit + 1)  # 多查一筆來判斷是否有更多

    messages = session.exec(stmt).all()

    # 判斷是否還有更多訊息
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # 組裝回應資料
    message_responses = []
    for message in messages:
        sender = session.get(User, message.sender_id)
        message_responses.append(
            MessageResponse(
                message_id=message.message_id,
                room_id=message.room_id,
                sender_id=message.sender_id,
                sender_name=sender.name if sender else "未知使用者",
                content=message.content,
                message_type=message.message_type,
                status=message.status,
                created_at=message.created_at,
                updated_at=message.updated_at,
                delivered_at=message.delivered_at,
                read_at=message.read_at,
                file_url=message.file_url,
                file_size=message.file_size,
                file_name=message.file_name,
                is_deleted=message.is_deleted
            )
        )

    # 反轉列表，使最舊的訊息在前（符合一般聊天室顯示習慣）
    message_responses.reverse()

    return MessageListResponse(
        messages=message_responses,
        total_count=len(message_responses),
        has_more=has_more
    )


async def mark_messages_as_read(
    session: Session,
    message_ids: List[uuid.UUID],
    user_id: uuid.UUID
) -> int:
    """將訊息標記為已讀

    只有訊息的接收者可以標記訊息為已讀。

    Args:
        session: 資料庫 Session
        message_ids: 要標記的訊息 ID 列表
        user_id: 請求者 ID（接收者）

    Returns:
        int: 成功標記的訊息數量

    Raises:
        HTTPException: 當無權限標記訊息時
    """
    marked_count = 0
    read_at = datetime.datetime.now()

    for message_id in message_ids:
        message = session.get(ChatMessage, message_id)

        if not message:
            continue

        # 驗證權限：只有接收者可以標記為已讀
        room = session.get(ChatRoom, message.room_id)
        if not room:
            continue

        # 接收者是聊天室的另一方（不是發送者）
        if message.sender_id == user_id:
            # 自己的訊息不能標記為已讀
            continue

        if user_id not in [room.client_id, room.therapist_id]:
            # 不是聊天室成員
            continue

        # 標記為已讀
        if message.status != MessageStatus.READ:
            message.status = MessageStatus.READ
            message.read_at = read_at
            message.updated_at = read_at
            session.add(message)
            marked_count += 1

    if marked_count > 0:
        session.commit()

    return marked_count


async def mark_message_as_delivered(
    session: Session,
    message_id: uuid.UUID
) -> bool:
    """將訊息標記為已送達

    此功能通常由 WebSocket 連線自動觸發。

    Args:
        session: 資料庫 Session
        message_id: 訊息 ID

    Returns:
        bool: 是否成功標記
    """
    message = session.get(ChatMessage, message_id)

    if not message:
        return False

    if message.status == MessageStatus.SENT:
        message.status = MessageStatus.DELIVERED
        message.delivered_at = datetime.datetime.now()
        message.updated_at = datetime.datetime.now()
        session.add(message)
        session.commit()
        return True

    return False


async def get_unread_count(
    session: Session,
    room_id: uuid.UUID,
    user_id: uuid.UUID
) -> int:
    """取得聊天室中使用者的未讀訊息數量

    Args:
        session: 資料庫 Session
        room_id: 聊天室 ID
        user_id: 使用者 ID

    Returns:
        int: 未讀訊息數量
    """
    stmt = select(ChatMessage).where(
        and_(
            ChatMessage.room_id == room_id,
            ChatMessage.sender_id != user_id,
            ChatMessage.status != MessageStatus.READ,
            ChatMessage.is_deleted == False
        )
    )

    messages = session.exec(stmt).all()
    return len(messages)

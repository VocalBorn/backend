"""聊天室管理服務

提供聊天室的建立、查詢和權限檢查等功能。
"""

import datetime
from typing import List, Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlmodel import Session, select, or_, and_, func

from src.auth.models import User, UserRole
from src.chat.models import ChatRoom, ChatMessage, MessageStatus
from src.chat.schemas import ChatRoomResponse, ChatRoomListResponse
from src.therapist.models import TherapistClient


async def get_or_create_chat_room(
    session: Session,
    client_id: uuid.UUID,
    therapist_id: uuid.UUID,
    current_user_id: uuid.UUID
) -> ChatRoom:
    """取得或建立聊天室

    檢查是否已存在該治療師與患者的聊天室，若不存在則建立新的。
    同時檢查權限，確保只有配對的治療師和患者才能建立聊天室。

    Args:
        session: 資料庫 Session
        client_id: 患者 ID
        therapist_id: 治療師 ID
        current_user_id: 當前使用者 ID（用於權限檢查）

    Returns:
        ChatRoom: 聊天室物件

    Raises:
        HTTPException: 當權限不足或使用者不存在時
    """
    # 驗證使用者存在
    client = session.get(User, client_id)
    therapist = session.get(User, therapist_id)

    if not client or not therapist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )

    # 驗證角色
    if client.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的 client_id 必須是患者角色"
        )

    if therapist.role != UserRole.THERAPIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的 therapist_id 必須是治療師角色"
        )

    # 檢查權限：只有患者本人或治療師本人可以建立/存取聊天室
    if current_user_id not in [client_id, therapist_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限建立或存取此聊天室"
        )

    # 檢查是否已配對
    therapist_client_stmt = select(TherapistClient).where(
        TherapistClient.therapist_id == therapist_id,
        TherapistClient.client_id == client_id,
        TherapistClient.is_active == True
    )
    therapist_client = session.exec(therapist_client_stmt).first()

    if not therapist_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="患者與治療師尚未建立配對關係"
        )

    # 查詢是否已存在聊天室
    stmt = select(ChatRoom).where(
        ChatRoom.client_id == client_id,
        ChatRoom.therapist_id == therapist_id
    )
    existing_room = session.exec(stmt).first()

    if existing_room:
        # 如果聊天室被停用，重新啟用它
        if not existing_room.is_active:
            existing_room.is_active = True
            existing_room.updated_at = datetime.datetime.now()
            session.add(existing_room)
            session.commit()
            session.refresh(existing_room)
        return existing_room

    # 建立新聊天室
    new_room = ChatRoom(
        client_id=client_id,
        therapist_id=therapist_id,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )

    session.add(new_room)
    session.commit()
    session.refresh(new_room)

    return new_room


async def get_user_chat_rooms(
    session: Session,
    user_id: uuid.UUID
) -> ChatRoomListResponse:
    """取得使用者的所有聊天室

    Args:
        session: 資料庫 Session
        user_id: 使用者 ID

    Returns:
        ChatRoomListResponse: 聊天室列表及總數

    Raises:
        HTTPException: 當使用者不存在時
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )

    # 查詢使用者的所有聊天室（無論是治療師還是患者）
    stmt = select(ChatRoom).where(
        and_(
            or_(
                ChatRoom.client_id == user_id,
                ChatRoom.therapist_id == user_id
            ),
            ChatRoom.is_active == True
        )
    ).order_by(ChatRoom.last_message_at.desc().nulls_last(), ChatRoom.created_at.desc())

    rooms = session.exec(stmt).all()

    # 組裝回應資料
    room_responses = []
    for room in rooms:
        client = session.get(User, room.client_id)
        therapist = session.get(User, room.therapist_id)

        # 計算未讀訊息數量（對方發送給我但我還沒讀的訊息）
        unread_stmt = select(func.count(ChatMessage.message_id)).where(
            ChatMessage.room_id == room.room_id,
            ChatMessage.sender_id != user_id,
            ChatMessage.status != MessageStatus.READ,
            ChatMessage.is_deleted == False
        )
        unread_count = session.exec(unread_stmt).one()

        room_responses.append(
            ChatRoomResponse(
                room_id=room.room_id,
                client_id=room.client_id,
                therapist_id=room.therapist_id,
                client_name=client.name if client else "未知使用者",
                therapist_name=therapist.name if therapist else "未知治療師",
                created_at=room.created_at,
                updated_at=room.updated_at,
                is_active=room.is_active,
                last_message_at=room.last_message_at,
                unread_count=unread_count
            )
        )

    return ChatRoomListResponse(
        rooms=room_responses,
        total_count=len(room_responses)
    )


async def get_chat_room_by_id(
    session: Session,
    room_id: uuid.UUID,
    user_id: uuid.UUID
) -> ChatRoomResponse:
    """根據 ID 取得聊天室詳情

    Args:
        session: 資料庫 Session
        room_id: 聊天室 ID
        user_id: 當前使用者 ID（用於權限檢查）

    Returns:
        ChatRoomResponse: 聊天室詳情

    Raises:
        HTTPException: 當聊天室不存在或無權限存取時
    """
    room = session.get(ChatRoom, room_id)

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天室不存在"
        )

    # 檢查權限
    if user_id not in [room.client_id, room.therapist_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限存取此聊天室"
        )

    client = session.get(User, room.client_id)
    therapist = session.get(User, room.therapist_id)

    # 計算未讀訊息數量
    unread_stmt = select(func.count(ChatMessage.message_id)).where(
        ChatMessage.room_id == room.room_id,
        ChatMessage.sender_id != user_id,
        ChatMessage.status != MessageStatus.READ,
        ChatMessage.is_deleted == False
    )
    unread_count = session.exec(unread_stmt).one()

    return ChatRoomResponse(
        room_id=room.room_id,
        client_id=room.client_id,
        therapist_id=room.therapist_id,
        client_name=client.name if client else "未知使用者",
        therapist_name=therapist.name if therapist else "未知治療師",
        created_at=room.created_at,
        updated_at=room.updated_at,
        is_active=room.is_active,
        last_message_at=room.last_message_at,
        unread_count=unread_count
    )


async def check_room_access_permission(
    session: Session,
    room_id: uuid.UUID,
    user_id: uuid.UUID
) -> Tuple[ChatRoom, User]:
    """檢查使用者是否有權限存取指定聊天室

    Args:
        session: 資料庫 Session
        room_id: 聊天室 ID
        user_id: 使用者 ID

    Returns:
        Tuple[ChatRoom, User]: 聊天室物件和對方使用者物件

    Raises:
        HTTPException: 當聊天室不存在或無權限存取時
    """
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

    # 檢查是否為聊天室成員
    if user_id not in [room.client_id, room.therapist_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限存取此聊天室"
        )

    # 取得對方使用者
    other_user_id = room.therapist_id if user_id == room.client_id else room.client_id
    other_user = session.get(User, other_user_id)

    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="對方使用者不存在"
        )

    return room, other_user

"""聊天功能 REST API 路由

提供聊天室和訊息的 REST API 端點。
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from src.auth.models import User
from src.auth.services.permission_service import get_current_user
from src.shared.database.database import get_session
from src.chat.schemas import (
    ChatRoomCreate,
    ChatRoomResponse,
    ChatRoomListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    MarkAsReadRequest,
    MarkAsReadResponse,
)
from src.chat.services.chat_service import (
    get_or_create_chat_room,
    get_user_chat_rooms,
    get_chat_room_by_id,
)
from src.chat.services.message_service import (
    create_message,
    get_room_messages,
    mark_messages_as_read,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get(
    "/rooms",
    response_model=ChatRoomListResponse,
    summary="取得使用者的聊天室列表",
    description="取得當前使用者參與的所有聊天室",
    responses={
        200: {
            "description": "成功取得聊天室列表",
            "content": {
                "application/json": {
                    "example": {
                        "rooms": [
                            {
                                "room_id": "550e8400-e29b-41d4-a716-446655440000",
                                "client_id": "123e4567-e89b-12d3-a456-426614174000",
                                "therapist_id": "789e0123-e89b-12d3-a456-426614174000",
                                "client_name": "王小明",
                                "therapist_name": "陳治療師",
                                "created_at": "2025-01-15T10:00:00",
                                "updated_at": "2025-01-15T14:30:00",
                                "is_active": True,
                                "last_message_at": "2025-01-15T14:30:00",
                                "unread_count": 3
                            }
                        ],
                        "total_count": 1
                    }
                }
            }
        },
        401: {"description": "未驗證 - 需要有效的 JWT token"},
        404: {"description": "使用者不存在"}
    }
)
async def get_rooms_router(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> ChatRoomListResponse:
    """
    取得使用者的聊天室列表

    回傳當前使用者參與的所有聊天室，包含：
    - 聊天室基本資訊
    - 對方資訊
    - 最後訊息時間
    - 未讀訊息數量

    需要有效的 JWT 驗證。
    """
    return await get_user_chat_rooms(session, current_user.user_id)


@router.post(
    "/rooms",
    response_model=ChatRoomResponse,
    summary="建立或取得聊天室",
    description="患者或治療師都可以建立聊天室，指定對方 ID。若已存在則取得現有聊天室",
    responses={
        200: {
            "description": "成功建立或取得聊天室",
            "content": {
                "application/json": {
                    "example": {
                        "room_id": "550e8400-e29b-41d4-a716-446655440000",
                        "client_id": "123e4567-e89b-12d3-a456-426614174000",
                        "therapist_id": "789e0123-e89b-12d3-a456-426614174000",
                        "client_name": "王小明",
                        "therapist_name": "陳治療師",
                        "created_at": "2025-01-15T10:00:00",
                        "updated_at": "2025-01-15T10:00:00",
                        "is_active": True,
                        "last_message_at": None,
                        "unread_count": 0
                    }
                }
            }
        },
        400: {"description": "請求錯誤 - 參數不正確或缺少必填欄位"},
        401: {"description": "未驗證 - 需要有效的 JWT token"},
        403: {"description": "無權限 - 未配對或無法建立聊天室"},
        404: {"description": "使用者不存在"}
    }
)
async def create_room_router(
    room_data: ChatRoomCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> ChatRoomResponse:
    """
    建立或取得聊天室

    患者或治療師都可以建立聊天室，指定對方的 ID。若聊天室已存在則直接回傳。

    - **therapist_id**: 治療師 ID（患者建立聊天室時使用，必填）
    - **client_id**: 患者 ID（治療師建立聊天室時使用，必填）

    權限限制：
    - 只能與已配對的對象建立聊天室
    - 患者需提供 therapist_id
    - 治療師需提供 client_id

    需要有效的 JWT 驗證。
    """
    from src.auth.models import UserRole

    # 根據當前使用者角色決定 client_id 和 therapist_id
    if current_user.role == UserRole.CLIENT:
        # 患者建立聊天室，需要提供 therapist_id
        if not room_data.therapist_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="患者建立聊天室時必須提供 therapist_id"
            )
        client_id = current_user.user_id
        therapist_id = room_data.therapist_id
    elif current_user.role == UserRole.THERAPIST:
        # 治療師建立聊天室，需要提供 client_id
        if not room_data.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="治療師建立聊天室時必須提供 client_id"
            )
        client_id = room_data.client_id
        therapist_id = current_user.user_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="角色無權限建立聊天室"
        )

    room = await get_or_create_chat_room(
        session=session,
        client_id=client_id,
        therapist_id=therapist_id,
        current_user_id=current_user.user_id
    )

    return await get_chat_room_by_id(session, room.room_id, current_user.user_id)


@router.get(
    "/rooms/{room_id}",
    response_model=ChatRoomResponse,
    summary="取得聊天室詳情",
    description="取得指定聊天室的詳細資訊",
    responses={
        200: {"description": "成功取得聊天室詳情"},
        401: {"description": "未驗證 - 需要有效的 JWT token"},
        403: {"description": "無權限 - 無法存取該聊天室"},
        404: {"description": "聊天室不存在"}
    }
)
async def get_room_router(
    room_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> ChatRoomResponse:
    """
    取得聊天室詳情

    回傳指定聊天室的詳細資訊，包含：
    - 聊天室基本資訊
    - 雙方資訊
    - 未讀訊息數量

    權限限制：
    - 只有聊天室成員可以存取

    需要有效的 JWT 驗證。
    """
    return await get_chat_room_by_id(session, room_id, current_user.user_id)


@router.get(
    "/rooms/{room_id}/messages",
    response_model=MessageListResponse,
    summary="取得聊天室訊息歷史",
    description="取得指定聊天室的訊息歷史記錄",
    responses={
        200: {
            "description": "成功取得訊息歷史",
            "content": {
                "application/json": {
                    "example": {
                        "messages": [
                            {
                                "message_id": "660e8400-e29b-41d4-a716-446655440000",
                                "room_id": "550e8400-e29b-41d4-a716-446655440000",
                                "sender_id": "123e4567-e89b-12d3-a456-426614174000",
                                "sender_name": "王小明",
                                "content": "請問下次諮詢時間...",
                                "message_type": "text",
                                "status": "read",
                                "created_at": "2025-01-15T14:00:00",
                                "updated_at": "2025-01-15T14:05:00",
                                "delivered_at": "2025-01-15T14:00:30",
                                "read_at": "2025-01-15T14:05:00",
                                "file_url": None,
                                "file_size": None,
                                "file_name": None,
                                "is_deleted": False
                            }
                        ],
                        "total_count": 1,
                        "has_more": False
                    }
                }
            }
        },
        401: {"description": "未驗證 - 需要有效的 JWT token"},
        403: {"description": "無權限 - 無法存取該聊天室"},
        404: {"description": "聊天室不存在"}
    }
)
async def get_messages_router(
    room_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=50, ge=1, le=100, description="每頁訊息數量"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    before_message_id: uuid.UUID = Query(default=None, description="在此訊息之前的訊息")
) -> MessageListResponse:
    """
    取得聊天室訊息歷史

    回傳指定聊天室的訊息歷史記錄。

    查詢參數：
    - **limit**: 每頁訊息數量（1-100，預設 50）
    - **offset**: 偏移量（預設 0）
    - **before_message_id**: 查詢在此訊息之前的訊息（分頁用）

    權限限制：
    - 只有聊天室成員可以查看訊息

    需要有效的 JWT 驗證。
    """
    return await get_room_messages(
        session=session,
        room_id=room_id,
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
        before_message_id=before_message_id
    )


@router.post(
    "/rooms/{room_id}/messages",
    response_model=MessageResponse,
    summary="發送訊息（REST API）",
    description="透過 REST API 發送訊息（建議使用 WebSocket）",
    responses={
        200: {
            "description": "訊息發送成功",
            "content": {
                "application/json": {
                    "example": {
                        "message_id": "660e8400-e29b-41d4-a716-446655440000",
                        "room_id": "550e8400-e29b-41d4-a716-446655440000",
                        "sender_id": "123e4567-e89b-12d3-a456-426614174000",
                        "sender_name": "王小明",
                        "content": "請問下次諮詢時間...",
                        "message_type": "text",
                        "status": "sent",
                        "created_at": "2025-01-15T14:00:00",
                        "updated_at": "2025-01-15T14:00:00",
                        "delivered_at": None,
                        "read_at": None,
                        "file_url": None,
                        "file_size": None,
                        "file_name": None,
                        "is_deleted": False
                    }
                }
            }
        },
        401: {"description": "未驗證 - 需要有效的 JWT token"},
        403: {"description": "無權限 - 無法在該聊天室發送訊息"},
        404: {"description": "聊天室不存在"}
    }
)
async def send_message_router(
    room_id: uuid.UUID,
    message_data: MessageCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> MessageResponse:
    """
    透過 REST API 發送訊息

    此端點適合測試或輕量級應用。建議使用 WebSocket 端點以獲得即時通訊體驗。

    - **content**: 訊息內容（1-5000 字元）
    - **message_type**: 訊息類型（text, image, audio, file）

    權限限制：
    - 只有聊天室成員可以發送訊息

    需要有效的 JWT 驗證。
    """
    return await create_message(
        session=session,
        room_id=room_id,
        sender_id=current_user.user_id,
        content=message_data.content,
        message_type=message_data.message_type
    )


@router.post(
    "/messages/mark-read",
    response_model=MarkAsReadResponse,
    summary="標記訊息為已讀",
    description="批量標記訊息為已讀狀態",
    responses={
        200: {
            "description": "成功標記訊息為已讀",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "marked_count": 5,
                        "message": "已將 5 則訊息標記為已讀"
                    }
                }
            }
        },
        401: {"description": "未驗證 - 需要有效的 JWT token"},
        403: {"description": "無權限 - 無法標記這些訊息"}
    }
)
async def mark_read_router(
    request: MarkAsReadRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> MarkAsReadResponse:
    """
    標記訊息為已讀

    批量標記訊息為已讀狀態，只能標記自己接收的訊息。

    - **message_ids**: 要標記為已讀的訊息 ID 列表

    權限限制：
    - 只能標記自己接收的訊息
    - 發送者不能標記自己的訊息

    需要有效的 JWT 驗證。
    """
    marked_count = await mark_messages_as_read(
        session=session,
        message_ids=request.message_ids,
        user_id=current_user.user_id
    )

    return MarkAsReadResponse(
        success=True,
        marked_count=marked_count,
        message=f"已將 {marked_count} 則訊息標記為已讀"
    )

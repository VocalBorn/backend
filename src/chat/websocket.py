"""WebSocket 聊天端點

提供即時聊天的 WebSocket 連線。
"""

import json
import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlmodel import Session

from src.auth.services.jwt_service import decode_token
from src.shared.database.database import get_session
from src.chat.services.chat_service import check_room_access_permission
from src.chat.services.message_service import create_message, mark_message_as_delivered
from src.chat.services.websocket_service import ws_manager
from src.chat.schemas import (
    WebSocketMessageType,
    WSConnectionAck,
    WSNewMessage,
    WSMessageDelivered,
    WSMessageRead,
    WSError,
)
from src.chat.models import MessageType, ChatMessage

logger = logging.getLogger(__name__)

ws_router = APIRouter(prefix="/chat", tags=["chat-websocket"])


@ws_router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: uuid.UUID,
    token: str = Query(..., description="JWT 認證 token"),
    session: Session = Depends(get_session)
):
    """
    WebSocket 聊天端點

    建立即時聊天連線。客戶端需要提供有效的 JWT token。

    連線後可以：
    - 發送訊息
    - 接收即時訊息
    - 標記訊息為已讀
    - 發送/接收輸入狀態通知

    Args:
        room_id: 聊天室 ID
        token: JWT 認證 token（透過 query參數傳遞）
        session: 資料庫 Session
    """
    user_id = None

    try:
        # 驗證 JWT token
        try:
            payload = decode_token(token)
            email = payload.get("sub")

            # 取得使用者
            from src.auth.models import Account, User
            from sqlmodel import select

            account = session.exec(
                select(Account).where(Account.email == email)
            ).first()

            if not account:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            user = session.exec(
                select(User).where(User.account_id == account.account_id)
            ).first()

            if not user:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            user_id = user.user_id

        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 檢查聊天室存取權限
        try:
            room, other_user = await check_room_access_permission(
                session=session,
                room_id=room_id,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Room access check failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 建立 WebSocket 連線
        await ws_manager.connect(websocket, room_id, user_id)

        # 發送連線確認訊息
        ack_message = WSConnectionAck(
            type=WebSocketMessageType.CONNECTION_ACK,
            room_id=room_id,
            user_id=user_id
        )
        await websocket.send_text(json.dumps(ack_message.model_dump(), default=str))

        logger.info(f"User {user_id} connected to room {room_id}")

        # 訊息處理循環
        while True:
            try:
                # 接收訊息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                message_type = message_data.get("type")

                # 根據訊息類型處理
                if message_type == WebSocketMessageType.SEND_MESSAGE:
                    # 處理發送訊息
                    await handle_send_message(
                        session=session,
                        room_id=room_id,
                        user_id=user_id,
                        other_user_id=other_user.user_id,
                        message_data=message_data
                    )

                elif message_type == WebSocketMessageType.MARK_AS_READ:
                    # 處理標記已讀
                    await handle_mark_as_read(
                        session=session,
                        room_id=room_id,
                        user_id=user_id,
                        other_user_id=other_user.user_id,
                        message_data=message_data
                    )

                elif message_type == WebSocketMessageType.TYPING_START:
                    # 處理開始輸入通知
                    await handle_typing_notification(
                        room_id=room_id,
                        user_id=user_id,
                        user_name=user.name,
                        other_user_id=other_user.user_id,
                        is_typing=True
                    )

                elif message_type == WebSocketMessageType.TYPING_STOP:
                    # 處理停止輸入通知
                    await handle_typing_notification(
                        room_id=room_id,
                        user_id=user_id,
                        user_name=user.name,
                        other_user_id=other_user.user_id,
                        is_typing=False
                    )

                else:
                    # 未知的訊息類型
                    error_message = WSError(
                        type=WebSocketMessageType.ERROR,
                        error_code="UNKNOWN_MESSAGE_TYPE",
                        message=f"未知的訊息類型: {message_type}"
                    )
                    await websocket.send_text(json.dumps(error_message.model_dump(), default=str))

            except WebSocketDisconnect:
                logger.info(f"User {user_id} disconnected from room {room_id}")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                error_message = WSError(
                    type=WebSocketMessageType.ERROR,
                    error_code="MESSAGE_PROCESSING_ERROR",
                    message=f"處理訊息時發生錯誤: {str(e)}"
                )
                await websocket.send_text(json.dumps(error_message.model_dump(), default=str))

    finally:
        # 斷開連線
        if user_id:
            ws_manager.disconnect(websocket, room_id, user_id)
            logger.info(f"User {user_id} cleaned up from room {room_id}")


async def handle_send_message(
    session: Session,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
    other_user_id: uuid.UUID,
    message_data: dict
):
    """處理發送訊息

    Args:
        session: 資料庫 Session
        room_id: 聊天室 ID
        user_id: 發送者 ID
        other_user_id: 接收者 ID
        message_data: 訊息資料
    """
    try:
        # 建立訊息
        content = message_data.get("content", "")
        message_type = message_data.get("message_type", MessageType.TEXT)
        file_url = message_data.get("file_url")
        file_size = message_data.get("file_size")
        file_name = message_data.get("file_name")

        message_response = await create_message(
            session=session,
            room_id=room_id,
            sender_id=user_id,
            content=content,
            message_type=message_type,
            file_url=file_url,
            file_size=file_size,
            file_name=file_name
        )

        # 如果對方在線，發送新訊息通知
        if ws_manager.is_user_online(other_user_id):
            new_message = WSNewMessage(
                type=WebSocketMessageType.NEW_MESSAGE,
                message=message_response
            )
            await ws_manager.send_personal_message(
                message=new_message.model_dump(),
                user_id=other_user_id
            )

            # 自動標記為已送達
            await mark_message_as_delivered(session, message_response.message_id)

            # 重新整理訊息以取得更新後的 delivered_at
            session.refresh(session.get(ChatMessage, message_response.message_id))
            updated_message = session.get(ChatMessage, message_response.message_id)

            # 通知發送者訊息已送達
            delivered_notification = WSMessageDelivered(
                type=WebSocketMessageType.MESSAGE_DELIVERED,
                message_id=message_response.message_id,
                delivered_at=updated_message.delivered_at if updated_message else datetime.datetime.now()
            )
            await ws_manager.send_personal_message(
                message=delivered_notification.model_dump(),
                user_id=user_id
            )

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        error_message = WSError(
            type=WebSocketMessageType.ERROR,
            error_code="SEND_MESSAGE_ERROR",
            message=f"發送訊息失敗: {str(e)}"
        )
        await ws_manager.send_personal_message(
            message=error_message.model_dump(),
            user_id=user_id
        )


async def handle_mark_as_read(
    session: Session,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
    other_user_id: uuid.UUID,
    message_data: dict
):
    """處理標記訊息為已讀

    Args:
        session: 資料庫 Session
        room_id: 聊天室 ID
        user_id: 當前使用者 ID
        other_user_id: 對方使用者 ID
        message_data: 訊息資料
    """
    try:
        from src.chat.services.message_service import mark_messages_as_read
        import datetime

        message_ids = [uuid.UUID(mid) for mid in message_data.get("message_ids", [])]

        if message_ids:
            marked_count = await mark_messages_as_read(
                session=session,
                message_ids=message_ids,
                user_id=user_id
            )

            if marked_count > 0:
                # 通知發送者訊息已讀
                read_notification = WSMessageRead(
                    type=WebSocketMessageType.MESSAGE_READ,
                    message_ids=message_ids,
                    read_at=datetime.datetime.now()
                )
                await ws_manager.send_personal_message(
                    message=read_notification.model_dump(),
                    user_id=other_user_id
                )

    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")


async def handle_typing_notification(
    room_id: uuid.UUID,
    user_id: uuid.UUID,
    user_name: str,
    other_user_id: uuid.UUID,
    is_typing: bool
):
    """處理輸入狀態通知

    Args:
        room_id: 聊天室 ID
        user_id: 輸入者 ID
        user_name: 輸入者名稱
        other_user_id: 對方使用者 ID
        is_typing: 是否正在輸入
    """
    try:
        from src.chat.schemas import WSTypingNotification

        notification_type = (
            WebSocketMessageType.USER_TYPING
            if is_typing
            else WebSocketMessageType.USER_STOP_TYPING
        )

        typing_notification = WSTypingNotification(
            type=notification_type,
            user_id=user_id,
            user_name=user_name
        )

        # 只通知對方，不通知自己
        await ws_manager.send_personal_message(
            message=typing_notification.model_dump(),
            user_id=other_user_id
        )

    except Exception as e:
        logger.error(f"Error sending typing notification: {e}")

"""WebSocket 連線管理服務

提供 WebSocket 連線的建立、管理和訊息廣播功能。
"""

import asyncio
import json
from typing import Dict, Set
import uuid
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 連線管理器

    管理所有活躍的 WebSocket 連線，支援訊息廣播和連線追蹤。
    使用單例模式確保全域只有一個管理器實例。
    """

    def __init__(self):
        """初始化 WebSocket 管理器"""
        # room_id -> set of (user_id, websocket) tuples
        self.active_connections: Dict[uuid.UUID, Set[tuple[uuid.UUID, WebSocket]]] = {}
        # user_id -> set of websocket connections
        self.user_connections: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        room_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """建立 WebSocket 連線

        Args:
            websocket: WebSocket 連線物件
            room_id: 聊天室 ID
            user_id: 使用者 ID
        """
        await websocket.accept()

        # 將連線加入到聊天室
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add((user_id, websocket))

        # 將連線加入到使用者連線集合
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        logger.info(f"User {user_id} connected to room {room_id}")

    def disconnect(
        self,
        websocket: WebSocket,
        room_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        """斷開 WebSocket 連線

        Args:
            websocket: WebSocket 連線物件
            room_id: 聊天室 ID
            user_id: 使用者 ID
        """
        # 從聊天室移除連線
        if room_id in self.active_connections:
            self.active_connections[room_id].discard((user_id, websocket))
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

        # 從使用者連線集合移除
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected from room {room_id}")

    async def send_personal_message(
        self,
        message: dict,
        user_id: uuid.UUID
    ) -> None:
        """發送訊息給特定使用者的所有連線

        Args:
            message: 要發送的訊息（dict 格式，將轉為 JSON）
            user_id: 目標使用者 ID
        """
        if user_id in self.user_connections:
            message_json = json.dumps(message, default=str)
            disconnected = []

            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(websocket)

            # 清理斷開的連線
            for ws in disconnected:
                self.user_connections[user_id].discard(ws)

    async def broadcast_to_room(
        self,
        message: dict,
        room_id: uuid.UUID,
        exclude_user_id: uuid.UUID = None
    ) -> None:
        """向聊天室中的所有使用者廣播訊息

        Args:
            message: 要廣播的訊息（dict 格式，將轉為 JSON）
            room_id: 聊天室 ID
            exclude_user_id: 要排除的使用者 ID（可選，通常排除發送者本人）
        """
        if room_id not in self.active_connections:
            return

        message_json = json.dumps(message, default=str)
        disconnected = []

        for user_id, websocket in self.active_connections[room_id]:
            if exclude_user_id and user_id == exclude_user_id:
                continue

            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to room {room_id}, user {user_id}: {e}")
                disconnected.append((user_id, websocket))

        # 清理斷開的連線
        for user_id, ws in disconnected:
            self.active_connections[room_id].discard((user_id, ws))
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(ws)

    async def send_to_room_members(
        self,
        message: dict,
        room_id: uuid.UUID,
        target_user_ids: list[uuid.UUID]
    ) -> None:
        """向聊天室中的特定使用者發送訊息

        Args:
            message: 要發送的訊息（dict 格式，將轉為 JSON）
            room_id: 聊天室 ID
            target_user_ids: 目標使用者 ID 列表
        """
        if room_id not in self.active_connections:
            return

        message_json = json.dumps(message, default=str)
        target_set = set(target_user_ids)
        disconnected = []

        for user_id, websocket in self.active_connections[room_id]:
            if user_id not in target_set:
                continue

            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to user {user_id} in room {room_id}: {e}")
                disconnected.append((user_id, websocket))

        # 清理斷開的連線
        for user_id, ws in disconnected:
            self.active_connections[room_id].discard((user_id, ws))
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(ws)

    def is_user_online(self, user_id: uuid.UUID) -> bool:
        """檢查使用者是否在線

        Args:
            user_id: 使用者 ID

        Returns:
            bool: 使用者是否有活躍的連線
        """
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0

    def get_room_online_users(self, room_id: uuid.UUID) -> Set[uuid.UUID]:
        """取得聊天室中在線的使用者

        Args:
            room_id: 聊天室 ID

        Returns:
            Set[uuid.UUID]: 在線使用者的 ID 集合
        """
        if room_id not in self.active_connections:
            return set()

        return {user_id for user_id, _ in self.active_connections[room_id]}

    def get_connection_count(self, room_id: uuid.UUID) -> int:
        """取得聊天室的連線數量

        Args:
            room_id: 聊天室 ID

        Returns:
            int: 連線數量
        """
        if room_id not in self.active_connections:
            return 0

        return len(self.active_connections[room_id])


# 全域 WebSocket 管理器實例
ws_manager = WebSocketManager()

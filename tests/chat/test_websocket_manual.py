"""WebSocket 手動測試腳本

使用方法：
1. 確保伺服器正在運行：uv run fastapi dev src/main.py
2. 執行此腳本：uv run python tests/chat/test_websocket_manual.py
3. 根據提示輸入測試資料

測試流程：
- 建立或選擇聊天室
- 使用兩個客戶端模擬雙方對話
- 測試發送訊息、已讀狀態、輸入提示等功能
"""

import asyncio
import json
import uuid
from typing import Optional
import websockets
import requests


# 設定
API_BASE_URL = "http://127.0.0.1:8000"
WS_BASE_URL = "ws://127.0.0.1:8000"


class WebSocketChatClient:
    """WebSocket 聊天客戶端測試類別"""

    def __init__(self, user_name: str, token: str, room_id: uuid.UUID):
        self.user_name = user_name
        self.token = token
        self.room_id = room_id
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self):
        """連線到 WebSocket"""
        ws_url = f"{WS_BASE_URL}/chat/ws/{self.room_id}?token={self.token}"
        print(f"[{self.user_name}] 正在連線到: {ws_url}")

        try:
            self.ws = await websockets.connect(ws_url)
            print(f"[{self.user_name}] ✓ WebSocket 連線成功")

            # 接收連線確認訊息
            ack = await self.ws.recv()
            ack_data = json.loads(ack)
            print(f"[{self.user_name}] 收到連線確認: {ack_data}")

        except Exception as e:
            print(f"[{self.user_name}] ✗ 連線失敗: {e}")
            raise

    async def send_message(self, content: str):
        """發送文字訊息"""
        if not self.ws:
            print(f"[{self.user_name}] ✗ 尚未連線")
            return

        message = {
            "type": "send_message",
            "content": content,
            "message_type": "text"
        }

        await self.ws.send(json.dumps(message))
        print(f"[{self.user_name}] → 發送訊息: {content}")

    async def send_typing_start(self):
        """發送開始輸入通知"""
        if not self.ws:
            return

        await self.ws.send(json.dumps({"type": "typing_start"}))
        print(f"[{self.user_name}] ⌨️  開始輸入...")

    async def send_typing_stop(self):
        """發送停止輸入通知"""
        if not self.ws:
            return

        await self.ws.send(json.dumps({"type": "typing_stop"}))
        print(f"[{self.user_name}] ⏸️  停止輸入")

    async def mark_as_read(self, message_ids: list):
        """標記訊息為已讀"""
        if not self.ws:
            return

        message = {
            "type": "mark_as_read",
            "message_ids": [str(mid) for mid in message_ids]
        }

        await self.ws.send(json.dumps(message))
        print(f"[{self.user_name}] ✓ 標記 {len(message_ids)} 則訊息為已讀")

    async def listen(self):
        """監聽接收訊息"""
        if not self.ws:
            return

        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "new_message":
                    msg = data["message"]
                    print(f"[{self.user_name}] ← 收到新訊息: {msg['content']} (來自: {msg['sender_name']})")

                elif msg_type == "message_delivered":
                    print(f"[{self.user_name}] ✓ 訊息已送達")

                elif msg_type == "message_read":
                    print(f"[{self.user_name}] ✓ 訊息已讀")

                elif msg_type == "user_typing":
                    print(f"[{self.user_name}] ⌨️  {data['user_name']} 正在輸入...")

                elif msg_type == "user_stop_typing":
                    print(f"[{self.user_name}] ⏸️  {data['user_name']} 停止輸入")

                elif msg_type == "error":
                    print(f"[{self.user_name}] ✗ 錯誤: {data['message']}")

                else:
                    print(f"[{self.user_name}] 收到訊息: {data}")

        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.user_name}] 連線已關閉")

    async def disconnect(self):
        """斷線"""
        if self.ws:
            await self.ws.close()
            print(f"[{self.user_name}] 已斷線")


async def interactive_test():
    """互動式測試"""
    print("=" * 60)
    print("WebSocket 聊天室測試工具")
    print("=" * 60)

    # 1. 取得測試用的 tokens
    print("\n步驟 1: 準備測試用戶")
    print("-" * 60)

    # 這裡你需要替換成實際的 JWT tokens
    # 可以透過登入 API 取得，或使用測試用的 token
    user1_token = input("請輸入用戶 1 的 JWT token（客戶端）: ").strip()
    user2_token = input("請輸入用戶 2 的 JWT token（治療師）: ").strip()

    # 2. 選擇或建立聊天室
    print("\n步驟 2: 選擇聊天室")
    print("-" * 60)
    room_id_str = input("請輸入聊天室 ID（或留空以建立新聊天室）: ").strip()

    if room_id_str:
        room_id = uuid.UUID(room_id_str)
    else:
        # 這裡需要實作建立聊天室的邏輯
        print("建立聊天室功能尚未實作，請提供現有的聊天室 ID")
        return

    # 3. 建立兩個客戶端
    print("\n步驟 3: 建立 WebSocket 連線")
    print("-" * 60)

    client1 = WebSocketChatClient("客戶端", user1_token, room_id)
    client2 = WebSocketChatClient("治療師", user2_token, room_id)

    try:
        # 連線
        await client1.connect()
        await client2.connect()

        # 啟動監聽任務
        listen_task1 = asyncio.create_task(client1.listen())
        listen_task2 = asyncio.create_task(client2.listen())

        print("\n步驟 4: 開始測試")
        print("-" * 60)
        print("提示: 輸入 'quit' 結束測試")
        print()

        # 4. 互動式訊息發送
        await asyncio.sleep(1)  # 等待連線穩定

        # 測試情境 1: 發送訊息
        print("\n[測試] 客戶端發送訊息...")
        await client1.send_message("你好，我想諮詢語言治療課程")
        await asyncio.sleep(1)

        print("\n[測試] 治療師回覆訊息...")
        await client2.send_message("您好！很高興為您服務，請問您想了解什麼？")
        await asyncio.sleep(1)

        # 測試情境 2: 輸入提示
        print("\n[測試] 治療師開始輸入...")
        await client2.send_typing_start()
        await asyncio.sleep(2)
        await client2.send_typing_stop()
        await client2.send_message("我們有多種課程可以選擇")
        await asyncio.sleep(1)

        # 測試情境 3: 標記已讀（需要先取得訊息 ID）
        print("\n[測試] 測試完成！")
        print("連線將持續 10 秒，您可以觀察訊息狀態...")
        await asyncio.sleep(10)

    except Exception as e:
        print(f"測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理
        await client1.disconnect()
        await client2.disconnect()
        listen_task1.cancel()
        listen_task2.cancel()


async def simple_test():
    """簡單測試（使用預設值）"""
    print("=" * 60)
    print("WebSocket 簡單測試")
    print("=" * 60)
    print("此測試需要您提供:")
    print("1. 有效的 JWT token")
    print("2. 有效的聊天室 ID")
    print()

    token = input("請輸入 JWT token: ").strip()
    room_id = uuid.UUID(input("請輸入聊天室 ID: ").strip())

    client = WebSocketChatClient("測試用戶", token, room_id)

    try:
        await client.connect()

        # 啟動監聽
        listen_task = asyncio.create_task(client.listen())

        # 發送測試訊息
        await asyncio.sleep(1)
        await client.send_message("這是一則測試訊息")

        # 保持連線
        print("\n保持連線 30 秒...")
        await asyncio.sleep(30)

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()
        listen_task.cancel()


def print_usage():
    """印出使用說明"""
    print("\n" + "=" * 60)
    print("使用說明")
    print("=" * 60)
    print("\n如何取得 JWT token:")
    print("1. 使用登入 API: POST /auth/login")
    print("2. 或使用 Swagger UI: http://127.0.0.1:8000/docs")
    print("\n如何取得或建立聊天室:")
    print("1. 查看聊天室列表: GET /chat/rooms")
    print("2. 建立新聊天室: POST /chat/rooms")
    print("3. 或使用 Swagger UI: http://127.0.0.1:8000/docs")
    print("\n執行測試:")
    print("uv run python tests/chat/test_websocket_manual.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_usage()

    print("選擇測試模式:")
    print("1. 互動式測試（雙客戶端）")
    print("2. 簡單測試（單客戶端）")
    print("3. 僅顯示使用說明")

    choice = input("\n請選擇 (1/2/3): ").strip()

    if choice == "1":
        asyncio.run(interactive_test())
    elif choice == "2":
        asyncio.run(simple_test())
    elif choice == "3":
        print_usage()
    else:
        print("無效的選擇")

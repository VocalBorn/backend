# 聊天系統前端開發手冊

## 目錄
- [系統架構概覽](#系統架構概覽)
- [快速開始](#快速開始)
- [REST API 端點](#rest-api-端點)
- [WebSocket 即時通訊](#websocket-即時通訊)
- [資料模型](#資料模型)
- [完整範例](#完整範例)
- [錯誤處理](#錯誤處理)
- [最佳實踐](#最佳實踐)

---

## 系統架構概覽

VocalBorn 聊天系統是一個基於 FastAPI 的即時通訊系統,支援治療師與患者之間的一對一溝通。系統提供兩種通訊方式:

1. **REST API**: 適合輕量級操作,如取得聊天室列表、建立聊天室、查詢歷史訊息
2. **WebSocket**: 適合即時通訊,如發送/接收訊息、輸入狀態通知、訊息狀態更新

### 主要功能

- ✅ 一對一聊天室管理
- ✅ 即時訊息發送與接收
- ✅ 訊息狀態追蹤 (已發送/已送達/已讀)
- ✅ 輸入狀態指示器
- ✅ 多種訊息類型 (文字、圖片、語音、檔案)
- ✅ 訊息歷史記錄與分頁
- ✅ 未讀訊息計數
- ✅ 權限控制 (只能與配對的治療師/患者聊天)

### 技術架構

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   前端應用   │ ◄────► │  REST API    │ ◄────► │   資料庫     │
│  (React/    │         │  (FastAPI)   │         │ (PostgreSQL) │
│   Vue等)    │ ◄────► │  WebSocket   │         │              │
└─────────────┘         └──────────────┘         └──────────────┘
```

---

## 快速開始

### 1. 認證

所有 API 端點都需要 JWT 認證。在請求時需要在 Header 中帶入 token:

```javascript
// REST API
const headers = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};

// WebSocket
const ws = new WebSocket(`ws://localhost:8000/chat/ws/${roomId}?token=${access_token}`);
```

### 2. 基本流程

```javascript
// 步驟 1: 取得或建立聊天室
const room = await createChatRoom(therapistId);

// 步驟 2: 連接 WebSocket
const ws = connectWebSocket(room.room_id);

// 步驟 3: 發送訊息
ws.send(JSON.stringify({
  type: 'send_message',
  content: 'Hello!',
  message_type: 'text'
}));

// 步驟 4: 接收訊息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleMessage(data);
};
```

---

## REST API 端點

Base URL: `/chat`

### 1. 取得聊天室列表

**端點**: `GET /chat/rooms`

**描述**: 取得當前使用者參與的所有聊天室

**請求範例**:
```javascript
const response = await fetch('/chat/rooms', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const data = await response.json();
```

**回應範例**:
```json
{
  "rooms": [
    {
      "room_id": "550e8400-e29b-41d4-a716-446655440000",
      "client_id": "123e4567-e89b-12d3-a456-426614174000",
      "therapist_id": "789e0123-e89b-12d3-a456-426614174000",
      "client_name": "王小明",
      "therapist_name": "陳治療師",
      "created_at": "2025-01-15T10:00:00",
      "updated_at": "2025-01-15T14:30:00",
      "is_active": true,
      "last_message_at": "2025-01-15T14:30:00",
      "unread_count": 3
    }
  ],
  "total_count": 1
}
```

**回應欄位說明**:
- `room_id`: 聊天室唯一識別碼
- `client_id`: 患者 ID
- `therapist_id`: 治療師 ID
- `client_name`: 患者姓名
- `therapist_name`: 治療師姓名
- `is_active`: 聊天室是否啟用
- `last_message_at`: 最後訊息時間
- `unread_count`: 未讀訊息數量

---

### 2. 建立或取得聊天室

**端點**: `POST /chat/rooms`

**描述**: 患者建立與治療師的聊天室,若已存在則回傳現有聊天室

**權限限制**:
- ⚠️ 只有患者可以建立聊天室
- ⚠️ 患者只能與已配對的治療師建立聊天室
- ⚠️ 治療師無法主動建立聊天室,需等待患者發起

**請求範例**:
```javascript
const response = await fetch('/chat/rooms', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    therapist_id: '789e0123-e89b-12d3-a456-426614174000'
  })
});

const room = await response.json();
```

**回應範例**:
```json
{
  "room_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "therapist_id": "789e0123-e89b-12d3-a456-426614174000",
  "client_name": "王小明",
  "therapist_name": "陳治療師",
  "created_at": "2025-01-15T10:00:00",
  "updated_at": "2025-01-15T10:00:00",
  "is_active": true,
  "last_message_at": null,
  "unread_count": 0
}
```

---

### 3. 取得聊天室詳情

**端點**: `GET /chat/rooms/{room_id}`

**描述**: 取得指定聊天室的詳細資訊

**請求範例**:
```javascript
const roomId = '550e8400-e29b-41d4-a716-446655440000';
const response = await fetch(`/chat/rooms/${roomId}`, {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const room = await response.json();
```

---

### 4. 取得訊息歷史

**端點**: `GET /chat/rooms/{room_id}/messages`

**描述**: 取得指定聊天室的訊息歷史記錄,支援分頁

**查詢參數**:
- `limit`: 每頁訊息數量 (1-100,預設 50)
- `offset`: 偏移量 (預設 0)
- `before_message_id`: 查詢在此訊息之前的訊息 (用於向上載入更多訊息)

**請求範例**:
```javascript
const roomId = '550e8400-e29b-41d4-a716-446655440000';
const response = await fetch(
  `/chat/rooms/${roomId}/messages?limit=50&offset=0`,
  {
    headers: {
      'Authorization': `Bearer ${access_token}`
    }
  }
);

const data = await response.json();
```

**回應範例**:
```json
{
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
      "file_url": null,
      "file_size": null,
      "file_name": null,
      "is_deleted": false
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

---

### 5. 發送訊息 (REST API)

**端點**: `POST /chat/rooms/{room_id}/messages`

**描述**: 透過 REST API 發送訊息 (⚠️ 建議使用 WebSocket 以獲得即時通訊體驗)

**請求範例**:
```javascript
const roomId = '550e8400-e29b-41d4-a716-446655440000';
const response = await fetch(`/chat/rooms/${roomId}/messages`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: '您好,請問下次諮詢時間?',
    message_type: 'text'
  })
});

const message = await response.json();
```

---

### 6. 標記訊息為已讀

**端點**: `POST /chat/messages/mark-read`

**描述**: 批量標記訊息為已讀狀態

**請求範例**:
```javascript
const response = await fetch('/chat/messages/mark-read', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message_ids: [
      '660e8400-e29b-41d4-a716-446655440000',
      '770e8400-e29b-41d4-a716-446655440001'
    ]
  })
});

const result = await response.json();
```

**回應範例**:
```json
{
  "success": true,
  "marked_count": 2,
  "message": "已將 2 則訊息標記為已讀"
}
```

---

## WebSocket 即時通訊

### 連線建立

**WebSocket URL**: `ws://localhost:8000/chat/ws/{room_id}?token={jwt_token}`

**連線範例**:
```javascript
const roomId = '550e8400-e29b-41d4-a716-446655440000';
const token = 'your_jwt_access_token';
const ws = new WebSocket(`ws://localhost:8000/chat/ws/${roomId}?token=${token}`);

ws.onopen = () => {
  console.log('WebSocket 連線已建立');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到訊息:', data);
  handleWebSocketMessage(data);
};

ws.onerror = (error) => {
  console.error('WebSocket 錯誤:', error);
};

ws.onclose = () => {
  console.log('WebSocket 連線已關閉');
};
```

### 連線確認

連線成功後,伺服器會發送連線確認訊息:

```json
{
  "type": "connection_ack",
  "room_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "已成功連線至聊天室",
  "timestamp": "2025-01-15T14:00:00"
}
```

---

### WebSocket 訊息類型

#### 1. 發送訊息 (客戶端 → 伺服器)

**類型**: `send_message`

**說明**: 發送文字或檔案訊息

**訊息格式**:
```javascript
ws.send(JSON.stringify({
  type: 'send_message',
  content: '您好,我想詢問一下...',
  message_type: 'text',  // text | image | audio | file
  file_url: null,        // 若為檔案類型,需提供檔案 URL
  file_size: null,
  file_name: null
}));
```

**訊息類型說明**:
- `text`: 純文字訊息
- `image`: 圖片訊息 (需先上傳檔案取得 URL)
- `audio`: 語音訊息 (需先上傳檔案取得 URL)
- `file`: 一般檔案 (需先上傳檔案取得 URL)

**範例 - 發送圖片訊息**:
```javascript
// 先上傳檔案到儲存服務 (如 S3)
const fileUrl = await uploadImage(imageFile);

// 透過 WebSocket 發送圖片訊息
ws.send(JSON.stringify({
  type: 'send_message',
  content: '[圖片]',
  message_type: 'image',
  file_url: fileUrl,
  file_size: imageFile.size,
  file_name: imageFile.name
}));
```

---

#### 2. 接收新訊息 (伺服器 → 客戶端)

**類型**: `new_message`

**說明**: 當對方發送訊息時,會收到此通知

**訊息格式**:
```json
{
  "type": "new_message",
  "message": {
    "message_id": "660e8400-e29b-41d4-a716-446655440000",
    "room_id": "550e8400-e29b-41d4-a716-446655440000",
    "sender_id": "789e0123-e89b-12d3-a456-426614174000",
    "sender_name": "陳治療師",
    "content": "下次諮詢時間是週三下午 2 點",
    "message_type": "text",
    "status": "delivered",
    "created_at": "2025-01-15T14:10:00",
    "updated_at": "2025-01-15T14:10:00",
    "delivered_at": "2025-01-15T14:10:00",
    "read_at": null,
    "file_url": null,
    "file_size": null,
    "file_name": null,
    "is_deleted": false
  },
  "timestamp": "2025-01-15T14:10:00"
}
```

**處理範例**:
```javascript
function handleWebSocketMessage(data) {
  switch(data.type) {
    case 'new_message':
      // 將新訊息加入聊天視窗
      addMessageToChat(data.message);

      // 標記為已讀
      markMessageAsRead(data.message.message_id);
      break;
    // ... 其他訊息類型處理
  }
}
```

---

#### 3. 訊息已送達通知 (伺服器 → 客戶端)

**類型**: `message_delivered`

**說明**: 當你發送的訊息成功送達對方時,會收到此通知

**訊息格式**:
```json
{
  "type": "message_delivered",
  "message_id": "660e8400-e29b-41d4-a716-446655440000",
  "delivered_at": "2025-01-15T14:10:00",
  "timestamp": "2025-01-15T14:10:00"
}
```

**處理範例**:
```javascript
case 'message_delivered':
  // 更新訊息狀態為「已送達」
  updateMessageStatus(data.message_id, 'delivered', data.delivered_at);
  break;
```

---

#### 4. 標記訊息為已讀 (客戶端 → 伺服器)

**類型**: `mark_as_read`

**說明**: 將收到的訊息標記為已讀

**訊息格式**:
```javascript
ws.send(JSON.stringify({
  type: 'mark_as_read',
  message_ids: [
    '660e8400-e29b-41d4-a716-446655440000',
    '770e8400-e29b-41d4-a716-446655440001'
  ]
}));
```

---

#### 5. 訊息已讀通知 (伺服器 → 客戶端)

**類型**: `message_read`

**說明**: 當對方已讀你的訊息時,會收到此通知

**訊息格式**:
```json
{
  "type": "message_read",
  "message_ids": [
    "660e8400-e29b-41d4-a716-446655440000"
  ],
  "read_at": "2025-01-15T14:15:00",
  "timestamp": "2025-01-15T14:15:00"
}
```

**處理範例**:
```javascript
case 'message_read':
  // 更新訊息狀態為「已讀」
  data.message_ids.forEach(messageId => {
    updateMessageStatus(messageId, 'read', data.read_at);
  });
  break;
```

---

#### 6. 開始輸入通知 (客戶端 → 伺服器)

**類型**: `typing_start`

**說明**: 通知對方你正在輸入

**訊息格式**:
```javascript
ws.send(JSON.stringify({
  type: 'typing_start'
}));
```

**實作範例**:
```javascript
let typingTimeout;

// 當輸入框內容變化時
inputElement.addEventListener('input', () => {
  // 清除之前的計時器
  clearTimeout(typingTimeout);

  // 發送開始輸入通知
  ws.send(JSON.stringify({ type: 'typing_start' }));

  // 3 秒後自動發送停止輸入通知
  typingTimeout = setTimeout(() => {
    ws.send(JSON.stringify({ type: 'typing_stop' }));
  }, 3000);
});
```

---

#### 7. 停止輸入通知 (客戶端 → 伺服器)

**類型**: `typing_stop`

**說明**: 通知對方你已停止輸入

**訊息格式**:
```javascript
ws.send(JSON.stringify({
  type: 'typing_stop'
}));
```

---

#### 8. 對方正在輸入通知 (伺服器 → 客戶端)

**類型**: `user_typing`

**說明**: 對方開始輸入時收到此通知

**訊息格式**:
```json
{
  "type": "user_typing",
  "user_id": "789e0123-e89b-12d3-a456-426614174000",
  "user_name": "陳治療師",
  "timestamp": "2025-01-15T14:20:00"
}
```

**處理範例**:
```javascript
case 'user_typing':
  // 顯示「對方正在輸入...」提示
  showTypingIndicator(data.user_name);
  break;
```

---

#### 9. 對方停止輸入通知 (伺服器 → 客戶端)

**類型**: `user_stop_typing`

**說明**: 對方停止輸入時收到此通知

**訊息格式**:
```json
{
  "type": "user_stop_typing",
  "user_id": "789e0123-e89b-12d3-a456-426614174000",
  "user_name": "陳治療師",
  "timestamp": "2025-01-15T14:20:05"
}
```

**處理範例**:
```javascript
case 'user_stop_typing':
  // 隱藏「對方正在輸入...」提示
  hideTypingIndicator();
  break;
```

---

#### 10. 錯誤訊息 (伺服器 → 客戶端)

**類型**: `error`

**說明**: 當操作失敗時收到錯誤訊息

**訊息格式**:
```json
{
  "type": "error",
  "error_code": "SEND_MESSAGE_ERROR",
  "message": "發送訊息失敗: 無權限",
  "timestamp": "2025-01-15T14:25:00"
}
```

**常見錯誤代碼**:
- `UNKNOWN_MESSAGE_TYPE`: 未知的訊息類型
- `MESSAGE_PROCESSING_ERROR`: 訊息處理錯誤
- `SEND_MESSAGE_ERROR`: 發送訊息失敗

**處理範例**:
```javascript
case 'error':
  console.error(`錯誤 [${data.error_code}]:`, data.message);
  showErrorNotification(data.message);
  break;
```

---

## 資料模型

### 訊息狀態 (MessageStatus)

```typescript
enum MessageStatus {
  SENT = 'sent',           // 已發送 (已儲存到資料庫)
  DELIVERED = 'delivered', // 已送達 (對方在線並收到訊息)
  READ = 'read'           // 已讀取 (對方已查看訊息)
}
```

**狀態轉換流程**:
```
SENT → DELIVERED → READ
```

---

### 訊息類型 (MessageType)

```typescript
enum MessageType {
  TEXT = 'text',     // 純文字訊息
  IMAGE = 'image',   // 圖片訊息
  AUDIO = 'audio',   // 語音訊息
  FILE = 'file'      // 檔案訊息
}
```

---

### 聊天室 (ChatRoom)

```typescript
interface ChatRoom {
  room_id: string;              // 聊天室 ID (UUID)
  client_id: string;            // 患者 ID (UUID)
  therapist_id: string;         // 治療師 ID (UUID)
  client_name: string;          // 患者姓名
  therapist_name: string;       // 治療師姓名
  created_at: string;           // 建立時間 (ISO 8601)
  updated_at: string;           // 更新時間 (ISO 8601)
  is_active: boolean;           // 是否啟用
  last_message_at: string | null; // 最後訊息時間
  unread_count: number;         // 未讀訊息數量
}
```

---

### 訊息 (Message)

```typescript
interface Message {
  message_id: string;           // 訊息 ID (UUID)
  room_id: string;              // 聊天室 ID (UUID)
  sender_id: string;            // 發送者 ID (UUID)
  sender_name: string;          // 發送者姓名
  content: string;              // 訊息內容
  message_type: MessageType;    // 訊息類型
  status: MessageStatus;        // 訊息狀態
  created_at: string;           // 建立時間 (ISO 8601)
  updated_at: string;           // 更新時間 (ISO 8601)
  delivered_at: string | null;  // 送達時間
  read_at: string | null;       // 已讀時間
  file_url: string | null;      // 檔案 URL
  file_size: number | null;     // 檔案大小 (bytes)
  file_name: string | null;     // 檔案名稱
  is_deleted: boolean;          // 是否已刪除
}
```

---

## 完整範例

### React 聊天組件範例

```typescript
import React, { useState, useEffect, useRef } from 'react';

interface ChatComponentProps {
  roomId: string;
  accessToken: string;
}

const ChatComponent: React.FC<ChatComponentProps> = ({ roomId, accessToken }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 建立 WebSocket 連線
  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/chat/ws/${roomId}?token=${accessToken}`
    );

    ws.onopen = () => {
      console.log('WebSocket 連線已建立');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket 錯誤:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket 連線已關閉');
      setIsConnected(false);
    };

    wsRef.current = ws;

    // 清理函數
    return () => {
      ws.close();
    };
  }, [roomId, accessToken]);

  // 載入歷史訊息
  useEffect(() => {
    loadMessages();
  }, [roomId]);

  const loadMessages = async () => {
    try {
      const response = await fetch(
        `/chat/rooms/${roomId}/messages?limit=50&offset=0`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );
      const data = await response.json();
      setMessages(data.messages);
    } catch (error) {
      console.error('載入訊息失敗:', error);
    }
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'connection_ack':
        console.log('連線確認:', data.message);
        break;

      case 'new_message':
        // 新增訊息到列表
        setMessages(prev => [...prev, data.message]);

        // 自動標記為已讀
        markAsRead([data.message.message_id]);

        // 滾動到底部
        scrollToBottom();
        break;

      case 'message_delivered':
        // 更新訊息狀態為已送達
        setMessages(prev =>
          prev.map(msg =>
            msg.message_id === data.message_id
              ? { ...msg, status: 'delivered', delivered_at: data.delivered_at }
              : msg
          )
        );
        break;

      case 'message_read':
        // 更新訊息狀態為已讀
        setMessages(prev =>
          prev.map(msg =>
            data.message_ids.includes(msg.message_id)
              ? { ...msg, status: 'read', read_at: data.read_at }
              : msg
          )
        );
        break;

      case 'user_typing':
        setIsTyping(true);
        break;

      case 'user_stop_typing':
        setIsTyping(false);
        break;

      case 'error':
        console.error('WebSocket 錯誤:', data.message);
        alert(`錯誤: ${data.message}`);
        break;
    }
  };

  const sendMessage = () => {
    if (!inputValue.trim() || !wsRef.current) return;

    wsRef.current.send(JSON.stringify({
      type: 'send_message',
      content: inputValue,
      message_type: 'text'
    }));

    setInputValue('');

    // 發送停止輸入通知
    wsRef.current.send(JSON.stringify({
      type: 'typing_stop'
    }));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);

    // 發送開始輸入通知
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: 'typing_start'
      }));
    }

    // 清除之前的計時器
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // 3 秒後自動發送停止輸入通知
    typingTimeoutRef.current = setTimeout(() => {
      if (wsRef.current) {
        wsRef.current.send(JSON.stringify({
          type: 'typing_stop'
        }));
      }
    }, 3000);
  };

  const markAsRead = (messageIds: string[]) => {
    if (!wsRef.current) return;

    wsRef.current.send(JSON.stringify({
      type: 'mark_as_read',
      message_ids: messageIds
    }));
  };

  const scrollToBottom = () => {
    // 實作滾動到底部的邏輯
  };

  return (
    <div className="chat-container">
      {/* 連線狀態指示器 */}
      <div className="connection-status">
        {isConnected ? '🟢 已連線' : '🔴 未連線'}
      </div>

      {/* 訊息列表 */}
      <div className="messages-list">
        {messages.map(msg => (
          <div
            key={msg.message_id}
            className={`message ${msg.sender_id === currentUserId ? 'sent' : 'received'}`}
          >
            <div className="message-content">{msg.content}</div>
            <div className="message-time">
              {new Date(msg.created_at).toLocaleTimeString()}
              {msg.sender_id === currentUserId && (
                <span className="message-status">
                  {msg.status === 'sent' && '✓'}
                  {msg.status === 'delivered' && '✓✓'}
                  {msg.status === 'read' && '✓✓ 已讀'}
                </span>
              )}
            </div>
          </div>
        ))}

        {/* 輸入狀態指示器 */}
        {isTyping && (
          <div className="typing-indicator">
            對方正在輸入...
          </div>
        )}
      </div>

      {/* 輸入框 */}
      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="輸入訊息..."
          disabled={!isConnected}
        />
        <button onClick={sendMessage} disabled={!isConnected}>
          發送
        </button>
      </div>
    </div>
  );
};

export default ChatComponent;
```

---

### Vue 3 聊天組件範例

```vue
<template>
  <div class="chat-container">
    <!-- 連線狀態 -->
    <div class="connection-status">
      {{ isConnected ? '🟢 已連線' : '🔴 未連線' }}
    </div>

    <!-- 訊息列表 -->
    <div class="messages-list" ref="messagesList">
      <div
        v-for="msg in messages"
        :key="msg.message_id"
        :class="['message', msg.sender_id === currentUserId ? 'sent' : 'received']"
      >
        <div class="message-content">{{ msg.content }}</div>
        <div class="message-time">
          {{ formatTime(msg.created_at) }}
          <span v-if="msg.sender_id === currentUserId" class="message-status">
            {{ getStatusIcon(msg.status) }}
          </span>
        </div>
      </div>

      <!-- 輸入狀態 -->
      <div v-if="isTyping" class="typing-indicator">
        對方正在輸入...
      </div>
    </div>

    <!-- 輸入框 -->
    <div class="input-container">
      <input
        v-model="inputValue"
        @input="handleInput"
        @keypress.enter="sendMessage"
        placeholder="輸入訊息..."
        :disabled="!isConnected"
      />
      <button @click="sendMessage" :disabled="!isConnected">
        發送
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';

interface Props {
  roomId: string;
  accessToken: string;
  currentUserId: string;
}

const props = defineProps<Props>();

const messages = ref<Message[]>([]);
const inputValue = ref('');
const isTyping = ref(false);
const isConnected = ref(false);
const messagesList = ref<HTMLElement | null>(null);

let ws: WebSocket | null = null;
let typingTimeout: NodeJS.Timeout | null = null;

onMounted(() => {
  connectWebSocket();
  loadMessages();
});

onUnmounted(() => {
  if (ws) {
    ws.close();
  }
});

const connectWebSocket = () => {
  ws = new WebSocket(
    `ws://localhost:8000/chat/ws/${props.roomId}?token=${props.accessToken}`
  );

  ws.onopen = () => {
    console.log('WebSocket 連線已建立');
    isConnected.value = true;
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWebSocketMessage(data);
  };

  ws.onerror = (error) => {
    console.error('WebSocket 錯誤:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket 連線已關閉');
    isConnected.value = false;
  };
};

const loadMessages = async () => {
  try {
    const response = await fetch(
      `/chat/rooms/${props.roomId}/messages?limit=50&offset=0`,
      {
        headers: {
          'Authorization': `Bearer ${props.accessToken}`
        }
      }
    );
    const data = await response.json();
    messages.value = data.messages;
    scrollToBottom();
  } catch (error) {
    console.error('載入訊息失敗:', error);
  }
};

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'new_message':
      messages.value.push(data.message);
      markAsRead([data.message.message_id]);
      scrollToBottom();
      break;

    case 'message_delivered':
      updateMessageStatus(data.message_id, 'delivered', data.delivered_at);
      break;

    case 'message_read':
      data.message_ids.forEach((id: string) => {
        updateMessageStatus(id, 'read', data.read_at);
      });
      break;

    case 'user_typing':
      isTyping.value = true;
      break;

    case 'user_stop_typing':
      isTyping.value = false;
      break;

    case 'error':
      console.error('WebSocket 錯誤:', data.message);
      break;
  }
};

const sendMessage = () => {
  if (!inputValue.value.trim() || !ws) return;

  ws.send(JSON.stringify({
    type: 'send_message',
    content: inputValue.value,
    message_type: 'text'
  }));

  inputValue.value = '';

  ws.send(JSON.stringify({
    type: 'typing_stop'
  }));
};

const handleInput = () => {
  if (!ws) return;

  ws.send(JSON.stringify({
    type: 'typing_start'
  }));

  if (typingTimeout) {
    clearTimeout(typingTimeout);
  }

  typingTimeout = setTimeout(() => {
    if (ws) {
      ws.send(JSON.stringify({
        type: 'typing_stop'
      }));
    }
  }, 3000);
};

const markAsRead = (messageIds: string[]) => {
  if (!ws) return;

  ws.send(JSON.stringify({
    type: 'mark_as_read',
    message_ids: messageIds
  }));
};

const updateMessageStatus = (messageId: string, status: string, timestamp: string) => {
  const message = messages.value.find(msg => msg.message_id === messageId);
  if (message) {
    message.status = status;
    if (status === 'delivered') {
      message.delivered_at = timestamp;
    } else if (status === 'read') {
      message.read_at = timestamp;
    }
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesList.value) {
      messagesList.value.scrollTop = messagesList.value.scrollHeight;
    }
  });
};

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString();
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'sent': return '✓';
    case 'delivered': return '✓✓';
    case 'read': return '✓✓ 已讀';
    default: return '';
  }
};
</script>

<style scoped>
/* 樣式省略 */
</style>
```

---

## 錯誤處理

### HTTP 錯誤碼

| 狀態碼 | 說明 | 處理方式 |
|--------|------|----------|
| 400 | 請求錯誤 | 檢查請求參數是否正確 |
| 401 | 未驗證 | 重新登入取得新的 token |
| 403 | 無權限 | 檢查是否與治療師配對 |
| 404 | 資源不存在 | 檢查聊天室或訊息 ID 是否正確 |
| 500 | 伺服器錯誤 | 聯絡技術支援 |

### WebSocket 錯誤處理

```typescript
const connectWebSocket = () => {
  const ws = new WebSocket(websocketUrl);

  ws.onerror = (error) => {
    console.error('WebSocket 錯誤:', error);
    // 顯示錯誤通知給使用者
    showNotification('連線錯誤,請重新整理頁面');
  };

  ws.onclose = (event) => {
    console.log('WebSocket 關閉:', event.code, event.reason);

    // 如果不是正常關閉,嘗試重新連線
    if (event.code !== 1000) {
      setTimeout(() => {
        console.log('嘗試重新連線...');
        connectWebSocket();
      }, 3000);
    }
  };
};
```

### 常見問題處理

**Q1: WebSocket 連線失敗怎麼辦?**
```typescript
// 檢查 token 是否有效
const isTokenValid = await checkTokenValidity(accessToken);
if (!isTokenValid) {
  // 重新登入
  await refreshToken();
}

// 檢查聊天室權限
const hasAccess = await checkRoomAccess(roomId);
if (!hasAccess) {
  alert('您沒有權限存取此聊天室');
}
```

**Q2: 訊息發送失敗怎麼辦?**
```typescript
const sendMessageWithRetry = async (message: string, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      await sendMessage(message);
      return; // 成功則返回
    } catch (error) {
      console.error(`發送失敗 (第 ${i + 1} 次):`, error);
      if (i === retries - 1) {
        // 最後一次失敗
        alert('訊息發送失敗,請稍後再試');
      } else {
        // 等待後重試
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }
};
```

**Q3: 如何處理斷線重連?**
```typescript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

const reconnectWebSocket = () => {
  if (reconnectAttempts >= maxReconnectAttempts) {
    alert('無法連線至伺服器,請重新整理頁面');
    return;
  }

  reconnectAttempts++;
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);

  setTimeout(() => {
    console.log(`重新連線中... (第 ${reconnectAttempts} 次)`);
    connectWebSocket();
  }, delay);
};

ws.onclose = (event) => {
  if (event.code !== 1000) {
    reconnectWebSocket();
  }
};

ws.onopen = () => {
  reconnectAttempts = 0; // 重置重連次數
};
```

---

## 最佳實踐

### 1. 連線管理

✅ **建議做法**:
- 在組件掛載時建立 WebSocket 連線
- 在組件卸載時關閉連線
- 實作自動重連機制
- 監聽網路狀態變化

```typescript
useEffect(() => {
  // 監聽網路狀態
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}, []);

const handleOnline = () => {
  console.log('網路已連線');
  connectWebSocket();
};

const handleOffline = () => {
  console.log('網路已斷線');
  if (ws) {
    ws.close();
  }
};
```

### 2. 訊息處理

✅ **建議做法**:
- 使用樂觀更新 (Optimistic Update)
- 實作本地快取機制
- 處理重複訊息
- 實作訊息佇列

```typescript
const sendMessageOptimistic = (content: string) => {
  // 立即在 UI 上顯示訊息 (樂觀更新)
  const tempMessage = {
    message_id: `temp-${Date.now()}`,
    content,
    status: 'sending',
    created_at: new Date().toISOString(),
    // ... 其他欄位
  };

  setMessages(prev => [...prev, tempMessage]);

  // 實際發送
  ws.send(JSON.stringify({
    type: 'send_message',
    content,
    message_type: 'text'
  }));
};
```

### 3. 效能優化

✅ **建議做法**:
- 使用虛擬滾動 (Virtual Scrolling) 處理大量訊息
- 實作分頁載入歷史訊息
- 使用防抖 (Debounce) 處理輸入事件
- 適當使用 React.memo 或 Vue computed

```typescript
// 分頁載入更多訊息
const loadMoreMessages = async () => {
  if (loading || !hasMore) return;

  setLoading(true);
  const oldestMessage = messages[0];

  try {
    const response = await fetch(
      `/chat/rooms/${roomId}/messages?limit=50&before_message_id=${oldestMessage.message_id}`,
      {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    );
    const data = await response.json();

    setMessages(prev => [...data.messages, ...prev]);
    setHasMore(data.has_more);
  } catch (error) {
    console.error('載入訊息失敗:', error);
  } finally {
    setLoading(false);
  }
};
```

### 4. 安全性

✅ **建議做法**:
- 定期刷新 token
- 驗證訊息來源
- 過濾惡意內容
- 使用 HTTPS/WSS

```typescript
// 定期刷新 token
useEffect(() => {
  const refreshInterval = setInterval(async () => {
    try {
      const newToken = await refreshAccessToken();
      setAccessToken(newToken);

      // 重新建立 WebSocket 連線
      if (ws) {
        ws.close();
        connectWebSocket();
      }
    } catch (error) {
      console.error('刷新 token 失敗:', error);
    }
  }, 30 * 60 * 1000); // 每 30 分鐘刷新一次

  return () => clearInterval(refreshInterval);
}, []);
```

### 5. 使用者體驗

✅ **建議做法**:
- 顯示連線狀態
- 實作訊息發送狀態指示
- 提供輸入狀態提示
- 自動滾動到最新訊息
- 提供訊息時間戳記

```typescript
// 智慧滾動 - 只在使用者在底部時自動滾動
const shouldAutoScroll = () => {
  if (!messagesList.current) return false;

  const { scrollTop, scrollHeight, clientHeight } = messagesList.current;
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

  return distanceFromBottom < 100; // 距離底部小於 100px
};

useEffect(() => {
  if (shouldAutoScroll()) {
    scrollToBottom();
  }
}, [messages]);
```

---

## 相關資源

- [FastAPI WebSocket 文件](https://fastapi.tiangolo.com/advanced/websockets/)
- [JWT 認證說明](./JWT_AUTH.md)
- [檔案上傳 API](./FILE_UPLOAD.md)
- [後端 API 完整文件](./API_REFERENCE.md)

---

## 變更日誌

### v1.0.0 (2025-01-15)
- 初始版本
- 支援基本聊天功能
- 支援 WebSocket 即時通訊
- 支援多種訊息類型
- 支援訊息狀態追蹤

---

## 技術支援

如有任何問題,請聯絡開發團隊:

- Email: support@vocalborn.com
- 問題回報: [GitHub Issues](https://github.com/vocalborn/backend/issues)

---

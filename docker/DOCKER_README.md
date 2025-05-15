# VocalBorn Docker 設置指南

本文件提供使用 Docker Compose 啟動 VocalBorn 服務的方法。

## 服務

Docker Compose 包含以下服務：

1. **PostgreSQL 17**：主要資料庫
2. **MinIO**：物件儲存服務，用於儲存影片或其他檔案
3. **pgAdmin4**：PostgreSQL 資料庫管理工具
4. **Backend**：VocalBorn FastAPI 後端服務

## 使用方法

### 啟動所有服務

```bash
docker-compose up -d
```

### 停止所有服務

```bash
docker-compose down
```

### 查看服務日誌

```bash
# 所有服務的日誌
docker-compose logs

# 特定服務的日誌，例如後端
docker-compose logs backend
```

## 存取服務

- MinIO 控制台：:4001
- pgAdmin 控制台：:4002
- 後端 API：:4003

## 注意事項

- 首次啟動時，PostgreSQL 和 MinIO 的資料會在 Docker 卷中持久化
- 如需修改環境變數，請編輯 docker-compose.yml 文件中的相應部分 
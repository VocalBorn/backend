# VocalBorn Docker 設置指南

本文件提供使用 Docker Compose 啟動 VocalBorn 服務的方法。

## 服務

Docker Compose 包含以下服務：

1. **PostgreSQL 17**：主要資料庫
   - 連結埠：5432
   - 使用者帳號：vocalborn
   - 密碼：vocalborn_password
   - 資料庫名：vocalborn_db

2. **MinIO**：物件儲存服務，用於儲存影片或其他檔案
   - API 連結埠：9000
   - 控制台連結埠：9001
   - 管理員帳號：minio_admin
   - 管理員密碼：minio_password

3. **pgAdmin4**：PostgreSQL 資料庫管理工具
   - 連結埠：5050
   - 管理員郵件：admin@vocalborn.com
   - 管理員密碼：admin_password

4. **Backend**：VocalBorn FastAPI 後端服務
   - 端口：5000

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

- 後端 API：http://localhost:5000
- MinIO 控制台：http://localhost:9001
- pgAdmin 控制台：http://localhost:5050

## 連接到 PostgreSQL

### 透過 pgAdmin

1. 訪問 http://localhost:5050
2. 使用管理員郵件和密碼登入
3. 添加新伺服器連接：
   - 名稱：VocalBorn
   - 連接內容：
     - 主機：postgres
     - 連結埠：5432
     - 使用者名稱：vocalborn
     - 密碼：vocalborn_password
     - 資料庫：vocalborn_db

### 使用 Minio

1. 打開 http://localhost:9001
2. 使用管理員帳號和密碼登入
3. 建立名為 `vocalborn-bucket` 的新 Bucket

## 注意事項

- 首次啟動時，PostgreSQL 和 MinIO 的資料會在 Docker 卷中持久化
- 如需修改環境變數，請編輯 docker-compose.yml 文件中的相應部分 
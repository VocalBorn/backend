# Celery 管理系統部署指南

## 概覽

VocalBorn Celery 管理系統提供完整的任務管理和監控功能，包括：

- 系統狀態監控
- Worker 管理
- 任務管理
- 佇列管理
- 即時監控和 WebSocket 支持
- 操作審計系統

## 系統要求

### 必需套件
```bash
# 已在 pyproject.toml 中包含
celery==5.4.0
redis==5.2.1
flower==2.0.1
psutil  # 需要手動添加用於系統監控
```

### 環境變數
```bash
# Redis 配置（用作 Celery 訊息代理和結果儲存）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_BROKER=0
REDIS_DB_BACKEND=1
REDIS_PASSWORD=  # 可選

# Celery 配置
CELERY_LOG_LEVEL=INFO
```

## 部署步驟

### 1. 安裝依賴套件
```bash
# 添加系統監控套件
uv add psutil

# 可選：添加更多監控工具
uv add prometheus-client  # 用於 Prometheus 整合
```

### 2. 資料庫遷移
```bash
cd alembic
uv run alembic upgrade head
```

這將創建以下資料表：
- `celery_audit_logs` - 操作審計日誌
- `celery_monitoring_snapshots` - 監控資料快照
- `celery_system_config` - 系統配置
- `celery_task_results_ext` - 擴展任務結果

### 3. 啟動 Celery Worker
```bash
# 啟動主要 AI 分析 Worker
uv run celery -A src.tasks.celery_app.app worker \
    --loglevel=info \
    --queues=ai_analysis \
    --concurrency=4 \
    --hostname=ai_worker@%h

# 啟動維護任務 Worker
uv run celery -A src.tasks.celery_app.app worker \
    --loglevel=info \
    --queues=maintenance,health \
    --concurrency=2 \
    --hostname=maintenance_worker@%h
```

### 4. 啟動 FastAPI 應用程式
```bash
uv run fastapi dev src/main.py
```

### 5. 可選：啟動 Flower（傳統 Celery 監控）
```bash
uv run celery -A src.tasks.celery_app.app flower \
    --port=5555 \
    --broker_api=http://localhost:15672/api/
```

## API 端點

### 系統管理
- `GET /celery-admin/system/status` - 系統狀態
- `GET /celery-admin/system/metrics` - 系統指標
- `GET /celery-admin/system/configuration` - 系統配置
- `POST /celery-admin/system/shutdown` - 關閉系統（超級管理員）
- `POST /celery-admin/system/restart` - 重啟系統（超級管理員）

### 即時監控
- `GET /celery-admin/monitoring/metrics/realtime` - 即時指標
- `GET /celery-admin/monitoring/dashboard` - 監控儀表板
- `POST /celery-admin/monitoring/start` - 啟動監控服務
- `POST /celery-admin/monitoring/stop` - 停止監控服務
- `WS /celery-admin/monitoring/ws` - WebSocket 即時監控

### 健康檢查
- `GET /celery-admin/system/health` - 輕量級健康檢查
- `GET /celery-admin/system/info` - 系統基本資訊（無需認證）

## 權限要求

### 管理員權限 (`admin`)
- 存取所有監控和管理功能
- 查看系統狀態和指標
- 管理 Worker 和任務

### 超級管理員權限 (`super_admin`)
- 系統關閉和重啟
- 修改系統配置
- 存取敏感操作

## 監控和警報

### WebSocket 監控
客戶端連接到 `/celery-admin/monitoring/ws` 可接收：
- 即時系統指標更新
- 任務狀態變化通知
- 系統警報和事件

### 監控指標
系統自動收集：
- 任務執行統計
- Worker 效能指標
- 佇列長度和處理速度
- 系統資源使用

### 審計日誌
所有管理操作都會記錄在 `celery_audit_logs` 表中，包括：
- 操作類型和結果
- 操作者資訊
- 請求和回應資料
- IP 位址和時間戳

## 故障排除

### 常見問題

1. **Redis 連接失敗**
   ```bash
   # 檢查 Redis 服務狀態
   redis-cli ping
   ```

2. **Worker 無法啟動**
   ```bash
   # 檢查 Celery 配置
   uv run python -c "from src.tasks.celery_app import app; print(app.conf)"
   ```

3. **WebSocket 連接失敗**
   - 確認 FastAPI 應用程式正常運行
   - 檢查防火牆設定
   - 驗證用戶權限

### 日誌檢查
```bash
# 查看 Celery Worker 日誌
tail -f /var/log/celery/worker.log

# 查看 FastAPI 應用程式日誌
tail -f /var/log/fastapi/app.log
```

## 效能調整

### Worker 配置
```bash
# 高性能配置
uv run celery -A src.tasks.celery_app.app worker \
    --loglevel=warning \
    --queues=ai_analysis \
    --concurrency=8 \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=1000
```

### Redis 優化
```redis
# redis.conf 建議設定
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 300
```

## 安全性建議

1. **網路安全**
   - 限制管理 API 的存取來源
   - 使用 HTTPS 連接
   - 配置適當的防火牆規則

2. **認證和授權**
   - 定期輪換 JWT 密鑰
   - 監控異常登入活動
   - 實施多重要素驗證

3. **資料保護**
   - 定期備份審計日誌
   - 加密敏感配置資料
   - 實施資料保留政策

## 監控整合

### Prometheus 整合
```python
# 可選：新增 Prometheus 指標導出
from prometheus_client import Counter, Histogram, Gauge

task_counter = Counter('celery_tasks_total', 'Total number of tasks', ['queue', 'status'])
task_duration = Histogram('celery_task_duration_seconds', 'Task execution time', ['queue'])
active_workers = Gauge('celery_active_workers', 'Number of active workers')
```

### 日誌聚合
建議整合到現有的日誌系統（如 ELK Stack）中，以便：
- 集中化日誌管理
- 建立警報規則
- 生成報告和儀表板

## 備份和災難恢復

### 資料備份
```bash
# 備份審計日誌
pg_dump -t celery_audit_logs vocalborn_db > audit_logs_backup.sql

# 備份系統配置
pg_dump -t celery_system_config vocalborn_db > system_config_backup.sql
```

### 災難恢復
1. 恢復資料庫資料
2. 重新部署應用程式
3. 重新啟動 Celery Worker
4. 驗證系統功能

## 版本更新

部署新版本時的建議步驟：
1. 停止新任務提交
2. 等待現有任務完成
3. 停止 Worker 程序
4. 更新應用程式碼
5. 執行資料庫遷移
6. 重新啟動服務
7. 驗證系統功能

---

**注意**：這是一個完整的企業級任務管理系統，建議在生產環境部署前進行充分的測試和調優。
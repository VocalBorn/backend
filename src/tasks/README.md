# VocalBorn Celery 任務系統

這個模組實作 VocalBorn 語言治療學習平台的分散式任務處理系統，基於 Celery + Redis 架構，用於處理 AI 音訊分析等耗時任務。

## 🏗️ 架構概覽

### 核心組件
- **celery_app.py**: Celery 應用配置核心
- **celery_tasks.py**: 任務定義和處理邏輯
- **management.py**: 命令列管理工具
- **usage_examples.py**: 使用範例和最佳實踐

### 系統特性
- ✅ 非同步任務處理，避免 API 阻塞
- ✅ Redis 雙資料庫架構（訊息代理 + 結果儲存）
- ✅ 多佇列支援（AI 分析、維護、健康檢查）
- ✅ 完整的重試和錯誤處理機制
- ✅ 進度追蹤和即時狀態更新
- ✅ 監控和告警支援
- ✅ 水平擴展能力

## 🚀 快速開始

### 1. 環境準備

確保已安裝 Redis 服務：
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

### 2. 配置設定

在 `.env` 檔案中確認以下配置：
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_BROKER=0
REDIS_DB_BACKEND=1

# Celery Configuration
CELERY_LOG_LEVEL=INFO
CELERY_WORKER_CONCURRENCY=4
```

### 3. 啟動服務

```bash
# 啟動 Celery Worker
cd /Users/sindy0514/Dev/VocalBorn/backend
uv run python -m src.tasks.management worker

# 啟動定時任務調度器（另一個終端）
uv run python -m src.tasks.management beat

# 啟動監控介面（可選）
uv run python -m src.tasks.management flower
```

### 4. 驗證安裝

```bash
# 檢查系統狀態
uv run python -m src.tasks.management status

# 執行健康檢查
uv run python -m src.tasks.management health

# 執行測試任務
uv run python -m src.tasks.management test --message "Hello VocalBorn!"
```

## 📋 佇列配置

系統使用三個主要佇列：

| 佇列名稱 | 用途 | 優先級 |
|---------|------|--------|
| `ai_analysis` | AI 音訊分析任務 | 高 |
| `maintenance` | 系統維護任務 | 中 |
| `health` | 健康檢查任務 | 低 |

## 🎯 使用方法

### 基本任務提交

```python
from src.tasks.celery_tasks import analyze_audio_task

# 提交音訊分析任務
task = analyze_audio_task.apply_async(
    args=["practice_record_id_123", {"model_version": "v2.1"}],
    queue='ai_analysis'
)

print(f"任務 ID: {task.id}")
```

### 任務狀態查詢

```python
from src.tasks.celery_app import app

# 查詢任務狀態
result = app.AsyncResult(task_id)
print(f"狀態: {result.status}")
print(f"進度: {result.info}")
```

### 使用任務管理器

```python
from src.tasks.usage_examples import TaskManager

task_manager = TaskManager()

# 提交分析任務
task_id = await task_manager.submit_audio_analysis(
    practice_record_id="123",
    analysis_params={"analysis_type": "full"}
)

# 查詢狀態
status = task_manager.get_task_status(task_id)
print(status)
```

## 🔧 管理工具

使用內建的 CLI 工具管理 Celery 系統：

```bash
# 查看所有可用命令
uv run python -m src.tasks.management --help

# 系統狀態檢查
uv run python -m src.tasks.management status

# 即時監控
uv run python -m src.tasks.management monitor-cmd

# 任務管理
uv run python -m src.tasks.management task <task_id>
uv run python -m src.tasks.management cancel <task_id>

# 佇列管理
uv run python -m src.tasks.management purge --queue ai_analysis
```

## 📊 監控和告警

### Flower 監控介面

訪問 `http://localhost:5555` 查看：
- 即時任務狀態
- Worker 效能指標
- 佇列統計資訊
- 歷史執行記錄

預設帳號: `admin` / `vocalborn2024`

### 系統監控指標

```python
from src.tasks.celery_app import monitor

# Worker 統計
stats = monitor.get_worker_stats()

# 佇列長度
length = monitor.get_queue_length('ai_analysis')

# 清空佇列
count = monitor.purge_queue('maintenance')
```

## 🛠️ 開發指南

### 新增自定義任務

```python
from src.tasks.celery_app import app
from celery import current_task

@app.task(bind=True)
def my_custom_task(self, param1, param2):
    \"\"\"自定義任務範例\"\"\"
    task_id = self.request.id
    
    # 更新進度
    current_task.update_state(
        state='PROGRESS',
        meta={'progress': 50, 'step': '處理中'}
    )
    
    # 任務邏輯
    result = process_data(param1, param2)
    
    return result
```

### 錯誤處理

```python
@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def robust_task(self, data):
    \"\"\"具有錯誤處理的任務\"\"\"
    try:
        return process(data)
    except SpecificError as exc:
        # 特定錯誤處理
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        else:
            # 達到最大重試次數
            raise exc
```

### 進度回調

```python
def progress_callback(current_step: str, progress: int):
    \"\"\"進度更新回調\"\"\"
    current_task.update_state(
        state='PROGRESS',
        meta={
            'current_step': current_step,
            'progress': progress
        }
    )

# 在任務中使用
def long_running_task():
    for i, step in enumerate(steps):
        progress_callback(f'執行步驟 {i+1}', (i+1) * 100 // len(steps))
        process_step(step)
```

## 🔍 故障排除

### 常見問題

#### 1. Redis 連線失敗
```bash
# 檢查 Redis 是否運行
redis-cli ping

# 檢查 Redis 配置
redis-cli info server
```

#### 2. Worker 無法啟動
```bash
# 檢查依賴套件
uv run python -c "import celery; print(celery.__version__)"

# 檢查配置
uv run python -c "from src.tasks.celery_app import app; print(app.conf)"
```

#### 3. 任務卡住不處理
```bash
# 查看 Worker 日誌
uv run python -m src.tasks.management worker --loglevel=DEBUG

# 檢查佇列狀態
uv run python -m src.tasks.management status
```

#### 4. 記憶體使用過高
```bash
# 調整 Worker 設定
export CELERY_WORKER_MAX_TASKS_PER_CHILD=500
export CELERY_WORKER_CONCURRENCY=2
```

### 日誌分析

```bash
# 開啟詳細日誌
export CELERY_LOG_LEVEL=DEBUG

# 查看特定模組日誌
import logging
logging.getLogger('src.tasks').setLevel(logging.DEBUG)
```

## 🚀 效能優化

### Worker 調整

根據系統資源調整 Worker 配置：

```bash
# CPU 密集型任務
uv run python -m src.tasks.management worker --concurrency=4

# I/O 密集型任務
uv run python -m src.tasks.management worker --concurrency=8 --pool=eventlet
```

### Redis 優化

```bash
# Redis 記憶體配置
redis-cli config set maxmemory 2gb
redis-cli config set maxmemory-policy allkeys-lru
```

### 任務設計原則

1. **保持任務輕量**: 避免在任務中載入大量資料
2. **使用進度追蹤**: 為長時間運行的任務提供進度反饋
3. **適當的超時設定**: 設定合理的軟硬超時時間
4. **錯誤處理**: 實作適當的重試和失敗處理邏輯

## 🧪 測試

### 單元測試

```python
import pytest
from src.tasks.celery_tasks import analyze_audio_task

@pytest.mark.asyncio
async def test_audio_analysis_task():
    # 使用測試模式
    task = analyze_audio_task.apply_async(
        args=["test_id", {}],
        queue='ai_analysis'
    )
    
    result = task.get(timeout=30)
    assert result['overall_score'] > 0
```

### 整合測試

```bash
# 執行完整的端到端測試
uv run python -m src.tasks.usage_examples
```

## 📚 參考資料

- [Celery 官方文檔](https://docs.celeryproject.org/)
- [Redis 官方文檔](https://redis.io/documentation)
- [VocalBorn Celery 整合計畫](../../../docs/plans/celery_redis_integration_plan.md)

## 🤝 貢獻指南

1. 遵循現有的程式碼風格和命名慣例
2. 為新任務新增適當的型別註解和文件字串
3. 實作完整的錯誤處理和測試覆蓋
4. 更新相關文件和使用範例

## 📄 授權

此專案遵循 VocalBorn 專案授權條款。
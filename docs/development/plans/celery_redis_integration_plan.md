# VocalBorn Celery + Redis 任務佇列系統整合規劃

## 專案概述

### 專案目標
為 VocalBorn 語言治療學習平台建立一個基於 Celery + Redis 的分散式任務佇列系統，用於處理練習會話的 AI 分析任務。由於 AI 分析任務通常需要 30 秒以上的處理時間，需要避免使用同步等待，改為非同步任務處理架構。

### 核心需求
- **非同步處理**：避免 API 請求阻塞，提升用戶體驗
- **任務追蹤**：完整的任務狀態管理和進度追蹤
- **可靠性**：具備錯誤處理、重試機制和故障恢復能力
- **可擴展性**：支援水平擴展和負載分散
- **監控性**：完整的監控、日誌和告警機制

### 技術堆疊
- **任務佇列**：Celery 5.3+
- **訊息代理**：Redis 7.0+
- **資料庫**：PostgreSQL（現有）
- **Web 框架**：FastAPI（現有）
- **監控工具**：Flower、Prometheus
- **容器化**：Docker + Docker Compose

## 系統架構設計

### 簡化系統架構

```
┌─────────────────────────┐    ┌──────────────────┐    ┌─────────────────────────┐
│      FastAPI App        │    │      Redis       │    │    Celery Workers       │
│                         │    │                  │    │                         │
│ ┌─────────────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────────────┐ │
│ │   Practice API      │◄┼────┼►│  Task Queue  │◄┼────┼►│  AI Analysis Pool   │ │
│ │   (現有路由整合)      │ │    │ │  (FIFO)      │ │    │ │  (2-4 Workers)      │ │
│ └─────────────────────┘ │    │ └──────────────┘ │    │ └─────────────────────┘ │
│ ┌─────────────────────┐ │    │ ┌──────────────┐ │    └─────────────────────────┘
│ │   Task Status API   │◄┼────┼►│ Result Cache │ │               │
│ └─────────────────────┘ │    │ └──────────────┘ │               │
└─────────────────────────┘    └──────────────────┘               │
         │                              │                         │
         └──────────────────────────────┼─────────────────────────┘
                                        │
                           ┌─────────────────────────┐
                           │      PostgreSQL         │
                           │                         │
                           │ ┌─────────────────────┐ │
                           │ │  ai_analysis_tasks  │ │
                           │ │  (任務追蹤)          │ │
                           │ └─────────────────────┘ │
                           │ ┌─────────────────────┐ │
                           │ │ ai_analysis_results │ │
                           │ │  (分析結果)          │ │
                           │ └─────────────────────┘ │
                           │ ┌─────────────────────┐ │
                           │ │  practice_records   │ │
                           │ │  (現有，新增關聯)     │ │
                           │ └─────────────────────┘ │
                           └─────────────────────────┘
```

### 簡化組件說明

#### 1. Redis 單一實例配置
- **任務佇列**：使用單一 Redis 實例，Database 0 存放任務佇列（FIFO 順序）
- **結果緩存**：Database 1 存放任務執行狀態和臨時結果
- **簡化管理**：避免複雜的多資料庫配置，降低維運複雜度

#### 2. Celery Worker 簡化設計
- **單一 Worker Pool**：統一處理所有 AI 分析任務（2-4 個併發 Worker）
- **FIFO 處理**：先進先出，無優先級區分，簡化任務調度邏輯
- **彈性擴展**：根據負載動態調整 Worker 數量

#### 3. 任務佇列簡化
- **ai_analysis**：統一的 AI 分析任務佇列
- **移除複雜分級**：不區分優先級，依提交順序處理
- **故障處理**：簡化的重試機制和錯誤處理

## 資料庫設計

### 新增資料表

#### AIAnalysisTask（任務追蹤表）

```sql
CREATE TABLE ai_analysis_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    celery_task_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- 關聯資訊（配合現有 practice_records 表）
    practice_record_id UUID NOT NULL REFERENCES practice_records(practice_record_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    -- 任務狀態（簡化狀態管理）
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'success', 'failure', 'retry'
    )),
    
    -- 任務配置
    task_type VARCHAR(50) NOT NULL DEFAULT 'audio_analysis',
    task_params JSONB,
    
    -- 執行資訊
    worker_name VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- 進度追蹤
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_step VARCHAR(100),
    
    -- 錯誤處理
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- 時間戳記
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 索引
    CONSTRAINT ai_analysis_tasks_pkey PRIMARY KEY (task_id)
);

-- 建立索引
CREATE INDEX idx_ai_analysis_tasks_celery_task_id ON ai_analysis_tasks(celery_task_id);
CREATE INDEX idx_ai_analysis_tasks_practice_session_id ON ai_analysis_tasks(practice_session_id);
CREATE INDEX idx_ai_analysis_tasks_user_id ON ai_analysis_tasks(user_id);
CREATE INDEX idx_ai_analysis_tasks_status ON ai_analysis_tasks(status);
CREATE INDEX idx_ai_analysis_tasks_created_at ON ai_analysis_tasks(created_at);
```

#### AIAnalysisResult（分析結果表）

```sql
CREATE TABLE ai_analysis_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID UNIQUE NOT NULL REFERENCES ai_analysis_tasks(task_id),
    
    -- 分析結果
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    pronunciation_accuracy DECIMAL(5,2) CHECK (pronunciation_accuracy >= 0 AND pronunciation_accuracy <= 100),
    fluency_score DECIMAL(5,2) CHECK (fluency_score >= 0 AND fluency_score <= 100),
    rhythm_score DECIMAL(5,2) CHECK (rhythm_score >= 0 AND rhythm_score <= 100),
    
    -- 詳細分析數據
    detailed_analysis JSONB NOT NULL,
    sentence_analyses JSONB,
    
    -- AI 建議
    suggestions TEXT,
    improvement_areas JSONB,
    
    -- 元資料
    analysis_model_version VARCHAR(50),
    processing_time_seconds DECIMAL(10,3),
    
    -- 時間戳記
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT ai_analysis_results_pkey PRIMARY KEY (result_id)
);

-- 建立索引
CREATE INDEX idx_ai_analysis_results_task_id ON ai_analysis_results(task_id);
CREATE INDEX idx_ai_analysis_results_created_at ON ai_analysis_results(created_at);
```

### 現有資料表修改

#### PracticeRecord 表關聯調整

由於現有的 `practice_records` 表已經包含完整的狀態管理（`record_status` 包含 `AI_QUEUED`, `AI_PROCESSING`, `AI_ANALYZED` 等狀態），我們只需要新增與任務追蹤的關聯：

```sql
-- 新增 AI 任務追蹤欄位到 practice_records 表
ALTER TABLE practice_records 
ADD COLUMN ai_task_id UUID REFERENCES ai_analysis_tasks(task_id);

-- 建立索引
CREATE INDEX idx_practice_records_ai_task_id ON practice_records(ai_task_id);
```

## API 設計

### 任務管理 API

#### 1. 提交分析任務

```http
POST /api/v1/tasks/analysis/submit
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
    "practice_session_id": "uuid",
    "parameters": {
        "analysis_type": "full",
        "include_suggestions": true,
        "model_version": "v2.1"
    }
}
```

**回應**：
```json
{
    "task_id": "uuid",
    "celery_task_id": "string",
    "status": "pending",
    "estimated_completion_time": "2024-01-01T12:30:00Z",
    "queue_position": 3
}
```

#### 2. 查詢任務狀態

```http
GET /api/v1/tasks/analysis/{task_id}/status
Authorization: Bearer {jwt_token}
```

**回應**：
```json
{
    "task_id": "uuid",
    "status": "processing",
    "progress": 65,
    "current_step": "語音特徵提取",
    "total_steps": 5,
    "started_at": "2024-01-01T12:00:00Z",
    "estimated_remaining_time": "PT45S",
    "worker_name": "worker-ai-001"
}
```

#### 3. 獲取分析結果

```http
GET /api/v1/tasks/analysis/{task_id}/result
Authorization: Bearer {jwt_token}
```

**回應**：
```json
{
    "task_id": "uuid",
    "result_id": "uuid",
    "overall_score": 85.5,
    "pronunciation_accuracy": 88.2,
    "fluency_score": 82.1,
    "rhythm_score": 86.9,
    "detailed_analysis": {
        "phoneme_analysis": [...],
        "timing_analysis": [...],
        "pitch_analysis": [...]
    },
    "suggestions": "建議加強子音發音的清晰度...",
    "improvement_areas": ["子音發音", "語調變化"],
    "processing_time_seconds": 42.3,
    "completed_at": "2024-01-01T12:01:30Z"
}
```

#### 4. 批量查詢會話任務

```http
GET /api/v1/tasks/analysis/session/{session_id}/status
Authorization: Bearer {jwt_token}
```

#### 5. WebSocket 即時通知

```javascript
// WebSocket 連線
const ws = new WebSocket('ws://localhost:8000/api/v1/tasks/ws/task/{task_id}');

// 接收進度更新
ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log('任務進度更新:', update);
    /*
    {
        "task_id": "uuid",
        "status": "processing",
        "progress": 75,
        "current_step": "生成建議",
        "timestamp": "2024-01-01T12:01:15Z"
    }
    */
};
```

### 管理員 API

#### 1. 系統監控

```http
GET /api/v1/admin/tasks/stats
Authorization: Bearer {admin_jwt_token}
```

#### 2. 任務管理

```http
# 取消任務
DELETE /api/v1/admin/tasks/{task_id}

# 重新執行任務
POST /api/v1/admin/tasks/{task_id}/retry

# 清理過期任務
POST /api/v1/admin/tasks/cleanup
```

## 與現有架構整合的核心服務

### 任務服務（TaskService）

配合現有的 `practice` 模組架構，任務服務將整合到現有的服務結構中：

```python
# src/tasks/services/task_service.py
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlmodel import Session, select
from celery import Celery

from ..models import AIAnalysisTask, AIAnalysisResult, TaskStatus
from ..celery_tasks import analyze_audio_task
from ...shared.database.database import get_session
from ...practice.models import PracticeRecord, PracticeRecordStatus

class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.celery_app = Celery('vocalborn_tasks')
    
    async def submit_analysis_task(
        self,
        practice_record_id: UUID,
        user_id: UUID,
        task_params: Optional[Dict[str, Any]] = None
    ) -> AIAnalysisTask:
        """提交 AI 分析任務（配合現有 PracticeRecord）"""
        
        # 驗證 practice_record 存在且屬於該用戶
        practice_record = self.db.exec(
            select(PracticeRecord).where(
                PracticeRecord.practice_record_id == practice_record_id,
                PracticeRecord.practice_session.has(user_id=user_id)
            )
        ).first()
        
        if not practice_record:
            raise ValueError("Practice record not found or access denied")
        
        # 建立任務記錄
        task = AIAnalysisTask(
            practice_record_id=practice_record_id,
            user_id=user_id,
            task_params=task_params or {},
            status=TaskStatus.PENDING
        )
        
        self.db.add(task)
        self.db.flush()  # 確保獲得 task_id
        
        # 更新 practice_record 狀態
        practice_record.record_status = PracticeRecordStatus.AI_QUEUED
        practice_record.ai_task_id = task.task_id
        
        self.db.commit()
        self.db.refresh(task)
        
        # 提交到 Celery（簡化版本）
        celery_task = analyze_audio_task.apply_async(
            args=[str(practice_record_id), task_params],
            task_id=str(task.task_id),
            queue='ai_analysis'
        )
        
        # 更新 Celery 任務 ID
        task.celery_task_id = celery_task.id
        self.db.commit()
        
        return task
    
    async def get_task_status(self, task_id: UUID, user_id: UUID) -> Optional[AIAnalysisTask]:
        """獲取任務狀態"""
        statement = select(AIAnalysisTask).where(
            AIAnalysisTask.task_id == task_id,
            AIAnalysisTask.user_id == user_id
        )
        return self.db.exec(statement).first()
    
    async def get_analysis_result(self, task_id: UUID, user_id: UUID) -> Optional[AIAnalysisResult]:
        """獲取分析結果"""
        statement = select(AIAnalysisResult).join(AIAnalysisTask).where(
            AIAnalysisTask.task_id == task_id,
            AIAnalysisTask.user_id == user_id,
            AIAnalysisTask.status == TaskStatus.SUCCESS
        )
        return self.db.exec(statement).first()
    
```

### 整合現有架構的 Celery 任務處理器

```python
# src/tasks/celery_tasks.py
import logging
from celery import current_task
from typing import Dict, Any
from uuid import UUID

from .celery_app import app
from .services.ai_analysis_service import AIAnalysisService
from .models import TaskStatus
from .utils.task_updater import update_task_status
from ..practice.models import PracticeRecord, PracticeRecordStatus
from ..shared.database.database import get_session

logger = logging.getLogger(__name__)

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def analyze_audio_task(self, practice_record_id: str, analysis_params: Dict[str, Any]):
    """音訊分析任務（配合現有 PracticeRecord）"""
    task_id = self.request.id
    
    try:
        # 更新任務狀態為處理中
        update_task_status(task_id, TaskStatus.PROCESSING)
        
        # 更新 practice_record 狀態
        with get_session() as db:
            practice_record = db.get(PracticeRecord, UUID(practice_record_id))
            if practice_record:
                practice_record.record_status = PracticeRecordStatus.AI_PROCESSING
                db.commit()
        
        # 初始化 AI 分析服務
        ai_service = AIAnalysisService()
        
        # 執行分析（包含進度回調）
        def progress_callback(step: str, progress: int):
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'current_step': step,
                    'progress': progress
                }
            )
            update_task_status(
                task_id, 
                TaskStatus.PROCESSING, 
                progress=progress,
                current_step=step
            )
        
        # 執行 AI 分析
        result = ai_service.analyze_practice_record(
            practice_record_id, 
            analysis_params,
            progress_callback=progress_callback
        )
        
        # 儲存分析結果
        ai_service.save_analysis_result(task_id, result)
        
        # 更新狀態為成功
        update_task_status(task_id, TaskStatus.SUCCESS, progress=100)
        
        # 更新 practice_record 狀態為 AI 分析完成
        with get_session() as db:
            practice_record = db.get(PracticeRecord, UUID(practice_record_id))
            if practice_record:
                practice_record.record_status = PracticeRecordStatus.AI_ANALYZED
                db.commit()
        
        logger.info(f"任務 {task_id} 執行成功")
        return result
        
    except Exception as exc:
        # 記錄錯誤
        logger.error(f"任務 {task_id} 執行失敗: {str(exc)}")
        
        # 更新錯誤狀態
        update_task_status(task_id, TaskStatus.FAILURE, error_message=str(exc))
        
        # 更新 practice_record 狀態
        with get_session() as db:
            practice_record = db.get(PracticeRecord, UUID(practice_record_id))
            if practice_record:
                practice_record.record_status = PracticeRecordStatus.RECORDED  # 回到錄音狀態
                db.commit()
        
        # 決定是否重試
        if self.request.retries < self.max_retries:
            update_task_status(task_id, TaskStatus.RETRY)
            logger.info(f"任務 {task_id} 準備重試 (第 {self.request.retries + 1} 次)")
            raise self.retry(exc=exc)
        else:
            logger.error(f"任務 {task_id} 達到最大重試次數，標記為失敗")
            raise exc

@app.task
def cleanup_expired_tasks():
    """清理過期任務（定時任務）"""
    from datetime import datetime, timedelta
    from .services.task_cleanup_service import TaskCleanupService
    
    cleanup_service = TaskCleanupService()
    
    # 清理超過 7 天的已完成任務
    cutoff_date = datetime.now() - timedelta(days=7)
    cleaned_count = cleanup_service.cleanup_completed_tasks(cutoff_date)
    
    logger.info(f"清理了 {cleaned_count} 個過期任務")
    return cleaned_count

@app.task
def health_check():
    """健康檢查任務"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

## 錯誤處理與監控

### 錯誤處理策略

#### 1. 任務層級錯誤處理

```python
# src/tasks/error_handlers.py
from enum import Enum
from typing import Dict, Any, Optional
import logging

class ErrorType(Enum):
    NETWORK_ERROR = "network_error"
    AI_SERVICE_ERROR = "ai_service_error"
    DATA_VALIDATION_ERROR = "data_validation_error"
    RESOURCE_ERROR = "resource_error"
    TIMEOUT_ERROR = "timeout_error"

class TaskErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_strategies = {
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.AI_SERVICE_ERROR: self._handle_ai_service_error,
            ErrorType.DATA_VALIDATION_ERROR: self._handle_validation_error,
            ErrorType.RESOURCE_ERROR: self._handle_resource_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
        }
    
    def handle_error(self, error: Exception, task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """統一錯誤處理入口"""
        error_type = self._classify_error(error)
        handler = self.error_strategies.get(error_type, self._handle_unknown_error)
        
        return handler(error, task_id, context)
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """錯誤分類"""
        error_name = error.__class__.__name__
        error_message = str(error).lower()
        
        if "network" in error_message or "connection" in error_message:
            return ErrorType.NETWORK_ERROR
        elif "timeout" in error_message:
            return ErrorType.TIMEOUT_ERROR
        elif "validation" in error_message:
            return ErrorType.DATA_VALIDATION_ERROR
        elif "memory" in error_message or "resource" in error_message:
            return ErrorType.RESOURCE_ERROR
        else:
            return ErrorType.AI_SERVICE_ERROR
    
    def _handle_network_error(self, error: Exception, task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理網路錯誤"""
        return {
            "should_retry": True,
            "retry_delay": 30,
            "max_retries": 5,
            "error_message": f"網路連線錯誤: {str(error)}"
        }
    
    def _handle_timeout_error(self, error: Exception, task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理超時錯誤"""
        return {
            "should_retry": True,
            "retry_delay": 60,
            "max_retries": 2,
            "error_message": f"任務執行超時: {str(error)}"
        }
    
    def _handle_validation_error(self, error: Exception, task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理資料驗證錯誤"""
        return {
            "should_retry": False,
            "error_message": f"資料驗證失敗: {str(error)}"
        }
```

#### 2. 監控和告警

```python
# src/tasks/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import logging
from typing import Dict, Any

# Prometheus 指標定義
TASK_COUNTER = Counter('celery_tasks_total', 'Total number of tasks', ['task_name', 'status'])
TASK_DURATION = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])
ACTIVE_TASKS = Gauge('celery_active_tasks', 'Number of active tasks')
QUEUE_SIZE = Gauge('celery_queue_size', 'Queue size', ['queue_name'])
ERROR_COUNTER = Counter('celery_task_errors_total', 'Task errors', ['task_name', 'error_type'])

class TaskMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def record_task_start(self, task_name: str, task_id: str):
        """記錄任務開始"""
        self.logger.info(f"任務開始: {task_id} ({task_name})")
        TASK_COUNTER.labels(task_name=task_name, status='started').inc()
        ACTIVE_TASKS.inc()
    
    def record_task_success(self, task_name: str, task_id: str, duration: float):
        """記錄任務成功完成"""
        self.logger.info(f"任務完成: {task_id} ({task_name}) - 耗時 {duration:.2f}s")
        TASK_COUNTER.labels(task_name=task_name, status='success').inc()
        TASK_DURATION.labels(task_name=task_name).observe(duration)
        ACTIVE_TASKS.dec()
    
    def record_task_failure(self, task_name: str, task_id: str, error_type: str, error_message: str):
        """記錄任務失敗"""
        self.logger.error(f"任務失敗: {task_id} ({task_name}) - 錯誤類型: {error_type}, 訊息: {error_message}")
        TASK_COUNTER.labels(task_name=task_name, status='failure').inc()
        ERROR_COUNTER.labels(task_name=task_name, error_type=error_type).inc()
        ACTIVE_TASKS.dec()
    
    def update_queue_metrics(self, queue_metrics: Dict[str, int]):
        """更新佇列指標"""
        for queue_name, size in queue_metrics.items():
            QUEUE_SIZE.labels(queue_name=queue_name).set(size)
```

### 告警規則配置

```yaml
# monitoring/alerts.yml
groups:
  - name: celery_alerts
    rules:
      - alert: CeleryTaskFailureRate
        expr: rate(celery_task_errors_total[5m]) / rate(celery_tasks_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Celery 任務失敗率過高"
          description: "最近 5 分鐘內任務失敗率超過 10%"
      
      - alert: CeleryQueueBacklog
        expr: celery_queue_size > 100
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Celery 佇列積壓嚴重"
          description: "佇列 {{ $labels.queue_name }} 積壓任務超過 100 個"
      
      - alert: CeleryWorkerDown
        expr: celery_active_tasks == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Celery Worker 可能已停止"
          description: "沒有檢測到活躍的任務處理"
```

## 部署配置

### Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Redis 服務
  redis:
    image: redis:7-alpine
    container_name: vocalborn-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    networks:
      - vocalborn_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker - 簡化單一池
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: vocalborn-celery-worker
    command: uv run celery -A src.tasks.celery_app worker --loglevel=info --queues=ai_analysis --concurrency=4 --hostname=worker@%h
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DATABASE_URL=postgresql://user:password@postgres:5432/vocalborn
      - AI_SERVICE_URL=http://ai-service:8001
    depends_on:
      - redis
      - postgres
    networks:
      - vocalborn_network
    volumes:
      - ./logs/celery:/app/logs
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    restart: unless-stopped

  # Celery Beat - 定時任務調度器
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: vocalborn-celery-beat
    command: uv run celery -A src.tasks.celery_app beat --loglevel=info --schedule=/app/celerybeat-schedule
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:password@postgres:5432/vocalborn
    depends_on:
      - redis
      - postgres
    networks:
      - vocalborn_network
    volumes:
      - ./logs/celery:/app/logs
      - celery_beat_data:/app
    restart: unless-stopped

  # Flower - 監控介面
  celery-flower:
    build:
      context: .
      dockerfile: Dockerfile.celery
    container_name: vocalborn-celery-flower
    command: uv run celery -A src.tasks.celery_app flower --port=5555 --basic_auth=admin:vocalborn2024
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
    networks:
      - vocalborn_network
    restart: unless-stopped

  # FastAPI 應用（現有，需要更新環境變數）
  api:
    build: .
    container_name: vocalborn-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/vocalborn
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - postgres
      - redis
    networks:
      - vocalborn_network
    restart: unless-stopped

volumes:
  redis_data:
  celery_beat_data:

networks:
  vocalborn_network:
    driver: bridge
```

### Celery Dockerfile

```dockerfile
# Dockerfile.celery
FROM python:3.13-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製專案檔案
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# 安裝 uv 和依賴
RUN pip install uv
RUN uv sync --frozen

# 建立日誌目錄
RUN mkdir -p /app/logs

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 建立非 root 用戶
RUN useradd --create-home --shell /bin/bash celery
RUN chown -R celery:celery /app
USER celery

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD uv run celery -A src.tasks.celery_app inspect ping || exit 1

# 預設命令
CMD ["uv", "run", "celery", "-A", "src.tasks.celery_app", "worker", "--loglevel=info"]
```

### 環境變數配置

```bash
# .env.production
# Database
DATABASE_URL=postgresql://vocalborn_user:secure_password@postgres:5432/vocalborn

# Celery/Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
CELERY_WORKER_PREFETCH_MULTIPLIER=1

# AI Service
AI_SERVICE_URL=http://ai-service:8001
AI_SERVICE_API_KEY=your_ai_service_api_key

# File Processing
MAX_AUDIO_FILE_SIZE=52428800  # 50MB
SUPPORTED_AUDIO_FORMATS=mp3,wav,m4a,aac

# Monitoring
PROMETHEUS_ENABLED=true
FLOWER_BASIC_AUTH=admin:vocalborn2024

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 簡化實作階段規劃

### 第一階段：基礎架構建設（第 1-2 週）

#### 目標
建立簡化的 Celery + Redis 環境，與現有 `practice` 模組整合

#### 工作項目
1. **環境搭建**（2 天）
   - Redis 單一實例安裝和配置
   - Celery 基礎配置（單一佇列）
   - 簡化 Docker 配置

2. **資料庫設計**（2 天）
   - 建立任務追蹤表（AIAnalysisTask）配合現有 PracticeRecord
   - 建立分析結果表（AIAnalysisResult）
   - 建立 Alembic 遷移腳本
   - 與現有 `practice_records` 表關聯

3. **整合現有架構**（3 天）
   - 在現有 `practice` 模組中新增任務相關服務
   - 整合到現有路由結構 (`practice/routers/`)
   - 配合現有認證和權限系統

4. **基礎 API 整合**（3 天）
   - 在現有練習 API 中新增任務提交功能
   - 任務狀態查詢整合到現有 API
   - 配合現有錯誤處理模式

#### 驗收標準
- [ ] Redis 和 Celery 可正常運行（單一佇列模式）
- [ ] 資料庫表結構與現有架構整合完成
- [ ] API 整合到現有路由系統
- [ ] 配合現有認證授權機制

### 第二階段：任務處理邏輯（第 3-4 週）

#### 目標
實作簡化的任務處理流程和 AI 分析整合

#### 工作項目
1. **Celery 任務處理器**（3 天）
   - 簡化的 AI 分析任務處理器
   - 配合現有 `PracticeRecord` 狀態管理
   - 基礎進度追蹤機制

2. **AI 服務整合**（4 天）
   - AI 分析服務客戶端開發
   - 配合現有音訊儲存系統 (`storage` 模組)
   - 結果解析和儲存到資料庫

3. **錯誤處理機制**（2 天）
   - 簡化的重試邏輯
   - 配合現有錯誤處理模式
   - 任務失敗時狀態回退機制

4. **系統整合測試**（1 天）
   - 端到端流程測試
   - 與現有功能相容性測試

#### 驗收標準
- [ ] 任務與現有 `PracticeRecord` 流程完整整合
- [ ] AI 分析結果正確儲存並可查詢
- [ ] 錯誤處理配合現有系統邏輯
- [ ] 不影響現有功能正常運作

### 第三階段：監控和維運準備（第 5-6 週）

#### 目標
建立完善的監控系統和效能優化

#### 工作項目
1. **基礎監控**（2 天）
   - Flower 監控介面配置
   - 基礎系統監控指標
   - 任務執行狀態監控

2. **效能調優**（3 天）
   - Worker 數量和併發調整
   - 記憶體使用優化
   - 任務處理時間優化

3. **簡化告警**（2 天）
   - 基礎告警規則（任務失敗、佇列積壓）
   - 簡單通知機制
   - 日誌記錄改善

4. **整合測試**（3 天）
   - 與現有系統整合測試
   - 基本負載測試
   - 用戶流程端到端測試

#### 驗收標準
- [ ] 基礎監控功能運作正常
- [ ] 系統整合穩定運行
- [ ] 基礎告警機制有效
- [ ] 符合業務基本需求

### 第四階段：部署和上線（第 7-8 週）

#### 目標
準備生產環境部署和建立維運流程

#### 工作項目
1. **生產環境準備**（3 天）
   - 簡化的 Docker Compose 生產配置
   - 基礎環境變數配置
   - 必要的安全設定

2. **部署流程**（2 天）
   - 配合現有部署流程
   - 資料庫遷移執行
   - 服務啟動順序規劃

3. **維運文件**（2 天）
   - 基礎操作手冊
   - 常見問題處理指南
   - 系統監控要點

4. **上線驗證**（3 天）
   - 生產環境功能驗證
   - 與現有系統相容性確認
   - 用戶接受度測試

#### 驗收標準
- [ ] 生產環境成功部署並穩定運行
- [ ] 與現有系統無縫整合
- [ ] 基礎維運文件完備
- [ ] 用戶可正常使用新功能

## 風險評估與緩解策略

### 技術風險

#### 1. AI 服務可用性風險
**風險描述**：外部 AI 服務不穩定或回應緩慢
**影響程度**：高
**緩解策略**：
- 實作服務熔斷器模式
- 設置多個 AI 服務提供商備援
- 建立本地快取機制
- 實作服務降級策略

#### 2. Redis 單點故障風險
**風險描述**：Redis 服務故障導致任務佇列不可用
**影響程度**：高
**緩解策略**：
- 配置 Redis 主從複製
- 實作 Redis Sentinel 高可用方案
- 建立定期備份機制
- 準備快速恢復流程

#### 3. 任務處理能力不足風險
**風險描述**：高峰期任務積壓，用戶等待時間過長
**影響程度**：中
**緩解策略**：
- 實作動態 Worker 擴展
- 建立任務優先級機制
- 設置合理的任務超時時間
- 實作任務預處理和批量處理

### 業務風險

#### 1. 用戶體驗下降風險
**風險描述**：任務處理時間過長影響用戶體驗
**影響程度**：中
**緩解策略**：
- 提供準確的完成時間預估
- 實作即時進度通知
- 設計良好的等待頁面
- 提供任務取消功能

#### 2. 資料安全風險
**風險描述**：用戶音訊資料在處理過程中可能洩露
**影響程度**：高
**緩解策略**：
- 實作端到端加密
- 定期清理暫存檔案
- 設置嚴格的存取權限
- 建立審計日誌

### 營運風險

#### 1. 維運複雜度增加風險
**風險描述**：系統複雜度增加，維運難度提升
**影響程度**：中
**緩解策略**：
- 建立完整監控體系
- 撰寫詳細操作文件
- 實作自動化運維工具
- 建立標準化故障處理流程

#### 2. 成本控制風險
**風險描述**：系統資源消耗超出預算
**影響程度**：中
**緩解策略**：
- 實作資源使用監控
- 設置自動擴縮容機制
- 建立成本告警系統
- 定期檢視和優化資源配置

## 測試策略

### 單元測試

```python
# tests/tasks/test_task_service.py
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.tasks.services.task_service import TaskService
from src.tasks.models import TaskStatus

class TestTaskService:
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def task_service(self, mock_db):
        return TaskService(mock_db)
    
    @pytest.mark.asyncio
    async def test_submit_analysis_task(self, task_service, mock_db):
        """測試提交分析任務"""
        practice_session_id = uuid4()
        user_id = uuid4()
        
        with patch.object(task_service, 'celery_app') as mock_celery:
            mock_celery.apply_async.return_value.id = "test-celery-id"
            
            task = await task_service.submit_analysis_task(
                practice_session_id=practice_session_id,
                user_id=user_id,
                priority=TaskPriority.NORMAL
            )
            
            assert task.practice_session_id == practice_session_id
            assert task.user_id == user_id
            assert task.status == TaskStatus.PENDING
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called()
```

### 整合測試

```python
# tests/tasks/test_celery_integration.py
import pytest
from celery import Celery
from unittest.mock import patch

from src.tasks.celery_tasks import analyze_audio_task

class TestCeleryIntegration:
    @pytest.fixture
    def celery_app(self):
        app = Celery('test_app')
        app.config_from_object('src.tasks.test_config')
        return app
    
    @pytest.mark.asyncio
    async def test_analyze_audio_task_success(self, celery_app):
        """測試音訊分析任務成功執行"""
        practice_session_id = str(uuid4())
        analysis_params = {"model_version": "v2.1"}
        
        with patch('src.tasks.services.ai_analysis_service.AIAnalysisService') as mock_service:
            mock_service.return_value.analyze_practice_session.return_value = {
                "overall_score": 85.5
            }
            
            result = analyze_audio_task.apply(
                args=[practice_session_id, analysis_params]
            )
            
            assert result.successful()
            assert result.result["overall_score"] == 85.5
```

### 效能測試

```python
# tests/performance/test_task_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestTaskPerformance:
    @pytest.mark.performance
    async def test_concurrent_task_submission(self):
        """測試併發任務提交效能"""
        task_service = TaskService(get_test_db())
        
        async def submit_task():
            return await task_service.submit_analysis_task(
                practice_session_id=uuid4(),
                user_id=uuid4()
            )
        
        start_time = time.time()
        tasks = await asyncio.gather(*[submit_task() for _ in range(100)])
        end_time = time.time()
        
        assert len(tasks) == 100
        assert (end_time - start_time) < 5.0  # 100 個任務應在 5 秒內完成
    
    @pytest.mark.performance
    def test_task_processing_throughput(self):
        """測試任務處理吞吐量"""
        # 提交 1000 個測試任務
        # 測量處理時間和成功率
        # 驗證系統在高負載下的表現
        pass
```

## 維運指南

### 日常監控檢查項目

#### 每日檢查
- [ ] Celery Worker 狀態正常
- [ ] Redis 連線狀態正常
- [ ] 任務佇列長度在合理範圍
- [ ] 錯誤率低於 5%
- [ ] 平均任務處理時間在 SLA 範圍內

#### 每週檢查
- [ ] 系統資源使用趨勢
- [ ] 任務處理效能趨勢
- [ ] 錯誤日誌分析
- [ ] 容量規劃評估

#### 每月檢查
- [ ] 系統效能全面評估
- [ ] 監控告警規則檢視
- [ ] 備份和恢復測試
- [ ] 安全性檢查

### 故障處理流程

#### 任務佇列積壓處理
1. 檢查 Worker 狀態
2. 檢查 Redis 連線
3. 檢查 AI 服務可用性
4. 必要時手動擴展 Worker 數量
5. 分析積壓原因並建立預防措施

#### Worker 異常停止處理
1. 檢查 Worker 日誌
2. 檢查系統資源使用情況
3. 重新啟動異常 Worker
4. 監控重啟後的運行狀態
5. 必要時調整 Worker 配置

#### Redis 服務故障處理
1. 檢查 Redis 服務狀態
2. 嘗試重新啟動 Redis 服務
3. 如有備份，從備份恢復
4. 通知相關團隊服務中斷情況
5. 服務恢復後驗證資料完整性

### 效能調優建議

#### Worker 配置優化
- 根據 CPU 核心數調整併發數
- 設置合適的任務預取數量
- 配置記憶體使用限制
- 定期重新啟動 Worker 避免記憶體洩漏

#### Redis 配置優化
- 設置合適的記憶體限制和淘汰策略
- 啟用持久化配置
- 調整連線池大小
- 監控記憶體使用情況

#### 資料庫優化
- 建立適當的索引
- 定期清理過期資料
- 監控查詢效能
- 考慮讀寫分離

## 總結

這個 Celery + Redis 任務佇列系統整合規劃提供了完整的架構設計、實作指導和維運方案。透過分階段實作，可以確保系統的穩定性和可靠性，同時為 VocalBorn 平台提供高效能的 AI 分析處理能力。

### 關鍵優勢

1. **非同步處理**：避免 API 阻塞，提升用戶體驗
2. **可擴展性**：支援水平擴展，應對業務增長
3. **可靠性**：完整的錯誤處理和重試機制
4. **監控性**：全面的監控和告警體系
5. **維運性**：標準化的維運流程和文件

### 成功關鍵因素

1. **團隊培訓**：確保開發和維運團隊熟悉 Celery 和 Redis
2. **分階段實作**：避免一次性大規模變更的風險
3. **充分測試**：包含單元測試、整合測試和效能測試
4. **監控完善**：建立全面的監控和告警機制
5. **文件完整**：提供詳細的操作和維運文件

通過遵循這個規劃，VocalBorn 平台將能夠成功整合 Celery + Redis 任務佇列系統，為用戶提供更好的 AI 分析體驗。
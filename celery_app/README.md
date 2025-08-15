# VocalBorn Celery 任務系統

簡化的 Celery 任務處理系統，用於處理 AI 音訊分析等耗時任務。

## 快速開始

### 啟動 Worker
```bash
celery -A celery_app.worker.celery worker --loglevel=info --logfile=logs/celery.log
```

### 啟動 Beat (定時任務)
```bash
celery -A celery_app.worker.celery beat --loglevel=info
```

### 啟動 Flower (監控介面)
```bash
celery -A celery_app.worker.celery flower --port=5555
```

## 其他命令

### 查看狀態
```bash
celery -A celery_app.worker.celery status
```

### 清空佇列
```bash
celery -A celery_app.worker.celery purge
```

### 檢查任務
```bash
celery -A celery_app.worker.celery inspect active
```

## 檔案結構
- `worker.py` - Celery 應用入口點
- `app.py` - 應用配置
- `tasks.py` - 任務匯入檔案
- `tasks/` - 任務模組資料夾
  - `__init__.py` - 任務模組匯出
  - `analyze_audio.py` - AI 音訊分析任務
  - `cleanup_expired.py` - 清理過期任務
  - `health_check.py` - 健康檢查任務
  - `test_task.py` - 測試任務
  - `utils.py` - 共用工具函數
- `__init__.py` - 模組匯出

## 可用任務
- `analyze_audio_task` - AI 音訊分析
- `cleanup_expired_tasks` - 清理過期任務
- `health_check` - 健康檢查
- `test_task` - 測試任務
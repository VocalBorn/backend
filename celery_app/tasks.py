"""
VocalBorn Celery 任務匯入檔案

這個檔案從 tasks 資料夾中匯入所有任務，提供統一的入口點。
為了保持向後相容性，所有任務都透過這個檔案匯出。
"""

# 從各個任務模組匯入任務
from .tasks.analyze_audio import analyze_audio_task
from .tasks.cleanup_expired import cleanup_expired_tasks
from .tasks.health_check import health_check
from .tasks.test_task import test_task

# Beat 排程配置
CELERYBEAT_SCHEDULE = {
    'cleanup-expired-tasks': {
        'task': 'celery_app.tasks.cleanup_expired_tasks',
        'schedule': 3600.0,  # 每小時執行一次
        'options': {'queue': 'maintenance'}
    },
    'health-check': {
        'task': 'celery_app.tasks.health_check',
        'schedule': 300.0,   # 每 5 分鐘執行一次
        'options': {'queue': 'health'}
    },
}

# 匯出所有任務
__all__ = [
    "analyze_audio_task",
    "cleanup_expired_tasks", 
    "health_check",
    "test_task",
    "CELERYBEAT_SCHEDULE"
]
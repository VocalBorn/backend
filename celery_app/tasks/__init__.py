"""
VocalBorn Celery 任務模組

包含所有的 Celery 任務定義和排程配置
"""

from .analyze_audio import analyze_audio_task, AudioAnalysisError
from .analyze_test_audio import analyze_test_audio_task
from .cleanup_expired import cleanup_expired_tasks
from .health_check import health_check
from .test_task import test_task

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

__all__ = [
    "analyze_audio_task",
    "AudioAnalysisError",
    "analyze_test_audio_task",
    "cleanup_expired_tasks", 
    "health_check",
    "test_task",
    "CELERYBEAT_SCHEDULE"
]
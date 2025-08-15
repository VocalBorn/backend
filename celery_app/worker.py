"""
VocalBorn Celery Worker 入口點

使用方式:
    uv run celery -A celery_app.worker worker --loglevel=info --logfile=logs/celery.log
    uv run celery -A celery_app.worker beat --loglevel=info
    uv run celery -A celery_app.worker flower --port=5555
"""

from .app import app

# 確保任務已載入
from . import tasks

# 匯出 celery 應用供命令列使用
celery = app
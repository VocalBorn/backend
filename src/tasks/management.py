"""
VocalBorn Celery 管理工具

提供命令列介面來管理 Celery 任務系統，包括：
- 啟動和停止 Worker
- 監控任務狀態
- 清理過期資料
- 系統健康檢查
"""

import click
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from .celery_app import app, monitor, CeleryConfig
from .celery_tasks import health_check, cleanup_expired_tasks, test_task

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """VocalBorn Celery 管理工具"""
    pass


@cli.command()
@click.option('--concurrency', '-c', default=4, help='Worker 併發數量')
@click.option('--loglevel', '-l', default='INFO', help='日誌等級')
@click.option('--queue', '-q', default='ai_analysis', help='監聽的佇列')
def worker(concurrency: int, loglevel: str, queue: str):
    """啟動 Celery Worker"""
    click.echo(f"啟動 Celery Worker...")
    click.echo(f"併發數: {concurrency}")
    click.echo(f"日誌等級: {loglevel}")
    click.echo(f"監聽佇列: {queue}")
    
    # 啟動 Worker
    app.worker_main([
        'worker',
        f'--concurrency={concurrency}',
        f'--loglevel={loglevel}',
        f'--queues={queue}',
        '--pool=prefork',  # 使用 prefork 池
    ])


@cli.command()
@click.option('--loglevel', '-l', default='INFO', help='日誌等級')
def beat(loglevel: str):
    """啟動 Celery Beat 定時任務調度器"""
    click.echo("啟動 Celery Beat...")
    click.echo(f"日誌等級: {loglevel}")
    
    app.control.add_consumer('maintenance')  # 確保監聽維護佇列
    app.start([
        'beat',
        f'--loglevel={loglevel}',
    ])


@cli.command()
@click.option('--basic-auth', default='admin:vocalborn2024', help='基本認證 (用戶名:密碼)')
@click.option('--port', default=5555, help='Flower 監控介面端口')
def flower(basic_auth: str, port: int):
    """啟動 Flower 監控介面"""
    click.echo(f"啟動 Flower 監控介面...")
    click.echo(f"端口: {port}")
    click.echo(f"基本認證: {basic_auth}")
    
    app.start([
        'flower',
        f'--port={port}',
        f'--basic_auth={basic_auth}',
    ])


@cli.command()
def status():
    """顯示系統狀態"""
    click.echo("=== VocalBorn Celery 系統狀態 ===")
    
    # 檢查配置
    config = CeleryConfig()
    click.echo(f"\n📋 配置資訊:")
    click.echo(f"  訊息代理: {config.broker_url}")
    click.echo(f"  結果儲存: {config.result_backend}")
    
    # 檢查 Worker 狀態
    click.echo(f"\n👷 Worker 狀態:")
    try:
        stats = monitor.get_worker_stats()
        if stats:
            for worker, info in stats.get('active', {}).items():
                click.echo(f"  {worker}: {len(info)} 個活躍任務")
        else:
            click.echo("  沒有檢測到活躍的 Worker")
    except Exception as exc:
        click.echo(f"  無法獲取 Worker 狀態: {exc}")
    
    # 檢查佇列狀態
    click.echo(f"\n📋 佇列狀態:")
    queues = ['ai_analysis', 'maintenance', 'health']
    for queue in queues:
        try:
            length = monitor.get_queue_length(queue)
            click.echo(f"  {queue}: {length} 個待處理任務")
        except Exception as exc:
            click.echo(f"  {queue}: 無法獲取佇列長度 ({exc})")


@cli.command()
def health():
    """執行系統健康檢查"""
    click.echo("🏥 執行系統健康檢查...")
    
    try:
        # 提交健康檢查任務
        task = health_check.apply_async(queue='health')
        click.echo(f"健康檢查任務 ID: {task.id}")
        
        # 等待結果
        result = task.get(timeout=30)
        
        # 顯示結果
        click.echo(f"\n✅ 健康檢查完成")
        click.echo(f"整體狀態: {result['status']}")
        click.echo(f"檢查時間: {result['timestamp']}")
        
        for check_name, check_result in result['checks'].items():
            status_emoji = "✅" if check_result['status'] == 'ok' else "❌" if check_result['status'] == 'error' else "⚠️"
            click.echo(f"{status_emoji} {check_name}: {check_result.get('message', check_result['status'])}")
            
    except Exception as exc:
        click.echo(f"❌ 健康檢查失敗: {exc}")


@cli.command()
@click.argument('task_id')
def task(task_id: str):
    """查詢特定任務狀態"""
    click.echo(f"📊 查詢任務狀態: {task_id}")
    
    try:
        result = app.AsyncResult(task_id)
        
        click.echo(f"狀態: {result.status}")
        click.echo(f"已完成: {result.ready()}")
        
        if result.status == 'PROGRESS':
            click.echo(f"進度資訊: {result.info}")
        elif result.ready():
            if result.successful():
                click.echo(f"結果: {result.result}")
            else:
                click.echo(f"錯誤: {result.info}")
                
    except Exception as exc:
        click.echo(f"❌ 查詢任務失敗: {exc}")


@cli.command()
@click.argument('task_id')
@click.option('--terminate', is_flag=True, help='強制終止任務')
def cancel(task_id: str, terminate: bool):
    """取消任務"""
    click.echo(f"⏹️  取消任務: {task_id}")
    
    try:
        app.control.revoke(task_id, terminate=terminate)
        if terminate:
            click.echo("✅ 任務已強制終止")
        else:
            click.echo("✅ 任務已標記為取消")
    except Exception as exc:
        click.echo(f"❌ 取消任務失敗: {exc}")


@cli.command()
@click.option('--message', default='Hello from CLI!', help='測試訊息')
def test(message: str):
    """執行測試任務"""
    click.echo(f"🧪 提交測試任務: {message}")
    
    try:
        task = test_task.apply_async(
            args=[message],
            queue='ai_analysis'
        )
        
        click.echo(f"任務 ID: {task.id}")
        click.echo("等待任務完成...")
        
        # 監控進度
        while not task.ready():
            if task.status == 'PROGRESS':
                info = task.info
                click.echo(f"進度: {info.get('progress', 0)}% - {info.get('current_step', 'Unknown')}")
            time.sleep(1)
        
        if task.successful():
            result = task.result
            click.echo(f"✅ 測試任務完成: {result}")
        else:
            click.echo(f"❌ 測試任務失敗: {task.info}")
            
    except Exception as exc:
        click.echo(f"❌ 測試任務執行失敗: {exc}")


@cli.command()
def cleanup():
    """清理過期任務"""
    click.echo("🧹 執行過期任務清理...")
    
    try:
        task = cleanup_expired_tasks.apply_async(queue='maintenance')
        click.echo(f"清理任務 ID: {task.id}")
        
        result = task.get(timeout=60)
        click.echo("✅ 清理完成:")
        click.echo(f"  清理任務數: {result['cleaned_tasks']}")
        click.echo(f"  清理結果數: {result['cleaned_results']}")
        click.echo(f"  釋放空間: {result['freed_space_mb']} MB")
        
    except Exception as exc:
        click.echo(f"❌ 清理失敗: {exc}")


@cli.command()
@click.option('--queue', default='ai_analysis', help='要清空的佇列')
def purge(queue: str):
    """清空指定佇列"""
    click.echo(f"🗑️  清空佇列: {queue}")
    
    if not click.confirm(f"確定要清空佇列 '{queue}' 嗎？這將刪除所有待處理的任務。"):
        click.echo("操作已取消")
        return
    
    try:
        count = monitor.purge_queue(queue)
        click.echo(f"✅ 已清空 {count} 個任務")
    except Exception as exc:
        click.echo(f"❌ 清空佇列失敗: {exc}")


@cli.command()
@click.option('--interval', default=5, help='更新間隔（秒）')
@click.option('--count', default=10, help='顯示次數')
def monitor_cmd(interval: int, count: int):
    """即時監控系統狀態"""
    click.echo("📈 開始即時監控...")
    click.echo("按 Ctrl+C 停止監控")
    
    try:
        for i in range(count):
            click.clear()
            click.echo(f"=== 監控資料 (第 {i+1}/{count} 次) ===")
            click.echo(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 顯示佇列狀態
            click.echo("\n📋 佇列狀態:")
            queues = ['ai_analysis', 'maintenance', 'health']
            for queue in queues:
                try:
                    length = monitor.get_queue_length(queue)
                    click.echo(f"  {queue}: {length}")
                except Exception:
                    click.echo(f"  {queue}: N/A")
            
            # 顯示 Worker 狀態
            click.echo("\n👷 Worker 狀態:")
            try:
                stats = monitor.get_worker_stats()
                active_workers = len(stats.get('active', {}))
                click.echo(f"  活躍 Worker 數: {active_workers}")
            except Exception:
                click.echo("  無法獲取 Worker 狀態")
            
            if i < count - 1:  # 不是最後一次
                time.sleep(interval)
                
    except KeyboardInterrupt:
        click.echo("\n⏹️  監控已停止")


if __name__ == '__main__':
    cli()
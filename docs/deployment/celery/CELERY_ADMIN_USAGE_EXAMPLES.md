# Celery 管理系統使用範例

## 基本 API 使用

### 1. 系統狀態檢查

```bash
# 健康檢查（無需認證）
curl -X GET "http://localhost:8000/celery-admin/system/health"

# 系統資訊（無需認證）
curl -X GET "http://localhost:8000/celery-admin/system/info"

# 完整系統狀態（需要管理員權限）
curl -X GET "http://localhost:8000/celery-admin/system/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. 即時監控

```bash
# 獲取即時指標
curl -X GET "http://localhost:8000/celery-admin/monitoring/metrics/realtime" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 獲取完整監控儀表板
curl -X GET "http://localhost:8000/celery-admin/monitoring/dashboard" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. 啟動監控服務

```bash
# 啟動背景監控
curl -X POST "http://localhost:8000/celery-admin/monitoring/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 檢查監控狀態
curl -X GET "http://localhost:8000/celery-admin/monitoring/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## WebSocket 即時監控

### JavaScript 客戶端範例

```html
<!DOCTYPE html>
<html>
<head>
    <title>Celery 監控儀表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div id="metrics">
        <h2>即時系統指標</h2>
        <div id="workers-count">活躍 Workers: <span id="active-workers">0</span></div>
        <div id="tasks-count">待處理任務: <span id="pending-tasks">0</span></div>
        <div id="system-health">系統健康: <span id="health-status">unknown</span></div>
    </div>

    <canvas id="metricsChart" width="400" height="200"></canvas>

    <script>
        // WebSocket 連接
        const ws = new WebSocket('ws://localhost:8000/celery-admin/monitoring/ws');
        
        // 圖表設定
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '任務吞吐量',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // WebSocket 事件處理
        ws.onopen = function(event) {
            console.log('WebSocket 連接已建立');
            document.getElementById('health-status').textContent = '連接中...';
        };

        ws.onmessage = function(event) {
            const message = JSON.parse(event.data);
            console.log('收到訊息:', message);

            if (message.message_type === 'metrics_update') {
                const metrics = message.data.metrics;
                updateMetrics(metrics);
            } else if (message.message_type === 'dashboard_data') {
                const dashboard = message.data;
                updateDashboard(dashboard);
            }
        };

        ws.onclose = function(event) {
            console.log('WebSocket 連接已關閉');
            document.getElementById('health-status').textContent = '已斷開';
        };

        ws.onerror = function(error) {
            console.error('WebSocket 錯誤:', error);
            document.getElementById('health-status').textContent = '錯誤';
        };

        // 更新指標顯示
        function updateMetrics(metrics) {
            document.getElementById('active-workers').textContent = metrics.active_workers;
            document.getElementById('pending-tasks').textContent = metrics.pending_tasks;
            document.getElementById('health-status').textContent = metrics.system_health;

            // 更新圖表
            const now = new Date().toLocaleTimeString();
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(metrics.current_throughput);

            // 保持最近 20 個資料點
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }

            chart.update();
        }

        // 更新儀表板資料
        function updateDashboard(dashboard) {
            console.log('儀表板資料:', dashboard);
            updateMetrics(dashboard.real_time_metrics);
        }
    </script>
</body>
</html>
```

### Python 客戶端範例

```python
import asyncio
import websockets
import json
from datetime import datetime

class CeleryMonitorClient:
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.metrics_history = []
    
    async def connect_and_monitor(self):
        """連接到 WebSocket 並開始監控"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                print("已連接到 Celery 監控系統")
                
                async for message in websocket:
                    await self.handle_message(json.loads(message))
                    
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket 連接已關閉")
        except Exception as e:
            print(f"監控錯誤: {e}")
    
    async def handle_message(self, message):
        """處理收到的訊息"""
        message_type = message.get('message_type')
        timestamp = message.get('timestamp')
        data = message.get('data', {})
        
        if message_type == 'connection_established':
            print(f"連接建立: {data.get('message')}")
            print(f"客戶端數量: {data.get('client_count')}")
            
        elif message_type == 'metrics_update':
            metrics = data.get('metrics', {})
            await self.process_metrics(metrics, timestamp)
            
        elif message_type == 'dashboard_data':
            print("收到儀表板資料")
            await self.process_dashboard(data)
    
    async def process_metrics(self, metrics, timestamp):
        """處理即時指標"""
        self.metrics_history.append({
            'timestamp': timestamp,
            'metrics': metrics
        })
        
        # 顯示關鍵指標
        print(f"[{timestamp}] 系統指標:")
        print(f"  活躍 Workers: {metrics.get('active_workers', 0)}")
        print(f"  待處理任務: {metrics.get('pending_tasks', 0)}")
        print(f"  處理中任務: {metrics.get('processing_tasks', 0)}")
        print(f"  系統健康: {metrics.get('system_health', 'unknown')}")
        print(f"  當前吞吐量: {metrics.get('current_throughput', 0):.2f} 任務/秒")
        print("-" * 50)
        
        # 檢查警報條件
        await self.check_alerts(metrics)
    
    async def process_dashboard(self, dashboard):
        """處理儀表板資料"""
        real_time = dashboard.get('real_time_metrics', {})
        await self.process_metrics(real_time, datetime.now().isoformat())
        
        # 顯示系統摘要
        summary = dashboard.get('system_summary', {})
        print("系統摘要:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    
    async def check_alerts(self, metrics):
        """檢查警報條件"""
        active_workers = metrics.get('active_workers', 0)
        pending_tasks = metrics.get('pending_tasks', 0)
        error_rate = metrics.get('error_rate_percent', 0)
        
        # 檢查 Worker 數量
        if active_workers == 0:
            print("⚠️  警報: 沒有活躍的 Worker！")
        
        # 檢查任務堆積
        if pending_tasks > 100:
            print(f"⚠️  警報: 任務堆積過多 ({pending_tasks} 個待處理任務)")
        
        # 檢查錯誤率
        if error_rate > 10:
            print(f"⚠️  警報: 錯誤率過高 ({error_rate:.1f}%)")
    
    def get_metrics_summary(self):
        """獲取指標摘要"""
        if not self.metrics_history:
            return "沒有可用的指標資料"
        
        latest = self.metrics_history[-1]['metrics']
        return {
            "資料點數量": len(self.metrics_history),
            "最新指標": latest,
            "監控時間範圍": {
                "開始": self.metrics_history[0]['timestamp'],
                "結束": self.metrics_history[-1]['timestamp']
            }
        }

# 使用範例
async def main():
    monitor = CeleryMonitorClient('ws://localhost:8000/celery-admin/monitoring/ws')
    
    # 啟動監控（會持續運行）
    try:
        await monitor.connect_and_monitor()
    except KeyboardInterrupt:
        print("\n監控已停止")
        print(json.dumps(monitor.get_metrics_summary(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
```

## 系統管理操作

### 1. 生成效能報告

```python
import httpx
import json
from datetime import datetime, timedelta

async def generate_performance_report():
    """生成系統效能報告"""
    
    # 設定時間範圍（最近 24 小時）
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    time_range = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/celery-admin/monitoring/reports/performance",
            json=time_range,
            headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
        )
        
        if response.status_code == 200:
            report = response.json()
            
            print("效能報告:")
            print(f"報告 ID: {report['report_id']}")
            print(f"時間範圍: {report['time_range']}")
            print(f"總任務數: {report['total_tasks']}")
            print(f"成功任務數: {report['successful_tasks']}")
            print(f"失敗任務數: {report['failed_tasks']}")
            print(f"平均執行時間: {report['avg_execution_time_ms']} ms")
            print(f"峰值吞吐量: {report['peak_throughput']} 任務/秒")
            
            # 顯示優化建議
            print("\n優化建議:")
            for rec in report['optimization_recommendations']:
                print(f"  • {rec}")
                
            return report
        else:
            print(f"生成報告失敗: {response.status_code}")
            return None

# 執行報告生成
# asyncio.run(generate_performance_report())
```

### 2. 批量操作範例

```python
async def batch_task_operations():
    """批量任務操作範例"""
    
    # 假設有一些需要撤銷的任務 ID
    task_ids = [
        "task-123-456-789",
        "task-987-654-321",
        "task-456-789-123"
    ]
    
    # 批量撤銷任務
    batch_request = {
        "task_ids": task_ids,
        "operation": "revoke",
        "parameters": {
            "terminate": True,
            "reason": "系統維護"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/celery-admin/tasks/batch",
            json=batch_request,
            headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"批量操作完成:")
            print(f"  總數: {result['total']}")
            print(f"  成功: {result['successful']}")
            print(f"  失敗: {result['failed']}")
            print(f"  摘要: {result['summary']}")
        else:
            print(f"批量操作失敗: {response.status_code}")
```

## 監控警報設定

### 自訂警報處理器

```python
class CeleryAlertHandler:
    def __init__(self):
        self.alert_rules = [
            {
                "name": "worker_down",
                "condition": lambda m: m.get("active_workers", 0) == 0,
                "message": "沒有活躍的 Worker"
            },
            {
                "name": "high_queue_backlog",
                "condition": lambda m: sum(m.get("queue_lengths", {}).values()) > 50,
                "message": "佇列積壓嚴重"
            },
            {
                "name": "high_error_rate",
                "condition": lambda m: m.get("error_rate_percent", 0) > 5,
                "message": "錯誤率過高"
            }
        ]
        
    def check_alerts(self, metrics):
        """檢查警報條件"""
        alerts = []
        
        for rule in self.alert_rules:
            if rule["condition"](metrics):
                alerts.append({
                    "name": rule["name"],
                    "message": rule["message"],
                    "severity": "warning",
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                })
        
        return alerts
    
    def send_alert(self, alert):
        """發送警報（可整合到各種通知系統）"""
        print(f"🚨 警報: {alert['message']}")
        
        # 這裡可以整合各種通知方式：
        # - 發送電子郵件
        # - 發送 Slack 訊息
        # - 調用 webhook
        # - 寫入日誌系統
        
        # 範例：寫入日誌
        import logging
        logger = logging.getLogger("celery_alerts")
        logger.warning(f"Celery Alert: {alert['name']} - {alert['message']}")
```

這個完整的 Celery 管理系統為 VocalBorn 平台提供了企業級的任務管理和監控能力，支持即時監控、歷史分析、警報通知和操作審計等功能。
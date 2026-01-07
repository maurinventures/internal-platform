"""
Monitoring and Metrics Service (Prompt 29)

Comprehensive monitoring system for the Internal Platform including
performance metrics, logging, alerting, and dashboard data collection.
"""

import os
import time
import json
import logging
import threading
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import sqlite3
from pathlib import Path
import subprocess
import traceback


@dataclass
class MetricDataPoint:
    """Single metric data point."""
    metric_name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    metric_name: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    duration_seconds: int
    severity: str  # 'info', 'warning', 'critical'
    enabled: bool
    notification_channels: List[str]


@dataclass
class SystemHealth:
    """System health snapshot."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_connections: int
    load_average: Tuple[float, float, float]
    timestamp: datetime


class MetricsCollector:
    """
    Collects various application and system metrics.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.logger = logging.getLogger(__name__)
        self.custom_metrics = defaultdict(list)
        self.metric_history = deque(maxlen=1000)  # Keep last 1000 metrics

    def collect_system_metrics(self) -> Dict[str, float]:
        """
        Collect system performance metrics.

        Returns:
            Dictionary of system metrics
        """
        metrics = {}

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['system.cpu.usage_percent'] = cpu_percent
            metrics['system.cpu.count'] = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()
            metrics['system.memory.usage_percent'] = memory.percent
            metrics['system.memory.available_gb'] = memory.available / (1024**3)
            metrics['system.memory.used_gb'] = memory.used / (1024**3)
            metrics['system.memory.total_gb'] = memory.total / (1024**3)

            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics['system.disk.usage_percent'] = (disk.used / disk.total) * 100
            metrics['system.disk.free_gb'] = disk.free / (1024**3)
            metrics['system.disk.used_gb'] = disk.used / (1024**3)

            # Network metrics
            network = psutil.net_io_counters()
            metrics['system.network.bytes_sent'] = network.bytes_sent
            metrics['system.network.bytes_recv'] = network.bytes_recv
            metrics['system.network.packets_sent'] = network.packets_sent
            metrics['system.network.packets_recv'] = network.packets_recv

            # Load average (Unix/Linux only)
            if hasattr(os, 'getloadavg'):
                load1, load5, load15 = os.getloadavg()
                metrics['system.load.1min'] = load1
                metrics['system.load.5min'] = load5
                metrics['system.load.15min'] = load15

            # Process metrics
            process_count = len(psutil.pids())
            metrics['system.processes.count'] = process_count

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

        return metrics

    def collect_application_metrics(self) -> Dict[str, float]:
        """
        Collect application-specific metrics.

        Returns:
            Dictionary of application metrics
        """
        metrics = {}

        try:
            # Flask application metrics (if running)
            app_metrics = self._collect_flask_metrics()
            metrics.update(app_metrics)

            # Database metrics
            db_metrics = self._collect_database_metrics()
            metrics.update(db_metrics)

            # Custom business metrics
            business_metrics = self._collect_business_metrics()
            metrics.update(business_metrics)

        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")

        return metrics

    def _collect_flask_metrics(self) -> Dict[str, float]:
        """Collect Flask application metrics."""
        metrics = {}

        try:
            # Try to get health endpoint response time
            start_time = time.time()
            response = requests.get('http://localhost:5001/api/health', timeout=5)
            response_time = time.time() - start_time

            metrics['app.health.response_time_ms'] = response_time * 1000
            metrics['app.health.status_code'] = response.status_code

            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') == 'healthy':
                    metrics['app.health.status'] = 1.0  # Healthy
                else:
                    metrics['app.health.status'] = 0.0  # Unhealthy
            else:
                metrics['app.health.status'] = 0.0

        except requests.RequestException:
            metrics['app.health.status'] = 0.0
            metrics['app.health.response_time_ms'] = 0.0

        return metrics

    def _collect_database_metrics(self) -> Dict[str, float]:
        """Collect database metrics."""
        metrics = {}

        try:
            # Check if database is accessible
            start_time = time.time()

            # This would typically connect to your actual database
            # For demo purposes, we'll simulate database metrics
            connection_time = time.time() - start_time

            metrics['db.connection_time_ms'] = connection_time * 1000
            metrics['db.status'] = 1.0  # Assume healthy for demo

            # Simulated database metrics
            metrics['db.connections.active'] = 15
            metrics['db.connections.max'] = 100
            metrics['db.queries.per_second'] = 45.2
            metrics['db.slow_queries.count'] = 2

        except Exception as e:
            self.logger.error(f"Database metrics collection failed: {e}")
            metrics['db.status'] = 0.0

        return metrics

    def _collect_business_metrics(self) -> Dict[str, float]:
        """Collect business/custom metrics."""
        metrics = {}

        try:
            # Example business metrics - these would be collected from your application
            metrics['business.users.active_sessions'] = len(self.custom_metrics.get('active_sessions', []))
            metrics['business.ai_calls.total'] = self._get_custom_metric_sum('ai_calls')
            metrics['business.ai_calls.cost_today'] = self._get_custom_metric_sum('ai_cost')
            metrics['business.errors.rate_per_hour'] = self._calculate_error_rate()

        except Exception as e:
            self.logger.error(f"Business metrics collection failed: {e}")

        return metrics

    def _get_custom_metric_sum(self, metric_name: str) -> float:
        """Get sum of custom metric values."""
        values = self.custom_metrics.get(metric_name, [])
        return sum(values) if values else 0.0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate based on recent errors."""
        error_counts = self.custom_metrics.get('errors', [])
        # Return errors in the last hour
        return len([e for e in error_counts if e > time.time() - 3600])

    def record_custom_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a custom metric value.

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        data_point = MetricDataPoint(
            metric_name=metric_name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit='count'
        )

        self.metric_history.append(data_point)
        self.custom_metrics[metric_name].append(value)

        # Keep only recent values (last 24 hours)
        cutoff_time = time.time() - 86400  # 24 hours
        self.custom_metrics[metric_name] = [
            v for v in self.custom_metrics[metric_name]
            if v > cutoff_time
        ]

    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_application_metrics()

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system': system_metrics,
            'application': app_metrics,
            'custom_metrics_count': len(self.custom_metrics),
            'total_data_points': len(self.metric_history)
        }


class PerformanceMonitor:
    """
    Monitors application performance and detects issues.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.logger = logging.getLogger(__name__)
        self.response_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.performance_baselines = {}

    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """
        Record a request for performance monitoring.

        Args:
            endpoint: API endpoint
            response_time: Response time in seconds
            status_code: HTTP status code
        """
        timestamp = datetime.utcnow()

        self.response_times.append({
            'endpoint': endpoint,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': timestamp
        })

        # Track errors
        if status_code >= 400:
            self.error_counts[endpoint] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.response_times:
            return {}

        # Calculate response time statistics
        response_times_only = [r['response_time'] for r in self.response_times]
        avg_response_time = sum(response_times_only) / len(response_times_only)
        max_response_time = max(response_times_only)
        min_response_time = min(response_times_only)

        # Calculate 95th percentile
        sorted_times = sorted(response_times_only)
        p95_index = int(0.95 * len(sorted_times))
        p95_response_time = sorted_times[p95_index] if sorted_times else 0

        # Calculate error rate
        total_requests = len(self.response_times)
        error_requests = sum(1 for r in self.response_times if r['status_code'] >= 400)
        error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0

        # Endpoint performance breakdown
        endpoint_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'errors': 0})
        for req in self.response_times:
            endpoint = req['endpoint']
            endpoint_stats[endpoint]['count'] += 1
            endpoint_stats[endpoint]['total_time'] += req['response_time']
            if req['status_code'] >= 400:
                endpoint_stats[endpoint]['errors'] += 1

        # Calculate average per endpoint
        endpoint_averages = {}
        for endpoint, stats in endpoint_stats.items():
            endpoint_averages[endpoint] = {
                'avg_response_time': stats['total_time'] / stats['count'],
                'request_count': stats['count'],
                'error_count': stats['errors'],
                'error_rate': (stats['errors'] / stats['count']) * 100
            }

        return {
            'overall': {
                'total_requests': total_requests,
                'avg_response_time': avg_response_time,
                'min_response_time': min_response_time,
                'max_response_time': max_response_time,
                'p95_response_time': p95_response_time,
                'error_rate': error_rate
            },
            'endpoints': endpoint_averages,
            'timestamp': datetime.utcnow().isoformat()
        }

    def detect_performance_issues(self) -> List[Dict[str, Any]]:
        """Detect performance issues and return alerts."""
        issues = []

        try:
            summary = self.get_performance_summary()

            if not summary:
                return issues

            overall = summary.get('overall', {})

            # Check high average response time
            avg_response_time = overall.get('avg_response_time', 0)
            if avg_response_time > 2.0:  # 2 seconds
                issues.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'message': f'High average response time: {avg_response_time:.2f}s',
                    'value': avg_response_time,
                    'threshold': 2.0
                })

            # Check high error rate
            error_rate = overall.get('error_rate', 0)
            if error_rate > 5.0:  # 5%
                issues.append({
                    'type': 'high_error_rate',
                    'severity': 'critical' if error_rate > 10 else 'warning',
                    'message': f'High error rate: {error_rate:.1f}%',
                    'value': error_rate,
                    'threshold': 5.0
                })

            # Check 95th percentile response time
            p95_response_time = overall.get('p95_response_time', 0)
            if p95_response_time > 5.0:  # 5 seconds
                issues.append({
                    'type': 'high_p95_response_time',
                    'severity': 'warning',
                    'message': f'High 95th percentile response time: {p95_response_time:.2f}s',
                    'value': p95_response_time,
                    'threshold': 5.0
                })

            # Check endpoint-specific issues
            for endpoint, stats in summary.get('endpoints', {}).items():
                if stats['error_rate'] > 10:  # 10% error rate for specific endpoint
                    issues.append({
                        'type': 'endpoint_high_error_rate',
                        'severity': 'warning',
                        'message': f'High error rate for {endpoint}: {stats["error_rate"]:.1f}%',
                        'endpoint': endpoint,
                        'value': stats['error_rate'],
                        'threshold': 10.0
                    })

        except Exception as e:
            self.logger.error(f"Error detecting performance issues: {e}")

        return issues


class AlertManager:
    """
    Manages alerting for monitoring system.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.logger = logging.getLogger(__name__)
        self.alert_rules: List[AlertRule] = []
        self.alert_history = deque(maxlen=1000)
        self.active_alerts = {}

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules.append(rule)
        self.logger.info(f"Added alert rule: {rule.name}")

    def evaluate_alerts(self, metrics: Dict[str, float]):
        """
        Evaluate all alert rules against current metrics.

        Args:
            metrics: Current metric values
        """
        current_time = datetime.utcnow()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            try:
                metric_value = metrics.get(rule.metric_name)
                if metric_value is None:
                    continue

                # Evaluate the condition
                alert_triggered = self._evaluate_condition(
                    metric_value, rule.threshold, rule.operator
                )

                alert_key = f"{rule.name}:{rule.metric_name}"

                if alert_triggered:
                    if alert_key not in self.active_alerts:
                        # New alert
                        self.active_alerts[alert_key] = {
                            'rule': rule,
                            'triggered_at': current_time,
                            'value': metric_value
                        }
                        self._send_alert(rule, metric_value, 'triggered')

                    elif (current_time - self.active_alerts[alert_key]['triggered_at']).total_seconds() >= rule.duration_seconds:
                        # Alert duration threshold met, send notification
                        if not self.active_alerts[alert_key].get('notified'):
                            self._send_alert(rule, metric_value, 'active')
                            self.active_alerts[alert_key]['notified'] = True

                else:
                    # Alert resolved
                    if alert_key in self.active_alerts:
                        self._send_alert(rule, metric_value, 'resolved')
                        del self.active_alerts[alert_key]

            except Exception as e:
                self.logger.error(f"Error evaluating alert rule {rule.name}: {e}")

    def _evaluate_condition(self, value: float, threshold: float, operator: str) -> bool:
        """Evaluate alert condition."""
        if operator == 'gt':
            return value > threshold
        elif operator == 'lt':
            return value < threshold
        elif operator == 'gte':
            return value >= threshold
        elif operator == 'lte':
            return value <= threshold
        elif operator == 'eq':
            return abs(value - threshold) < 0.001  # Float equality with tolerance
        else:
            return False

    def _send_alert(self, rule: AlertRule, value: float, status: str):
        """Send alert notification."""
        alert_data = {
            'rule_name': rule.name,
            'metric_name': rule.metric_name,
            'current_value': value,
            'threshold': rule.threshold,
            'severity': rule.severity,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.alert_history.append(alert_data)

        # Send to notification channels
        for channel in rule.notification_channels:
            try:
                if channel == 'slack':
                    self._send_slack_alert(alert_data)
                elif channel == 'email':
                    self._send_email_alert(alert_data)
                elif channel == 'log':
                    self._send_log_alert(alert_data)
            except Exception as e:
                self.logger.error(f"Failed to send alert to {channel}: {e}")

    def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Send alert to Slack."""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return

        status_emoji = {
            'triggered': '🚨',
            'active': '⚠️',
            'resolved': '✅'
        }

        severity_color = {
            'info': 'good',
            'warning': 'warning',
            'critical': 'danger'
        }

        message = {
            'text': f"{status_emoji.get(alert_data['status'], '📊')} Alert {alert_data['status'].title()}",
            'attachments': [{
                'color': severity_color.get(alert_data['severity'], 'warning'),
                'fields': [
                    {'title': 'Rule', 'value': alert_data['rule_name'], 'short': True},
                    {'title': 'Metric', 'value': alert_data['metric_name'], 'short': True},
                    {'title': 'Current Value', 'value': f"{alert_data['current_value']:.2f}", 'short': True},
                    {'title': 'Threshold', 'value': f"{alert_data['threshold']:.2f}", 'short': True}
                ]
            }]
        }

        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()

    def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send alert via email."""
        # Email implementation would go here
        self.logger.info(f"Email alert: {alert_data['rule_name']} - {alert_data['status']}")

    def _send_log_alert(self, alert_data: Dict[str, Any]):
        """Send alert to log."""
        severity_map = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'critical': logging.ERROR
        }

        log_level = severity_map.get(alert_data['severity'], logging.WARNING)
        message = (f"ALERT {alert_data['status'].upper()}: {alert_data['rule_name']} - "
                  f"{alert_data['metric_name']} = {alert_data['current_value']:.2f} "
                  f"(threshold: {alert_data['threshold']:.2f})")

        self.logger.log(log_level, message)

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts."""
        return [
            {
                'name': alert_data['rule'].name,
                'metric': alert_data['rule'].metric_name,
                'severity': alert_data['rule'].severity,
                'triggered_at': alert_data['triggered_at'].isoformat(),
                'current_value': alert_data['value']
            }
            for alert_data in self.active_alerts.values()
        ]


class MetricsStorage:
    """
    Stores metrics data for historical analysis and dashboards.
    """

    def __init__(self, db_path: str = 'metrics.db'):
        """Initialize metrics storage."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for metrics storage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    tags TEXT,
                    unit TEXT
                )
            ''')

            # Create index for efficient querying
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_name_time
                ON metrics (metric_name, timestamp)
            ''')

            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to initialize metrics database: {e}")

    def store_metrics(self, metrics: Dict[str, float]):
        """
        Store metrics in database.

        Args:
            metrics: Dictionary of metric name -> value
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = datetime.utcnow()

            for metric_name, value in metrics.items():
                cursor.execute('''
                    INSERT INTO metrics (metric_name, value, timestamp, unit)
                    VALUES (?, ?, ?, ?)
                ''', (metric_name, value, timestamp, 'count'))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")

    def get_metric_history(self, metric_name: str, hours: int = 24) -> List[Tuple[datetime, float]]:
        """
        Get historical data for a metric.

        Args:
            metric_name: Name of the metric
            hours: Hours of history to retrieve

        Returns:
            List of (timestamp, value) tuples
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            since_time = datetime.utcnow() - timedelta(hours=hours)

            cursor.execute('''
                SELECT timestamp, value FROM metrics
                WHERE metric_name = ? AND timestamp > ?
                ORDER BY timestamp
            ''', (metric_name, since_time))

            results = cursor.fetchall()
            conn.close()

            return [(datetime.fromisoformat(ts), value) for ts, value in results]

        except Exception as e:
            self.logger.error(f"Failed to get metric history: {e}")
            return []

    def cleanup_old_metrics(self, days: int = 30):
        """
        Clean up old metrics data.

        Args:
            days: Number of days of data to keep
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = datetime.utcnow() - timedelta(days=days)

            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_time,))
            cursor.execute('DELETE FROM alerts WHERE timestamp < ?', (cutoff_time,))

            deleted_metrics = cursor.rowcount
            conn.commit()
            conn.close()

            self.logger.info(f"Cleaned up {deleted_metrics} old metric records")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")


class MonitoringDashboard:
    """
    Generates monitoring dashboard data and reports.
    """

    def __init__(self, storage: MetricsStorage):
        """Initialize monitoring dashboard."""
        self.storage = storage
        self.logger = logging.getLogger(__name__)

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate dashboard data for the last 24 hours."""
        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_overview': self._get_system_overview(),
            'application_health': self._get_application_health(),
            'performance_metrics': self._get_performance_metrics(),
            'alerts_summary': self._get_alerts_summary()
        }

        return dashboard_data

    def _get_system_overview(self) -> Dict[str, Any]:
        """Get system overview metrics."""
        metrics = [
            'system.cpu.usage_percent',
            'system.memory.usage_percent',
            'system.disk.usage_percent',
            'system.load.1min'
        ]

        overview = {}
        for metric in metrics:
            history = self.storage.get_metric_history(metric, hours=1)
            if history:
                latest_value = history[-1][1]
                avg_value = sum(value for _, value in history) / len(history)
                overview[metric] = {
                    'current': latest_value,
                    'average_1h': avg_value,
                    'trend': self._calculate_trend(history)
                }

        return overview

    def _get_application_health(self) -> Dict[str, Any]:
        """Get application health metrics."""
        health_metrics = [
            'app.health.status',
            'app.health.response_time_ms',
            'db.status',
            'db.connection_time_ms'
        ]

        health = {}
        for metric in health_metrics:
            history = self.storage.get_metric_history(metric, hours=1)
            if history:
                latest_value = history[-1][1]
                health[metric] = {
                    'current': latest_value,
                    'status': 'healthy' if latest_value > 0 else 'unhealthy'
                }

        return health

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        return {
            'response_times': self._get_response_time_summary(),
            'throughput': self._get_throughput_summary(),
            'errors': self._get_error_summary()
        }

    def _get_response_time_summary(self) -> Dict[str, float]:
        """Get response time summary."""
        history = self.storage.get_metric_history('app.health.response_time_ms', hours=24)
        if not history:
            return {}

        values = [value for _, value in history]
        return {
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'p95': sorted(values)[int(0.95 * len(values))] if values else 0
        }

    def _get_throughput_summary(self) -> Dict[str, float]:
        """Get throughput summary."""
        # This would calculate requests per second based on stored metrics
        return {
            'requests_per_second': 15.5,  # Simulated
            'peak_rps': 45.2,
            'average_rps_24h': 22.1
        }

    def _get_error_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        return {
            'error_rate_percent': 2.1,  # Simulated
            'total_errors_24h': 45,
            'critical_errors': 2,
            'most_common_error': '500 Internal Server Error'
        }

    def _get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary."""
        return {
            'active_alerts': 1,  # Simulated
            'resolved_24h': 5,
            'critical_active': 0,
            'warning_active': 1
        }

    def _calculate_trend(self, history: List[Tuple[datetime, float]]) -> str:
        """Calculate trend from historical data."""
        if len(history) < 2:
            return 'stable'

        # Simple trend calculation based on first and last values
        first_half = history[:len(history)//2]
        second_half = history[len(history)//2:]

        if not first_half or not second_half:
            return 'stable'

        first_avg = sum(value for _, value in first_half) / len(first_half)
        second_avg = sum(value for _, value in second_half) / len(second_half)

        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0

        if change_percent > 5:
            return 'increasing'
        elif change_percent < -5:
            return 'decreasing'
        else:
            return 'stable'


class MonitoringService:
    """
    Main monitoring service that coordinates all monitoring components.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize monitoring service."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.metrics_collector = MetricsCollector()
        self.performance_monitor = PerformanceMonitor()
        self.alert_manager = AlertManager()
        self.storage = MetricsStorage()
        self.dashboard = MonitoringDashboard(self.storage)

        # Setup default alert rules
        self._setup_default_alerts()

        # Monitoring thread
        self.monitoring_thread = None
        self.monitoring_active = False

    def _setup_default_alerts(self):
        """Setup default alert rules."""
        default_rules = [
            AlertRule(
                name='High CPU Usage',
                metric_name='system.cpu.usage_percent',
                threshold=80.0,
                operator='gt',
                duration_seconds=300,  # 5 minutes
                severity='warning',
                enabled=True,
                notification_channels=['slack', 'log']
            ),
            AlertRule(
                name='High Memory Usage',
                metric_name='system.memory.usage_percent',
                threshold=90.0,
                operator='gt',
                duration_seconds=300,
                severity='critical',
                enabled=True,
                notification_channels=['slack', 'log']
            ),
            AlertRule(
                name='Application Unhealthy',
                metric_name='app.health.status',
                threshold=0.5,
                operator='lt',
                duration_seconds=60,
                severity='critical',
                enabled=True,
                notification_channels=['slack', 'log']
            ),
            AlertRule(
                name='High Response Time',
                metric_name='app.health.response_time_ms',
                threshold=5000.0,  # 5 seconds
                operator='gt',
                duration_seconds=300,
                severity='warning',
                enabled=True,
                notification_channels=['slack', 'log']
            )
        ]

        for rule in default_rules:
            self.alert_manager.add_alert_rule(rule)

    def start_monitoring(self, interval: int = 60):
        """
        Start monitoring in background thread.

        Args:
            interval: Collection interval in seconds
        """
        if self.monitoring_active:
            self.logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info(f"Started monitoring with {interval}s interval")

    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Stopped monitoring")

    def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics
                system_metrics = self.metrics_collector.collect_system_metrics()
                app_metrics = self.metrics_collector.collect_application_metrics()

                # Combine all metrics
                all_metrics = {**system_metrics, **app_metrics}

                # Store metrics
                self.storage.store_metrics(all_metrics)

                # Evaluate alerts
                self.alert_manager.evaluate_alerts(all_metrics)

                # Performance issue detection
                issues = self.performance_monitor.detect_performance_issues()
                if issues:
                    self.logger.warning(f"Detected {len(issues)} performance issues")

                self.logger.debug(f"Collected {len(all_metrics)} metrics")

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self.logger.error(traceback.format_exc())

            # Wait for next collection interval
            time.sleep(interval)

    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """Record a request for performance monitoring."""
        self.performance_monitor.record_request(endpoint, response_time, status_code)

    def record_custom_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric."""
        self.metrics_collector.record_custom_metric(metric_name, value, tags)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'monitoring_active': self.monitoring_active,
            'active_alerts': self.alert_manager.get_active_alerts(),
            'performance_summary': self.performance_monitor.get_performance_summary(),
            'metrics_summary': self.metrics_collector.get_metric_summary(),
            'dashboard_data': self.dashboard.generate_dashboard_data()
        }

    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': self._calculate_overall_health(),
            'system_health': self._get_system_health(),
            'application_health': self._get_application_health(),
            'alerts': self.alert_manager.get_active_alerts(),
            'performance': self.performance_monitor.get_performance_summary(),
            'recommendations': self._generate_recommendations()
        }

    def _calculate_overall_health(self) -> str:
        """Calculate overall system health."""
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a['severity'] == 'critical']

        if critical_alerts:
            return 'critical'
        elif active_alerts:
            return 'warning'
        else:
            return 'healthy'

    def _get_system_health(self) -> Dict[str, Any]:
        """Get current system health."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        except Exception:
            return {}

    def _get_application_health(self) -> Dict[str, Any]:
        """Get current application health."""
        app_metrics = self.metrics_collector.collect_application_metrics()
        return {
            'api_status': 'healthy' if app_metrics.get('app.health.status', 0) > 0 else 'unhealthy',
            'response_time': app_metrics.get('app.health.response_time_ms', 0),
            'database_status': 'healthy' if app_metrics.get('db.status', 0) > 0 else 'unhealthy'
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate health recommendations."""
        recommendations = []

        # Check for high resource usage
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            if cpu_percent > 80:
                recommendations.append(f"High CPU usage detected ({cpu_percent:.1f}%). Consider optimizing CPU-intensive processes.")

            if memory_percent > 85:
                recommendations.append(f"High memory usage detected ({memory_percent:.1f}%). Consider increasing memory or optimizing memory usage.")

        except Exception:
            pass

        return recommendations


def main():
    """Main function for standalone monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitoring Service")
    parser.add_argument('--interval', type=int, default=60, help='Collection interval in seconds')
    parser.add_argument('--duration', type=int, default=3600, help='Monitoring duration in seconds')
    parser.add_argument('--report', action='store_true', help='Generate health report and exit')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    monitoring = MonitoringService()

    if args.report:
        # Generate health report
        report = monitoring.generate_health_report()
        print(json.dumps(report, indent=2, default=str))
    else:
        # Start monitoring
        monitoring.start_monitoring(args.interval)

        try:
            print(f"Monitoring started for {args.duration} seconds...")
            time.sleep(args.duration)
        except KeyboardInterrupt:
            print("Monitoring interrupted by user")
        finally:
            monitoring.stop_monitoring()


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Monitoring CLI Tool (Prompt 29)

Command-line interface for managing the monitoring system including
starting/stopping monitoring, viewing metrics, managing alerts, and
generating reports.
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.monitoring_service import MonitoringService
import yaml


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load monitoring configuration."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing configuration: {e}")
        return {}


def format_metrics_table(metrics: Dict[str, float]) -> str:
    """Format metrics as a table."""
    if not metrics:
        return "No metrics available"

    lines = []
    lines.append("METRIC                           VALUE")
    lines.append("-" * 50)

    for metric_name, value in sorted(metrics.items()):
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)

        lines.append(f"{metric_name:<30} {formatted_value:>15}")

    return "\n".join(lines)


def format_alerts_table(alerts: List[Dict[str, Any]]) -> str:
    """Format alerts as a table."""
    if not alerts:
        return "No active alerts"

    lines = []
    lines.append("ALERT NAME                 METRIC                  SEVERITY    TRIGGERED")
    lines.append("-" * 80)

    for alert in alerts:
        name = alert['name'][:25]
        metric = alert['metric'][:20]
        severity = alert['severity']
        triggered = alert['triggered_at'][:19]  # Remove microseconds

        lines.append(f"{name:<25} {metric:<20} {severity:<10} {triggered}")

    return "\n".join(lines)


def format_health_report(health: Dict[str, Any]) -> str:
    """Format health report."""
    lines = []
    lines.append("=== SYSTEM HEALTH REPORT ===")
    lines.append(f"Generated: {health.get('timestamp', 'N/A')}")
    lines.append(f"Overall Status: {health.get('overall_status', 'unknown').upper()}")
    lines.append("")

    # System health
    system_health = health.get('system_health', {})
    if system_health:
        lines.append("System Resources:")
        lines.append(f"  CPU Usage:    {system_health.get('cpu_percent', 0):.1f}%")
        lines.append(f"  Memory Usage: {system_health.get('memory_percent', 0):.1f}%")
        lines.append(f"  Disk Usage:   {system_health.get('disk_percent', 0):.1f}%")
        load_avg = system_health.get('load_average', [0, 0, 0])
        lines.append(f"  Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
        lines.append("")

    # Application health
    app_health = health.get('application_health', {})
    if app_health:
        lines.append("Application Health:")
        lines.append(f"  API Status:      {app_health.get('api_status', 'unknown')}")
        lines.append(f"  Response Time:   {app_health.get('response_time', 0):.0f}ms")
        lines.append(f"  Database Status: {app_health.get('database_status', 'unknown')}")
        lines.append("")

    # Active alerts
    alerts = health.get('alerts', [])
    if alerts:
        lines.append("Active Alerts:")
        for alert in alerts:
            severity_icon = "🔥" if alert['severity'] == 'critical' else "⚠️"
            lines.append(f"  {severity_icon} {alert['name']} - {alert['metric']}")
        lines.append("")

    # Recommendations
    recommendations = health.get('recommendations', [])
    if recommendations:
        lines.append("Recommendations:")
        for rec in recommendations:
            lines.append(f"  • {rec}")

    return "\n".join(lines)


def start_command(args):
    """Handle start command."""
    print("Starting monitoring service...")

    config = load_config(args.config) if args.config else {}
    monitoring = MonitoringService(config)

    interval = args.interval or config.get('collection', {}).get('interval_seconds', 60)

    try:
        monitoring.start_monitoring(interval)
        print(f"✅ Monitoring started with {interval}s interval")

        if args.duration:
            print(f"Running for {args.duration} seconds...")
            time.sleep(args.duration)
            monitoring.stop_monitoring()
            print("✅ Monitoring completed")
        else:
            print("Press Ctrl+C to stop monitoring...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                monitoring.stop_monitoring()
                print("✅ Monitoring stopped")

    except Exception as e:
        print(f"❌ Error starting monitoring: {e}")
        return 1

    return 0


def status_command(args):
    """Handle status command."""
    print("Getting monitoring status...")

    config = load_config(args.config) if args.config else {}
    monitoring = MonitoringService(config)

    try:
        status = monitoring.get_monitoring_status()

        print("\n=== MONITORING STATUS ===")
        print(f"Active: {'Yes' if status.get('monitoring_active') else 'No'}")

        # Active alerts
        alerts = status.get('active_alerts', [])
        print(f"\nActive Alerts: {len(alerts)}")
        if alerts:
            print(format_alerts_table(alerts))

        # Performance summary
        perf = status.get('performance_summary', {})
        if perf:
            print("\n=== PERFORMANCE SUMMARY ===")
            overall = perf.get('overall', {})
            if overall:
                print(f"Total Requests: {overall.get('total_requests', 0)}")
                print(f"Avg Response Time: {overall.get('avg_response_time', 0):.3f}s")
                print(f"Error Rate: {overall.get('error_rate', 0):.1f}%")

        # Metrics summary
        metrics_summary = status.get('metrics_summary', {})
        if metrics_summary:
            print(f"\nMetrics Collected: {metrics_summary.get('total_data_points', 0)}")

        return 0

    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return 1


def metrics_command(args):
    """Handle metrics command."""
    print("Collecting current metrics...")

    config = load_config(args.config) if args.config else {}
    monitoring = MonitoringService(config)

    try:
        # Get current metrics
        system_metrics = monitoring.metrics_collector.collect_system_metrics()
        app_metrics = monitoring.metrics_collector.collect_application_metrics()

        all_metrics = {**system_metrics, **app_metrics}

        if args.output == 'json':
            print(json.dumps(all_metrics, indent=2))
        else:
            print("\n=== CURRENT METRICS ===")
            print(format_metrics_table(all_metrics))

        return 0

    except Exception as e:
        print(f"❌ Error collecting metrics: {e}")
        return 1


def alerts_command(args):
    """Handle alerts command."""
    config = load_config(args.config) if args.config else {}
    monitoring = MonitoringService(config)

    if args.action == 'list':
        try:
            alerts = monitoring.alert_manager.get_active_alerts()

            print("\n=== ACTIVE ALERTS ===")
            if alerts:
                print(format_alerts_table(alerts))
            else:
                print("No active alerts")

            return 0

        except Exception as e:
            print(f"❌ Error listing alerts: {e}")
            return 1

    elif args.action == 'test':
        try:
            print("Triggering test alert...")

            # Record a test metric that will trigger an alert
            monitoring.metrics_collector.record_custom_metric('test.metric', 150.0)

            # Create a test alert rule
            from scripts.monitoring_service import AlertRule
            test_rule = AlertRule(
                name='Test Alert',
                metric_name='test.metric',
                threshold=100.0,
                operator='gt',
                duration_seconds=1,
                severity='warning',
                enabled=True,
                notification_channels=['log']
            )

            monitoring.alert_manager.add_alert_rule(test_rule)

            # Evaluate alerts
            test_metrics = {'test.metric': 150.0}
            monitoring.alert_manager.evaluate_alerts(test_metrics)

            print("✅ Test alert triggered (check logs)")
            return 0

        except Exception as e:
            print(f"❌ Error testing alerts: {e}")
            return 1

    else:
        print(f"Unknown action: {args.action}")
        return 1


def health_command(args):
    """Handle health command."""
    print("Generating health report...")

    config = load_config(args.config) if args.config else {}
    monitoring = MonitoringService(config)

    try:
        health = monitoring.generate_health_report()

        if args.output == 'json':
            print(json.dumps(health, indent=2, default=str))
        else:
            print(format_health_report(health))

        # Save to file if specified
        if args.save:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"health_report_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(health, f, indent=2, default=str)
            print(f"\n💾 Report saved to {filename}")

        return 0

    except Exception as e:
        print(f"❌ Error generating health report: {e}")
        return 1


def dashboard_command(args):
    """Handle dashboard command."""
    print("Generating dashboard data...")

    config = load_config(args.config) if args.config else {}
    monitoring = MonitoringService(config)

    try:
        dashboard_data = monitoring.dashboard.generate_dashboard_data()

        if args.output == 'json':
            print(json.dumps(dashboard_data, indent=2, default=str))
        else:
            print("\n=== DASHBOARD DATA ===")

            # System overview
            system_overview = dashboard_data.get('system_overview', {})
            if system_overview:
                print("\nSystem Overview:")
                for metric, data in system_overview.items():
                    if isinstance(data, dict):
                        current = data.get('current', 0)
                        trend = data.get('trend', 'stable')
                        trend_icon = {'increasing': '↗️', 'decreasing': '↘️', 'stable': '➡️'}.get(trend, '➡️')
                        print(f"  {metric}: {current:.1f} {trend_icon}")

            # Application health
            app_health = dashboard_data.get('application_health', {})
            if app_health:
                print("\nApplication Health:")
                for metric, data in app_health.items():
                    if isinstance(data, dict):
                        status = data.get('status', 'unknown')
                        status_icon = '✅' if status == 'healthy' else '❌'
                        print(f"  {metric}: {status} {status_icon}")

        return 0

    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        return 1


def cleanup_command(args):
    """Handle cleanup command."""
    print("Cleaning up old monitoring data...")

    config = load_config(args.config) if args.config else {}
    monitoring = MonitoringService(config)

    try:
        days = args.days or config.get('storage', {}).get('retention_days', 30)

        monitoring.storage.cleanup_old_metrics(days)
        print(f"✅ Cleaned up metrics older than {days} days")

        return 0

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Monitoring System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global arguments
    parser.add_argument('--config', '-c', help='Configuration file path',
                       default='config/monitoring.yaml')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start monitoring')
    start_parser.add_argument('--interval', type=int, help='Collection interval in seconds')
    start_parser.add_argument('--duration', type=int, help='Duration to run (seconds)')

    # Status command
    status_parser = subparsers.add_parser('status', help='Get monitoring status')

    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show current metrics')
    metrics_parser.add_argument('--output', choices=['table', 'json'], default='table')

    # Alerts command
    alerts_parser = subparsers.add_parser('alerts', help='Manage alerts')
    alerts_parser.add_argument('action', choices=['list', 'test'], help='Alert action')

    # Health command
    health_parser = subparsers.add_parser('health', help='Generate health report')
    health_parser.add_argument('--output', choices=['text', 'json'], default='text')
    health_parser.add_argument('--save', action='store_true', help='Save report to file')

    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Generate dashboard data')
    dashboard_parser.add_argument('--output', choices=['summary', 'json'], default='summary')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, help='Days of data to keep')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging(args.verbose)

    # Execute command
    try:
        if args.command == 'start':
            return start_command(args)
        elif args.command == 'status':
            return status_command(args)
        elif args.command == 'metrics':
            return metrics_command(args)
        elif args.command == 'alerts':
            return alerts_command(args)
        elif args.command == 'health':
            return health_command(args)
        elif args.command == 'dashboard':
            return dashboard_command(args)
        elif args.command == 'cleanup':
            return cleanup_command(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
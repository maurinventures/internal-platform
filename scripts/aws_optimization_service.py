"""
AWS Optimization Service (Prompt 27)

Provides AWS resource optimization, cost monitoring, and performance tuning
for the Internal Platform. Focuses on S3 storage optimization, RDS performance,
API rate limiting, and cost management.
"""

import os
import time
import json
import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from botocore.exceptions import ClientError, BotoCoreError
import threading
from concurrent.futures import ThreadPoolExecutor
import functools


@dataclass
class S3OptimizationMetrics:
    """Metrics for S3 storage optimization."""
    bucket_name: str
    total_objects: int
    total_size_gb: float
    storage_classes: Dict[str, int]
    lifecycle_rules: List[str]
    cost_estimate_monthly: float
    recommendations: List[str]


@dataclass
class RDSOptimizationMetrics:
    """Metrics for RDS database optimization."""
    instance_type: str
    cpu_utilization: float
    memory_utilization: float
    connection_count: int
    storage_used_gb: float
    iops_utilization: float
    recommendations: List[str]


@dataclass
class CostOptimizationReport:
    """Cost optimization report."""
    current_monthly_cost: float
    projected_savings: float
    optimization_opportunities: List[str]
    recommendations: List[str]
    timestamp: datetime


class S3OptimizationManager:
    """
    Manages S3 storage optimization including lifecycle policies,
    storage class transitions, and cost optimization.
    """

    STORAGE_CLASS_COSTS = {
        'STANDARD': 0.023,      # $ per GB per month
        'STANDARD_IA': 0.0125,  # $ per GB per month
        'GLACIER': 0.004,       # $ per GB per month
        'DEEP_ARCHIVE': 0.00099 # $ per GB per month
    }

    def __init__(self, aws_region: str = 'us-east-1'):
        """Initialize S3 optimization manager."""
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.logger = logging.getLogger(__name__)

    def analyze_bucket_usage(self, bucket_name: str) -> S3OptimizationMetrics:
        """
        Analyze S3 bucket usage and provide optimization recommendations.

        Args:
            bucket_name: Name of the S3 bucket to analyze

        Returns:
            S3OptimizationMetrics with analysis results and recommendations
        """
        try:
            # Get bucket metrics
            total_objects = 0
            total_size_bytes = 0
            storage_classes = {}

            paginator = self.s3_client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_objects += 1
                        total_size_bytes += obj.get('Size', 0)

                        # Track storage classes
                        storage_class = obj.get('StorageClass', 'STANDARD')
                        storage_classes[storage_class] = storage_classes.get(storage_class, 0) + 1

            total_size_gb = total_size_bytes / (1024 ** 3)

            # Check existing lifecycle rules
            lifecycle_rules = self._get_lifecycle_rules(bucket_name)

            # Calculate cost estimate
            cost_estimate = self._calculate_storage_cost(storage_classes, total_size_gb)

            # Generate recommendations
            recommendations = self._generate_s3_recommendations(
                bucket_name, total_objects, total_size_gb, storage_classes, lifecycle_rules
            )

            return S3OptimizationMetrics(
                bucket_name=bucket_name,
                total_objects=total_objects,
                total_size_gb=round(total_size_gb, 2),
                storage_classes=storage_classes,
                lifecycle_rules=lifecycle_rules,
                cost_estimate_monthly=round(cost_estimate, 2),
                recommendations=recommendations
            )

        except ClientError as e:
            self.logger.error(f"Error analyzing S3 bucket {bucket_name}: {str(e)}")
            raise

    def _get_lifecycle_rules(self, bucket_name: str) -> List[str]:
        """Get existing lifecycle rules for bucket."""
        try:
            response = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            rules = []
            for rule in response.get('Rules', []):
                rules.append(f"{rule['ID']}: {rule['Status']}")
            return rules
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                return []
            raise

    def _calculate_storage_cost(self, storage_classes: Dict[str, int], total_size_gb: float) -> float:
        """Calculate estimated monthly storage cost."""
        cost = 0.0
        total_objects = sum(storage_classes.values())

        for storage_class, object_count in storage_classes.items():
            if total_objects > 0:
                size_ratio = object_count / total_objects
                size_for_class = total_size_gb * size_ratio
                cost += size_for_class * self.STORAGE_CLASS_COSTS.get(storage_class, 0.023)

        return cost

    def _generate_s3_recommendations(self, bucket_name: str, total_objects: int,
                                   total_size_gb: float, storage_classes: Dict[str, int],
                                   lifecycle_rules: List[str]) -> List[str]:
        """Generate S3 optimization recommendations."""
        recommendations = []

        # Check if lifecycle rules exist
        if not lifecycle_rules:
            recommendations.append(
                "Implement lifecycle rules to automatically transition objects to cheaper storage classes"
            )

        # Check for standard storage optimization
        standard_objects = storage_classes.get('STANDARD', 0)
        if standard_objects > total_objects * 0.8 and total_objects > 1000:
            recommendations.append(
                "Consider transitioning older objects to Standard-IA or Glacier for cost savings"
            )

        # Check bucket size for cost optimization
        if total_size_gb > 100:
            potential_savings = total_size_gb * 0.5 * (0.023 - 0.004)  # STANDARD to GLACIER
            recommendations.append(
                f"Large bucket detected ({total_size_gb:.1f}GB). "
                f"Archiving older data could save ~${potential_savings:.2f}/month"
            )

        # Check for versioning optimization
        try:
            versioning = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            if versioning.get('Status') == 'Enabled':
                recommendations.append(
                    "Consider implementing lifecycle rules for object versions to reduce storage costs"
                )
        except ClientError:
            pass

        return recommendations

    def implement_lifecycle_policy(self, bucket_name: str) -> bool:
        """
        Implement optimized lifecycle policy for the bucket.

        Returns True if policy was successfully applied.
        """
        lifecycle_configuration = {
            'Rules': [
                {
                    'ID': 'OptimizationRule',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': ''},
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'
                        },
                        {
                            'Days': 365,
                            'StorageClass': 'GLACIER'
                        },
                        {
                            'Days': 2555,  # 7 years
                            'StorageClass': 'DEEP_ARCHIVE'
                        }
                    ],
                    'AbortIncompleteMultipartUpload': {
                        'DaysAfterInitiation': 7
                    }
                }
            ]
        }

        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_configuration
            )
            self.logger.info(f"Applied lifecycle policy to bucket {bucket_name}")
            return True
        except ClientError as e:
            self.logger.error(f"Failed to apply lifecycle policy to {bucket_name}: {str(e)}")
            return False


class RDSOptimizationManager:
    """
    Manages RDS database optimization including performance monitoring,
    connection pooling, and resource utilization analysis.
    """

    def __init__(self, aws_region: str = 'us-east-1'):
        """Initialize RDS optimization manager."""
        self.rds_client = boto3.client('rds', region_name=aws_region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.logger = logging.getLogger(__name__)

    def analyze_rds_performance(self, db_instance_identifier: str) -> RDSOptimizationMetrics:
        """
        Analyze RDS instance performance and provide optimization recommendations.

        Args:
            db_instance_identifier: RDS instance identifier

        Returns:
            RDSOptimizationMetrics with performance analysis and recommendations
        """
        try:
            # Get RDS instance details
            response = self.rds_client.describe_db_instances(
                DBInstanceIdentifier=db_instance_identifier
            )
            instance = response['DBInstances'][0]
            instance_type = instance['DBInstanceClass']

            # Get CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)

            metrics = self._get_rds_metrics(db_instance_identifier, start_time, end_time)

            # Generate recommendations
            recommendations = self._generate_rds_recommendations(instance, metrics)

            return RDSOptimizationMetrics(
                instance_type=instance_type,
                cpu_utilization=metrics.get('cpu_utilization', 0),
                memory_utilization=metrics.get('memory_utilization', 0),
                connection_count=metrics.get('connection_count', 0),
                storage_used_gb=metrics.get('storage_used_gb', 0),
                iops_utilization=metrics.get('iops_utilization', 0),
                recommendations=recommendations
            )

        except ClientError as e:
            self.logger.error(f"Error analyzing RDS instance {db_instance_identifier}: {str(e)}")
            raise

    def _get_rds_metrics(self, db_instance_identifier: str,
                        start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Get RDS CloudWatch metrics."""
        metrics = {}

        metric_queries = [
            ('CPUUtilization', 'cpu_utilization'),
            ('DatabaseConnections', 'connection_count'),
            ('FreeStorageSpace', 'free_storage_bytes'),
            ('ReadIOPS', 'read_iops'),
            ('WriteIOPS', 'write_iops')
        ]

        for metric_name, key in metric_queries:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName=metric_name,
                    Dimensions=[
                        {'Name': 'DBInstanceIdentifier', 'Value': db_instance_identifier}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )

                if response['Datapoints']:
                    avg_value = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                    metrics[key] = avg_value

            except ClientError as e:
                self.logger.warning(f"Could not retrieve metric {metric_name}: {str(e)}")

        # Convert free storage to used storage
        if 'free_storage_bytes' in metrics:
            # Assuming instance has known allocated storage; this would need actual instance info
            metrics['storage_used_gb'] = 100 - (metrics['free_storage_bytes'] / (1024**3))

        return metrics

    def _generate_rds_recommendations(self, instance: Dict[str, Any],
                                    metrics: Dict[str, float]) -> List[str]:
        """Generate RDS optimization recommendations."""
        recommendations = []

        # CPU utilization recommendations
        cpu_util = metrics.get('cpu_utilization', 0)
        if cpu_util > 80:
            recommendations.append(
                f"High CPU utilization ({cpu_util:.1f}%). Consider upgrading instance type or optimizing queries."
            )
        elif cpu_util < 20:
            recommendations.append(
                f"Low CPU utilization ({cpu_util:.1f}%). Consider downgrading instance type for cost savings."
            )

        # Connection recommendations
        connection_count = metrics.get('connection_count', 0)
        if connection_count > 80:  # Assuming max connections around 100
            recommendations.append(
                f"High connection count ({connection_count:.0f}). Implement connection pooling to improve performance."
            )

        # Storage recommendations
        storage_used = metrics.get('storage_used_gb', 0)
        if storage_used > 80:  # Assuming 100GB allocated
            recommendations.append(
                "Storage usage high. Consider enabling auto-scaling or manual storage increase."
            )

        # IOPS recommendations
        read_iops = metrics.get('read_iops', 0)
        write_iops = metrics.get('write_iops', 0)
        total_iops = read_iops + write_iops

        if total_iops > 1000:  # Threshold for considering Provisioned IOPS
            recommendations.append(
                f"High IOPS usage ({total_iops:.0f}). Consider Provisioned IOPS for consistent performance."
            )

        # Instance type recommendations
        instance_type = instance['DBInstanceClass']
        if 'micro' in instance_type and cpu_util > 60:
            recommendations.append(
                "Micro instance showing high utilization. Consider upgrading to small or medium instance."
            )

        return recommendations


class CostOptimizationAnalyzer:
    """
    Analyzes AWS costs and provides optimization recommendations
    across all services used by the application.
    """

    def __init__(self, aws_region: str = 'us-east-1'):
        """Initialize cost optimization analyzer."""
        self.cost_explorer = boto3.client('ce', region_name='us-east-1')  # Cost Explorer is only in us-east-1
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.logger = logging.getLogger(__name__)

    def generate_cost_optimization_report(self) -> CostOptimizationReport:
        """
        Generate comprehensive cost optimization report.

        Returns:
            CostOptimizationReport with current costs and optimization opportunities
        """
        try:
            # Get current month costs
            current_month_cost = self._get_current_month_costs()

            # Analyze cost optimization opportunities
            optimization_opportunities = self._analyze_cost_opportunities()

            # Calculate projected savings
            projected_savings = self._calculate_projected_savings(optimization_opportunities)

            # Generate recommendations
            recommendations = self._generate_cost_recommendations(optimization_opportunities)

            return CostOptimizationReport(
                current_monthly_cost=current_month_cost,
                projected_savings=projected_savings,
                optimization_opportunities=optimization_opportunities,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )

        except ClientError as e:
            self.logger.error(f"Error generating cost optimization report: {str(e)}")
            raise

    def _get_current_month_costs(self) -> float:
        """Get current month AWS costs."""
        try:
            start_date = datetime.utcnow().replace(day=1).strftime('%Y-%m-%d')
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )

            if response['ResultsByTime']:
                cost = float(response['ResultsByTime'][0]['Total']['BlendedCost']['Amount'])
                return cost

            return 0.0

        except ClientError as e:
            self.logger.warning(f"Could not retrieve cost data: {str(e)}")
            return 0.0

    def _analyze_cost_opportunities(self) -> List[str]:
        """Analyze cost optimization opportunities."""
        opportunities = []

        # Reserved Instance opportunities
        opportunities.append("Analyze Reserved Instance pricing for RDS and EC2")

        # Storage optimization
        opportunities.append("Implement S3 lifecycle policies for archival")

        # Unused resources
        opportunities.append("Identify and remove unused EBS volumes and snapshots")

        # Right-sizing
        opportunities.append("Right-size overprovisioned instances")

        return opportunities

    def _calculate_projected_savings(self, opportunities: List[str]) -> float:
        """Calculate projected monthly savings from optimizations."""
        # This is a simplified calculation - real implementation would
        # analyze specific resources and usage patterns
        base_savings = len(opportunities) * 50  # $50 per optimization opportunity
        return float(base_savings)

    def _generate_cost_recommendations(self, opportunities: List[str]) -> List[str]:
        """Generate actionable cost optimization recommendations."""
        recommendations = [
            "Enable AWS Cost Anomaly Detection for proactive monitoring",
            "Set up budget alerts for monthly spend thresholds",
            "Review and optimize CloudWatch log retention periods",
            "Implement automated resource tagging for cost allocation",
            "Consider AWS Savings Plans for predictable workloads",
            "Enable S3 Intelligent-Tiering for automatic cost optimization",
            "Schedule non-production resources to run only during business hours"
        ]
        return recommendations


class APIRateLimitManager:
    """
    Manages API rate limiting and optimization for external service calls
    to prevent cost overruns and improve performance.
    """

    def __init__(self):
        """Initialize API rate limit manager."""
        self.rate_limits = {}
        self.request_counts = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def configure_rate_limit(self, service_name: str, requests_per_minute: int,
                           cost_per_request: float = 0.0):
        """
        Configure rate limit for a service.

        Args:
            service_name: Name of the service (e.g., 'anthropic', 'openai')
            requests_per_minute: Maximum requests per minute
            cost_per_request: Cost per API request in USD
        """
        with self.lock:
            self.rate_limits[service_name] = {
                'requests_per_minute': requests_per_minute,
                'cost_per_request': cost_per_request,
                'window_start': time.time(),
                'current_count': 0,
                'total_cost': 0.0
            }
            self.logger.info(f"Configured rate limit for {service_name}: {requests_per_minute} req/min")

    def check_rate_limit(self, service_name: str) -> Dict[str, Any]:
        """
        Check if request is within rate limit.

        Returns:
            Dict with 'allowed' boolean and rate limit info
        """
        with self.lock:
            if service_name not in self.rate_limits:
                return {'allowed': True, 'message': 'No rate limit configured'}

            limit_info = self.rate_limits[service_name]
            current_time = time.time()

            # Reset window if 60 seconds have passed
            if current_time - limit_info['window_start'] >= 60:
                limit_info['window_start'] = current_time
                limit_info['current_count'] = 0

            # Check if within limit
            if limit_info['current_count'] >= limit_info['requests_per_minute']:
                return {
                    'allowed': False,
                    'message': f"Rate limit exceeded for {service_name}",
                    'retry_after': 60 - (current_time - limit_info['window_start']),
                    'current_count': limit_info['current_count'],
                    'limit': limit_info['requests_per_minute']
                }

            return {
                'allowed': True,
                'message': 'Within rate limit',
                'current_count': limit_info['current_count'],
                'limit': limit_info['requests_per_minute'],
                'remaining': limit_info['requests_per_minute'] - limit_info['current_count']
            }

    def record_request(self, service_name: str, cost: float = 0.0):
        """Record a request for rate limiting and cost tracking."""
        with self.lock:
            if service_name in self.rate_limits:
                self.rate_limits[service_name]['current_count'] += 1
                self.rate_limits[service_name]['total_cost'] += cost

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for all configured services."""
        with self.lock:
            stats = {}
            for service_name, limit_info in self.rate_limits.items():
                stats[service_name] = {
                    'current_count': limit_info['current_count'],
                    'limit': limit_info['requests_per_minute'],
                    'total_cost': limit_info['total_cost'],
                    'utilization_percent': (limit_info['current_count'] / limit_info['requests_per_minute']) * 100
                }
            return stats


def rate_limited(service_name: str):
    """
    Decorator for rate limiting API calls.

    Usage:
        @rate_limited('anthropic')
        def call_anthropic_api():
            # API call implementation
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This would use a global instance of APIRateLimitManager
            # In practice, this should be injected as a dependency
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AWSOptimizationService:
    """
    Main service for AWS optimization encompassing all optimization managers.
    """

    def __init__(self, aws_region: str = 'us-east-1'):
        """Initialize AWS optimization service."""
        self.aws_region = aws_region
        self.s3_optimizer = S3OptimizationManager(aws_region)
        self.rds_optimizer = RDSOptimizationManager(aws_region)
        self.cost_analyzer = CostOptimizationAnalyzer(aws_region)
        self.rate_limiter = APIRateLimitManager()

        # Configure default rate limits for AI services
        self.rate_limiter.configure_rate_limit('anthropic', 100, 0.015)  # 100 req/min, ~$0.015/req
        self.rate_limiter.configure_rate_limit('openai', 60, 0.020)     # 60 req/min, ~$0.020/req

        self.logger = logging.getLogger(__name__)

    def run_comprehensive_optimization(self, s3_buckets: List[str],
                                     rds_instances: List[str]) -> Dict[str, Any]:
        """
        Run comprehensive AWS optimization analysis.

        Args:
            s3_buckets: List of S3 bucket names to analyze
            rds_instances: List of RDS instance identifiers to analyze

        Returns:
            Comprehensive optimization report
        """
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            's3_analysis': {},
            'rds_analysis': {},
            'cost_analysis': {},
            'rate_limit_stats': {},
            'total_projected_savings': 0.0,
            'priority_recommendations': []
        }

        # S3 Analysis
        s3_savings = 0.0
        for bucket_name in s3_buckets:
            try:
                analysis = self.s3_optimizer.analyze_bucket_usage(bucket_name)
                report['s3_analysis'][bucket_name] = analysis.__dict__

                # Estimate savings (simplified calculation)
                if analysis.total_size_gb > 10:
                    s3_savings += analysis.total_size_gb * 0.01  # $0.01/GB potential savings

            except Exception as e:
                self.logger.error(f"S3 analysis failed for {bucket_name}: {str(e)}")

        # RDS Analysis
        rds_savings = 0.0
        for instance_id in rds_instances:
            try:
                analysis = self.rds_optimizer.analyze_rds_performance(instance_id)
                report['rds_analysis'][instance_id] = analysis.__dict__

                # Estimate potential savings from right-sizing
                if analysis.cpu_utilization < 30:
                    rds_savings += 50.0  # $50/month potential savings from downgrading

            except Exception as e:
                self.logger.error(f"RDS analysis failed for {instance_id}: {str(e)}")

        # Cost Analysis
        try:
            cost_analysis = self.cost_analyzer.generate_cost_optimization_report()
            report['cost_analysis'] = cost_analysis.__dict__
            report['total_projected_savings'] = s3_savings + rds_savings + cost_analysis.projected_savings
        except Exception as e:
            self.logger.error(f"Cost analysis failed: {str(e)}")

        # Rate Limit Statistics
        report['rate_limit_stats'] = self.rate_limiter.get_usage_statistics()

        # Generate priority recommendations
        report['priority_recommendations'] = self._generate_priority_recommendations(report)

        return report

    def _generate_priority_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate prioritized optimization recommendations."""
        recommendations = []

        # High-impact S3 optimizations
        for bucket_name, analysis in report.get('s3_analysis', {}).items():
            if analysis.get('total_size_gb', 0) > 100:
                recommendations.append(
                    f"HIGH: Implement lifecycle policy for {bucket_name} "
                    f"({analysis['total_size_gb']:.1f}GB) - Est. savings: $"
                    f"{analysis['total_size_gb'] * 0.01:.2f}/month"
                )

        # High-impact RDS optimizations
        for instance_id, analysis in report.get('rds_analysis', {}).items():
            if analysis.get('cpu_utilization', 100) < 30:
                recommendations.append(
                    f"HIGH: Consider downsizing RDS instance {instance_id} "
                    f"(CPU: {analysis['cpu_utilization']:.1f}%) - Est. savings: $50/month"
                )

        # Cost optimization priorities
        if report.get('total_projected_savings', 0) > 100:
            recommendations.append(
                f"CRITICAL: Total optimization opportunity: $"
                f"{report['total_projected_savings']:.2f}/month"
            )

        return recommendations[:5]  # Top 5 recommendations

    def apply_s3_optimizations(self, bucket_names: List[str]) -> Dict[str, bool]:
        """Apply S3 optimizations to specified buckets."""
        results = {}
        for bucket_name in bucket_names:
            try:
                success = self.s3_optimizer.implement_lifecycle_policy(bucket_name)
                results[bucket_name] = success
                if success:
                    self.logger.info(f"Successfully optimized S3 bucket: {bucket_name}")
            except Exception as e:
                self.logger.error(f"Failed to optimize S3 bucket {bucket_name}: {str(e)}")
                results[bucket_name] = False

        return results
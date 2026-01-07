#!/usr/bin/env python3
"""
AWS Optimization CLI Tool (Prompt 27)

Command-line interface for running AWS optimization analysis and applying
optimizations to reduce costs and improve performance.

Usage:
    python run_aws_optimization.py analyze --s3-buckets bucket1,bucket2 --rds-instances instance1
    python run_aws_optimization.py optimize --apply --service s3
    python run_aws_optimization.py report --email admin@example.com
"""

import os
import sys
import json
import argparse
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.aws_optimization_service import AWSOptimizationService
from scripts.db import DatabaseSession


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('aws_optimization.log')
        ]
    )


def load_config() -> Dict[str, Any]:
    """Load AWS optimization configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'aws_optimization.yaml'

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        return {}


def get_s3_buckets_from_config(config: Dict[str, Any]) -> List[str]:
    """Extract S3 bucket names from configuration."""
    buckets = []
    for bucket_config in config.get('s3', {}).get('buckets', []):
        buckets.append(bucket_config['name'])
    return buckets


def get_rds_instances_from_config(config: Dict[str, Any]) -> List[str]:
    """Extract RDS instance identifiers from configuration."""
    instances = []
    for instance_config in config.get('rds', {}).get('instances', []):
        instances.append(instance_config['identifier'])
    return instances


def format_optimization_report(report: Dict[str, Any]) -> str:
    """Format optimization report for display."""
    output = []
    output.append("=" * 80)
    output.append("AWS OPTIMIZATION REPORT")
    output.append("=" * 80)
    output.append(f"Generated: {report.get('timestamp', 'N/A')}")
    output.append(f"Total Projected Savings: ${report.get('total_projected_savings', 0):.2f}/month")
    output.append("")

    # S3 Analysis
    if report.get('s3_analysis'):
        output.append("S3 STORAGE ANALYSIS")
        output.append("-" * 40)
        for bucket_name, analysis in report['s3_analysis'].items():
            output.append(f"Bucket: {bucket_name}")
            output.append(f"  Size: {analysis.get('total_size_gb', 0):.2f} GB")
            output.append(f"  Objects: {analysis.get('total_objects', 0):,}")
            output.append(f"  Monthly Cost: ${analysis.get('cost_estimate_monthly', 0):.2f}")

            recommendations = analysis.get('recommendations', [])
            if recommendations:
                output.append("  Recommendations:")
                for rec in recommendations:
                    output.append(f"    • {rec}")
            output.append("")

    # RDS Analysis
    if report.get('rds_analysis'):
        output.append("RDS PERFORMANCE ANALYSIS")
        output.append("-" * 40)
        for instance_id, analysis in report['rds_analysis'].items():
            output.append(f"Instance: {instance_id}")
            output.append(f"  Type: {analysis.get('instance_type', 'N/A')}")
            output.append(f"  CPU Utilization: {analysis.get('cpu_utilization', 0):.1f}%")
            output.append(f"  Connections: {analysis.get('connection_count', 0):.0f}")

            recommendations = analysis.get('recommendations', [])
            if recommendations:
                output.append("  Recommendations:")
                for rec in recommendations:
                    output.append(f"    • {rec}")
            output.append("")

    # Priority Recommendations
    if report.get('priority_recommendations'):
        output.append("PRIORITY RECOMMENDATIONS")
        output.append("-" * 40)
        for rec in report['priority_recommendations']:
            output.append(f"• {rec}")
        output.append("")

    # Rate Limiting Stats
    if report.get('rate_limit_stats'):
        output.append("API USAGE STATISTICS")
        output.append("-" * 40)
        for service, stats in report['rate_limit_stats'].items():
            output.append(f"{service.upper()}:")
            output.append(f"  Current Usage: {stats.get('current_count', 0)}/{stats.get('limit', 0)} req/min")
            output.append(f"  Utilization: {stats.get('utilization_percent', 0):.1f}%")
            output.append(f"  Total Cost: ${stats.get('total_cost', 0):.3f}")
        output.append("")

    output.append("=" * 80)
    return "\n".join(output)


def save_report(report: Dict[str, Any], output_file: str):
    """Save optimization report to file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logging.info(f"Report saved to: {output_file}")
    except Exception as e:
        logging.error(f"Failed to save report: {e}")


def send_email_report(report: Dict[str, Any], email: str):
    """Send optimization report via email."""
    try:
        # This would integrate with your email service
        # For now, just log the action
        logging.info(f"Email report would be sent to: {email}")
        logging.info("Email functionality not implemented in this demo")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def analyze_command(args, config: Dict[str, Any]):
    """Handle the analyze command."""
    # Get buckets and instances from command line or config
    if args.s3_buckets:
        s3_buckets = args.s3_buckets.split(',')
    else:
        s3_buckets = get_s3_buckets_from_config(config)

    if args.rds_instances:
        rds_instances = args.rds_instances.split(',')
    else:
        rds_instances = get_rds_instances_from_config(config)

    logging.info(f"Analyzing S3 buckets: {s3_buckets}")
    logging.info(f"Analyzing RDS instances: {rds_instances}")

    # Initialize optimization service
    optimizer = AWSOptimizationService(args.region)

    try:
        # Run comprehensive analysis
        report = optimizer.run_comprehensive_optimization(s3_buckets, rds_instances)

        # Display results
        if not args.quiet:
            print(format_optimization_report(report))

        # Save to file if requested
        if args.output:
            save_report(report, args.output)

        # Send email if requested
        if args.email:
            send_email_report(report, args.email)

        return True

    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        return False


def optimize_command(args, config: Dict[str, Any]):
    """Handle the optimize command."""
    optimizer = AWSOptimizationService(args.region)

    if args.service == 's3':
        # Apply S3 optimizations
        if args.s3_buckets:
            buckets = args.s3_buckets.split(',')
        else:
            buckets = get_s3_buckets_from_config(config)

        logging.info(f"Applying S3 optimizations to: {buckets}")

        if args.apply:
            results = optimizer.apply_s3_optimizations(buckets)

            print("S3 OPTIMIZATION RESULTS")
            print("-" * 30)
            for bucket, success in results.items():
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"{bucket}: {status}")

            return all(results.values())
        else:
            print("DRY RUN MODE - No changes will be applied")
            print("Add --apply flag to execute optimizations")
            return True

    elif args.service == 'rds':
        logging.info("RDS optimizations require manual review")
        print("RDS optimizations require manual intervention")
        print("Please review the analysis report and apply changes manually")
        return True

    else:
        logging.error(f"Unknown service: {args.service}")
        return False


def report_command(args, config: Dict[str, Any]):
    """Handle the report command."""
    # Generate a simple status report
    optimizer = AWSOptimizationService(args.region)

    # Get configuration info
    s3_buckets = get_s3_buckets_from_config(config)
    rds_instances = get_rds_instances_from_config(config)

    print("AWS OPTIMIZATION STATUS REPORT")
    print("=" * 50)
    print(f"Configured S3 Buckets: {len(s3_buckets)}")
    for bucket in s3_buckets:
        print(f"  • {bucket}")

    print(f"\nConfigured RDS Instances: {len(rds_instances)}")
    for instance in rds_instances:
        print(f"  • {instance}")

    # Get rate limiting stats
    stats = optimizer.rate_limiter.get_usage_statistics()
    if stats:
        print("\nAPI Usage Statistics:")
        for service, service_stats in stats.items():
            utilization = service_stats.get('utilization_percent', 0)
            print(f"  {service}: {utilization:.1f}% utilization")

    # Send email if requested
    if args.email:
        logging.info(f"Status report would be sent to: {args.email}")

    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AWS Optimization CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global arguments
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run optimization analysis')
    analyze_parser.add_argument('--s3-buckets', help='Comma-separated list of S3 buckets')
    analyze_parser.add_argument('--rds-instances', help='Comma-separated list of RDS instances')
    analyze_parser.add_argument('--output', '-o', help='Save report to file')
    analyze_parser.add_argument('--email', help='Email address to send report')

    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Apply optimizations')
    optimize_parser.add_argument('--service', choices=['s3', 'rds'], required=True,
                                help='Service to optimize')
    optimize_parser.add_argument('--s3-buckets', help='Comma-separated list of S3 buckets')
    optimize_parser.add_argument('--apply', action='store_true',
                                help='Actually apply changes (default is dry run)')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate status report')
    report_parser.add_argument('--email', help='Email address to send report')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    setup_logging(args.verbose)

    # Load configuration
    config = load_config()

    # Execute command
    try:
        if args.command == 'analyze':
            success = analyze_command(args, config)
        elif args.command == 'optimize':
            success = optimize_command(args, config)
        elif args.command == 'report':
            success = report_command(args, config)
        else:
            logging.error(f"Unknown command: {args.command}")
            success = False

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logging.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
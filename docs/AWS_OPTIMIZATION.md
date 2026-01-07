# AWS Optimization Guide (Prompt 27)

This guide covers AWS resource optimization, cost monitoring, and performance tuning for the Internal Platform. The optimization system helps reduce costs, improve performance, and maintain efficient resource utilization.

## Overview

The AWS Optimization system provides:
- **Cost Analysis** - Monitor spending and identify savings opportunities
- **S3 Storage Optimization** - Lifecycle policies and storage class transitions
- **RDS Performance Tuning** - Database optimization and right-sizing
- **API Rate Limiting** - Prevent cost overruns from AI service calls
- **Automated Monitoring** - Scheduled analysis and alerting

## Components

### 1. AWS Optimization Service
**File**: `scripts/aws_optimization_service.py`

Core service providing:
- S3 bucket analysis and lifecycle management
- RDS performance monitoring and recommendations
- Cost optimization analysis across all services
- API rate limiting for external services

### 2. CLI Tool
**File**: `scripts/run_aws_optimization.py`

Command-line interface for:
- Running optimization analysis
- Applying optimizations
- Generating reports

### 3. Configuration
**File**: `config/aws_optimization.yaml`

Centralized configuration for:
- S3 bucket settings and lifecycle policies
- RDS monitoring thresholds
- Cost budgets and alerts
- Rate limiting settings

### 4. GitHub Actions Workflow
**File**: `.github/workflows/aws-optimization.yml`

Automated workflows for:
- Daily cost analysis
- Weekly deep optimization
- Monthly reporting

## Usage

### Manual Analysis

```bash
# Analyze all configured resources
python scripts/run_aws_optimization.py analyze

# Analyze specific S3 buckets
python scripts/run_aws_optimization.py analyze \
  --s3-buckets bucket1,bucket2 \
  --output analysis_report.json

# Analyze specific RDS instances
python scripts/run_aws_optimization.py analyze \
  --rds-instances instance1,instance2 \
  --email admin@example.com
```

### Apply Optimizations

```bash
# Dry run (preview changes)
python scripts/run_aws_optimization.py optimize --service s3

# Apply S3 optimizations
python scripts/run_aws_optimization.py optimize --service s3 --apply

# Apply to specific buckets
python scripts/run_aws_optimization.py optimize \
  --service s3 \
  --s3-buckets bucket1,bucket2 \
  --apply
```

### Generate Reports

```bash
# Generate status report
python scripts/run_aws_optimization.py report

# Email report to administrator
python scripts/run_aws_optimization.py report \
  --email admin@example.com
```

## S3 Storage Optimization

### Lifecycle Policies

Automatic storage class transitions:

| Age | Storage Class | Cost/GB/month | Use Case |
|-----|---------------|---------------|----------|
| 0-30 days | Standard | $0.023 | Active data |
| 30-365 days | Standard-IA | $0.0125 | Infrequent access |
| 365-2555 days | Glacier | $0.004 | Archive |
| 2555+ days | Deep Archive | $0.00099 | Long-term backup |

### Configuration Levels

**Conservative**:
```yaml
transition_to_ia_days: 60
transition_to_glacier_days: 365
transition_to_deep_archive_days: 1095  # 3 years
```

**Moderate** (default):
```yaml
transition_to_ia_days: 30
transition_to_glacier_days: 365
transition_to_deep_archive_days: 2555  # 7 years
```

**Aggressive**:
```yaml
transition_to_ia_days: 30
transition_to_glacier_days: 90
transition_to_deep_archive_days: 365  # 1 year
```

### S3 Recommendations

The system provides recommendations for:
- Implementing lifecycle rules for cost savings
- Transitioning infrequently accessed data
- Optimizing versioning policies
- Cleaning up incomplete multipart uploads

## RDS Performance Optimization

### Monitoring Metrics

- **CPU Utilization** - Target 50-70% average
- **Memory Usage** - Monitor for memory pressure
- **Connection Count** - Implement pooling if >80% capacity
- **Storage Usage** - Enable auto-scaling at 80%
- **IOPS Usage** - Consider Provisioned IOPS if >1000

### Right-sizing Recommendations

| Current Utilization | Recommendation | Potential Savings |
|-------------------|----------------|-------------------|
| CPU < 20% for 7 days | Downgrade instance | $50-200/month |
| CPU > 80% sustained | Upgrade instance | Improve performance |
| High connection count | Implement pooling | Reduce load |

### Performance Thresholds

```yaml
cpu_utilization:
  high_threshold: 80.0  # %
  low_threshold: 20.0   # %

memory_utilization:
  high_threshold: 85.0  # %

connection_count:
  warning_threshold: 80   # connections
  critical_threshold: 95  # connections
```

## Cost Monitoring

### Budget Configuration

```yaml
monthly_budget: 500.0  # USD
warning_threshold: 80.0  # % of budget
critical_threshold: 95.0 # % of budget
```

### Cost Optimization Opportunities

1. **Reserved Instances** - Save 30-60% for predictable workloads
2. **Storage Class Optimization** - Reduce S3 costs by 60-90%
3. **Right-sizing** - Eliminate over-provisioned resources
4. **Unused Resource Cleanup** - Remove idle resources

### Automated Alerts

Alerts trigger when:
- Monthly spend exceeds 80% of budget
- Projected savings > $100/month identified
- CPU utilization < 20% for 7 days
- Storage usage > 90%

## API Rate Limiting

### Configured Limits

**Anthropic API**:
- 100 requests/minute
- 3,000 requests/hour
- 50,000 requests/day
- ~$0.015 per request average

**OpenAI API**:
- 60 requests/minute
- 2,000 requests/hour
- 30,000 requests/day
- ~$0.020 per request average

### Rate Limiting Features

- Automatic request throttling
- Burst allowance for traffic spikes
- Cost tracking per service
- Usage statistics and reporting

### Implementation

```python
from scripts.aws_optimization_service import APIRateLimitManager

# Configure rate limits
rate_limiter = APIRateLimitManager()
rate_limiter.configure_rate_limit('anthropic', 100, 0.015)

# Check before API call
check = rate_limiter.check_rate_limit('anthropic')
if check['allowed']:
    # Make API call
    response = make_api_call()
    # Record usage
    rate_limiter.record_request('anthropic', 0.015)
else:
    # Wait or return error
    time.sleep(check['retry_after'])
```

## Automated Monitoring

### GitHub Actions Workflows

**Daily Analysis** (6 AM UTC):
- Run cost and performance analysis
- Generate optimization recommendations
- Alert on high-cost opportunities

**Weekly Deep Scan** (Sunday 2 AM UTC):
- Comprehensive optimization analysis
- Apply approved optimizations
- Generate weekly reports

**Monthly Reporting** (1st of month):
- Historical cost analysis
- Savings achievement report
- Archive optimization data

### Manual Triggers

Available via GitHub Actions:
- **Analyze** - Run optimization analysis
- **Optimize** - Apply optimizations (requires approval)
- **Report** - Generate status report

## Security and Permissions

### Required AWS IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketVersioning",
        "s3:GetLifecycleConfiguration",
        "s3:PutLifecycleConfiguration",
        "rds:DescribeDBInstances",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage"
      ],
      "Resource": "*"
    }
  ]
}
```

### GitHub Secrets Required

- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `SLACK_WEBHOOK_URL` - Optional Slack notifications

## Configuration Examples

### Production Environment

```yaml
environments:
  production:
    auto_apply_optimizations: false  # Manual approval required
    aggressive_optimizations: false
    backup_before_changes: true
    notification_level: "all"
```

### Staging Environment

```yaml
environments:
  staging:
    auto_apply_optimizations: true
    aggressive_optimizations: true
    backup_before_changes: false
    notification_level: "errors_only"
```

## Monitoring Dashboard

### Key Metrics to Track

1. **Monthly AWS Spend**
   - Current month vs. budget
   - Month-over-month trends
   - Service breakdown

2. **Optimization Savings**
   - Realized savings from optimizations
   - Projected savings opportunities
   - ROI from optimization efforts

3. **Resource Utilization**
   - S3 storage growth and transitions
   - RDS performance metrics
   - API usage patterns

4. **Cost per Service**
   - S3 storage costs
   - RDS compute costs
   - AI API costs
   - Other AWS services

## Best Practices

### S3 Optimization

1. **Implement Lifecycle Policies Early**
   - Set up policies before accumulating data
   - Use moderate transitions initially
   - Monitor and adjust based on access patterns

2. **Monitor Storage Classes**
   - Review transition effectiveness monthly
   - Adjust policies based on access patterns
   - Consider Intelligent Tiering for unknown patterns

3. **Clean Up Regularly**
   - Remove incomplete multipart uploads
   - Delete unnecessary object versions
   - Review and remove unused buckets

### RDS Optimization

1. **Right-size Gradually**
   - Monitor performance after changes
   - Test in staging before production
   - Plan maintenance windows for changes

2. **Optimize Queries First**
   - Identify slow queries before scaling up
   - Add appropriate indexes
   - Consider read replicas for read-heavy workloads

3. **Monitor Connection Patterns**
   - Implement connection pooling
   - Set appropriate timeout values
   - Monitor for connection leaks

### Cost Management

1. **Set Realistic Budgets**
   - Based on historical usage
   - Include growth projections
   - Set appropriate alert thresholds

2. **Review Regularly**
   - Monthly cost reviews
   - Quarterly optimization assessments
   - Annual architecture reviews

3. **Tag Resources Properly**
   - Consistent tagging strategy
   - Cost allocation by project/team
   - Automated tag enforcement

## Troubleshooting

### Common Issues

**S3 Lifecycle Policy Failures**:
```
Error: Access Denied when applying lifecycle policy
```
**Solution**: Verify IAM permissions include `s3:PutLifecycleConfiguration`

**RDS Metrics Not Available**:
```
Warning: Could not retrieve metric CPUUtilization
```
**Solution**: Enable CloudWatch detailed monitoring for RDS instance

**Cost Explorer API Errors**:
```
Error: Cost Explorer API not available in region
```
**Solution**: Cost Explorer is only available in us-east-1 region

**Rate Limit Exceeded**:
```
Error: Rate limit exceeded for anthropic
```
**Solution**: Implement exponential backoff or adjust rate limits

### Debug Mode

Enable verbose logging:
```bash
python scripts/run_aws_optimization.py analyze --verbose
```

Check optimization logs:
```bash
tail -f aws_optimization.log
```

### Support

For optimization issues:
1. Check AWS IAM permissions
2. Review configuration file syntax
3. Verify AWS credentials and region
4. Check CloudWatch metrics availability
5. Review GitHub Actions logs for automated runs

## Performance Impact

### Optimization Benefits

**Expected Cost Savings**:
- S3 optimization: 30-70% storage cost reduction
- RDS right-sizing: 20-50% compute cost reduction
- API rate limiting: 15-25% AI service cost reduction

**Performance Improvements**:
- Reduced S3 retrieval times through proper storage classes
- Better RDS performance through right-sizing
- More predictable AI service performance

**Operational Benefits**:
- Automated cost monitoring
- Proactive optimization recommendations
- Reduced manual optimization effort

### Resource Usage

The optimization system uses minimal resources:
- CLI tool: <100MB memory, <1 CPU minute
- GitHub Actions: ~5 minutes execution time
- AWS API calls: <100 requests per analysis

For detailed implementation examples and API references, see the source code in `scripts/aws_optimization_service.py`.
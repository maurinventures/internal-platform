# Deployment Automation Guide (Prompt 28)

This guide covers the automated deployment system for the Internal Platform, including blue-green deployments, health checks, smoke tests, automatic rollback, and deployment monitoring.

## Overview

The Deployment Automation system provides:
- **Automated Deployments** - Standardized deployment process across environments
- **Blue-Green Deployments** - Zero-downtime deployments for production
- **Health Monitoring** - Comprehensive health checks and smoke tests
- **Automatic Rollback** - Immediate rollback on deployment failures
- **Deployment History** - Complete audit trail of all deployments
- **Manual Controls** - Emergency rollback and manual deployment options

## Components

### 1. Core Deployment Service
**File**: `scripts/deployment_automation.py`

Main orchestration service providing:
- Environment-specific deployment strategies
- Blue-green deployment implementation
- Direct deployment for staging/development
- Health checking and smoke test integration
- Automatic rollback capabilities

### 2. CLI Tools

**Deployment Script**: `scripts/deploy.sh`
- User-friendly command-line interface
- Interactive confirmations for production
- Status checking and log viewing

**Python CLI**: `scripts/deployment_automation.py`
- Programmatic deployment interface
- Integration with CI/CD pipelines

### 3. Configuration
**File**: `config/deployment.yaml`

Centralized configuration for:
- Environment-specific settings
- Health check endpoints
- Deployment scripts and commands
- Notification channels

### 4. GitHub Actions Workflows

**Main Deploy Workflow**: `.github/workflows/deploy.yml`
- Manual deployment triggers
- Automatic staging deployments
- Production deployment with approvals
- Emergency rollback procedures

**CI Integration**: `.github/workflows/ci.yml`
- Automated deployment after successful tests
- Post-deployment verification

## Deployment Strategies

### Direct Deployment

Simple deployment strategy suitable for staging and development:

1. **Pre-deployment backup** (optional)
2. **Health check** current environment
3. **Execute deployment** commands
4. **Post-deployment health check**
5. **Run smoke tests**
6. **Rollback if health checks fail**

**Use Cases**:
- Staging environment deployments
- Development environment deployments
- Simple production deployments with maintenance windows

### Blue-Green Deployment

Zero-downtime deployment strategy for production:

1. **Prepare green environment** (new version)
2. **Deploy to green environment**
3. **Health check green environment**
4. **Run smoke tests on green**
5. **Switch traffic to green**
6. **Verify production traffic**
7. **Cleanup old blue environment**

**Use Cases**:
- Production deployments requiring zero downtime
- Large applications with complex startup procedures
- Deployments requiring extensive validation

## Usage

### Command Line Interface

```bash
# Deploy to staging (simple)
./scripts/deploy.sh deploy -e staging

# Deploy to production with blue-green
./scripts/deploy.sh deploy -e production -t blue_green

# Deploy specific commit
./scripts/deploy.sh deploy -e production -c abc1234 -f

# Check deployment status
./scripts/deploy.sh status -e production

# Run health check
./scripts/deploy.sh health -e production

# View deployment logs
./scripts/deploy.sh logs -e production

# Emergency rollback
./scripts/deploy.sh rollback -e production
```

### GitHub Actions

**Manual Deployment**:
1. Go to Actions → Deploy Application
2. Click "Run workflow"
3. Select environment, branch, deployment type
4. For production, approval will be required

**Automatic Deployment**:
- Pushes to `main` branch automatically deploy to staging
- Production deployments require manual trigger

### Programmatic Usage

```python
from scripts.deployment_automation import DeploymentOrchestrator

# Initialize orchestrator
orchestrator = DeploymentOrchestrator('config/deployment.yaml')

# Deploy to staging
metrics = orchestrator.deploy(
    environment='staging',
    branch='main',
    commit_hash='abc1234'
)

# Check if deployment succeeded
if metrics.status == DeploymentStatus.SUCCESS:
    print(f"Deployment completed in {metrics.duration_seconds:.1f}s")
else:
    print(f"Deployment failed: {metrics.error_message}")

# Get deployment history
history = orchestrator.get_deployment_history(limit=5)

# Rollback if needed
orchestrator.rollback_last_deployment('production')
```

## Configuration

### Environment Configuration

```yaml
environments:
  production:
    url: "https://maurinventuresinternal.com"
    deployment_type: "blue_green"
    health_check_timeout: 300
    auto_deploy: false
    rollback_enabled: true

  staging:
    url: "https://staging.maurinventuresinternal.com"
    deployment_type: "direct"
    health_check_timeout: 180
    auto_deploy: true
    rollback_enabled: true
```

### Health Check Configuration

```yaml
health_checks:
  post_deployment:
    - endpoint: "/api/health"
      expected_status: 200
      timeout: 30
      max_attempts: 20
      interval: 15

    - endpoint: "/api/auth/me"
      expected_status: 401
      timeout: 30

    - endpoint: "/"
      expected_status: 200
      timeout: 30
```

### Deployment Scripts

```yaml
deployment_scripts:
  frontend:
    build_commands:
      - "cd frontend"
      - "npm ci --legacy-peer-deps"
      - "npm run build"

    deploy_commands:
      production:
        - "sudo cp -r frontend/build/* /var/www/html/"
        - "sudo systemctl reload nginx"
```

## Health Monitoring

### Health Check Endpoints

The system performs comprehensive health checks:

**Application Health** (`/api/health`):
- Database connectivity test
- Application status verification
- Response time monitoring

**Frontend Health** (`/`):
- HTML content verification
- Static asset loading
- Response time monitoring

**Authentication Health** (`/api/auth/me`):
- Authentication endpoint responsiveness
- Expected 401 response for unauthenticated requests

### Smoke Tests Integration

Post-deployment smoke tests verify:
- Critical user flows
- API endpoint functionality
- Database connectivity
- Static asset loading

```bash
# Smoke tests are automatically run after deployment
python tests/smoke_tests.py --url https://maurinventuresinternal.com --timeout 30
```

### Health Check Results

Health check results include:

```json
{
  "overall_status": "healthy",
  "checks": {
    "API Health": {"status": "healthy", "details": {...}},
    "Frontend": {"status": "healthy", "details": "Frontend serving HTML"},
    "Authentication": {"status": "healthy", "details": "Auth endpoint responding correctly"}
  },
  "response_times": {
    "API Health": 0.23,
    "Frontend": 0.45,
    "Authentication": 0.18
  }
}
```

## Rollback Procedures

### Automatic Rollback

Automatic rollback is triggered by:
- Health check failures after deployment
- Smoke test failures (configurable)
- Response time degradation
- Error rate increases

### Manual Rollback

```bash
# Emergency rollback via CLI
./scripts/deploy.sh rollback -e production

# Rollback via GitHub Actions
# Go to Actions → Deploy Application → Run workflow → Select "rollback"

# Programmatic rollback
orchestrator.rollback_last_deployment('production')
```

### Rollback Process

1. **Identify previous version** from deployment history
2. **Execute rollback deployment** to previous commit
3. **Verify rollback success** with health checks
4. **Notify stakeholders** of rollback completion

## Deployment History

### Metrics Tracked

Each deployment records:
- Deployment ID and timestamp
- Environment and commit hash
- Deployment duration
- Success/failure status
- Health check results
- Error messages (if any)
- Rollback status

### History Access

```bash
# View recent deployments
./scripts/deploy.sh status -e production

# Programmatic access
history = orchestrator.get_deployment_history(limit=10)
for deployment in history:
    print(f"{deployment['commit_hash'][:8]} - {deployment['status']} - {deployment['environment']}")
```

## Notifications

### Slack Integration

Deployment notifications are sent to configured Slack channels:

**Deployment Started**:
```
🚀 Deployment Started
Environment: production
Branch: main
Commit: abc1234
Type: blue_green
```

**Deployment Success**:
```
✅ Deployment Successful
Environment: production
Commit: abc1234
Duration: 245s
Health: healthy
```

**Deployment Failure**:
```
❌ Deployment Failed
Environment: production
Commit: abc1234
Error: Health check failed
Rollback: true
```

### Email Notifications

Email notifications are sent to configured recipients for:
- Production deployment success/failure
- Emergency rollbacks
- Extended health check failures

## Security

### Deployment Approvals

Production deployments require approval:

```yaml
security:
  deployment_approvals:
    production:
      required: true
      approvers: ["admin@maurinventures.com"]
      timeout_hours: 24
```

### Access Control

```yaml
security:
  access_control:
    deploy_permissions: ["admin", "devops"]
    rollback_permissions: ["admin", "devops", "lead-dev"]
```

### Audit Logging

All deployment activities are logged:
- Deployment initiation and completion
- Health check results
- Rollback actions
- User actions and approvals

## Monitoring and Alerting

### Deployment Metrics

Tracked metrics include:
- Deployment frequency
- Deployment duration
- Success/failure rates
- Rollback frequency
- Health check response times

### Performance Targets

| Metric | Target | Alerting Threshold |
|--------|--------|--------------------|
| Deployment Duration | < 5 minutes | > 10 minutes |
| Health Check Response | < 2 seconds | > 5 seconds |
| Success Rate | > 95% | < 90% |
| Rollback Rate | < 5% | > 10% |

### Alerts

Alerts are triggered for:
- Deployment failures
- Rollback executions
- Extended deployment durations
- Health check degradations

## Best Practices

### Pre-deployment

1. **Run Tests Locally**
   ```bash
   # Frontend tests
   cd frontend && npm test

   # Backend tests
   pytest tests/

   # Smoke tests
   python tests/smoke_tests.py --url http://localhost:5001
   ```

2. **Check Environment Status**
   ```bash
   ./scripts/deploy.sh health -e staging
   ./scripts/deploy.sh status -e staging
   ```

3. **Review Changes**
   - Review Git diff since last deployment
   - Check for breaking changes
   - Verify database migration compatibility

### During Deployment

1. **Monitor Progress**
   - Watch GitHub Actions workflow progress
   - Monitor Slack notifications
   - Check application logs

2. **Be Ready to Rollback**
   - Have rollback command ready
   - Monitor application metrics
   - Watch for error alerts

### Post-deployment

1. **Verify Deployment**
   ```bash
   # Run health check
   ./scripts/deploy.sh health -e production

   # Check application functionality
   curl -s https://maurinventuresinternal.com/api/health
   ```

2. **Monitor for Issues**
   - Watch error rates
   - Monitor response times
   - Check user reports

3. **Document Changes**
   - Update deployment notes
   - Record any issues encountered
   - Share deployment summary with team

## Troubleshooting

### Common Issues

**Deployment Timeout**:
```
Error: Health check timeout after 300 seconds
```
**Solution**: Check application logs, increase timeout, or investigate startup issues

**Health Check Failure**:
```
Error: API health endpoint returned 500
```
**Solution**: Check database connectivity, application logs, verify configuration

**Blue-Green Switch Failure**:
```
Error: Failed to switch traffic to green environment
```
**Solution**: Check load balancer configuration, verify green environment health

**Rollback Failure**:
```
Error: Rollback failed to previous commit
```
**Solution**: Manual intervention required, check Git history, restore from backup

### Debug Mode

Enable verbose logging:
```bash
./scripts/deploy.sh deploy -e staging -v
```

Check deployment logs:
```bash
./scripts/deploy.sh logs -e production
```

Access system logs:
```bash
sudo journalctl -u mv-internal -f
```

### Emergency Procedures

**Complete System Failure**:
1. Initiate emergency rollback
2. Check system status
3. Restore from backup if needed
4. Contact development team

**Database Issues**:
1. Check RDS status
2. Verify connection strings
3. Run database health checks
4. Consider read-only mode

**Load Balancer Issues**:
1. Check AWS Load Balancer status
2. Verify target group health
3. Manual traffic routing if needed

## Integration with Other Systems

### CI/CD Pipeline

The deployment system integrates with:
- GitHub Actions for automated testing
- Smoke tests for post-deployment verification
- AWS optimization for resource management
- Monitoring systems for alerting

### External Services

- **AWS Services**: EC2, RDS, S3, Load Balancer
- **GitHub**: Repository, Actions, Pull Requests
- **Slack**: Team notifications
- **Email**: Stakeholder notifications

For detailed implementation examples, see the source code in `scripts/deployment_automation.py` and related configuration files.
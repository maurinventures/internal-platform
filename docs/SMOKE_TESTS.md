# Smoke Tests Documentation (Prompt 26)

Smoke tests are automated health checks that verify the application is working correctly in production. They run critical user flows and API endpoints to ensure the application is functional after deployment.

## Overview

Smoke tests are designed to:
- ✅ Verify application is accessible and responding
- ✅ Check critical API endpoints are working
- ✅ Validate database connectivity
- ✅ Test authentication flows
- ✅ Ensure static assets load correctly
- ✅ Monitor application health over time

## Test Components

### Core Smoke Tests

1. **Homepage Load Test**
   - Verifies the main application loads successfully
   - Checks for proper HTML content type
   - Validates response time

2. **API Health Check**
   - Tests the `/api/health` endpoint
   - Verifies database connectivity
   - Checks application health status

3. **Auth Endpoint Test**
   - Validates authentication endpoints are reachable
   - Expects proper 401 responses for unauthenticated requests
   - Ensures auth flow is functional

4. **Models Endpoint Test**
   - Tests AI models API endpoint
   - Validates proper JSON responses
   - Checks for available models

5. **Static Assets Test**
   - Verifies CSS, JavaScript, and favicon load
   - Tests common static file paths
   - Ensures frontend resources are accessible

6. **Database Connectivity Test**
   - Tests database connectivity through API calls
   - Detects potential database connection issues
   - Validates data layer functionality

7. **Login Form Test**
   - Verifies login page loads correctly
   - Checks for required form elements
   - Tests user interface accessibility

## Running Smoke Tests

### Local Development

```bash
# Test local development server
./scripts/run_smoke_tests.sh

# Test specific URL
./scripts/run_smoke_tests.sh -u http://localhost:3000

# Test with custom timeout
./scripts/run_smoke_tests.sh -u https://staging.example.com -t 60

# Fail fast mode (exit on first failure)
./scripts/run_smoke_tests.sh -f

# Save results to file
./scripts/run_smoke_tests.sh -o smoke_results.json
```

### Production Testing

```bash
# Test production environment
./scripts/run_smoke_tests.sh -u https://maurinventuresinternal.com

# Quick health check with fail-fast
./scripts/run_smoke_tests.sh -u https://maurinventuresinternal.com -f
```

### Direct Python Usage

```bash
# Run smoke tests with Python directly
python tests/smoke_tests.py --url https://maurinventuresinternal.com --timeout 30

# Save detailed results
python tests/smoke_tests.py \
  --url https://maurinventuresinternal.com \
  --output production_smoke_results.json

# Fail fast mode
python tests/smoke_tests.py \
  --url https://maurinventuresinternal.com \
  --fail-fast
```

## Automated Testing

### GitHub Actions Integration

Smoke tests run automatically:
- **After deployments** - Validates successful deployment
- **On schedule** - Regular health monitoring (every 2 hours during business hours)
- **Manual triggers** - On-demand testing via GitHub Actions

### Workflow Files

- **`.github/workflows/smoke-tests.yml`** - Dedicated smoke test workflow
- **`.github/workflows/ci.yml`** - Includes post-deployment smoke tests

### Monitoring Schedule

```yaml
# Runs every 2 hours during business hours (9 AM to 5 PM UTC)
schedule:
  - cron: '0 9-17/2 * * 1-5'
```

## Understanding Results

### Test Output

Each test shows:
- **Status**: ✅ PASS or ❌ FAIL
- **Response Time**: Request duration in seconds
- **HTTP Status Code**: Response status (if applicable)
- **Message**: Detailed result description

Example output:
```
✅ PASS: Homepage Load (0.45s) [200] - Homepage loaded successfully
✅ PASS: API Health Check (0.23s) [200] - API health check passed
❌ FAIL: Auth Endpoint Reachable (5.12s) [500] - Auth endpoint returned error
```

### Success Criteria

**Individual Tests:**
- Response time < 5 seconds (warning if > 2 seconds)
- Correct HTTP status codes (200, 401 where expected)
- Proper content types and response data

**Overall Health:**
- All critical tests pass (Homepage, API Health, Database)
- Success rate > 85% for full test suite
- No critical failures (500 errors, timeouts)

### Result Files

JSON output contains:
```json
{
  "total_tests": 7,
  "passed": 6,
  "failed": 1,
  "success_rate": 85.7,
  "total_time": 3.45,
  "base_url": "https://maurinventuresinternal.com",
  "test_results": [
    {
      "test_name": "Homepage Load",
      "success": true,
      "message": "Homepage loaded successfully",
      "response_time": 0.45,
      "status_code": 200,
      "timestamp": 1609459200.0
    }
  ]
}
```

## Health Check Endpoint

### API Endpoint: `/api/health`

Returns application health status:

```json
{
  "status": "healthy",
  "timestamp": 1609459200.0,
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "application": "healthy"
  }
}
```

**Response Codes:**
- `200` - All systems healthy
- `503` - System unhealthy (database issues, etc.)

**Health Checks:**
- Database connectivity test
- Application responsiveness
- System timestamp

## Troubleshooting

### Common Issues

#### Connection Refused
```
❌ FAIL: Homepage Load - Request failed: Connection refused
```
**Causes:** Application not running, wrong URL, firewall issues
**Solutions:** Check if app is running, verify URL, test network connectivity

#### Timeout Errors
```
❌ FAIL: API Health Check (30.00s) - Request failed: Timeout
```
**Causes:** Slow response, high server load, network issues
**Solutions:** Increase timeout, check server resources, investigate performance

#### Database Connectivity Issues
```
❌ FAIL: Database Connectivity [503] - Possible database connectivity issue
```
**Causes:** Database offline, connection pool exhausted, credentials invalid
**Solutions:** Check database status, review connection settings, monitor logs

#### SSL/TLS Errors
```
❌ FAIL: Homepage Load - SSL certificate verification failed
```
**Causes:** Expired certificates, certificate mismatch, CA issues
**Solutions:** Check certificate expiry, verify DNS, update certificates

### Debug Mode

For detailed debugging, run with verbose output:
```bash
python tests/smoke_tests.py --url https://example.com --timeout 60 -v
```

Add debug logging to Flask app:
```bash
export FLASK_DEBUG=1
export LOG_LEVEL=DEBUG
```

### Log Analysis

Check application logs for errors during smoke test execution:
```bash
# Check Flask application logs
tail -f /var/log/mv-internal/app.log

# Check system logs
sudo journalctl -u mv-internal -f

# Check smoke test results in GitHub Actions
# Go to Actions tab → Select workflow run → View job logs
```

## Performance Benchmarks

### Target Response Times

| Test | Target | Warning Threshold |
|------|--------|-------------------|
| Homepage Load | < 2s | > 3s |
| API Health Check | < 1s | > 2s |
| Auth Endpoints | < 1s | > 2s |
| Database Tests | < 2s | > 5s |
| Static Assets | < 3s | > 5s |

### Availability Targets

- **Uptime**: 99.9% (< 45 minutes downtime per month)
- **Response Time**: 95% of requests under 2 seconds
- **Error Rate**: < 0.1% of smoke tests failing

## Integration with Monitoring

### Alerts

Smoke test failures can trigger:
- Slack/Discord notifications
- Email alerts to development team
- PagerDuty incidents (for critical failures)
- GitHub issue creation (for persistent issues)

### Metrics Collection

Results are stored and can be used for:
- Application performance trending
- Availability reporting
- SLA monitoring
- Capacity planning

### Dashboard Integration

Smoke test results can be integrated with:
- Grafana dashboards
- Application monitoring tools
- Custom status pages
- Health check aggregators

## Best Practices

### Writing Smoke Tests

1. **Keep Tests Simple**
   - Test critical paths only
   - Avoid complex business logic
   - Focus on availability and basic functionality

2. **Make Tests Fast**
   - Target < 30 seconds total runtime
   - Use timeouts to prevent hanging
   - Test in parallel when possible

3. **Ensure Tests are Reliable**
   - Handle network issues gracefully
   - Account for temporary failures
   - Use appropriate retry logic

4. **Test Production-like Environment**
   - Use realistic data and scenarios
   - Test with production configurations
   - Validate external dependencies

### Monitoring Strategy

1. **Run After Deployments**
   - Validate successful deployments
   - Catch deployment-related issues early
   - Provide confidence for releases

2. **Schedule Regular Health Checks**
   - Monitor ongoing availability
   - Detect gradual degradation
   - Maintain system awareness

3. **Alert on Failures**
   - Notify team of issues immediately
   - Escalate persistent failures
   - Track resolution times

4. **Review Results Regularly**
   - Analyze trends and patterns
   - Identify improvement opportunities
   - Update tests as application evolves

## Security Considerations

Smoke tests should:
- ✅ Not use real user credentials
- ✅ Test authentication without bypassing security
- ✅ Respect rate limits and usage policies
- ✅ Use read-only operations when possible
- ✅ Clean up any test data created

Avoid:
- ❌ Testing with production user accounts
- ❌ Bypassing authentication mechanisms
- ❌ Creating permanent test data
- ❌ Exposing sensitive information in logs
- ❌ Running destructive operations

For detailed implementation, see `tests/smoke_tests.py` and related workflow files.
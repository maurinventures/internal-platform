# CI Pipeline Setup Guide (Prompt 25)

This document explains how to set up and configure the Continuous Integration (CI) pipeline for the Internal Platform.

## Overview

The CI pipeline runs automatically on:
- **Push to main branch** - Full test suite + deployment
- **Pull requests** - Full test suite + deployment preview

## Pipeline Components

### 1. Frontend Tests & Linting
- **ESLint** - Code quality and consistency
- **Prettier** - Code formatting
- **TypeScript** - Type checking
- **Jest** - Unit and integration tests
- **Build validation** - Ensures production build works

### 2. Backend Tests & Linting
- **flake8** - Python code quality
- **black** - Python code formatting
- **isort** - Import sorting
- **pytest** - API and unit tests with coverage
- **PostgreSQL** - Database tests with real DB

### 3. Security & Quality
- **safety** - Known vulnerability scanning
- **bandit** - Security linting
- **Test coverage** - Ensures adequate test coverage

### 4. Deployment
- **Preview deployment** - For pull requests
- **Production deployment** - For main branch (after all tests pass)

## GitHub Setup Instructions

### Step 1: Enable GitHub Actions
1. Go to your repository on GitHub
2. Click **Actions** tab
3. If prompted, enable GitHub Actions for the repository

### Step 2: Configure Branch Protection
1. Go to **Settings** > **Branches**
2. Click **Add rule** or edit existing rule for `main`
3. Configure the following settings:

#### Required Settings:
```
Branch name pattern: main

☑️ Restrict pushes that create files larger than 100MB
☑️ Require a pull request before merging
  ☑️ Require approvals (1)
  ☑️ Dismiss stale reviews when new commits are pushed
  ☑️ Require review from CODEOWNERS

☑️ Require status checks to pass before merging
  ☑️ Require branches to be up to date before merging

  Required status checks:
  - Frontend Tests & Linting
  - Backend Tests & Linting
  - Security & Quality Checks

☑️ Require conversation resolution before merging
☑️ Require signed commits
☑️ Include administrators
```

### Step 3: Configure Secrets
Add the following secrets in **Settings** > **Secrets and variables** > **Actions**:

```bash
# Production deployment secrets
DEPLOY_HOST=your-production-server
DEPLOY_USER=deployment-user
DEPLOY_KEY=-----BEGIN RSA PRIVATE KEY-----...

# Database for tests (if using external DB)
TEST_DATABASE_URL=postgresql://user:pass@host:port/testdb

# Optional: Notification webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Local Development Setup

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm ci

# Run tests
npm test

# Run linting
npm run lint
npm run prettier:check
npm run type-check

# Fix linting issues
npm run lint:fix
npm run prettier:write
```

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run linting
flake8 .
black --check .
isort --check .

# Fix linting issues
black .
isort .
```

## Workflow Files

### Main CI Workflow: `.github/workflows/ci.yml`
- Runs on push/PR
- Parallel job execution for speed
- Comprehensive test coverage
- Automatic deployment

### Configuration Files:
- **Frontend**: `.eslintrc.js`, `.prettierrc`, `package.json`
- **Backend**: `.flake8`, `pyproject.toml`, `pytest.ini`
- **Git**: `.github/pull_request_template.md`

## Monitoring & Debugging

### View Pipeline Status
1. Go to **Actions** tab in GitHub
2. Click on specific workflow run
3. Expand job sections to see detailed logs

### Common Issues & Solutions

#### Frontend Tests Failing
```bash
# Run tests locally to debug
cd frontend
npm test

# Check for missing dependencies
npm ci
```

#### Backend Tests Failing
```bash
# Run tests locally
pytest tests/ -v

# Check database connection
pytest tests/test_api_endpoints.py -v -s
```

#### Linting Failures
```bash
# Frontend
npm run lint:fix
npm run prettier:write

# Backend
black .
isort .
flake8 . --statistics
```

#### Security Scan Issues
```bash
# Check for known vulnerabilities
safety check

# Security linting
bandit -r . -f json
```

## Performance Optimization

### Pipeline Speed
- **Parallel jobs** - Frontend and backend tests run simultaneously
- **Dependency caching** - npm and pip dependencies cached
- **Early failure** - Pipeline stops on first critical failure

### Cost Optimization
- **Conditional deployment** - Only deploys on main branch
- **Efficient test selection** - Only runs affected tests when possible
- **Resource limits** - Appropriate runner sizes for each job

## Success Metrics

### Test Coverage Targets
- **Frontend**: >80% code coverage
- **Backend**: >85% code coverage
- **Critical paths**: 100% coverage

### Performance Targets
- **Pipeline runtime**: <10 minutes total
- **Frontend tests**: <3 minutes
- **Backend tests**: <5 minutes
- **Deployment**: <2 minutes

## Troubleshooting

### Pipeline Not Triggering
1. Check if GitHub Actions are enabled
2. Verify workflow file syntax with GitHub Actions validator
3. Check repository permissions

### Tests Passing Locally But Failing in CI
1. Check environment differences (Node/Python versions)
2. Verify all dependencies are in package.json/requirements.txt
3. Check for file system case sensitivity issues
4. Review environment variables and secrets

### Deployment Failures
1. Verify deployment secrets are correctly set
2. Check server connectivity and permissions
3. Review deployment logs in Actions tab
4. Test deployment commands manually

For additional help, check the Actions logs or contact the development team.
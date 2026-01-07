# Internal Platform

A comprehensive video content management and AI-powered analysis system with advanced monitoring, testing, and deployment automation.

## Overview

The Internal Platform is a full-stack application that provides video content management, AI-powered content generation, and comprehensive system monitoring. Built with React and Flask, it features advanced capabilities including usage tracking, cost optimization, automated deployment, and intelligent monitoring.

## 🚀 Features

### Core Functionality
- **Video Content Management** - Upload, process, and manage video/audio files
- **AI-Powered Chat Interface** - Interactive chat with Claude and OpenAI models
- **Long-form Content Generation** - Multi-stage AI content creation pipeline
- **User Authentication** - Secure login with 2FA support
- **Usage Tracking** - Token limits, cost tracking, and optimization

### Advanced Capabilities
- **Automated Testing** - Comprehensive frontend and backend test suites
- **CI/CD Pipeline** - GitHub Actions with automated testing and deployment
- **Blue-Green Deployments** - Zero-downtime production deployments
- **Health Monitoring** - Real-time system health checks and smoke tests
- **Performance Metrics** - Detailed monitoring and alerting system
- **AWS Optimization** - Automated cost optimization and resource management

## 🏗️ Architecture

```
Frontend (React) → API (Flask) → Services → Database (PostgreSQL)
                                      ↓
              AWS S3 ← Monitoring ← AI Services (Claude/OpenAI)
```

**Technology Stack**:
- **Frontend**: React 19, TypeScript, Tailwind CSS
- **Backend**: Flask, Python 3.9+
- **Database**: PostgreSQL 14+
- **Storage**: AWS S3
- **AI Services**: Anthropic Claude, OpenAI
- **Monitoring**: Custom metrics system with SQLite
- **Deployment**: GitHub Actions, Blue-Green deployment
- **Testing**: Jest, pytest, smoke tests

## 📋 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd internal-platform
   ```

2. **Setup backend**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup frontend**:
   ```bash
   cd frontend
   npm ci --legacy-peer-deps
   cd ..
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   # Create PostgreSQL database and user
   sudo -u postgres createdb internal_platform
   sudo -u postgres psql -c "CREATE USER app_user WITH PASSWORD 'password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE internal_platform TO app_user;"

   # Initialize tables
   python -c "from scripts.db import Base, engine; Base.metadata.create_all(engine)"
   ```

6. **Start services**:
   ```bash
   # Terminal 1 - Backend
   python web/app.py

   # Terminal 2 - Frontend
   cd frontend && npm start
   ```

7. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001
   - Health Check: http://localhost:5001/api/health

### Demo Login
- Email: `joy@maurinventures.com`
- Password: Any password (demo mode)

## 📚 Documentation

### Core Documentation
- **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)** - Complete architectural overview
- **[Setup Guide](docs/SETUP_GUIDE.md)** - Detailed installation and deployment instructions
- **[API Documentation](docs/API.md)** - REST API endpoints and usage

### Feature Documentation
- **[Monitoring and Metrics](docs/MONITORING_AND_METRICS.md)** - Performance monitoring and alerting
- **[Deployment Automation](docs/DEPLOYMENT_AUTOMATION.md)** - Blue-green deployments and CI/CD
- **[AWS Optimization](docs/AWS_OPTIMIZATION.md)** - Cost optimization and resource management
- **[Testing Guide](docs/TESTING.md)** - Test suites and quality assurance
- **[Smoke Tests](docs/SMOKE_TESTS.md)** - Production health monitoring

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
pytest tests/ -v --cov=web --cov=scripts

# Frontend tests
cd frontend && npm test

# Smoke tests
python tests/smoke_tests.py --url http://localhost:5001

# Integration tests
pytest tests/test_api_endpoints.py -v
```

### Test Coverage
- **Backend**: 85%+ coverage with pytest
- **Frontend**: 80%+ coverage with Jest
- **Integration**: Full API endpoint coverage
- **E2E**: Smoke tests for critical user flows

## 🔧 Development Tools

### Command Line Interfaces

**Deployment Management**:
```bash
# Deploy to staging
./scripts/deploy.sh deploy -e staging

# Deploy to production with blue-green
./scripts/deploy.sh deploy -e production -t blue_green

# Emergency rollback
./scripts/deploy.sh rollback -e production
```

**Monitoring**:
```bash
# Start monitoring
./scripts/monitoring_cli.py start

# Get system status
./scripts/monitoring_cli.py status

# Generate health report
./scripts/monitoring_cli.py health --save
```

**AWS Optimization**:
```bash
# Analyze AWS costs
python scripts/run_aws_optimization.py analyze

# Apply S3 optimizations
python scripts/run_aws_optimization.py optimize --service s3 --apply
```

### Development Scripts

- **`scripts/deploy.sh`** - Deployment automation
- **`scripts/monitoring_cli.py`** - System monitoring
- **`scripts/run_aws_optimization.py`** - AWS cost optimization
- **`scripts/test_ci_locally.sh`** - Local CI validation
- **`tests/smoke_tests.py`** - Production health checks

## 🏭 Production Deployment

### Automated Deployment

**GitHub Actions Workflows**:
- **CI Pipeline** (`.github/workflows/ci.yml`) - Automated testing and deployment
- **Deploy Workflow** (`.github/workflows/deploy.yml`) - Manual and scheduled deployments
- **Smoke Tests** (`.github/workflows/smoke-tests.yml`) - Post-deployment health monitoring
- **AWS Optimization** (`.github/workflows/aws-optimization.yml`) - Automated cost optimization

### Manual Deployment

```bash
# Production deployment
./scripts/deploy.sh deploy \
  --environment production \
  --type blue_green \
  --branch main

# Monitor deployment
./scripts/monitoring_cli.py status
python tests/smoke_tests.py --url https://your-domain.com
```

### Infrastructure Requirements

**Minimum Production Setup**:
- **Server**: 2 CPU, 4GB RAM, 20GB storage
- **Database**: PostgreSQL RDS or equivalent
- **Storage**: S3 bucket for file uploads
- **Domain**: SSL certificate for HTTPS

**Recommended Production Setup**:
- **Server**: 4+ CPU, 8GB+ RAM, 50GB+ SSD storage
- **Database**: PostgreSQL RDS with Multi-AZ
- **Storage**: S3 with lifecycle policies
- **Load Balancer**: Application Load Balancer
- **Monitoring**: CloudWatch or equivalent

## 📊 Monitoring

### System Monitoring

**Real-time Metrics**:
- System resources (CPU, memory, disk)
- Application performance (response times, error rates)
- Database health (connections, query performance)
- Business metrics (user activity, AI usage costs)

**Alerting**:
- Slack notifications for team alerts
- Email alerts for critical issues
- Automatic escalation procedures
- Performance degradation detection

**Health Checks**:
- Automated smoke tests every 30 seconds
- Database connectivity monitoring
- External service availability checks
- Custom business logic validation

### Performance Optimization

**Monitoring Dashboard**:
```bash
# Real-time dashboard data
./scripts/monitoring_cli.py dashboard

# Historical performance analysis
./scripts/monitoring_cli.py metrics --output json
```

**AWS Cost Optimization**:
```bash
# Analyze and optimize costs
python scripts/run_aws_optimization.py analyze
python scripts/run_aws_optimization.py optimize --service s3 --apply
```

## 🔐 Security

### Authentication & Authorization
- **Multi-Factor Authentication** - TOTP with backup codes
- **Session Management** - Secure session handling with expiration
- **API Security** - Rate limiting and request validation
- **Data Protection** - Encryption at rest and in transit

### Security Monitoring
- **Audit Logging** - All authentication and administrative actions
- **Security Alerts** - Failed login attempts and suspicious activity
- **Vulnerability Scanning** - Automated dependency vulnerability checks
- **Access Control** - Role-based permissions and API access restrictions

## 💰 Cost Management

### AI Service Optimization
- **Token Limits** - 50K context, 500K daily per user
- **Prompt Caching** - Avoid duplicate AI API costs
- **Model Selection** - Intelligent model routing based on request type
- **Cost Tracking** - Real-time usage and cost monitoring

### AWS Resource Optimization
- **S3 Lifecycle Policies** - Automatic storage class transitions
- **RDS Right-sizing** - Database performance and cost optimization
- **Reserved Instance Recommendations** - Cost savings through commitments
- **Resource Usage Analysis** - Identify unused or underutilized resources

## 🚨 Incident Response

### Automated Response
- **Health Check Failures** - Automatic service restart
- **Performance Degradation** - Alert notifications and diagnostics
- **Resource Exhaustion** - Automatic scaling triggers
- **Security Events** - Immediate notification and isolation

### Manual Procedures
- **Emergency Rollback** - One-command production rollback
- **Service Recovery** - Step-by-step recovery procedures
- **Data Recovery** - Database and file system backup restoration
- **Communication** - Incident notification and status updates

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**:
   ```bash
   git clone <your-fork-url>
   cd internal-platform
   ```

2. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Development**:
   ```bash
   # Make changes
   # Run tests: pytest tests/ && cd frontend && npm test
   # Run linting: flake8 . && cd frontend && npm run lint
   ```

4. **Submit Pull Request**:
   - Ensure all tests pass
   - Include comprehensive description
   - Add any necessary documentation updates

### Code Quality Standards
- **Backend**: PEP 8 with flake8, black formatting
- **Frontend**: ESLint rules, Prettier formatting
- **Testing**: Minimum 80% code coverage
- **Documentation**: Comprehensive inline comments and README updates

## 📞 Support

### Getting Help

**Documentation**:
- Check the comprehensive guides in `/docs`
- Review inline code comments and docstrings
- Consult the troubleshooting sections

**Community**:
- GitHub Issues for bug reports and feature requests
- Slack channel for team communication
- Email support for critical production issues

**Self-Diagnosis**:
```bash
# System health check
./scripts/monitoring_cli.py health

# Run diagnostics
./scripts/test_ci_locally.sh

# Check logs
tail -f monitoring.log
sudo journalctl -u internal-platform -f
```

### Troubleshooting

**Common Issues**:
- **Database Connection**: Check PostgreSQL service and credentials
- **Frontend Build Errors**: Clear npm cache and reinstall dependencies
- **API Errors**: Verify environment variables and service status
- **Performance Issues**: Check monitoring dashboard and resource usage

**Emergency Contacts**:
- **Production Issues**: admin@maurinventures.com
- **Security Incidents**: security@maurinventures.com
- **Development Support**: dev-team@maurinventures.com

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📈 Roadmap

### Immediate Goals (Next 30 Days)
- [ ] Enhanced mobile responsiveness
- [ ] Additional AI model integrations
- [ ] Advanced analytics dashboard
- [ ] Performance optimizations

### Medium-term Goals (Next 90 Days)
- [ ] Microservices architecture migration
- [ ] Advanced user role management
- [ ] API rate limiting enhancements
- [ ] Multi-tenant support

### Long-term Goals (Next Year)
- [ ] Machine learning-based optimization
- [ ] Global deployment and CDN integration
- [ ] Advanced business intelligence features
- [ ] Ecosystem integration partnerships

## 🎯 Project Stats

- **Total Lines of Code**: ~15,000+
- **Test Coverage**: 85%+ backend, 80%+ frontend
- **Documentation**: 12 comprehensive guides
- **API Endpoints**: 25+ REST endpoints
- **CI/CD Workflows**: 4 automated workflows
- **Monitoring Metrics**: 50+ system and business metrics

---

**Built with ❤️ for video content creators and AI-powered productivity**

For detailed setup instructions, see [Setup Guide](docs/SETUP_GUIDE.md)
For architectural details, see [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
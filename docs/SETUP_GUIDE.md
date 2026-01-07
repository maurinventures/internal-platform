# Setup Guide (Prompt 30)

This guide provides step-by-step instructions for setting up and deploying the Internal Platform, including all dependencies, services, and configurations implemented through Prompts 19-30.

## Prerequisites

### System Requirements

**Minimum Requirements**:
- **OS**: Ubuntu 20.04 LTS or macOS 10.15+
- **CPU**: 2 cores, 2.4 GHz
- **Memory**: 4 GB RAM
- **Storage**: 20 GB available space
- **Network**: Internet connection for API services

**Recommended Requirements**:
- **OS**: Ubuntu 22.04 LTS or macOS 12+
- **CPU**: 4+ cores, 3.0 GHz
- **Memory**: 8+ GB RAM
- **Storage**: 50+ GB available space (SSD preferred)
- **Network**: Stable broadband connection

### Required Software

**Development Tools**:
- **Git** 2.34+ - Version control
- **Python** 3.9+ - Backend development
- **Node.js** 18+ - Frontend development
- **npm** 8+ - Package management

**Database**:
- **PostgreSQL** 14+ - Primary database
- **SQLite** 3+ - Metrics storage (included with Python)

**Optional Tools**:
- **Docker** 20+ - Containerization (optional)
- **nginx** 1.18+ - Production web server
- **systemd** - Service management (Linux)

### External Services

**Required API Keys**:
- **Anthropic API Key** - Claude AI integration
- **OpenAI API Key** - GPT model integration

**Optional Services**:
- **Slack Webhook URL** - Team notifications
- **Email Service** - Alert notifications
- **AWS Account** - Cloud services and optimization

## Quick Start

### 1. Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd internal-platform

# Verify you have all the files
ls -la
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import flask, anthropic, openai; print('Dependencies installed successfully')"
```

### 3. Database Setup

```bash
# Install PostgreSQL (Ubuntu)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE internal_platform;"
sudo -u postgres psql -c "CREATE USER app_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE internal_platform TO app_user;"

# Verify connection
psql -h localhost -U app_user -d internal_platform -c "SELECT version();"
```

### 4. Environment Configuration

```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables**:
```bash
# Database Configuration
DATABASE_URL=postgresql://app_user:secure_password@localhost:5432/internal_platform

# AI Service API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
SECRET_KEY=your_secret_key_here
FLASK_ENV=development

# Optional: Notification Services
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
EMAIL_USERNAME=your_email_username
EMAIL_PASSWORD=your_email_password

# Optional: AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 5. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm ci --legacy-peer-deps

# Verify installation
npm run type-check
```

### 6. Initialize Database

```bash
# Return to project root
cd ..

# Run database initialization script (if available)
python scripts/init_database.py

# Or manually create tables
python -c "
from scripts.db import Base, engine
Base.metadata.create_all(engine)
print('Database tables created successfully')
"
```

### 7. Start Services

```bash
# Start backend server (in one terminal)
cd /path/to/internal-platform
source venv/bin/activate
python web/app.py

# Start frontend development server (in another terminal)
cd /path/to/internal-platform/frontend
npm start
```

### 8. Verify Installation

**Backend Health Check**:
```bash
curl http://localhost:5001/api/health
```
Expected response: `{"status": "healthy", ...}`

**Frontend Access**:
- Open browser to http://localhost:3000
- Should see login page
- Test with demo credentials: `joy@maurinventures.com` / any password

**Run Tests**:
```bash
# Backend tests
pytest tests/

# Frontend tests
cd frontend && npm test
```

## Detailed Setup Instructions

### Development Environment

#### 1. Python Environment Setup

```bash
# Install Python (if not already installed)
# Ubuntu/Debian:
sudo apt install python3.9 python3.9-venv python3.9-dev

# macOS with Homebrew:
brew install python@3.9

# Create and activate virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 black isort
```

#### 2. Node.js Environment Setup

```bash
# Install Node.js (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Node.js (macOS with Homebrew)
brew install node@18

# Verify installation
node --version  # Should be 18.x.x
npm --version   # Should be 8.x.x or higher

# Install frontend dependencies
cd frontend
npm ci --legacy-peer-deps

# Install additional development tools
npm install -g typescript eslint prettier
```

#### 3. Database Configuration

**PostgreSQL Installation and Setup**:

```bash
# Ubuntu/Debian installation
sudo apt update
sudo apt install postgresql-14 postgresql-client-14 postgresql-contrib-14

# macOS installation
brew install postgresql@14
brew services start postgresql@14

# Create application database
sudo -u postgres createdb internal_platform

# Create application user
sudo -u postgres psql -c "
CREATE USER internal_platform_user WITH PASSWORD 'development_password';
GRANT ALL PRIVILEGES ON DATABASE internal_platform TO internal_platform_user;
ALTER USER internal_platform_user CREATEDB;
"

# Test connection
psql -h localhost -U internal_platform_user -d internal_platform -c "SELECT 1;"
```

**Database Schema Setup**:

```bash
# Initialize database tables
python -c "
import sys
sys.path.append('.')
from scripts.db import Base, engine
Base.metadata.create_all(engine)
print('✅ Database schema created successfully')
"

# Verify tables were created
psql -h localhost -U internal_platform_user -d internal_platform -c "\dt"
```

#### 4. Configuration Files

**Create Application Configuration**:

```bash
# Create main environment file
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://internal_platform_user:development_password@localhost:5432/internal_platform

# Application
SECRET_KEY=development-secret-key-change-in-production
FLASK_ENV=development
TESTING=False

# AI Services
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url

# AWS (Optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
EOF
```

**Update Configuration Files**:

```bash
# Update deployment configuration
cp config/deployment.yaml.example config/deployment.yaml
nano config/deployment.yaml  # Edit as needed

# Update monitoring configuration
cp config/monitoring.yaml.example config/monitoring.yaml
nano config/monitoring.yaml  # Edit as needed

# Update AWS optimization configuration
cp config/aws_optimization.yaml.example config/aws_optimization.yaml
nano config/aws_optimization.yaml  # Edit as needed
```

### Production Deployment

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.9 python3.9-venv python3.9-dev \
                   postgresql-14 nginx git curl \
                   build-essential libpq-dev

# Create application user
sudo useradd -m -s /bin/bash internal-platform
sudo mkdir -p /opt/internal-platform
sudo chown internal-platform:internal-platform /opt/internal-platform
```

#### 2. Application Deployment

```bash
# Switch to application user
sudo -u internal-platform -i

# Clone application
cd /opt/internal-platform
git clone <repository-url> .

# Set up Python environment
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd frontend
npm ci --legacy-peer-deps --production
npm run build
cd ..
```

#### 3. Database Setup (Production)

```bash
# Create production database
sudo -u postgres createdb internal_platform_prod

# Create production user with limited privileges
sudo -u postgres psql -c "
CREATE USER internal_platform_prod WITH PASSWORD 'production_password_here';
GRANT CONNECT ON DATABASE internal_platform_prod TO internal_platform_prod;
GRANT USAGE ON SCHEMA public TO internal_platform_prod;
GRANT CREATE ON SCHEMA public TO internal_platform_prod;
"

# Initialize production database
sudo -u internal-platform bash -c "
cd /opt/internal-platform
source venv/bin/activate
DATABASE_URL=postgresql://internal_platform_prod:production_password_here@localhost:5432/internal_platform_prod python -c '
from scripts.db import Base, engine
Base.metadata.create_all(engine)
print(\"Production database initialized\")
'
"
```

#### 4. Systemd Service Configuration

```bash
# Create systemd service file
sudo cat > /etc/systemd/system/internal-platform.service << 'EOF'
[Unit]
Description=Internal Platform Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=internal-platform
Group=internal-platform
WorkingDirectory=/opt/internal-platform
Environment=PATH=/opt/internal-platform/venv/bin
Environment=DATABASE_URL=postgresql://internal_platform_prod:production_password_here@localhost:5432/internal_platform_prod
Environment=SECRET_KEY=production_secret_key_here
Environment=FLASK_ENV=production
ExecStart=/opt/internal-platform/venv/bin/python web/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable internal-platform
sudo systemctl start internal-platform
sudo systemctl status internal-platform
```

#### 5. Nginx Configuration

```bash
# Create nginx site configuration
sudo cat > /etc/nginx/sites-available/internal-platform << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    # Frontend static files
    location / {
        root /opt/internal-platform/frontend/build;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/api/health;
        access_log off;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/internal-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. SSL Configuration (Optional)

```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Monitoring Setup

#### 1. System Monitoring

```bash
# Install monitoring dependencies
pip install psutil requests pyyaml

# Start monitoring service
python scripts/monitoring_cli.py start --duration 86400  # Run for 24 hours

# Check monitoring status
python scripts/monitoring_cli.py status

# Generate health report
python scripts/monitoring_cli.py health --save
```

#### 2. Log Configuration

```bash
# Create log directories
sudo mkdir -p /var/log/internal-platform
sudo chown internal-platform:internal-platform /var/log/internal-platform

# Configure log rotation
sudo cat > /etc/logrotate.d/internal-platform << 'EOF'
/var/log/internal-platform/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 internal-platform internal-platform
    postrotate
        systemctl reload internal-platform
    endscript
}
EOF
```

#### 3. Automated Backups

```bash
# Create backup script
sudo cat > /opt/internal-platform/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/internal-platform"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump -h localhost -U internal_platform_prod internal_platform_prod > "$BACKUP_DIR/db_$DATE.sql"

# Application backup
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" -C /opt/internal-platform \
    --exclude='venv' --exclude='node_modules' --exclude='.git' .

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/internal-platform/scripts/backup.sh

# Add to crontab
echo "0 2 * * * /opt/internal-platform/scripts/backup.sh" | sudo crontab -u internal-platform -
```

## Testing and Validation

### 1. Unit Tests

```bash
# Run backend tests
pytest tests/ -v --cov=web --cov=scripts

# Run frontend tests
cd frontend
npm test -- --coverage --watchAll=false

# Run linting
flake8 .
cd frontend && npm run lint
```

### 2. Integration Tests

```bash
# Run API integration tests
pytest tests/test_api_endpoints.py -v

# Run smoke tests against running application
python tests/smoke_tests.py --url http://localhost:5001

# Test deployment automation
python scripts/deployment_automation.py deploy \
  --environment staging \
  --branch main \
  --commit $(git rev-parse HEAD)
```

### 3. Performance Testing

```bash
# Run performance monitoring
python scripts/monitoring_cli.py start --duration 300  # 5 minutes

# Generate performance report
python scripts/monitoring_cli.py metrics --output json

# Test AWS optimization
python scripts/run_aws_optimization.py analyze --s3-buckets test-bucket
```

## Troubleshooting

### Common Issues

**Database Connection Failed**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U internal_platform_user -d internal_platform

# Check connection string in .env file
echo $DATABASE_URL
```

**Frontend Build Errors**:
```bash
# Clear npm cache
cd frontend
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**Python Import Errors**:
```bash
# Activate virtual environment
source venv/bin/activate

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Permission Errors**:
```bash
# Fix file permissions
sudo chown -R internal-platform:internal-platform /opt/internal-platform
sudo chmod +x scripts/*.sh scripts/*.py

# Fix service permissions
sudo systemctl daemon-reload
sudo systemctl restart internal-platform
```

### Log Analysis

**Application Logs**:
```bash
# View application logs
sudo journalctl -u internal-platform -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# View monitoring logs
tail -f monitoring.log
tail -f monitoring_alerts.log
```

**Performance Debugging**:
```bash
# Check system resources
python scripts/monitoring_cli.py metrics

# Check database performance
psql -h localhost -U internal_platform_user -d internal_platform -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;
"

# Check API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5001/api/health
```

## Security Hardening

### 1. System Security

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS

# Disable unnecessary services
sudo systemctl disable apache2 # If installed
sudo systemctl disable sendmail # If installed
```

### 2. Application Security

```bash
# Set secure file permissions
sudo chmod 600 .env
sudo chmod 700 /opt/internal-platform
sudo chmod 755 /opt/internal-platform/web
sudo chmod 644 /opt/internal-platform/web/*.py

# Set up fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Database Security

```bash
# Configure PostgreSQL security
sudo -u postgres psql -c "
ALTER USER postgres PASSWORD 'secure_postgres_password';
REVOKE ALL ON DATABASE template0 FROM public;
REVOKE ALL ON DATABASE template1 FROM public;
"

# Update PostgreSQL configuration
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure local connections use md5 authentication

sudo systemctl restart postgresql
```

## Maintenance

### Regular Maintenance Tasks

**Daily**:
- Check system health: `python scripts/monitoring_cli.py health`
- Review application logs: `sudo journalctl -u internal-platform --since="1 day ago"`
- Verify backups: `ls -la /opt/backups/internal-platform/`

**Weekly**:
- Update system packages: `sudo apt update && sudo apt upgrade`
- Clean up old logs: `sudo logrotate -f /etc/logrotate.d/internal-platform`
- Review monitoring alerts: `python scripts/monitoring_cli.py alerts list`

**Monthly**:
- Update dependencies: `pip list --outdated` and `npm outdated`
- Review AWS costs: `python scripts/run_aws_optimization.py analyze`
- Performance optimization: Review monitoring dashboard data

### Scaling Considerations

**Horizontal Scaling**:
- Set up load balancer (nginx, HAProxy, AWS ALB)
- Configure session store (Redis, database)
- Implement database read replicas

**Vertical Scaling**:
- Monitor resource usage trends
- Upgrade server instance sizes
- Optimize database configuration

**Monitoring Scaling**:
- Implement centralized logging (ELK stack)
- Set up metrics collection (Prometheus)
- Configure advanced alerting

This setup guide provides a comprehensive foundation for deploying and maintaining the Internal Platform. For specific troubleshooting or advanced configuration, refer to the individual component documentation in the `/docs` directory.
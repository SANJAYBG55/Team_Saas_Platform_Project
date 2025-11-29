# DEPLOYMENT GUIDE

## Complete Setup Instructions for Team SaaS Platform

### 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Post-Installation](#post-installation)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Python 3.11 or higher
- MySQL 8.0 or higher
- Redis 7.0+ (optional but recommended)
- Node.js 18+ (for frontend assets)
- Git

### For Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+

---

## Local Development Setup

### Step 1: Clone and Setup Environment

```bash
# Navigate to project directory
cd "c:\ABSP\Django Projects\Team_Saas_Platform_Project"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy example env file
copy .env.example .env

# Edit .env file with your configuration
# Important variables to set:
# - SECRET_KEY (generate a new one for production)
# - DEBUG=True (for development)
# - DATABASE credentials
# - EMAIL settings
```

### Step 3: Setup MySQL Database

```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE Team_Saas_Platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'Saas_User'@'localhost' IDENTIFIED BY 'Saas@123';

-- Grant privileges
GRANT ALL PRIVILEGES ON Team_Saas_Platform.* TO 'Saas_User'@'localhost';
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

### Step 4: Run Migrations

```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Follow prompts to create admin user
```

### Step 5: Create Initial Data

```bash
# Create initial subscription plans (optional script)
python manage.py shell

# In Python shell:
from apps.subscriptions.models import Plan
from decimal import Decimal

# Create Starter Plan
Plan.objects.create(
    name="Starter",
    slug="starter",
    description="Perfect for small teams",
    price=Decimal("19.00"),
    billing_interval="MONTHLY",
    max_users=10,
    max_teams=5,
    max_projects=10,
    max_storage_gb=10,
    trial_days=14,
    is_active=True,
    sort_order=1
)

# Create Professional Plan
Plan.objects.create(
    name="Professional",
    slug="professional",
    description="For growing businesses",
    price=Decimal("49.00"),
    billing_interval="MONTHLY",
    max_users=50,
    max_teams=999,
    max_projects=999,
    max_storage_gb=100,
    enable_advanced_reports=True,
    enable_priority_support=True,
    is_popular=True,
    trial_days=14,
    is_active=True,
    sort_order=2
)

# Create Enterprise Plan
Plan.objects.create(
    name="Enterprise",
    slug="enterprise",
    description="For large organizations",
    price=Decimal("199.00"),
    billing_interval="MONTHLY",
    max_users=999,
    max_teams=999,
    max_projects=999,
    max_storage_gb=1000,
    enable_api_access=True,
    enable_advanced_reports=True,
    enable_priority_support=True,
    enable_custom_branding=True,
    enable_sso=True,
    enable_audit_logs=True,
    trial_days=30,
    is_active=True,
    sort_order=3
)

exit()
```

### Step 6: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 7: Run Development Server

```bash
# Run Django development server
python manage.py runserver

# Access application:
# - Web: http://localhost:8000
# - Admin: http://localhost:8000/django-admin/
```

### Optional: Run Redis and Celery

```bash
# Terminal 1: Redis (if installed locally)
redis-server

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Celery Beat (for scheduled tasks)
celery -A config beat -l info
```

---

## Docker Deployment

### Step 1: Prepare Environment

```bash
# Copy environment file
copy .env.example .env

# Edit .env with production values
# Set DEBUG=False
# Set strong SECRET_KEY
# Configure email settings
```

### Step 2: Build and Run

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 3: Initialize Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Step 4: Create Initial Data

```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Run the same Plan creation code from Step 5 above
```

### Step 5: Access Application

- Web Application: http://localhost:8000
- Django Admin: http://localhost:8000/django-admin/
- MySQL: localhost:3306
- Redis: localhost:6379

### Docker Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web

# Stop services
docker-compose stop

# Start services
docker-compose start

# Restart services
docker-compose restart

# Remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Setup SSL/HTTPS
- [ ] Configure production database
- [ ] Setup email service (SMTP/SendGrid/etc.)
- [ ] Configure static file storage (S3/CDN)
- [ ] Setup monitoring (Sentry, etc.)
- [ ] Configure backup strategy
- [ ] Setup domain/subdomain
- [ ] Configure firewall rules

### Recommended Production Stack

```
Internet
    ↓
NGINX (Reverse Proxy + SSL)
    ↓
Gunicorn (WSGI Server)
    ↓
Django Application
    ↓
MySQL Database + Redis Cache
```

### NGINX Configuration Example

```nginx
# /etc/nginx/sites-available/saasplatform

upstream django {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Static files
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /app/media/;
        expires 7d;
    }
    
    # Django application
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Gunicorn Configuration

```python
# gunicorn_config.py

bind = "0.0.0.0:8000"
workers = 4  # (2 x num_cores) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "saas_platform"

# Security
limit_request_line = 4096
limit_request_fields = 100
```

### Systemd Service (for non-Docker deployment)

```ini
# /etc/systemd/system/saasplatform.service

[Unit]
Description=SaaS Platform Gunicorn Application
After=network.target mysql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/app
Environment="PATH=/app/venv/bin"
ExecStart=/app/venv/bin/gunicorn -c /app/gunicorn_config.py config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Celery Systemd Services

```ini
# /etc/systemd/system/celery.service

[Unit]
Description=Celery Service
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/app
Environment="PATH=/app/venv/bin"
ExecStart=/app/venv/bin/celery -A config worker -l info
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID

[Install]
WantedBy=multi-user.target
```

---

## Post-Installation

### Create Sample Tenants (for testing)

```bash
python manage.py shell
```

```python
from apps.tenants.models import Tenant, Domain
from apps.accounts.models import User
from datetime import datetime, timedelta

# Create a sample tenant
tenant = Tenant.objects.create(
    name="Test Company",
    slug="testcompany",
    company_name="Test Company Inc.",
    company_email="contact@testcompany.com",
    status="PENDING",
    is_approved=False,
)

# Create domain
Domain.objects.create(
    tenant=tenant,
    domain="testcompany.localhost",
    domain_type="SUBDOMAIN",
    is_primary=True,
    is_verified=True,
)

print(f"Created tenant: {tenant.name}")
```

### Test Email Functionality

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from SaaS Platform.',
    'noreply@saasplatform.com',
    ['test@example.com'],
    fail_silently=False,
)
```

### Monitor Application

```bash
# Check logs
tail -f logs/django.log

# Check Celery workers
celery -A config inspect active

# Check database connections
python manage.py dbshell
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Problem**: `django.db.utils.OperationalError: (2002, "Can't connect to MySQL server")`

**Solution**:
- Verify MySQL is running: `systemctl status mysql`
- Check credentials in .env file
- Ensure MySQL port (3306) is accessible
- Test connection: `mysql -u Saas_User -p Team_Saas_Platform`

#### 2. Static Files Not Loading

**Problem**: CSS/JS files return 404

**Solution**:
```bash
# Collect static files
python manage.py collectstatic --noinput

# Verify STATIC_ROOT in settings
# Check NGINX static file configuration
```

#### 3. Permission Errors

**Problem**: Permission denied when uploading files

**Solution**:
```bash
# Set proper permissions
chmod -R 755 media/
chown -R www-data:www-data media/
```

#### 4. Celery Not Processing Tasks

**Problem**: Tasks stuck in queue

**Solution**:
```bash
# Check Celery worker status
celery -A config inspect active

# Restart Celery
systemctl restart celery

# Clear queue (if needed)
celery -A config purge
```

#### 5. Docker Container Crashes

**Problem**: Web container keeps restarting

**Solution**:
```bash
# Check logs
docker-compose logs web

# Check database connection
docker-compose exec web python manage.py check

# Verify migrations
docker-compose exec web python manage.py showmigrations
```

### Performance Optimization

1. **Enable Redis Caching**
```python
# Ensure Redis is running and configured in settings.py
```

2. **Database Optimization**
```sql
-- Add indexes for frequently queried fields
-- Check slow query log
```

3. **Enable Gzip Compression** (in NGINX)
```nginx
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript;
```

4. **Use CDN for Static Files**
- Configure S3/CloudFront for static assets
- Update `STATIC_URL` in settings

### Health Checks

```bash
# Check application health
curl http://localhost:8000/

# Check database
python manage.py check --database default

# Check migrations
python manage.py showmigrations

# Test celery
celery -A config inspect ping
```

---

## Backup Strategy

### Database Backup

```bash
# Create backup
mysqldump -u Saas_User -p Team_Saas_Platform > backup_$(date +%Y%m%d).sql

# Restore backup
mysql -u Saas_User -p Team_Saas_Platform < backup_20240101.sql
```

### Media Files Backup

```bash
# Create tar archive
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Restore
tar -xzf media_backup_20240101.tar.gz
```

### Automated Backups

Add to crontab:
```bash
# Daily database backup at 2 AM
0 2 * * * mysqldump -u Saas_User -p'Saas@123' Team_Saas_Platform | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz

# Weekly media backup on Sundays at 3 AM
0 3 * * 0 tar -czf /backups/media_$(date +\%Y\%m\%d).tar.gz /app/media/
```

---

## Security Recommendations

1. **Change default passwords**
2. **Enable firewall (ufw/iptables)**
3. **Regular security updates**
4. **Implement rate limiting**
5. **Enable SSL/TLS**
6. **Use environment variables for secrets**
7. **Regular security audits**
8. **Monitor logs for suspicious activity**

---

## Support

For issues or questions:
- Check logs: `logs/django.log`
- Review documentation
- Contact: support@example.com

---

**Last Updated**: 2024
**Version**: 1.0.0

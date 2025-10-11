# ======================================================================================
# ==                    API DEPLOYMENT GUIDE (v1.0)                                  ==
# ======================================================================================
# PRIME DIRECTIVE:
#   دليل نشر API احترافي - Professional API deployment guide

# 🚀 DEPLOYMENT GUIDE - دليل النشر

## 📋 Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Production Setup](#production-setup)
3. [Environment Variables](#environment-variables)
4. [Nginx Configuration](#nginx-configuration)
5. [SSL/HTTPS Setup](#ssl-https-setup)
6. [Monitoring & Logging](#monitoring--logging)

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t cogniforge-api:latest .
```

### Run Docker Container

```bash
docker run -d \
  --name cogniforge-api \
  -p 5000:5000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e SECRET_KEY="your-secret-key" \
  -e FLASK_ENV="production" \
  -e OPENAI_API_KEY="your-openai-key" \
  --restart unless-stopped \
  cogniforge-api:latest
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

---

## 🏭 Production Setup

### 1. Install Production Server (Gunicorn)

```bash
pip install gunicorn
```

### 2. Create Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
# Gunicorn configuration
bind = "0.0.0.0:5000"
workers = 4  # (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Process naming
proc_name = "cogniforge-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if not using nginx)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
```

### 3. Run with Gunicorn

```bash
gunicorn -c gunicorn.conf.py "app:create_app()"
```

### 4. Create Systemd Service

Create `/etc/systemd/system/cogniforge-api.service`:

```ini
[Unit]
Description=CogniForge API Service
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/cogniforge
Environment="PATH=/var/www/cogniforge/venv/bin"
Environment="DATABASE_URL=postgresql://..."
Environment="SECRET_KEY=..."
Environment="FLASK_ENV=production"
ExecStart=/var/www/cogniforge/venv/bin/gunicorn -c gunicorn.conf.py "app:create_app()"
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cogniforge-api
sudo systemctl start cogniforge-api
sudo systemctl status cogniforge-api
```

---

## 🔐 Environment Variables

### Production Environment Variables

Create `.env.production`:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-change-this
FLASK_APP=app

# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# API Keys
OPENAI_API_KEY=your-openai-api-key

# CORS Origins (comma-separated)
PRODUCTION_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Logging
APP_LOG_LEVEL=INFO

# Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Rate Limiting (if implemented)
RATELIMIT_ENABLED=true
RATELIMIT_DEFAULT=100/hour
```

---

## 🔧 Nginx Configuration

### Basic Nginx Configuration

Create `/etc/nginx/sites-available/cogniforge-api`:

```nginx
upstream cogniforge_api {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Logging
    access_log /var/log/nginx/cogniforge-api-access.log;
    error_log /var/log/nginx/cogniforge-api-error.log;
    
    # Max upload size
    client_max_body_size 10M;
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://cogniforge_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # CORS headers (if not handled by Flask)
        # add_header Access-Control-Allow-Origin "*" always;
        # add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        # add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    }
    
    # Static files (if any)
    location /static {
        alias /var/www/cogniforge/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://cogniforge_api/admin/api/database/health;
        access_log off;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/cogniforge-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 SSL/HTTPS Setup

### Using Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## 📊 Monitoring & Logging

### 1. Application Logging

Logs are stored in `/var/www/cogniforge/logs/`:
- `cogniforge.log` - Application logs
- `gunicorn-access.log` - Access logs
- `gunicorn-error.log` - Error logs

### 2. Log Rotation

Create `/etc/logrotate.d/cogniforge-api`:

```
/var/www/cogniforge/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload cogniforge-api > /dev/null 2>&1 || true
    endscript
}
```

### 3. Health Monitoring

Use the health check endpoint:
```bash
curl https://api.yourdomain.com/admin/api/database/health
```

### 4. Performance Monitoring

Consider using:
- **Prometheus** + **Grafana** for metrics
- **ELK Stack** (Elasticsearch, Logstash, Kibana) for log analysis
- **Sentry** for error tracking
- **New Relic** or **DataDog** for APM

---

## 🚦 Health Checks

### Basic Health Check Script

Create `health_check.sh`:

```bash
#!/bin/bash

# Health check script
API_URL="http://localhost:5000/admin/api/database/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "✅ API is healthy"
    exit 0
else
    echo "❌ API is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

Add to crontab for monitoring:
```bash
# Check every 5 minutes
*/5 * * * * /var/www/cogniforge/health_check.sh >> /var/log/cogniforge-health.log 2>&1
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /var/www/cogniforge
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          flask db upgrade
          sudo systemctl restart cogniforge-api
```

---

## 📦 Backup Strategy

### Database Backup

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/var/backups/cogniforge"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump $DATABASE_URL > "$BACKUP_DIR/db_backup_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db_backup_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /var/www/cogniforge/backup.sh
```

---

## ✅ Pre-Deployment Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up SSL/HTTPS
- [ ] Configure CORS properly
- [ ] Set up logging and monitoring
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Test health check endpoint
- [ ] Configure log rotation
- [ ] Set up error tracking (Sentry)
- [ ] Load test the API
- [ ] Document API endpoints
- [ ] Set up CI/CD pipeline
- [ ] Configure rate limiting
- [ ] Review security headers
- [ ] Test disaster recovery

---

## 🎉 Deployment Complete!

Your enterprise-grade CRUD RESTful API is now deployed and ready for production use!

For support, visit: https://cogniforge.ai/support

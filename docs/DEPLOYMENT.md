# 🚀 Deployment Guide

## Production Environment Setup

### Environment Variables
```bash
# Required production settings
export SECRET_KEY="your-32-character-random-secret-key-here"
export FLASK_ENV="production"
export FLASK_DEBUG=0

# Optional settings
export PORT="3001"
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

### Basic Production Server
```bash
# Install production WSGI server
pip install gunicorn

# Start production server
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:3001 backend.app:app
```

## AWS Deployment

### EC2 + Application Load Balancer

#### Step 1: Launch EC2 Instance
```bash
# Launch Ubuntu 22.04 LTS instance (t3.medium recommended)
# Security group: Allow HTTP (80), HTTPS (443), SSH (22), Custom (3001)

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### Step 2: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip python3-venv nginx git -y

# Clone repository
git clone https://github.com/your-username/TriviaApp.git
cd TriviaApp

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
```

#### Step 3: Configure Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/trivia-app.service
```

```ini
[Unit]
Description=Trivia App Gunicorn
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/TriviaApp
Environment="PATH=/home/ubuntu/TriviaApp/venv/bin"
Environment="SECRET_KEY=your-production-secret-key"
Environment="FLASK_ENV=production"
ExecStart=/home/ubuntu/TriviaApp/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:3001 backend.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trivia-app
sudo systemctl start trivia-app
sudo systemctl status trivia-app
```

#### Step 4: Configure Nginx
```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/trivia-app
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # WebSocket upgrade headers for Socket.IO
    location /socket.io/ {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Application routes
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/trivia-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5: SSL with Let's Encrypt
```bash
# Install certbot
sudo apt install snapd
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

#### Cost: ~$50-60/month
- EC2 t3.medium: ~$30/month
- Application Load Balancer: ~$20/month  
- Route 53: ~$0.50/month
- SSL Certificate: Free

## Azure Deployment

### App Service

#### Step 1: Prepare Application
```bash
# Add gunicorn to requirements
echo "gunicorn" >> requirements.txt

# Create startup script
cat > startup.sh << 'EOF'
#!/bin/bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 backend.app:app
EOF
chmod +x startup.sh
```

#### Step 2: Deploy via Azure CLI
```bash
# Login and create resources
az login
az group create --name trivia-rg --location "East US"

# Create App Service plan
az appservice plan create \
  --name trivia-plan \
  --resource-group trivia-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group trivia-rg \
  --plan trivia-plan \
  --name your-app-name \
  --runtime "PYTHON|3.9" \
  --startup-file startup.sh

# Configure settings
az webapp config appsettings set \
  --resource-group trivia-rg \
  --name your-app-name \
  --settings SECRET_KEY="your-key" FLASK_ENV="production"

# Enable WebSockets
az webapp config set \
  --resource-group trivia-rg \
  --name your-app-name \
  --web-sockets-enabled true
```

#### Step 3: Add Custom Domain & SSL
```bash
# Add domain
az webapp config hostname add \
  --resource-group trivia-rg \
  --webapp-name your-app-name \
  --hostname yourdomain.com

# Create SSL certificate (managed)
az webapp config ssl create \
  --resource-group trivia-rg \
  --name your-app-name \
  --hostname yourdomain.com

# Bind certificate  
az webapp config ssl bind \
  --resource-group trivia-rg \
  --name your-app-name \
  --certificate-thumbprint [thumbprint] \
  --ssl-type SNI
```

#### Cost: ~$15/month
- App Service B1: ~$13/month
- SSL Certificate: Free (managed)

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV SECRET_KEY="your-production-key"
ENV FLASK_ENV="production"

# Expose port
EXPOSE 3001

# Start application
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:3001", "backend.app:app"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  trivia-app:
    build: .
    ports:
      - "3001:3001"
    environment:
      - SECRET_KEY=your-production-key
      - FLASK_ENV=production
    restart: unless-stopped
    volumes:
      - ./sample_questions.csv:/app/sample_questions.csv

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - trivia-app
    restart: unless-stopped
```

### Build and Deploy
```bash
# Build image
docker build -t trivia-app .

# Test locally
docker run -p 3001:3001 trivia-app

# Deploy to registry
docker tag trivia-app your-registry/trivia-app
docker push your-registry/trivia-app

# Deploy with compose
docker-compose up -d
```

## Cloud Container Services

### AWS ECS
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name trivia-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster trivia-cluster \
  --service-name trivia-service \
  --task-definition trivia-app:1 \
  --desired-count 1
```

### Google Cloud Run
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/trivia-app

# Deploy to Cloud Run
gcloud run deploy trivia-app \
  --image gcr.io/PROJECT-ID/trivia-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3001
```

## Performance Optimization

### Application Optimization
```python
# backend/app.py - Production config
import os

# Production SocketIO configuration
socketio = SocketIO(
    app,
    cors_allowed_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1000000,
    logger=False,
    engineio_logger=False
)

# Enable gzip compression
from flask_compress import Compress
Compress(app)
```

### Nginx Optimization
```nginx
# Add to nginx config
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied expired no-cache no-store private must-revalidate auth;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# Caching static files
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Database Integration (Optional)

### Redis for Session Storage
```python
# requirements.txt
redis
flask-session

# backend/app.py
import redis
from flask_session import Session

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
Session(app)
```

### PostgreSQL for Persistence
```python
# requirements.txt  
psycopg2-binary
flask-sqlalchemy

# backend/app.py
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)
```

## Monitoring & Logging

### Application Logging
```python
# backend/app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/trivia.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Health Monitoring
```python
# Enhanced health endpoint
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'active_games': len(game_state_manager.games),
        'total_connections': len(websocket_manager.connections)
    }
```

### External Monitoring
- **Uptime monitoring:** Pingdom, StatusCake
- **Application monitoring:** New Relic, DataDog
- **Log aggregation:** ELK Stack, Splunk

## Security Hardening

### Production Security Checklist
- [ ] Strong SECRET_KEY (32+ random characters)
- [ ] CORS configured for specific domains
- [ ] HTTPS/SSL enabled with valid certificates  
- [ ] Environment variables for sensitive data
- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] Regular security updates
- [ ] Error messages don't expose sensitive info
- [ ] Rate limiting implemented
- [ ] Input validation and sanitization
- [ ] Security headers configured

### Security Headers
```python
# backend/app.py
@app.after_request  
def after_request(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

## Backup & Recovery

### Data Backup (if using database)
```bash
# PostgreSQL backup
pg_dump trivia_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DB_NAME="trivia_db"
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

### Application Backup
```bash
# Backup application files
tar -czf trivia-app-backup-$(date +%Y%m%d).tar.gz \
  --exclude=venv \
  --exclude=__pycache__ \
  --exclude=.git \
  TriviaApp/
```

## Troubleshooting Deployment

### Common Issues
- **WebSocket connections fail:** Check nginx WebSocket proxy config
- **SSL certificate errors:** Verify certificate paths and permissions
- **Application won't start:** Check logs in systemd journal
- **High memory usage:** Monitor with `htop`, consider adding swap
- **Database connection errors:** Verify connection string and credentials

### Debug Commands
```bash
# Check application logs
sudo journalctl -u trivia-app -f

# Check nginx logs  
sudo tail -f /var/log/nginx/error.log

# Monitor system resources
htop
df -h
free -m

# Test WebSocket connection
wscat -c ws://localhost:3001/socket.io/
```

This deployment guide covers the most common production deployment scenarios. Choose the option that best fits your requirements and budget.
# 🎯 Trivia Competition App

A real-time multiplayer trivia webapp with persistent connections and comprehensive testing. Built with Python Flask/SocketIO backend and vanilla JavaScript frontend.

## ✨ Features

### 🎮 Real-Time Gameplay
- **Multiplayer support** - Multiple teams can compete simultaneously
- **Live updates** - Real-time question display, answer submission, and leaderboard updates
- **Admin controls** - Host can manage game flow, grade answers, and progress through questions
- **Persistent connections** - Users stay connected through page refreshes and browser restarts

### 🔄 Connection Resilience
- **Automatic reconnection** - Seamless reconnection after network interruptions
- **Session persistence** - Game state saved across browser sessions
- **Rejoin functionality** - Teams can rejoin games after closing and reopening browser
- **Connection status** - Visual indicators for connection health

### 📱 Cross-Platform Support
- **Responsive design** - Works on desktop, tablet, and mobile devices
- **Browser compatibility** - Tested on Chrome, Firefox, Safari, and Edge
- **Touch-friendly** - Optimized for mobile touch interactions

## 🏗️ Architecture

### Backend (Python)
- **Flask** web server with **SocketIO** for real-time WebSocket communication
- **Question Management** - CSV-based question loading with round/question organization
- **Game State Management** - Complete game lifecycle, team registration, and scoring
- **WebSocket Events** - 13 client-to-server and 11 server-to-client event types

### Frontend (JavaScript)
- **Vanilla JavaScript** - No framework dependencies, lightweight and fast
- **Real-time UI** - Responsive interface with live updates
- **State Management** - LocalStorage persistence with automatic recovery
- **Connection Manager** - Robust WebSocket handling with automatic reconnection

### Testing Infrastructure
- **79 automated tests** with pytest
- **End-to-end testing** with Selenium WebDriver
- **Integration tests** for multi-component workflows
- **Manual testing framework** for friend/family testing

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch with Demo Game
```bash
python launch_trivia.py
```

This will:
- Start server on `http://localhost:5000`
- Create demo game automatically
- Open browser to the app
- **Game ID:** `demo_game`
- **Admin Password:** `admin123`

### 3. Play the Game!
- **Teams:** Click "Join as Team", enter game ID and team name
- **Admin:** Click "Admin Panel", enter game ID and password
- **Host controls** the game flow, **teams** answer questions in real-time

## 🎮 How to Play

### For Teams
1. **Join Game** - Enter the game ID provided by host and your team name
2. **Wait for Start** - See other teams in the waiting room
3. **Answer Questions** - Type answers when questions appear
4. **View Results** - See if you were correct and updated leaderboard
5. **Continue Playing** - Answer all questions to complete the game

### For Host/Admin
1. **Login** - Use admin panel with game ID and password
2. **Monitor Teams** - See teams as they join in real-time
3. **Start Game** - Begin the trivia session
4. **Control Questions** - Start each question, close for answers, grade responses
5. **Manage Flow** - Progress through all questions to finish the game

## 📋 CSV Question Format

Questions are loaded from CSV files with this format:

```csv
round_num,question_num,question,answer
1,1,What is the capital of France?,Paris
1,2,What is 2+2?,4
1,3,Who painted the Mona Lisa?,Leonardo da Vinci
2,1,What is the largest planet?,Jupiter
2,2,How many continents are there?,7
2,3,What year did World War II end?,1945
```

### CSV Requirements
- **Headers:** `round_num`, `question_num`, `question`, `answer`
- **Round organization** - Questions grouped by rounds for better game flow
- **Sequential numbering** - Questions numbered within each round
- **Clear answers** - Unambiguous correct answers for easy grading

## 🧪 Running Tests

### Automated Test Suite
```bash
# Run all backend tests (79 tests)
python -m pytest tests/ -v --ignore=tests/test_e2e.py

# Run with coverage report
python -m pytest tests/ --cov=backend --cov-report=html --ignore=tests/test_e2e.py

# Run specific test categories
python -m pytest tests/test_question_manager.py -v    # Question management
python -m pytest tests/test_game_state.py -v         # Game logic
python -m pytest tests/test_websocket_manager.py -v  # WebSocket communication
python -m pytest tests/test_integration.py -v        # Integration tests
```

### End-to-End Tests (Requires ChromeDriver)
```bash
# Install selenium and ChromeDriver first
pip install selenium
# Download ChromeDriver from https://chromedriver.chromium.org/

# Run E2E tests
python -m pytest tests/test_e2e.py -v
```

### Test Coverage
- **Unit Tests:** All backend components individually tested
- **Integration Tests:** Component interaction and full workflows
- **WebSocket Tests:** Real-time communication and state synchronization
- **E2E Tests:** Complete user workflows with browser automation

## 👥 Testing with Friends

### Network Setup for Friend Testing

1. **Start the Server**
   ```bash
   python launch_trivia.py
   ```

2. **Find Your IP Address**
   ```bash
   # Windows
   ipconfig | findstr "IPv4"
   
   # Mac/Linux  
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

3. **Share Access Details**
   - **URL:** `http://[YOUR_IP_ADDRESS]:5000`
   - **Game ID:** `demo_game`
   - **Admin Password:** `admin123`

### Friend Testing Scenarios

Follow the comprehensive **[TESTING_PLAN.md](TESTING_PLAN.md)** which includes:

#### 🎯 **Scenario 1: Basic Game Flow** (2-4 people, 15 minutes)
- Complete gameplay with real users
- Team registration and admin controls
- Full question/answer/grading cycle
- **Objective:** Verify core functionality works smoothly

#### 🔄 **Scenario 2: Connection Resilience** (3-4 people, 20 minutes)
- Page refresh during gameplay
- Browser close/reopen testing
- Network interruption recovery
- **Objective:** Test persistent connection features

#### ⚠️ **Scenario 3: Edge Cases** (2-3 people, 15 minutes)
- Invalid inputs and error handling
- Timing conflicts and rapid actions
- Cross-browser compatibility
- **Objective:** Validate error handling and robustness

#### 📈 **Scenario 4: Scale Testing** (5-10 people, 25 minutes)
- Large group simultaneous play
- Concurrent answer submission
- Performance under load
- **Objective:** Test scalability and performance

#### 📱 **Scenario 5: Cross-Platform** (3-5 people, 20 minutes)
- Mix of desktop, tablet, and mobile devices
- Different browsers and operating systems
- Touch interaction testing
- **Objective:** Verify universal device compatibility

### Quick Friend Test Setup
```bash
# 1. Host starts server
python launch_trivia.py

# 2. Share these details with friends:
#    URL: http://[YOUR_IP]:5000
#    Game ID: demo_game
#    Admin Password: admin123

# 3. One person becomes admin, others join as teams
# 4. Play through a few questions together!
# 5. Test reconnection by refreshing browsers
```

## 🛠️ Development

### Project Structure
```
TriviaApp/
├── backend/                 # Python Flask backend
│   ├── app.py              # Main Flask application
│   ├── question_manager.py # CSV question loading and management
│   ├── game_state.py       # Game logic, teams, and scoring
│   └── websocket_manager.py# Real-time WebSocket communication
├── frontend/               # JavaScript frontend
│   ├── index.html          # Main application page
│   ├── css/styles.css      # Modern responsive styling
│   └── js/
│       ├── game-client.js  # WebSocket client and state management
│       └── app.js          # UI logic and event handling
├── tests/                  # Comprehensive test suite
│   ├── test_question_manager.py
│   ├── test_game_state.py
│   ├── test_websocket_manager.py
│   ├── test_integration.py
│   ├── test_websocket_integration.py
│   └── test_e2e.py         # Selenium end-to-end tests
├── sample_questions.csv    # Demo question set
├── requirements.txt        # Python dependencies
├── launch_trivia.py       # Easy launch script
├── RUNNING.md             # Detailed setup instructions
├── TESTING_PLAN.md        # Comprehensive testing guide
└── BUILD_PLAN.md          # Development roadmap
```

### Key Technologies
- **Backend:** Python 3.9+, Flask 2.3, Flask-SocketIO 5.3, Pandas 2.1
- **Frontend:** Vanilla JavaScript ES6+, Socket.IO 4.7, Modern CSS3
- **Testing:** Pytest 7.4, Selenium 4.15, Coverage reporting
- **Data:** CSV-based question storage with pandas parsing

## 📊 Game Workflow

### Complete Game Flow
1. **Setup:** Admin creates game, loads questions from CSV
2. **Registration:** Teams join using game ID, see waiting room
3. **Game Start:** Admin initiates game, teams move to game screen
4. **Question Loop:**
   - Admin starts question → Question displays to all teams
   - Teams submit answers → Admin sees all submissions
   - Admin closes question → Teams see "awaiting results"  
   - Admin grades each answer → Teams see results and updated leaderboard
   - Admin starts next question → Repeat until all questions complete
5. **Game End:** Final leaderboard shown, option to start new game

### Real-Time Events
- **Team joins/leaves** - Live updates to team lists
- **Game state changes** - Status updates across all clients  
- **Question progression** - Synchronized question display
- **Answer submission** - Real-time answer collection
- **Grading results** - Instant score updates and leaderboard refresh
- **Connection status** - Live connection health monitoring

## 🔧 API Reference

### REST API Endpoints
- `GET /` - Serve main application page
- `GET /health` - Health check endpoint  
- `POST /api/create-game` - Create new game with CSV file
- `GET /api/games/<game_id>` - Get game information

### WebSocket Events

#### Client → Server Events
- `join_game` - Team joins a game
- `admin_login` - Admin authentication  
- `start_game` - Admin starts the game
- `start_question` - Admin starts a question
- `submit_answer` - Team submits an answer
- `close_question` - Admin closes current question
- `grade_answer` - Admin grades an answer
- `next_question` - Admin moves to next question
- `get_leaderboard` - Request current leaderboard

#### Server → Client Events  
- `team_joined` - Team successfully joined
- `team_list_update` - Updated team list
- `game_started` - Game has started
- `question_started` - New question started
- `answer_submitted` - Answer was submitted
- `question_closed` - Question was closed
- `answer_graded` - Answer was graded
- `leaderboard_update` - Updated leaderboard
- `game_finished` - Game completed
- `error` - Error occurred
- `success` - Operation successful

## 🚀 Production Deployment

### Environment Setup
```bash
# Production environment variables
export SECRET_KEY="your-production-secret-key"
export FLASK_ENV="production"

# Start production server
python -m backend.app
```

### Network Configuration
- **Firewall:** Allow port 5000 (or your chosen port)
- **CORS:** Configured for development, adjust for production domains
- **HTTPS:** Consider SSL/TLS for production deployment
- **Database:** Currently uses in-memory storage, consider persistent storage for production

## ☁️ Cloud Deployment

### AWS Deployment (EC2 + Application Load Balancer)

#### Prerequisites
- AWS Account with appropriate permissions
- Domain registered and managed through Route 53 (or external DNS)
- SSL certificate via AWS Certificate Manager

#### Step 1: Launch EC2 Instance
```bash
# Launch Ubuntu 22.04 LTS instance
# Instance type: t3.medium (or larger for high traffic)
# Security group: Allow HTTP (80), HTTPS (443), SSH (22)

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### Step 2: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx git -y

# Clone your repository
git clone https://github.com/your-username/TriviaApp.git
cd TriviaApp

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### Step 3: Configure Gunicorn Service
```bash
# Create service file
sudo nano /etc/systemd/system/trivia-app.service
```

Add the following content:
```ini
[Unit]
Description=Trivia App Gunicorn
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/TriviaApp
Environment="PATH=/home/ubuntu/TriviaApp/venv/bin"
Environment="SECRET_KEY=your-production-secret-key-here"
Environment="FLASK_ENV=production"
ExecStart=/home/ubuntu/TriviaApp/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 backend.app:app
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
# Create nginx configuration
sudo nano /etc/nginx/sites-available/trivia-app
```

Add the following content:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (replace with your certificate paths)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # WebSocket upgrade headers
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
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
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (if serving directly)
    location /static {
        alias /home/ubuntu/TriviaApp/frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site and restart nginx
sudo ln -s /etc/nginx/sites-available/trivia-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5: Setup SSL with Let's Encrypt (Alternative to ACM)
```bash
# Install certbot
sudo apt install snapd
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Get certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

#### Step 6: Configure Route 53
```bash
# In AWS Console -> Route 53:
# Create A record: your-domain.com -> EC2 Public IP
# Create CNAME: www.your-domain.com -> your-domain.com
```

### Azure Deployment (App Service)

#### Prerequisites
- Azure Account with active subscription
- Azure CLI installed locally
- Domain registered

#### Step 1: Prepare Application
```bash
# Create requirements.txt with gunicorn
echo "gunicorn" >> requirements.txt

# Create startup.sh
cat > startup.sh << 'EOF'
#!/bin/bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 backend.app:app
EOF

chmod +x startup.sh
```

#### Step 2: Deploy to App Service
```bash
# Login to Azure
az login

# Create resource group
az group create --name trivia-app-rg --location "East US"

# Create App Service plan
az appservice plan create \
  --name trivia-app-plan \
  --resource-group trivia-app-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group trivia-app-rg \
  --plan trivia-app-plan \
  --name your-unique-app-name \
  --runtime "PYTHON|3.9" \
  --startup-file startup.sh

# Configure app settings
az webapp config appsettings set \
  --resource-group trivia-app-rg \
  --name your-unique-app-name \
  --settings SECRET_KEY="your-production-secret-key" FLASK_ENV="production"

# Enable WebSocket support
az webapp config set \
  --resource-group trivia-app-rg \
  --name your-unique-app-name \
  --web-sockets-enabled true

# Deploy code
az webapp deployment source config-zip \
  --resource-group trivia-app-rg \
  --name your-unique-app-name \
  --src trivia-app.zip
```

#### Step 3: Configure Custom Domain
```bash
# Add custom domain
az webapp config hostname add \
  --resource-group trivia-app-rg \
  --webapp-name your-unique-app-name \
  --hostname your-domain.com

# Create managed SSL certificate
az webapp config ssl create \
  --resource-group trivia-app-rg \
  --name your-unique-app-name \
  --hostname your-domain.com

# Bind SSL certificate
az webapp config ssl bind \
  --resource-group trivia-app-rg \
  --name your-unique-app-name \
  --certificate-thumbprint [certificate-thumbprint] \
  --ssl-type SNI
```

#### Step 4: Configure DNS
```bash
# In your domain registrar or Azure DNS:
# Create CNAME record: your-domain.com -> your-unique-app-name.azurewebsites.net
# Create CNAME record: www.your-domain.com -> your-unique-app-name.azurewebsites.net
```

### Docker Deployment (Any Cloud Provider)

#### Step 1: Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV SECRET_KEY="your-production-secret-key"
ENV FLASK_ENV="production"

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "backend.app:app"]
```

#### Step 2: Build and Deploy
```bash
# Build image
docker build -t trivia-app .

# Run locally to test
docker run -p 5000:5000 trivia-app

# Deploy to Docker Hub
docker tag trivia-app your-dockerhub-username/trivia-app
docker push your-dockerhub-username/trivia-app

# Deploy to cloud container service
# (AWS ECS, Azure Container Instances, Google Cloud Run, etc.)
```

### Performance Optimization for Production

#### Application Optimization
```python
# Update backend/app.py for production
import os
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')

# Production SocketIO configuration
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",  # Restrict to your domain in production
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1000000
)
```

#### Database Persistence (Optional)
```bash
# For persistent storage, consider adding Redis or PostgreSQL:
# Redis for session storage
pip install redis flask-session

# PostgreSQL for game data
pip install psycopg2-binary flask-sqlalchemy
```

### Monitoring and Logging

#### AWS CloudWatch Integration
```bash
# Install CloudWatch agent
sudo wget https://s3.amazonaws.com/amazoncloudwatch-agent/linux/amd64/latest/AmazonCloudWatchAgent.zip
sudo unzip AmazonCloudWatchAgent.zip
sudo ./install.sh

# Configure log monitoring for your application logs
```

#### Health Check Endpoint
The application already includes `/health` endpoint for monitoring:
```python
# Monitor this endpoint with:
# - AWS Application Load Balancer health checks
# - Azure App Service health checks
# - External monitoring services (Pingdom, DataDog, etc.)
```

### Security Considerations

#### Production Security Checklist
- [ ] Use strong SECRET_KEY (32+ random characters)
- [ ] Configure CORS for your specific domain only
- [ ] Enable HTTPS/SSL certificates
- [ ] Use environment variables for sensitive data
- [ ] Configure firewall rules (allow only 80, 443, 22)
- [ ] Regular security updates (`sudo apt update && sudo apt upgrade`)
- [ ] Monitor logs for suspicious activity
- [ ] Consider WAF (Web Application Firewall)
- [ ] Backup strategy for game data/configurations

#### Environment Variables Template
```bash
# Create .env file for production
SECRET_KEY="your-32-character-random-secret-key-here"
FLASK_ENV="production"
DOMAIN_NAME="your-domain.com"
CORS_ORIGINS="https://your-domain.com,https://www.your-domain.com"
```

### Cost Optimization

#### AWS Cost Estimates (Monthly)
- **EC2 t3.medium:** ~$30/month
- **Application Load Balancer:** ~$20/month
- **Route 53 Hosted Zone:** ~$0.50/month
- **SSL Certificate (ACM):** Free
- **Total:** ~$50-60/month

#### Azure Cost Estimates (Monthly)
- **App Service B1:** ~$13/month
- **Custom Domain + SSL:** Free (managed certificate)
- **Total:** ~$15/month

Choose based on your expected traffic and feature requirements.

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run the test suite: `python -m pytest tests/ -v`
4. Make your changes with tests
5. Ensure all tests pass
6. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

**Connection Problems:**
- Check firewall settings and port 5000 access
- Verify server IP address is correct
- Test health endpoint: `http://[IP]:5000/health`

**Game Not Starting:**
- Ensure CSV file exists and has correct format
- Check admin password is correct
- Verify at least one team has joined

**WebSocket Issues:**
- Check browser console for errors
- Try refreshing the page
- Verify network connectivity

**Performance Issues:**
- Monitor server resource usage
- Check network bandwidth with many users
- Consider reducing concurrent users if needed

### Getting Help
- Check [TESTING_PLAN.md](TESTING_PLAN.md) for detailed troubleshooting
- Review server logs for error messages
- Test with [RUNNING.md](RUNNING.md) basic setup instructions

---

**Ready to host your own trivia night? 🎉**

```bash
pip install -r requirements.txt
python launch_trivia.py
# Share the URL with friends and start playing!
```
# 📋 Setup Guide

## Installation

### Prerequisites
- Python 3.9 or higher
- Git (optional, for cloning)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch with Demo Game
```bash
python launch_trivia.py
```

This will:
- Start server on `http://localhost:3001`
- Create demo game automatically
- Open browser to the app
- **Game ID:** `demo_game`
- **Admin Password:** `admin123`

## Manual Setup

### 1. Start Backend Server
```bash
python -m backend.app
```

### 2. Create Custom Game
```bash
# Using the launch script with custom CSV
python launch_trivia.py --csv your_questions.csv --game-id my_game --password my_password

# Or use the REST API
curl -X POST http://localhost:3001/api/create-game \
  -F "csv_file=@your_questions.csv" \
  -F "game_id=my_game" \
  -F "admin_password=my_password"
```

### 3. Access the Application
- **Main App:** `http://localhost:3001`
- **Admin Panel:** `http://localhost:3001/admin`
- **Health Check:** `http://localhost:3001/health`

## CSV Question Format

### Required Format
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
- **Headers:** Must include `round_num`, `question_num`, `question`, `answer`
- **Round Organization:** Questions grouped by rounds for better game flow
- **Sequential Numbering:** Questions numbered within each round (1, 2, 3, etc.)
- **Clear Answers:** Unambiguous correct answers for automatic grading

### Example CSV Files
See `sample_questions.csv` for a complete example with math and geography questions.

## Environment Configuration

### Development Settings
```bash
# Optional environment variables
export SECRET_KEY="your-development-secret-key"
export FLASK_ENV="development"
export FLASK_DEBUG=1
```

### Production Settings
```bash
export SECRET_KEY="your-32-character-production-key"
export FLASK_ENV="production"
export FLASK_DEBUG=0
```

## Network Setup for Multiplayer

### 1. Find Your IP Address
```bash
# Windows
ipconfig | findstr "IPv4"

# Mac/Linux  
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### 2. Share Access Details
- **URL:** `http://[YOUR_IP_ADDRESS]:3001`
- **Game ID:** `demo_game` (or your custom game ID)
- **Admin Password:** `admin123` (or your custom password)

### 3. Firewall Configuration
Ensure port 3001 is open for incoming connections:

```bash
# Windows (run as administrator)
netsh advfirewall firewall add rule name="Trivia App" dir=in action=allow protocol=TCP localport=3001

# Mac
sudo ufw allow 3001

# Linux
sudo iptables -A INPUT -p tcp --dport 3001 -j ACCEPT
```

## Troubleshooting

### Common Installation Issues

**Python Version Error:**
```bash
# Check Python version
python --version
# Should be 3.9+, if not install newer Python
```

**Port Already in Use:**
```bash
# Kill process using port 3001
# Windows
netstat -ano | findstr :3001
taskkill /PID [PID_NUMBER] /F

# Mac/Linux  
lsof -ti:3001 | xargs kill
```

**Module Import Errors:**
```bash
# Ensure you're in the TriviaApp directory
cd TriviaApp

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Connection Issues

**Can't Access from Other Devices:**
1. Check firewall settings
2. Verify server is running on 0.0.0.0 (all interfaces)
3. Test health endpoint: `http://[YOUR_IP]:3001/health`

**WebSocket Connection Failed:**
1. Clear browser cache and cookies
2. Try different browser
3. Check browser console for error messages

### Game Issues

**CSV File Not Loading:**
1. Verify CSV file exists and has correct headers
2. Check for special characters or encoding issues
3. Test with the included `sample_questions.csv`

**Admin Can't Login:**
1. Verify game was created successfully
2. Check admin password matches exactly
3. Look for error messages in browser console

For more troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
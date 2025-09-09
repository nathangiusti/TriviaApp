# 🎯 Trivia Competition App

A real-time multiplayer trivia webapp with persistent connections and comprehensive testing. Built with Python Flask/SocketIO backend and vanilla JavaScript frontend.

## ✨ Key Features

- **🎮 Real-Time Multiplayer** - Multiple teams compete with live updates and persistent connections
- **🔄 Connection Resilience** - Automatic reconnection and session persistence
- **📱 Cross-Platform** - Works on desktop, tablet, and mobile devices
- **🧪 Comprehensive Testing** - 89+ automated tests with E2E coverage

## 🚀 Quick Start

### 1. Install and Run
```bash
pip install -r requirements.txt
python launch_trivia.py
```

### 2. Play the Game
- **Server:** `http://localhost:3001`
- **Game ID:** `demo_game` 
- **Admin Password:** `admin123`

### 3. How to Play
- **Teams:** Enter game ID and team name to join
- **Admin:** Navigate to `/admin`, login, and control the game flow
- **Host:** Start game, manage questions, grade answers in real-time

## 📋 CSV Question Format

```csv
round_num,question_num,question,answer
1,1,What is the capital of France?,Paris
1,2,What is 2+2?,4
2,1,What is the largest planet?,Jupiter
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v --ignore=tests/test_e2e.py

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# E2E tests (requires ChromeDriver)
python -m pytest tests/test_e2e.py -v
```

## 👥 Testing with Friends

1. **Start Server:** `python launch_trivia.py`
2. **Get IP:** `ipconfig | findstr "IPv4"` (Windows) 
3. **Share:** `http://[YOUR_IP]:3001` with Game ID `demo_game`

See **[TESTING_PLAN.md](docs/TESTING_PLAN.md)** for comprehensive multiplayer testing scenarios.

## 📚 Documentation

### Setup & Usage
- **[SETUP.md](docs/SETUP.md)** - Detailed installation and configuration
- **[GAMEPLAY.md](docs/GAMEPLAY.md)** - How to play guide for teams and admins
- **[TESTING_PLAN.md](docs/TESTING_PLAN.md)** - Friend testing scenarios

### Development  
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture and design
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - REST endpoints and WebSocket events
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development workflow and project structure

### Deployment
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guides (AWS, Azure, Docker)
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🏗️ Architecture Overview

```
Backend (Python)          Frontend (JavaScript)        Testing
├── Flask + SocketIO      ├── Separated Admin/Player    ├── 89+ automated tests
├── Real-time WebSocket   ├── Context-Aware UI          ├── Unit + integration  
├── CSV question loading  ├── Vanilla JS + Socket.IO    ├── E2E with Selenium
└── Game state management ├── Responsive Design         └── Cross-platform testing
                          └── Auto-reconnection
```

### Frontend Architecture Separation
- **`admin-app.js`** - Admin-specific logic (game control, question management)
- **`player-app.js`** - Player-specific logic (joining games, answering questions)  
- **`game-client.js`** - Shared WebSocket communication layer
- **Context isolation** prevents admin/player UI conflicts and null reference errors

## 🛠️ Technology Stack

- **Backend:** Python 3.9+, Flask 2.3, Flask-SocketIO 5.3
- **Frontend:** Vanilla JavaScript ES6+, Socket.IO 4.7, Modern CSS3  
- **Testing:** Pytest 7.4, Selenium 4.15, 89+ test coverage
- **Data:** CSV-based questions with pandas parsing

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch  
3. Run tests: `python -m pytest tests/ -v`
4. Make changes with tests
5. Submit a pull request

---

**Ready to host your own trivia night? 🎉**

```bash
pip install -r requirements.txt
python launch_trivia.py
# Share http://[YOUR_IP]:3001 with friends!
```
# 🛠️ Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.9+
- Git
- Code editor (VS Code recommended)
- Chrome/Firefox for testing

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd TriviaApp

# Create virtual environment  
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest-cov black flake8 mypy
```

### Development Server
```bash
# Start development server with auto-reload
python -m backend.app

# Or use the launcher for full setup
python launch_trivia.py
```

## Project Structure

```
TriviaApp/
├── backend/                    # Python backend
│   ├── __init__.py
│   ├── app.py                 # Flask application & routes
│   ├── question_manager.py    # CSV question management
│   ├── game_state.py         # Game logic & state
│   └── websocket_manager.py  # WebSocket communication
├── frontend/                  # JavaScript frontend  
│   ├── index.html            # Main application
│   ├── admin.html            # Admin panel
│   ├── css/
│   │   └── styles.css        # Responsive styling
│   └── js/
│       ├── game-client.js    # WebSocket client
│       └── app.js            # UI logic
├── tests/                    # Test suite
│   ├── test_*.py            # Unit tests
│   ├── test_integration.py  # Integration tests
│   ├── test_e2e.py          # End-to-end tests
│   └── test_helpers.py      # Test utilities
├── docs/                     # Documentation
│   ├── SETUP.md
│   ├── GAMEPLAY.md
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── sample_questions.csv      # Demo questions
├── requirements.txt          # Python dependencies
├── launch_trivia.py         # Launch script
└── README.md                # Project overview
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes with tests
# Run tests frequently
python -m pytest tests/ -v

# Commit changes
git add .
git commit -m "Add new feature with tests"
```

### 2. Code Quality
```bash
# Format code
black backend/ tests/

# Lint code  
flake8 backend/ tests/

# Type checking
mypy backend/

# Run all quality checks
./scripts/quality-check.sh  # If you create this script
```

### 3. Testing
```bash
# Run unit tests
python -m pytest tests/test_*.py -v

# Run integration tests
python -m pytest tests/test_integration.py -v  

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Run E2E tests (requires ChromeDriver)
python -m pytest tests/test_e2e.py -v
```

## Testing Framework

### Test Categories
1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Component interaction testing  
3. **WebSocket Tests** - Real-time communication testing
4. **Frontend Tests** - UI component and workflow testing
5. **End-to-End Tests** - Complete user workflow testing

### Writing Tests

#### Unit Test Example
```python
# tests/test_question_manager.py
import pytest
from backend.question_manager import QuestionManager

class TestQuestionManager:
    def setup_method(self):
        self.qm = QuestionManager()
    
    def test_load_valid_csv(self):
        # Create test CSV
        csv_content = "round_num,question_num,question,answer\n1,1,Test?,Answer"
        csv_file = self.create_temp_csv(csv_content)
        
        # Test loading
        self.qm.load_questions_from_csv("test_game", csv_file)
        questions = self.qm.get_questions_for_game("test_game")
        
        assert len(questions) == 1
        assert questions[0].question == "Test?"
```

#### Integration Test Example  
```python
# tests/test_integration.py
def test_full_game_workflow(self):
    # Setup components
    qm = QuestionManager() 
    gsm = GameStateManager(qm)
    wsm = WebSocketManager(gsm)
    
    # Test complete workflow
    # 1. Create game
    # 2. Teams join
    # 3. Start game  
    # 4. Play through questions
    # 5. Verify final state
```

#### Frontend Test Example
```python
# tests/test_frontend_workflow.py
def test_team_join_workflow(self):
    driver = webdriver.Chrome()
    try:
        # Navigate to app
        driver.get("http://localhost:3001")
        
        # Test join workflow
        game_id_input = driver.find_element(By.ID, "game-id")
        game_id_input.send_keys("test_game")
        
        # Verify UI transitions
        assert driver.find_element(By.ID, "waiting-room")
    finally:
        driver.quit()
```

### Test Utilities
```python
# tests/test_helpers.py
def create_temp_csv(content):
    """Create temporary CSV file for testing"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        return f.name

def cleanup_temp_file(file_path):
    """Clean up temporary test files"""
    import os
    if os.path.exists(file_path):
        os.unlink(file_path)
```

## Code Style Guidelines

### Python Code Style
- **PEP 8** compliance
- **Black** formatting
- **Type hints** for function signatures
- **Docstrings** for classes and public methods

```python
def create_game(self, game_id: str, csv_file_path: str, admin_password: str) -> GameSession:
    """Create a new game session with questions from CSV file.
    
    Args:
        game_id: Unique identifier for the game
        csv_file_path: Path to CSV file containing questions  
        admin_password: Password for admin authentication
        
    Returns:
        GameSession object for the created game
        
    Raises:
        ValueError: If game_id already exists or CSV is invalid
    """
```

### JavaScript Code Style
- **ES6+** features
- **Camel case** naming
- **JSDoc** comments for functions
- **Consistent** indentation (2 spaces)

```javascript
/**
 * Connect to WebSocket server with auto-retry
 * @param {string} serverUrl - WebSocket server URL
 * @returns {Promise<void>} Connection promise
 */
async connect(serverUrl = null) {
    // Implementation
}
```

### CSS Code Style
- **Mobile-first** responsive design
- **BEM** naming convention
- **CSS Grid/Flexbox** for layout
- **CSS custom properties** for theming

```css
/* Component styles */
.answer-item {
    background: var(--bg-light);
    border-radius: 8px;
    padding: 15px;
}

.answer-item__header {
    display: flex;
    justify-content: space-between;
}

.answer-item--correct {
    border-left: 4px solid var(--success-color);
}
```

## Debugging

### Backend Debugging
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use Flask debug mode
app.run(debug=True, port=3001)

# Add breakpoints
import pdb; pdb.set_trace()
```

### Frontend Debugging  
```javascript
// Browser console debugging
console.log('Game state:', gameState);
console.table(leaderboard);

// WebSocket message debugging
socket.on('*', (event, data) => {
    console.log('WebSocket event:', event, data);
});

// Network debugging in browser DevTools
// - Network tab for HTTP requests
// - WebSocket frames in Network tab
// - Console for JavaScript errors
```

### Test Debugging
```bash
# Run single test with output
python -m pytest tests/test_specific.py::test_function -v -s

# Debug test failures
python -m pytest tests/ -v --tb=short

# Run tests with debugger on failure
python -m pytest tests/ --pdb
```

## Performance Optimization

### Backend Performance
```python
# Profile code execution
import cProfile
cProfile.run('your_function()')

# Memory usage monitoring
import tracemalloc
tracemalloc.start()
# ... code ...
current, peak = tracemalloc.get_traced_memory()
```

### Frontend Performance
```javascript
// Measure performance
console.time('operation');
// ... code ...
console.timeEnd('operation');

// Monitor WebSocket performance
const startTime = performance.now();
socket.emit('event', data);
socket.on('response', () => {
    const duration = performance.now() - startTime;
    console.log('Round-trip time:', duration);
});
```

## Common Development Tasks

### Adding New WebSocket Event
1. **Define event type** in `websocket_manager.py`
2. **Add handler method** in WebSocketManager
3. **Register event** in Flask app
4. **Add client-side handler** in `game-client.js`  
5. **Write tests** for the new event

### Adding New UI Component
1. **Add HTML structure** to appropriate page
2. **Add CSS styles** in `styles.css`
3. **Add JavaScript logic** in `app.js`
4. **Write component tests**

### Adding New Game Feature
1. **Update data models** in `game_state.py`
2. **Add business logic** methods
3. **Update WebSocket events** if needed
4. **Update frontend** to handle new feature
5. **Add comprehensive tests**

## Git Workflow

### Branching Strategy
```bash
# Main branches
main          # Production ready code
develop       # Development integration

# Feature branches  
feature/xyz   # New features
bugfix/xyz    # Bug fixes
hotfix/xyz    # Emergency fixes
```

### Commit Messages
```
feat: add automatic answer grading
fix: resolve WebSocket connection issue  
test: add integration tests for game flow
docs: update API documentation
refactor: simplify question manager logic
```

### Pull Request Process
1. **Create feature branch** from main
2. **Implement changes** with tests
3. **Run test suite** and ensure all pass
4. **Update documentation** if needed
5. **Submit pull request** with description
6. **Code review** and feedback
7. **Merge to main** after approval

## Deployment Preparation

### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Code coverage > 90%
- [ ] No console errors in browser
- [ ] Performance tests completed
- [ ] Security review completed
- [ ] Documentation updated

### Environment Configuration
```bash
# Development
export FLASK_ENV=development
export FLASK_DEBUG=1

# Production  
export FLASK_ENV=production
export SECRET_KEY="production-secret-key"
```

### Build Process
```bash
# Run quality checks
python -m pytest tests/ --cov=backend
black --check backend/
flake8 backend/

# Build for production
# (Currently no build step needed for vanilla JS)

# Package for deployment  
tar -czf trivia-app.tar.gz backend/ frontend/ requirements.txt
```

This development guide provides the foundation for contributing to and maintaining the Trivia App codebase.
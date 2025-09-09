# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Development
```bash
# Install dependencies
pip install -r requirements.txt

# Launch app with demo game (port 3001)
python launch_trivia.py

# Start backend only
python -m backend.app

# Alternative frontend server (port 8000)
python serve_frontend.py
```

### Testing Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Run core tests (excluding frontend/E2E)
python -m pytest tests/ -v --ignore=tests/test_frontend_component_visibility.py --ignore=tests/test_frontend_workflow.py --ignore=tests/test_e2e.py

# Run specific test categories
python -m pytest tests/test_core_game_logic.py -v         # Game logic & data models
python -m pytest tests/test_websocket_system.py -v       # WebSocket communication
python -m pytest tests/test_complete_workflows.py -v     # End-to-end workflows
python -m pytest tests/test_routes.py -v                 # Flask routes

# Run single test
python -m pytest tests/test_e2e.py::TestE2ETrivia::test_admin_login_workflow -v -s

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

### E2E Testing (requires ChromeDriver)
```bash
# Admin login tests
python -m pytest tests/test_e2e.py::TestE2ETrivia::test_admin_login_workflow -v -s
python -m pytest tests/test_e2e.py::TestE2ETrivia::test_admin_login_invalid_credentials -v -s

# Player workflow tests  
python -m pytest tests/test_e2e.py::TestE2ETrivia::test_player_join_success_workflow -v -s
```

## Architecture Overview

### Real-Time WebSocket Architecture
The app uses Flask-SocketIO for bidirectional real-time communication:

- **Backend**: `WebSocketManager` handles 13 client→server and 11 server→client event types
- **Frontend**: `GameClient` manages connection state, reconnection, and UI updates
- **State Sync**: All game state changes broadcast to relevant clients immediately
- **Connection Resilience**: Automatic reconnection with session persistence via localStorage

### Progressive UI Disclosure Pattern
Critical UI pattern: **Only show relevant components at each stage**
- **Initial Load**: Only join game form visible (`display: none !important` on other components)
- **After Join**: Automatic transition to waiting room
- **Game Start**: Automatic transition to game screen
- **Game End**: Automatic transition to final results

JavaScript functions like `showWaitingRoom()`, `showGameScreen()` use `element.style.display = 'block'` to override CSS `!important` hidden styles.

### Game State Flow
```
Game Creation → Team Registration → Game Start → Question Loop → Game End
     ↓               ↓                ↓           ↓            ↓
[Admin creates] → [Teams join] → [Admin starts] → [Q&A cycle] → [Final scores]
```

Each stage has specific WebSocket events and UI transitions that are automatically synchronized across all connected clients.

### Core Components

#### Backend (`backend/`)
- **`app.py`**: Flask app with SocketIO handlers (uses `_handle_socketio_event()` helper to reduce duplication)
- **`websocket_manager.py`**: Real-time communication logic, client connection management
- **`game_state.py`**: Game logic, team management, scoring, question progression
- **`question_manager.py`**: CSV question loading and retrieval

#### Frontend (`frontend/`)
- **`js/game-client.js`**: Shared WebSocket client, connection management, state persistence
- **`js/admin-app.js`**: Admin-specific UI logic, panel management, game controls (used by admin.html)
- **`js/player-app.js`**: Player-specific UI logic, game joining, question answering (used by index.html)
- **CSS**: Uses `!important` for initial hiding, JavaScript overrides for display

**Architecture Separation**: Frontend logic is cleanly separated by context:
- **Admin Context** (`admin.html` + `admin-app.js`): Admin login, game management, question control, answer grading
- **Player Context** (`index.html` + `player-app.js`): Team joining, question answering, leaderboard viewing
- **Shared Logic** (`game-client.js`): WebSocket communication, connection management, state persistence

#### Testing (`tests/`) - Organized by Functionality

**Core Test Categories:**
- **`test_core_game_logic.py`**: Unit tests for game data models (Team, Answer, GameSession, Question, QuestionManager, GameStateManager)
- **`test_websocket_system.py`**: WebSocket communication, message handling, client connections
- **`test_complete_workflows.py`**: End-to-end integration tests, complete game workflows, multi-game isolation
- **`test_routes.py`**: Flask route testing, API endpoints, HTTP responses

**Specialized Tests:**
- **`test_e2e.py`**: Browser automation tests with Selenium (requires ChromeDriver)
- **`test_frontend_component_visibility.py`**: UI element visibility and progressive disclosure
- **`test_frontend_workflow.py`**: Frontend JavaScript workflow testing

**Test Organization:**
- **74 consolidated tests** covering all core functionality (reduced from 16 scattered test files)
- **Eliminated duplicate tests** while maintaining comprehensive coverage
- **Clear separation** between unit, integration, and end-to-end testing
- **Helper utilities** in `test_helpers.py` for consistent test setup and reusable CSV content
- **Improved maintainability** with logical grouping by functionality rather than scattered files

## Architecture Benefits

### Clean Context Separation
- **No Context Confusion**: Pages always know their role (admin vs player)
- **No Null Reference Errors**: Admin functions only exist on admin pages, player functions only on player pages  
- **Better Security**: No accidental admin functionality exposure on player pages
- **Easier Debugging**: Issues are isolated to specific contexts
- **Maintainable Code**: Single responsibility principle applied to frontend architecture

### File Organization
```
frontend/
├── index.html          # Player interface
├── admin.html          # Admin interface  
├── js/
│   ├── game-client.js  # Shared WebSocket logic
│   ├── player-app.js   # Player-specific logic
│   └── admin-app.js    # Admin-specific logic
└── css/styles.css      # Shared styling
```

## Key Implementation Details

### WebSocket Event Handling
All SocketIO handlers use a generic `_handle_socketio_event()` function to eliminate code duplication. The function handles:
- Client validation
- Message processing via `WebSocketManager`
- Response broadcasting with target client support

### Admin Login Enhancement
Admin login sends two responses:
1. Success confirmation
2. Current team list update

This ensures admins see existing teams immediately upon login. Tests expect both responses.

### CSS Display Pattern & Context Management
Components use `style="display: none !important;"` for initial hiding. JavaScript functions override with `element.style.display = 'block'` for proper progressive disclosure.

**Context-Aware Functions**: 
- **Admin functions** (`admin-app.js`) only access admin DOM elements, with proper error handling if elements don't exist
- **Player functions** (`player-app.js`) only access player DOM elements  
- **Shared functions** (`game-client.js`) handle WebSocket communication and state management for both contexts

### Connection Management
- **Socket Mapping**: `socket_to_client` and `client_to_socket` dictionaries
- **Game Connections**: `game_connections[game_id]` tracks clients per game
- **Cleanup**: Automatic cleanup on disconnect

### Question Management
Questions loaded from CSV with structure:
```csv
round_num,question_num,question,answer
1,1,What is 2+2?,4
```

### Game Configuration
- **Default Port**: 3001 (changed from 5000 to avoid macOS AirPlay conflicts)
- **Demo Game**: `game_id: "demo_game"`, `password: "admin123"`
- **Questions**: `sample_questions.csv` with 6 questions across 2 rounds

## Common Patterns

### Testing WebSocket Events
```python
message = WebSocketMessage(EventType.JOIN_GAME, {
    "game_id": "test_game",
    "team_name": "Team Alpha"
})
responses = websocket_manager.handle_message(client_id, message)
```

### UI State Transitions (Context-Specific)

**Player App Pattern:**
```javascript
function showWaitingRoom() {
    hideAllScreens();  // Only hides player screens
    const waitingRoom = document.getElementById('waiting-room');
    if (waitingRoom) {
        waitingRoom.style.display = 'block'; // Override !important CSS
        waitingRoom.classList.remove('hidden');
    }
}
```

**Admin App Pattern:**
```javascript
function showAdminPreGamePanel() {
    hideAllScreens();  // Only hides admin screens
    const adminPanel = document.getElementById('admin-pregame-panel');
    if (adminPanel) {  // Context-aware null check
        adminPanel.style.display = 'block';
        adminPanel.classList.remove('hidden');
    }
}
```

### Error Handling
All WebSocket handlers return error responses for invalid states:
```python
return [WebSocketMessage(EventType.ERROR, {"message": "Error description"})]
```

## Port Configuration
The app uses port 3001 by default (configured in `backend/app.py` line 344, `launch_trivia.py` line 81). This was changed from 5000 to avoid conflicts with macOS AirPlay receiver.

## Test Execution Notes
- Some tests require `bs4` (BeautifulSoup4) dependency
- E2E tests require ChromeDriver installation
- Core functionality tests can run without additional dependencies
- Coverage reports generate in `htmlcov/` directory
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

# Run specific test files
python -m pytest tests/test_game_state.py -v
python -m pytest tests/test_websocket_manager.py -v
python -m pytest tests/test_integration.py -v

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
- **`js/game-client.js`**: WebSocket client, connection management, state persistence
- **`js/app.js`**: UI logic, DOM manipulation, progressive screen transitions
- **CSS**: Uses `!important` for initial hiding, JavaScript overrides for display

#### Testing (`tests/`)
- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-component workflows
- **WebSocket Tests**: Real-time communication testing  
- **E2E Tests**: Full user workflows with Selenium
- **Frontend Tests**: UI component visibility and transitions

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

### CSS Display Pattern
Components use `style="display: none !important;"` for initial hiding. JavaScript functions override with `element.style.display = 'block'` for proper progressive disclosure.

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

### UI State Transitions
```javascript
function showWaitingRoom() {
    hideAllScreens();
    const waitingRoom = document.getElementById('waiting-room');
    waitingRoom.style.display = 'block'; // Override !important CSS
    waitingRoom.classList.remove('hidden');
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
# 🏗️ Architecture Guide

## System Overview

The Trivia App is built with a client-server architecture using WebSocket connections for real-time communication.

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Frontend      │◄───────────────►│   Backend       │
│                 │                 │                 │
│ ┌─────────────┐ │                 │ ┌─────────────┐ │
│ │ HTML/CSS/JS │ │                 │ │ Flask+      │ │
│ │ Socket.IO   │ │                 │ │ SocketIO    │ │
│ │ State Mgmt  │ │                 │ │ Game Logic  │ │
│ └─────────────┘ │                 │ └─────────────┘ │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │ LocalStorage                      │ CSV Files
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│ Browser Storage │                 │ Question Data   │
│ - Game State    │                 │ - Rounds        │
│ - Team Info     │                 │ - Questions     │
│ - Connection    │                 │ - Answers       │
└─────────────────┘                 └─────────────────┘
```

## Backend Architecture

### Core Components

```
backend/
├── app.py                 # Flask application entry point
├── question_manager.py    # CSV question loading & management  
├── game_state.py         # Game logic, teams, scoring
└── websocket_manager.py  # Real-time WebSocket communication
```

### Component Responsibilities

#### 1. Flask Application (`app.py`)
- HTTP server setup with CORS configuration
- Route handlers for web pages and API endpoints
- WebSocket event registration and delegation
- Static file serving

#### 2. Question Manager (`question_manager.py`)  
- CSV file parsing with pandas
- Question validation and organization
- Round and question navigation
- Question retrieval by game/round/number

#### 3. Game State Manager (`game_state.py`)
- Game lifecycle management (create, start, finish)
- Team registration and management  
- Answer submission and grading
- Scoring and leaderboard calculation
- Game status tracking

#### 4. WebSocket Manager (`websocket_manager.py`)
- Client connection management
- Real-time event handling (13 client→server, 11 server→client events)
- Message broadcasting and targeting
- Connection cleanup and error handling

### Data Models

```python
# Core data structures
@dataclass
class Question:
    round_num: int
    question_num: int  
    question: str
    answer: str

@dataclass  
class Team:
    team_id: str
    name: str
    score: int

@dataclass
class Answer:
    team_id: str
    answer_text: str
    submitted_at: float
    is_correct: Optional[bool]
    points_awarded: int

@dataclass
class GameSession:
    game_id: str
    admin_password: str
    status: GameStatus
    teams: Dict[str, Team]
    answers: List[Answer]
    current_round: int
    current_question: int
```

### WebSocket Event Flow

```
Client Events → WebSocket Manager → Game State Manager
                       ↓
              Response Messages ← Question Manager
                       ↓  
              Broadcast to Clients
```

## Frontend Architecture

### Component Structure

```
frontend/
├── index.html          # Main application page
├── admin.html         # Admin control panel
├── css/styles.css     # Responsive styling
└── js/
    ├── game-client.js # WebSocket client & connection management
    └── app.js         # UI logic & event handling
```

### Frontend Layers

#### 1. Presentation Layer (`HTML/CSS`)
- Responsive design with mobile-first approach
- Component-based UI structure (screens/panels)
- CSS animations and transitions
- Cross-browser compatibility

#### 2. Application Layer (`app.js`)
- UI state management and screen transitions
- Event handling for user interactions  
- DOM manipulation and updates
- Browser storage management (localStorage)

#### 3. Communication Layer (`game-client.js`)
- WebSocket connection management
- Automatic reconnection with exponential backoff
- Event subscription and handling
- Connection status monitoring

### State Management

```javascript
// Client-side state structure
const gameState = {
    connectionStatus: 'connected|connecting|disconnected',
    gameInfo: {
        gameId: string,
        teamId: string, 
        teamName: string,
        isAdmin: boolean
    },
    currentScreen: 'home|waiting|game|results',
    gameStatus: 'setup|waiting|active|finished',
    leaderboard: Array<{teamName, score}>
}
```

## Real-Time Communication

### WebSocket Events

#### Client → Server Events
```javascript
// Team operations
join_game: {game_id, team_name}
submit_answer: {answer}

// Admin operations  
admin_login: {game_id, password}
start_game: {password}
start_question: {password}
close_question: {password}
grade_answer: {team_id, round_num, question_num, is_correct, points}
next_question: {password}
```

#### Server → Client Events
```javascript
// Game state updates
team_joined: {team_id, team_name}
game_started: {message}
question_started: {round, question_num, question, answer?}

// Answer flow
answer_submitted: {team_name?, answer, submitted_at}
question_closed: {answers}
answer_graded: {team_id, is_correct, points_awarded}

// Status updates
leaderboard_update: {leaderboard}
game_finished: {final_results}
```

### Connection Management

```javascript
// Automatic reconnection strategy
class GameClient {
    connect() {
        // WebSocket connection with auto-retry
        this.socket = io(serverUrl, {
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true
        });
        
        this.socket.on('disconnect', () => {
            this.handleDisconnection();
        });
    }
    
    handleDisconnection() {
        // Exponential backoff reconnection
        const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000);
        setTimeout(() => this.connect(), delay);
    }
}
```

## Data Flow

### Complete Game Workflow

```
1. Game Creation
   CSV File → Question Manager → Game State Manager → Game Session

2. Team Registration  
   Client → WebSocket Manager → Game State Manager → Broadcast Update

3. Game Start
   Admin → WebSocket Manager → Game State Manager → All Clients

4. Question Flow
   Admin Start → All Clients Display Question
   Clients Submit → Admin Sees Submissions (with auto-grading)
   Admin Grades → All Clients See Results
   Admin Next → Repeat

5. Game Completion
   Final Question → Game State Update → Results to All Clients
```

### Answer Grading Enhancement

```
Team Submits Answer
       ↓
WebSocket Manager receives submission
       ↓
Automatic correctness detection:
  - Get correct answer from Question Manager
  - Compare with submitted answer (case-insensitive)
  - Include auto-detection in admin notification
       ↓
Admin sees submission with auto-grade suggestion
       ↓  
Admin confirms/overrides grading
       ↓
Broadcast results to all teams
```

## Testing Architecture

### Test Categories

```
tests/
├── Unit Tests
│   ├── test_question_manager.py    # Question loading/parsing
│   ├── test_game_state.py         # Game logic & state
│   └── test_websocket_manager.py  # WebSocket communication
├── Integration Tests  
│   ├── test_integration.py        # Multi-component workflows
│   ├── test_websocket_integration.py # Real-time communication
│   └── test_routes.py            # HTTP endpoints
├── Frontend Tests
│   ├── test_frontend_component_visibility.py # UI flow
│   └── test_frontend_workflow.py  # Selenium browser tests
└── End-to-End Tests
    └── test_e2e.py               # Complete user workflows
```

### Test Infrastructure

```python
# Test helpers and utilities
class TestGameSetup:
    - Creates temporary CSV files
    - Sets up test game sessions
    - Manages client connections
    - Cleans up resources

class MockWebSocketManager:
    - Simulates real-time communication
    - Tests event handling without network
    - Validates message broadcasting
```

## Performance Considerations

### Backend Optimization
- **Single Worker Process** - Uses eventlet for async I/O
- **In-Memory Storage** - Fast access to game state
- **Efficient CSV Parsing** - Pandas for question loading
- **Connection Pooling** - Manages WebSocket connections efficiently

### Frontend Optimization  
- **Vanilla JavaScript** - No framework overhead
- **Event Delegation** - Efficient DOM event handling
- **LocalStorage Caching** - Reduces server requests
- **Lazy Loading** - Only load active UI components

### Real-Time Performance
- **WebSocket over HTTP** - Lower latency than polling
- **Message Batching** - Group related updates
- **Selective Broadcasting** - Target specific clients
- **Connection Health Monitoring** - Proactive reconnection

## Security Architecture

### Authentication & Authorization
- **Admin Password Protection** - Game-level admin access
- **Session-Based Auth** - WebSocket connection validation
- **Input Validation** - Sanitize all user inputs
- **CORS Configuration** - Restrict cross-origin requests

### Data Protection
- **No Persistent Storage** - In-memory only (privacy)
- **Environment Variables** - Sensitive config externalized
- **Error Handling** - No sensitive data in error messages
- **Rate Limiting** - Prevent abuse (future enhancement)

## Scalability Considerations

### Current Limitations
- **Single Server Instance** - Not horizontally scalable
- **In-Memory Storage** - Limited by server RAM
- **Single Process** - CPU bound by Python GIL

### Scaling Strategies  
- **Redis for State** - Shared state across instances
- **Load Balancer** - Distribute WebSocket connections  
- **Database Storage** - Persistent game data
- **Message Queue** - Async processing

This architecture provides a solid foundation for real-time multiplayer gaming with room for future enhancements and scaling.
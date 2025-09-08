# 🔧 API Reference

## REST API Endpoints

### Application Routes

#### `GET /`
Serves the main application page.

**Response:** HTML page with team join interface

#### `GET /admin`  
Serves the admin control panel.

**Response:** HTML page with admin login interface

#### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### Game Management API

#### `POST /api/create-game`
Creates a new game with questions from CSV file.

**Parameters:**
- `csv_file` (file) - CSV file containing questions
- `game_id` (string) - Unique game identifier  
- `admin_password` (string) - Admin authentication password

**Response:**
```json
{
    "success": true,
    "game_id": "demo_game",
    "message": "Game created successfully",
    "question_count": 12,
    "rounds": 2
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "Game ID already exists"
}
```

#### `GET /api/games/<game_id>`
Retrieves game information (admin only).

**Response:**
```json
{
    "game_id": "demo_game",
    "status": "waiting",
    "team_count": 3,
    "current_round": 1,
    "current_question": 1,
    "total_questions": 12
}
```

## WebSocket Events

### Connection
Connect to WebSocket endpoint: `/socket.io/`

### Client → Server Events

#### `join_game`
Team joins a game session.

**Data:**
```json
{
    "game_id": "demo_game",
    "team_name": "Team Alpha"
}
```

**Success Response:** `team_joined` event
**Error Response:** `error` event

#### `admin_login`
Admin authentication for game control.

**Data:**
```json
{
    "game_id": "demo_game", 
    "password": "admin123"
}
```

**Success Response:** `success` event
**Error Response:** `error` event

#### `start_game`
Admin starts the game (moves teams from waiting to active).

**Data:**
```json
{
    "password": "admin123"
}
```

**Broadcasts:** `game_started` to all clients

#### `start_question`  
Admin starts a specific question.

**Data:**
```json
{
    "password": "admin123"
}
```

**Broadcasts:** `question_started` to all clients

#### `submit_answer`
Team submits an answer to current question.

**Data:**
```json
{
    "answer": "Paris"
}
```

**Responses:** 
- `answer_submitted` to submitting team (confirmation)
- `answer_submitted` to admin (with auto-grading info)

#### `close_question`
Admin closes question for new submissions.

**Data:**
```json
{
    "password": "admin123"
}
```

**Broadcasts:** `question_closed` to all clients

#### `grade_answer`
Admin grades a team's answer.

**Data:**
```json
{
    "team_id": "uuid-string",
    "round_num": 1,
    "question_num": 1, 
    "is_correct": true,
    "points": 1
}
```

**Broadcasts:** `answer_graded` to all clients

#### `next_question`
Admin progresses to next question.

**Data:**
```json
{
    "password": "admin123"
}
```

**Broadcasts:** `question_started` or `game_finished`

#### `get_leaderboard`
Request current leaderboard standings.

**Data:** `{}` (empty)

**Response:** `leaderboard_update` event

#### `get_game_state`
Request current game state information.

**Data:** `{}` (empty)

**Response:** Game state data

### Server → Client Events

#### `team_joined`
Confirms team successfully joined game.

**Data:**
```json
{
    "team_id": "uuid-string",
    "team_name": "Team Alpha",
    "game_id": "demo_game"
}
```

#### `team_list_update`
Updates list of teams in game.

**Data:**
```json
{
    "teams": [
        {"team_id": "uuid-1", "name": "Team Alpha", "score": 0},
        {"team_id": "uuid-2", "name": "Team Beta", "score": 0}
    ]
}
```

#### `game_started`
Game has been started by admin.

**Data:**
```json
{
    "message": "Game has been started",
    "status": "in_progress"
}
```

#### `question_started`
New question is now active.

**Team Data:**
```json
{
    "round": 1,
    "question_num": 1,
    "question": "What is the capital of France?"
}
```

**Admin Data:**
```json
{
    "round": 1,
    "question_num": 1, 
    "question": "What is the capital of France?",
    "answer": "Paris"
}
```

#### `answer_submitted`
Answer has been submitted.

**Team Confirmation:**
```json
{
    "answer": "Paris",
    "submitted_at": 1640995200.123
}
```

**Admin Notification:**
```json
{
    "team_name": "Team Alpha",
    "team_id": "uuid-string",
    "answer": "Paris", 
    "submitted_at": 1640995200.123,
    "is_auto_correct": true,
    "correct_answer": "Paris"
}
```

#### `question_closed`
Question closed, no more submissions accepted.

**Data:**
```json
{
    "answers": [
        {
            "team_id": "uuid-1",
            "team_name": "Team Alpha", 
            "answer": "Paris",
            "submitted_at": 1640995200.123
        }
    ],
    "status": "closed"
}
```

#### `answer_graded`
Answer has been graded by admin.

**Data:**
```json
{
    "team_id": "uuid-string",
    "team_name": "Team Alpha",
    "is_correct": true,
    "points_awarded": 1,
    "round": 1,
    "question_num": 1
}
```

#### `leaderboard_update`
Updated team standings.

**Data:**
```json
{
    "leaderboard": [
        {"team_name": "Team Alpha", "score": 5},
        {"team_name": "Team Beta", "score": 3},
        {"team_name": "Team Gamma", "score": 1}
    ]
}
```

#### `game_finished`  
Game completed, final results.

**Data:**
```json
{
    "message": "Game completed!",
    "final_results": [
        {"team_name": "Team Alpha", "score": 10, "rank": 1},
        {"team_name": "Team Beta", "score": 8, "rank": 2}  
    ],
    "total_questions": 12
}
```

#### `error`
Error occurred during operation.

**Data:**
```json
{
    "message": "Error description",
    "code": "ERROR_CODE"
}
```

#### `success`
Operation completed successfully.

**Data:**
```json
{
    "message": "Operation successful"
}
```

## Error Codes

### Common Errors
- `GAME_NOT_FOUND` - Game ID does not exist
- `INVALID_PASSWORD` - Admin password incorrect
- `TEAM_ALREADY_EXISTS` - Team name already taken in game
- `GAME_ALREADY_STARTED` - Cannot join game after start
- `NOT_ADMIN` - Admin privileges required
- `NOT_IN_TEAM` - Must be part of team for operation
- `QUESTION_NOT_ACTIVE` - Cannot submit answer when question closed
- `DUPLICATE_ANSWER` - Team already submitted answer for question

### WebSocket Errors
- `CONNECTION_FAILED` - Unable to establish WebSocket connection
- `RECONNECTION_FAILED` - Auto-reconnection attempts failed
- `INVALID_EVENT` - Unknown event type received

## Rate Limiting

Currently no rate limiting implemented. Consider adding for production:

```javascript
// Suggested rate limits
{
    "submit_answer": "1 per question per team",
    "join_game": "5 per minute per IP",
    "admin_actions": "10 per minute per game"
}
```

## Authentication

### Team Authentication
- No explicit authentication required
- Teams identified by `team_id` assigned at join
- Connection session maintains team identity

### Admin Authentication  
- Password-based authentication per game
- Admin status maintained during WebSocket session
- All admin operations require password validation

## Data Validation

### Input Sanitization
All user inputs are validated:
- **Team Names:** 1-50 characters, alphanumeric + spaces
- **Game IDs:** 1-50 characters, alphanumeric + underscores  
- **Answers:** 1-500 characters, any printable characters
- **CSV Files:** Valid format with required headers

### Security Headers
```http
Content-Type: application/json
X-Frame-Options: DENY  
X-Content-Type-Options: nosniff
```

## Response Times

### Expected Latencies
- **HTTP Requests:** < 100ms
- **WebSocket Events:** < 50ms  
- **Question Display:** < 100ms (synchronized)
- **Answer Submission:** < 50ms
- **Leaderboard Update:** < 100ms

### Performance Monitoring
Monitor these endpoints:
- `GET /health` - Application health
- WebSocket connection count
- Event processing time
- Error rates per event type
# Running the Trivia App

## Quick Start

**The fastest way to get started:**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch with sample game
python launch_trivia.py
```

This will:
- Start the server on `http://localhost:5000`
- Create a demo game with sample questions
- Open your browser automatically
- **Game ID:** `demo_game`
- **Admin Password:** `admin123`

## Manual Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python -m backend.app
```

The app will be available at `http://localhost:5000`

### 3. Create a Game
```bash
# Using curl
curl -X POST http://localhost:5000/api/create-game \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "my_game",
    "csv_file_path": "sample_questions.csv",
    "admin_password": "secret123"
  }'
```

### 4. Access the App
Open `http://localhost:5000/` in your browser

## API Endpoints

### REST API
- `GET /health` - Health check
- `POST /api/create-game` - Create new game
- `GET /api/games/<game_id>` - Get game information

### WebSocket Events (SocketIO)

#### Client to Server Events:
- `join_game` - Team joins a game
- `admin_login` - Admin authentication
- `start_game` - Admin starts the game
- `start_question` - Admin starts a question
- `submit_answer` - Team submits an answer
- `close_question` - Admin closes current question
- `grade_answer` - Admin grades an answer
- `next_question` - Admin moves to next question
- `get_leaderboard` - Request current leaderboard

#### Server to Client Events:
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

## Game Workflow

1. **Setup**: Admin creates game with CSV file
2. **Registration**: Teams join using game ID
3. **Start**: Admin starts the game
4. **Questions**: 
   - Admin starts each question
   - Teams submit answers
   - Admin closes question
   - Admin grades each answer
   - Admin moves to next question
5. **Finish**: Game ends when all questions completed

## Testing

Run the complete test suite:
```bash
pytest -v
```

Current test coverage: **79 tests, all passing**

## CSV Format

Questions should be in CSV format with headers:
```csv
round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6
2,1,What is the capital of France?,Paris
```

## Architecture

- **QuestionManager**: Handles CSV loading and question retrieval
- **GameStateManager**: Manages game state, teams, and scoring
- **WebSocketManager**: Handles real-time communication
- **Flask App**: REST API and SocketIO integration

All components are fully tested with comprehensive unit and integration tests.
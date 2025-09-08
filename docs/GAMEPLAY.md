# 🎮 Gameplay Guide

## For Teams (Players)

### 1. Joining the Game
1. **Navigate** to the shared URL (e.g., `http://192.168.1.100:3001`)
2. **Enter Game ID** provided by the host (e.g., `demo_game`)
3. **Choose Team Name** - make it fun and memorable!
4. **Click "Join Game"** - you'll automatically move to the waiting room

### 2. Waiting Room
- **See Other Teams** - view all teams that have joined
- **Connection Status** - ensure you're connected to the server
- **Wait for Host** - the admin will start the game when ready

### 3. During Gameplay
- **Read Questions** - displayed automatically when started by admin
- **Submit Answers** - type your answer and click submit
- **One Chance** - you can only submit one answer per question
- **Wait for Results** - no feedback until admin closes the question

### 4. Results and Scoring
- **View Results** - see if your answer was correct after each question
- **Live Leaderboard** - track your team's ranking in real-time  
- **Final Scores** - complete results shown at game end

### 5. Connection Features
- **Auto-Reconnect** - if you lose connection, the app will reconnect automatically
- **Page Refresh** - you can refresh without losing your place
- **Rejoin Game** - close browser and rejoin later with same team name

## For Host/Admin

### 1. Admin Access
1. **Navigate** to `/admin` URL (e.g., `http://localhost:3001/admin`)
2. **Enter Game ID** and **Admin Password**
3. **Login** - you'll see the admin dashboard

### 2. Pre-Game Setup
- **Monitor Team Joins** - see teams join in real-time
- **Verify Questions** - ensure CSV loaded correctly
- **Check Connections** - confirm all teams are connected

### 3. Game Management

#### Starting the Game
- **Click "Start Game"** - moves all teams from waiting room to game screen
- **No Going Back** - once started, teams can't be added

#### Question Flow
1. **Start Question** - click to display question to all teams
2. **Monitor Submissions** - see answers appear in real-time with auto-grading
3. **Grade Answers** - mark each answer correct/incorrect (auto-suggestions provided)
4. **Close Question** - teams see results and updated leaderboard
5. **Next Question** - progress through all questions

#### Answer Grading Features
- **Auto-Detection** - answers matching CSV are automatically marked correct/incorrect
- **Manual Override** - you can change the auto-detection if needed
- **Visual Indicators** - green checkmarks for correct, red X for incorrect
- **Instant Grading** - click buttons to quickly grade each team's answer

### 4. Admin Controls
- **Question Navigation** - move through rounds and questions
- **Score Management** - adjust points awarded per question
- **Game Status** - monitor overall game progress
- **Leaderboard** - view live rankings

## Game Flow Overview

### Complete Workflow
```
1. Setup → Admin creates game, loads questions from CSV
2. Join → Teams see only join form, enter details → move to waiting room  
3. Start → Admin starts game → teams move to game screen
4. Questions → For each question:
   - Admin starts question → question displays to teams
   - Teams submit answers → admin sees submissions with auto-grading
   - Admin grades answers → admin sees all submissions
   - Admin closes question → teams see results + leaderboard
   - Admin moves to next question → repeat
5. End → All questions complete → teams see final results
```

### Game States
- **Setup** - Admin preparing game
- **Waiting** - Teams joined, waiting for start  
- **Active** - Game in progress, questions being answered
- **Question Active** - Current question open for answers
- **Question Closed** - Question closed, being graded
- **Finished** - Game complete, final results shown

## Tips for Success

### For Teams
- **Stay Connected** - keep browser window open
- **Be Quick** - some games may have time limits
- **Team Communication** - discuss answers if playing in groups
- **Refresh if Needed** - app will restore your session

### For Hosts
- **Test First** - run through a practice round with friends
- **Clear Instructions** - explain rules before starting
- **Monitor Submissions** - watch for technical issues
- **Use Auto-Grading** - trust the automatic correctness detection for speed
- **Have Backup** - prepare extra questions in case needed

### Best Practices
- **Internet Connection** - ensure stable WiFi for all players
- **Device Variety** - works on phones, tablets, and computers
- **Browser Choice** - Chrome, Firefox, Safari, and Edge all supported
- **Screen Size** - responsive design works on any screen size

## Advanced Features

### Reconnection System
- **Automatic** - app reconnects if connection is lost
- **Manual Refresh** - refresh browser to reconnect manually
- **Session Restore** - rejoins your team and current game state
- **Cross-Device** - join on phone, switch to computer, rejoin seamlessly

### Real-Time Updates  
- **Live Team List** - see teams join/leave instantly
- **Synchronized Questions** - all players see questions simultaneously
- **Instant Results** - scores update immediately after grading
- **Connection Status** - visual indicators show connection health

### Mobile Optimization
- **Touch-Friendly** - large buttons and easy navigation
- **Portrait/Landscape** - works in any orientation
- **Zoom Support** - pinch to zoom if needed
- **Responsive Design** - optimized layout for all screen sizes
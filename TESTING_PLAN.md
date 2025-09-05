# Trivia App Testing Plan

## Overview
This document provides comprehensive testing plans for both automated and manual testing of the Trivia App, including multi-device testing with friends and family.

## Automated Testing Status

### ✅ Current Test Coverage
- **79 automated tests** covering:
  - Unit tests for all backend components
  - Integration tests for component interaction
  - WebSocket communication tests
  - End-to-end workflow tests

### Test Categories
1. **Unit Tests (47 tests)**
   - QuestionManager: CSV loading, question retrieval
   - GameStateManager: Game lifecycle, team management, scoring
   - WebSocketManager: Event handling, client management

2. **Integration Tests (11 tests)**
   - Full game workflow testing
   - Multi-game isolation
   - Error handling across components
   - CSV format edge cases

3. **WebSocket Integration Tests (6 tests)**
   - Real-time communication
   - Client connection lifecycle
   - Multi-game broadcasting

4. **End-to-End Tests (15 tests)**
   - Browser automation with Selenium
   - Complete user workflows
   - Multi-user game sessions

## Manual Testing Plan for External Testing

### Prerequisites
Before testing with friends, ensure:

1. **Server Setup**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Start the server
   python -m backend.app
   ```
   
2. **Network Configuration**
   - Server accessible on local network: `http://[YOUR_IP]:5000`
   - Firewall allows port 5000
   - All devices on same WiFi network

3. **Test Data Preparation**
   - Create diverse question sets
   - Questions with varying difficulty
   - Clear, unambiguous answers

### Test Scenarios

## Scenario 1: Basic Game Flow (2-4 people, 15 minutes)

**Participants:** 1 Admin + 2-3 Teams

**Objective:** Test complete game flow with real users

**Steps:**
1. **Setup Phase (2 minutes)**
   - Admin creates game via API or direct server access
   - Share Game ID with participants
   - All participants open `http://[SERVER_IP]:5000/frontend/`

2. **Registration Phase (3 minutes)**
   - Each team joins with unique team names
   - Admin logs in to admin panel
   - Verify all teams appear in both waiting room and admin panel
   - **Test**: Try duplicate team names (should fail)
   - **Test**: Try invalid game ID (should show error)

3. **Game Play Phase (8 minutes)**
   - Admin starts the game
   - Admin starts first question
   - Teams submit answers (mix of correct/incorrect)
   - Admin closes question and grades answers
   - Repeat for 3-4 questions
   - **Test**: Try submitting multiple answers (should fail)
   - **Test**: Submit answers after question closed (should fail)

4. **Completion Phase (2 minutes)**
   - Admin progresses through all questions
   - Verify final leaderboard is correct
   - Check all participants see game finished screen

**Expected Results:**
- All participants stay connected throughout
- Real-time updates work correctly
- Scoring is accurate
- No crashes or error states

## Scenario 2: Connection Resilience (3-4 people, 20 minutes)

**Participants:** 1 Admin + 2-3 Teams

**Objective:** Test reconnection and persistence features

**Steps:**
1. **Initial Setup** (5 minutes)
   - Complete Scenario 1 setup
   - Start game and play 1-2 questions

2. **Reconnection Testing** (10 minutes)
   - **Test A**: Team refreshes browser during question
     - Should see rejoin modal
     - Should reconnect with same team name
     - Should rejoin current game state
   
   - **Test B**: Team closes browser and reopens
     - Should see rejoin modal with saved game ID
     - Should be able to rejoin by entering team name
   
   - **Test C**: Admin refreshes during game
     - Should automatically reconnect as admin
     - Should maintain admin privileges
     - Should see current game state

3. **Network Interruption** (5 minutes)
   - **Test**: Temporarily disconnect WiFi on one device
     - Should show "Reconnecting..." status
     - Should automatically reconnect when WiFi returns
     - Should rejoin game state correctly

**Expected Results:**
- All reconnection scenarios work smoothly
- No loss of game progress or team information
- Admin maintains control after reconnection
- Real-time sync resumes correctly

## Scenario 3: Edge Cases and Error Handling (2-3 people, 15 minutes)

**Participants:** 1 Admin + 1-2 Teams

**Objective:** Test error conditions and edge cases

**Steps:**
1. **Invalid Inputs** (5 minutes)
   - Try joining with empty team name
   - Try admin login with wrong password
   - Try starting game with no teams
   - Submit empty answers

2. **Timing Edge Cases** (5 minutes)
   - Submit answer just as question closes
   - Admin starts next question before grading complete
   - Multiple rapid admin actions

3. **Browser Compatibility** (5 minutes)
   - Test on different browsers (Chrome, Firefox, Safari, Edge)
   - Test on mobile devices (phones, tablets)
   - Test with different screen sizes

**Expected Results:**
- Clear error messages for invalid inputs
- Graceful handling of timing conflicts
- Consistent behavior across browsers and devices

## Scenario 4: Scale Testing (5-10 people, 25 minutes)

**Participants:** 1 Admin + 4-9 Teams

**Objective:** Test with larger group sizes

**Steps:**
1. **Mass Registration** (5 minutes)
   - All teams join simultaneously
   - Verify all appear in admin panel
   - Check for any performance issues

2. **Concurrent Answer Submission** (10 minutes)
   - All teams submit answers quickly when question starts
   - Admin grades all answers
   - Verify leaderboard updates correctly
   - Check response times remain acceptable

3. **Extended Game Session** (10 minutes)
   - Play through full question set (10+ questions)
   - Monitor for memory leaks or performance degradation
   - Verify final results are accurate

**Expected Results:**
- Server handles multiple concurrent connections
- WebSocket performance remains good
- UI remains responsive with many teams
- No connection drops under load

## Scenario 5: Mobile and Cross-Platform (3-5 people, 20 minutes)

**Participants:** Mix of desktop and mobile users

**Objective:** Test cross-platform compatibility

**Device Mix:**
- Desktop computers (Windows, Mac, Linux)
- Smartphones (iOS, Android)
- Tablets (iPad, Android tablets)
- Different browsers on each platform

**Steps:**
1. **Cross-Platform Registration** (5 minutes)
   - Each person joins from different device type
   - Verify UI adapts to screen sizes
   - Check touch interactions work on mobile

2. **Mixed Platform Gameplay** (10 minutes)
   - Admin on desktop, teams on various devices
   - Play complete game round
   - Verify all platforms receive updates correctly

3. **Mobile-Specific Testing** (5 minutes)
   - Test portrait/landscape orientation changes
   - Test with poor cellular connection
   - Verify touch targets are appropriate size

**Expected Results:**
- Responsive design works on all screen sizes
- Touch interactions are smooth on mobile
- Performance is acceptable on all platforms

## Test Data Sets

### Sample Question Sets

**Set 1: General Knowledge (Easy)**
```csv
round_num,question_num,question,answer
1,1,What is the capital of France?,Paris
1,2,What is 2+2?,4
1,3,What color is the sun?,Yellow
2,1,How many days in a week?,7
2,2,What is the largest ocean?,Pacific
2,3,What animal says 'moo'?,Cow
```

**Set 2: Mixed Difficulty**
```csv
round_num,question_num,question,answer
1,1,What is the chemical symbol for water?,H2O
1,2,Who painted the Mona Lisa?,Leonardo da Vinci
1,3,What is the square root of 64?,8
2,1,In what year did World War II end?,1945
2,2,What is the longest river in the world?,Nile
2,3,How many bones are in an adult human body?,206
```

**Set 3: Fun/Personal Questions**
```csv
round_num,question_num,question,answer
1,1,What is your favorite pizza topping?,Any answer accepted
1,2,Name a superhero,Any superhero name
1,3,What's your dream vacation destination?,Any location
2,1,Favorite movie genre?,Any genre
2,2,Best day of the week?,Any day
2,3,Cats or dogs?,Either answer
```

## Testing Checklist

### Pre-Test Setup ✅
- [ ] Server running on accessible IP
- [ ] Game created with test questions
- [ ] All participants have access to server URL
- [ ] Network connectivity verified

### During Testing ✅
- [ ] All participants can connect
- [ ] Team registration works correctly
- [ ] Admin panel functions properly
- [ ] Real-time updates work
- [ ] Question display is clear
- [ ] Answer submission works
- [ ] Grading interface is intuitive
- [ ] Leaderboard updates correctly
- [ ] Game completion works

### Post-Test Validation ✅
- [ ] Final scores are accurate
- [ ] All participants saw game end
- [ ] No error messages or crashes
- [ ] Performance was acceptable
- [ ] Reconnection features worked

## Troubleshooting Guide

### Common Issues and Solutions

**Connection Problems:**
- Check firewall settings
- Verify IP address is correct
- Ensure port 5000 is open
- Try accessing health endpoint: `http://[IP]:5000/health`

**WebSocket Issues:**
- Check browser console for errors
- Verify SocketIO library loaded
- Try refreshing the page
- Check network connectivity

**Game State Issues:**
- Clear localStorage in browser
- Restart game session
- Verify CSV file format
- Check server logs for errors

**Performance Issues:**
- Monitor server resource usage
- Check network bandwidth
- Reduce concurrent users if needed
- Clear browser cache

## Success Criteria

### Functional Requirements ✅
- [ ] Teams can join games reliably
- [ ] Admin can control game flow
- [ ] Questions display correctly
- [ ] Answers submit successfully
- [ ] Scoring works accurately
- [ ] Real-time updates function
- [ ] Game completes properly

### Quality Requirements ✅
- [ ] Response time under 2 seconds
- [ ] No crashes during normal use
- [ ] Graceful error handling
- [ ] Intuitive user interface
- [ ] Cross-platform compatibility
- [ ] Connection persistence works

### User Experience ✅
- [ ] Easy to understand and use
- [ ] Clear feedback for all actions
- [ ] Responsive on all devices
- [ ] Engaging and fun to play
- [ ] Reliable reconnection
- [ ] Smooth game flow

## Reporting Issues

When reporting issues during testing:

1. **Include Environment Info:**
   - Device type and operating system
   - Browser name and version
   - Network connection type
   - Number of participants

2. **Describe the Problem:**
   - What were you trying to do?
   - What actually happened?
   - What should have happened?
   - Can you reproduce it?

3. **Provide Context:**
   - Game ID and role (admin/team)
   - Which step in the process
   - Any error messages
   - Screenshots if helpful

## Next Steps After Testing

Based on test results:

1. **Fix Critical Issues:** Connection problems, scoring errors
2. **Improve UX:** Based on user feedback
3. **Performance Optimization:** If needed for larger groups
4. **Additional Features:** Based on user requests
5. **Documentation Updates:** Based on testing insights

---

**Happy Testing! 🎯**

Remember: The goal is to have fun while ensuring the app works reliably for everyone. Don't hesitate to experiment and try unexpected things - that's how we find the best bugs!
# 🐛 Troubleshooting Guide

## Common Issues

### Connection Problems

#### **Issue:** Cannot connect to server from other devices
**Symptoms:**
- App works on host computer but not on phones/other computers
- Browser shows "Connection failed" or infinite loading

**Solutions:**
```bash
# 1. Check if server is running on all interfaces (0.0.0.0)
# Should see "Running on all addresses (0.0.0.0)" in console

# 2. Find your IP address
# Windows
ipconfig | findstr "IPv4"
# Mac/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# 3. Test server accessibility
curl http://[YOUR_IP]:3001/health

# 4. Check firewall settings
# Windows (run as administrator)
netsh advfirewall firewall add rule name="Trivia App" dir=in action=allow protocol=TCP localport=3001
# Mac
sudo ufw allow 3001
# Linux
sudo iptables -A INPUT -p tcp --dport 3001 -j ACCEPT

# 5. Verify port isn't blocked by router
# Check router admin panel for port blocking
```

#### **Issue:** WebSocket connection keeps disconnecting
**Symptoms:**
- Frequent "Disconnected" messages
- Players get kicked out of game randomly

**Solutions:**
```javascript
// Check browser console for WebSocket errors
// Look for messages like "WebSocket connection failed"

// 1. Browser DevTools → Network → WS (WebSocket) tab
// Look for failed WebSocket frames

// 2. Try different browsers (Chrome, Firefox, Safari)

// 3. Clear browser cache and cookies
// Chrome: Ctrl+Shift+Delete
// Firefox: Ctrl+Shift+Delete
// Safari: Cmd+Option+E

// 4. Check network stability
// Test with mobile hotspot vs WiFi

// 5. Server-side: Check for errors
tail -f logs/trivia.log  # If logging is enabled
```

### Game Setup Issues

#### **Issue:** Game ID not found
**Symptoms:**
- "Game not found" error when joining
- Admin can't login to existing game

**Solutions:**
```bash
# 1. Verify game was created successfully
curl http://localhost:3001/api/games/your_game_id

# 2. Check CSV file loading
# Look for errors in server console when starting

# 3. Recreate game if needed
python launch_trivia.py --game-id new_game --password newpass

# 4. Check server logs for creation errors
python -m pytest tests/test_question_manager.py -v  # Test CSV parsing
```

#### **Issue:** CSV file won't load / Questions not appearing
**Symptoms:**
- Server starts but no questions available
- Error messages about CSV format

**Solutions:**
```csv
# 1. Verify CSV format exactly matches required headers
round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is the capital of France?,Paris

# 2. Check for common CSV issues:
# - Missing headers
# - Extra spaces in headers
# - Special characters/encoding issues
# - Empty lines
# - Commas within questions (use quotes: "What is 2+2, exactly?")

# 3. Test with sample file
cp sample_questions.csv test.csv
python launch_trivia.py --csv test.csv

# 4. Validate CSV programmatically
python -c "
import pandas as pd
df = pd.read_csv('your_file.csv')
print('Headers:', df.columns.tolist())
print('Shape:', df.shape)
print('First few rows:')
print(df.head())
"
```

### Gameplay Issues

#### **Issue:** Teams can't join game
**Symptoms:**  
- "Team name already exists" error for unique names
- Join button doesn't work
- Stuck on join screen

**Solutions:**
```javascript
// 1. Check browser console for JavaScript errors
// Press F12 → Console tab

// 2. Verify game hasn't started yet
// Teams can only join before admin starts game

// 3. Clear browser storage
localStorage.clear();
sessionStorage.clear();

// 4. Try different team name
// Check if name has special characters

// 5. Refresh page and try again
location.reload();
```

#### **Issue:** Admin can't start game
**Symptoms:**
- "Start Game" button doesn't work  
- Error about password or permissions

**Solutions:**
```bash
# 1. Verify admin password is correct
# Check exact spelling and case sensitivity

# 2. Ensure at least one team has joined
# Game requires teams before starting

# 3. Check browser console for errors
# Look for WebSocket connection issues

# 4. Verify admin is properly logged in
# Should see admin controls and team list

# 5. Try refreshing admin page
# Clear cache if needed
```

#### **Issue:** Answers not being submitted
**Symptoms:**
- Submit button doesn't work
- Answer form doesn't respond
- Teams can't answer questions

**Solutions:**
```javascript
// 1. Check question is actually active
// Admin must start question first

// 2. Verify team hasn't already submitted
// Each team can only submit once per question

// 3. Check for JavaScript errors
console.log('Current game state:', gameClient?.gameState);

// 4. Test WebSocket connection
gameClient?.socket?.connected  // Should return true

// 5. Clear form and try again
document.getElementById('answer-input').value = '';
```

### Technical Issues

#### **Issue:** Server won't start
**Symptoms:**
- Python errors when running launch script
- Port already in use errors
- Module import errors

**Solutions:**
```bash
# 1. Check Python version
python --version  # Should be 3.9+

# 2. Install/reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 3. Check for port conflicts
# Windows
netstat -ano | findstr :3001
taskkill /PID [PID_NUMBER] /F

# Mac/Linux
lsof -ti:3001 | xargs kill

# 4. Try different port
python -m backend.app  # Uses port 3001 by default
# Or modify backend/app.py to use different port

# 5. Check file permissions
ls -la backend/
chmod +x launch_trivia.py
```

#### **Issue:** High memory/CPU usage
**Symptoms:**
- Server becomes slow or unresponsive
- High resource usage with few players

**Solutions:**
```bash
# 1. Monitor resource usage
htop  # Linux/Mac
Task Manager  # Windows

# 2. Check for memory leaks
# Look for growing Python processes

# 3. Restart server regularly for long games
sudo systemctl restart trivia-app  # If using systemd

# 4. Limit concurrent players
# Current architecture supports ~20-50 concurrent users

# 5. Check logs for errors
tail -f /var/log/trivia-app.log
```

### Browser-Specific Issues

#### **Chrome Issues**
```javascript
// Clear site data
// Chrome Settings → Privacy → Clear browsing data → Advanced → All time

// Disable extensions temporarily
// Chrome menu → Extensions → Disable all

// Check for WebSocket blocking
// Some corporate networks block WebSocket connections
```

#### **Safari Issues**
```javascript
// Enable WebSocket support
// Safari → Preferences → Advanced → Show Develop menu
// Develop → Experimental Features → Ensure WebSocket is enabled

// Clear website data
// Safari → Preferences → Privacy → Manage Website Data
```

#### **Firefox Issues**
```javascript
// Check WebSocket settings
// Type about:config in address bar
// Search for network.websocket.enabled (should be true)

// Disable tracking protection temporarily
// Shield icon in address bar → Turn off
```

### Mobile Device Issues

#### **iOS Issues**
```bash
# Safari mobile WebSocket issues
# Update to latest iOS version
# Try Chrome or Firefox on iOS instead

# Touch interface problems
# Ensure buttons are large enough (CSS touch-action)
# Test in both portrait and landscape modes
```

#### **Android Issues**
```bash
# Chrome mobile issues
# Clear Chrome app data
# Update Chrome app to latest version

# Network issues
# Try switching between WiFi and mobile data
# Some mobile carriers block WebSocket connections
```

## Advanced Troubleshooting

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
python -m backend.app

# This will show detailed error messages and stack traces
```

### WebSocket Debugging
```javascript
// Monitor WebSocket traffic in browser
// F12 → Network → WS (WebSocket) tab
// Watch for connection attempts and messages

// Manual WebSocket testing
const socket = io('http://localhost:3001');
socket.on('connect', () => console.log('Connected'));
socket.on('disconnect', () => console.log('Disconnected'));
socket.emit('test_event', {data: 'test'});
```

### Server Diagnostics
```bash
# Check server health
curl http://localhost:3001/health

# Expected response:
{
    "status": "healthy",
    "timestamp": 1640995200.123
}

# Test WebSocket endpoint
wscat -c ws://localhost:3001/socket.io/

# Monitor server performance
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
"
```

### Database Debugging (if using)
```bash
# Test database connection
python -c "
import os
import psycopg2  # or other database adapter
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
print('Database connection successful')
conn.close()
"
```

## Performance Issues

### Slow Response Times
```bash
# 1. Check network latency
ping your-server-ip

# 2. Monitor server load
top  # Linux/Mac
Task Manager  # Windows

# 3. Profile application
# Add timing to critical operations
import time
start = time.time()
# ... operation ...
print(f'Operation took {time.time() - start:.2f} seconds')
```

### Memory Issues
```python
# Monitor memory usage
import tracemalloc
import gc

tracemalloc.start()

# ... run your code ...

current, peak = tracemalloc.get_traced_memory()
print(f'Current memory usage: {current / 1024 / 1024:.1f} MB')
print(f'Peak memory usage: {peak / 1024 / 1024:.1f} MB')

# Force garbage collection
gc.collect()
```

## Error Message Reference

### Common Error Messages

#### `"Game not found"`
- Game ID doesn't exist or was typed incorrectly
- Game may have been deleted/restarted

#### `"Team name already exists"`
- Another team in the game has the same name
- Try a different team name

#### `"Game already started"`
- Teams can't join after admin starts game
- Contact admin to restart if needed

#### `"Admin access required"`
- Operation requires admin privileges
- Ensure you're logged in as admin with correct password

#### `"Question not active"`
- Trying to submit answer when question is closed
- Wait for admin to start next question

#### `"Team has already submitted"`
- Each team can only submit one answer per question
- Wait for question to close and next one to start

### HTTP Error Codes

#### `404 Not Found`
- URL path is incorrect
- Server may not be running

#### `500 Internal Server Error`
- Server-side error occurred
- Check server logs for details

#### `502 Bad Gateway`
- Proxy/load balancer can't reach application
- Check nginx configuration if using

#### `503 Service Unavailable`
- Server is temporarily down
- Wait and retry

## Getting Additional Help

### Diagnostic Information to Collect
When reporting issues, please include:

```bash
# System information
python --version
pip list | grep -E "(flask|socketio)"

# Browser information
# Which browser and version
# Any console error messages (F12 → Console)

# Network information
# Are you on same network as server?
# Any corporate firewalls or proxies?

# Error reproduction
# Exact steps to reproduce the issue
# Screenshots if applicable

# Server logs
# Any error messages from server console
# Check browser network tab for failed requests
```

### Self-Diagnosis Checklist
Before reporting issues, try:

1. **Restart everything**
   - Close all browser tabs
   - Restart server
   - Try again

2. **Test with minimal setup**
   - Use sample CSV file
   - Test on localhost first
   - Try with single team/admin

3. **Check basics**
   - Python version 3.9+
   - All dependencies installed
   - Correct file permissions
   - Port not blocked

4. **Browser testing**
   - Try different browser
   - Disable extensions
   - Clear cache and cookies

5. **Network testing**
   - Test on same WiFi
   - Try mobile hotspot
   - Check firewall settings

If issues persist after trying these solutions, consider:
- Checking the [GitHub Issues](https://github.com/your-repo/issues) page
- Running the test suite to identify component failures
- Testing with the included sample files to isolate custom content issues

Most issues are related to network configuration, browser compatibility, or CSV file formatting. The diagnostic steps above resolve 90%+ of common problems.
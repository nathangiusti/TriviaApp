/**
 * Trivia App Main Application
 */
let gameClient;
let adminPassword = '';

// Initialize the application
document.addEventListener('DOMContentLoaded', async function() {
    gameClient = new GameClient();
    
    try {
        // Connect to server
        await gameClient.connect();
        updateConnectionStatus('connected');
        
        // Setup event handlers
        setupEventHandlers();
        
        // Check if we're on the admin page
        const adminLoginScreen = document.getElementById('admin-login-screen');
        if (adminLoginScreen) {
            // We're on the admin page - ensure admin panel is hidden and login screen is visible
            hideAllScreens();
            adminLoginScreen.classList.remove('hidden');
            console.log('Admin page detected, showing login form only');
        } else {
            // On main page - always start with home screen showing only join game
            // Even if there's existing game state, let user choose to reconnect or start fresh
            showHome();
            
            // Check for existing game state but don't auto-reconnect
            const gameState = gameClient.getGameState();
            if (gameState.gameId) {
                console.log('Found existing game state:', gameState);
                // The reconnection logic will handle showing rejoin prompt if appropriate
            }
        }
        
    } catch (error) {
        console.error('Failed to connect:', error);
        updateConnectionStatus('disconnected');
    }
});

// Setup WebSocket event handlers
function setupEventHandlers() {
    // Team joined successfully
    gameClient.on('team_joined', (data) => {
        showAlert('success', `Successfully joined as ${data.team_name}!`);
        document.getElementById('current-game-id').textContent = data.game_id;
        document.getElementById('current-team-name').textContent = data.team_name;
        // Only show waiting room after successful team join
        showWaitingRoom();
    });
    
    // Team list updated
    gameClient.on('team_list_update', (data) => {
        updateTeamsList(data.teams);
    });
    
    // Game started
    gameClient.on('game_started', (data) => {
        showAlert('success', 'Game has started!');
        const gameState = gameClient.getGameState();
        if (gameState.isAdmin) {
            // Transition admin to game control panel
            showAdminGamePanel();
            updateAdminGameStatus('in_progress');
        } else {
            // Only show game screen when game actually starts
            showGameScreen();
        }
    });
    
    // Question started
    gameClient.on('question_started', (data) => {
        displayQuestion(data);
        
        // Clear previous answers for admin when new question starts
        const answersList = document.getElementById('answers-list');
        if (answersList) {
            answersList.innerHTML = '';
        }
        
        // Hide answers panel until answers are submitted
        const answersPanel = document.getElementById('answers-panel');
        if (answersPanel) {
            answersPanel.classList.add('hidden');
        }
    });
    
    // Answer submitted
    gameClient.on('answer_submitted', (data) => {
        if (data.team_name) {
            // Admin view - show answer was submitted with details
            showAlert('info', `${data.team_name} submitted an answer`);
            
            // Add answer to the admin answers panel with automatic correctness detection
            addAnswerToAdminPanel(data);
        } else {
            // Team view - show confirmation
            document.getElementById('answer-form').classList.add('hidden');
            document.getElementById('answer-submitted').classList.remove('hidden');
        }
    });
    
    // Question closed
    gameClient.on('question_closed', (data) => {
        if (data.answers) {
            // Admin view - show submitted answers for grading
            displayAnswersForGrading(data.answers);
        } else {
            // Team view - show waiting for results
            document.getElementById('question-display').classList.add('hidden');
            document.getElementById('question-closed').classList.remove('hidden');
        }
        
        const gameState = gameClient.getGameState();
        if (gameState.isAdmin) {
            updateAdminControls('question_closed');
        }
    });
    
    // Answer graded
    gameClient.on('answer_graded', (data) => {
        showAlert(data.is_correct ? 'success' : 'error', 
                 `${data.team_name}: ${data.is_correct ? 'Correct' : 'Incorrect'} (+${data.points_awarded} points)`);
        
        // Update leaderboard
        gameClient.getLeaderboard();
    });
    
    // Leaderboard updated
    gameClient.on('leaderboard_update', (data) => {
        updateLeaderboard(data.leaderboard);
    });
    
    // Game finished
    gameClient.on('game_finished', (data) => {
        // Only show game finished screen when all questions are done
        showGameFinished(data.final_leaderboard);
    });
    
    // Success messages
    gameClient.on('success', (data) => {
        console.log('Success event received:', data);
        if (data.is_admin) {
            // Admin logged in successfully
            adminPassword = document.getElementById('admin-password').value;
            console.log('Setting adminPassword to:', adminPassword);
            gameClient.gameState.adminPassword = adminPassword;
            gameClient.saveGameState();
            
            // Hide login form and show pre-game admin panel
            hideAdminError();
            document.getElementById('admin-login-screen').classList.add('hidden');
            document.getElementById('admin-current-game-id').textContent = data.game_id;
            
            // Add temporary visual debug message
            const debugMessage = document.createElement('div');
            debugMessage.style.cssText = 'position:fixed; top:10px; right:10px; background:green; color:white; padding:10px; z-index:9999; border-radius:5px;';
            debugMessage.textContent = `Admin logged in! Password: ${adminPassword}`;
            document.body.appendChild(debugMessage);
            setTimeout(() => debugMessage.remove(), 5000);
            
            showAdminPreGamePanel();
            console.log('Admin pre-game panel should now be visible');
        } else if (data.message) {
            showAlert('success', data.message);
        }
        
        const gameState = gameClient.getGameState();
        if (gameState.isAdmin) {
            updateAdminControls(gameState.gameStatus);
        }
    });
    
    // Error messages
    gameClient.on('error', (data) => {
        // Check if we're on the admin page and show admin-specific error
        const adminLoginScreen = document.getElementById('admin-login-screen');
        if (adminLoginScreen && !adminLoginScreen.classList.contains('hidden')) {
            showAdminError(data.message);
        } else {
            showAlert('error', data.message);
        }
    });
    
    // Connection events
    gameClient.socket.on('connect', () => {
        updateConnectionStatus('connected');
    });
    
    gameClient.socket.on('disconnect', () => {
        updateConnectionStatus('reconnecting');
    });
}

// UI Navigation Functions
function showHome() {
    hideAllScreens();
    document.getElementById('home-screen').classList.remove('hidden');
    document.getElementById('player-join-form').classList.remove('hidden');
    
    // Hide any admin-specific elements that might exist
    const adminLoginForm = document.getElementById('admin-login-form');
    if (adminLoginForm) {
        adminLoginForm.classList.add('hidden');
    }
}

function showPlayerJoin() {
    document.getElementById('player-join-form').classList.remove('hidden');
    document.getElementById('admin-login-form').classList.add('hidden');
    
    // Pre-fill if we have saved state
    const gameState = gameClient.getGameState();
    if (gameState.gameId) {
        document.getElementById('game-id').value = gameState.gameId;
    }
    if (gameState.teamName) {
        document.getElementById('team-name').value = gameState.teamName;
    }
}

function showAdminLogin() {
    document.getElementById('admin-login-form').classList.remove('hidden');
    document.getElementById('player-join-form').classList.add('hidden');
    
    // Pre-fill if we have saved state
    const gameState = gameClient.getGameState();
    if (gameState.gameId) {
        document.getElementById('admin-game-id').value = gameState.gameId;
    }
}

function showWaitingRoom() {
    hideAllScreens();
    const waitingRoom = document.getElementById('waiting-room');
    waitingRoom.classList.remove('hidden');
    waitingRoom.style.display = 'block'; // Override the !important hidden style
    
    // Request current team list
    gameClient.getLeaderboard();
}

function showGameScreen() {
    hideAllScreens();
    const gameScreen = document.getElementById('game-screen');
    gameScreen.classList.remove('hidden');
    gameScreen.style.display = 'block'; // Override the !important hidden style
    
    // Show game status and leaderboard initially 
    // Question will be shown when admin starts a question
    document.getElementById('game-status').textContent = 'Game in Progress - Waiting for first question';
    
    // Hide question-specific elements initially
    document.getElementById('question-display').classList.add('hidden');
    document.getElementById('question-closed').classList.add('hidden');
    document.getElementById('results-display').classList.add('hidden');
    
    // Show leaderboard section so players can see the screen is working
    const leaderboard = document.getElementById('leaderboard');
    if (leaderboard) {
        leaderboard.style.display = 'block';
    }
    
    // Request current leaderboard
    gameClient.getLeaderboard();
}

function showAdminPreGamePanel() {
    hideAllScreens();
    const adminPanel = document.getElementById('admin-pregame-panel');
    
    // Check if admin panel exists (only on admin.html)
    if (!adminPanel) {
        console.warn('showAdminPreGamePanel called but admin-pregame-panel element not found. Likely on player page.');
        return;
    }
    
    adminPanel.classList.remove('hidden');
    adminPanel.style.display = 'block'; // Override the !important hidden style
    
    // Add visual debug indicator
    console.log('Admin pre-game panel shown');
    
    // Ensure start game button is clickable by adding event listener as backup
    const startGameBtn = document.getElementById('start-game-btn');
    if (startGameBtn) {
        console.log('Start game button found, ensuring it\'s clickable');
        startGameBtn.style.cursor = 'pointer';
        startGameBtn.style.opacity = '1';
        startGameBtn.disabled = false;
        
        // Add event listener as backup to onclick
        startGameBtn.removeEventListener('click', startGame); // Remove any existing listener
        startGameBtn.addEventListener('click', startGame);
        console.log('Event listener added to start game button');
    } else {
        console.error('Start game button not found!');
    }
    
    // Request current game state and team list
    updateAdminPreGameInfo();
    
    // Force enable start game button after any potential admin controls update
    setTimeout(() => {
        if (startGameBtn) {
            startGameBtn.disabled = false;
            console.log('Start game button force-enabled after admin info update');
        }
    }, 100);
}

function showAdminGamePanel() {
    hideAllScreens();
    const adminPanel = document.getElementById('admin-game-panel');
    
    // Check if admin panel exists (only on admin.html)
    if (!adminPanel) {
        console.warn('showAdminGamePanel called but admin-game-panel element not found. Likely on player page.');
        return;
    }
    
    adminPanel.classList.remove('hidden');
    adminPanel.style.display = 'block'; // Override the !important hidden style
    
    // Request current game state
    updateAdminGameInfo();
}

// Legacy function for backward compatibility
function showAdminPanel() {
    // Determine which admin panel to show based on game state
    const gameState = gameClient.getGameState();
    if (gameState.gameStatus === 'waiting') {
        showAdminPreGamePanel();
    } else {
        showAdminGamePanel();
    }
}

function showGameFinished(leaderboard) {
    hideAllScreens();
    const gameFinished = document.getElementById('game-finished');
    gameFinished.classList.remove('hidden');
    gameFinished.style.display = 'block'; // Override the !important hidden style
    updateFinalLeaderboard(leaderboard);
}

function hideAllScreens() {
    const screens = ['home-screen', 'waiting-room', 'game-screen', 'admin-pregame-panel', 'admin-game-panel', 'game-finished', 'admin-login-screen'];
    screens.forEach(screenId => {
        const element = document.getElementById(screenId);
        if (element) {
            element.classList.add('hidden');
        }
    });
}

// Game Actions
async function joinGame() {
    const gameId = document.getElementById('game-id').value.trim();
    const teamName = document.getElementById('team-name').value.trim();
    
    if (!gameId || !teamName) {
        showAlert('error', 'Please enter both Game ID and Team Name');
        return;
    }
    
    try {
        gameClient.joinGame(gameId, teamName);
    } catch (error) {
        showAlert('error', 'Failed to join game: ' + error.message);
    }
}

async function adminLogin() {
    const gameId = document.getElementById('admin-game-id').value.trim();
    const password = document.getElementById('admin-password').value.trim();
    
    // Clear any existing errors
    hideAdminError();
    
    if (!gameId || !password) {
        showAdminError('Please enter both Game ID and Password');
        return;
    }
    
    // Check if gameClient exists
    if (!gameClient) {
        showAdminError('Game client not initialized. Please refresh the page.');
        return;
    }
    
    try {
        gameClient.adminLogin(gameId, password);
    } catch (error) {
        showAdminError('Failed to login: ' + error.message);
    }
}

function startGame() {
    console.log('startGame() called');
    console.log('adminPassword:', adminPassword);
    console.log('gameClient:', gameClient);
    
    if (!adminPassword) {
        console.error('Admin password not available!');
        showAlert('error', 'Admin password not available');
        return;
    }
    
    try {
        console.log('Calling gameClient.startGame() with password:', adminPassword);
        gameClient.startGame(adminPassword);
        showAlert('info', 'Starting game...');
        // Transition to game control panel will happen when game_started event is received
    } catch (error) {
        console.error('Error in startGame():', error);
        showAlert('error', 'Failed to start game: ' + error.message);
    }
}

function startQuestion() {
    if (!adminPassword) {
        showAlert('error', 'Admin password not available');
        return;
    }
    
    try {
        gameClient.startQuestion(adminPassword);
        showAlert('info', 'Starting question...');
    } catch (error) {
        showAlert('error', 'Failed to start question: ' + error.message);
    }
}

function submitAnswer() {
    const answer = document.getElementById('answer-input').value.trim();
    
    if (!answer) {
        showAlert('error', 'Please enter an answer');
        return;
    }
    
    try {
        gameClient.submitAnswer(answer);
        document.getElementById('submit-btn').disabled = true;
    } catch (error) {
        showAlert('error', 'Failed to submit answer: ' + error.message);
    }
}

function closeQuestion() {
    if (!adminPassword) {
        showAlert('error', 'Admin password not available');
        return;
    }
    
    try {
        gameClient.closeQuestion(adminPassword);
        showAlert('info', 'Closing question...');
    } catch (error) {
        showAlert('error', 'Failed to close question: ' + error.message);
    }
}

function gradeAnswer(teamId, roundNum, questionNum, isCorrect) {
    try {
        gameClient.gradeAnswer(teamId, roundNum, questionNum, isCorrect, 1);
    } catch (error) {
        showAlert('error', 'Failed to grade answer: ' + error.message);
    }
}

function nextQuestion() {
    if (!adminPassword) {
        showAlert('error', 'Admin password not available');
        return;
    }
    
    try {
        gameClient.nextQuestion(adminPassword);
        showAlert('info', 'Moving to next question...');
        
        // Hide current question display
        document.getElementById('admin-question-display').classList.add('hidden');
        document.getElementById('answers-panel').classList.add('hidden');
    } catch (error) {
        showAlert('error', 'Failed to move to next question: ' + error.message);
    }
}

function previousQuestion() {
    // Note: This function would need backend support to implement
    // For now, just show a message
    showAlert('info', 'Previous question navigation would need backend implementation');
}

function leaveGame() {
    if (confirm('Are you sure you want to leave the game?')) {
        gameClient.clearGameState();
        gameClient.disconnect();
        showHome();
        showAlert('info', 'Left the game');
        
        // Reconnect for future games
        setTimeout(async () => {
            try {
                await gameClient.connect();
                updateConnectionStatus('connected');
            } catch (error) {
                console.error('Failed to reconnect:', error);
            }
        }, 1000);
    }
}

function startNewGame() {
    gameClient.clearGameState();
    showHome();
}

// Display Functions
function displayQuestion(data) {
    const gameState = gameClient.getGameState();
    
    if (gameState.isAdmin) {
        // Admin view - check if admin elements exist (only on admin.html)
        const adminQuestionRound = document.getElementById('admin-question-round');
        const adminQuestionNumber = document.getElementById('admin-question-number');
        const adminQuestionText = document.getElementById('admin-question-text');
        const adminCorrectAnswer = document.getElementById('admin-correct-answer');
        const adminQuestionDisplay = document.getElementById('admin-question-display');
        
        if (!adminQuestionRound || !adminQuestionNumber || !adminQuestionText || !adminCorrectAnswer || !adminQuestionDisplay) {
            console.warn('displayQuestion called for admin but admin elements not found. Likely on player page. Falling back to player view.');
            // Fall through to player view
        } else {
            // Admin elements exist, populate them
            adminQuestionRound.textContent = data.round;
            adminQuestionNumber.textContent = data.question_num;
            adminQuestionText.textContent = data.question;
            adminCorrectAnswer.textContent = data.answer || 'N/A';
            adminQuestionDisplay.classList.remove('hidden');
            updateAdminControls('question_active');
            return; // Exit early for admin view
        }
    }
    
    // Player view (or fallback from admin view)
    {
        // Team view - ensure we're showing the game screen first
        const gameScreen = document.getElementById('game-screen');
        if (gameScreen && gameScreen.classList.contains('hidden')) {
            showGameScreen();
        }
        
        // Update game status to show question is active
        const gameStatus = document.getElementById('game-status');
        if (gameStatus) {
            gameStatus.textContent = 'Question Active - Submit your answer!';
        }
        
        // Display the question with null checks
        const questionRound = document.getElementById('question-round');
        const questionNumber = document.getElementById('question-number');
        const questionText = document.getElementById('question-text');
        const answerInput = document.getElementById('answer-input');
        const submitBtn = document.getElementById('submit-btn');
        const questionDisplay = document.getElementById('question-display');
        const answerForm = document.getElementById('answer-form');
        const answerSubmitted = document.getElementById('answer-submitted');
        const questionClosed = document.getElementById('question-closed');
        
        if (questionRound) questionRound.textContent = data.round;
        if (questionNumber) questionNumber.textContent = data.question_num;
        if (questionText) questionText.textContent = data.question;
        
        // Reset answer form
        if (answerInput) answerInput.value = '';
        if (submitBtn) submitBtn.disabled = false;
        
        // Show question and answer form
        if (questionDisplay) questionDisplay.classList.remove('hidden');
        if (answerForm) answerForm.classList.remove('hidden');
        if (answerSubmitted) answerSubmitted.classList.add('hidden');
        if (questionClosed) questionClosed.classList.add('hidden');
    }
}

function displayAnswersForGrading(answers) {
    const answersList = document.getElementById('answers-list');
    answersList.innerHTML = '';
    
    answers.forEach(answer => {
        const answerItem = document.createElement('div');
        answerItem.className = 'answer-item';
        answerItem.innerHTML = `
            <div>
                <div class="team-name">${answer.team_name}</div>
                <div class="answer-text">"${answer.answer}"</div>
            </div>
            <div class="grading-buttons">
                <button class="btn btn-success" onclick="gradeAnswer('${answer.team_id}', ${gameClient.gameState.currentQuestion.round}, ${gameClient.gameState.currentQuestion.question_num}, true)">
                    ✓ Correct
                </button>
                <button class="btn btn-danger" onclick="gradeAnswer('${answer.team_id}', ${gameClient.gameState.currentQuestion.round}, ${gameClient.gameState.currentQuestion.question_num}, false)">
                    ✗ Incorrect
                </button>
            </div>
        `;
        answersList.appendChild(answerItem);
    });
    
    document.getElementById('answers-panel').classList.remove('hidden');
}

function updateTeamsList(teams) {
    const teamsList = document.getElementById('teams-list');
    const adminTeamsList = document.getElementById('admin-teams-list');
    
    // Update waiting room teams list
    if (teamsList) {
        teamsList.innerHTML = '';
        teams.forEach(team => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${team.name}</span>
                <span class="team-score">${team.score} points</span>
            `;
            teamsList.appendChild(li);
        });
    }
    
    // Update admin teams list
    if (adminTeamsList) {
        adminTeamsList.innerHTML = '';
        teams.forEach(team => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${team.name}</span>
                <span class="team-score">${team.score} points</span>
            `;
            adminTeamsList.appendChild(li);
        });
        
        // Update team count in pre-game panel
        const teamCountElement = document.getElementById('admin-team-count');
        if (teamCountElement) {
            teamCountElement.textContent = teams.length;
        }
        
        // Update team count in game control panel
        const teamCountControlElement = document.getElementById('admin-team-count-control');
        if (teamCountControlElement) {
            teamCountControlElement.textContent = teams.length;
        }
        
        // Show/hide no teams message
        const noTeamsMessage = document.getElementById('no-teams-message');
        if (noTeamsMessage) {
            if (teams.length === 0) {
                noTeamsMessage.style.display = 'block';
            } else {
                noTeamsMessage.style.display = 'none';
            }
        }
    }
}

function updateLeaderboard(leaderboard) {
    const leaderboardList = document.getElementById('leaderboard-list');
    if (!leaderboardList) return;
    
    leaderboardList.innerHTML = '';
    
    leaderboard.forEach((team, index) => {
        const li = document.createElement('li');
        li.className = 'leaderboard-item';
        
        let rankClass = '';
        if (index === 0) rankClass = 'first';
        else if (index === 1) rankClass = 'second';
        else if (index === 2) rankClass = 'third';
        
        li.innerHTML = `
            <div style="display: flex; align-items: center; gap: 15px;">
                <span class="rank ${rankClass}">#${index + 1}</span>
                <span>${team.name}</span>
            </div>
            <span class="team-score">${team.score}</span>
        `;
        leaderboardList.appendChild(li);
    });
}

function updateFinalLeaderboard(leaderboard) {
    const finalLeaderboard = document.getElementById('final-leaderboard');
    if (!finalLeaderboard) return;
    
    finalLeaderboard.innerHTML = '';
    
    leaderboard.forEach((team, index) => {
        const li = document.createElement('li');
        li.className = 'leaderboard-item';
        
        let rankClass = '';
        let medal = '';
        if (index === 0) {
            rankClass = 'first';
            medal = '🥇';
        } else if (index === 1) {
            rankClass = 'second';
            medal = '🥈';
        } else if (index === 2) {
            rankClass = 'third';
            medal = '🥉';
        }
        
        li.innerHTML = `
            <div style="display: flex; align-items: center; gap: 15px;">
                <span class="rank ${rankClass}">${medal} #${index + 1}</span>
                <span>${team.name}</span>
            </div>
            <span class="team-score">${team.score}</span>
        `;
        finalLeaderboard.appendChild(li);
    });
}

function updateAdminPreGameInfo() {
    // Initialize admin team count
    document.getElementById('admin-team-count').textContent = '0';
    
    // Request current team list to populate admin view
    gameClient.getLeaderboard();
}

function updateAdminGameInfo() {
    // Initialize admin team count for game control panel
    const teamCountElement = document.getElementById('admin-team-count-control');
    if (teamCountElement) {
        teamCountElement.textContent = '0';
    }
    
    // Update game ID in control panel
    const gameState = gameClient.getGameState();
    const gameIdElement = document.getElementById('admin-current-game-id-control');
    if (gameIdElement && gameState.gameId) {
        gameIdElement.textContent = gameState.gameId;
    }
    
    // This would be populated from game state or server response
    if (gameState.currentQuestion) {
        document.getElementById('admin-current-round').textContent = gameState.currentQuestion.round;
        document.getElementById('admin-current-question').textContent = gameState.currentQuestion.question_num;
    }
    
    // Request current team list and update controls
    gameClient.getLeaderboard();
}

// Legacy function for backward compatibility
function updateAdminInfo() {
    const gameState = gameClient.getGameState();
    if (gameState.gameStatus === 'waiting') {
        updateAdminPreGameInfo();
    } else {
        updateAdminGameInfo();
    }
}

function updateAdminGameStatus(status) {
    const statusElement = document.getElementById('admin-game-status');
    
    // Check if admin status element exists (only on admin.html)
    if (!statusElement) {
        console.warn('updateAdminGameStatus called but admin-game-status element not found. Likely on player page.');
        return;
    }
    
    statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusElement.className = `status ${status.replace('_', '-')}`;
    
    updateAdminControls(status);
}

function updateAdminControls(gameStatus) {
    const startGameBtn = document.getElementById('start-game-btn');
    const startQuestionBtn = document.getElementById('start-question-btn');
    const closeQuestionBtn = document.getElementById('close-question-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    const previousQuestionBtn = document.getElementById('previous-question-btn');
    
    // Don't disable start game button if we're in pre-game panel
    const preGamePanel = document.getElementById('admin-pregame-panel');
    const isPreGamePanelVisible = preGamePanel && !preGamePanel.classList.contains('hidden') && preGamePanel.style.display !== 'none';
    
    // Reset all buttons except start game button if we're in pre-game
    [startQuestionBtn, closeQuestionBtn, nextQuestionBtn, previousQuestionBtn].forEach(btn => {
        if (btn) btn.disabled = true;
    });
    
    // Only disable start game button if we're not in pre-game panel
    if (startGameBtn && !isPreGamePanelVisible) {
        startGameBtn.disabled = true;
    }
    
    switch (gameStatus) {
        case 'waiting':
            if (startGameBtn) startGameBtn.disabled = false;
            break;
        case 'in_progress':
        case 'in-progress':
            if (startQuestionBtn) startQuestionBtn.disabled = false;
            // Enable previous question button if we're not on the first question
            // This would need proper implementation based on current question state
            if (previousQuestionBtn) previousQuestionBtn.disabled = false;
            break;
        case 'question_active':
        case 'question-active':
            if (closeQuestionBtn) closeQuestionBtn.disabled = false;
            break;
        case 'question_closed':
        case 'question-closed':
            if (nextQuestionBtn) nextQuestionBtn.disabled = false;
            break;
    }
    
    // Ensure start game button stays enabled in pre-game panel
    if (startGameBtn && isPreGamePanelVisible) {
        startGameBtn.disabled = false;
    }
}

// Utility Functions
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    statusElement.className = `connection-status ${status}`;
    
    switch (status) {
        case 'connected':
            statusElement.textContent = '✓ Connected';
            break;
        case 'disconnected':
            statusElement.textContent = '✗ Disconnected';
            break;
        case 'reconnecting':
            statusElement.textContent = '⟳ Reconnecting...';
            break;
    }
}

function showAlert(type, message) {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    alert.textContent = message;
    
    // Insert at top of current screen
    const currentScreen = document.querySelector('.card:not(.hidden)');
    if (currentScreen) {
        currentScreen.insertBefore(alert, currentScreen.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
}

// Admin-specific error handling functions
function showAdminError(message) {
    const errorDiv = document.getElementById('admin-error');
    const errorMessage = document.getElementById('admin-error-message');
    
    if (errorDiv && errorMessage) {
        errorMessage.textContent = message;
        errorDiv.classList.remove('hidden');
    }
}

function hideAdminError() {
    const errorDiv = document.getElementById('admin-error');
    if (errorDiv) {
        errorDiv.classList.add('hidden');
    }
}

function addAnswerToAdminPanel(data) {
    // Show the answers panel if it's hidden
    const answersPanel = document.getElementById('answers-panel');
    if (answersPanel) {
        answersPanel.classList.remove('hidden');
    }
    
    // Get the answers list container
    const answersList = document.getElementById('answers-list');
    if (!answersList) return;
    
    // Create answer item element
    const answerItem = document.createElement('div');
    answerItem.className = 'answer-item';
    answerItem.setAttribute('data-team-id', data.team_id);
    
    // Determine correctness styling
    const correctnessClass = data.is_auto_correct ? 'auto-correct' : 'auto-incorrect';
    const correctnessIcon = data.is_auto_correct ? '✅' : '❌';
    const correctnessText = data.is_auto_correct ? 'Auto-detected: Correct' : 'Auto-detected: Incorrect';
    
    answerItem.innerHTML = `
        <div class="answer-header">
            <strong>${data.team_name}</strong>
            <span class="answer-time">${new Date(data.submitted_at * 1000).toLocaleTimeString()}</span>
        </div>
        <div class="answer-content">
            <div class="submitted-answer">
                <strong>Answer:</strong> <span class="answer-text">${data.answer}</span>
            </div>
            <div class="correctness-info ${correctnessClass}">
                ${correctnessIcon} ${correctnessText}
                <small>(Correct answer: ${data.correct_answer})</small>
            </div>
        </div>
        <div class="grading-controls">
            <button class="btn btn-sm btn-success" onclick="gradeAnswer('${data.team_id}', true, 1)">✅ Mark Correct</button>
            <button class="btn btn-sm btn-danger" onclick="gradeAnswer('${data.team_id}', false, 0)">❌ Mark Incorrect</button>
        </div>
    `;
    
    // Add the answer to the list
    answersList.appendChild(answerItem);
}

function gradeAnswer(teamId, isCorrect, points) {
    // This function will be called when admin clicks grading buttons
    try {
        // Get current game state to determine round and question
        const gameState = gameClient.getGameState();
        
        // We need to get the current round and question from the admin panel or game state
        // For now, we'll try to get it from the DOM elements
        const currentRound = document.getElementById('admin-current-round')?.textContent || '1';
        const currentQuestion = document.getElementById('admin-current-question')?.textContent || '1';
        
        gameClient.gradeAnswer(teamId, parseInt(currentRound), parseInt(currentQuestion), isCorrect, points);
        
        // Update the answer item to show it's been graded
        const answerItem = document.querySelector(`[data-team-id="${teamId}"]`);
        if (answerItem) {
            const gradingControls = answerItem.querySelector('.grading-controls');
            if (gradingControls) {
                gradingControls.innerHTML = `
                    <span class="graded-status ${isCorrect ? 'correct' : 'incorrect'}">
                        ${isCorrect ? '✅ Marked Correct' : '❌ Marked Incorrect'} 
                        (${points} point${points !== 1 ? 's' : ''})
                    </span>
                `;
            }
        }
        
        showAlert('success', `Answer graded as ${isCorrect ? 'correct' : 'incorrect'}`);
    } catch (error) {
        console.error('Error grading answer:', error);
        showAlert('error', 'Failed to grade answer: ' + error.message);
    }
}

// Handle page visibility changes (for reconnection)
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && gameClient && !gameClient.socket?.connected) {
        console.log('Page became visible, attempting to reconnect...');
        gameClient.connect().catch(console.error);
    }
});

// Handle beforeunload to save state
window.addEventListener('beforeunload', function() {
    if (gameClient) {
        gameClient.saveGameState();
    }
});
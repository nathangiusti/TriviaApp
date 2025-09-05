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
        
        // Check for existing game state
        const gameState = gameClient.getGameState();
        if (gameState.gameId) {
            // User has existing game state, will be handled by reconnection logic
            console.log('Found existing game state:', gameState);
        } else {
            // Show home screen for new users
            showHome();
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
            updateAdminGameStatus('in_progress');
        } else {
            showGameScreen();
        }
    });
    
    // Question started
    gameClient.on('question_started', (data) => {
        displayQuestion(data);
    });
    
    // Answer submitted
    gameClient.on('answer_submitted', (data) => {
        if (data.team_name) {
            // Admin view - show answer was submitted
            showAlert('info', `${data.team_name} submitted an answer`);
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
        showGameFinished(data.final_leaderboard);
    });
    
    // Success messages
    gameClient.on('success', (data) => {
        if (data.is_admin) {
            // Admin logged in successfully
            adminPassword = document.getElementById('admin-password').value;
            gameClient.gameState.adminPassword = adminPassword;
            gameClient.saveGameState();
            
            document.getElementById('admin-current-game-id').textContent = data.game_id;
            showAdminPanel();
            showAlert('success', 'Admin login successful!');
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
        showAlert('error', data.message);
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
    document.getElementById('player-join-form').classList.add('hidden');
    document.getElementById('admin-login-form').classList.add('hidden');
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
    document.getElementById('waiting-room').classList.remove('hidden');
    
    // Request current team list
    gameClient.getLeaderboard();
}

function showGameScreen() {
    hideAllScreens();
    document.getElementById('game-screen').classList.remove('hidden');
    
    // Request current leaderboard
    gameClient.getLeaderboard();
}

function showAdminPanel() {
    hideAllScreens();
    document.getElementById('admin-panel').classList.remove('hidden');
    
    // Request current game state
    updateAdminInfo();
}

function showGameFinished(leaderboard) {
    hideAllScreens();
    document.getElementById('game-finished').classList.remove('hidden');
    updateFinalLeaderboard(leaderboard);
}

function hideAllScreens() {
    const screens = ['home-screen', 'waiting-room', 'game-screen', 'admin-panel', 'game-finished'];
    screens.forEach(screenId => {
        document.getElementById(screenId).classList.add('hidden');
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
    
    if (!gameId || !password) {
        showAlert('error', 'Please enter both Game ID and Password');
        return;
    }
    
    try {
        gameClient.adminLogin(gameId, password);
    } catch (error) {
        showAlert('error', 'Failed to login: ' + error.message);
    }
}

function startGame() {
    if (!adminPassword) {
        showAlert('error', 'Admin password not available');
        return;
    }
    
    try {
        gameClient.startGame(adminPassword);
        showAlert('info', 'Starting game...');
    } catch (error) {
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
        // Admin view
        document.getElementById('admin-question-round').textContent = data.round;
        document.getElementById('admin-question-number').textContent = data.question_num;
        document.getElementById('admin-question-text').textContent = data.question;
        document.getElementById('admin-correct-answer').textContent = data.answer || 'N/A';
        document.getElementById('admin-question-display').classList.remove('hidden');
        updateAdminControls('question_active');
    } else {
        // Team view
        document.getElementById('question-round').textContent = data.round;
        document.getElementById('question-number').textContent = data.question_num;
        document.getElementById('question-text').textContent = data.question;
        
        // Reset answer form
        document.getElementById('answer-input').value = '';
        document.getElementById('submit-btn').disabled = false;
        
        // Show question and answer form
        document.getElementById('question-display').classList.remove('hidden');
        document.getElementById('answer-form').classList.remove('hidden');
        document.getElementById('answer-submitted').classList.add('hidden');
        document.getElementById('question-closed').classList.add('hidden');
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
        
        document.getElementById('admin-team-count').textContent = teams.length;
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

function updateAdminInfo() {
    // This would be populated from game state or server response
    const gameState = gameClient.getGameState();
    if (gameState.currentQuestion) {
        document.getElementById('admin-current-round').textContent = gameState.currentQuestion.round;
        document.getElementById('admin-current-question').textContent = gameState.currentQuestion.question_num;
    }
}

function updateAdminGameStatus(status) {
    const statusElement = document.getElementById('admin-game-status');
    statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusElement.className = `status ${status.replace('_', '-')}`;
    
    updateAdminControls(status);
}

function updateAdminControls(gameStatus) {
    const startGameBtn = document.getElementById('start-game-btn');
    const startQuestionBtn = document.getElementById('start-question-btn');
    const closeQuestionBtn = document.getElementById('close-question-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    
    // Reset all buttons
    [startGameBtn, startQuestionBtn, closeQuestionBtn, nextQuestionBtn].forEach(btn => {
        if (btn) btn.disabled = true;
    });
    
    switch (gameStatus) {
        case 'waiting':
            if (startGameBtn) startGameBtn.disabled = false;
            break;
        case 'in_progress':
        case 'in-progress':
            if (startQuestionBtn) startQuestionBtn.disabled = false;
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
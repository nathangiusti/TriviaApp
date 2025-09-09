// Admin-specific application logic
let gameClient;
let adminPassword = '';
let currentTeams = [];

// Initialize the admin application
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Admin app initializing...');
    
    try {
        gameClient = new GameClient();
        await gameClient.connect();
        setupAdminEventHandlers();
        initializeAdminUI();
        setupAdminUIEventListeners(); // Add UI event listeners
        exposeAdminFunctionsGlobally(); // Make functions available globally for backward compatibility
        updateConnectionStatus('connected'); // Set initial connection status
    } catch (error) {
        console.error('Failed to initialize admin app:', error);
        showAlert('error', 'Failed to connect to server');
    }
});

// Setup admin-specific event handlers
function setupAdminEventHandlers() {
    // Connection status updates
    gameClient.on('connected', () => {
        updateConnectionStatus('connected');
    });
    
    gameClient.on('disconnect', () => {
        updateConnectionStatus('disconnected');
    });
    
    gameClient.on('reconnecting', () => {
        updateConnectionStatus('reconnecting');
    });
    // Game started - show admin game panel
    gameClient.on('game_started', (data) => {
        showAlert('success', 'Game has started!');
        showAdminGamePanel();
        updateAdminGameStatus('in_progress');
    });
    
    // Question started - display admin question view and setup grading interface
    gameClient.on('question_started', (data) => {
        displayAdminQuestion(data);
        setupGradingInterface();
    });
    
    // Answer submitted - update grading interface
    gameClient.on('answer_submitted', (data) => {
        if (data.team_name) {
            console.log('Answer received from', data.team_name, ':', data.answer);
            updateTeamAnswerInGrading(data);
        }
    });
    
    // Question closed
    gameClient.on('question_closed', (data) => {
        updateAdminGameStatus('question_closed');
        updateAdminControls('question_closed');
        hideGradingInterface();
    });
    
    // Team list updates
    gameClient.on('team_list_update', (data) => {
        updateAdminTeamsList(data.teams);
    });
    
    // Leaderboard updates
    gameClient.on('leaderboard_update', (data) => {
        updateAdminLeaderboard(data.leaderboard);
    });
    
    // Success responses (admin login, etc.)
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
            
            // Show pre-game admin panel
            showAdminPreGamePanel();
            
            // Debug indicator
            const debugMessage = document.createElement('div');
            debugMessage.style.cssText = 'position:fixed; top:10px; right:10px; background:green; color:white; padding:10px; z-index:9999; border-radius:5px;';
            debugMessage.textContent = `Admin logged in! Password: ${adminPassword}`;
            document.body.appendChild(debugMessage);
            setTimeout(() => debugMessage.remove(), 3000);
        } else if (data.message && data.message.includes('Moved to next question')) {
            // Next question was successful - update admin controls back to in_progress state
            console.log('Next question successful, updating admin controls');
            updateAdminGameStatus('in_progress');
            updateAdminControls('in_progress');
        }
    });
    
    // Error handling
    gameClient.on('error', (data) => {
        console.error('Admin error:', data.message);
        const adminLoginScreen = document.getElementById('admin-login-screen');
        if (adminLoginScreen && !adminLoginScreen.classList.contains('hidden')) {
            showAdminError(data.message);
        } else {
            showAlert('error', data.message);
        }
    });
}

// Initialize admin UI
function initializeAdminUI() {
    // Show admin login screen
    hideAllScreens();
    const adminLoginScreen = document.getElementById('admin-login-screen');
    if (adminLoginScreen) {
        adminLoginScreen.classList.remove('hidden');
        adminLoginScreen.style.display = 'block'; // Override display: none from hideAllScreens()
        console.log('Admin page initialized, showing login form');
    }
    
    // Load any saved admin session
    const gameState = gameClient.getGameState();
    if (gameState.gameId && gameState.isAdmin) {
        document.getElementById('admin-game-id').value = gameState.gameId;
        if (gameState.adminPassword) {
            adminPassword = gameState.adminPassword;
        }
    }
}

// Admin UI Management Functions
function showAdminPreGamePanel() {
    hideAllScreens();
    const adminPanel = document.getElementById('admin-pregame-panel');
    
    if (!adminPanel) {
        console.error('Admin pre-game panel not found');
        return;
    }
    
    adminPanel.classList.remove('hidden');
    adminPanel.style.display = 'block';
    
    // Add visual debug indicator
    console.log('Admin pre-game panel shown');
    
    // Ensure start game button is clickable
    const startGameBtn = document.getElementById('start-game-btn');
    if (startGameBtn) {
        console.log('Start game button found, ensuring it\'s clickable');
        startGameBtn.style.cursor = 'pointer';
        startGameBtn.style.opacity = '1';
        startGameBtn.disabled = false;
        
        // Add event listener as backup to onclick
        startGameBtn.removeEventListener('click', startGame);
        startGameBtn.addEventListener('click', startGame);
        console.log('Event listener added to start game button');
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
    
    if (!adminPanel) {
        console.error('Admin game panel not found');
        return;
    }
    
    adminPanel.classList.remove('hidden');
    adminPanel.style.display = 'block';
    
    // Request current game state
    updateAdminGameInfo();
}

function displayAdminQuestion(data) {
    console.log('Displaying question in admin view');
    
    const adminQuestionRound = document.getElementById('admin-question-round');
    const adminQuestionNumber = document.getElementById('admin-question-number');
    const adminQuestionText = document.getElementById('admin-question-text');
    const adminCorrectAnswer = document.getElementById('admin-correct-answer');
    const adminQuestionDisplay = document.getElementById('admin-question-display');
    
    if (!adminQuestionRound || !adminQuestionNumber || !adminQuestionText || !adminCorrectAnswer || !adminQuestionDisplay) {
        console.error('Admin question elements not found');
        return;
    }
    
    // Admin elements exist, populate them
    adminQuestionRound.textContent = data.round;
    adminQuestionNumber.textContent = data.question_num;
    adminQuestionText.textContent = data.question;
    adminCorrectAnswer.textContent = data.answer || 'N/A';
    adminQuestionDisplay.classList.remove('hidden');
    updateAdminControls('question_active');
}

function updateAdminTeamsList(teams) {
    // Store teams for grading interface
    currentTeams = teams;
    
    const adminTeamsList = document.getElementById('admin-teams-list');
    
    if (adminTeamsList) {
        adminTeamsList.innerHTML = '';
        teams.forEach(team => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="team-name">${team.name}</span>
                <span class="team-score">${team.score} pts</span>
            `;
            adminTeamsList.appendChild(li);
        });
        
        // Update team count in pre-game panel
        const teamCountElement = document.getElementById('admin-team-count');
        if (teamCountElement) {
            teamCountElement.textContent = teams.length.toString();
        }
        
        // Update team count in game control panel
        const teamCountControlElement = document.getElementById('admin-team-count-control');
        if (teamCountControlElement) {
            teamCountControlElement.textContent = teams.length.toString();
        }
    }
}

function updateAdminLeaderboard(leaderboard) {
    const adminLeaderboardList = document.getElementById('admin-leaderboard-list');
    if (adminLeaderboardList) {
        adminLeaderboardList.innerHTML = '';
        leaderboard.forEach((team, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="position">${index + 1}.</span>
                <span class="team-name">${team.name}</span>
                <span class="team-score">${team.score} pts</span>
            `;
            adminLeaderboardList.appendChild(li);
        });
    }
}

function updateAdminPreGameInfo() {
    // Initialize admin team count
    const teamCount = document.getElementById('admin-team-count');
    if (teamCount) {
        teamCount.textContent = '0';
    }
    
    // Request current team list and leaderboard
    gameClient.getLeaderboard();
}

function updateAdminGameInfo() {
    // Request current game state and leaderboard for game control panel
    const teamCountControl = document.getElementById('admin-team-count-control');
    if (teamCountControl) {
        teamCountControl.textContent = '0';
    }
    
    gameClient.getLeaderboard();
}

function updateAdminGameStatus(status) {
    const statusElement = document.getElementById('admin-game-status');
    
    if (!statusElement) {
        console.warn('updateAdminGameStatus called but admin-game-status element not found.');
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

// Grading Interface Functions
function setupGradingInterface() {
    const teams = currentTeams;
    
    const gradingPanel = document.getElementById('grading-panel');
    const teamsGradingList = document.getElementById('teams-grading-list');
    
    if (!gradingPanel || !teamsGradingList) return;
    
    // Clear previous content
    teamsGradingList.innerHTML = '';
    
    // Create grading items for each team
    teams.forEach(team => {
        const teamItem = createTeamGradingItem(team);
        teamsGradingList.appendChild(teamItem);
    });
    
    // Show the grading panel
    gradingPanel.classList.remove('hidden');
}

function createTeamGradingItem(team) {
    const teamDiv = document.createElement('div');
    teamDiv.className = 'team-grading-item';
    const teamId = team.team_id || team.id;
    teamDiv.id = `grading-${teamId}`;
    
    teamDiv.innerHTML = `
        <div class="team-info">
            <div class="team-name-grading">${team.name}</div>
            <div class="team-answer-display" id="answer-${teamId}">
                Waiting for answer...
            </div>
        </div>
        <div class="answer-status">
            <div class="status-indicator waiting" id="status-${teamId}">
                Waiting
            </div>
            <div class="grading-buttons" id="buttons-${teamId}" style="display: none;">
                <button class="btn btn-correct" onclick="gradeAnswer('${teamId}', true)">
                    ✓ Correct
                </button>
                <button class="btn btn-incorrect" onclick="gradeAnswer('${teamId}', false)">
                    ✗ Incorrect
                </button>
            </div>
        </div>
    `;
    
    return teamDiv;
}

function updateTeamAnswerInGrading(data) {
    const teamId = data.team_id;
    const answerElement = document.getElementById(`answer-${teamId}`);
    const statusElement = document.getElementById(`status-${teamId}`);
    const buttonsElement = document.getElementById(`buttons-${teamId}`);
    const teamItem = document.getElementById(`grading-${teamId}`);
    
    if (!answerElement || !statusElement || !buttonsElement || !teamItem) return;
    
    // Update answer display
    answerElement.textContent = `"${data.answer}"`;
    answerElement.className = 'team-answer-display submitted';
    
    // Check if answer is automatically correct
    const correctAnswerElement = document.getElementById('admin-correct-answer');
    const correctAnswer = correctAnswerElement ? correctAnswerElement.textContent : '';
    const isAutoCorrect = data.is_auto_correct || 
        (data.answer.toLowerCase().trim() === correctAnswer.toLowerCase().trim());
    
    // Update team item styling
    teamItem.className = 'team-grading-item has-answer';
    
    if (isAutoCorrect) {
        // Answer is automatically correct
        statusElement.textContent = 'Auto-Correct ✓';
        statusElement.className = 'status-indicator auto-correct';
        teamItem.classList.add('auto-correct');
        buttonsElement.style.display = 'none'; // Hide grading buttons
    } else {
        // Answer needs manual grading
        statusElement.textContent = 'Needs Grading';
        statusElement.className = 'status-indicator waiting';
        buttonsElement.style.display = 'flex'; // Show grading buttons
    }
}

function gradeAnswer(teamId, isCorrect) {
    const gameState = gameClient.getGameState();
    const currentRound = gameState.currentRound || 1;
    const currentQuestion = gameState.currentQuestion || 1;
    
    try {
        // Send grading to server
        gameClient.gradeAnswer(teamId, currentRound, currentQuestion, isCorrect);
        
        // Update UI immediately
        updateGradingUIAfterGrading(teamId, isCorrect);
        
    } catch (error) {
        console.error('Failed to grade answer:', error);
        showAlert('error', 'Failed to grade answer');
    }
}

function updateGradingUIAfterGrading(teamId, isCorrect) {
    const statusElement = document.getElementById(`status-${teamId}`);
    const buttonsElement = document.getElementById(`buttons-${teamId}`);
    const teamItem = document.getElementById(`grading-${teamId}`);
    
    if (!statusElement || !buttonsElement || !teamItem) return;
    
    // Update status
    if (isCorrect) {
        statusElement.textContent = 'Graded: Correct ✓';
        statusElement.className = 'status-indicator graded-correct';
    } else {
        statusElement.textContent = 'Graded: Incorrect ✗';
        statusElement.className = 'status-indicator graded-incorrect';
    }
    
    // Update team item styling
    teamItem.classList.remove('has-answer');
    teamItem.classList.add('manually-graded');
    
    // Hide grading buttons
    buttonsElement.style.display = 'none';
}

function hideGradingInterface() {
    const gradingPanel = document.getElementById('grading-panel');
    if (gradingPanel) {
        gradingPanel.classList.add('hidden');
    }
}

// Admin Action Functions
async function adminLogin() {
    const gameId = document.getElementById('admin-game-id').value.trim();
    const password = document.getElementById('admin-password').value.trim();
    
    if (!gameId || !password) {
        showAdminError('Please enter both Game ID and Admin Password');
        return;
    }
    
    hideAdminError();
    
    // Show loading state
    const loginBtn = document.querySelector('#admin-login-form button');
    const originalText = loginBtn.textContent;
    loginBtn.textContent = 'Logging in...';
    loginBtn.disabled = true;
    
    try {
        gameClient.adminLogin(gameId, password);
    } catch (error) {
        showAdminError(error.message);
        loginBtn.textContent = originalText;
        loginBtn.disabled = false;
    }
}

function startGame() {
    console.log('startGame() called');
    console.log('adminPassword:', adminPassword);
    
    if (!adminPassword) {
        console.error('Admin password not available!');
        showAlert('error', 'Admin password not available. Please login again.');
        return;
    }
    
    try {
        console.log('Calling gameClient.startGame() with password:', adminPassword);
        gameClient.startGame(adminPassword);
        showAlert('info', 'Starting game...');
    } catch (error) {
        console.error('Error starting game:', error);
        showAlert('error', 'Failed to start game');
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
        showAlert('error', 'Failed to start question');
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
        showAlert('error', 'Failed to close question');
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
        const adminQuestionDisplay = document.getElementById('admin-question-display');
        const answersPanel = document.getElementById('answers-panel');
        if (adminQuestionDisplay) adminQuestionDisplay.classList.add('hidden');
        if (answersPanel) answersPanel.classList.add('hidden');
    } catch (error) {
        showAlert('error', 'Failed to move to next question');
    }
}

// Admin Error Handling
function showAdminError(message) {
    const errorDiv = document.getElementById('admin-error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }
}

function hideAdminError() {
    const errorDiv = document.getElementById('admin-error');
    if (errorDiv) {
        errorDiv.classList.add('hidden');
        errorDiv.textContent = '';
    }
}

// Utility Functions (shared between admin and player)
function hideAllScreens() {
    const screens = ['admin-pregame-panel', 'admin-game-panel', 'admin-login-screen'];
    screens.forEach(screenId => {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.add('hidden');
            screen.style.display = 'none';
        }
    });
}

function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    if (!statusElement) return;
    
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
        default:
            statusElement.textContent = status;
    }
}

function showAlert(type, message) {
    // Create or update alert element
    let alertElement = document.getElementById('alert-message');
    if (!alertElement) {
        alertElement = document.createElement('div');
        alertElement.id = 'alert-message';
        alertElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 10000;
            max-width: 300px;
        `;
        document.body.appendChild(alertElement);
    }
    
    // Set alert style based on type
    const colors = {
        success: '#4CAF50',
        error: '#f44336',
        info: '#2196F3',
        warning: '#ff9800'
    };
    
    alertElement.style.backgroundColor = colors[type] || colors.info;
    alertElement.textContent = message;
    alertElement.style.display = 'block';
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        if (alertElement) {
            alertElement.style.display = 'none';
        }
    }, 3000);
}

// Setup UI event listeners for admin interface
function setupAdminUIEventListeners() {
    // Admin login form
    const adminLoginBtn = document.getElementById('admin-login-btn');
    if (adminLoginBtn) {
        adminLoginBtn.addEventListener('click', adminLogin);
    }
    
    // Admin game control buttons
    const startGameBtn = document.getElementById('start-game-btn');
    if (startGameBtn) {
        startGameBtn.addEventListener('click', startGame);
    }
    
    const startQuestionBtn = document.getElementById('start-question-btn');
    if (startQuestionBtn) {
        startQuestionBtn.addEventListener('click', startQuestion);
    }
    
    const closeQuestionBtn = document.getElementById('close-question-btn');
    if (closeQuestionBtn) {
        closeQuestionBtn.addEventListener('click', closeQuestion);
    }
    
    const nextQuestionBtn = document.getElementById('next-question-btn');
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', nextQuestion);
    }
    
    const previousQuestionBtn = document.getElementById('previous-question-btn');
    if (previousQuestionBtn) {
        previousQuestionBtn.addEventListener('click', adminPreviousQuestion);
    }
    
    // Exit admin buttons
    const exitAdminBtn = document.getElementById('exit-admin-btn');
    if (exitAdminBtn) {
        exitAdminBtn.addEventListener('click', adminLeaveGame);
    }
    
    const exitAdminGameBtn = document.getElementById('exit-admin-game-btn');
    if (exitAdminGameBtn) {
        exitAdminGameBtn.addEventListener('click', adminLeaveGame);
    }
    
    // Start new game button
    const startNewGameBtn = document.getElementById('start-new-game-btn');
    if (startNewGameBtn) {
        startNewGameBtn.addEventListener('click', adminStartNewGame);
    }
    
    // Keyboard event listeners for Enter key
    const adminGameIdInput = document.getElementById('admin-game-id');
    if (adminGameIdInput) {
        adminGameIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') adminLogin();
        });
    }
    
    const adminPasswordInput = document.getElementById('admin-password');
    if (adminPasswordInput) {
        adminPasswordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') adminLogin();
        });
    }
}

// Expose admin functions globally for backward compatibility and tests
function exposeAdminFunctionsGlobally() {
    window.adminLogin = adminLogin;
    window.startGame = startGame;
    window.startQuestion = startQuestion;
    window.closeQuestion = closeQuestion;
    window.nextQuestion = nextQuestion;
    window.previousQuestion = adminPreviousQuestion;
    window.leaveGame = adminLeaveGame;
    window.startNewGame = adminStartNewGame;
    window.gradeAnswer = gradeAnswer;
}

// Additional admin functions
function adminPreviousQuestion() {
    showAlert('info', 'Previous question navigation not yet implemented');
}

function adminLeaveGame() {
    if (confirm('Are you sure you want to leave the admin panel?')) {
        gameClient.clearGameState();
        gameClient.disconnect();
        location.reload(); // Reload to reset admin state
    }
}

function adminStartNewGame() {
    gameClient.clearGameState();
    location.reload(); // Reload to start fresh
}
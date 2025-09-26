// Player-specific application logic
let gameClient;

// Initialize the player application
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Player app initializing...');
    
    try {
        gameClient = new GameClient();
        await gameClient.connect();
        setupPlayerEventHandlers();
        initializePlayerUI();
        setupPlayerUIEventListeners(); // Add UI event listeners
        exposePlayerFunctionsGlobally(); // Make functions available globally for backward compatibility
        updateConnectionStatus('connected'); // Set initial connection status
    } catch (error) {
        console.error('Failed to initialize player app:', error);
        showAlert('error', 'Failed to connect to server');
    }
});

// Setup player-specific event handlers
function setupPlayerEventHandlers() {
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
    // Game started - show game screen for players
    gameClient.on('game_started', (data) => {
        showAlert('success', 'Game has started!');
        showGameScreen();
    });
    
    // Question started - display question for players
    gameClient.on('question_started', (data) => {
        displayPlayerQuestion(data);
    });
    
    // Question closed - show results to players
    gameClient.on('question_closed', (data) => {
        console.log('PLAYER: Received question_closed event:', data);
        hideAnswerForm();
        displayQuestionResults(data);
    });
    
    // Answer submitted confirmation
    gameClient.on('answer_submitted', (data) => {
        if (data.team_name === gameClient.getGameState().teamName) {
            showAnswerSubmitted();
            showAlert('success', 'Answer submitted successfully!');
        }
    });
    
    // Team joined successfully
    gameClient.on('team_joined', (data) => {
        console.log('Team joined:', data);
        gameClient.gameState.teamName = data.team_name;
        gameClient.gameState.teamId = data.team_id;
        gameClient.gameState.gameId = data.game_id;
        gameClient.saveGameState();
        
        showAlert('success', `Joined as ${data.team_name}!`);
        showWaitingRoom();
    });
    
    // Team list updates
    gameClient.on('team_list_update', (data) => {
        updatePlayerTeamsList(data.teams);
    });
    
    // Leaderboard updates
    gameClient.on('leaderboard_update', (data) => {
        updatePlayerLeaderboard(data.leaderboard);
    });
    
    // Game finished
    gameClient.on('game_finished', (data) => {
        showGameFinished(data.final_leaderboard);
    });
    
    // Error handling
    gameClient.on('error', (data) => {
        console.error('Player error:', data.message);
        showAlert('error', data.message);
        
        // Handle specific error cases
        if (data.message.includes('Game not found')) {
            showHome();
        }
    });
}

// Initialize player UI
function initializePlayerUI() {
    // Check if we have a saved game state for reconnection
    const gameState = gameClient.getGameState();
    
    if (gameState.teamName && gameState.gameId) {
        // Show reconnection prompt
        showReconnectPrompt();
    } else {
        // Show home screen with join form
        showHome();
    }
}

// Player UI Management Functions
function showHome() {
    hideAllScreens();
    const homeScreen = document.getElementById('home-screen');
    if (homeScreen) {
        homeScreen.classList.remove('hidden');
        homeScreen.style.display = 'block';
        
        // Focus on game ID input for better UX
        const gameIdInput = document.getElementById('game-id');
        if (gameIdInput) {
            gameIdInput.focus();
        }
    }
}

function showWaitingRoom() {
    hideAllScreens();
    const waitingRoom = document.getElementById('waiting-room');
    if (waitingRoom) {
        waitingRoom.classList.remove('hidden');
        waitingRoom.style.display = 'block';
    }
    
    // Request current leaderboard
    gameClient.getLeaderboard();
}

function showGameScreen() {
    hideAllScreens();
    const gameScreen = document.getElementById('game-screen');
    if (gameScreen) {
        gameScreen.classList.remove('hidden');
        gameScreen.style.display = 'block';
    }
    
    // Show game status and leaderboard initially 
    // Question will be shown when admin starts a question
    const gameStatus = document.getElementById('game-status');
    if (gameStatus) {
        gameStatus.textContent = 'Game in Progress - Waiting for first question';
    }
    
    // Request current leaderboard
    gameClient.getLeaderboard();
}

function showGameFinished(finalLeaderboard) {
    hideAllScreens();
    const gameFinished = document.getElementById('game-finished');
    if (gameFinished) {
        gameFinished.classList.remove('hidden');
        gameFinished.style.display = 'block';
    }
    
    // Update final leaderboard
    updatePlayerLeaderboard(finalLeaderboard || []);
    showAlert('info', 'Game finished! Thanks for playing!');
}

function showReconnectPrompt() {
    const reconnectPrompt = document.getElementById('reconnect-prompt');
    if (reconnectPrompt) {
        hideAllScreens();
        reconnectPrompt.classList.remove('hidden');
        reconnectPrompt.style.display = 'block';
        
        // Populate team name
        const gameState = gameClient.getGameState();
        const rejoinTeamName = document.getElementById('rejoin-team-name');
        if (rejoinTeamName && gameState.teamName) {
            rejoinTeamName.value = gameState.teamName;
        }
    }
}

function displayPlayerQuestion(data) {
    console.log('Displaying question in player view');
    
    // Ensure we're showing the game screen first
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
    
    // Show question and answer form, hide results
    if (questionDisplay) questionDisplay.classList.remove('hidden');
    if (answerForm) answerForm.classList.remove('hidden');
    if (answerSubmitted) answerSubmitted.classList.add('hidden');
    if (questionClosed) questionClosed.classList.add('hidden');
    
    // Hide results from previous question
    const resultsDisplay = document.getElementById('results-display');
    if (resultsDisplay) resultsDisplay.classList.add('hidden');
}

function hideAnswerForm() {
    const answerForm = document.getElementById('answer-form');
    const questionClosed = document.getElementById('question-closed');
    
    if (answerForm) answerForm.classList.add('hidden');
    if (questionClosed) questionClosed.classList.remove('hidden');
}

function displayQuestionResults(data) {
    console.log('PLAYER: Displaying question results:', data);
    console.log('PLAYER: team_answer =', data.team_answer);
    console.log('PLAYER: team_correct =', data.team_correct);
    
    // Hide answer form and submission status
    const answerForm = document.getElementById('answer-form');
    const answerSubmitted = document.getElementById('answer-submitted');
    const questionClosed = document.getElementById('question-closed');
    
    if (answerForm) answerForm.classList.add('hidden');
    if (answerSubmitted) answerSubmitted.classList.add('hidden');
    if (questionClosed) questionClosed.classList.add('hidden');
    
    // Show results display
    const resultsDisplay = document.getElementById('results-display');
    if (resultsDisplay) {
        console.log('PLAYER: Showing results display');
        console.log('PLAYER: Before - display style:', resultsDisplay.style.display);
        console.log('PLAYER: Before - hidden class:', resultsDisplay.classList.contains('hidden'));
        
        resultsDisplay.classList.remove('hidden');
        resultsDisplay.style.display = 'block'; // Override any CSS hiding
        
        console.log('PLAYER: After - display style:', resultsDisplay.style.display);
        console.log('PLAYER: After - hidden class:', resultsDisplay.classList.contains('hidden'));
    } else {
        console.error('PLAYER: results-display element not found');
    }
        
        // Create results content
        let resultsHTML = '<div class="question-results">';
        
        // Show correct answer
        if (data.correct_answer) {
            resultsHTML += `<div class="correct-answer">
                <h4>Correct Answer:</h4>
                <p class="answer-text">${data.correct_answer}</p>
            </div>`;
        }
        
        // Show team's answer and result
        if (data.team_answer !== null && data.team_answer !== undefined) {
            const correctClass = data.team_correct ? 'correct' : 'incorrect';
            const resultIcon = data.team_correct ? '✅' : '❌';
            const resultText = data.team_correct ? 'Correct!' : 'Incorrect';
            
            resultsHTML += `<div class="team-result ${correctClass}">
                <h4>Your Answer:</h4>
                <p class="answer-text">${data.team_answer}</p>
                <p class="result-status">${resultIcon} ${resultText}</p>
            </div>`;
            
            // Show alert with result
            const alertType = data.team_correct ? 'success' : 'error';
            const alertMessage = data.team_correct ? 
                'Correct! +1 point' : 
                `Incorrect. The answer was: ${data.correct_answer}`;
            showAlert(alertType, alertMessage);
        } else {
            // Team didn't submit an answer
            resultsHTML += `<div class="team-result no-answer">
                <h4>Your Answer:</h4>
                <p class="no-answer-text">No answer submitted</p>
                <p class="result-status">❌ No points awarded</p>
            </div>`;
            
            showAlert('warning', `No answer submitted. The correct answer was: ${data.correct_answer}`);
        }
        
        resultsHTML += '</div>';
        
        // Update results content
        const resultsContent = document.getElementById('results-content');
        if (resultsContent) {
            console.log('PLAYER: Setting results content HTML:', resultsHTML);
            resultsContent.innerHTML = resultsHTML;
            console.log('PLAYER: Results content updated successfully');
        } else {
            console.error('PLAYER: results-content element not found');
        }
    }
    
    // Update game status
    const gameStatus = document.getElementById('game-status');
    if (gameStatus) {
        gameStatus.textContent = 'Question Results - Check your answer above';
    }
    
    // Update leaderboard with new scores
    if (data.leaderboard) {
        updatePlayerLeaderboard(data.leaderboard);
    }
}

function showAnswerSubmitted() {
    const answerForm = document.getElementById('answer-form');
    const answerSubmitted = document.getElementById('answer-submitted');
    
    if (answerForm) answerForm.classList.add('hidden');
    if (answerSubmitted) answerSubmitted.classList.remove('hidden');
}

function updatePlayerTeamsList(teams) {
    const teamsList = document.getElementById('teams-list');
    
    if (teamsList) {
        teamsList.innerHTML = '';
        teams.forEach(team => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="team-name">${team.name}</span>
                <span class="team-score">${team.score} pts</span>
            `;
            teamsList.appendChild(li);
        });
        
        // Update team count
        const teamCount = document.getElementById('team-count');
        if (teamCount) {
            teamCount.textContent = teams.length.toString();
        }
    }
}

function updatePlayerLeaderboard(leaderboard) {
    const leaderboardList = document.getElementById('leaderboard-list');
    if (leaderboardList) {
        leaderboardList.innerHTML = '';
        leaderboard.forEach((team, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="position">${index + 1}.</span>
                <span class="team-name">${team.name}</span>
                <span class="team-score">${team.score} pts</span>
            `;
            leaderboardList.appendChild(li);
        });
    }
}

// Player Action Functions
async function joinGame() {
    const gameId = document.getElementById('game-id').value.trim();
    const teamName = document.getElementById('team-name').value.trim();
    
    if (!gameId || !teamName) {
        showAlert('error', 'Please enter both Game ID and Team Name');
        return;
    }
    
    // Show loading state
    const joinBtn = document.querySelector('#player-join-form button');
    const originalText = joinBtn.textContent;
    joinBtn.textContent = 'Joining...';
    joinBtn.disabled = true;
    
    try {
        gameClient.joinGame(gameId, teamName);
        // Success will be handled by the 'team_joined' event handler
    } catch (error) {
        showAlert('error', error.message);
        joinBtn.textContent = originalText;
        joinBtn.disabled = false;
    }
}

function submitAnswer() {
    const answerInput = document.getElementById('answer-input');
    const submitBtn = document.getElementById('submit-btn');
    
    if (!answerInput || !submitBtn) {
        console.error('Answer form elements not found');
        return;
    }
    
    const answer = answerInput.value.trim();
    if (!answer) {
        showAlert('error', 'Please enter an answer');
        answerInput.focus();
        return;
    }
    
    // Disable the form to prevent double submission
    answerInput.disabled = true;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    try {
        gameClient.submitAnswer(answer);
        // Success will be handled by the 'answer_submitted' event handler
    } catch (error) {
        showAlert('error', 'Failed to submit answer');
        // Re-enable the form on error
        answerInput.disabled = false;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Answer';
    }
}

function startNewGame() {
    gameClient.clearGameState();
    showHome();
}

// Utility Functions (shared between admin and player)
function hideAllScreens() {
    const screens = ['home-screen', 'waiting-room', 'game-screen', 'game-finished', 'reconnect-prompt'];
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

// Setup UI event listeners for player interface
function setupPlayerUIEventListeners() {
    // Join game button
    const joinGameBtn = document.getElementById('join-game-btn');
    if (joinGameBtn) {
        joinGameBtn.addEventListener('click', joinGame);
    }
    
    // Leave game button
    const leaveGameBtn = document.getElementById('leave-game-btn');
    if (leaveGameBtn) {
        leaveGameBtn.addEventListener('click', playerLeaveGame);
    }
    
    // Submit answer button
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitAnswer);
    }
    
    // Start new game button (player version)
    const startNewGamePlayerBtn = document.getElementById('start-new-game-player-btn');
    if (startNewGamePlayerBtn) {
        startNewGamePlayerBtn.addEventListener('click', playerStartNewGame);
    }
    
    // Rejoin and start fresh buttons
    const rejoinGameBtn = document.getElementById('rejoin-game-btn');
    if (rejoinGameBtn) {
        rejoinGameBtn.addEventListener('click', () => gameClient.confirmRejoin());
    }
    
    const startFreshBtn = document.getElementById('start-fresh-btn');
    if (startFreshBtn) {
        startFreshBtn.addEventListener('click', () => {
            gameClient.hideRejoinPrompt();
            gameClient.clearGameState();
            showHome();
        });
    }
    
    // Keyboard event listeners for Enter key
    const gameIdInput = document.getElementById('game-id');
    if (gameIdInput) {
        gameIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                joinGame();
            }
        });
    }
    
    const teamNameInput = document.getElementById('team-name');
    if (teamNameInput) {
        teamNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                joinGame();
            }
        });
    }
    
    const answerInput = document.getElementById('answer-input');
    if (answerInput) {
        answerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitAnswer();
            }
        });
    }
    
    const rejoinTeamNameInput = document.getElementById('rejoin-team-name');
    if (rejoinTeamNameInput) {
        rejoinTeamNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                gameClient.confirmRejoin();
            }
        });
    }
}

// Expose player functions globally for backward compatibility and tests
function exposePlayerFunctionsGlobally() {
    window.joinGame = joinGame;
    window.submitAnswer = submitAnswer;
    window.leaveGame = playerLeaveGame;
    window.startNewGame = playerStartNewGame;
}

// Player-specific versions of common functions
function playerLeaveGame() {
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

function playerStartNewGame() {
    gameClient.clearGameState();
    showHome();
}

// Handle Enter key in forms (legacy support - now handled by individual listeners)
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        const activeElement = document.activeElement;
        
        // Handle enter in game ID or team name inputs
        if (activeElement.id === 'game-id' || activeElement.id === 'team-name') {
            e.preventDefault();
            joinGame();
        }
        
        // Handle enter in answer input
        if (activeElement.id === 'answer-input') {
            e.preventDefault();
            submitAnswer();
        }
        
        // Handle enter in rejoin team name input
        if (activeElement.id === 'rejoin-team-name') {
            e.preventDefault();
            gameClient.confirmRejoin();
        }
    }
});
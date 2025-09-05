/**
 * Game Client - Handles WebSocket communication and state persistence
 */
class GameClient {
    constructor() {
        this.socket = null;
        this.gameState = this.loadGameState();
        this.eventHandlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isReconnecting = false;
    }

    // Initialize connection with persistence support
    connect(serverUrl = 'http://localhost:5000') {
        if (this.socket && this.socket.connected) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            this.socket = io(serverUrl);
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.reconnectAttempts = 0;
                this.isReconnecting = false;
                
                // Auto-rejoin if we have saved state
                this.handleReconnection();
                resolve();
            });

            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from server:', reason);
                if (reason !== 'io client disconnect') {
                    this.handleDisconnection();
                }
            });

            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.handleConnectionError();
                reject(error);
            });

            this.socket.on('connected', (data) => {
                this.gameState.clientId = data.client_id;
                this.saveGameState();
            });

            // Register message handlers
            this.setupEventHandlers();
        });
    }

    // Setup WebSocket event handlers
    setupEventHandlers() {
        const events = [
            'team_joined', 'team_list_update', 'game_started', 'question_started',
            'answer_submitted', 'question_closed', 'answer_graded', 'leaderboard_update',
            'game_finished', 'error', 'success'
        ];

        events.forEach(event => {
            this.socket.on(event, (data) => {
                this.handleEvent(event, data);
            });
        });

        // Handle generic message events
        this.socket.on('message', (data) => {
            try {
                const message = JSON.parse(data);
                this.handleEvent(message.event, message.data);
            } catch (e) {
                console.error('Failed to parse message:', data, e);
            }
        });
    }

    // Handle events and trigger callbacks
    handleEvent(eventType, data) {
        console.log(`Event: ${eventType}`, data);
        
        // Update internal state based on events
        this.updateStateFromEvent(eventType, data);
        
        // Trigger registered callbacks
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    console.error(`Error in event handler for ${eventType}:`, e);
                }
            });
        }
    }

    // Update game state based on received events
    updateStateFromEvent(eventType, data) {
        switch (eventType) {
            case 'team_joined':
                this.gameState.teamId = data.team_id;
                this.gameState.teamName = data.team_name;
                this.gameState.gameId = data.game_id;
                this.gameState.isTeam = true;
                break;
            case 'success':
                if (data.is_admin) {
                    this.gameState.isAdmin = true;
                    this.gameState.gameId = data.game_id;
                }
                break;
            case 'game_started':
                this.gameState.gameStatus = 'in_progress';
                break;
            case 'question_started':
                this.gameState.currentQuestion = {
                    round: data.round,
                    question_num: data.question_num,
                    question: data.question,
                    answer: data.answer // Only for admin
                };
                this.gameState.gameStatus = 'question_active';
                break;
            case 'question_closed':
                this.gameState.gameStatus = 'question_closed';
                break;
            case 'game_finished':
                this.gameState.gameStatus = 'finished';
                break;
        }
        
        this.saveGameState();
    }

    // Register event callback
    on(eventType, callback) {
        if (!this.eventHandlers[eventType]) {
            this.eventHandlers[eventType] = [];
        }
        this.eventHandlers[eventType].push(callback);
    }

    // Remove event callback
    off(eventType, callback) {
        if (this.eventHandlers[eventType]) {
            const index = this.eventHandlers[eventType].indexOf(callback);
            if (index > -1) {
                this.eventHandlers[eventType].splice(index, 1);
            }
        }
    }

    // Join game as team
    joinGame(gameId, teamName) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('join_game', {
            game_id: gameId,
            team_name: teamName
        });
    }

    // Admin login
    adminLogin(gameId, password) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('admin_login', {
            game_id: gameId,
            password: password
        });
    }

    // Start game (admin only)
    startGame(password) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('start_game', {
            password: password
        });
    }

    // Start question (admin only)
    startQuestion(password) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('start_question', {
            password: password
        });
    }

    // Submit answer (team only)
    submitAnswer(answer) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('submit_answer', {
            answer: answer
        });
    }

    // Close question (admin only)
    closeQuestion(password) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('close_question', {
            password: password
        });
    }

    // Grade answer (admin only)
    gradeAnswer(teamId, roundNum, questionNum, isCorrect, points = 1) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('grade_answer', {
            team_id: teamId,
            round_num: roundNum,
            question_num: questionNum,
            is_correct: isCorrect,
            points: points
        });
    }

    // Move to next question (admin only)
    nextQuestion(password) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('next_question', {
            password: password
        });
    }

    // Get leaderboard
    getLeaderboard() {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('get_leaderboard', {});
    }

    // Handle reconnection after disconnect
    handleReconnection() {
        if (this.gameState.gameId) {
            // Try to rejoin based on saved state
            if (this.gameState.isAdmin && this.gameState.adminPassword) {
                // Re-login as admin
                setTimeout(() => {
                    this.adminLogin(this.gameState.gameId, this.gameState.adminPassword);
                }, 500);
            } else if (this.gameState.teamName) {
                // Show rejoin prompt for teams
                this.showRejoinPrompt();
            }
        }
    }

    // Handle disconnection
    handleDisconnection() {
        if (!this.isReconnecting) {
            this.isReconnecting = true;
            this.attemptReconnect();
        }
    }

    // Handle connection errors
    handleConnectionError() {
        if (!this.isReconnecting && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.isReconnecting = true;
            this.attemptReconnect();
        }
    }

    // Attempt to reconnect
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            this.showConnectionError();
            return;
        }

        this.reconnectAttempts++;
        console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        
        setTimeout(() => {
            if (this.socket) {
                this.socket.disconnect();
            }
            this.connect().catch(() => {
                this.attemptReconnect();
            });
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    // Show rejoin prompt for teams
    showRejoinPrompt() {
        const modal = document.getElementById('rejoin-modal');
        if (modal) {
            document.getElementById('rejoin-game-id').textContent = this.gameState.gameId;
            document.getElementById('rejoin-team-name').value = this.gameState.teamName || '';
            modal.style.display = 'flex';
        }
    }

    // Hide rejoin prompt
    hideRejoinPrompt() {
        const modal = document.getElementById('rejoin-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Handle rejoin confirmation
    confirmRejoin() {
        const teamNameInput = document.getElementById('rejoin-team-name');
        const teamName = teamNameInput.value.trim();
        
        if (teamName) {
            this.joinGame(this.gameState.gameId, teamName);
            this.hideRejoinPrompt();
        }
    }

    // Show connection error
    showConnectionError() {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'connection-error';
        errorDiv.innerHTML = `
            <div class="error-message">
                <h3>Connection Lost</h3>
                <p>Unable to connect to the game server. Please check your internet connection and refresh the page.</p>
                <button onclick="location.reload()">Refresh Page</button>
            </div>
        `;
        document.body.appendChild(errorDiv);
    }

    // Save game state to localStorage
    saveGameState() {
        try {
            localStorage.setItem('triviaGameState', JSON.stringify(this.gameState));
        } catch (e) {
            console.warn('Failed to save game state:', e);
        }
    }

    // Load game state from localStorage
    loadGameState() {
        try {
            const saved = localStorage.getItem('triviaGameState');
            if (saved) {
                return { ...this.getDefaultState(), ...JSON.parse(saved) };
            }
        } catch (e) {
            console.warn('Failed to load game state:', e);
        }
        return this.getDefaultState();
    }

    // Get default game state
    getDefaultState() {
        return {
            clientId: null,
            gameId: null,
            teamId: null,
            teamName: null,
            isAdmin: false,
            isTeam: false,
            gameStatus: 'waiting',
            currentQuestion: null,
            adminPassword: null
        };
    }

    // Clear game state
    clearGameState() {
        this.gameState = this.getDefaultState();
        localStorage.removeItem('triviaGameState');
    }

    // Get current game state
    getGameState() {
        return { ...this.gameState };
    }

    // Disconnect and cleanup
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.reconnectAttempts = 0;
        this.isReconnecting = false;
    }
}

// Export for use in other files
window.GameClient = GameClient;
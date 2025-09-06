from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit, disconnect
import uuid
import os
from .question_manager import QuestionManager
from .game_state import GameStateManager
from .websocket_manager import WebSocketManager, WebSocketMessage, EventType
import json

app = Flask(__name__, static_folder='../frontend', static_url_path='/frontend')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Initialize SocketIO with CORS enabled for development
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Initialize managers
question_manager = QuestionManager()
game_state_manager = GameStateManager(question_manager)
websocket_manager = WebSocketManager(game_state_manager)

# Store socket ID to client ID mapping
socket_to_client = {}
client_to_socket = {}


@app.route('/')
def index():
    """Serve the main frontend page"""
    return send_file('../frontend/index.html')

@app.route('/admin')
def admin():
    """Serve the admin page"""
    return send_file('../frontend/admin.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "trivia-app"})


@app.route('/api/create-game', methods=['POST'])
def create_game():
    """Create a new game with CSV file"""
    try:
        data = request.json
        game_id = data.get('game_id')
        csv_file_path = data.get('csv_file_path')
        admin_password = data.get('admin_password')
        
        if not all([game_id, csv_file_path, admin_password]):
            return jsonify({"error": "Missing required fields"}), 400
        
        game = game_state_manager.create_game(game_id, csv_file_path, admin_password)
        
        return jsonify({
            "success": True,
            "game_id": game.game_id,
            "status": game.status.value
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/games/<game_id>', methods=['GET'])
def get_game_info(game_id):
    """Get basic game information"""
    try:
        summary = game_state_manager.get_game_summary(game_id)
        return jsonify({"success": True, "game": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    client_id = str(uuid.uuid4())
    socket_id = request.sid
    
    # Map socket to client
    socket_to_client[socket_id] = client_id
    client_to_socket[client_id] = socket_id
    
    # Register with websocket manager
    try:
        connection = websocket_manager.connect_client(client_id)
        emit('connected', {
            'client_id': client_id,
            'message': 'Connected successfully'
        })
        
        print(f"Client {client_id} connected with socket {socket_id}")
    
    except Exception as e:
        emit('error', {'message': str(e)})
        disconnect()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    socket_id = request.sid
    
    if socket_id in socket_to_client:
        client_id = socket_to_client[socket_id]
        
        # Clean up websocket manager
        websocket_manager.disconnect_client(client_id)
        
        # Clean up mappings
        del socket_to_client[socket_id]
        if client_id in client_to_socket:
            del client_to_socket[client_id]
        
        print(f"Client {client_id} disconnected")


@socketio.on('message')
def handle_message(data):
    """Handle incoming WebSocket messages"""
    socket_id = request.sid
    
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    
    try:
        # Parse message
        if isinstance(data, str):
            message_data = json.loads(data)
        else:
            message_data = data
        
        message = WebSocketMessage(
            event_type=EventType(message_data['event']),
            data=message_data['data']
        )
        
        # Handle message
        responses = websocket_manager.handle_message(client_id, message)
        
        # Send responses
        for response in responses:
            target_client = response.data.get('target_client')
            
            if target_client and target_client in client_to_socket:
                # Send to specific client
                target_socket = client_to_socket[target_client]
                socketio.emit('message', response.to_json(), room=target_socket)
            else:
                # Send to current client
                emit('message', response.to_json())
    
    except Exception as e:
        emit('error', {'message': str(e)})
        print(f"Error handling message from {client_id}: {str(e)}")


def send_message_to_client(client_id: str, message: WebSocketMessage):
    """Send message to specific client"""
    if client_id in client_to_socket:
        socket_id = client_to_socket[client_id]
        socketio.emit('message', message.to_json(), room=socket_id)


# Additional SocketIO event handlers for specific events
@socketio.on('join_game')
def handle_join_game(data):
    """Handle team joining game"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.JOIN_GAME, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        target_client = response.data.get('target_client')
        if target_client and target_client in client_to_socket:
            target_socket = client_to_socket[target_client]
            socketio.emit(response.event_type.value, response.data, room=target_socket)
        else:
            emit(response.event_type.value, response.data)


@socketio.on('admin_login')
def handle_admin_login(data):
    """Handle admin login"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.ADMIN_LOGIN, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        emit(response.event_type.value, response.data)


@socketio.on('start_game')
def handle_start_game(data):
    """Handle game start"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.START_GAME, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        target_client = response.data.get('target_client')
        if target_client and target_client in client_to_socket:
            target_socket = client_to_socket[target_client]
            socketio.emit(response.event_type.value, response.data, room=target_socket)


@socketio.on('start_question')
def handle_start_question(data):
    """Handle question start"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.START_QUESTION, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        target_client = response.data.get('target_client')
        if target_client and target_client in client_to_socket:
            target_socket = client_to_socket[target_client]
            socketio.emit(response.event_type.value, response.data, room=target_socket)


@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Handle answer submission"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.SUBMIT_ANSWER, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        target_client = response.data.get('target_client')
        if target_client and target_client in client_to_socket:
            target_socket = client_to_socket[target_client]
            socketio.emit(response.event_type.value, response.data, room=target_socket)
        else:
            emit(response.event_type.value, response.data)


@socketio.on('close_question')
def handle_close_question(data):
    """Handle question closing"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.CLOSE_QUESTION, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        target_client = response.data.get('target_client')
        if target_client and target_client in client_to_socket:
            target_socket = client_to_socket[target_client]
            socketio.emit(response.event_type.value, response.data, room=target_socket)


@socketio.on('grade_answer')
def handle_grade_answer(data):
    """Handle answer grading"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.GRADE_ANSWER, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        target_client = response.data.get('target_client')
        if target_client and target_client in client_to_socket:
            target_socket = client_to_socket[target_client]
            socketio.emit(response.event_type.value, response.data, room=target_socket)


@socketio.on('next_question')
def handle_next_question(data):
    """Handle moving to next question"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.NEXT_QUESTION, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        target_client = response.data.get('target_client')
        if target_client and target_client in client_to_socket:
            target_socket = client_to_socket[target_client]
            socketio.emit(response.event_type.value, response.data, room=target_socket)
        else:
            emit(response.event_type.value, response.data)


@socketio.on('get_leaderboard')
def handle_get_leaderboard(data):
    """Handle leaderboard request"""
    socket_id = request.sid
    if socket_id not in socket_to_client:
        emit('error', {'message': 'Client not registered'})
        return
    
    client_id = socket_to_client[socket_id]
    message = WebSocketMessage(EventType.GET_LEADERBOARD, data)
    responses = websocket_manager.handle_message(client_id, message)
    
    for response in responses:
        emit(response.event_type.value, response.data)


if __name__ == '__main__':
    # Development server
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
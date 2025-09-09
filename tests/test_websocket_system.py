"""
WebSocket system tests - consolidated WebSocket and message handling tests
"""
import pytest
import json
import time
from backend.websocket_manager import WebSocketManager, WebSocketMessage, EventType, ClientConnection
from backend.game_state import GameStateManager
from backend.question_manager import QuestionManager
from .test_helpers import create_temp_csv, cleanup_temp_file, STANDARD_CSV_CONTENT


class TestWebSocketMessage:
    """Test WebSocket message functionality"""
    
    def test_message_creation(self):
        data = {"key": "value", "number": 42}
        message = WebSocketMessage(EventType.JOIN_GAME, data)
        
        assert message.event_type == EventType.JOIN_GAME
        assert message.data == data
        assert message.timestamp is not None
        assert isinstance(message.timestamp, float)
    
    def test_message_to_json(self):
        data = {"test": "data"}
        message = WebSocketMessage(EventType.SUCCESS, data, timestamp=1234567890.0)
        
        json_str = message.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["event"] == "success"
        assert parsed["data"] == data
        assert parsed["timestamp"] == 1234567890.0
    
    def test_message_from_json(self):
        json_str = '{"event": "join_game", "data": {"game_id": "test"}, "timestamp": 1234567890.0}'
        message = WebSocketMessage.from_json(json_str)
        
        assert message.event_type == EventType.JOIN_GAME
        assert message.data == {"game_id": "test"}
        assert message.timestamp == 1234567890.0


class TestClientConnection:
    """Test client connection functionality"""
    
    def test_client_connection_creation(self):
        connection = ClientConnection("client123")
        
        assert connection.client_id == "client123"
        assert connection.game_id is None
        assert connection.team_id is None
        assert connection.is_admin is False
        assert connection.connected_at is not None


class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
        self.wsm = WebSocketManager(self.gsm)
        self.csv_file = create_temp_csv(STANDARD_CSV_CONTENT)
        self.gsm.create_game("test_game", self.csv_file, "admin123")
    
    def teardown_method(self):
        cleanup_temp_file(self.csv_file)
    
    def test_connect_client(self):
        connection = self.wsm.connect_client("client1")
        assert connection.client_id == "client1"
        assert "client1" in self.wsm.connections
    
    def test_connect_duplicate_client_raises_error(self):
        self.wsm.connect_client("client1")
        
        with pytest.raises(ValueError, match="Client client1 already connected"):
            self.wsm.connect_client("client1")
    
    def test_disconnect_client(self):
        self.wsm.connect_client("client1")
        self.wsm.disconnect_client("client1")
        
        assert "client1" not in self.wsm.connections
    
    def test_disconnect_nonexistent_client(self):
        # Should not raise error
        self.wsm.disconnect_client("nonexistent")
    
    def test_join_game_success(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        
        responses = self.wsm.handle_message("client1", message)
        
        # Should get team_joined and team_list_update messages
        assert len(responses) >= 2
        
        team_joined = next(r for r in responses if r.event_type == EventType.TEAM_JOINED)
        assert team_joined.data["team_name"] == "Team Alpha"
        assert team_joined.data["game_id"] == "test_game"
        
        team_list_updates = [r for r in responses if r.event_type == EventType.TEAM_LIST_UPDATE]
        assert len(team_list_updates) >= 1
    
    def test_join_game_missing_data(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.JOIN_GAME, {"game_id": "test_game"})
        responses = self.wsm.handle_message("client1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Missing game_id or team_name" in responses[0].data["message"]
    
    def test_join_nonexistent_game(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "nonexistent",
            "team_name": "Team Alpha"
        })
        
        responses = self.wsm.handle_message("client1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Game not found" in responses[0].data["message"]
    
    def test_admin_login_success(self):
        self.wsm.connect_client("admin1")
        
        message = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        
        responses = self.wsm.handle_message("admin1", message)
        
        # Should get success and team_list_update messages
        assert len(responses) >= 2
        
        success_msg = next(r for r in responses if r.event_type == EventType.SUCCESS)
        assert success_msg.data["is_admin"] is True
        assert success_msg.data["game_id"] == "test_game"
        
        team_list_msg = next(r for r in responses if r.event_type == EventType.TEAM_LIST_UPDATE)
        assert "teams" in team_list_msg.data
    
    def test_admin_login_wrong_password(self):
        self.wsm.connect_client("admin1")
        
        message = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "wrongpassword"
        })
        
        responses = self.wsm.handle_message("admin1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Invalid admin password" in responses[0].data["message"]
    
    def test_start_game_success(self):
        # Setup admin
        self.wsm.connect_client("admin1")
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        # Add a team
        self.wsm.connect_client("client1")
        join_message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_message)
        
        # Start game
        start_message = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_message)
        
        # Should broadcast game_started to all clients
        game_started_msgs = [r for r in responses if r.event_type == EventType.GAME_STARTED]
        assert len(game_started_msgs) == 2  # admin + player
    
    def test_start_game_non_admin(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("client1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Admin access required" in responses[0].data["message"]
    
    def test_start_question_success(self):
        # Setup admin and start game
        self.wsm.connect_client("admin1")
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        self.wsm.connect_client("client1")
        join_message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_message)
        
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        # Start question
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_question)
        
        # Should send question to all clients
        question_started_msgs = [r for r in responses if r.event_type == EventType.QUESTION_STARTED]
        assert len(question_started_msgs) == 2  # admin + player
        
        # Admin should see the answer
        admin_msg = next(r for r in question_started_msgs if "answer" in r.data)
        assert admin_msg.data["question"] == "What is 2+2?"
        assert admin_msg.data["answer"] == "4"
        
        # Player should not see the answer
        player_msg = next(r for r in question_started_msgs if "answer" not in r.data)
        assert player_msg.data["question"] == "What is 2+2?"
    
    def test_submit_answer_success(self):
        # Setup game with active question
        self.wsm.connect_client("admin1")
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        self.wsm.connect_client("client1")
        join_responses = self.wsm.handle_message("client1", WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        }))
        
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_question)
        
        # Submit answer
        submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("client1", submit_answer)
        
        # Should get answer_submitted confirmations
        answer_submitted_msgs = [r for r in responses if r.event_type == EventType.ANSWER_SUBMITTED]
        assert len(answer_submitted_msgs) >= 1
        
        # Team confirmation
        team_msg = next(r for r in answer_submitted_msgs if "team_name" not in r.data)
        assert team_msg.data["answer"] == "4"
        
        # Admin notification
        admin_msg = next(r for r in answer_submitted_msgs if "team_name" in r.data)
        assert admin_msg.data["team_name"] == "Team Alpha"
        assert admin_msg.data["answer"] == "4"
        assert admin_msg.data["is_auto_correct"] is True  # Correct answer
    
    def test_submit_answer_not_in_team(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "test"})
        responses = self.wsm.handle_message("client1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Must be part of a team" in responses[0].data["message"]
    
    def test_close_question_success(self):
        # Setup game with submitted answers
        self.wsm.connect_client("admin1")
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        self.wsm.connect_client("client1")
        join_responses = self.wsm.handle_message("client1", WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        }))
        
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_question)
        
        submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        self.wsm.handle_message("client1", submit_answer)
        
        # Close question
        close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", close_question)
        
        # Should get question_closed and leaderboard_update messages
        question_closed_msgs = [r for r in responses if r.event_type == EventType.QUESTION_CLOSED]
        leaderboard_msgs = [r for r in responses if r.event_type == EventType.LEADERBOARD_UPDATE]
        
        assert len(question_closed_msgs) >= 2  # admin + player
        assert len(leaderboard_msgs) >= 2     # admin + player
        
        # Admin should get answers for grading
        admin_msg = next(r for r in question_closed_msgs if "answers" in r.data)
        assert len(admin_msg.data["answers"]) == 1
        assert admin_msg.data["answers"][0]["team_name"] == "Team Alpha"
        assert admin_msg.data["answers"][0]["is_correct"] is True
        
        # Player should get results
        player_msg = next(r for r in question_closed_msgs if "correct_answer" in r.data)
        assert player_msg.data["correct_answer"] == "4"
        assert player_msg.data["team_answer"] == "4"
        assert player_msg.data["team_correct"] is True
    
    def test_grade_answer_success(self):
        # Setup game with closed question
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("client1")
        
        # Complete setup through question closing
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        join_responses = self.wsm.handle_message("client1", WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        }))
        
        # Get team_id from join response
        team_joined_msg = next(r for r in join_responses if r.event_type == EventType.TEAM_JOINED)
        team_id = team_joined_msg.data["team_id"]
        
        self.wsm.handle_message("admin1", WebSocketMessage(EventType.START_GAME, {"password": "admin123"}))
        self.wsm.handle_message("admin1", WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"}))
        self.wsm.handle_message("client1", WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "wrong"}))
        self.wsm.handle_message("admin1", WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"}))
        
        # Grade answer
        grade_answer = WebSocketMessage(EventType.GRADE_ANSWER, {
            "team_id": team_id,
            "round_num": 1,
            "question_num": 1,
            "is_correct": True,
            "points": 1
        })
        
        responses = self.wsm.handle_message("admin1", grade_answer)
        
        answer_graded_msgs = [r for r in responses if r.event_type == EventType.ANSWER_GRADED]
        assert len(answer_graded_msgs) == 2  # Broadcast to both clients
        
        for msg in answer_graded_msgs:
            assert msg.data["is_correct"] is True
            assert msg.data["points_awarded"] == 1
            assert msg.data["new_score"] == 1  # Updated score after manual grading
    
    def test_get_leaderboard(self):
        self.wsm.connect_client("client1")
        
        # Join game first
        join_message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_message)
        
        # Get leaderboard
        leaderboard_message = WebSocketMessage(EventType.GET_LEADERBOARD, {})
        responses = self.wsm.handle_message("client1", leaderboard_message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.LEADERBOARD_UPDATE
        assert "leaderboard" in responses[0].data
        assert len(responses[0].data["leaderboard"]) == 1
        assert responses[0].data["leaderboard"][0]["name"] == "Team Alpha"
    
    def test_get_game_state(self):
        self.wsm.connect_client("client1")
        
        # Join game first
        join_message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_message)
        
        # Get game state
        state_message = WebSocketMessage(EventType.GET_GAME_STATE, {})
        responses = self.wsm.handle_message("client1", state_message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.SUCCESS
        assert "game_state" in responses[0].data
        game_state = responses[0].data["game_state"]
        assert game_state["game_id"] == "test_game"
        assert game_state["status"] == "waiting"
    
    def test_unknown_event_type(self):
        self.wsm.connect_client("client1")
        
        # Create message with invalid event type (this will be handled by the error case)
        responses = self.wsm.handle_message("client1", WebSocketMessage(EventType.SUCCESS, {}))
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Unknown event type" in responses[0].data["message"]
    
    def test_message_from_unconnected_client(self):
        message = WebSocketMessage(EventType.JOIN_GAME, {"game_id": "test"})
        responses = self.wsm.handle_message("unconnected_client", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Client not connected" in responses[0].data["message"]
    
    def test_get_game_clients(self):
        self.wsm.connect_client("client1")
        self.wsm.connect_client("client2")
        
        # Join game
        join_message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_message)
        
        clients = self.wsm.get_game_clients("test_game")
        assert len(clients) == 1
        assert "client1" in clients
        
        # Client2 not in game yet
        assert "client2" not in clients
    
    def test_disconnect_client_from_game_cleanup(self):
        self.wsm.connect_client("client1")
        
        # Join game
        join_message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_message)
        
        # Verify client is in game
        clients = self.wsm.get_game_clients("test_game")
        assert "client1" in clients
        
        # Disconnect client
        self.wsm.disconnect_client("client1")
        
        # Verify client is removed from game
        clients = self.wsm.get_game_clients("test_game")
        assert len(clients) == 0
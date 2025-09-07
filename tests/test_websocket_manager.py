import pytest
import os
import json
from backend.websocket_manager import WebSocketManager, WebSocketMessage, EventType, ClientConnection
from backend.game_state import GameStateManager, GameStatus
from backend.question_manager import QuestionManager
from .test_helpers import create_standard_test_csv, cleanup_temp_file


class TestWebSocketMessage:
    def test_message_creation(self):
        message = WebSocketMessage(EventType.JOIN_GAME, {"game_id": "test", "team_name": "Team A"})
        assert message.event_type == EventType.JOIN_GAME
        assert message.data["game_id"] == "test"
        assert message.timestamp is not None
    
    def test_message_to_json(self):
        message = WebSocketMessage(EventType.JOIN_GAME, {"game_id": "test"})
        json_str = message.to_json()
        data = json.loads(json_str)
        
        assert data["event"] == "join_game"
        assert data["data"]["game_id"] == "test"
        assert "timestamp" in data
    
    def test_message_from_json(self):
        json_str = '{"event": "join_game", "data": {"game_id": "test"}, "timestamp": 1234567890}'
        message = WebSocketMessage.from_json(json_str)
        
        assert message.event_type == EventType.JOIN_GAME
        assert message.data["game_id"] == "test"
        assert message.timestamp == 1234567890


class TestClientConnection:
    def test_client_connection_creation(self):
        connection = ClientConnection("client123")
        assert connection.client_id == "client123"
        assert connection.game_id is None
        assert connection.team_id is None
        assert connection.is_admin is False
        assert connection.connected_at is not None


class TestWebSocketManager:
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
        self.wsm = WebSocketManager(self.gsm)
        
        # Create a test game using standard test CSV
        self.csv_file_path = create_standard_test_csv()
        self.gsm.create_game("test_game", self.csv_file_path, "admin123")
    
    def teardown_method(self):
        if hasattr(self, 'csv_file_path'):
            cleanup_temp_file(self.csv_file_path)
    
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
        assert "client1" in self.wsm.connections
        
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
        
        # Should get team joined confirmation and team list update
        assert len(responses) >= 1
        
        team_joined_msg = next((r for r in responses if r.event_type == EventType.TEAM_JOINED), None)
        assert team_joined_msg is not None
        assert team_joined_msg.data["team_name"] == "Team Alpha"
        assert team_joined_msg.data["game_id"] == "test_game"
        
        # Check connection was updated
        connection = self.wsm.get_client_connection("client1")
        assert connection.game_id == "test_game"
        assert connection.team_id is not None
    
    def test_join_game_missing_data(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.JOIN_GAME, {"game_id": "test_game"})  # Missing team_name
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
        
        # Should get success message and team list update
        assert len(responses) == 2
        
        success_msgs = [r for r in responses if r.event_type == EventType.SUCCESS]
        team_list_msgs = [r for r in responses if r.event_type == EventType.TEAM_LIST_UPDATE]
        
        assert len(success_msgs) == 1
        assert len(team_list_msgs) == 1
        
        assert success_msgs[0].data["is_admin"] is True
        assert team_list_msgs[0].data["teams"] == []  # Empty team list initially
        
        connection = self.wsm.get_client_connection("admin1")
        assert connection.is_admin is True
        assert connection.game_id == "test_game"
    
    def test_admin_login_wrong_password(self):
        self.wsm.connect_client("admin1")
        
        message = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "wrong"
        })
        
        responses = self.wsm.handle_message("admin1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Invalid admin password" in responses[0].data["message"]
    
    def test_start_game_success(self):
        # Setup admin and team
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("client1")
        
        # Admin login
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        # Add team
        join_msg = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg)
        
        # Start game
        start_msg = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_msg)
        
        # Should broadcast to both admin and team
        game_started_msgs = [r for r in responses if r.event_type == EventType.GAME_STARTED]
        assert len(game_started_msgs) == 2  # One for admin, one for team
        
        for msg in game_started_msgs:
            assert msg.data["status"] == "in_progress"
    
    def test_start_game_non_admin(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("client1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Admin access required" in responses[0].data["message"]
    
    def test_start_question_success(self):
        # Setup game with admin and team
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("client1")
        
        # Admin login and team join
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        join_msg = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg)
        
        # Start game
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        # Start question
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_question)
        
        question_started_msgs = [r for r in responses if r.event_type == EventType.QUESTION_STARTED]
        assert len(question_started_msgs) == 2  # One for admin, one for team
        
        # Admin should see answer, team should not
        admin_msg = next((r for r in question_started_msgs if "answer" in r.data), None)
        team_msg = next((r for r in question_started_msgs if "answer" not in r.data), None)
        
        assert admin_msg is not None
        assert team_msg is not None
        assert admin_msg.data["answer"] == "4"
        assert admin_msg.data["question"] == "What is 2+2?"
    
    def test_submit_answer_success(self):
        # Setup game in question state
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("client1")
        
        # Complete setup
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        join_msg = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg)
        
        self.wsm.handle_message("admin1", WebSocketMessage(EventType.START_GAME, {"password": "admin123"}))
        self.wsm.handle_message("admin1", WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"}))
        
        # Submit answer
        submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("client1", submit_answer)
        
        # Team gets confirmation, admin gets notification
        assert len(responses) >= 1
        
        answer_submitted_msgs = [r for r in responses if r.event_type == EventType.ANSWER_SUBMITTED]
        assert len(answer_submitted_msgs) >= 1
    
    def test_submit_answer_not_in_team(self):
        self.wsm.connect_client("client1")
        
        message = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("client1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Must be part of a team" in responses[0].data["message"]
    
    def test_close_question_success(self):
        # Setup game with submitted answer
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("client1")
        
        # Complete setup to question submission
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        join_msg = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg)
        
        self.wsm.handle_message("admin1", WebSocketMessage(EventType.START_GAME, {"password": "admin123"}))
        self.wsm.handle_message("admin1", WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"}))
        self.wsm.handle_message("client1", WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"}))
        
        # Close question
        close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", close_question)
        
        question_closed_msgs = [r for r in responses if r.event_type == EventType.QUESTION_CLOSED]
        assert len(question_closed_msgs) == 2  # One for admin, one for team
        
        # Admin should get answer details, team should get simple notification
        admin_msg = next((r for r in question_closed_msgs if "answers" in r.data), None)
        team_msg = next((r for r in question_closed_msgs if "message" in r.data), None)
        
        assert admin_msg is not None
        assert team_msg is not None
        assert len(admin_msg.data["answers"]) == 1
    
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
        self.wsm.handle_message("client1", WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"}))
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
            assert msg.data["new_score"] == 1
    
    def test_get_leaderboard(self):
        # Setup game with team
        self.wsm.connect_client("client1")
        
        join_msg = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg)
        
        # Request leaderboard
        leaderboard_msg = WebSocketMessage(EventType.GET_LEADERBOARD, {})
        responses = self.wsm.handle_message("client1", leaderboard_msg)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.LEADERBOARD_UPDATE
        assert len(responses[0].data["leaderboard"]) == 1
        assert responses[0].data["leaderboard"][0]["name"] == "Team Alpha"
    
    def test_get_game_state(self):
        # Setup game with team
        self.wsm.connect_client("client1")
        
        join_msg = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg)
        
        # Request game state
        state_msg = WebSocketMessage(EventType.GET_GAME_STATE, {})
        responses = self.wsm.handle_message("client1", state_msg)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.SUCCESS
        assert "game_state" in responses[0].data
        assert responses[0].data["game_state"]["game_id"] == "test_game"
    
    def test_unknown_event_type(self):
        self.wsm.connect_client("client1")
        
        # Create message with invalid event type manually
        message = WebSocketMessage(EventType.JOIN_GAME, {})  # Start with valid
        message.event_type = "invalid_event"  # Then change to invalid
        
        # Mock the unknown event
        responses = self.wsm.handle_message("client1", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
    
    def test_message_from_unconnected_client(self):
        message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        
        responses = self.wsm.handle_message("unconnected", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Client not connected" in responses[0].data["message"]
    
    def test_get_game_clients(self):
        # Connect clients to game
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("client1")
        self.wsm.connect_client("client2")
        
        # Add them to game
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "test_game",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        join_msg1 = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg1)
        
        join_msg2 = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Beta"
        })
        self.wsm.handle_message("client2", join_msg2)
        
        # Check game clients
        clients = self.wsm.get_game_clients("test_game")
        assert len(clients) == 3
        assert {"admin1", "client1", "client2"} == clients
    
    def test_disconnect_client_from_game_cleanup(self):
        # Connect client and add to game
        self.wsm.connect_client("client1")
        
        join_msg = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "test_game",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_msg)
        
        # Verify client is in game
        clients = self.wsm.get_game_clients("test_game")
        assert "client1" in clients
        
        # Disconnect client
        self.wsm.disconnect_client("client1")
        
        # Verify cleanup
        clients = self.wsm.get_game_clients("test_game")
        assert "client1" not in clients
        assert "client1" not in self.wsm.connections
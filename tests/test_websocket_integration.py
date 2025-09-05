import pytest
import tempfile
import os
from backend.websocket_manager import WebSocketManager, WebSocketMessage, EventType
from backend.game_state import GameStateManager, GameStatus
from backend.question_manager import QuestionManager


class TestWebSocketGameIntegration:
    """Integration tests for WebSocket manager with game components"""
    
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
        self.wsm = WebSocketManager(self.gsm)
        
        # Create test game
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6
2,1,What is the capital of France?,Paris
2,2,What is the capital of Spain?,Madrid"""
        
        self.csv_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.csv_file.write(csv_content)
        self.csv_file.close()
        
        self.gsm.create_game("integration_test", self.csv_file.name, "admin123")
    
    def teardown_method(self):
        if hasattr(self, 'csv_file'):
            os.unlink(self.csv_file.name)
    
    def test_complete_game_workflow_via_websocket(self):
        """Test complete game from start to finish using WebSocket messages"""
        
        # 1. Connect clients
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        self.wsm.connect_client("team2")
        
        # 2. Admin login
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "integration_test",
            "password": "admin123"
        })
        responses = self.wsm.handle_message("admin1", admin_login)
        assert any(r.event_type == EventType.SUCCESS for r in responses)
        
        # 3. Teams join
        team1_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "integration_test",
            "team_name": "Team Alpha"
        })
        responses = self.wsm.handle_message("team1", team1_join)
        team1_id = None
        for r in responses:
            if r.event_type == EventType.TEAM_JOINED:
                team1_id = r.data["team_id"]
        assert team1_id is not None
        
        team2_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "integration_test",
            "team_name": "Team Beta"
        })
        responses = self.wsm.handle_message("team2", team2_join)
        team2_id = None
        for r in responses:
            if r.event_type == EventType.TEAM_JOINED:
                team2_id = r.data["team_id"]
        assert team2_id is not None
        
        # Verify game state
        game = self.gsm.get_game("integration_test")
        assert len(game.teams) == 2
        assert game.status == GameStatus.WAITING
        
        # 4. Start game
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_game)
        
        game_started_msgs = [r for r in responses if r.event_type == EventType.GAME_STARTED]
        assert len(game_started_msgs) == 3  # Admin + 2 teams
        
        # Verify game state changed
        assert game.status == GameStatus.IN_PROGRESS
        
        # 5. Play through first question
        start_q1 = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_q1)
        
        question_msgs = [r for r in responses if r.event_type == EventType.QUESTION_STARTED]
        assert len(question_msgs) == 3
        
        # Admin sees answer, teams don't
        admin_q_msg = next((r for r in question_msgs if "answer" in r.data), None)
        team_q_msgs = [r for r in question_msgs if "answer" not in r.data]
        assert admin_q_msg is not None
        assert len(team_q_msgs) == 2
        assert admin_q_msg.data["question"] == "What is 2+2?"
        assert admin_q_msg.data["answer"] == "4"
        
        # Verify game state
        assert game.status == GameStatus.QUESTION_ACTIVE
        
        # 6. Teams submit answers
        team1_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("team1", team1_answer)
        assert any(r.event_type == EventType.ANSWER_SUBMITTED for r in responses)
        
        team2_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "5"})
        responses = self.wsm.handle_message("team2", team2_answer)
        assert any(r.event_type == EventType.ANSWER_SUBMITTED for r in responses)
        
        # 7. Close question
        close_q1 = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", close_q1)
        
        closed_msgs = [r for r in responses if r.event_type == EventType.QUESTION_CLOSED]
        assert len(closed_msgs) == 3
        
        # Admin gets answer details
        admin_closed_msg = next((r for r in closed_msgs if "answers" in r.data), None)
        assert admin_closed_msg is not None
        assert len(admin_closed_msg.data["answers"]) == 2
        
        # Verify game state
        assert game.status == GameStatus.QUESTION_CLOSED
        
        # 8. Grade answers
        grade1 = WebSocketMessage(EventType.GRADE_ANSWER, {
            "team_id": team1_id,
            "round_num": 1,
            "question_num": 1,
            "is_correct": True,
            "points": 1
        })
        responses = self.wsm.handle_message("admin1", grade1)
        graded_msgs = [r for r in responses if r.event_type == EventType.ANSWER_GRADED]
        assert len(graded_msgs) == 3
        
        grade2 = WebSocketMessage(EventType.GRADE_ANSWER, {
            "team_id": team2_id,
            "round_num": 1,
            "question_num": 1,
            "is_correct": False,
            "points": 0
        })
        responses = self.wsm.handle_message("admin1", grade2)
        
        # Verify scores updated
        team1_obj = game.teams[team1_id]
        team2_obj = game.teams[team2_id]
        assert team1_obj.score == 1
        assert team2_obj.score == 0
        
        # 9. Move to next question
        next_q = WebSocketMessage(EventType.NEXT_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", next_q)
        
        success_msgs = [r for r in responses if r.event_type == EventType.SUCCESS]
        assert len(success_msgs) == 1
        assert game.current_question == 2
        
        # 10. Get leaderboard
        leaderboard = WebSocketMessage(EventType.GET_LEADERBOARD, {})
        responses = self.wsm.handle_message("team1", leaderboard)
        
        leaderboard_msgs = [r for r in responses if r.event_type == EventType.LEADERBOARD_UPDATE]
        assert len(leaderboard_msgs) == 1
        leaderboard_data = leaderboard_msgs[0].data["leaderboard"]
        assert len(leaderboard_data) == 2
        assert leaderboard_data[0]["name"] == "Team Alpha"
        assert leaderboard_data[0]["score"] == 1
    
    def test_websocket_game_state_synchronization(self):
        """Test that WebSocket operations correctly update game state"""
        
        # Connect and setup
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        
        # Verify initial state
        game = self.gsm.get_game("integration_test")
        assert len(game.teams) == 0
        assert game.status == GameStatus.WAITING
        
        # Admin login via WebSocket
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "integration_test",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        # Team join via WebSocket
        team_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "integration_test",
            "team_name": "Test Team"
        })
        responses = self.wsm.handle_message("team1", team_join)
        
        # Verify game state updated
        assert len(game.teams) == 1
        team_id = list(game.teams.keys())[0]
        assert game.teams[team_id].name == "Test Team"
        
        # Start game via WebSocket
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        # Verify state change
        assert game.status == GameStatus.IN_PROGRESS
        
        # Start question via WebSocket
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_question)
        
        # Verify question state
        assert game.status == GameStatus.QUESTION_ACTIVE
        assert game.current_round == 1
        assert game.current_question == 1
        
        # Submit answer via WebSocket
        submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        self.wsm.handle_message("team1", submit_answer)
        
        # Verify answer recorded
        assert len(game.answers) == 1
        assert game.answers[0].answer_text == "4"
        assert game.answers[0].team_id == team_id
    
    def test_websocket_error_handling_with_game_state(self):
        """Test error handling maintains game state consistency"""
        
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        
        # Try to start game without admin login
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("team1", start_game)  # Non-admin tries
        
        assert any(r.event_type == EventType.ERROR for r in responses)
        
        game = self.gsm.get_game("integration_test")
        assert game.status == GameStatus.WAITING  # State unchanged
        
        # Try to submit answer without being in team
        submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("team1", submit_answer)
        
        assert any(r.event_type == EventType.ERROR for r in responses)
        assert len(game.answers) == 0  # No answer recorded
        
        # Try to join with duplicate team name
        self.wsm.connect_client("team2")
        
        join1 = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "integration_test",
            "team_name": "Test Team"
        })
        self.wsm.handle_message("team1", join1)
        
        join2 = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "integration_test",
            "team_name": "Test Team"  # Duplicate
        })
        responses = self.wsm.handle_message("team2", join2)
        
        assert any(r.event_type == EventType.ERROR for r in responses)
        assert len(game.teams) == 1  # Only one team added
    
    def test_websocket_multi_game_isolation(self):
        """Test WebSocket manager handles multiple games correctly"""
        
        # Create second game
        csv_content2 = """round_num,question_num,question,answer
1,1,Game 2 Question,Game 2 Answer"""
        
        csv_file2 = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        csv_file2.write(csv_content2)
        csv_file2.close()
        
        try:
            self.gsm.create_game("game2", csv_file2.name, "admin456")
            
            # Connect clients to different games
            self.wsm.connect_client("admin1")
            self.wsm.connect_client("admin2")
            self.wsm.connect_client("team1_g1")
            self.wsm.connect_client("team1_g2")
            
            # Admin logins to different games
            admin1_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
                "game_id": "integration_test",
                "password": "admin123"
            })
            self.wsm.handle_message("admin1", admin1_login)
            
            admin2_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
                "game_id": "game2",
                "password": "admin456"
            })
            self.wsm.handle_message("admin2", admin2_login)
            
            # Teams join different games
            team1_join = WebSocketMessage(EventType.JOIN_GAME, {
                "game_id": "integration_test",
                "team_name": "Team Game 1"
            })
            self.wsm.handle_message("team1_g1", team1_join)
            
            team2_join = WebSocketMessage(EventType.JOIN_GAME, {
                "game_id": "game2",
                "team_name": "Team Game 2"
            })
            self.wsm.handle_message("team1_g2", team2_join)
            
            # Verify isolation
            game1 = self.gsm.get_game("integration_test")
            game2 = self.gsm.get_game("game2")
            
            assert len(game1.teams) == 1
            assert len(game2.teams) == 1
            
            # Verify different client sets
            game1_clients = self.wsm.get_game_clients("integration_test")
            game2_clients = self.wsm.get_game_clients("game2")
            
            assert "admin1" in game1_clients
            assert "team1_g1" in game1_clients
            assert "admin2" in game2_clients
            assert "team1_g2" in game2_clients
            
            assert game1_clients.isdisjoint(game2_clients)
            
        finally:
            os.unlink(csv_file2.name)
    
    def test_websocket_client_disconnection_cleanup(self):
        """Test client disconnection properly cleans up game state"""
        
        # Setup game with multiple clients
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        self.wsm.connect_client("team2")
        
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "integration_test",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        team1_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "integration_test",
            "team_name": "Team 1"
        })
        self.wsm.handle_message("team1", team1_join)
        
        team2_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "integration_test",
            "team_name": "Team 2"
        })
        self.wsm.handle_message("team2", team2_join)
        
        # Verify all connected
        clients = self.wsm.get_game_clients("integration_test")
        assert len(clients) == 3
        assert {"admin1", "team1", "team2"} == clients
        
        # Disconnect team1
        self.wsm.disconnect_client("team1")
        
        # Verify cleanup
        clients = self.wsm.get_game_clients("integration_test")
        assert len(clients) == 2
        assert "team1" not in clients
        assert {"admin1", "team2"} == clients
        
        # Game state should still have the team (team disconnection doesn't remove team)
        game = self.gsm.get_game("integration_test")
        assert len(game.teams) == 2  # Teams remain even if client disconnects
        
        # Disconnect admin
        self.wsm.disconnect_client("admin1")
        
        # Verify admin cleanup
        clients = self.wsm.get_game_clients("integration_test")
        assert len(clients) == 1
        assert clients == {"team2"}
    
    def test_websocket_broadcast_functionality(self):
        """Test message broadcasting to all game clients"""
        
        # Setup multiple clients in same game
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        self.wsm.connect_client("team2")
        self.wsm.connect_client("team3")
        
        # Add all to game
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "integration_test",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        for i, team_client in enumerate(["team1", "team2", "team3"], 1):
            join_msg = WebSocketMessage(EventType.JOIN_GAME, {
                "game_id": "integration_test",
                "team_name": f"Team {i}"
            })
            self.wsm.handle_message(team_client, join_msg)
        
        # Start game (broadcasts to all)
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_game)
        
        # Should broadcast to all 4 clients
        game_started_msgs = [r for r in responses if r.event_type == EventType.GAME_STARTED]
        assert len(game_started_msgs) == 4
        
        # Each message should have target_client specified
        target_clients = {msg.data.get("target_client") for msg in game_started_msgs}
        assert target_clients == {"admin1", "team1", "team2", "team3"}
        
        # Start question (broadcasts to all with different data)
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_question)
        
        question_msgs = [r for r in responses if r.event_type == EventType.QUESTION_STARTED]
        assert len(question_msgs) == 4
        
        # Admin should see answer, teams should not
        admin_msgs = [msg for msg in question_msgs if "answer" in msg.data]
        team_msgs = [msg for msg in question_msgs if "answer" not in msg.data]
        
        assert len(admin_msgs) == 1  # Only admin gets answer
        assert len(team_msgs) == 3   # Teams don't get answer
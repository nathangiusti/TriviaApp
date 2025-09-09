"""
Complete workflow tests - consolidated integration and end-to-end workflow testing
"""
import pytest
from backend.websocket_manager import WebSocketManager, WebSocketMessage, EventType
from backend.game_state import GameStateManager, GameStatus
from backend.question_manager import QuestionManager
from .test_helpers import create_temp_csv, cleanup_temp_file, STANDARD_CSV_CONTENT


class TestCompleteGameWorkflows:
    """Test complete game workflows from start to finish"""
    
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
        self.wsm = WebSocketManager(self.gsm)
        self.csv_file = create_temp_csv(STANDARD_CSV_CONTENT)
    
    def teardown_method(self):
        cleanup_temp_file(self.csv_file)
    
    def test_complete_game_workflow_via_websocket(self):
        """Test a complete game workflow through WebSocket messages"""
        
        # 1. Create game
        game = self.gsm.create_game("workflow_test", self.csv_file, "admin123")
        assert game.game_id == "workflow_test"
        
        # 2. Connect clients
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        self.wsm.connect_client("team2")
        
        # 3. Admin login
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "workflow_test",
            "password": "admin123"
        })
        responses = self.wsm.handle_message("admin1", admin_login)
        
        success_msg = next(r for r in responses if r.event_type == EventType.SUCCESS)
        assert success_msg.data["is_admin"] is True
        
        # 4. Teams join
        team1_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "workflow_test",
            "team_name": "Team Alpha"
        })
        responses = self.wsm.handle_message("team1", team1_join)
        team1_id = next(r for r in responses if r.event_type == EventType.TEAM_JOINED).data["team_id"]
        
        team2_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "workflow_test",
            "team_name": "Team Beta"
        })
        responses = self.wsm.handle_message("team2", team2_join)
        team2_id = next(r for r in responses if r.event_type == EventType.TEAM_JOINED).data["team_id"]
        
        # 5. Start game
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_game)
        
        game_started_msgs = [r for r in responses if r.event_type == EventType.GAME_STARTED]
        assert len(game_started_msgs) == 3  # admin + 2 teams
        
        # 6. Play through first question
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_question)
        
        question_started_msgs = [r for r in responses if r.event_type == EventType.QUESTION_STARTED]
        assert len(question_started_msgs) == 3
        
        # Teams submit answers
        team1_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})  # Correct
        self.wsm.handle_message("team1", team1_answer)
        
        team2_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "5"})  # Incorrect
        self.wsm.handle_message("team2", team2_answer)
        
        # Close question
        close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", close_question)
        
        # Verify automatic grading occurred
        question_closed_msgs = [r for r in responses if r.event_type == EventType.QUESTION_CLOSED]
        admin_msg = next(r for r in question_closed_msgs if "answers" in r.data)
        
        answers = admin_msg.data["answers"]
        assert len(answers) == 2
        
        # Find team answers
        team1_answer_data = next(a for a in answers if a["team_name"] == "Team Alpha")
        team2_answer_data = next(a for a in answers if a["team_name"] == "Team Beta")
        
        assert team1_answer_data["is_correct"] is True
        assert team1_answer_data["points_awarded"] == 1
        assert team2_answer_data["is_correct"] is False
        assert team2_answer_data["points_awarded"] == 0
        
        # Verify scores updated
        game = self.gsm.get_game("workflow_test")
        assert game.teams[team1_id].score == 1
        assert game.teams[team2_id].score == 0
        
        # 7. Move to next question
        next_question = WebSocketMessage(EventType.NEXT_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", next_question)
        
        success_msg = next(r for r in responses if r.event_type == EventType.SUCCESS)
        assert "Moved to next question" in success_msg.data["message"]
        
        # Verify game state
        assert game.current_question == 2
        assert game.status == GameStatus.IN_PROGRESS
    
    def test_answer_grading_workflow_integration(self):
        """Test complete answer submission, grading, and result distribution workflow"""
        
        # Setup
        game = self.gsm.create_game("grading_test", self.csv_file, "admin123")
        
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        self.wsm.connect_client("team2")
        
        # Admin login and team joins
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "grading_test",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        team1_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "grading_test",
            "team_name": "Team Alpha"
        })
        responses = self.wsm.handle_message("team1", team1_join)
        team1_id = next(r for r in responses if r.event_type == EventType.TEAM_JOINED).data["team_id"]
        
        team2_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "grading_test",
            "team_name": "Team Beta"
        })
        responses = self.wsm.handle_message("team2", team2_join)
        team2_id = next(r for r in responses if r.event_type == EventType.TEAM_JOINED).data["team_id"]
        
        # Start game and question
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_question)
        
        # Verify admin sees correct answer
        admin_question = next(r for r in responses if r.event_type == EventType.QUESTION_STARTED and "answer" in r.data)
        assert admin_question.data["answer"] == "4"
        
        # Teams submit answers - one correct, one incorrect
        team1_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})  # Correct
        responses = self.wsm.handle_message("team1", team1_answer)
        
        # Verify admin gets notification with auto-correct detection
        admin_notification = next(r for r in responses if r.event_type == EventType.ANSWER_SUBMITTED and "team_name" in r.data)
        assert admin_notification.data["team_name"] == "Team Alpha"
        assert admin_notification.data["is_auto_correct"] is True
        
        team2_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "wrong"})  # Incorrect
        responses = self.wsm.handle_message("team2", team2_answer)
        
        admin_notification = next(r for r in responses if r.event_type == EventType.ANSWER_SUBMITTED and "team_name" in r.data)
        assert admin_notification.data["team_name"] == "Team Beta"
        assert admin_notification.data["is_auto_correct"] is False
        
        # Manual grading of Team Beta's incorrect answer
        grade_team2 = WebSocketMessage(EventType.GRADE_ANSWER, {
            "team_id": team2_id,
            "round_num": 1,
            "question_num": 1,
            "is_correct": False,
            "points": 0
        })
        responses = self.wsm.handle_message("admin1", grade_team2)
        
        grading_msgs = [r for r in responses if r.event_type == EventType.ANSWER_GRADED]
        assert len(grading_msgs) == 3  # admin + 2 teams
        
        # Close question and verify results sent to players
        close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", close_question)
        
        # Find player result messages
        team1_result = None
        team2_result = None
        
        for response in responses:
            if response.event_type == EventType.QUESTION_CLOSED and "correct_answer" in response.data:
                target_client = response.data.get("target_client")
                if target_client == "team1":
                    team1_result = response.data
                elif target_client == "team2":
                    team2_result = response.data
        
        # Verify Team Alpha (correct) result
        assert team1_result is not None
        assert team1_result["correct_answer"] == "4"
        assert team1_result["team_answer"] == "4"
        assert team1_result["team_correct"] is True
        
        # Verify Team Beta (incorrect) result
        assert team2_result is not None
        assert team2_result["correct_answer"] == "4"
        assert team2_result["team_answer"] == "wrong"
        assert team2_result["team_correct"] is False
        
        # Verify leaderboard shows updated scores
        leaderboard = team1_result["leaderboard"]
        assert len(leaderboard) == 2
        
        alpha_entry = next(team for team in leaderboard if team["name"] == "Team Alpha")
        beta_entry = next(team for team in leaderboard if team["name"] == "Team Beta")
        
        assert alpha_entry["score"] == 1  # Got question right
        assert beta_entry["score"] == 0   # Got question wrong
    
    def test_game_completion_workflow(self):
        """Test complete game workflow through to finish"""
        
        # Create smaller game for faster completion
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            game = self.gsm.create_game("completion_test", csv_file, "admin123")
            
            self.wsm.connect_client("admin1")
            self.wsm.connect_client("team1")
            
            # Setup
            admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
                "game_id": "completion_test",
                "password": "admin123"
            })
            self.wsm.handle_message("admin1", admin_login)
            
            team_join = WebSocketMessage(EventType.JOIN_GAME, {
                "game_id": "completion_test",
                "team_name": "Test Team"
            })
            self.wsm.handle_message("team1", team_join)
            
            start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
            self.wsm.handle_message("admin1", start_game)
            
            # Play through all questions
            for question_num in [1, 2]:
                # Start question
                start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
                self.wsm.handle_message("admin1", start_question)
                
                # Submit answer
                answer = "4" if question_num == 1 else "6"
                submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": answer})
                self.wsm.handle_message("team1", submit_answer)
                
                # Close question
                close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
                self.wsm.handle_message("admin1", close_question)
                
                # Move to next question (except for last)
                if question_num < 2:
                    next_question = WebSocketMessage(EventType.NEXT_QUESTION, {"password": "admin123"})
                    self.wsm.handle_message("admin1", next_question)
            
            # Try to move past last question - should finish game
            next_question = WebSocketMessage(EventType.NEXT_QUESTION, {"password": "admin123"})
            responses = self.wsm.handle_message("admin1", next_question)
            
            # Should get game_finished messages
            game_finished_msgs = [r for r in responses if r.event_type == EventType.GAME_FINISHED]
            assert len(game_finished_msgs) == 2  # admin + team
            
            # Verify final leaderboard
            team_msg = next(r for r in game_finished_msgs if r.data.get("target_client") == "team1")
            final_leaderboard = team_msg.data["final_leaderboard"]
            assert len(final_leaderboard) == 1
            assert final_leaderboard[0]["name"] == "Test Team"
            assert final_leaderboard[0]["score"] == 2  # Both questions correct
            
            # Verify game status
            game = self.gsm.get_game("completion_test")
            assert game.status == GameStatus.FINISHED
        
        finally:
            cleanup_temp_file(csv_file)
    
    def test_multi_game_isolation(self):
        """Test that multiple games operate independently"""
        
        # Create two separate games
        game1 = self.gsm.create_game("game1", self.csv_file, "admin123")
        game2 = self.gsm.create_game("game2", self.csv_file, "admin456")
        
        # Connect clients to different games
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("admin2")
        self.wsm.connect_client("team1a")
        self.wsm.connect_client("team2a")
        
        # Admin logins
        admin1_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "game1",
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
            "game_id": "game1",
            "team_name": "Game1 Team"
        })
        self.wsm.handle_message("team1a", team1_join)
        
        team2_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "game2",
            "team_name": "Game2 Team"
        })
        self.wsm.handle_message("team2a", team2_join)
        
        # Verify game isolation
        game1_clients = self.wsm.get_game_clients("game1")
        game2_clients = self.wsm.get_game_clients("game2")
        
        assert "admin1" in game1_clients
        assert "team1a" in game1_clients
        assert "admin2" not in game1_clients
        assert "team2a" not in game1_clients
        
        assert "admin2" in game2_clients
        assert "team2a" in game2_clients
        assert "admin1" not in game2_clients
        assert "team1a" not in game2_clients
        
        # Start one game, verify other is unaffected
        start_game1 = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game1)
        
        assert game1.status == GameStatus.IN_PROGRESS
        assert game2.status == GameStatus.WAITING
    
    def test_websocket_client_disconnection_cleanup(self):
        """Test that client disconnections are properly cleaned up"""
        
        game = self.gsm.create_game("disconnect_test", self.csv_file, "admin123")
        
        self.wsm.connect_client("client1")
        self.wsm.connect_client("client2")
        
        # Both clients join game
        join_message = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "disconnect_test",
            "team_name": "Team Alpha"
        })
        self.wsm.handle_message("client1", join_message)
        
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "disconnect_test",
            "password": "admin123"
        })
        self.wsm.handle_message("client2", admin_login)
        
        # Verify both are in game
        clients = self.wsm.get_game_clients("disconnect_test")
        assert len(clients) == 2
        assert "client1" in clients
        assert "client2" in clients
        
        # Disconnect one client
        self.wsm.disconnect_client("client1")
        
        # Verify cleanup
        clients = self.wsm.get_game_clients("disconnect_test")
        assert len(clients) == 1
        assert "client1" not in clients
        assert "client2" in clients
        
        # Verify client1 is completely removed
        assert "client1" not in self.wsm.connections
        assert "client2" in self.wsm.connections
    
    def test_error_handling_integration(self):
        """Test error handling throughout the system"""
        
        game = self.gsm.create_game("error_test", self.csv_file, "admin123")
        
        # Test unconnected client
        message = WebSocketMessage(EventType.JOIN_GAME, {"game_id": "error_test", "team_name": "Test"})
        responses = self.wsm.handle_message("unconnected", message)
        
        assert len(responses) == 1
        assert responses[0].event_type == EventType.ERROR
        assert "Client not connected" in responses[0].data["message"]
        
        # Connect client and test various error conditions
        self.wsm.connect_client("client1")
        
        # Invalid game
        invalid_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "nonexistent",
            "team_name": "Test Team"
        })
        responses = self.wsm.handle_message("client1", invalid_join)
        
        assert responses[0].event_type == EventType.ERROR
        assert "Game not found" in responses[0].data["message"]
        
        # Invalid admin password
        invalid_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "error_test",
            "password": "wrong"
        })
        responses = self.wsm.handle_message("client1", invalid_login)
        
        assert responses[0].event_type == EventType.ERROR
        assert "Invalid admin password" in responses[0].data["message"]
        
        # Non-admin trying admin actions
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        responses = self.wsm.handle_message("client1", start_game)
        
        assert responses[0].event_type == EventType.ERROR
        assert "Admin access required" in responses[0].data["message"]
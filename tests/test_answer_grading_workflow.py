import pytest
import os
from backend.websocket_manager import WebSocketManager, WebSocketMessage, EventType
from backend.game_state import GameStateManager, GameStatus
from backend.question_manager import QuestionManager
from .test_helpers import create_temp_csv, cleanup_temp_file


class TestAnswerGradingWorkflow:
    """Test the complete answer grading workflow"""
    
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
        self.wsm = WebSocketManager(self.gsm)
        
        # Create test game with known questions and answers
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6
2,1,What is the capital of France?,Paris
2,2,What is the capital of Spain?,Madrid"""
        
        self.csv_file_path = create_temp_csv(csv_content)
        self.gsm.create_game("answer_test", self.csv_file_path, "admin123")
    
    def teardown_method(self):
        if hasattr(self, 'csv_file_path'):
            cleanup_temp_file(self.csv_file_path)
    
    def test_answer_submission_admin_display_and_grading_workflow(self):
        """Test complete workflow: submit answers -> admin sees them -> grades them -> teams get feedback after question closes"""
        
        # Setup: Connect admin and teams
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        self.wsm.connect_client("team2")
        
        # Admin login
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "answer_test",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        # Teams join
        team1_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "answer_test",
            "team_name": "Team Alpha"
        })
        responses = self.wsm.handle_message("team1", team1_join)
        team1_id = None
        for r in responses:
            if r.event_type == EventType.TEAM_JOINED:
                team1_id = r.data["team_id"]
        
        team2_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "answer_test", 
            "team_name": "Team Beta"
        })
        responses = self.wsm.handle_message("team2", team2_join)
        team2_id = None
        for r in responses:
            if r.event_type == EventType.TEAM_JOINED:
                team2_id = r.data["team_id"]
        
        # Start game and question
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", start_question)
        
        # Verify admin sees the correct answer in question start
        admin_question_msg = None
        for r in responses:
            if r.event_type == EventType.QUESTION_STARTED and "answer" in r.data:
                admin_question_msg = r
                break
        
        assert admin_question_msg is not None
        assert admin_question_msg.data["answer"] == "4"  # Correct answer from CSV
        assert admin_question_msg.data["question"] == "What is 2+2?"
        
        # STEP 1: Teams submit answers
        admin_notifications = []
        
        # Team 1 submits correct answer
        submit_answer1 = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("team1", submit_answer1)
        
        # Capture admin notification for team 1
        for r in responses:
            if r.event_type == EventType.ANSWER_SUBMITTED and "team_name" in r.data:
                admin_notifications.append(r)
        
        # Team 2 submits incorrect answer  
        submit_answer2 = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "5"})
        responses = self.wsm.handle_message("team2", submit_answer2)
        
        # Capture admin notification for team 2
        for r in responses:
            if r.event_type == EventType.ANSWER_SUBMITTED and "team_name" in r.data:
                admin_notifications.append(r)
        
        # STEP 2: Verify admin sees submitted answers with automatic correctness detection
        assert len(admin_notifications) == 2
        
        # Verify automatic correctness detection in admin notifications
        team1_notification = None
        team2_notification = None
        
        for notification in admin_notifications:
            if notification.data["team_name"] == "Team Alpha":
                team1_notification = notification
            elif notification.data["team_name"] == "Team Beta":
                team2_notification = notification
        
        assert team1_notification is not None
        assert team2_notification is not None
        
        # Verify Team Alpha's correct answer is detected as correct
        assert team1_notification.data["answer"] == "4"
        assert team1_notification.data["is_auto_correct"] is True
        assert team1_notification.data["correct_answer"] == "4"
        
        # Verify Team Beta's incorrect answer is detected as incorrect  
        assert team2_notification.data["answer"] == "5"
        assert team2_notification.data["is_auto_correct"] is False
        assert team2_notification.data["correct_answer"] == "4"
        
        # STEP 4: Test admin grading workflow
        # Admin grades Team 1 as correct (matches auto-detection)
        grade_answer1 = WebSocketMessage(EventType.GRADE_ANSWER, {
            "team_id": team1_id,
            "round_num": 1,
            "question_num": 1,
            "is_correct": True,
            "points": 1
        })
        responses = self.wsm.handle_message("admin1", grade_answer1)
        
        # Admin grades Team 2 as incorrect (matches auto-detection)
        grade_answer2 = WebSocketMessage(EventType.GRADE_ANSWER, {
            "team_id": team2_id,
            "round_num": 1,
            "question_num": 1,
            "is_correct": False,
            "points": 0
        })
        responses = self.wsm.handle_message("admin1", grade_answer2)
        
        # Verify grading results are broadcast
        grading_results = [r for r in responses if r.event_type == EventType.ANSWER_GRADED]
        
        # Currently this should work but might not be properly broadcasting
        # This part might fail if grading results aren't properly sent to teams
        
        # STEP 5: Test delayed feedback - teams should not get correctness info until question closes
        # Currently teams get ANSWER_SUBMITTED confirmation but no correctness info
        # This should remain the case until close_question
        
        # Close the question
        close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", close_question)
        
        # After closing, teams should get their feedback
        question_closed_msgs = [r for r in responses if r.event_type == EventType.QUESTION_CLOSED]
        
        # This tests the current behavior, but we might need to enhance it
        # to ensure teams get proper feedback with their correctness info
        
        # STEP 6: Verify final scores
        game = self.gsm.get_game("answer_test")
        team1_obj = game.teams[team1_id]
        team2_obj = game.teams[team2_id]
        
        # Team 1 should have 1 point (correct answer)
        # Team 2 should have 0 points (incorrect answer)
        assert team1_obj.score == 1
        assert team2_obj.score == 0
        
    def test_automatic_correctness_detection_enhancement(self):
        """Test that admin should get automatic correctness detection in answer submissions"""
        
        # This test specifically focuses on the enhancement needed:
        # When teams submit answers, admin should immediately see if they're correct/incorrect
        
        # Setup
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "answer_test",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        team_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "answer_test",
            "team_name": "Test Team"
        })
        responses = self.wsm.handle_message("team1", team_join)
        team_id = responses[0].data["team_id"]
        
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_question)
        
        # Submit a correct answer
        submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("team1", submit_answer)
        
        # Find the admin notification
        admin_notification = None
        for r in responses:
            if r.event_type == EventType.ANSWER_SUBMITTED and "team_name" in r.data:
                admin_notification = r
                break
        
        assert admin_notification is not None
        
        # THIS IS WHAT WE WANT TO IMPLEMENT:
        # The admin notification should include automatic correctness detection
        # Currently it probably doesn't, so this test should fail initially
        
        # Expected enhancement: admin notification should include:
        # - is_auto_correct: True/False (automatic detection)
        # - correct_answer: "4" (for admin reference)
        # - team_answer: "4" (what team submitted)
        
        # This assertion will likely FAIL initially, driving the implementation
        try:
            assert "is_auto_correct" in admin_notification.data
            assert "correct_answer" in admin_notification.data
            assert admin_notification.data["is_auto_correct"] is True
            assert admin_notification.data["correct_answer"] == "4"
        except (AssertionError, KeyError):
            # This is expected to fail initially - this drives our implementation
            pytest.fail("Admin should receive automatic correctness detection in answer submissions - FEATURE NOT YET IMPLEMENTED")
    
    def test_teams_no_feedback_until_question_closed(self):
        """Test that teams don't get correctness feedback until question is closed"""
        
        # Setup
        self.wsm.connect_client("admin1")
        self.wsm.connect_client("team1")
        
        admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
            "game_id": "answer_test",
            "password": "admin123"
        })
        self.wsm.handle_message("admin1", admin_login)
        
        team_join = WebSocketMessage(EventType.JOIN_GAME, {
            "game_id": "answer_test",
            "team_name": "Test Team"
        })
        responses = self.wsm.handle_message("team1", team_join)
        team_id = responses[0].data["team_id"]
        
        start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_game)
        
        start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
        self.wsm.handle_message("admin1", start_question)
        
        # Team submits answer
        submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "4"})
        responses = self.wsm.handle_message("team1", submit_answer)
        
        # Team should only get submission confirmation, NO correctness info
        team_response = None
        for r in responses:
            if r.event_type == EventType.ANSWER_SUBMITTED and "team_name" not in r.data:
                team_response = r
                break
        
        assert team_response is not None
        assert "answer" in team_response.data  # Confirmation of what they submitted
        assert "submitted_at" in team_response.data
        
        # Team should NOT get correctness info yet
        assert "is_correct" not in team_response.data
        assert "points_awarded" not in team_response.data
        
        # Admin grades the answer
        grade_answer = WebSocketMessage(EventType.GRADE_ANSWER, {
            "team_id": team_id,
            "round_num": 1,
            "question_num": 1,
            "is_correct": True,
            "points": 1
        })
        responses = self.wsm.handle_message("admin1", grade_answer)
        
        # Even after grading, team should not get feedback until question closes
        # (Current implementation might already handle this correctly)
        
        # Close question
        close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
        responses = self.wsm.handle_message("admin1", close_question)
        
        # NOW teams should get their feedback
        # Find team feedback in question_closed responses
        team_feedback = None
        for r in responses:
            if r.event_type == EventType.QUESTION_CLOSED and "target_client" in r.data:
                target = r.data.get("target_client")
                if target == "team1":  # This is for our team
                    team_feedback = r
                    break
        
        # Team should now have access to results
        # This might need enhancement to include per-team results
        assert team_feedback is not None
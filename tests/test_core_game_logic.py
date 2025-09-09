"""
Core game logic tests - consolidated unit tests for game components
"""
import pytest
import tempfile
import os
from backend.game_state import GameStateManager, GameStatus, Team, Answer, GameSession
from backend.question_manager import QuestionManager, Question
from .test_helpers import create_temp_csv, cleanup_temp_file, STANDARD_CSV_CONTENT


class TestTeam:
    """Test Team dataclass"""
    
    def test_valid_team_creation(self):
        team = Team("Test Team")
        assert team.name == "Test Team"
        assert team.score == 0
        assert team.team_id is not None
        assert len(team.team_id) > 0
    
    def test_empty_team_name_raises_error(self):
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            Team("")
        
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            Team("   ")


class TestAnswer:
    """Test Answer dataclass"""
    
    def test_valid_answer_creation(self):
        answer = Answer("team123", 1, 1, "Test answer")
        assert answer.team_id == "team123"
        assert answer.question_round == 1
        assert answer.question_num == 1
        assert answer.answer_text == "Test answer"
        assert answer.is_correct is None
        assert answer.points_awarded == 0


class TestGameSession:
    """Test GameSession dataclass"""
    
    def test_valid_game_session_creation(self):
        game = GameSession("test_game", "test.csv", "admin123")
        assert game.game_id == "test_game"
        assert game.csv_file_path == "test.csv"
        assert game.admin_password == "admin123"
        assert game.status == GameStatus.WAITING
        assert len(game.teams) == 0
        assert len(game.answers) == 0
    
    def test_invalid_game_session_raises_errors(self):
        with pytest.raises(ValueError, match="Game ID cannot be empty"):
            GameSession("", "test.csv", "admin123")
        
        with pytest.raises(ValueError, match="CSV file path cannot be empty"):
            GameSession("test_game", "", "admin123")
        
        with pytest.raises(ValueError, match="Admin password cannot be empty"):
            GameSession("test_game", "test.csv", "")


class TestQuestion:
    """Test Question dataclass"""
    
    def test_valid_question_creation(self):
        question = Question(1, 1, "What is 2+2?", "4")
        assert question.round_num == 1
        assert question.question_num == 1
        assert question.question == "What is 2+2?"
        assert question.answer == "4"
    
    def test_empty_question_raises_error(self):
        with pytest.raises(ValueError, match="Question cannot be empty"):
            Question(1, 1, "", "4")
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            Question(1, 1, "   ", "4")
    
    def test_empty_answer_raises_error(self):
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            Question(1, 1, "What is 2+2?", "")
        
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            Question(1, 1, "What is 2+2?", "   ")
    
    def test_invalid_round_number(self):
        with pytest.raises(ValueError, match="Round number must be positive"):
            Question(0, 1, "What is 2+2?", "4")
        
        with pytest.raises(ValueError, match="Round number must be positive"):
            Question(-1, 1, "What is 2+2?", "4")
    
    def test_invalid_question_number(self):
        with pytest.raises(ValueError, match="Question number must be positive"):
            Question(1, 0, "What is 2+2?", "4")
        
        with pytest.raises(ValueError, match="Question number must be positive"):
            Question(1, -1, "What is 2+2?", "4")


class TestQuestionManager:
    """Test QuestionManager functionality"""
    
    def setup_method(self):
        self.qm = QuestionManager()
    
    def test_load_valid_csv(self):
        csv_content = STANDARD_CSV_CONTENT
        csv_file = create_temp_csv(csv_content)
        
        try:
            self.qm.load_questions_from_csv("test_game", csv_file)
            questions = self.qm.get_questions_for_game("test_game")
            assert len(questions) == 4
            
            # Check first question
            q1 = questions[0]
            assert q1.round_num == 1
            assert q1.question_num == 1
            assert q1.question == "What is 2+2?"
            assert q1.answer == "4"
        finally:
            cleanup_temp_file(csv_file)
    
    def test_load_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.qm.load_questions_from_csv("test_game", "nonexistent.csv")
    
    def test_load_csv_missing_columns(self):
        csv_content = "invalid,columns\n1,2"
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="CSV must contain columns"):
                self.qm.load_questions_from_csv("test_game", csv_file)
        finally:
            cleanup_temp_file(csv_file)
    
    def test_load_csv_empty_questions(self):
        csv_content = """round_num,question_num,question,answer
1,1,,4"""
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="Question cannot be empty"):
                self.qm.load_questions_from_csv("test_game", csv_file)
        finally:
            cleanup_temp_file(csv_file)
    
    def test_load_csv_empty_answers(self):
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,"""
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="Answer cannot be empty"):
                self.qm.load_questions_from_csv("test_game", csv_file)
        finally:
            cleanup_temp_file(csv_file)
    
    def test_load_empty_csv(self):
        csv_content = "round_num,question_num,question,answer"
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="CSV file contains no valid questions"):
                self.qm.load_questions_from_csv("test_game", csv_file)
        finally:
            cleanup_temp_file(csv_file)
    
    def test_get_questions_for_nonexistent_game(self):
        with pytest.raises(ValueError, match="No questions loaded for game: nonexistent_game"):
            self.qm.get_questions_for_game("nonexistent_game")
    
    def test_get_question_by_round_and_num(self):
        csv_file = create_temp_csv(STANDARD_CSV_CONTENT)
        
        try:
            self.qm.load_questions_from_csv("test_game", csv_file)
            
            question = self.qm.get_question_by_round_and_num("test_game", 1, 2)
            assert question is not None
            assert question.question == "What is the capital of France?"
            assert question.answer == "Paris"
            
            # Test nonexistent question
            question = self.qm.get_question_by_round_and_num("test_game", 99, 99)
            assert question is None
        finally:
            cleanup_temp_file(csv_file)
    
    def test_get_total_questions(self):
        csv_file = create_temp_csv(STANDARD_CSV_CONTENT)
        
        try:
            self.qm.load_questions_from_csv("test_game", csv_file)
            total = self.qm.get_total_questions("test_game")
            assert total == 4
            
            # Test nonexistent game
            with pytest.raises(ValueError, match="No questions loaded for game: nonexistent_game"):
                self.qm.get_total_questions("nonexistent_game")
        finally:
            cleanup_temp_file(csv_file)
    
    def test_get_questions_for_round(self):
        csv_file = create_temp_csv(STANDARD_CSV_CONTENT)
        
        try:
            self.qm.load_questions_from_csv("test_game", csv_file)
            
            round1_questions = self.qm.get_questions_for_round("test_game", 1)
            assert len(round1_questions) == 2
            
            round2_questions = self.qm.get_questions_for_round("test_game", 2)
            assert len(round2_questions) == 2
            
            # Test nonexistent round
            round99_questions = self.qm.get_questions_for_round("test_game", 99)
            assert len(round99_questions) == 0
        finally:
            cleanup_temp_file(csv_file)
    
    def test_get_rounds_for_game(self):
        csv_file = create_temp_csv(STANDARD_CSV_CONTENT)
        
        try:
            self.qm.load_questions_from_csv("test_game", csv_file)
            rounds = self.qm.get_rounds_for_game("test_game")
            assert rounds == [1, 2]
            
            # Test nonexistent game
            with pytest.raises(ValueError, match="No questions loaded for game: nonexistent_game"):
                self.qm.get_rounds_for_game("nonexistent_game")
        finally:
            cleanup_temp_file(csv_file)
    
    def test_multiple_games(self):
        csv_file1 = create_temp_csv(STANDARD_CSV_CONTENT)
        csv_content2 = """round_num,question_num,question,answer
1,1,Different question?,Different answer"""
        csv_file2 = create_temp_csv(csv_content2)
        
        try:
            self.qm.load_questions_from_csv("game1", csv_file1)
            self.qm.load_questions_from_csv("game2", csv_file2)
            
            game1_questions = self.qm.get_questions_for_game("game1")
            game2_questions = self.qm.get_questions_for_game("game2")
            
            assert len(game1_questions) == 4
            assert len(game2_questions) == 1
            assert game1_questions[0].question == "What is 2+2?"
            assert game2_questions[0].question == "Different question?"
        finally:
            cleanup_temp_file(csv_file1)
            cleanup_temp_file(csv_file2)


class TestGameStateManager:
    """Test GameStateManager functionality"""
    
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
        self.csv_file = create_temp_csv(STANDARD_CSV_CONTENT)
    
    def teardown_method(self):
        cleanup_temp_file(self.csv_file)
    
    def test_create_game_success(self):
        game = self.gsm.create_game("test_game", self.csv_file, "admin123")
        assert game.game_id == "test_game"
        assert game.admin_password == "admin123"
        assert game.status == GameStatus.WAITING
        
        # Verify questions were loaded
        questions = self.qm.get_questions_for_game("test_game")
        assert len(questions) == 4
    
    def test_create_duplicate_game_raises_error(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        
        with pytest.raises(ValueError, match="Game test_game already exists"):
            self.gsm.create_game("test_game", self.csv_file, "admin456")
    
    def test_add_team_success(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        
        assert team.name == "Team Alpha"
        assert team.team_id is not None
        
        game = self.gsm.get_game("test_game")
        assert len(game.teams) == 1
        assert team.team_id in game.teams
    
    def test_add_duplicate_team_name_raises_error(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        self.gsm.add_team("test_game", "Team Alpha")
        
        with pytest.raises(ValueError, match="Team name 'Team Alpha' already exists"):
            self.gsm.add_team("test_game", "Team Alpha")
    
    def test_add_team_to_nonexistent_game_raises_error(self):
        with pytest.raises(ValueError, match="Game nonexistent not found"):
            self.gsm.add_team("nonexistent", "Team Alpha")
    
    def test_add_team_after_game_started_raises_error(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        
        with pytest.raises(ValueError, match="Cannot add teams after game has started"):
            self.gsm.add_team("test_game", "Team Beta")
    
    def test_start_game_success(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        self.gsm.add_team("test_game", "Team Alpha")
        
        result = self.gsm.start_game("test_game", "admin123")
        assert result is True
        
        game = self.gsm.get_game("test_game")
        assert game.status == GameStatus.IN_PROGRESS
        assert game.started_at is not None
    
    def test_start_game_invalid_password_raises_error(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        self.gsm.add_team("test_game", "Team Alpha")
        
        with pytest.raises(ValueError, match="Invalid admin password"):
            self.gsm.start_game("test_game", "wrongpassword")
    
    def test_start_game_no_teams_raises_error(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        
        with pytest.raises(ValueError, match="Cannot start game with no teams"):
            self.gsm.start_game("test_game", "admin123")
    
    def test_start_question_success(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        
        question = self.gsm.start_question("test_game", "admin123")
        assert question.question == "What is 2+2?"
        assert question.answer == "4"
        
        game = self.gsm.get_game("test_game")
        assert game.status == GameStatus.QUESTION_ACTIVE
    
    def test_submit_answer_success(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        self.gsm.start_question("test_game", "admin123")
        
        answer = self.gsm.submit_answer("test_game", team.team_id, "4")
        assert answer.answer_text == "4"
        assert answer.team_id == team.team_id
        assert answer.question_round == 1
        assert answer.question_num == 1
    
    def test_submit_duplicate_answer_raises_error(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        self.gsm.start_question("test_game", "admin123")
        
        self.gsm.submit_answer("test_game", team.team_id, "4")
        
        with pytest.raises(ValueError, match="Team has already submitted an answer"):
            self.gsm.submit_answer("test_game", team.team_id, "5")
    
    def test_close_question_success(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        self.gsm.start_question("test_game", "admin123")
        self.gsm.submit_answer("test_game", team.team_id, "4")
        
        answers = self.gsm.close_question("test_game", "admin123")
        assert len(answers) == 1
        assert answers[0].is_correct is True
        assert answers[0].points_awarded == 1
        
        game = self.gsm.get_game("test_game")
        assert game.status == GameStatus.QUESTION_CLOSED
        assert game.teams[team.team_id].score == 1
    
    def test_grade_answer_correct(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        self.gsm.start_question("test_game", "admin123")
        self.gsm.submit_answer("test_game", team.team_id, "wrong")
        self.gsm.close_question("test_game", "admin123")
        
        answer = self.gsm.grade_answer("test_game", team.team_id, 1, 1, True, 1)
        assert answer.is_correct is True
        assert answer.points_awarded == 1
        
        game = self.gsm.get_game("test_game")
        assert game.teams[team.team_id].score == 1
    
    def test_grade_answer_incorrect(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        self.gsm.start_question("test_game", "admin123")
        self.gsm.submit_answer("test_game", team.team_id, "wrong")
        self.gsm.close_question("test_game", "admin123")
        
        answer = self.gsm.grade_answer("test_game", team.team_id, 1, 1, False, 0)
        assert answer.is_correct is False
        assert answer.points_awarded == 0
        
        game = self.gsm.get_game("test_game")
        assert game.teams[team.team_id].score == 0
    
    def test_next_question_within_round(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        self.gsm.start_question("test_game", "admin123")
        self.gsm.submit_answer("test_game", team.team_id, "4")
        self.gsm.close_question("test_game", "admin123")
        
        next_question = self.gsm.next_question("test_game", "admin123")
        assert next_question.question == "What is the capital of France?"
        
        game = self.gsm.get_game("test_game")
        assert game.current_round == 1
        assert game.current_question == 2
        assert game.status == GameStatus.IN_PROGRESS
    
    def test_next_question_next_round(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        
        # Complete round 1
        for q_num in [1, 2]:
            self.gsm.start_question("test_game", "admin123")
            self.gsm.submit_answer("test_game", team.team_id, "answer")
            self.gsm.close_question("test_game", "admin123")
            if q_num < 2:
                self.gsm.next_question("test_game", "admin123")
        
        # Move to round 2
        next_question = self.gsm.next_question("test_game", "admin123")
        assert next_question.question == "What is the largest planet?"
        
        game = self.gsm.get_game("test_game")
        assert game.current_round == 2
        assert game.current_question == 1
    
    def test_game_finishes_when_no_more_questions(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team = self.gsm.add_team("test_game", "Team Alpha")
        self.gsm.start_game("test_game", "admin123")
        
        # Complete all questions
        for round_num in [1, 2]:
            for q_num in [1, 2]:
                self.gsm.start_question("test_game", "admin123")
                self.gsm.submit_answer("test_game", team.team_id, "answer")
                self.gsm.close_question("test_game", "admin123")
                
                if not (round_num == 2 and q_num == 2):  # Not the last question
                    self.gsm.next_question("test_game", "admin123")
        
        # Try to move past last question
        result = self.gsm.next_question("test_game", "admin123")
        assert result is None
        
        game = self.gsm.get_game("test_game")
        assert game.status == GameStatus.FINISHED
    
    def test_get_leaderboard(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        team1 = self.gsm.add_team("test_game", "Team Alpha")
        team2 = self.gsm.add_team("test_game", "Team Beta")
        
        # Give team1 higher score
        game = self.gsm.get_game("test_game")
        game.teams[team1.team_id].score = 3
        game.teams[team2.team_id].score = 1
        
        leaderboard = self.gsm.get_leaderboard("test_game")
        assert len(leaderboard) == 2
        assert leaderboard[0].name == "Team Alpha"  # Higher score first
        assert leaderboard[0].score == 3
        assert leaderboard[1].name == "Team Beta"
        assert leaderboard[1].score == 1
    
    def test_get_game_summary(self):
        self.gsm.create_game("test_game", self.csv_file, "admin123")
        self.gsm.add_team("test_game", "Team Alpha")
        
        summary = self.gsm.get_game_summary("test_game")
        assert summary["game_id"] == "test_game"
        assert summary["status"] == "waiting"
        assert summary["team_count"] == 1
        assert summary["current_round"] == 1
        assert summary["current_question"] == 1
        assert summary["total_rounds"] == 2
        assert summary["created_at"] is not None
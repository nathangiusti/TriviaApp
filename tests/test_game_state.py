import pytest
import os
from backend.game_state import GameStateManager, GameSession, Team, Answer, GameStatus
from backend.question_manager import QuestionManager
from .test_helpers import create_temp_csv, cleanup_temp_file


class TestTeam:
    def test_valid_team_creation(self):
        team = Team("Test Team")
        assert team.name == "Test Team"
        assert team.score == 0
        assert team.team_id is not None
        assert team.joined_at > 0
    
    def test_empty_team_name_raises_error(self):
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            Team("")
        
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            Team("   ")


class TestAnswer:
    def test_valid_answer_creation(self):
        answer = Answer("team123", 1, 1, "Test answer")
        assert answer.team_id == "team123"
        assert answer.question_round == 1
        assert answer.question_num == 1
        assert answer.answer_text == "Test answer"
        assert answer.submitted_at > 0
        assert answer.is_correct is None
        assert answer.points_awarded == 0


class TestGameSession:
    def test_valid_game_session_creation(self):
        session = GameSession("game1", "test.csv", "password123")
        assert session.game_id == "game1"
        assert session.csv_file_path == "test.csv"
        assert session.admin_password == "password123"
        assert session.status == GameStatus.WAITING
        assert session.current_round == 1
        assert session.current_question == 1
        assert len(session.teams) == 0
        assert len(session.answers) == 0
    
    def test_invalid_game_session_raises_errors(self):
        with pytest.raises(ValueError, match="Game ID cannot be empty"):
            GameSession("", "test.csv", "password")
        
        with pytest.raises(ValueError, match="CSV file path cannot be empty"):
            GameSession("game1", "", "password")
        
        with pytest.raises(ValueError, match="Admin password cannot be empty"):
            GameSession("game1", "test.csv", "")


class TestGameStateManager:
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
    
    
    def create_test_game(self) -> str:
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6
2,1,What is the capital of France?,Paris"""
        
        csv_file = create_temp_csv(csv_content)
        try:
            self.gsm.create_game("test_game", csv_file, "admin123")
            return csv_file
        except Exception:
            os.unlink(csv_file)
            raise
    
    def test_create_game_success(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            game = self.gsm.get_game("test_game")
            
            assert game is not None
            assert game.game_id == "test_game"
            assert game.admin_password == "admin123"
            assert game.status == GameStatus.WAITING
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_create_duplicate_game_raises_error(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            
            with pytest.raises(ValueError, match="Game test_game already exists"):
                self.gsm.create_game("test_game", csv_file, "admin456")
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_add_team_success(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            
            team = self.gsm.add_team("test_game", "Team Alpha")
            assert team.name == "Team Alpha"
            assert team.team_id is not None
            
            game = self.gsm.get_game("test_game")
            assert len(game.teams) == 1
            assert game.teams[team.team_id] == team
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_add_duplicate_team_name_raises_error(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            
            self.gsm.add_team("test_game", "Team Alpha")
            
            with pytest.raises(ValueError, match="Team name 'Team Alpha' already exists"):
                self.gsm.add_team("test_game", "Team Alpha")
            
            with pytest.raises(ValueError, match="Team name 'team alpha' already exists"):
                self.gsm.add_team("test_game", "team alpha")
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_add_team_to_nonexistent_game_raises_error(self):
        with pytest.raises(ValueError, match="Game nonexistent not found"):
            self.gsm.add_team("nonexistent", "Team Alpha")
    
    def test_add_team_after_game_started_raises_error(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            
            with pytest.raises(ValueError, match="Cannot add teams after game has started"):
                self.gsm.add_team("test_game", "Team Beta")
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_start_game_success(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            self.gsm.add_team("test_game", "Team Alpha")
            
            result = self.gsm.start_game("test_game", "admin123")
            assert result is True
            
            game = self.gsm.get_game("test_game")
            assert game.status == GameStatus.IN_PROGRESS
            assert game.started_at is not None
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_start_game_invalid_password_raises_error(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            self.gsm.add_team("test_game", "Team Alpha")
            
            with pytest.raises(ValueError, match="Invalid admin password"):
                self.gsm.start_game("test_game", "wrong_password")
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_start_game_no_teams_raises_error(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            
            with pytest.raises(ValueError, match="Cannot start game with no teams"):
                self.gsm.start_game("test_game", "admin123")
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_start_question_success(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            
            question = self.gsm.start_question("test_game", "admin123")
            assert question is not None
            assert question.question == "What is 2+2?"
            assert question.answer == "4"
            
            game = self.gsm.get_game("test_game")
            assert game.status == GameStatus.QUESTION_ACTIVE
            assert game.question_started_at is not None
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_submit_answer_success(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            team = self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            self.gsm.start_question("test_game", "admin123")
            
            answer = self.gsm.submit_answer("test_game", team.team_id, "4")
            assert answer.answer_text == "4"
            assert answer.team_id == team.team_id
            assert answer.question_round == 1
            assert answer.question_num == 1
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_submit_duplicate_answer_raises_error(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            team = self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            self.gsm.start_question("test_game", "admin123")
            
            self.gsm.submit_answer("test_game", team.team_id, "4")
            
            with pytest.raises(ValueError, match="Team has already submitted an answer"):
                self.gsm.submit_answer("test_game", team.team_id, "5")
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_close_question_success(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            team = self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            self.gsm.start_question("test_game", "admin123")
            self.gsm.submit_answer("test_game", team.team_id, "4")
            
            answers = self.gsm.close_question("test_game", "admin123")
            assert len(answers) == 1
            assert answers[0].answer_text == "4"
            
            game = self.gsm.get_game("test_game")
            assert game.status == GameStatus.QUESTION_CLOSED
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_grade_answer_correct(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            team = self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            self.gsm.start_question("test_game", "admin123")
            self.gsm.submit_answer("test_game", team.team_id, "4")
            
            graded_answer = self.gsm.grade_answer("test_game", team.team_id, 1, 1, True, 1)
            assert graded_answer.is_correct is True
            assert graded_answer.points_awarded == 1
            
            updated_team = self.gsm.get_game("test_game").teams[team.team_id]
            assert updated_team.score == 1
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_grade_answer_incorrect(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            team = self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            self.gsm.start_question("test_game", "admin123")
            self.gsm.submit_answer("test_game", team.team_id, "5")
            
            graded_answer = self.gsm.grade_answer("test_game", team.team_id, 1, 1, False)
            assert graded_answer.is_correct is False
            assert graded_answer.points_awarded == 0
            
            updated_team = self.gsm.get_game("test_game").teams[team.team_id]
            assert updated_team.score == 0
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_next_question_within_round(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            team = self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            self.gsm.start_question("test_game", "admin123")
            self.gsm.close_question("test_game", "admin123")
            
            next_q = self.gsm.next_question("test_game", "admin123")
            assert next_q is not None
            assert next_q.question == "What is 3+3?"
            
            game = self.gsm.get_game("test_game")
            assert game.current_round == 1
            assert game.current_question == 2
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_next_question_next_round(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            self.gsm.add_team("test_game", "Team Alpha")
            self.gsm.start_game("test_game", "admin123")
            
            # Complete round 1
            self.gsm.start_question("test_game", "admin123")
            self.gsm.close_question("test_game", "admin123")
            self.gsm.next_question("test_game", "admin123")  # Q1->Q2
            
            self.gsm.start_question("test_game", "admin123")
            self.gsm.close_question("test_game", "admin123")
            next_q = self.gsm.next_question("test_game", "admin123")  # Round 1->Round 2
            
            assert next_q is not None
            assert next_q.question == "What is the capital of France?"
            
            game = self.gsm.get_game("test_game")
            assert game.current_round == 2
            assert game.current_question == 1
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_game_finishes_when_no_more_questions(self):
        csv_file = None
        try:
            csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4"""
            csv_file = create_temp_csv(csv_content)
            self.gsm.create_game("finish_test", csv_file, "admin123")
            
            self.gsm.add_team("finish_test", "Team Alpha")
            self.gsm.start_game("finish_test", "admin123")
            self.gsm.start_question("finish_test", "admin123")
            self.gsm.close_question("finish_test", "admin123")
            
            next_q = self.gsm.next_question("finish_test", "admin123")
            assert next_q is None
            
            game = self.gsm.get_game("finish_test")
            assert game.status == GameStatus.FINISHED
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_get_leaderboard(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            team1 = self.gsm.add_team("test_game", "Team Alpha")
            team2 = self.gsm.add_team("test_game", "Team Beta")
            
            # Set scores manually for testing
            game = self.gsm.get_game("test_game")
            game.teams[team1.team_id].score = 5
            game.teams[team2.team_id].score = 3
            
            leaderboard = self.gsm.get_leaderboard("test_game")
            assert len(leaderboard) == 2
            assert leaderboard[0].name == "Team Alpha"
            assert leaderboard[0].score == 5
            assert leaderboard[1].name == "Team Beta"
            assert leaderboard[1].score == 3
        finally:
            if csv_file:
                os.unlink(csv_file)
    
    def test_get_game_summary(self):
        csv_file = None
        try:
            csv_file = self.create_test_game()
            self.gsm.add_team("test_game", "Team Alpha")
            
            summary = self.gsm.get_game_summary("test_game")
            assert summary["game_id"] == "test_game"
            assert summary["status"] == "waiting"
            assert summary["team_count"] == 1
            assert summary["current_round"] == 1
            assert summary["current_question"] == 1
            assert summary["total_rounds"] == 2
        finally:
            if csv_file:
                os.unlink(csv_file)
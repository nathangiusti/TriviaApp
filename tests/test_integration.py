import pytest
import os
from backend.question_manager import QuestionManager
from backend.game_state import GameStateManager, GameStatus
from .test_helpers import create_temp_csv, cleanup_temp_file


class TestIntegration:
    """Integration tests to ensure components work together correctly"""
    
    def setup_method(self):
        self.qm = QuestionManager()
        self.gsm = GameStateManager(self.qm)
    
    
    def test_full_game_workflow_integration(self):
        """Test a complete game from creation to finish"""
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6
2,1,What is the capital of France?,Paris
2,2,What is the capital of Spain?,Madrid"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            # 1. Create game (integrates QuestionManager + GameStateManager)
            game = self.gsm.create_game("integration_test", csv_file, "admin123")
            assert game.game_id == "integration_test"
            
            # Verify questions were loaded correctly
            questions = self.qm.get_questions_for_game("integration_test")
            assert len(questions) == 4
            
            # 2. Add teams
            team1 = self.gsm.add_team("integration_test", "Team Alpha")
            team2 = self.gsm.add_team("integration_test", "Team Beta")
            assert len(game.teams) == 2
            
            # 3. Start game
            self.gsm.start_game("integration_test", "admin123")
            assert game.status == GameStatus.IN_PROGRESS
            
            # 4. Play through all questions
            total_questions = 0
            current_round = 1
            
            while game.status != GameStatus.FINISHED:
                # Start question
                question = self.gsm.start_question("integration_test", "admin123")
                assert question is not None
                assert game.status == GameStatus.QUESTION_ACTIVE
                total_questions += 1
                
                # Teams submit answers
                if current_round == 1:  # Math questions
                    if game.current_question == 1:
                        self.gsm.submit_answer("integration_test", team1.team_id, "4")  # Correct
                        self.gsm.submit_answer("integration_test", team2.team_id, "5")  # Wrong
                    else:  # Question 2
                        self.gsm.submit_answer("integration_test", team1.team_id, "7")  # Wrong
                        self.gsm.submit_answer("integration_test", team2.team_id, "6")  # Correct
                else:  # Geography questions
                    if game.current_question == 1:
                        self.gsm.submit_answer("integration_test", team1.team_id, "Paris")  # Correct
                        self.gsm.submit_answer("integration_test", team2.team_id, "London")  # Wrong
                    else:  # Question 2
                        self.gsm.submit_answer("integration_test", team1.team_id, "Madrid")  # Correct
                        self.gsm.submit_answer("integration_test", team2.team_id, "Barcelona")  # Wrong
                
                # Close question and get answers
                answers = self.gsm.close_question("integration_test", "admin123")
                assert len(answers) == 2
                assert game.status == GameStatus.QUESTION_CLOSED
                
                # Grade answers
                correct_answer = question.answer
                for answer in answers:
                    is_correct = answer.answer_text.lower() == correct_answer.lower()
                    self.gsm.grade_answer("integration_test", answer.team_id, 
                                        answer.question_round, answer.question_num, 
                                        is_correct, 1)
                
                # Move to next question or finish
                next_question = self.gsm.next_question("integration_test", "admin123")
                if next_question is None:
                    assert game.status == GameStatus.FINISHED
                else:
                    if game.current_round > current_round:
                        current_round = game.current_round
            
            # 5. Verify final state
            assert total_questions == 4
            assert game.status == GameStatus.FINISHED
            
            # Team Alpha should have 3 points (Q1, Q2-R2, Q1-R2, Q2-R2)
            # Team Beta should have 1 point (Q2-R1)
            leaderboard = self.gsm.get_leaderboard("integration_test")
            assert len(leaderboard) == 2
            assert leaderboard[0].score == 3  # Team Alpha
            assert leaderboard[1].score == 1  # Team Beta
            
        finally:
            os.unlink(csv_file)
    
    def test_question_manager_game_state_data_consistency(self):
        """Test that data remains consistent between QuestionManager and GameStateManager"""
        csv_content = """round_num,question_num,question,answer
1,1,Test Question 1,Answer 1
1,2,Test Question 2,Answer 2
2,1,Test Question 3,Answer 3"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            # Create game
            self.gsm.create_game("consistency_test", csv_file, "admin123")
            
            # Verify QuestionManager has correct data
            qm_questions = self.qm.get_questions_for_game("consistency_test")
            qm_rounds = self.qm.get_rounds_for_game("consistency_test")
            
            # Verify GameStateManager can access the same data
            game = self.gsm.get_game("consistency_test")
            current_q = self.gsm.get_current_question("consistency_test")
            
            assert len(qm_questions) == 3
            assert qm_rounds == [1, 2]
            assert current_q.question == "Test Question 1"
            
            # Test navigation consistency
            self.gsm.add_team("consistency_test", "Test Team")
            self.gsm.start_game("consistency_test", "admin123")
            
            # Round 1, Question 1
            q1 = self.gsm.start_question("consistency_test", "admin123")
            assert q1.question == qm_questions[0].question
            assert q1.round_num == 1
            assert q1.question_num == 1
            
            self.gsm.close_question("consistency_test", "admin123")
            
            # Round 1, Question 2
            q2 = self.gsm.next_question("consistency_test", "admin123")
            assert q2.question == qm_questions[1].question
            assert q2.round_num == 1
            assert q2.question_num == 2
            
            self.gsm.start_question("consistency_test", "admin123")
            self.gsm.close_question("consistency_test", "admin123")
            
            # Round 2, Question 1
            q3 = self.gsm.next_question("consistency_test", "admin123")
            assert q3.question == qm_questions[2].question
            assert q3.round_num == 2
            assert q3.question_num == 1
            
        finally:
            os.unlink(csv_file)
    
    def test_multiple_games_isolation(self):
        """Test that multiple games don't interfere with each other"""
        csv_content1 = """round_num,question_num,question,answer
1,1,Game 1 Question,Game 1 Answer"""
        
        csv_content2 = """round_num,question_num,question,answer
1,1,Game 2 Question,Game 2 Answer"""
        
        csv_file1 = create_temp_csv(csv_content1)
        csv_file2 = create_temp_csv(csv_content2)
        
        try:
            # Create two different games
            game1 = self.gsm.create_game("game1", csv_file1, "admin1")
            game2 = self.gsm.create_game("game2", csv_file2, "admin2")
            
            # Add teams to each game
            team1_g1 = self.gsm.add_team("game1", "Team Alpha")
            team1_g2 = self.gsm.add_team("game2", "Team Alpha")  # Same name, different game
            team2_g1 = self.gsm.add_team("game1", "Team Beta")
            
            # Verify isolation
            assert len(game1.teams) == 2
            assert len(game2.teams) == 1
            assert team1_g1.team_id != team1_g2.team_id
            
            # Start games independently
            self.gsm.start_game("game1", "admin1")
            assert game1.status == GameStatus.IN_PROGRESS
            assert game2.status == GameStatus.WAITING
            
            self.gsm.start_game("game2", "admin2")
            assert game2.status == GameStatus.IN_PROGRESS
            
            # Verify questions are different
            q1 = self.gsm.start_question("game1", "admin1")
            q2 = self.gsm.start_question("game2", "admin2")
            
            assert q1.question == "Game 1 Question"
            assert q2.question == "Game 2 Question"
            assert q1.answer == "Game 1 Answer"
            assert q2.answer == "Game 2 Answer"
            
            # Verify game states are independent
            assert game1.status == GameStatus.QUESTION_ACTIVE
            assert game2.status == GameStatus.QUESTION_ACTIVE
            
            # Submit answers
            self.gsm.submit_answer("game1", team1_g1.team_id, "Test Answer 1")
            self.gsm.submit_answer("game2", team1_g2.team_id, "Test Answer 2")
            
            # Verify answers are in correct games
            assert len(game1.answers) == 1
            assert len(game2.answers) == 1
            assert game1.answers[0].answer_text == "Test Answer 1"
            assert game2.answers[0].answer_text == "Test Answer 2"
            
        finally:
            os.unlink(csv_file1)
            os.unlink(csv_file2)
    
    def test_error_handling_integration(self):
        """Test error handling across components"""
        csv_content = """round_num,question_num,question,answer
1,1,Test Question,Test Answer"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            self.gsm.create_game("error_test", csv_file, "admin123")
            team = self.gsm.add_team("error_test", "Test Team")
            
            # Test invalid game state transitions
            with pytest.raises(ValueError, match="Cannot start question in current game state"):
                self.gsm.start_question("error_test", "admin123")
            
            self.gsm.start_game("error_test", "admin123")
            
            with pytest.raises(ValueError, match="No active question to answer"):
                self.gsm.submit_answer("error_test", team.team_id, "Answer")
            
            with pytest.raises(ValueError, match="No active question to close"):
                self.gsm.close_question("error_test", "admin123")
            
            # Test proper workflow
            self.gsm.start_question("error_test", "admin123")
            self.gsm.submit_answer("error_test", team.team_id, "Answer")
            
            with pytest.raises(ValueError, match="Cannot advance to next question"):
                self.gsm.next_question("error_test", "admin123")
            
            self.gsm.close_question("error_test", "admin123")
            
            # Should return None when no more questions
            next_q = self.gsm.next_question("error_test", "admin123")
            assert next_q is None
            
            game = self.gsm.get_game("error_test")
            assert game.status == GameStatus.FINISHED
            
        finally:
            os.unlink(csv_file)
    
    def test_csv_format_edge_cases_integration(self):
        """Test integration with various CSV formats"""
        # Test with spaces in values
        csv_content = """round_num,question_num,question,answer
1,1,"What is 2 + 2?","4"
1,2,"What is the capital of United States?","Washington D.C."
2,1,"Name a programming language","Python"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            self.gsm.create_game("format_test", csv_file, "admin123")
            
            # Verify questions loaded correctly despite formatting
            questions = self.qm.get_questions_for_game("format_test")
            assert len(questions) == 3
            assert questions[0].question == "What is 2 + 2?"
            assert questions[0].answer == "4"
            assert questions[1].answer == "Washington D.C."
            
            # Test game flow works with formatted data
            team = self.gsm.add_team("format_test", "Test Team")
            self.gsm.start_game("format_test", "admin123")
            
            question = self.gsm.start_question("format_test", "admin123")
            assert question.question == "What is 2 + 2?"
            
            self.gsm.submit_answer("format_test", team.team_id, "4")
            answers = self.gsm.close_question("format_test", "admin123")
            
            # Grade and verify
            self.gsm.grade_answer("format_test", team.team_id, 1, 1, True, 1)
            assert team.score == 1
            
        finally:
            os.unlink(csv_file)
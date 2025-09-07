import pytest
import os
from backend.question_manager import QuestionManager, Question
from .test_helpers import create_temp_csv, cleanup_temp_file


class TestQuestion:
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
    def setup_method(self):
        self.qm = QuestionManager()
    
    
    def test_load_valid_csv(self):
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is the capital of France?,Paris
2,1,What color is the sky?,Blue"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            result = self.qm.load_questions_from_csv("game1", csv_file)
            assert result is True
            assert self.qm.is_game_loaded("game1")
            
            questions = self.qm.get_questions_for_game("game1")
            assert len(questions) == 3
            
            assert questions[0].round_num == 1
            assert questions[0].question_num == 1
            assert questions[0].question == "What is 2+2?"
            assert questions[0].answer == "4"
            assert questions[1].round_num == 1
            assert questions[1].question_num == 2
            assert questions[1].question == "What is the capital of France?"
            assert questions[1].answer == "Paris"
        finally:
            os.unlink(csv_file)
    
    def test_load_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.qm.load_questions_from_csv("game1", "nonexistent.csv")
    
    def test_load_csv_missing_columns(self):
        csv_content = """round,question,answer
1,What is 2+2?,4"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="CSV must contain columns"):
                self.qm.load_questions_from_csv("game1", csv_file)
        finally:
            os.unlink(csv_file)
    
    def test_load_csv_empty_questions(self):
        csv_content = """round_num,question_num,question,answer
1,1,,4
1,2,What is the capital of France?,Paris"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="Invalid question at row 2"):
                self.qm.load_questions_from_csv("game1", csv_file)
        finally:
            os.unlink(csv_file)
    
    def test_load_csv_empty_answers(self):
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,
1,2,What is the capital of France?,Paris"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="Invalid question at row 2"):
                self.qm.load_questions_from_csv("game1", csv_file)
        finally:
            os.unlink(csv_file)
    
    def test_load_empty_csv(self):
        csv_content = """round_num,question_num,question,answer"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            with pytest.raises(ValueError, match="CSV file contains no valid questions"):
                self.qm.load_questions_from_csv("game1", csv_file)
        finally:
            os.unlink(csv_file)
    
    def test_get_questions_for_nonexistent_game(self):
        with pytest.raises(ValueError, match="No questions loaded for game"):
            self.qm.get_questions_for_game("nonexistent")
    
    def test_get_question_by_round_and_num(self):
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is the capital of France?,Paris
2,1,What color is the sky?,Blue"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            self.qm.load_questions_from_csv("game1", csv_file)
            
            question = self.qm.get_question_by_round_and_num("game1", 1, 1)
            assert question is not None
            assert question.question == "What is 2+2?"
            
            question = self.qm.get_question_by_round_and_num("game1", 1, 2)
            assert question is not None
            assert question.question == "What is the capital of France?"
            
            question = self.qm.get_question_by_round_and_num("game1", 2, 1)
            assert question is not None
            assert question.question == "What color is the sky?"
            
            question = self.qm.get_question_by_round_and_num("game1", 99, 1)
            assert question is None
        finally:
            os.unlink(csv_file)
    
    def test_get_total_questions(self):
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is the capital of France?,Paris
2,1,What color is the sky?,Blue"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            self.qm.load_questions_from_csv("game1", csv_file)
            assert self.qm.get_total_questions("game1") == 3
        finally:
            os.unlink(csv_file)
    
    def test_get_questions_for_round(self):
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6
2,1,What is the capital of France?,Paris
2,2,What is the capital of Spain?,Madrid"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            self.qm.load_questions_from_csv("game1", csv_file)
            
            round1_questions = self.qm.get_questions_for_round("game1", 1)
            assert len(round1_questions) == 2
            assert round1_questions[0].question == "What is 2+2?"
            assert round1_questions[1].question == "What is 3+3?"
            
            round2_questions = self.qm.get_questions_for_round("game1", 2)
            assert len(round2_questions) == 2
            assert round2_questions[0].question == "What is the capital of France?"
            assert round2_questions[1].question == "What is the capital of Spain?"
            
            round3_questions = self.qm.get_questions_for_round("game1", 3)
            assert len(round3_questions) == 0
        finally:
            os.unlink(csv_file)
    
    def test_get_rounds_for_game(self):
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
3,1,What is 3+3?,6
2,1,What is the capital of France?,Paris
2,2,What is the capital of Spain?,Madrid"""
        
        csv_file = create_temp_csv(csv_content)
        
        try:
            self.qm.load_questions_from_csv("game1", csv_file)
            rounds = self.qm.get_rounds_for_game("game1")
            assert rounds == [1, 2, 3]
        finally:
            os.unlink(csv_file)
    
    def test_multiple_games(self):
        csv_content1 = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is 3+3?,6"""
        
        csv_content2 = """round_num,question_num,question,answer
1,1,What is the capital of France?,Paris
1,2,What is the capital of Spain?,Madrid
2,1,What is the capital of Italy?,Rome"""
        
        csv_file1 = create_temp_csv(csv_content1)
        csv_file2 = create_temp_csv(csv_content2)
        
        try:
            self.qm.load_questions_from_csv("math", csv_file1)
            self.qm.load_questions_from_csv("geography", csv_file2)
            
            assert self.qm.is_game_loaded("math")
            assert self.qm.is_game_loaded("geography")
            assert not self.qm.is_game_loaded("science")
            
            assert self.qm.get_total_questions("math") == 2
            assert self.qm.get_total_questions("geography") == 3
            
            math_questions = self.qm.get_questions_for_game("math")
            geo_questions = self.qm.get_questions_for_game("geography")
            
            assert len(math_questions) == 2
            assert len(geo_questions) == 3
            assert math_questions[0].question == "What is 2+2?"
            assert geo_questions[0].question == "What is the capital of France?"
            
            math_rounds = self.qm.get_rounds_for_game("math")
            geo_rounds = self.qm.get_rounds_for_game("geography")
            assert math_rounds == [1]
            assert geo_rounds == [1, 2]
        finally:
            os.unlink(csv_file1)
            os.unlink(csv_file2)
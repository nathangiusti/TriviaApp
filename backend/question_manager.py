import csv
import os
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Question:
    round_num: int
    question_num: int
    question: str
    answer: str
    
    def __post_init__(self):
        if not self.question.strip():
            raise ValueError("Question cannot be empty")
        if not self.answer.strip():
            raise ValueError("Answer cannot be empty")
        if self.round_num <= 0:
            raise ValueError("Round number must be positive")
        if self.question_num <= 0:
            raise ValueError("Question number must be positive")


class QuestionManager:
    def __init__(self):
        self.games: Dict[str, List[Question]] = {}
    
    def load_questions_from_csv(self, game_id: str, csv_file_path: str) -> bool:
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        questions = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                expected_columns = {'round_num', 'question_num', 'question', 'answer'}
                actual_columns = {col.strip() for col in csv_reader.fieldnames}
                if not expected_columns.issubset(actual_columns):
                    raise ValueError(f"CSV must contain columns: {expected_columns}")
                
                for idx, row in enumerate(csv_reader):
                    try:
                        cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                        question = Question(
                            round_num=int(cleaned_row['round_num']),
                            question_num=int(cleaned_row['question_num']),
                            question=cleaned_row['question'],
                            answer=cleaned_row['answer']
                        )
                        questions.append(question)
                    except (ValueError, KeyError) as e:
                        raise ValueError(f"Invalid question at row {idx + 2}: {str(e)}")
            
            if not questions:
                raise ValueError("CSV file contains no valid questions")
            
            self.games[game_id] = questions
            return True
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to load CSV: {str(e)}")
    
    def get_questions_for_game(self, game_id: str) -> List[Question]:
        if game_id not in self.games:
            raise ValueError(f"No questions loaded for game: {game_id}")
        return self.games[game_id].copy()
    
    def get_question_by_round_and_num(self, game_id: str, round_num: int, question_num: int) -> Optional[Question]:
        questions = self.get_questions_for_game(game_id)
        for question in questions:
            if question.round_num == round_num and question.question_num == question_num:
                return question
        return None
    
    def get_questions_for_round(self, game_id: str, round_num: int) -> List[Question]:
        questions = self.get_questions_for_game(game_id)
        return [q for q in questions if q.round_num == round_num]
    
    def get_rounds_for_game(self, game_id: str) -> List[int]:
        questions = self.get_questions_for_game(game_id)
        rounds = list(set(q.round_num for q in questions))
        return sorted(rounds)
    
    def get_total_questions(self, game_id: str) -> int:
        return len(self.get_questions_for_game(game_id))
    
    def is_game_loaded(self, game_id: str) -> bool:
        return game_id in self.games
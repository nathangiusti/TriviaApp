from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import time
import uuid
from .question_manager import QuestionManager, Question


class GameStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    QUESTION_ACTIVE = "question_active"
    QUESTION_CLOSED = "question_closed"
    FINISHED = "finished"


@dataclass
class Team:
    name: str
    team_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    score: int = 0
    joined_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Team name cannot be empty")


@dataclass
class Answer:
    team_id: str
    question_round: int
    question_num: int
    answer_text: str
    submitted_at: float = field(default_factory=time.time)
    is_correct: Optional[bool] = None
    points_awarded: int = 0


@dataclass
class GameSession:
    game_id: str
    csv_file_path: str
    admin_password: str
    status: GameStatus = GameStatus.WAITING
    teams: Dict[str, Team] = field(default_factory=dict)
    current_round: int = 1
    current_question: int = 1
    answers: List[Answer] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    question_started_at: Optional[float] = None
    
    def __post_init__(self):
        if not self.game_id.strip():
            raise ValueError("Game ID cannot be empty")
        if not self.csv_file_path.strip():
            raise ValueError("CSV file path cannot be empty")
        if not self.admin_password.strip():
            raise ValueError("Admin password cannot be empty")


class GameStateManager:
    def __init__(self, question_manager: QuestionManager):
        self.question_manager = question_manager
        self.games: Dict[str, GameSession] = {}
    
    def create_game(self, game_id: str, csv_file_path: str, admin_password: str) -> GameSession:
        if game_id in self.games:
            raise ValueError(f"Game {game_id} already exists")
        
        self.question_manager.load_questions_from_csv(game_id, csv_file_path)
        
        game = GameSession(
            game_id=game_id,
            csv_file_path=csv_file_path,
            admin_password=admin_password
        )
        
        self.games[game_id] = game
        return game
    
    def get_game(self, game_id: str) -> Optional[GameSession]:
        return self.games.get(game_id)
    
    def add_team(self, game_id: str, team_name: str) -> Team:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.status != GameStatus.WAITING:
            raise ValueError("Cannot add teams after game has started")
        
        team_name = team_name.strip()
        if any(team.name.lower() == team_name.lower() for team in game.teams.values()):
            raise ValueError(f"Team name '{team_name}' already exists")
        
        team = Team(name=team_name)
        game.teams[team.team_id] = team
        return team
    
    def start_game(self, game_id: str, admin_password: str) -> bool:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.admin_password != admin_password:
            raise ValueError("Invalid admin password")
        
        if game.status != GameStatus.WAITING:
            raise ValueError("Game has already started")
        
        if not game.teams:
            raise ValueError("Cannot start game with no teams")
        
        game.status = GameStatus.IN_PROGRESS
        game.started_at = time.time()
        return True
    
    def start_question(self, game_id: str, admin_password: str) -> Question:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.admin_password != admin_password:
            raise ValueError("Invalid admin password")
        
        if game.status not in [GameStatus.IN_PROGRESS, GameStatus.QUESTION_CLOSED]:
            raise ValueError("Cannot start question in current game state")
        
        question = self.question_manager.get_question_by_round_and_num(
            game_id, game.current_round, game.current_question
        )
        
        if not question:
            raise ValueError(f"No question found for round {game.current_round}, question {game.current_question}")
        
        game.status = GameStatus.QUESTION_ACTIVE
        game.question_started_at = time.time()
        return question
    
    def submit_answer(self, game_id: str, team_id: str, answer_text: str) -> Answer:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.status != GameStatus.QUESTION_ACTIVE:
            raise ValueError("No active question to answer")
        
        if team_id not in game.teams:
            raise ValueError("Team not found in this game")
        
        existing_answer = self._get_team_answer(game, team_id, game.current_round, game.current_question)
        if existing_answer:
            raise ValueError("Team has already submitted an answer for this question")
        
        answer = Answer(
            team_id=team_id,
            question_round=game.current_round,
            question_num=game.current_question,
            answer_text=answer_text.strip()
        )
        
        game.answers.append(answer)
        return answer
    
    def close_question(self, game_id: str, admin_password: str) -> List[Answer]:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.admin_password != admin_password:
            raise ValueError("Invalid admin password")
        
        if game.status != GameStatus.QUESTION_ACTIVE:
            raise ValueError("No active question to close")
        
        game.status = GameStatus.QUESTION_CLOSED
        
        current_answers = [
            ans for ans in game.answers 
            if ans.question_round == game.current_round and ans.question_num == game.current_question
        ]
        
        return current_answers
    
    def grade_answer(self, game_id: str, team_id: str, round_num: int, question_num: int, 
                    is_correct: bool, points: int = 1) -> Answer:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        answer = self._get_team_answer(game, team_id, round_num, question_num)
        if not answer:
            raise ValueError("Answer not found")
        
        answer.is_correct = is_correct
        answer.points_awarded = points if is_correct else 0
        
        if is_correct:
            game.teams[team_id].score += points
        
        return answer
    
    def next_question(self, game_id: str, admin_password: str) -> Optional[Question]:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.admin_password != admin_password:
            raise ValueError("Invalid admin password")
        
        if game.status != GameStatus.QUESTION_CLOSED:
            raise ValueError("Cannot advance to next question in current state")
        
        questions_in_round = self.question_manager.get_questions_for_round(game_id, game.current_round)
        
        if game.current_question < len(questions_in_round):
            game.current_question += 1
        else:
            available_rounds = self.question_manager.get_rounds_for_game(game_id)
            if game.current_round < max(available_rounds):
                game.current_round += 1
                game.current_question = 1
            else:
                game.status = GameStatus.FINISHED
                return None
        
        game.status = GameStatus.IN_PROGRESS
        return self.question_manager.get_question_by_round_and_num(
            game_id, game.current_round, game.current_question
        )
    
    def get_leaderboard(self, game_id: str) -> List[Team]:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        return sorted(game.teams.values(), key=lambda team: team.score, reverse=True)
    
    def get_current_question(self, game_id: str) -> Optional[Question]:
        game = self.get_game(game_id)
        if not game:
            return None
        
        return self.question_manager.get_question_by_round_and_num(
            game_id, game.current_round, game.current_question
        )
    
    def get_game_summary(self, game_id: str) -> Dict:
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        return {
            "game_id": game.game_id,
            "status": game.status.value,
            "team_count": len(game.teams),
            "current_round": game.current_round,
            "current_question": game.current_question,
            "total_rounds": len(self.question_manager.get_rounds_for_game(game_id)),
            "created_at": game.created_at,
            "started_at": game.started_at
        }
    
    def _get_team_answer(self, game: GameSession, team_id: str, round_num: int, question_num: int) -> Optional[Answer]:
        for answer in game.answers:
            if (answer.team_id == team_id and 
                answer.question_round == round_num and 
                answer.question_num == question_num):
                return answer
        return None
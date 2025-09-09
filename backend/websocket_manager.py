from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import json
import time
from enum import Enum
from .game_state import GameStateManager, GameStatus
from .question_manager import QuestionManager


class EventType(Enum):
    # Client to server events
    JOIN_GAME = "join_game"
    ADMIN_LOGIN = "admin_login"
    START_GAME = "start_game"
    START_QUESTION = "start_question"
    SUBMIT_ANSWER = "submit_answer"
    CLOSE_QUESTION = "close_question"
    GRADE_ANSWER = "grade_answer"
    NEXT_QUESTION = "next_question"
    GET_LEADERBOARD = "get_leaderboard"
    GET_GAME_STATE = "get_game_state"
    
    # Server to client events
    TEAM_JOINED = "team_joined"
    TEAM_LIST_UPDATE = "team_list_update"
    GAME_STARTED = "game_started"
    QUESTION_STARTED = "question_started"
    ANSWER_SUBMITTED = "answer_submitted"
    QUESTION_CLOSED = "question_closed"
    ANSWER_GRADED = "answer_graded"
    LEADERBOARD_UPDATE = "leaderboard_update"
    GAME_FINISHED = "game_finished"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class WebSocketMessage:
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        return json.dumps({
            "event": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        data = json.loads(json_str)
        return cls(
            event_type=EventType(data["event"]),
            data=data["data"],
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class ClientConnection:
    client_id: str
    game_id: Optional[str] = None
    team_id: Optional[str] = None
    is_admin: bool = False
    connected_at: float = None
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = time.time()


class WebSocketManager:
    def __init__(self, game_state_manager: GameStateManager):
        self.gsm = game_state_manager
        self.connections: Dict[str, ClientConnection] = {}
        self.game_connections: Dict[str, Set[str]] = {}  # game_id -> set of client_ids
        
    def connect_client(self, client_id: str) -> ClientConnection:
        """Register a new client connection"""
        if client_id in self.connections:
            raise ValueError(f"Client {client_id} already connected")
        
        connection = ClientConnection(client_id=client_id)
        self.connections[client_id] = connection
        return connection
    
    def disconnect_client(self, client_id: str) -> None:
        """Remove client connection and clean up"""
        if client_id not in self.connections:
            return
        
        connection = self.connections[client_id]
        if connection.game_id:
            self.game_connections[connection.game_id].discard(client_id)
            if not self.game_connections[connection.game_id]:
                del self.game_connections[connection.game_id]
        
        del self.connections[client_id]
    
    def handle_message(self, client_id: str, message: WebSocketMessage) -> List[WebSocketMessage]:
        """Process incoming message and return list of messages to send"""
        if client_id not in self.connections:
            return [WebSocketMessage(EventType.ERROR, {"message": "Client not connected"})]
        
        try:
            handler_name = f"_handle_{message.event_type.value}"
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                return handler(client_id, message.data)
            else:
                return [WebSocketMessage(EventType.ERROR, {"message": f"Unknown event type: {message.event_type.value}"})]
        
        except Exception as e:
            return [WebSocketMessage(EventType.ERROR, {"message": str(e)})]
    
    def _handle_join_game(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle team joining a game"""
        game_id = data.get("game_id")
        team_name = data.get("team_name")
        
        if not game_id or not team_name:
            return [WebSocketMessage(EventType.ERROR, {"message": "Missing game_id or team_name"})]
        
        # Check if game exists
        game = self.gsm.get_game(game_id)
        if not game:
            return [WebSocketMessage(EventType.ERROR, {"message": "Game not found"})]
        
        # Add team to game
        team = self.gsm.add_team(game_id, team_name)
        
        # Update connection
        connection = self.connections[client_id]
        connection.game_id = game_id
        connection.team_id = team.team_id
        
        # Add to game connections
        if game_id not in self.game_connections:
            self.game_connections[game_id] = set()
        self.game_connections[game_id].add(client_id)
        
        # Prepare messages
        messages = []
        
        # Success message to joining team
        messages.append(WebSocketMessage(EventType.TEAM_JOINED, {
            "team_id": team.team_id,
            "team_name": team.name,
            "game_id": game_id
        }))
        
        # Broadcast team list update to all clients in game
        team_list = [{"team_id": t.team_id, "name": t.name, "score": t.score} 
                    for t in game.teams.values()]
        
        for other_client_id in self.game_connections[game_id]:
            messages.append(WebSocketMessage(EventType.TEAM_LIST_UPDATE, {
                "teams": team_list,
                "target_client": other_client_id
            }))
        
        return messages
    
    def _handle_admin_login(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle admin login"""
        game_id = data.get("game_id")
        password = data.get("password")
        
        if not game_id or not password:
            return [WebSocketMessage(EventType.ERROR, {"message": "Missing game_id or password"})]
        
        game = self.gsm.get_game(game_id)
        if not game:
            return [WebSocketMessage(EventType.ERROR, {"message": "Game not found"})]
        
        if game.admin_password != password:
            return [WebSocketMessage(EventType.ERROR, {"message": "Invalid admin password"})]
        
        # Update connection
        connection = self.connections[client_id]
        connection.game_id = game_id
        connection.is_admin = True
        
        # Add to game connections
        if game_id not in self.game_connections:
            self.game_connections[game_id] = set()
        self.game_connections[game_id].add(client_id)
        
        # Prepare response messages
        messages = []
        
        # Success message
        messages.append(WebSocketMessage(EventType.SUCCESS, {
            "message": "Admin logged in successfully",
            "game_id": game_id,
            "is_admin": True
        }))
        
        # Send current team list to admin
        team_list = [{"team_id": t.team_id, "name": t.name, "score": t.score} 
                    for t in game.teams.values()]
        messages.append(WebSocketMessage(EventType.TEAM_LIST_UPDATE, {
            "teams": team_list
        }))
        
        return messages
    
    def _handle_start_game(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle game start by admin"""
        connection = self.connections[client_id]
        if not connection.is_admin:
            return [WebSocketMessage(EventType.ERROR, {"message": "Admin access required"})]
        
        game_id = connection.game_id
        password = data.get("password")
        
        self.gsm.start_game(game_id, password)
        
        # Broadcast to all clients in game
        messages = []
        game = self.gsm.get_game(game_id)
        
        for client_id in self.game_connections[game_id]:
            messages.append(WebSocketMessage(EventType.GAME_STARTED, {
                "game_id": game_id,
                "status": game.status.value,
                "target_client": client_id
            }))
        
        return messages
    
    def _handle_start_question(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle question start by admin"""
        connection = self.connections[client_id]
        if not connection.is_admin:
            return [WebSocketMessage(EventType.ERROR, {"message": "Admin access required"})]
        
        game_id = connection.game_id
        password = data.get("password")
        
        question = self.gsm.start_question(game_id, password)
        
        # Broadcast to all clients in game
        messages = []
        
        for target_client_id in self.game_connections[game_id]:
            target_connection = self.connections[target_client_id]
            
            # Send different data to admin vs teams
            if target_connection.is_admin:
                question_data = {
                    "round": question.round_num,
                    "question_num": question.question_num,
                    "question": question.question,
                    "answer": question.answer,  # Admin sees answer
                    "target_client": target_client_id
                }
            else:
                question_data = {
                    "round": question.round_num,
                    "question_num": question.question_num,
                    "question": question.question,
                    "target_client": target_client_id
                }
            
            messages.append(WebSocketMessage(EventType.QUESTION_STARTED, question_data))
        
        return messages
    
    def _handle_submit_answer(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle answer submission by team"""
        connection = self.connections[client_id]
        if not connection.team_id:
            return [WebSocketMessage(EventType.ERROR, {"message": "Must be part of a team to submit answers"})]
        
        game_id = connection.game_id
        answer_text = data.get("answer")
        
        if not answer_text:
            return [WebSocketMessage(EventType.ERROR, {"message": "Answer cannot be empty"})]
        
        answer = self.gsm.submit_answer(game_id, connection.team_id, answer_text)
        
        # Send confirmation to submitting team
        messages = [WebSocketMessage(EventType.ANSWER_SUBMITTED, {
            "answer": answer_text,
            "submitted_at": answer.submitted_at
        })]
        
        # Notify admin of answer submission with automatic correctness detection
        game = self.gsm.get_game(game_id)
        for target_client_id in self.game_connections[game_id]:
            target_connection = self.connections[target_client_id]
            if target_connection.is_admin:
                team = game.teams[connection.team_id]
                
                # Get correct answer for automatic detection
                correct_answer = ""
                is_auto_correct = False
                try:
                    question = self.gsm.question_manager.get_question_by_round_and_num(
                        game_id, game.current_round, game.current_question
                    )
                    if question:
                        correct_answer = question.answer
                        # Case-insensitive comparison with whitespace trimming
                        is_auto_correct = answer_text.strip().lower() == correct_answer.strip().lower()
                except Exception:
                    # If we can't get the correct answer, default to False
                    pass
                
                messages.append(WebSocketMessage(EventType.ANSWER_SUBMITTED, {
                    "team_name": team.name,
                    "team_id": connection.team_id,
                    "answer": answer_text,
                    "submitted_at": answer.submitted_at,
                    "target_client": target_client_id,
                    "is_auto_correct": is_auto_correct,
                    "correct_answer": correct_answer
                }))
        
        return messages
    
    def _handle_close_question(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle question closing by admin"""
        connection = self.connections[client_id]
        if not connection.is_admin:
            return [WebSocketMessage(EventType.ERROR, {"message": "Admin access required"})]
        
        game_id = connection.game_id
        password = data.get("password")
        
        answers = self.gsm.close_question(game_id, password)
        
        # Get current question and updated game state
        game = self.gsm.get_game(game_id)
        current_question = self.gsm.get_current_question(game_id)
        
        # Create leaderboard with updated scores
        leaderboard = [
            {"name": team.name, "score": team.score}
            for team in game.teams.values()
        ]
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Broadcast to all clients
        messages = []
        
        for target_client_id in self.game_connections[game_id]:
            target_connection = self.connections[target_client_id]
            
            if target_connection.is_admin:
                # Admin gets all answers for grading (existing behavior)
                answer_data = []
                for answer in answers:
                    team = game.teams[answer.team_id]
                    answer_data.append({
                        "team_id": answer.team_id,
                        "team_name": team.name,
                        "answer": answer.answer_text,
                        "submitted_at": answer.submitted_at,
                        "is_correct": answer.is_correct,
                        "points_awarded": answer.points_awarded
                    })
                
                messages.append(WebSocketMessage(EventType.QUESTION_CLOSED, {
                    "answers": answer_data,
                    "target_client": target_client_id
                }))
            else:
                # Teams get question results and updated scores
                team_answer = None
                team_correct = None
                
                # Find this team's answer
                for answer in answers:
                    if answer.team_id == target_connection.team_id:
                        team_answer = answer.answer_text
                        team_correct = answer.is_correct
                        break
                
                messages.append(WebSocketMessage(EventType.QUESTION_CLOSED, {
                    "correct_answer": current_question.answer if current_question else "N/A",
                    "team_answer": team_answer,
                    "team_correct": team_correct,
                    "leaderboard": leaderboard,
                    "message": "Question results",
                    "target_client": target_client_id
                }))
        
        # Send leaderboard update to all clients
        for target_client_id in self.game_connections[game_id]:
            messages.append(WebSocketMessage(EventType.LEADERBOARD_UPDATE, {
                "leaderboard": leaderboard,
                "target_client": target_client_id
            }))
        
        return messages
    
    def _handle_grade_answer(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle answer grading by admin"""
        connection = self.connections[client_id]
        if not connection.is_admin:
            return [WebSocketMessage(EventType.ERROR, {"message": "Admin access required"})]
        
        game_id = connection.game_id
        team_id = data.get("team_id")
        round_num = data.get("round_num")
        question_num = data.get("question_num")
        is_correct = data.get("is_correct")
        points = data.get("points", 1)
        
        answer = self.gsm.grade_answer(game_id, team_id, round_num, question_num, is_correct, points)
        
        # Broadcast results to all clients
        messages = []
        game = self.gsm.get_game(game_id)
        team = game.teams[team_id]
        
        for target_client_id in self.game_connections[game_id]:
            messages.append(WebSocketMessage(EventType.ANSWER_GRADED, {
                "team_id": team_id,
                "team_name": team.name,
                "is_correct": is_correct,
                "points_awarded": answer.points_awarded,
                "new_score": team.score,
                "target_client": target_client_id
            }))
        
        return messages
    
    def _handle_next_question(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle moving to next question by admin"""
        connection = self.connections[client_id]
        if not connection.is_admin:
            return [WebSocketMessage(EventType.ERROR, {"message": "Admin access required"})]
        
        game_id = connection.game_id
        password = data.get("password")
        
        next_question = self.gsm.next_question(game_id, password)
        
        # Check if game finished
        game = self.gsm.get_game(game_id)
        if game.status == GameStatus.FINISHED:
            # Broadcast game finished
            messages = []
            leaderboard = self.gsm.get_leaderboard(game_id)
            leaderboard_data = [{"name": t.name, "score": t.score} for t in leaderboard]
            
            for target_client_id in self.game_connections[game_id]:
                messages.append(WebSocketMessage(EventType.GAME_FINISHED, {
                    "final_leaderboard": leaderboard_data,
                    "target_client": target_client_id
                }))
            
            return messages
        
        # Return success for progression
        return [WebSocketMessage(EventType.SUCCESS, {
            "message": "Moved to next question",
            "current_round": game.current_round,
            "current_question": game.current_question
        })]
    
    def _handle_get_leaderboard(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle leaderboard request"""
        connection = self.connections[client_id]
        game_id = connection.game_id
        
        if not game_id:
            return [WebSocketMessage(EventType.ERROR, {"message": "Not in a game"})]
        
        leaderboard = self.gsm.get_leaderboard(game_id)
        leaderboard_data = [{"name": t.name, "score": t.score} for t in leaderboard]
        
        return [WebSocketMessage(EventType.LEADERBOARD_UPDATE, {
            "leaderboard": leaderboard_data
        })]
    
    def _handle_get_game_state(self, client_id: str, data: Dict[str, Any]) -> List[WebSocketMessage]:
        """Handle game state request"""
        connection = self.connections[client_id]
        game_id = connection.game_id
        
        if not game_id:
            return [WebSocketMessage(EventType.ERROR, {"message": "Not in a game"})]
        
        summary = self.gsm.get_game_summary(game_id)
        return [WebSocketMessage(EventType.SUCCESS, {
            "game_state": summary
        })]
    
    def get_client_connection(self, client_id: str) -> Optional[ClientConnection]:
        """Get connection info for a client"""
        return self.connections.get(client_id)
    
    def get_game_clients(self, game_id: str) -> Set[str]:
        """Get all client IDs connected to a game"""
        return self.game_connections.get(game_id, set()).copy()
    
    def broadcast_to_game(self, game_id: str, message: WebSocketMessage) -> List[WebSocketMessage]:
        """Broadcast a message to all clients in a game"""
        if game_id not in self.game_connections:
            return []
        
        messages = []
        for client_id in self.game_connections[game_id]:
            message_copy = WebSocketMessage(message.event_type, {
                **message.data,
                "target_client": client_id
            })
            messages.append(message_copy)
        
        return messages
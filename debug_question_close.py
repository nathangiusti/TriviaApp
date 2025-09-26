#!/usr/bin/env python3
"""
Debug script to test question closing and see what data is sent to teams
"""

from backend.question_manager import QuestionManager
from backend.game_state import GameStateManager
from backend.websocket_manager import WebSocketManager, WebSocketMessage, EventType

def debug_question_close():
    # Initialize managers
    question_manager = QuestionManager()
    gsm = GameStateManager(question_manager)
    wsm = WebSocketManager(gsm)
    
    # Create test game
    gsm.create_game("demo_game", "sample_questions.csv", "admin123")
    
    # Connect clients
    wsm.connect_client("admin1")
    wsm.connect_client("player1")
    
    # Admin login
    admin_login = WebSocketMessage(EventType.ADMIN_LOGIN, {
        "game_id": "demo_game",
        "password": "admin123"
    })
    responses = wsm.handle_message("admin1", admin_login)
    print("Admin login responses:", len(responses))
    
    # Team joins
    join_message = WebSocketMessage(EventType.JOIN_GAME, {
        "game_id": "demo_game",
        "team_name": "Test Team"
    })
    responses = wsm.handle_message("player1", join_message)
    print("Join game responses:", len(responses))
    
    # Start game
    start_game = WebSocketMessage(EventType.START_GAME, {"password": "admin123"})
    responses = wsm.handle_message("admin1", start_game)
    print("Start game responses:", len(responses))
    
    # Start question
    start_question = WebSocketMessage(EventType.START_QUESTION, {"password": "admin123"})
    responses = wsm.handle_message("admin1", start_question)
    print("Start question responses:", len(responses))
    
    # Submit answer
    submit_answer = WebSocketMessage(EventType.SUBMIT_ANSWER, {"answer": "Nathan"})
    responses = wsm.handle_message("player1", submit_answer)
    print("Submit answer responses:", len(responses))
    
    # Close question
    close_question = WebSocketMessage(EventType.CLOSE_QUESTION, {"password": "admin123"})
    responses = wsm.handle_message("admin1", close_question)
    
    print(f"\nClose question responses: {len(responses)}")
    for i, response in enumerate(responses):
        print(f"Response {i+1}: {response.event_type.value}")
        print(f"Data: {response.data}")
        if response.event_type == EventType.QUESTION_CLOSED:
            print(f"  Target client: {response.data.get('target_client', 'ALL')}")
            if 'team_answer' in response.data:
                print(f"  Team answer: {response.data['team_answer']}")
                print(f"  Team correct: {response.data['team_correct']}")
                print(f"  Correct answer: {response.data['correct_answer']}")
        print()

if __name__ == "__main__":
    debug_question_close()
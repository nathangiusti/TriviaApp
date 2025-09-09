#!/usr/bin/env python3
"""
Trivia App Launcher
Creates a sample game and starts the server for immediate testing
"""

import os
import requests
import time
import webbrowser
import threading
from backend.app import app, socketio, game_state_manager

def create_sample_game():
    """Create a sample game for testing"""
    # Wait for server to start
    print(">> Waiting for server to start...")
    time.sleep(3)
    
    # Try multiple times to ensure server is ready
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            print(f">> Attempting to create demo game (attempt {attempt + 1}/{max_attempts})")
            response = requests.post('http://localhost:3001/api/create-game', json={
                'game_id': 'demo_game',
                'csv_file_path': 'sample_questions.csv',
                'admin_password': 'admin123'
            }, timeout=5)
            
            if response.status_code == 200:
                print(">> Sample game created successfully!")
                print("   Game ID: demo_game")
                print("   Admin Password: admin123")
                print("   CSV File: sample_questions.csv")
                return
            else:
                print(f">> Failed to create sample game (HTTP {response.status_code}): {response.text}")
        
        except requests.exceptions.ConnectionError:
            print(f">> Server not ready yet (attempt {attempt + 1})...")
            if attempt < max_attempts - 1:
                time.sleep(2)
        except requests.exceptions.Timeout:
            print(f">> Request timed out (attempt {attempt + 1})...")
            if attempt < max_attempts - 1:
                time.sleep(2)
        except Exception as e:
            print(f">> Error creating sample game: {e}")
    
    print(">> Failed to create sample game via API after all attempts")
    print(">> Attempting to create game directly...")
    
    # Fallback: create game directly using the game state manager
    try:
        game = game_state_manager.create_game("demo_game", "sample_questions.csv", "admin123")
        print(">> Sample game created successfully (direct method)!")
        print("   Game ID: demo_game")
        print("   Admin Password: admin123")
        print("   CSV File: sample_questions.csv")
    except Exception as e:
        print(f">> Failed to create game directly: {e}")
        print(">> You can manually create a game using the admin interface")

def main():
    print(">> Trivia App Launcher")
    print("=" * 50)
    
    # Check if sample questions file exists
    if not os.path.exists('sample_questions.csv'):
        print(">> sample_questions.csv not found!")
        print("   Make sure you're running from the project root directory.")
        return
    
    print(">> Sample questions found")
    print(">> Starting server...")
    
    # Start game creation in background
    game_thread = threading.Thread(target=create_sample_game, daemon=True)
    game_thread.start()
    
    print(">> Server will be available at: http://localhost:3001/")
    print(">> Health check: http://localhost:3001/health")
    print(">> API endpoint: http://localhost:3001/api/create-game")
    print("\n" + "="*50)
    print("GAME DETAILS:")
    print("Game ID: demo_game")
    print("Admin Password: admin123")
    print("Questions: 6 questions across 2 rounds")
    print("="*50)
    print("\nPress Ctrl+C to stop the server\n")
    
    # Optionally open browser after a delay
    def open_browser():
        time.sleep(4)
        try:
            webbrowser.open('http://localhost:3001/')
            print(">> Browser opened to http://localhost:3001/")
        except:
            print(">> Open your browser to: http://localhost:3001/")
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start the server
    try:
        socketio.run(app, host='0.0.0.0', port=3001, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n>> Shutting down server...")
    except Exception as e:
        print(f">> Server error: {e}")

if __name__ == '__main__':
    main()
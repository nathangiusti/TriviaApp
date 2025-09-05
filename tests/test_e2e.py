import pytest
import time
import tempfile
import os
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from backend.app import app, socketio
from backend.question_manager import QuestionManager
from backend.game_state import GameStateManager
from backend.websocket_manager import WebSocketManager


class TestE2ETrivia:
    """End-to-End tests using Selenium WebDriver"""
    
    @classmethod
    def setup_class(cls):
        """Setup test server and WebDriver"""
        # Create test CSV
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
1,2,What is the capital of France?,Paris
2,1,What is the largest planet?,Jupiter"""
        
        cls.csv_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        cls.csv_file.write(csv_content)
        cls.csv_file.close()
        
        # Start Flask app in a thread
        cls.server_thread = threading.Thread(
            target=lambda: socketio.run(app, host='localhost', port=5000, debug=False),
            daemon=True
        )
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Setup WebDriver options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode for CI
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, 10)
        except Exception as e:
            pytest.skip(f"ChromeDriver not available: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup resources"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        if hasattr(cls, 'csv_file'):
            os.unlink(cls.csv_file.name)
    
    def setup_method(self):
        """Setup for each test"""
        # Create game via API
        import requests
        try:
            response = requests.post('http://localhost:5000/api/create-game', json={
                'game_id': 'e2e_test',
                'csv_file_path': self.csv_file.name,
                'admin_password': 'admin123'
            })
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Flask server not running")
    
    def test_team_join_workflow(self):
        """Test team joining a game"""
        # Load the page
        self.driver.get('http://localhost:5000/frontend/index.html')
        
        # Wait for page to load and connect
        self.wait.until(
            EC.text_to_be_present_in_element((By.ID, 'connection-status'), 'Connected')
        )
        
        # Click "Join as Team"
        join_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Join as Team')]"))
        )
        join_btn.click()
        
        # Fill in game details
        game_id_input = self.wait.until(EC.presence_of_element_located((By.ID, 'game-id')))
        game_id_input.send_keys('e2e_test')
        
        team_name_input = self.driver.find_element(By.ID, 'team-name')
        team_name_input.send_keys('Test Team Alpha')
        
        # Click join game
        join_game_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Join Game')]")
        join_game_btn.click()
        
        # Wait for waiting room
        self.wait.until(
            EC.presence_of_element_located((By.ID, 'waiting-room'))
        )
        
        # Verify team info is displayed
        team_name_element = self.wait.until(
            EC.text_to_be_present_in_element((By.ID, 'current-team-name'), 'Test Team Alpha')
        )
        
        game_id_element = self.driver.find_element(By.ID, 'current-game-id')
        assert game_id_element.text == 'e2e_test'
    
    def test_admin_login_workflow(self):
        """Test admin login and game control"""
        # Load the page
        self.driver.get('http://localhost:5000/frontend/index.html')
        
        # Wait for connection
        self.wait.until(
            EC.text_to_be_present_in_element((By.ID, 'connection-status'), 'Connected')
        )
        
        # Click "Admin Panel"
        admin_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Admin Panel')]"))
        )
        admin_btn.click()
        
        # Fill in admin details
        admin_game_id = self.wait.until(EC.presence_of_element_located((By.ID, 'admin-game-id')))
        admin_game_id.send_keys('e2e_test')
        
        admin_password = self.driver.find_element(By.ID, 'admin-password')
        admin_password.send_keys('admin123')
        
        # Click login
        login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        login_btn.click()
        
        # Wait for admin panel
        self.wait.until(
            EC.presence_of_element_located((By.ID, 'admin-panel'))
        )
        
        # Verify admin panel elements
        game_id_element = self.wait.until(
            EC.text_to_be_present_in_element((By.ID, 'admin-current-game-id'), 'e2e_test')
        )
        
        # Verify start game button is enabled
        start_game_btn = self.driver.find_element(By.ID, 'start-game-btn')
        assert not start_game_btn.get_attribute('disabled')
    
    def test_reconnection_after_refresh(self):
        """Test that user can reconnect after page refresh"""
        # First, join as a team
        self.test_team_join_workflow()
        
        # Refresh the page
        self.driver.refresh()
        
        # Wait for reconnection modal
        try:
            rejoin_modal = self.wait.until(
                EC.presence_of_element_located((By.ID, 'rejoin-modal'))
            )
            
            # Verify game ID is shown
            rejoin_game_id = self.driver.find_element(By.ID, 'rejoin-game-id')
            assert rejoin_game_id.text == 'e2e_test'
            
            # Enter team name
            rejoin_team_name = self.driver.find_element(By.ID, 'rejoin-team-name')
            rejoin_team_name.clear()
            rejoin_team_name.send_keys('Test Team Alpha')
            
            # Click rejoin
            rejoin_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Rejoin Game')]"
            )
            rejoin_btn.click()
            
            # Should be back in waiting room
            self.wait.until(
                EC.presence_of_element_located((By.ID, 'waiting-room'))
            )
            
            # Verify team info is restored
            team_name_element = self.wait.until(
                EC.text_to_be_present_in_element((By.ID, 'current-team-name'), 'Test Team Alpha')
            )
            
        except TimeoutException:
            # If no modal appears, check if we're already reconnected
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.ID, 'waiting-room'))
                )
            except TimeoutException:
                pytest.fail("Neither rejoin modal nor waiting room appeared after refresh")
    
    def test_error_handling_invalid_game(self):
        """Test error handling for invalid game ID"""
        # Load the page
        self.driver.get('http://localhost:5000/frontend/index.html')
        
        # Wait for connection
        self.wait.until(
            EC.text_to_be_present_in_element((By.ID, 'connection-status'), 'Connected')
        )
        
        # Try to join invalid game
        join_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Join as Team')]"))
        )
        join_btn.click()
        
        # Fill in invalid game details
        game_id_input = self.wait.until(EC.presence_of_element_located((By.ID, 'game-id')))
        game_id_input.send_keys('invalid_game')
        
        team_name_input = self.driver.find_element(By.ID, 'team-name')
        team_name_input.send_keys('Test Team')
        
        # Click join game
        join_game_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Join Game')]")
        join_game_btn.click()
        
        # Wait for error message
        error_alert = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert.error'))
        )
        
        assert 'Game not found' in error_alert.text or 'not found' in error_alert.text.lower()


@pytest.mark.integration
class TestMultiUserE2E:
    """Multi-user end-to-end tests requiring multiple browser instances"""
    
    @classmethod
    def setup_class(cls):
        """Setup multiple WebDriver instances"""
        # Same server setup as above
        csv_content = """round_num,question_num,question,answer
1,1,What is 2+2?,4
2,1,What is the capital of France?,Paris"""
        
        cls.csv_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        cls.csv_file.write(csv_content)
        cls.csv_file.close()
        
        # Start Flask app
        cls.server_thread = threading.Thread(
            target=lambda: socketio.run(app, host='localhost', port=5000, debug=False),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(2)
        
        # Setup multiple drivers
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1280,720')
        
        try:
            cls.admin_driver = webdriver.Chrome(options=chrome_options)
            cls.team1_driver = webdriver.Chrome(options=chrome_options)
            cls.team2_driver = webdriver.Chrome(options=chrome_options)
            
            cls.admin_wait = WebDriverWait(cls.admin_driver, 10)
            cls.team1_wait = WebDriverWait(cls.team1_driver, 10)
            cls.team2_wait = WebDriverWait(cls.team2_driver, 10)
            
        except Exception as e:
            pytest.skip(f"ChromeDriver not available: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup all drivers"""
        for driver in [cls.admin_driver, cls.team1_driver, cls.team2_driver]:
            if driver:
                driver.quit()
        if hasattr(cls, 'csv_file'):
            os.unlink(cls.csv_file.name)
    
    def setup_method(self):
        """Create game for each test"""
        import requests
        try:
            response = requests.post('http://localhost:5000/api/create-game', json={
                'game_id': 'multi_test',
                'csv_file_path': self.csv_file.name,
                'admin_password': 'admin123'
            })
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Flask server not running")
    
    def join_as_team(self, driver, wait, team_name):
        """Helper to join as team"""
        driver.get('http://localhost:5000/frontend/index.html')
        
        wait.until(
            EC.text_to_be_present_in_element((By.ID, 'connection-status'), 'Connected')
        )
        
        join_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Join as Team')]"))
        )
        join_btn.click()
        
        game_id_input = wait.until(EC.presence_of_element_located((By.ID, 'game-id')))
        game_id_input.send_keys('multi_test')
        
        team_name_input = driver.find_element(By.ID, 'team-name')
        team_name_input.send_keys(team_name)
        
        join_game_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Join Game')]")
        join_game_btn.click()
        
        wait.until(EC.presence_of_element_located((By.ID, 'waiting-room')))
    
    def login_as_admin(self, driver, wait):
        """Helper to login as admin"""
        driver.get('http://localhost:5000/frontend/index.html')
        
        wait.until(
            EC.text_to_be_present_in_element((By.ID, 'connection-status'), 'Connected')
        )
        
        admin_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Admin Panel')]"))
        )
        admin_btn.click()
        
        admin_game_id = wait.until(EC.presence_of_element_located((By.ID, 'admin-game-id')))
        admin_game_id.send_keys('multi_test')
        
        admin_password = driver.find_element(By.ID, 'admin-password')
        admin_password.send_keys('admin123')
        
        login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        login_btn.click()
        
        wait.until(EC.presence_of_element_located((By.ID, 'admin-panel')))
    
    def test_complete_game_flow(self):
        """Test complete game flow with admin and multiple teams"""
        # Setup all users
        self.login_as_admin(self.admin_driver, self.admin_wait)
        self.join_as_team(self.team1_driver, self.team1_wait, 'Team Alpha')
        self.join_as_team(self.team2_driver, self.team2_wait, 'Team Beta')
        
        # Admin starts the game
        start_game_btn = self.admin_wait.until(
            EC.element_to_be_clickable((By.ID, 'start-game-btn'))
        )
        start_game_btn.click()
        
        # Verify teams see game started
        self.team1_wait.until(
            EC.presence_of_element_located((By.ID, 'game-screen'))
        )
        self.team2_wait.until(
            EC.presence_of_element_located((By.ID, 'game-screen'))
        )
        
        # Admin starts first question
        start_question_btn = self.admin_wait.until(
            EC.element_to_be_clickable((By.ID, 'start-question-btn'))
        )
        start_question_btn.click()
        
        # Teams should see question
        question_display1 = self.team1_wait.until(
            EC.presence_of_element_located((By.ID, 'question-display'))
        )
        question_display2 = self.team2_wait.until(
            EC.presence_of_element_located((By.ID, 'question-display'))
        )
        
        # Teams submit answers
        answer_input1 = self.team1_driver.find_element(By.ID, 'answer-input')
        answer_input1.send_keys('4')
        submit_btn1 = self.team1_driver.find_element(By.ID, 'submit-btn')
        submit_btn1.click()
        
        answer_input2 = self.team2_driver.find_element(By.ID, 'answer-input')
        answer_input2.send_keys('5')
        submit_btn2 = self.team2_driver.find_element(By.ID, 'submit-btn')
        submit_btn2.click()
        
        # Admin closes question
        close_question_btn = self.admin_wait.until(
            EC.element_to_be_clickable((By.ID, 'close-question-btn'))
        )
        close_question_btn.click()
        
        # Admin should see answers for grading
        self.admin_wait.until(
            EC.presence_of_element_located((By.ID, 'answers-panel'))
        )
        
        # Grade answers (Alpha correct, Beta incorrect)
        correct_btns = self.admin_driver.find_elements(
            By.XPATH, "//button[contains(text(), 'Correct')]"
        )
        incorrect_btns = self.admin_driver.find_elements(
            By.XPATH, "//button[contains(text(), 'Incorrect')]"
        )
        
        if correct_btns:
            correct_btns[0].click()  # Grade first team correct
        if incorrect_btns:
            incorrect_btns[0].click()  # Grade second team incorrect
        
        # Move to next question
        next_question_btn = self.admin_wait.until(
            EC.element_to_be_clickable((By.ID, 'next-question-btn'))
        )
        next_question_btn.click()
        
        # Verify we can start the next question
        start_question_btn = self.admin_wait.until(
            EC.element_to_be_clickable((By.ID, 'start-question-btn'))
        )
        
        # This confirms the complete workflow is functional
        assert start_question_btn.is_enabled()


# Utility function to run E2E tests
def run_e2e_tests():
    """Run end-to-end tests (can be called from external test runner)"""
    pytest.main([__file__ + '::TestE2ETrivia', '-v', '-s'])


if __name__ == '__main__':
    run_e2e_tests()
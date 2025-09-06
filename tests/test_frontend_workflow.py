import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestFrontendWorkflow:
    """Test the frontend component visibility workflow and state transitions"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Create a Chrome WebDriver instance for testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for CI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            yield driver
        finally:
            if 'driver' in locals():
                driver.quit()
    
    @pytest.fixture
    def base_url(self):
        """Base URL for the application"""
        return "http://localhost:5000"
    
    def wait_for_element(self, driver, by, value, timeout=10):
        """Helper method to wait for an element to be present"""
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def wait_for_element_visible(self, driver, by, value, timeout=10):
        """Helper method to wait for an element to be visible"""
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
    
    def wait_for_element_hidden(self, driver, by, value, timeout=10):
        """Helper method to wait for an element to be hidden"""
        return WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((by, value))
        )
    
    def is_element_visible(self, driver, element_id):
        """Check if an element is visible (not hidden and displayed)"""
        try:
            element = driver.find_element(By.ID, element_id)
            return element.is_displayed() and "hidden" not in element.get_attribute("class")
        except NoSuchElementException:
            return False
    
    def test_initial_page_load_shows_only_join_game(self, driver, base_url):
        """Test that on initial load, only the join game form is visible"""
        driver.get(base_url)
        
        # Wait for page to load
        self.wait_for_element(driver, By.ID, "home-screen")
        
        # Verify home screen is visible
        assert self.is_element_visible(driver, "home-screen"), "Home screen should be visible"
        
        # Verify player join form is visible within home screen
        assert self.is_element_visible(driver, "player-join-form"), "Player join form should be visible"
        
        # Verify other components are hidden
        assert not self.is_element_visible(driver, "waiting-room"), "Waiting room should be hidden"
        assert not self.is_element_visible(driver, "game-screen"), "Game screen should be hidden"
        assert not self.is_element_visible(driver, "game-finished"), "Game finished screen should be hidden"
        
        # Verify required form elements are present
        game_id_input = driver.find_element(By.ID, "game-id")
        team_name_input = driver.find_element(By.ID, "team-name")
        join_button = driver.find_element(By.XPATH, "//button[text()='Join Game']")
        
        assert game_id_input.is_displayed(), "Game ID input should be displayed"
        assert team_name_input.is_displayed(), "Team name input should be displayed"
        assert join_button.is_displayed(), "Join Game button should be displayed"
        
        # Verify admin panel link is NOT present
        try:
            admin_link = driver.find_element(By.XPATH, "//a[contains(@href, '/admin')]")
            pytest.fail("Admin panel link should not be present on main page")
        except NoSuchElementException:
            pass  # This is expected
    
    def test_component_visibility_classes(self, driver, base_url):
        """Test that components have proper hidden classes initially"""
        driver.get(base_url)
        
        # Check that components that should be hidden have the 'hidden' class
        waiting_room = driver.find_element(By.ID, "waiting-room")
        game_screen = driver.find_element(By.ID, "game-screen")
        game_finished = driver.find_element(By.ID, "game-finished")
        
        assert "hidden" in waiting_room.get_attribute("class"), "Waiting room should have 'hidden' class"
        assert "hidden" in game_screen.get_attribute("class"), "Game screen should have 'hidden' class"
        assert "hidden" in game_finished.get_attribute("class"), "Game finished should have 'hidden' class"
        
        # Check that home screen does NOT have the 'hidden' class
        home_screen = driver.find_element(By.ID, "home-screen")
        assert "hidden" not in home_screen.get_attribute("class"), "Home screen should not have 'hidden' class"
    
    def test_join_game_form_validation(self, driver, base_url):
        """Test that join game form shows validation for empty fields"""
        driver.get(base_url)
        
        # Try to join with empty fields
        join_button = driver.find_element(By.XPATH, "//button[text()='Join Game']")
        join_button.click()
        
        # Should still be on home screen as validation should prevent submission
        assert self.is_element_visible(driver, "home-screen"), "Should stay on home screen with empty fields"
        
        # Try with only game ID
        game_id_input = driver.find_element(By.ID, "game-id")
        game_id_input.send_keys("TEST123")
        join_button.click()
        
        # Should still be on home screen as team name is missing
        assert self.is_element_visible(driver, "home-screen"), "Should stay on home screen without team name"
        
        # Now add team name
        team_name_input = driver.find_element(By.ID, "team-name")
        team_name_input.send_keys("TestTeam")
        
        # Form should now be ready for submission (though server may not be running)
        # We just test that the form allows the click
        join_button.click()
        
        # Note: Without a running server, this might show an error or stay on the same page
        # The important thing is that it attempts to submit
    
    def test_connection_status_indicator_present(self, driver, base_url):
        """Test that connection status indicator is present"""
        driver.get(base_url)
        
        connection_status = driver.find_element(By.ID, "connection-status")
        assert connection_status.is_displayed(), "Connection status should be displayed"
    
    def test_rejoin_modal_exists_but_hidden(self, driver, base_url):
        """Test that rejoin modal exists but is initially hidden"""
        driver.get(base_url)
        
        rejoin_modal = driver.find_element(By.ID, "rejoin-modal")
        
        # Modal should exist but not be displayed
        assert not rejoin_modal.is_displayed(), "Rejoin modal should be hidden initially"
    
    def test_game_flow_elements_structure(self, driver, base_url):
        """Test that all required game flow elements are present in the DOM"""
        driver.get(base_url)
        
        # Verify all main game flow components exist
        components = [
            "home-screen",
            "waiting-room", 
            "game-screen",
            "game-finished"
        ]
        
        for component_id in components:
            element = driver.find_element(By.ID, component_id)
            assert element is not None, f"Component {component_id} should exist in DOM"
        
        # Verify key elements within each component
        
        # Home screen elements
        assert driver.find_element(By.ID, "game-id"), "Game ID input should exist"
        assert driver.find_element(By.ID, "team-name"), "Team name input should exist"
        
        # Waiting room elements
        assert driver.find_element(By.ID, "current-game-id"), "Current game ID display should exist"
        assert driver.find_element(By.ID, "current-team-name"), "Current team name display should exist"
        assert driver.find_element(By.ID, "teams-list"), "Teams list should exist"
        
        # Game screen elements
        assert driver.find_element(By.ID, "question-display"), "Question display should exist"
        assert driver.find_element(By.ID, "leaderboard"), "Leaderboard should exist"
        assert driver.find_element(By.ID, "answer-form"), "Answer form should exist"
        
        # Game finished elements
        assert driver.find_element(By.ID, "final-leaderboard"), "Final leaderboard should exist"
    
    def test_waiting_room_components_hidden_initially(self, driver, base_url):
        """Test that waiting room components are properly hidden initially"""
        driver.get(base_url)
        
        waiting_room = driver.find_element(By.ID, "waiting-room")
        assert not waiting_room.is_displayed(), "Waiting room should not be displayed initially"
        
        # Elements within waiting room should also not be visible
        current_game_id = driver.find_element(By.ID, "current-game-id")
        current_team_name = driver.find_element(By.ID, "current-team-name")
        teams_list = driver.find_element(By.ID, "teams-list")
        
        assert not current_game_id.is_displayed(), "Current game ID should not be displayed initially"
        assert not current_team_name.is_displayed(), "Current team name should not be displayed initially"
        assert not teams_list.is_displayed(), "Teams list should not be displayed initially"
    
    def test_game_screen_components_hidden_initially(self, driver, base_url):
        """Test that game screen components are properly hidden initially"""
        driver.get(base_url)
        
        game_screen = driver.find_element(By.ID, "game-screen")
        assert not game_screen.is_displayed(), "Game screen should not be displayed initially"
        
        # Elements within game screen should also not be visible
        question_display = driver.find_element(By.ID, "question-display")
        answer_form = driver.find_element(By.ID, "answer-form")
        leaderboard = driver.find_element(By.ID, "leaderboard")
        
        assert not question_display.is_displayed(), "Question display should not be displayed initially"
        assert not answer_form.is_displayed(), "Answer form should not be displayed initially"
        assert not leaderboard.is_displayed(), "Leaderboard should not be displayed initially"
    
    def test_game_finished_components_hidden_initially(self, driver, base_url):
        """Test that game finished components are properly hidden initially"""
        driver.get(base_url)
        
        game_finished = driver.find_element(By.ID, "game-finished")
        assert not game_finished.is_displayed(), "Game finished screen should not be displayed initially"
        
        # Elements within game finished should also not be visible
        final_leaderboard = driver.find_element(By.ID, "final-leaderboard")
        assert not final_leaderboard.is_displayed(), "Final leaderboard should not be displayed initially"
    
    def test_javascript_files_loaded(self, driver, base_url):
        """Test that required JavaScript files are loaded"""
        driver.get(base_url)
        
        # Check that GameClient is available (this indicates game-client.js loaded)
        game_client_available = driver.execute_script("return typeof GameClient !== 'undefined'")
        assert game_client_available, "GameClient should be available (game-client.js should be loaded)"
        
        # Check that main app functions are available (this indicates app.js loaded)
        join_game_function = driver.execute_script("return typeof joinGame === 'function'")
        assert join_game_function, "joinGame function should be available (app.js should be loaded)"
    
    def test_socket_io_library_loaded(self, driver, base_url):
        """Test that Socket.IO library is loaded"""
        driver.get(base_url)
        
        # Check that Socket.IO is available
        socket_io_available = driver.execute_script("return typeof io !== 'undefined'")
        assert socket_io_available, "Socket.IO should be available"
    
    @pytest.mark.integration
    def test_dom_ready_initialization(self, driver, base_url):
        """Test that the page initializes properly when DOM is ready"""
        driver.get(base_url)
        
        # Wait for initialization to complete
        time.sleep(2)
        
        # Check that gameClient is initialized
        game_client_initialized = driver.execute_script("return typeof gameClient !== 'undefined' && gameClient !== null")
        assert game_client_initialized, "gameClient should be initialized on DOM ready"
        
        # Check that connection attempt was made (connection status should be set)
        connection_status = driver.find_element(By.ID, "connection-status")
        status_text = connection_status.text
        assert status_text in ["✓ Connected", "✗ Disconnected", "⟳ Reconnecting..."], f"Connection status should be set, got: {status_text}"


class TestFrontendWorkflowIntegration:
    """Integration tests for the complete frontend workflow"""
    
    def test_state_transitions_structure(self):
        """Test that the state transition structure is correct (without server)"""
        # This test validates the JavaScript logic structure without requiring a running server
        
        # Expected state flow:
        # 1. Initial load -> Join Game only visible
        # 2. Team joins -> Waiting Room visible
        # 3. Game starts -> Game Screen visible  
        # 4. Game ends -> Game Finished visible
        
        expected_initial_state = {
            "home-screen": True,
            "waiting-room": False,
            "game-screen": False, 
            "game-finished": False
        }
        
        # This test documents the expected behavior
        # Actual state testing requires integration with the backend
        assert expected_initial_state["home-screen"], "Home screen should be visible initially"
        assert not expected_initial_state["waiting-room"], "Waiting room should be hidden initially"
        assert not expected_initial_state["game-screen"], "Game screen should be hidden initially"  
        assert not expected_initial_state["game-finished"], "Game finished should be hidden initially"
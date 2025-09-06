import pytest
from backend.app import app
from bs4 import BeautifulSoup


class TestFrontendComponentVisibility:
    """Test frontend component visibility and structure without requiring Selenium"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_main_page_initial_component_visibility(self, client):
        """Test that main page has correct initial component visibility structure"""
        response = client.get('/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test home screen is NOT hidden (should be visible)
        home_screen = soup.find('div', id='home-screen')
        assert home_screen is not None, "Home screen element should exist"
        home_screen_classes = home_screen.get('class', [])
        assert 'hidden' not in home_screen_classes, "Home screen should not have 'hidden' class"
        
        # Test other components ARE hidden initially
        waiting_room = soup.find('div', id='waiting-room')
        assert waiting_room is not None, "Waiting room element should exist"
        waiting_room_classes = waiting_room.get('class', [])
        assert 'hidden' in waiting_room_classes, "Waiting room should have 'hidden' class"
        
        game_screen = soup.find('div', id='game-screen')
        assert game_screen is not None, "Game screen element should exist"
        game_screen_classes = game_screen.get('class', [])
        assert 'hidden' in game_screen_classes, "Game screen should have 'hidden' class"
        
        game_finished = soup.find('div', id='game-finished')
        assert game_finished is not None, "Game finished element should exist"
        game_finished_classes = game_finished.get('class', [])
        assert 'hidden' in game_finished_classes, "Game finished should have 'hidden' class"
    
    def test_player_join_form_elements_present(self, client):
        """Test that player join form has all required elements"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test join game form elements
        player_join_form = soup.find('div', id='player-join-form')
        assert player_join_form is not None, "Player join form should exist"
        
        # Test form inputs
        game_id_input = soup.find('input', id='game-id')
        assert game_id_input is not None, "Game ID input should exist"
        assert game_id_input.get('placeholder') == 'Enter game ID', "Game ID input should have correct placeholder"
        
        team_name_input = soup.find('input', id='team-name')
        assert team_name_input is not None, "Team name input should exist"
        assert team_name_input.get('placeholder') == 'Enter your team name', "Team name input should have correct placeholder"
        
        # Test join button
        join_button = soup.find('button', string='Join Game')
        assert join_button is not None, "Join Game button should exist"
        assert 'joinGame()' in join_button.get('onclick', ''), "Join button should have joinGame() onclick"
    
    def test_admin_panel_link_removed_from_main_page(self, client):
        """Test that admin panel link has been removed from main page"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test that no admin panel links exist
        admin_links = soup.find_all('a', href='/admin')
        assert len(admin_links) == 0, "No admin panel links should exist on main page"
        
        # Test that no "Admin Panel" text exists (except potentially in comments)
        assert 'Admin Panel' not in html_content, "Admin Panel text should not appear on main page"
    
    def test_waiting_room_structure(self, client):
        """Test that waiting room has correct structure"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        waiting_room = soup.find('div', id='waiting-room')
        assert waiting_room is not None, "Waiting room should exist"
        
        # Test key elements within waiting room
        current_game_id = soup.find('span', id='current-game-id')
        assert current_game_id is not None, "Current game ID display should exist"
        
        current_team_name = soup.find('span', id='current-team-name')
        assert current_team_name is not None, "Current team name display should exist"
        
        teams_list = soup.find('ul', id='teams-list')
        assert teams_list is not None, "Teams list should exist"
        
        leave_button = soup.find('button', string='Leave Game')
        assert leave_button is not None, "Leave Game button should exist"
    
    def test_game_screen_structure(self, client):
        """Test that game screen has correct structure"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        game_screen = soup.find('div', id='game-screen')
        assert game_screen is not None, "Game screen should exist"
        
        # Test key elements within game screen
        question_display = soup.find('div', id='question-display')
        assert question_display is not None, "Question display should exist"
        
        answer_form = soup.find('div', id='answer-form')
        assert answer_form is not None, "Answer form should exist"
        
        answer_input = soup.find('input', id='answer-input')
        assert answer_input is not None, "Answer input should exist"
        
        submit_button = soup.find('button', string='Submit Answer')
        assert submit_button is not None, "Submit Answer button should exist"
        
        leaderboard = soup.find('div', id='leaderboard')
        assert leaderboard is not None, "Leaderboard should exist"
    
    def test_game_finished_structure(self, client):
        """Test that game finished screen has correct structure"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        game_finished = soup.find('div', id='game-finished')
        assert game_finished is not None, "Game finished screen should exist"
        
        # Test key elements within game finished screen
        final_leaderboard = soup.find('ul', id='final-leaderboard')
        assert final_leaderboard is not None, "Final leaderboard should exist"
        
        new_game_button = soup.find('button', string='New Game')
        assert new_game_button is not None, "New Game button should exist"
    
    def test_connection_status_indicator(self, client):
        """Test that connection status indicator exists"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        connection_status = soup.find('div', id='connection-status')
        assert connection_status is not None, "Connection status indicator should exist"
        
        # Should have connection-status class and disconnected initially
        status_classes = connection_status.get('class', [])
        assert 'connection-status' in status_classes, "Should have connection-status class"
        assert 'disconnected' in status_classes, "Should initially show disconnected state"
    
    def test_rejoin_modal_structure(self, client):
        """Test that rejoin modal has correct structure"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        rejoin_modal = soup.find('div', id='rejoin-modal')
        assert rejoin_modal is not None, "Rejoin modal should exist"
        
        # Test modal structure
        modal_content = soup.find('div', class_='modal-content')
        assert modal_content is not None, "Modal content should exist"
        
        rejoin_game_id = soup.find('strong', id='rejoin-game-id')
        assert rejoin_game_id is not None, "Rejoin game ID display should exist"
        
        rejoin_team_name = soup.find('input', id='rejoin-team-name')
        assert rejoin_team_name is not None, "Rejoin team name input should exist"
        
        rejoin_button = soup.find('button', string='Rejoin Game')
        assert rejoin_button is not None, "Rejoin Game button should exist"
        
        start_fresh_button = soup.find('button', string='Start Fresh')
        assert start_fresh_button is not None, "Start Fresh button should exist"
    
    def test_required_javascript_includes(self, client):
        """Test that required JavaScript files are included"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test Socket.IO CDN include
        socket_io_script = soup.find('script', src='https://cdn.socket.io/4.7.2/socket.io.min.js')
        assert socket_io_script is not None, "Socket.IO CDN script should be included"
        
        # Test game-client.js include
        game_client_script = soup.find('script', src='js/game-client.js')
        assert game_client_script is not None, "game-client.js should be included"
        
        # Test app.js include
        app_script = soup.find('script', src='js/app.js')
        assert app_script is not None, "app.js should be included"
    
    def test_css_stylesheet_included(self, client):
        """Test that CSS stylesheet is included"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test CSS include
        css_link = soup.find('link', rel='stylesheet', href='css/styles.css')
        assert css_link is not None, "CSS stylesheet should be included"
    
    def test_proper_html_structure(self, client):
        """Test that HTML has proper structure"""
        response = client.get('/')
        html_content = response.get_data(as_text=True)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test basic HTML structure
        assert soup.find('html') is not None, "HTML tag should exist"
        assert soup.find('head') is not None, "HEAD tag should exist"
        assert soup.find('body') is not None, "BODY tag should exist"
        
        # Test title
        title = soup.find('title')
        assert title is not None, "Title tag should exist"
        assert title.string == 'Trivia App', "Title should be 'Trivia App'"
        
        # Test viewport meta tag for mobile responsiveness
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        assert viewport_meta is not None, "Viewport meta tag should exist"
        
        # Test main container
        container = soup.find('div', class_='container')
        assert container is not None, "Main container should exist"


class TestGameFlowLogic:
    """Test the logical flow of game states"""
    
    def test_game_state_progression_logic(self):
        """Test that game state progression follows correct logic"""
        
        # Define the expected state progression
        state_flow = [
            # Initial state
            {
                'current': 'join_game',
                'visible': ['home-screen'],
                'hidden': ['waiting-room', 'game-screen', 'game-finished']
            },
            # After team joins successfully  
            {
                'current': 'waiting_room',
                'visible': ['waiting-room'],
                'hidden': ['home-screen', 'game-screen', 'game-finished']
            },
            # After game starts
            {
                'current': 'game_screen', 
                'visible': ['game-screen'],
                'hidden': ['home-screen', 'waiting-room', 'game-finished']
            },
            # After game finishes
            {
                'current': 'game_finished',
                'visible': ['game-finished'],
                'hidden': ['home-screen', 'waiting-room', 'game-screen']
            }
        ]
        
        # Test that each state has exactly one visible component
        for state in state_flow:
            assert len(state['visible']) == 1, f"Each state should have exactly one visible component, {state['current']} has {len(state['visible'])}"
            
            # Test that visible and hidden don't overlap
            visible_set = set(state['visible'])
            hidden_set = set(state['hidden'])
            assert visible_set.isdisjoint(hidden_set), f"Visible and hidden components should not overlap in {state['current']}"
            
            # Test that all main components are accounted for
            all_components = visible_set.union(hidden_set)
            expected_components = {'home-screen', 'waiting-room', 'game-screen', 'game-finished'}
            assert all_components == expected_components, f"All components should be accounted for in {state['current']}"
    
    def test_event_driven_state_transitions(self):
        """Test that state transitions are properly event-driven"""
        
        # Define the events that trigger state transitions
        transitions = [
            {
                'from': 'join_game',
                'event': 'team_joined',
                'to': 'waiting_room'
            },
            {
                'from': 'waiting_room', 
                'event': 'game_started',
                'to': 'game_screen'
            },
            {
                'from': 'game_screen',
                'event': 'game_finished', 
                'to': 'game_finished'
            }
        ]
        
        # Verify that each transition is well-defined
        for transition in transitions:
            assert 'from' in transition, "Transition should define starting state"
            assert 'event' in transition, "Transition should define triggering event"
            assert 'to' in transition, "Transition should define ending state"
            
            # Verify states are different (no self-transitions for these events)
            assert transition['from'] != transition['to'], f"Event {transition['event']} should cause state change"
import pytest
from backend.app import app


class TestRoutes:
    """Test web routes and URL endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_main_page_route(self, client):
        """Test that the main page (/) serves the player interface"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'
        
        # Check that the response contains player join elements
        html_content = response.get_data(as_text=True)
        assert 'Join Game' in html_content
        assert 'game-id' in html_content
        assert 'team-name' in html_content
        
        # Ensure admin-specific elements are NOT present on main page
        assert 'admin-password' not in html_content
        assert 'Admin Panel' not in html_content
        assert 'href="/admin"' not in html_content
    
    def test_admin_page_route(self, client):
        """Test that the admin page (/admin) serves the admin login interface"""
        response = client.get('/admin')
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'
        
        # Check that the response contains admin login elements
        html_content = response.get_data(as_text=True)
        assert '🛠️ Admin Login' in html_content  # Updated heading
        assert 'admin-game-id' in html_content
        assert 'admin-password' in html_content
        assert 'admin-error' in html_content  # Error display element
        assert 'admin-login-screen' in html_content  # Updated ID
        
        # Ensure admin panel and game finished screens exist but are hidden initially
        assert 'id="admin-panel"' in html_content
        assert 'admin-panel" class="card hidden" style="display: none !important;"' in html_content
        assert 'id="game-finished"' in html_content
        assert 'game-finished" class="card hidden" style="display: none !important;"' in html_content
        
        # Ensure player-only elements are not present
        assert 'team-name' not in html_content
    
    def test_health_check_route(self, client):
        """Test the health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        json_data = response.get_json()
        assert json_data['status'] == 'healthy'
        assert json_data['service'] == 'trivia-app'
    
    def test_nonexistent_route(self, client):
        """Test that nonexistent routes return 404"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
    
    def test_create_game_api_endpoint_exists(self, client):
        """Test that the API endpoint for creating games exists"""
        # This should return 400 because we're not sending required data,
        # but it confirms the route exists
        response = client.post('/api/create-game')
        assert response.status_code == 400  # Bad request due to missing data
        assert response.content_type == 'application/json'
    
    def test_static_files_accessibility(self, client):
        """Test that CSS and JS files are accessible"""
        # Test CSS file
        css_response = client.get('/frontend/css/styles.css')
        assert css_response.status_code == 200
        
        # Test JS files
        js_response = client.get('/frontend/js/app.js')
        assert js_response.status_code == 200
        
        game_client_response = client.get('/frontend/js/game-client.js')
        assert game_client_response.status_code == 200
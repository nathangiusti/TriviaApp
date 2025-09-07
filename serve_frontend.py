#!/usr/bin/env python3
"""
Simple HTTP server to serve frontend files alongside the Flask app
"""

import os
import http.server
import socketserver
import threading
import webbrowser
from backend.app import app, socketio

class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='frontend', **kwargs)
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_frontend_server(port=8000):
    """Start HTTP server for frontend files"""
    handler = FrontendHandler
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"Frontend server running at http://localhost:{port}/")
    httpd.serve_forever()

def start_backend_server():
    """Start Flask/SocketIO backend server"""
    print("Backend server running at http://localhost:3001/")
    socketio.run(app, host='0.0.0.0', port=3001, debug=False)

def main():
    print("🎯 Starting Trivia App Servers")
    print("=" * 50)
    
    # Start backend in a thread
    backend_thread = threading.Thread(target=start_backend_server, daemon=True)
    backend_thread.start()
    
    # Start frontend server in a thread
    frontend_thread = threading.Thread(target=lambda: start_frontend_server(8000), daemon=True)
    frontend_thread.start()
    
    # Wait a moment for servers to start
    import time
    time.sleep(2)
    
    print("\n✅ Servers started successfully!")
    print(f"🌐 Open your browser to: http://localhost:8000/")
    print(f"🔧 Backend API available at: http://localhost:3001/")
    print(f"📊 Health check: http://localhost:3001/health")
    print("\nPress Ctrl+C to stop servers")
    
    # Optionally open browser
    try:
        webbrowser.open('http://localhost:8000/')
    except:
        pass
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down servers...")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Simple HTTP server for serving the frontend files
"""

import http.server
import socketserver
import os
import sys

PORT = 5500

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    print(f"Starting frontend server on port {PORT}...")
    print(f"Frontend will be available at: http://localhost:{PORT}")
    print(f"Make sure the backend is running on http://localhost:8000")
    print("\nPress Ctrl+C to stop the server")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

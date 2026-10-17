import http.server
import socketserver
import os
import sys
import json
import webbrowser

PORT = 40404
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_FILE = os.path.join(BASE_DIR, "data", "academic_data.json")

class KampusIntelligenceHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_GET(self):
        # API Endpoints
        if self.path == "/api/data" or self.path.startswith("/api/data?"):
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error": "Data file not found"}')
            return

        if self.path.startswith("/api/student/"):
            npm = self.path.split("/api/student/")[1].split("?")[0].strip()
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                matched = next((s for s in data.get("students", []) if s["npm"] == npm), None)
                if matched:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps(matched, ensure_ascii=False).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Mahasiswa tidak ditemukan"}')
            return

        # Fallback to serving static files from public/
        return super().do_GET()

def run_server():
    os.chdir(BASE_DIR)
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    
    # Allow port reuse immediately
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), KampusIntelligenceHandler) as httpd:
        print("=" * 65)
        print(f"🎓 SIAK-KAPRODI ARSITEKTUR INTELLIGENCE SERVER ACTIVE")
        print(f"📡 Local Server URL: http://localhost:{PORT}")
        print(f"📁 Serving Root: {PUBLIC_DIR}")
        print(f"⚡ Press Ctrl+C or run stop_server.bat to terminate")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server cleanly...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()

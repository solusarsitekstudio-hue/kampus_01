import http.server
import socketserver
import os
import sys
import json
import webbrowser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

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

        # API Output Runs & Hierarchy Metadata
        if self.path == "/api/runs":
            output_root = os.path.join(BASE_DIR, "output")
            runs = []
            if os.path.exists(output_root):
                for course_f in sorted(os.listdir(output_root)):
                    course_p = os.path.join(output_root, course_f)
                    if os.path.isdir(course_p):
                        for ts in sorted(os.listdir(course_p), reverse=True):
                            ts_p = os.path.join(course_p, ts)
                            manifest_p = os.path.join(ts_p, "manifest.json")
                            if os.path.isfile(manifest_p):
                                try:
                                    with open(manifest_p, "r", encoding="utf-8") as mf:
                                        runs.append(json.load(mf))
                                except Exception:
                                    pass
            latest_p = os.path.join(output_root, "latest_run.json")
            latest = {}
            if os.path.exists(latest_p):
                with open(latest_p, "r", encoding="utf-8") as lf:
                    latest = json.load(lf)

            res = {"latest": latest, "runs": runs}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        # Serving files directly from output/ hierarchy (e.g. /output/<course>/<timestamp>/<file>)
        if self.path.startswith("/output/"):
            rel_path = self.path[len("/output/"):].split("?")[0]
            safe_rel_path = os.path.normpath(rel_path).lstrip("\\/")
            if safe_rel_path.startswith(".."):
                self.send_response(403)
                self.end_headers()
                return
            filepath = os.path.join(BASE_DIR, "output", safe_rel_path)
            if os.path.exists(filepath) and os.path.isfile(filepath):
                self.send_response(200)
                if filepath.endswith(".pdf"):
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", f'inline; filename="{os.path.basename(filepath)}"')
                elif filepath.endswith(".json"):
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Output file not found")
            return

        # Serving Generated PDF Documents (with fallback to latest output run)
        if self.path.startswith("/generated_pdfs/"):
            filename = self.path.split("/generated_pdfs/")[1].split("?")[0]
            filepath = os.path.join(BASE_DIR, "generated_pdfs", filename)
            
            # Fallback check into latest_run directory if legacy file does not exist
            if not os.path.exists(filepath):
                latest_p = os.path.join(BASE_DIR, "output", "latest_run.json")
                if os.path.exists(latest_p):
                    try:
                        with open(latest_p, "r", encoding="utf-8") as lf:
                            latest_data = json.load(lf)
                            candidate = os.path.join(latest_data.get("latest_directory", ""), filename)
                            if os.path.exists(candidate):
                                filepath = candidate
                    except Exception:
                        pass

            if os.path.exists(filepath) and os.path.isfile(filepath):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"PDF file not found")
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
        print("[SIAK-KAPRODI] ARSITEKTUR INTELLIGENCE SERVER ACTIVE")
        print(f"[STATUS] Local Server URL: http://localhost:{PORT}")
        print(f"[ROOT] Serving Root: {PUBLIC_DIR}")
        print(f"[INFO] Press Ctrl+C or run stop_server.bat to terminate")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server cleanly...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()

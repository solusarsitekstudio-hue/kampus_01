"""
SIAK-KAPRODI - Arsitektur Intelligence Server
=============================================
Local-only web server untuk dashboard akademik Program Studi Arsitektur.

FIX TAHAP A (aman - tidak mengubah satu pun angka/data):
  * Server jadi THREADING  -> render PDF/video tidak lagi membekukan seluruh app
  * Bind ke 127.0.0.1      -> tidak bisa diakses dari jaringan lain
  * Path traversal ditutup -> /generated_pdfs/, /output/, /api/open_folder
  * Error dibalas JSON valid (json.dumps), bukan f-string rusak
  * Fallback "students[0]" dihapus -> NPM salah = error jelas, bukan rapor orang lain
  * Penulisan data atomic + threading.Lock -> aman dari race condition
  * sys.path di-hoist ke module scope -> tidak menumpuk tiap request

FIX TAHAP C-2 (aman - tidak mengubah satu pun angka/data):
  * HTTP/1.1            -> koneksi keep-alive, header Range dihormati
  * Byte-range (206)    -> video portofolio bisa di-SEEK di browser; dulu tidak
  * Kirim per 64 KB     -> video 856 KB tidak lagi dibaca penuh ke RAM setiap kali
  * Guard double-start  -> server kedua menolak jalan (Windows SO_REUSEADDR bisa
                           membuat dua server :40404 tanpa error)

FIX TAHAP C-5 (aman - tidak mengubah satu pun angka/data):
  * Penjaga katalog     -> /api/switch_course MENOLAK katalog yang versinya lebih
                           lama dari master. Dulu sekali "ganti mata kuliah" bisa
                           mengembalikan seluruh sistem ke aturan lama (At-Risk
                           10 -> 1) tanpa satu pun pesan error.
  * MK aktif = no-op    -> ganti ke MK yang sedang aktif tidak menimpa master;
                           katalognya malah diselaraskan dari master.
"""

import http.server
import socketserver
import os
import sys
import json
import re
import shutil
import socket
import threading
import tempfile
import time
from urllib.parse import urlparse, parse_qs

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PORT = 40404
HOST = "127.0.0.1"  # LOCAL ONLY - jangan diubah tanpasadari risikonya
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_FILE = os.path.join(BASE_DIR, "data", "academic_data.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GENERATED_PDFS_DIR = os.path.join(BASE_DIR, "generated_pdfs")
PROGRESS_ROOT = os.path.join(BASE_DIR, "input", "progress_mahasiswa")
DECKCRAFT_SCRIPTS = os.environ.get(
    "OPENCRAFT_MCP_SCRIPTS", r"E:\WORKSHOP\OPEN_CRAFT_MCP\scripts"
)

# NPM mahasiswa: 8-14 digit. Dipakai untuk validate SEBELUM path dipakai.
NPM_RE = re.compile(r"^\d{8,14}$")

# Pengaman penulisan data master (dipakai saat /api/switch_course)
DATA_LOCK = threading.Lock()

# sys.path di-hoist ke module scope (sekali saja, bukan tiap request)
_SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
for _p in (_SCRIPTS_DIR, DECKCRAFT_SCRIPTS):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)


# =============================================================================
# HELPER
# =============================================================================
def _sanitize_error(exc: Exception) -> str:
    """Ubah exception jadi teks 1 baris yang aman ditaruh di dalam JSON."""
    return " ".join(str(exc).split())[:400] or exc.__class__.__name__


def atomic_write_json(path: str, payload) -> None:
    """Tulis JSON secara atomic: tulis ke .tmp dulu, lalu os.replace().
    Mencegah file 0-byte kalau server mati di tengah proses."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)  # atomic di Windows & POSIX
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def read_json_safe(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_student(data: dict, npm):
    """Cari mahasiswa by NPM. TIDAK ADA fallback ke students[0] -
    fallback dulu membuat rapor orang salah terkirim ke wali murid yang salah."""
    if npm is None:
        return None
    target = str(npm).strip()
    return next((s for s in data.get("students", []) if str(s.get("npm", "")) == target), None)


def safe_relative_path(raw: str):
    """Cegah path traversal. Return path absolut yang aman, atau None."""
    if raw is None:
        return None
    # Tolak drive letter absolut (C:\... atau C:/...)
    if os.path.isabs(raw) or re.match(r"^[A-Za-z]:", raw):
        return None
    # Tolak NUL byte
    if "\x00" in raw:
        return None
    norm = os.path.normpath(raw).lstrip("\\/")
    if norm.startswith("..") or os.path.isabs(norm):
        return None
    return norm


# =============================================================================
# TABEL MIME + PARAMETER TRANSFER FILE
# =============================================================================
# FIX TAHAP C-2: sebelumnya _send_file_inline hanya mengenali 4 ekstensi, dan
# video MP4 dilayani sebagai application/octet-stream oleh SimpleHTTPRequestHandler.
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}

# "bytes=0-", "bytes=1000-2000", "bytes=-500" (500 byte terakhir)
RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")
CHUNK_SIZE = 64 * 1024


def guess_content_type(filepath: str) -> str:
    return CONTENT_TYPES.get(os.path.splitext(filepath)[1].lower(),
                             "application/octet-stream")


def versi_tuple(versi) -> tuple:
    """'2.5-GOLDEN-DEMO' -> (2, 5). Dipakai penjaga katalog (FIX TAHAP C-5).

    Tidak bisa dibandingkan sebagai teks: '2.10' < '2.9' secara alfabet,
    padahal sebaliknya secara versi.
    """
    if not isinstance(versi, str):
        return (0,)
    angka = re.findall(r"\d+", versi)
    return tuple(int(a) for a in angka) if angka else (0,)


# =============================================================================
# HANDLER
# =============================================================================
class KampusIntelligenceHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "SIAK-KAPRODI"
    # FIX TAHAP C-2: HTTP/1.0 memaksa satu koneksi per permintaan dan TIDAK
    # mendukung byte-range. Akibatnya pemutar video di browser tidak bisa
    # "seek": menggeser timeline berarti mengunduh ulang dari detik 0, dan
    # beberapa browser menolak memutar file sama sekali.
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    # ------------------------------------------------------------------ output
    def _send_bytes(self, status: int, body: bytes, content_type: str, extra=None):
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # user nutup tab - bukan error fatal

    def _send_json(self, status: int, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _send_error_json(self, status: int, message: str, extra: dict | None = None):
        payload = {"error": message}
        if extra:
            payload.update(extra)
        self._send_json(status, payload)

    def handle_error(self, type_, value, tb):  # noqa: ANN001
        """Jangan dump traceback ke console buat error koneksi (user nutup tab)."""
        if issubclass(type_, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        socketserver.BaseServer.handle_error(self, type_, value, tb)

    # -------------------------------------------------------------------- GET
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/data":
            return self._api_data()
        if path == "/api/courses":
            return self._api_courses()
        if path == "/api/runs":
            return self._api_runs()
        if path.startswith("/api/switch_course"):
            return self._api_switch_course(query)
        if path.startswith("/api/student/images"):
            return self._api_student_images(query)
        if path.startswith("/api/student/"):
            return self._api_student(path)
        if path.startswith("/api/deckcraft_html"):
            return self._api_deckcraft_html(query)
        if path.startswith("/api/pdf/download"):
            return self._api_pdf_download(query)
        if path.startswith("/api/open_folder"):
            return self._api_open_folder(query)
        if path.startswith("/api/video/generate"):
            return self._api_video_generate(query)
        if path.startswith("/output/"):
            return self._serve_output(path[len("/output/"):])
        if path.startswith("/generated_pdfs/"):
            return self._serve_generated_pdf(path[len("/generated_pdfs/"):])
        # FIX TAHAP C-2: video dilayani dengan byte-range supaya bisa di-seek.
        if path.startswith("/videos/"):
            return self._serve_video(path[len("/videos/"):])

        return super().do_GET()

    def do_HEAD(self):
        # Pakai routing yang sama - biar monitor/proxy tidak salah menandai 200/404
        return self.do_GET()

    # ------------------------------------------------------------------- APIs
    def _api_data(self):
        if not os.path.exists(DATA_FILE):
            return self._send_error_json(404, "Data file not found")
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().encode("utf-8")
        except OSError as e:
            return self._send_error_json(500, f"Gagal baca data: {_sanitize_error(e)}")
        return self._send_bytes(200, content, "application/json; charset=utf-8")

    def _api_courses(self):
        courses_dir = os.path.join(BASE_DIR, "data", "courses")
        courses_list = []
        if os.path.exists(courses_dir):
            for fname in sorted(os.listdir(courses_dir)):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(courses_dir, fname), "r", encoding="utf-8") as cf:
                            cdata = json.load(cf)
                            courses_list.append({
                                "id": fname[:-5],
                                "nama_mk": cdata.get("course", {}).get("nama_mk", fname[:-5]),
                                "kode_mk": cdata.get("course", {}).get("kode_mk", ""),
                                "sks": cdata.get("course", {}).get("sks", 2),
                                "total_mahasiswa": len(cdata.get("students", []))
                            })
                    except Exception:
                        pass
        return self._send_json(200, courses_list)

    def _api_student(self, path: str):
        if not os.path.exists(DATA_FILE):
            return self._send_error_json(404, "Data file not found")
        npm = path.split("/api/student/")[1].split("?")[0].strip()
        try:
            data = read_json_safe(DATA_FILE)
        except (OSError, json.JSONDecodeError) as e:
            return self._send_error_json(500, f"Data rusak: {_sanitize_error(e)}")
        matched = find_student(data, npm)
        if not matched:
            return self._send_error_json(404, f"Mahasiswa dengan NPM {npm} tidak ditemukan")
        return self._send_json(200, matched)

    def _api_switch_course(self, query):
        target_course = query.get("course", [None])[0]
        if not target_course:
            return self._send_error_json(400, "Parameter 'course' wajib diisi")
        # Jangan izinkan path traversal lewat ?course=
        safe = safe_relative_path(target_course)
        if safe is None or safe != target_course or "/" in safe or "\\" in safe:
            return self._send_error_json(400, "Course ID tidak valid")

        course_file = os.path.join(BASE_DIR, "data", "courses", f"{safe}.json")
        if not os.path.exists(course_file):
            return self._send_error_json(404, f"Course '{safe}' tidak ditemukan di katalog")

        try:
            with open(course_file, "r", encoding="utf-8") as f:
                c_data = json.load(f)

            # -----------------------------------------------------------------
            # FIX TAHAP C-5 - PENJAGA KATALOG (pelajaran mahal).
            #
            # Endpoint ini MENIMPA data master dengan file katalog. Kalau file
            # katalog masih memakai aturan lama (versi lebih rendah), master ikut
            # mundur, dan seluruh dashboard, PDF, serta KPI diam-diam kembali ke
            # angka lama tanpa satu pun pesan error.
            #
            # Ini benar-benar terjadi: katalog mata kuliah aktif tertinggal di
            # versi 2.0 sementara master sudah 2.5. Sekali "ganti mata kuliah",
            # master kembali ke 2.0 (At-Risk 10 -> 1, nilai 80.6 -> 82.5).
            #
            # Aturan penyelamatan:
            #   * Katalog MK yang SEDANG AKTIF (kode_mk sama dengan master)
            #     disalin dari master - lossless, tidak ada isi yang hilang.
            #     Sekaligus membuat "ganti ke MK yang sudah aktif" jadi no-op.
            #   * Katalog MK lain yang ketinggalan versi DITOLAK (fail-closed).
            #     Membangunnya dari template akan menimpa deskripsi, topik RPS,
            #     dan tanggal yang sudah benar dengan isi template yang lebih
            #     pendek/salah. Jadi tidak dilakukan diam-diam di dalam request.
            # -----------------------------------------------------------------
            master_data = None
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    master_data = json.load(f)
            except (OSError, json.JSONDecodeError):
                master_data = None

            if master_data is not None:
                versi_katalog = c_data.get("metadata", {}).get("versi")
                versi_master = master_data.get("metadata", {}).get("versi")
                kode_katalog = str(c_data.get("course", {}).get("kode_mk") or "")
                kode_master = str(master_data.get("course", {}).get("kode_mk") or "")

                # (a) MK ini SEDANG AKTIF -> jangan timpa master sama sekali.
                #     Cukup pastikan katalognya seversi dengan master. Ini juga
                #     membuat "ganti ke MK yang sudah aktif" bebas efek samping
                #     (dulu: menulis ulang master + membuat file backup baru
                #     setiap kali tanpa ada yang berubah).
                if kode_katalog and kode_katalog == kode_master:
                    catatan = "Mata kuliah ini sudah aktif; data master tidak diubah."
                    if versi_tuple(versi_katalog) < versi_tuple(versi_master):
                        with DATA_LOCK:
                            atomic_write_json(course_file, master_data)
                        catatan = (f"Katalog MK aktif masih versi {versi_katalog} dan "
                                   f"telah diselaraskan ke master {versi_master}.")
                        print(f"[SWITCH] {safe}: {catatan}")
                    return self._send_json(200, {
                        "success": True,
                        "active_course": master_data.get("course", {}),
                        "catatan": catatan,
                    })

                # (b) MK lain dengan katalog lebih lama -> TOLAK (fail-closed).
                if versi_tuple(versi_katalog) < versi_tuple(versi_master):
                    return self._send_error_json(
                        409,
                        f"Katalog '{safe}' masih versi {versi_katalog}, sedangkan aturan "
                        f"aktif sudah {versi_master}. Pergantian DIBATALKAN supaya data "
                        f"tidak mundur. Jalankan `process_input.bat` (atau "
                        f"`python scripts\\process_input.py --sync-katalog`) untuk "
                        f"membangun ulang katalog, lalu ulangi.",
                    )

            # Lock + atomic write: tidak ada kemungkinan 2 request corrupt file.
            # Backup dulu supaya "ganti MK" bisa dikembalikan kalau ada yang salah.
            with DATA_LOCK:
                if os.path.exists(DATA_FILE):
                    bak_dir = os.path.join(BASE_DIR, "data", "_backup")
                    os.makedirs(bak_dir, exist_ok=True)
                    stamp = time.strftime("%Y%m%d_%H%M%S")
                    try:
                        shutil.copy2(
                            DATA_FILE,
                            os.path.join(bak_dir, f"academic_data.json.{stamp}.bak"),
                        )
                    except OSError:
                        pass  # backup gagal bukan alasan menolak switch
                atomic_write_json(DATA_FILE, c_data)
        except (OSError, json.JSONDecodeError) as e:
            return self._send_error_json(500, f"Gagal switch course: {_sanitize_error(e)}")

        return self._send_json(200, {"success": True, "active_course": c_data.get("course", {})})

    def _api_deckcraft_html(self, query):
        npm = query.get("npm", [None])[0]
        if npm is None or not NPM_RE.match(str(npm).strip()):
            return self._send_error_json(400, "Parameter NPM tidak valid")
        if not os.path.exists(DATA_FILE):
            return self._send_error_json(404, "Data file not found")
        try:
            data = read_json_safe(DATA_FILE)
        except (OSError, json.JSONDecodeError) as e:
            return self._send_error_json(500, f"Data rusak: {_sanitize_error(e)}")

        matched = find_student(data, npm)
        # TIDAK ada fallback ke students[0] - dulu ini bisa mengirim rapor orang salah
        if not matched:
            return self._send_error_json(404, f"Mahasiswa NPM {npm} tidak ditemukan")

        try:
            if DECKCRAFT_SCRIPTS not in sys.path:
                sys.path.append(DECKCRAFT_SCRIPTS)
            from deckcraft_builder import render_deckcraft_slides_html
            html_content = render_deckcraft_slides_html(matched, data["course"])
        except ImportError:
            return self._send_error_json(
                503, "Modul DeckCraft tidak tersedia. Set env OPENCRAFT_MCP_SCRIPTS."
            )
        except Exception as e:
            return self._send_error_json(500, f"Error rendering DeckCraft: {_sanitize_error(e)}")

        return self._send_bytes(200, html_content.encode("utf-8"), "text/html; charset=utf-8")

    def _api_pdf_download(self, query):
        pdf_type = query.get("type", ["rapor"])[0]
        npm = query.get("npm", [None])[0]
        per_student_types = {"monthly", "presensi", "rapor", "final", "deckcraft", "portofolio"}
        if pdf_type in per_student_types:
            if npm is None or not NPM_RE.match(str(npm).strip()):
                return self._send_error_json(
                    400, f"NPM wajib diisi untuk dokumen '{pdf_type}' (contoh: npm=2510015410010)"
                )
        try:
            from generate_pdfs import generate_pdf_bytes_on_demand
            pdf_bytes, filename = generate_pdf_bytes_on_demand(pdf_type, npm)
        except ValueError as e:
            # Error yang bisa dipahami user (NPM tidak ketemu, tipe tidak dikenal)
            return self._send_error_json(404, _sanitize_error(e))
        except Exception as e:
            return self._send_error_json(500, f"PDF Generation error: {_sanitize_error(e)}")

        if not pdf_bytes:
            return self._send_error_json(500, "Gagal membuat PDF (file kosong)")
        return self._send_bytes(
            200, pdf_bytes, "application/pdf",
            {"Content-Disposition": f'inline; filename="{filename}"'}
        )

    def _api_student_images(self, query):
        npm = query.get("npm", [None])[0]
        if npm is None or not NPM_RE.match(str(npm).strip()):
            return self._send_error_json(400, "Parameter NPM tidak valid")
        try:
            from video_composer import find_student_images
        except ImportError as e:
            return self._send_error_json(503, f"Modul video_composer tidak termuat: {_sanitize_error(e)}")
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            course_name = cdata.get("course", {}).get("nama_mk") or "APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS"
            imgs, folder = find_student_images(npm, course_name)
            img_filenames = [os.path.basename(p) for p in imgs]
            res = {
                "npm": npm,
                "count": len(imgs),
                "filenames": img_filenames,
                # Path relatif terhadap BASE_DIR - jangan bocorkan path absolut ke browser
                "folder": os.path.relpath(folder, BASE_DIR) if folder else "",
                "folder_exists": bool(folder) and os.path.exists(folder)
            }
        except Exception as e:
            return self._send_error_json(500, _sanitize_error(e))
        return self._send_json(200, res)

    def _api_open_folder(self, query):
        import subprocess
        npm = query.get("npm", [None])[0]
        # VALIDASI KETAT sebelum path dipakai - mencegah mkdir di luar proyek
        if npm is None or not NPM_RE.match(str(npm).strip()):
            return self._send_error_json(400, "Parameter NPM tidak valid (harus 8-14 digit)")
        try:
            from video_composer import find_student_images, sanitize_folder_name
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            course_name = cdata.get("course", {}).get("nama_mk") or "APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS"
            imgs, folder = find_student_images(npm, course_name)
            if not folder:
                clean_course = sanitize_folder_name(course_name)
                folder = os.path.join(PROGRESS_ROOT, clean_course, str(npm).strip())
                os.makedirs(folder, exist_ok=True)
            subprocess.Popen(["explorer", folder])
        except Exception as e:
            return self._send_error_json(500, _sanitize_error(e))
        return self._send_json(200, {"success": True, "folder": os.path.relpath(folder, BASE_DIR)})

    def _api_video_generate(self, query):
        npm = query.get("npm", [None])[0]
        if npm is None or not NPM_RE.match(str(npm).strip()):
            return self._send_error_json(400, "Parameter NPM tidak valid (harus 8-14 digit)")
        try:
            from video_composer import generate_video_short_for_student
            res = generate_video_short_for_student(npm)
        except ValueError as e:
            return self._send_error_json(404, _sanitize_error(e))
        except Exception as e:
            return self._send_error_json(500, f"Video generation error: {_sanitize_error(e)}")

        if not res or not res.get("success"):
            return self._send_error_json(
                500, (res or {}).get("error", "Gagal membuat video")
            )
        res["video_url"] = f"/videos/video_portofolio_{res['npm']}.mp4?t={int(time.time())}"
        return self._send_json(200, res)

    def _api_runs(self):
        runs = []
        if os.path.exists(OUTPUT_DIR):
            for course_f in sorted(os.listdir(OUTPUT_DIR)):
                course_p = os.path.join(OUTPUT_DIR, course_f)
                if not os.path.isdir(course_p):
                    continue
                for ts in sorted(os.listdir(course_p), reverse=True):
                    manifest_p = os.path.join(course_p, ts, "manifest.json")
                    if os.path.isfile(manifest_p):
                        try:
                            with open(manifest_p, "r", encoding="utf-8") as mf:
                                runs.append(json.load(mf))
                        except Exception:
                            pass
        latest_p = os.path.join(OUTPUT_DIR, "latest_run.json")
        latest = {}
        if os.path.exists(latest_p):
            try:
                with open(latest_p, "r", encoding="utf-8") as lf:
                    latest = json.load(lf)
            except Exception:
                latest = {}
        return self._send_json(200, {"latest": latest, "runs": runs})

    # ------------------------------------------------------------ static files
    def _serve_output(self, raw_rel: str):
        safe_rel = safe_relative_path(raw_rel.split("?")[0])
        if safe_rel is None:
            return self._send_error_json(403, "Akses ditolak")
        filepath = os.path.join(OUTPUT_DIR, safe_rel)
        if not (os.path.isfile(filepath) and os.path.abspath(filepath).startswith(
                os.path.abspath(OUTPUT_DIR))):
            return self._send_error_json(404, "Output file not found")
        return self._send_file_inline(filepath, os.path.basename(filepath))

    def _serve_generated_pdf(self, raw_name: str):
        safe_name = safe_relative_path(raw_name.split("?")[0])
        if safe_name is None:
            return self._send_error_json(403, "Akses ditolak")
        filepath = os.path.join(GENERATED_PDFS_DIR, safe_name)

        # Fallback ke run terakhir kalau file legacy tidak ada
        if not os.path.exists(filepath):
            latest_p = os.path.join(OUTPUT_DIR, "latest_run.json")
            if os.path.exists(latest_p):
                try:
                    with open(latest_p, "r", encoding="utf-8") as lf:
                        latest_data = json.load(lf)
                    rel_latest = safe_relative_path(
                        latest_data.get("latest_directory", "").strip())
                    if rel_latest:
                        candidate = os.path.join(BASE_DIR, rel_latest, safe_name)
                        if os.path.isfile(candidate):
                            filepath = candidate
                except Exception:
                    pass

        if not (os.path.isfile(filepath) and os.path.abspath(filepath).startswith(
                os.path.abspath(BASE_DIR))):
            return self._send_error_json(404, "PDF file not found")
        return self._send_file_inline(filepath, safe_name)

    def _serve_video(self, raw_name: str):
        """Video portofolio. Mendukung HTTP Range -> bisa di-seek di browser."""
        safe_name = safe_relative_path(raw_name.split("?")[0])
        if safe_name is None:
            return self._send_error_json(403, "Akses ditolak")
        video_dir = os.path.join(PUBLIC_DIR, "videos")
        filepath = os.path.join(video_dir, safe_name)
        if not (os.path.isfile(filepath) and os.path.abspath(filepath).startswith(
                os.path.abspath(video_dir))):
            return self._send_error_json(404, "Video tidak ditemukan")
        return self._send_file_with_range(filepath, os.path.basename(filepath),
                                          inline=False)

    def _send_file_inline(self, filepath: str, filename: str):
        return self._send_file_with_range(filepath, filename, inline=True)

    def _send_file_with_range(self, filepath: str, filename: str,
                              inline: bool = True):
        """Kirim file dengan dukungan HTTP Range (206 Partial Content).

        FIX TAHAP C-2. Sebelumnya seluruh isi file dibaca ke memori (`f.read()`)
        dan tidak ada header Accept-Ranges, sehingga:
          * video 856 KB dibaca penuh ke RAM untuk SETIAP permintaan;
          * browser tidak bisa seek (geser timeline) - harus unduh ulang;
          * permintaan dibatalkan user tetap membaca file sampai habis.
        Sekarang dikirim per potongan 64 KB, dan permintaan yang dibatalkan
        langsung berhenti di potongan berikutnya.
        """
        try:
            size = os.path.getsize(filepath)
        except OSError as e:
            return self._send_error_json(404, f"File tidak ditemukan: {_sanitize_error(e)}")

        ctype = guess_content_type(filepath)
        start, end, status = 0, size - 1, 200

        range_header = self.headers.get("Range")
        if range_header:
            m = RANGE_RE.match(range_header.strip())
            if m and (m.group(1) or m.group(2)):
                g_start, g_end = m.group(1), m.group(2)
                if not g_start:               # bytes=-500 (N byte terakhir)
                    start = max(0, size - int(g_end))
                else:
                    start = int(g_start)
                    end = int(g_end) if g_end else size - 1
                end = min(end, size - 1)

                if start > end or start >= size:
                    # 416: range tidak masuk akal. WAJIB beri tahu klien ukuran
                    # sebenarnya, kalau tidak pemutar video akan macet.
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    self.close_connection = True
                    return
                status = 206

        length = end - start + 1
        try:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(length))
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            if inline and ctype == "application/pdf":
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
            self.end_headers()

            if self.command == "HEAD":
                return

            remaining = length
            with open(filepath, "rb") as f:
                f.seek(start)
                while remaining > 0:
                    chunk = f.read(min(CHUNK_SIZE, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

            if remaining > 0:
                # File berubah ukuran saat dikirim. Klien menunggu byte yang
                # tidak akan pernah datang -> tutup koneksi supaya tidak hang.
                self.close_connection = True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # User menutup tab / membatalkan unduhan - bukan error.
            self.close_connection = True


# =============================================================================
# SERVER
# =============================================================================
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threading MixIn: satu request panjang (render PDF / video 2 menit)
    TIDAK lagi membekukan seluruh dashboard."""
    daemon_threads = True
    allow_reuse_address = True


def port_is_serving(host: str, port: int, timeout: float = 1.0) -> bool:
    """Apakah sudah ada yang MELAYANI di host:port?

    FIX TAHAP C-2. Tidak cukup mengandalkan bind(). Di Windows, SO_REUSEADDR
    (dipasang oleh allow_reuse_address=True) memperbolehkan DUA proses bind ke
    port yang sama TANPA error. Hasilnya bisa ada dua server di :40404 dan
    permintaan terbagi acak antara keduanya - gejalanya menipu: dashboard
    kadang menampilkan data baru, kadang data lama. connect_ex() mendeteksi
    kondisi ini dengan andal.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def run_server():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    # Jangan os.chdir() di process global - tidak perlu, semua path sudah absolut

    if port_is_serving(HOST, PORT):
        print(f"[ERROR] Sudah ada server yang berjalan di http://{HOST}:{PORT}")
        print("        Jalankan stop_server.bat dulu, atau tutup jendela server lama.")
        print("        Server kedua sengaja TIDAK dijalankan agar tidak saling")
        print("        menimpa data dan membuat hasil tidak dapat dipercaya.")
        raise SystemExit(1)

    try:
        httpd = ThreadedHTTPServer((HOST, PORT), KampusIntelligenceHandler)
    except OSError as e:
        if getattr(e, "winerror", None) == 10048 or "address already in use" in str(e).lower():
            print(f"[ERROR] Port {PORT} sedang dipakai. Jalankan stop_server.bat dulu.")
            raise SystemExit(1)
        raise

    print("=" * 65)
    print("[SIAK-KAPRODI] ARSITEKTUR INTELLIGENCE SERVER ACTIVE")
    print(f"[STATUS] Local Server URL: http://localhost:{PORT}  (LOCAL ONLY)")
    print(f"[ROOT] Serving Root: {PUBLIC_DIR}")
    print("[MODE] HTTP/1.1 + byte-range (video bisa di-seek) | aset 100% lokal")
    print("[INFO] Press Ctrl+C or run stop_server.bat to terminate")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server cleanly...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
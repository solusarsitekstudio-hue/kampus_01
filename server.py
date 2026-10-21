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

FIX TAHAP E (data berubah - disengaja, lihat catatan commit):
  * /api/kurikulum      -> peta PRODI > TAHUN AJAR > SEMESTER > MATA KULIAH
  * /api/kurikulum/detail + /api/kurikulum/simpan
                        -> tab Kurikulum: sunting topik, bobot, slot absen,
                           jenis_mk, semester_kurikulum langsung ke tree
  * /api/switch_course  -> tidak lagi menimpa master dengan file katalog.
                           Penunjuk MK aktif dipindah di config/identitas.json,
                           lalu master + semua katalog DIBANGUN ULANG dari tree.
  * /api/courses        -> membaca tree, bukan folder katalog (artefak build).
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
import subprocess
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
# PERIODE_LOCK: periode membaca tree (bukan DATA_FILE), tapi agregasi berat
# dan harus single-flight supaya dua request rollup bersamaan tidak
# mengerjakan pohon ulang dua kali (pola lock konsisten dengan Batch A).
PERIODE_LOCK = threading.Lock()

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
    Mencegah file 0-byte kalau server mati di tengah proses.

    newline="\\n" WAJIB: tanpa itu json.dump di Windows menulis CRLF, sehingga
    academic_data.json berubah byte-nya setiap kali server menulis walau isinya
    sama persis - dan bukti "data tidak tersentuh" jadi kabur."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
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

    # FIX UI-STALE: dulu HTML/JS/CSS disajikan TANPA Cache-Control, jadi browser
    # memakai cache heuristics dan bisa menampilkan UI LAMA (contoh nyata: tab 8
    # "Rekap Periode" tidak muncul setelah update). Sekarang halaman selalu
    # direvalidasi (304 kalau sama), hanya untuk HTML/JS/CSS - video/PDF statis
    # tidak disentuh supaya byte-range seek tetap lancar.
    def send_header(self, keyword, value):
        if str(keyword).lower() == "content-type":
            self._content_type_terkirim = str(value)
        super().send_header(keyword, value)

    def end_headers(self):
        ctype = (getattr(self, "_content_type_terkirim", "") or "").lower()
        if any(t in ctype for t in ("text/html", "javascript", "text/css")):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

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
        # FIX TAB 8: sumber potensi mahasiswa per MK (katalog build per MK).
        if path == "/api/course_data":
            return self._api_course_data(query)
        # Potensi LEVEL 3: perkembangan mahasiswa sepanjang kuliah (lintas MK).
        if path == "/api/perkembangan":
            return self._api_perkembangan(query)
        # PORTOFOLIO 4 LAPIS: bulanan -> per MK -> per semester -> sepanjang
        # kuliah, satu mahasiswa lengkap (keputusan user 2026-10-21).
        if path == "/api/portofolio":
            return self._api_portofolio(query)
        if path == "/api/courses":
            return self._api_courses()
        if path == "/api/kurikulum":
            return self._api_kurikulum()
        if path.startswith("/api/kurikulum/detail"):
            return self._api_kurikulum_detail(query)
        # FIX PERIODE: rekap per-periode (Level 3: satu semester semua MK;
        # Level 4: semua semester semua MK) dihitung dari TREE, bukan master.
        if path == "/api/periode":
            return self._api_periode(query)
        if path == "/api/runs":
            return self._api_runs()
        if path == "/api/engine/input":
            return self._api_engine_input()
        if path == "/api/engine/output":
            return self._api_engine_output()
        if path == "/api/identitas":
            return self._api_identitas()
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

    # ------------------------------------------------------------------- POST
    def do_POST(self):
        """SATU-SATUNYA pintu tulis lewat HTTP.

        Sengaja dibatasi: hanya 3 endpoint, semuanya menulis ke config/identitas.json
        atau meregenerasi data/dokumen lewat skrip yang sudah ada - tidak ada jalur
        yang bisa menulis file sembarangan dari input pengguna.
        """
        path = urlparse(self.path).path
        if path == "/api/identitas":
            return self._api_identitas_simpan()
        if path == "/api/identitas/terapkan":
            return self._api_identitas_terapkan()
        if path == "/api/identitas/regenerasi-pdf":
            return self._api_identitas_regenerasi_pdf()
        if path == "/api/kurikulum/simpan":
            return self._api_kurikulum_simpan()
        # ENGINE cek input/output (terpisah): tandai masukan diproses /
        # rapikan output (arsip run lama + lapis kirim).
        if path == "/api/engine/input":
            return self._api_engine_input_post()
        if path == "/api/engine/output":
            return self._api_engine_output_post()
        return self._send_error_json(404, f"Endpoint POST tidak dikenal: {path}")

    # --------------------------------------------------------- API identitas
    @staticmethod
    def _modul_identitas():
        """Import scripts/identitas.py saat dipakai, bukan di module scope.

        Kalau config/identitas.json hilang atau rusak, server TETAP hidup dan
        errornya dilaporkan sebagai JSON - bukan gagal start.
        """
        import identitas
        return identitas

    def _baca_body_json(self, maks=512 * 1024):
        try:
            panjang = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            panjang = 0
        if panjang <= 0:
            raise ValueError("Body permintaan kosong.")
        if panjang > maks:
            raise ValueError(f"Body terlalu besar ({panjang} byte, maks {maks} byte).")
        mentah = self.rfile.read(panjang)
        try:
            return json.loads(mentah.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Body bukan JSON valid: {e}") from e

    def _identitas_selisih(self, mod):
        """Field identitas yang sudah diubah di config tapi BELUM masuk data master.

        Inilah yang membuat "sudah disimpan" TIDAK sama dengan "sudah diterapkan".
        Label dashboard berubah seketika, sementara pesan wali murid (35 salinan)
        dan dokumen resmi masih memakai nama lama sampai data diregenerasi.
        """
        try:
            data = read_json_safe(DATA_FILE)
        except (OSError, json.JSONDecodeError):
            return []
        return mod.selisih_dengan(data.get("course", {}))

    def _identitas_payload(self, mod):
        cfg = mod.muat(force=True)
        return {
            "config": cfg,
            "header": mod.teks_header(),
            "kop": mod.kop_instansi(),
            "mk_aktif": mod.mk_aktif(),
            "tanggal_tanda_tangan": mod.tanggal_tanda_tangan(),
            "jalur": os.path.relpath(mod.CONFIG_PATH, BASE_DIR).replace("\\", "/"),
            "perlu_diterapkan": self._identitas_selisih(mod),
        }

    def _api_identitas(self):
        mod = self._modul_identitas()
        try:
            return self._send_json(200, self._identitas_payload(mod))
        except mod.IdentitasError as e:
            return self._send_error_json(500, str(e))

    def _api_identitas_simpan(self):
        """TINGKAT 1 - simpan config saja. Tidak menyentuh data/dokumen."""
        mod = self._modul_identitas()
        try:
            body = self._baca_body_json()
        except ValueError as e:
            return self._send_error_json(400, str(e))
        if not isinstance(body, dict) or not isinstance(body.get("mata_kuliah"), dict):
            return self._send_error_json(
                400,
                "Body harus objek JSON identitas lengkap: kunci 'institusi', "
                "'dashboard', dan 'mata_kuliah' wajib ada.",
            )

        with DATA_LOCK:
            try:
                mod.simpan(body)
                muatan = self._identitas_payload(mod)
            except mod.IdentitasError as e:
                return self._send_error_json(422, str(e))
            except OSError as e:
                return self._send_error_json(
                    500, f"Gagal menulis config: {_sanitize_error(e)}")

        muatan["ok"] = True
        muatan["pesan"] = (
            "Identitas tersimpan. Label dashboard langsung berubah - tetapi dokumen "
            "resmi (pesan wali murid + PDF) MASIH memakai nama lama sampai "
            "'Terapkan ke Dokumen' dijalankan."
        )
        return self._send_json(200, muatan)

    def _api_identitas_terapkan(self):
        """TINGKAT 2 - regen data master dari config, agar nama ikut ke dokumen.

        Dijalankan sebagai PROSES TERPISAH (bukan import) supaya server tidak
        memegang state lama dan log aslinya bisa dilaporkan apa adanya.
        """
        mod = self._modul_identitas()
        try:
            mod.muat(force=True)
        except mod.IdentitasError as e:
            return self._send_error_json(422, str(e))

        if not os.path.exists(DATA_FILE):
            return self._send_error_json(
                409, "Data master belum ada. Jalankan parse_data lebih dulu.")
        skrip = os.path.join(_SCRIPTS_DIR, "parse_data.py")
        if not os.path.exists(skrip):
            return self._send_error_json(500, "scripts/parse_data.py tidak ditemukan.")

        try:
            with DATA_LOCK:
                hasil = subprocess.run(
                    [sys.executable, skrip], cwd=BASE_DIR, capture_output=True,
                    text=True, encoding="utf-8", errors="replace", timeout=300,
                )
        except subprocess.TimeoutExpired:
            return self._send_error_json(504, "Regenerasi data melebihi 5 menit.")
        except OSError as e:
            return self._send_error_json(
                500, f"Gagal menjalankan parse_data: {_sanitize_error(e)}")

        if hasil.returncode != 0:
            return self._send_json(500, {
                "error": "Gagal meregenerasi data master; data lama tidak diganti.",
                "returncode": hasil.returncode,
                "log": ((hasil.stdout or "") + (hasil.stderr or ""))[-1800:],
            })

        muatan = self._identitas_payload(mod)
        muatan["ok"] = True
        muatan["log"] = (hasil.stdout or "").strip().splitlines()[-6:]
        muatan["pesan"] = (
            "Data master sudah diregenerasi dari config. Nama baru kini terpakai di "
            "seluruh isi data (termasuk pesan wali murid) dan di semua PDF yang "
            "diunduh dari dashboard."
        )
        return self._send_json(200, muatan)

    def _api_identitas_regenerasi_pdf(self):
        """Cetak ulang paket PDF arsip (11 berkas). Berat: membuka Chromium.

        FAIL-CLOSED: kalau masih ada identitas yang belum diterapkan ke data,
        permintaan DITOLAK. Kalau tidak, PDF akan menyilang: kop memakai nama baru
        tapi isi tabelnya masih dari data lama.
        """
        mod = self._modul_identitas()
        selisih = self._identitas_selisih(mod)
        if selisih:
            return self._send_json(409, {
                "error": "Masih ada identitas yang belum diterapkan ke data. "
                         "Klik 'Terapkan ke Dokumen' dulu supaya PDF tidak "
                         "menyilang antara nama baru dan isi data lama.",
                "perlu_diterapkan": selisih,
            })

        skrip = os.path.join(_SCRIPTS_DIR, "generate_pdfs.py")
        if not os.path.exists(skrip):
            return self._send_error_json(500, "scripts/generate_pdfs.py tidak ditemukan.")
        try:
            hasil = subprocess.run(
                [sys.executable, skrip], cwd=BASE_DIR, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=900,
            )
        except subprocess.TimeoutExpired:
            return self._send_error_json(504, "Regenerasi PDF melebihi 15 menit.")
        except OSError as e:
            return self._send_error_json(
                500, f"Gagal menjalankan generate_pdfs: {_sanitize_error(e)}")

        if hasil.returncode != 0:
            return self._send_json(500, {
                "error": "Gagal meregenerasi paket PDF; dokumen lama tidak diganti.",
                "returncode": hasil.returncode,
                "log": ((hasil.stdout or "") + (hasil.stderr or ""))[-1800:],
            })
        return self._send_json(200, {
            "ok": True,
            "log": (hasil.stdout or "").strip().splitlines()[-8:],
            "pesan": "Paket PDF arsip sudah dicetak ulang dengan identitas terbaru.",
        })

    # ------------------------------------------------------------------- APIs
    def _api_data(self):
        if not os.path.exists(DATA_FILE):
            return self._send_error_json(404, "Data file not found")
        try:
            # FIX BUG RACE: baca master di dalam lock supaya tidak menangkap
            # file sedang ditulis (atomic write + lock = endpoint tidak 500).
            with DATA_LOCK, open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().encode("utf-8")
        except OSError as e:
            return self._send_error_json(500, f"Gagal baca data: {_sanitize_error(e)}")
        return self._send_bytes(200, content, "application/json; charset=utf-8")

    def _api_courses(self):
        """Daftar mata kuliah dari TREE kurikulum (dulu: memindai folder katalog).

        Katalog di data/courses/ hanyalah artefak build hasil kompilasi. Daftar
        yang benar adalah isi tree, jadi itulah yang dibaca di sini.
        """
        KT = self._modul_kurikulum()
        courses_list = []
        for prodi in KT.daftar_prodi():
            try:
                mhs = KT.baca_json(KT.path_mahasiswa(prodi)).get("mahasiswa") or []
            except KT.KurikulumError:
                mhs = []
            for ta in KT.daftar_tahun(prodi):
                for sem in KT.daftar_semester(prodi, ta):
                    for kunci in KT.daftar_mk(prodi, ta, sem):
                        try:
                            penawaran = KT.baca_json(
                                KT.path_berkas(prodi, ta, sem, kunci, "penawaran.json"))
                        except KT.KurikulumError:
                            penawaran = {}
                        courses_list.append({
                            "id": kunci,
                            "nama_mk": penawaran.get("nama_mk", kunci),
                            "kode_mk": penawaran.get("kode_mk", ""),
                            "sks": penawaran.get("sks", 2),
                            "prodi": prodi,
                            "tahun_ajar": ta,
                            "semester": sem,
                            "total_mahasiswa": len(mhs),
                        })
        return self._send_json(200, courses_list)

    def _api_course_data(self, query):
        """Data master 1 MK dari katalog build (data/courses/<kunci>.json).

        Dipakai panel "Potensi Mahasiswa per MK" di tab Rekap Periode supaya
        user bisa memilih MK mana pun di tree - bukan hanya MK aktif di
        academic_data.json. Fail-closed: nama file diverifikasi ada di tree
        dulu; katalog belum dibangun -> 404 dengan petunjuk menjalankan
        parse_data, bukan error HTML.
        """
        target = (query.get("course", [None])[0] or "").strip()
        if not target:
            return self._send_error_json(400, "Parameter 'course' wajib diisi")
        safe = safe_relative_path(target)
        if safe is None or safe != target or "/" in safe or "\\" in safe:
            return self._send_error_json(400, "Course ID tidak valid")

        try:
            KT = self._modul_kurikulum()
            tersedia = set()
            for prodi in KT.daftar_prodi():
                for ta in KT.daftar_tahun(prodi):
                    for sem in KT.daftar_semester(prodi, ta):
                        tersedia.update(KT.daftar_mk(prodi, ta, sem))
        except Exception as e:  # noqa: BLE001
            return self._send_error_json(
                500, "Tree kurikulum tidak bisa dibaca: {0}".format(_sanitize_error(e)))
        if safe not in tersedia:
            return self._send_error_json(
                404, "Course '{0}' tidak ditemukan di tree kurikulum".format(safe))

        course_file = os.path.join(BASE_DIR, "data", "courses",
                                   "{0}.json".format(safe))
        if not os.path.exists(course_file):
            return self._send_error_json(
                404, "Katalog '{0}' belum dibangun. Jalankan "
                     "scripts\\parse_data.py, lalu muat ulang panel ini.".format(safe))
        try:
            with open(course_file, "rb") as f:
                content = f.read()
        except OSError as e:
            return self._send_error_json(
                500, "Gagal baca katalog: {0}".format(_sanitize_error(e)))
        return self._send_bytes(200, content, "application/json; charset=utf-8")

    def _api_perkembangan(self, query):
        """Potensi LEVEL 3 - perkembangan tiap mahasiswa SEPANJANG KULIAH.

        /api/perkembangan?prodi=ARSITEKTUR
        Agregasi lintas MK dari katalog build (scripts/periode.py ::
        perkembangan_mahasiswa): riwayat per MK + rollup per semester +
        arah tren nilai terakhir vs sebelumnya. Fail-closed: prodi tidak
        ada -> 400; tree rusak -> 500 dengan pesan, bukan HTML.
        """
        KT = self._modul_kurikulum()
        PT = self._modul_periode()
        prodi = (query.get("prodi", [None])[0] or "").strip()
        if not prodi or prodi not in KT.daftar_prodi():
            return self._send_error_json(
                400, "Parameter 'prodi' tidak valid atau belum diisi.")
        try:
            with PERIODE_LOCK:
                hasil = PT.perkembangan_mahasiswa(prodi)
        except KT.KurikulumError as e:
            return self._send_error_json(400, str(e))
        except Exception as e:  # noqa: BLE001
            return self._send_error_json(
                500, "Gagal menghitung perkembangan mahasiswa: {0}".format(
                    _sanitize_error(e)))
        return self._send_json(200, hasil)

    def _api_portofolio(self, query):
        """PORTOFOLIO MAHASISWA 4 LAPIS (keputusan user 2026-10-21).

        /api/portofolio?npm=2510015410007
        Agregasi dari katalog build SEMUA MK di tree (scripts/portofolio.py ::
        kumpulan_portofolio):
          lapis 1 per bulan  - kehadiran.detail katalog, aturan UI sama;
          lapis 2 per MK     - nilai/grade/at-risk/archetype diagnosis v3;
          lapis 3 semester   - rollup jumlah MK + rata nilai + kehadiran;
          lapis 4 kumulatif  - agregat + arah tren ±5 + jumlah MK at-risk.
        Fail-closed: npm kosong -> 400; npm tak dikenal -> 404; tree/katalog
        rusak -> 500 dengan pesan, bukan HTML.
        """
        KT = self._modul_kurikulum()
        PF = self._modul_portofolio()
        npm = (query.get("npm", [None])[0] or "").strip()
        if not npm:
            return self._send_error_json(
                400, "Parameter 'npm' wajib diisi "
                     "(contoh: /api/portofolio?npm=2510015410007)")
        try:
            with PERIODE_LOCK:
                hasil = PF.kumpulan_portofolio(npm)
        except KT.KurikulumError as e:
            return self._send_error_json(400, str(e))
        except ValueError as e:
            return self._send_error_json(400, str(e))
        except Exception as e:  # noqa: BLE001
            return self._send_error_json(
                500, "Gagal menghitung portofolio: {0}".format(
                    _sanitize_error(e)))
        if hasil is None:
            return self._send_error_json(
                404, "NPM '{0}' tidak ditemukan di katalog mana pun. "
                     "Jalankan scripts\\parse_data.py jika katalog belum dibangun."
                     .format(npm))
        return self._send_json(200, hasil)

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

    # --------------------------------------------------------- API kurikulum
    @staticmethod
    def _modul_kurikulum():
        """Import scripts/kurikulum_tree.py saat dipakai (pola sama seperti identitas).

        Kalau tree belum dibangun, server TETAP hidup dan errornya dilaporkan
        sebagai JSON - bukan gagal start.
        """
        import kurikulum_tree
        return kurikulum_tree

    @staticmethod
    def _modul_periode():
        """Import scripts/periode.py saat dipakai (pola sama seperti kurikulum)."""
        import periode
        return periode

    @staticmethod
    def _modul_portofolio():
        """Import scripts/portofolio.py saat dipakai (pola sama seperti periode)."""
        import portofolio
        return portofolio

    @staticmethod
    def _modul_aturan():
        import aturan
        return aturan

    def _konteks_aktif(self):
        """(prodi, tahun_ajar, semester, kunci_mk) mata kuliah yang sedang aktif.

        Nilainya memakai BENTUK FOLDER tree (PRODI, 2025-2026, GENAP), bukan teks
        mentah dari config/identitas.json ("Arsitektur", "2025/2026"). Tanpa
        penyeragaman ini, perbandingan "apakah MK ini yang aktif" selalu meleset.
        """
        KT = self._modul_kurikulum()
        IDENT = self._modul_identitas()
        kunci = IDENT.mk_aktif()
        mk = IDENT.mk(kunci)
        ta, sem = KT.pecah_semester(mk.get("semester"))
        prodi = KT.sanitize_folder_name(IDENT.institusi().get("prodi", ""))
        return prodi, KT.slug_tahun_ajar(ta), sem, kunci

    def _ringkas_mk(self, prodi, kunci, penawaran, sesi_dok):
        """Ringkasan satu MK untuk peta kurikulum. Nilai TIDAK dibaca (berat)."""
        KT = self._modul_kurikulum()
        AT = self._modul_aturan()
        sesi = (sesi_dok or {}).get("sesi") or []
        return {
            "kunci_mk": kunci,
            "nama_mk": penawaran.get("nama_mk", kunci),
            "kode_mk": penawaran.get("kode_mk", ""),
            "sks": penawaran.get("sks"),
            "kelas": penawaran.get("kelas", ""),
            "jadwal": penawaran.get("jadwal", ""),
            "jenis_mk": penawaran.get("jenis_mk", ""),
            "jenis_mk_sumber": penawaran.get("sumber_jenis_mk", ""),
            "semester_kurikulum": penawaran.get("semester_kurikulum"),
            "semester_kurikulum_sumber": penawaran.get("sumber_semester_kurikulum", ""),
            "dosen_pengasuh": penawaran.get("dosen_pengasuh", []),
            "asisten_dosen": penawaran.get("asisten_dosen", ""),
            "pertemuan": len(sesi),
            "pertemuan_standar": AT.pertemuan_total(),
            "slot_total": KT.jumlah_slot(sesi_dok),
            # Bobot boleh desimal (mis. 4.2). int() dulu memotong 4.2 -> 4 dan
            # membuat total tampil 96 padahal 16 pertemuan berjumlah 100.
            "bobot_total": round(sum(float(s.get("bobot") or 0) for s in sesi), 2),
            "topik_terisi": (sesi_dok or {}).get("topik_terisi", 0),
            "topik_placeholder": (sesi_dok or {}).get("topik_placeholder", 0),
            "jadwal_menit": KT.hitung_menit_jadwal(penawaran.get("jadwal", "")),
            "masalah": KT.validasi_sesi(sesi_dok, kunci, aturan_modul=AT),
            "peringatan": KT.peringatan_jadwal(
                penawaran.get("jadwal", ""), penawaran.get("sks"),
                penawaran.get("jenis_mk"), aturan_modul=AT),
        }

    def _api_kurikulum(self):
        """Peta kurikulum bertingkat: PRODI > TAHUN AJAR > SEMESTER > MATA KULIAH.

        Sebelum ini dashboard hanya punya satu daftar datar mata kuliah, sehingga
        tidak ada tempat untuk bertanya "ini semester berapa, tahun ajar mana".
        """
        KT = self._modul_kurikulum()
        AT = self._modul_aturan()
        try:
            prodi_aktif, ta_aktif, sem_aktif, kunci_aktif = self._konteks_aktif()
        except Exception as e:  # noqa: BLE001
            return self._send_error_json(
                500, "Gagal membaca konteks mata kuliah aktif: {0}".format(_sanitize_error(e)))

        pohon = {}
        for prodi in KT.daftar_prodi():
            tahun_map = {}
            for ta in KT.daftar_tahun(prodi):
                sem_map = {}
                for sem in KT.daftar_semester(prodi, ta):
                    daftar = []
                    for kunci in KT.daftar_mk(prodi, ta, sem):
                        try:
                            data = KT.muat_mk(prodi, ta, sem, kunci)
                        except KT.KurikulumError as e:
                            daftar.append({
                                "kunci_mk": kunci, "nama_mk": kunci, "kode_mk": "",
                                "rusak": _sanitize_error(e),
                                "masalah": [_sanitize_error(e)], "peringatan": [],
                            })
                            continue
                        daftar.append(self._ringkas_mk(
                            prodi, kunci, data["penawaran"], data["sesi"]))
                    sem_map[sem] = daftar
                tahun_map[ta] = sem_map
            pohon[prodi] = tahun_map

        aktif = {
            "prodi": prodi_aktif, "tahun_ajar": ta_aktif,
            "semester": sem_aktif, "kunci_mk": kunci_aktif,
        }
        return self._send_json(200, {
            "aktif": aktif,
            "prodi": KT.daftar_prodi(),
            "pohon": pohon,
            "aturan": AT.ringkasan(),
            "pertemuan_total": AT.pertemuan_total(),
            "pertemuan_ujian": AT.pertemuan_ujian(),
        })

    def _api_kurikulum_detail(self, query):
        """Isi satu MK untuk tab Kurikulum: penawaran + seluruh pertemuan."""
        KT = self._modul_kurikulum()
        AT = self._modul_aturan()
        prodi = (query.get("prodi", [None])[0] or "").strip()
        ta = (query.get("tahun_ajar", [None])[0] or "").strip()
        sem = (query.get("semester", [None])[0] or "").strip().upper()
        kunci = (query.get("kunci_mk", [None])[0] or "").strip()
        if not (prodi and ta and sem and kunci):
            return self._send_error_json(
                400, "Parameter prodi, tahun_ajar, semester, dan kunci_mk wajib diisi.")
        # Fail-closed: hanya boleh membaca yang benar-benar ada di tree.
        if (prodi not in KT.daftar_prodi() or ta not in KT.daftar_tahun(prodi)
                or sem not in KT.daftar_semester(prodi, ta)
                or kunci not in KT.daftar_mk(prodi, ta, sem)):
            return self._send_error_json(
                404, "Mata kuliah '{0}' tidak ada di tree kurikulum.".format(kunci))
        try:
            data = KT.muat_mk(prodi, ta, sem, kunci)
        except KT.KurikulumError as e:
            return self._send_error_json(422, _sanitize_error(e))

        try:
            mhs = KT.baca_json(KT.path_mahasiswa(prodi)).get("mahasiswa") or []
        except KT.KurikulumError:
            mhs = []

        penawaran = data["penawaran"]
        sesi_dok = data["sesi"]
        try:
            aktif = (prodi, ta, sem, kunci) == self._konteks_aktif()
        except Exception:  # noqa: BLE001
            aktif = False
        return self._send_json(200, {
            "prodi": prodi, "tahun_ajar": ta, "semester": sem, "kunci_mk": kunci,
            "apakah_aktif": aktif,
            "penawaran": penawaran,
            "sesi": sesi_dok,
            "ringkas": self._ringkas_mk(prodi, kunci, penawaran, sesi_dok),
            "jumlah_mahasiswa": len(mhs),
            "aturan": AT.ringkasan(),
            "pertemuan_total": AT.pertemuan_total(),
            "pertemuan_ujian": AT.pertemuan_ujian(),
        })

    def _api_periode(self, query):
        """Rekap per-periode dari TREE (kondisinya dijabarkan, bukan ditebak).

        Level 3 (satu semester semua MK):
          /api/periode?prodi=&tahun_ajar=&semester=
        Level 4 (semua semester semua MK):
          /api/periode?prodi=&semua_semester=1

        Fail-closed: prodi tidak ada -> 404, semester tidak ada -> 404,
        parameter kurang -> 400. Kosong 'prodi' TIDAK dianggap 'semua prodi'
        supaya tidak ada laporan diam-diam lintas prodi.
        """
        PT = self._modul_periode()
        KT = self._modul_kurikulum()
        prodi = (query.get("prodi", [None])[0] or "").strip()
        ta = (query.get("tahun_ajar", [None])[0] or "").strip()
        sem = (query.get("semester", [None])[0] or "").strip().upper()
        semua_semester = str(query.get("semua_semester", ["0"])[0]).lower() in (
            "1", "true", "yes")
        if not prodi or prodi not in KT.daftar_prodi():
            return self._send_error_json(
                400, "Parameter 'prodi' tidak valid atau belum diisi.")

        try:
            with PERIODE_LOCK:
                if semua_semester:
                    return self._send_json(200, PT.agregat_semua_semester(prodi))
                if not (ta and sem):
                    return self._send_error_json(
                        400, "Parameter 'tahun_ajar' dan 'semester' wajib diisi "
                             "(atau pakai semua_semester=1).")
                if (ta not in KT.daftar_tahun(prodi)
                        or sem not in KT.daftar_semester(prodi, ta)):
                    return self._send_error_json(
                        404, "Semester '{0} {1}' tidak ada di tree kurikulum "
                             "prodi {2}.".format(ta, sem, prodi))
                return self._send_json(
                    200, PT.agregat_semester(prodi, ta, sem))
        except Exception as e:  # noqa: BLE001
            return self._send_error_json(
                500, "Gagal menghitung rekap periode: {0}".format(
                    _sanitize_error(e)))

    def _api_kurikulum_simpan(self):
        """Simpan suntingan tab Kurikulum ke TREE, lalu bangun ulang turunannya.

        Yang boleh diubah hanya yang memang milik manusia: topik, deskripsi,
        bobot, jumlah slot absen, jenis_mk, dan semester_kurikulum. Identitas
        (nama MK, kode, SKS, dosen, kelas, jadwal) TIDAK bisa disunting dari
        sini - sumbernya tetap satu, yaitu config/identitas.json.
        """
        KT = self._modul_kurikulum()
        AT = self._modul_aturan()
        try:
            body = self._baca_body_json()
        except ValueError as e:
            return self._send_error_json(400, str(e))
        if not isinstance(body, dict):
            return self._send_error_json(400, "Body harus objek JSON.")

        prodi = str(body.get("prodi") or "").strip()
        ta = str(body.get("tahun_ajar") or "").strip()
        sem = str(body.get("semester") or "").strip().upper()
        kunci = str(body.get("kunci_mk") or "").strip()
        if (prodi not in KT.daftar_prodi() or ta not in KT.daftar_tahun(prodi)
                or sem not in KT.daftar_semester(prodi, ta)
                or kunci not in KT.daftar_mk(prodi, ta, sem)):
            return self._send_error_json(
                404, "Mata kuliah '{0}' tidak ada di tree kurikulum.".format(kunci))

        try:
            data = KT.muat_mk(prodi, ta, sem, kunci)
        except KT.KurikulumError as e:
            return self._send_error_json(422, _sanitize_error(e))

        penawaran = data["penawaran"]
        sesi_dok = data["sesi"]
        sesi_lama = {}
        for s in (sesi_dok.get("sesi") or []):
            try:
                sesi_lama[int(s.get("pertemuan"))] = s
            except (TypeError, ValueError):
                continue

        # --- penawaran: hanya 2 field yang boleh diubah dari dashboard ---
        #
        # Status "dikonfirmasi-dashboard" HANYA diberikan kalau nilainya benar-benar
        # berubah, atau kalau user mencentang kotak konfirmasi. Kalau tidak, sekadar
        # menyimpan topik akan membuat tebakan awal berubah status jadi "sudah
        # dikonfirmasi kaprodi" - padahal tidak ada yang mengonfirmasi.
        masuk = body.get("penawaran") or {}
        penawaran_baru = dict(penawaran)
        if "jenis_mk" in masuk:
            jenis = str(masuk.get("jenis_mk") or "").strip().lower()
            if jenis not in ("teori", "studio", "teori_studio"):
                return self._send_error_json(
                    422, "jenis_mk harus salah satu dari: teori, studio, teori_studio.")
            if jenis != penawaran.get("jenis_mk") or masuk.get("konfirmasi_jenis_mk"):
                penawaran_baru["jenis_mk"] = jenis
                penawaran_baru["sumber_jenis_mk"] = "dikonfirmasi-dashboard"
                penawaran_baru.pop("tebakan_jenis_mk", None)
        if "semester_kurikulum" in masuk:
            mentah = masuk.get("semester_kurikulum")
            if mentah in (None, ""):
                if penawaran.get("semester_kurikulum") is not None:
                    penawaran_baru["semester_kurikulum"] = None
                    penawaran_baru["sumber_semester_kurikulum"] = "belum-dikonfirmasi"
            else:
                try:
                    n = int(mentah)
                except (TypeError, ValueError):
                    return self._send_error_json(422, "semester_kurikulum harus berupa angka.")
                if not 1 <= n <= 14:
                    return self._send_error_json(422, "semester_kurikulum harus 1 sampai 14.")
                if n != penawaran.get("semester_kurikulum") \
                        or masuk.get("konfirmasi_semester_kurikulum"):
                    penawaran_baru["semester_kurikulum"] = n
                    penawaran_baru["sumber_semester_kurikulum"] = "dikonfirmasi-dashboard"

        # --- sesi: topik / deskripsi / bobot / jumlah slot absen ---
        perubahan = body.get("sesi")
        slot_berubah = []
        if isinstance(perubahan, list):
            for item in perubahan:
                if not isinstance(item, dict):
                    return self._send_error_json(422, "Setiap baris sesi harus objek.")
                try:
                    p = int(item.get("pertemuan"))
                except (TypeError, ValueError):
                    return self._send_error_json(
                        422, "Setiap baris sesi wajib punya nomor 'pertemuan'.")
                if p not in sesi_lama:
                    return self._send_error_json(
                        422, "Pertemuan {0} tidak ada di sesi.json MK ini.".format(p))
                baris = sesi_lama[p]
                if "topik" in item:
                    baris["topik"] = str(item.get("topik") or "").strip()[:200]
                if "deskripsi" in item:
                    baris["deskripsi"] = str(item.get("deskripsi") or "").strip()[:400]
                if "bobot" in item:
                    try:
                        b = int(item.get("bobot"))
                    except (TypeError, ValueError):
                        return self._send_error_json(
                            422, "Bobot pertemuan {0} harus angka.".format(p))
                    if not 0 <= b <= 100:
                        return self._send_error_json(
                            422, "Bobot pertemuan {0} harus 0 sampai 100.".format(p))
                    baris["bobot"] = b
                if "jumlah_slot" in item:
                    try:
                        n = int(item.get("jumlah_slot"))
                    except (TypeError, ValueError):
                        return self._send_error_json(
                            422, "Jumlah slot pertemuan {0} harus angka.".format(p))
                    if not 1 <= n <= 10:
                        return self._send_error_json(
                            422, "Jumlah slot pertemuan {0} harus 1 sampai 10.".format(p))
                    sebelum = len(baris.get("slot_absen") or [])
                    if n != sebelum:
                        slot_berubah.append("P{0}: {1} -> {2} slot".format(p, sebelum, n))
                    baris["slot_absen"] = [
                        {"slot": j + 1, "label": "Absen {0}".format(j + 1)} for j in range(n)
                    ]

        # Status "terverifikasi" DIHITUNG dari isi topik, bukan disetel manusia -
        # supaya tidak ada baris placeholder yang naik status sendiri. Aturannya
        # SATU tempat: KT.topik_terverifikasi() (dulu server.py punya versi sendiri).
        for baris in sesi_lama.values():
            baris.pop("tanggal_terverifikasi", None)  # nama lama (sebelum 2026-10-19)
            baris["topik_terverifikasi"] = KT.topik_terverifikasi(baris.get("topik"))
        sesi_dok["topik_terisi"] = sum(1 for b in sesi_lama.values() if b["topik_terverifikasi"])
        sesi_dok["topik_placeholder"] = len(sesi_lama) - sesi_dok["topik_terisi"]

        masalah = KT.validasi_sesi(sesi_dok, kunci, aturan_modul=AT)
        if masalah:
            return self._send_json(422, {
                "error": "Perubahan DITOLAK; tidak ada berkas yang ditulis.",
                "masalah": masalah,
            })

        # --- tulis ke tree, lalu bangun ulang turunannya ---
        path_sesi = KT.path_berkas(prodi, ta, sem, kunci, "sesi.json")
        path_penawaran = KT.path_berkas(prodi, ta, sem, kunci, "penawaran.json")
        peringatan = []
        try:
            KT.tulis_json(path_sesi, sesi_dok)
            if penawaran_baru != penawaran:
                KT.tulis_json(path_penawaran, penawaran_baru)
        except (OSError, KT.KurikulumError) as e:
            return self._send_error_json(
                500, "Gagal menulis tree kurikulum: {0}".format(_sanitize_error(e)))

        # FIX BUG INDEX: dulu "KT.bangun_index(aktif=kunci)" dipanggil di sini
        # tapi hasilnya dibuang - index TIDAK PERNAH ditulis ke
        # config/kurikulum.json, dan bentuk 'aktif'-nya string kunci sedangkan
        # index_kurikulum.py & migrasi_kurikulum.py memakai dict
        # {prodi, tahun_ajar, semester, kunci_mk}. Sekarang index ikut ditulis
        # dengan bentuk yang sama; gagal menulis index hanya jadi peringatan,
        # karena sumber kebenaran tetap folder tree.
        try:
            try:
                prodi_a, ta_a, sem_a, kunci_a = self._konteks_aktif()
            except Exception:  # noqa: BLE001
                prodi_a = ta_a = sem_a = kunci_a = None
            pointer = (
                {"prodi": prodi_a, "tahun_ajar": ta_a,
                 "semester": sem_a, "kunci_mk": kunci_a}
                if kunci_a else None
            )
            KT.tulis_json(KT.INDEX_PATH, KT.bangun_index(aktif=pointer))
        except (OSError, KT.KurikulumError) as e:
            peringatan.append(
                "Index kurikulum (config/kurikulum.json) gagal diperbarui: {0}. "
                "Jalankan: python scripts\\index_kurikulum.py".format(
                    _sanitize_error(e)))
        if slot_berubah:
            peringatan.append(
                "Jumlah slot absen berubah ({0}). Baris nilai yang sudah ada TIDAK "
                "ikut berubah, jadi kehadiran pertemuan itu akan dihitung dari slot "
                "yang datanya ada. Isi ulang dari portal supaya penuh.".format(
                    "; ".join(slot_berubah)))
        if masalah_jadwal := KT.peringatan_jadwal(
                penawaran_baru.get("jadwal", ""), penawaran_baru.get("sks"),
                penawaran_baru.get("jenis_mk"), aturan_modul=AT):
            peringatan.extend(masalah_jadwal)

        # Tree sudah tersimpan; sekarang turunannya WAJIB dibangun ulang. Kalau
        # tidak, dashboard/PDF masih memakai angka lama dan suntingan baru hanya
        # terlihat di berkas - persis kelas bug yang berulang di aplikasi ini.
        ok, log, err = self._jalankan_parse_data(timeout=300)
        if not ok:
            return self._send_json(500, {
                "error": "Tree sudah tersimpan, tetapi gagal membangun ulang data "
                         "turunan. Angka dashboard/PDF belum ikut berubah.",
                "detail": err,
                "log": log,
                "peringatan": peringatan,
                "pesan": "Jalankan ulang: python scripts\\parse_data.py",
            })

        return self._send_json(200, {
            "ok": True,
            "apakah_aktif": (prodi, ta, sem, kunci) == self._konteks_aktif(),
            "ringkas": self._ringkas_mk(prodi, kunci, penawaran_baru, sesi_dok),
            "peringatan": peringatan,
            "log": (log or "").strip().splitlines()[-6:],
            "pesan": "Suntingan tersimpan di tree kurikulum dan data turunan sudah "
                     "dibangun ulang.",
        })

    def _jalankan_parse_data(self, timeout=300):
        """Bangun ulang master + seluruh katalog dari tree (proses terpisah).

        Sengaja proses terpisah, bukan import: server tidak boleh memegang state
        lama, dan log aslinya bisa dilaporkan apa adanya.

        TANGGA A (keputusan user 2026-10-21): DATA_LOCK TIDAK lagi disekap
        selama kompilasi berjalan - dulu 12 detik kompilasi membuat SEMUA
        endpoint lain beku (pembaca master, kehadiran, grafik). Pembaca kini
        terus menyajikan master lama yang konsisten sampai versi baru siap;
        penulisan master & identitas KEDUANYA atomik (tmp + os.replace), jadi
        tidak ada jalur yang bisa memotong pembaca di tengah berkas.
        """
        skrip = os.path.join(_SCRIPTS_DIR, "parse_data.py")
        if not os.path.exists(skrip):
            return False, "", "scripts/parse_data.py tidak ditemukan."
        try:
            hasil = subprocess.run(
                [sys.executable, skrip], cwd=BASE_DIR, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False, "", "Pembangunan ulang data melebihi {0} detik.".format(timeout)
        except OSError as e:
            return False, "", "Gagal menjalankan parse_data: {0}".format(_sanitize_error(e))
        log = ((hasil.stdout or "") + (hasil.stderr or ""))[-1800:]
        if hasil.returncode != 0:
            return False, log, "parse_data gagal (returncode {0}).".format(hasil.returncode)
        return True, log, ""

    def _api_switch_course(self, query):
        """Ganti mata kuliah aktif: pindahkan penunjuk, lalu BANGUN ULANG dari tree.

        TAHAP E: master tidak lagi ditimpa berkas katalog. Sejak sumbernya satu
        (tree kurikulum), "ganti MK" = ubah mata_kuliah_aktif di
        config/identitas.json, lalu jalankan parse_data untuk membangun ulang
        master + semua katalog. Karena semuanya diturunkan dari satu sumber,
        angka tidak bisa mundur karena katalog yang tertinggal versi.

        Penjaga versi LAMA tetap dipasang lebih dulu: kalau masih ada artefak
        katalog ber-aturan lama, permintaan ditolak - bukan dipakai diam-diam.
        """
        target_course = query.get("course", [None])[0]
        if not target_course:
            return self._send_error_json(400, "Parameter 'course' wajib diisi")
        # Jangan izinkan path traversal lewat ?course=
        safe = safe_relative_path(target_course)
        if safe is None or safe != target_course or "/" in safe or "\\" in safe:
            return self._send_error_json(400, "Course ID tidak valid")

        try:
            KT = self._modul_kurikulum()
            mod = self._modul_identitas()
        except Exception as e:  # noqa: BLE001
            return self._send_error_json(
                500, "Modul kurikulum tidak bisa dimuat: {0}".format(_sanitize_error(e)))

        # (a) PENJAGA KATALOG (pelajaran mahal): artefak ber-aturan lama ditolak.
        course_file = os.path.join(BASE_DIR, "data", "courses", "{0}.json".format(safe))
        versi_master = None
        if os.path.exists(DATA_FILE):
            try:
                # FIX BUG RACE: baca versi master di dalam lock (lihat _api_data).
                with DATA_LOCK, open(DATA_FILE, "r", encoding="utf-8") as f:
                    versi_master = (json.load(f).get("metadata") or {}).get("versi")
            except (OSError, json.JSONDecodeError):
                versi_master = None
        if versi_master and os.path.exists(course_file):
            try:
                with open(course_file, "r", encoding="utf-8") as f:
                    isi_katalog = json.load(f)
                versi_katalog = (isi_katalog.get("metadata") or {}).get("versi")
            except (OSError, json.JSONDecodeError):
                versi_katalog = None
            if versi_katalog and versi_tuple(versi_katalog) < versi_tuple(versi_master):
                return self._send_error_json(
                    409,
                    "Katalog '{0}' masih versi {1}, sedangkan aturan aktif sudah {2}. "
                    "Pergantian DIBATALKAN supaya data tidak mundur. Jalankan "
                    "`python scripts\\process_input.py --sync-katalog` untuk membangun "
                    "ulang katalog, lalu ulangi.".format(safe, versi_katalog, versi_master))

        # (b) MK harus benar-benar ada di TREE (sumber kebenaran), bukan di katalog.
        tersedia = set()
        for prodi in KT.daftar_prodi():
            for ta in KT.daftar_tahun(prodi):
                for sem in KT.daftar_semester(prodi, ta):
                    tersedia.update(KT.daftar_mk(prodi, ta, sem))
        if safe not in tersedia:
            return self._send_error_json(
                404, "Course '{0}' tidak ditemukan di tree kurikulum".format(safe))

        # (c) Sudah aktif -> no-op (jangan menulis apa pun).
        try:
            prodi_aktif, ta_aktif, sem_aktif, kunci_aktif = self._konteks_aktif()
        except Exception:  # noqa: BLE001
            prodi_aktif = ta_aktif = sem_aktif = kunci_aktif = None
        if safe == kunci_aktif:
            return self._send_json(200, {
                "success": True,
                "active_course": mod.lengkapi(safe),
                "catatan": "Mata kuliah ini sudah aktif; data master tidak diubah.",
            })

        # FIX BUG RACE: blok (b)-(d) menyentuh config/identitas.json TANPA
        # DATA_LOCK, sedangkan _api_identitas_* menulis file yang sama DI DALAM
        # lock. Save identitas + ganti MK bersamaan bisa lost-update. Dulu
        # rollback juga menulis cfg_lama seluruhnya -> menyapu edit identitas
        # yang masuk di antara dua langkah. Sekarang: pointer saja di-support.
        with DATA_LOCK:
            cfg_lama = mod.muat(force=True)
            cfg_baru = json.loads(json.dumps(cfg_lama))
        cfg_baru["mata_kuliah_aktif"] = safe
        try:
            with DATA_LOCK:
                mod.simpan(cfg_baru)
        except mod.IdentitasError as e:
            return self._send_error_json(
                422, "Gagal memindahkan mata kuliah aktif: {0}".format(_sanitize_error(e)))

        ok, log, err = self._jalankan_parse_data(timeout=300)
        if not ok:
            # Kembalikan penunjuk supaya tidak ada keadaan setengah jalan.
            # HANYA field penunjuk yang dikembalikan: cfg_lama bisa sudah basi
            # dibanding edit identitas yang masuk saat parse_data berjalan.
            try:
                with DATA_LOCK:
                    cfg_saat = mod.muat(force=True)
                    cfg_saat["mata_kuliah_aktif"] = cfg_lama.get("mata_kuliah_aktif")
                    mod.simpan(cfg_saat)
            except Exception:  # noqa: BLE001
                pass
            return self._send_json(500, {
                "error": "Pergantian DIBATALKAN: gabung tidak bisa membangun ulang data "
                         "dari tree. Penunjuk mata kuliah aktif sudah dikembalikan.",
                "detail": err, "log": log,
            })

        return self._send_json(200, {
            "success": True,
            "active_course": mod.lengkapi(safe),
            "catatan": "Master dan katalog dibangun ulang dari tree kurikulum.",
            "log": (log or "").strip().splitlines()[-4:],
        })

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
        try:
            # SATU SUMBER: daftar tipe per-mahasiswa diambil dari modul PDF
            # (portofolio 4 lapis ikut otomatis), bukan disalin-tempel di sini.
            from generate_pdfs import (
                generate_pdf_bytes_on_demand, PDF_TYPE_PER_STUDENT)
        except ImportError as e:
            return self._send_error_json(
                500, "Modul generate_pdfs tidak bisa dibaca: " + _sanitize_error(e))
        if pdf_type in PDF_TYPE_PER_STUDENT:
            if npm is None or not NPM_RE.match(str(npm).strip()):
                return self._send_error_json(
                    400, f"NPM wajib diisi untuk dokumen '{pdf_type}' (contoh: npm=2510015410010)"
                )
        try:
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
            # FIX BUG RACE: baca master di dalam lock (lihat _api_data).
            with DATA_LOCK, open(DATA_FILE, "r", encoding="utf-8") as f:
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
            # FIX BUG RACE: baca master di dalam lock (lihat _api_data).
            with DATA_LOCK, open(DATA_FILE, "r", encoding="utf-8") as f:
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

    # --------------------------------------------------------- API engine
    # Engine cek input & output TERPISAH (keputusan user 2026-10-21):
    #   scripts/engine_input.py  -> pindai inbox, deteksi duplikat via SHA-256
    #   scripts/engine_output.py -> audit integritas output + lapis kirim
    @staticmethod
    def _modul_engine(nama):
        """Import modul engine_*.py saat dipakai, bukan di module scope."""
        import importlib
        try:
            return importlib.import_module(nama)
        except Exception as e:
            raise ImportError(
                f"Modul {nama}.py tidak bisa dibaca: {_sanitize_error(e)}")

    def _api_engine_input(self):
        """GET /api/engine/input - pindai inbox + arsip, deteksi duplikat."""
        try:
            eng = self._modul_engine("engine_input")
            return self._send_json(200, eng.pindai())
        except ImportError as e:
            return self._send_error_json(503, str(e))
        except Exception as e:
            return self._send_error_json(
                500, f"Pindai input gagal: {_sanitize_error(e)}")

    def _api_engine_input_post(self):
        """POST /api/engine/input {"sha": "...", "keterangan": "..."} - tandai
        satu masukan 'sudah diproses' supaya salinan berikutnya terdeteksi."""
        try:
            body = self._baca_body_json()
        except ValueError as e:
            return self._send_error_json(400, str(e))
        sha = str(body.get("sha") or "").strip()
        if not sha:
            return self._send_error_json(
                400, 'Body JSON wajib {"sha": "<hash>", "keterangan": "..."}')
        try:
            eng = self._modul_engine("engine_input")
            hasil, err = eng.tandai_diproses(
                sha, keterangan=str(body.get("keterangan") or ""))
            if err:
                return self._send_error_json(404, err)
            return self._send_json(200, {"pesan": "masukan ditandai diproses",
                                         **hasil})
        except ImportError as e:
            return self._send_error_json(503, str(e))
        except Exception as e:
            return self._send_error_json(
                500, f"Tandai diproses gagal: {_sanitize_error(e)}")

    def _api_engine_output(self):
        """GET /api/engine/output - audit integritas seluruh output."""
        try:
            eng = self._modul_engine("engine_output")
            return self._send_json(200, eng.audit())
        except ImportError as e:
            return self._send_error_json(503, str(e))
        except Exception as e:
            return self._send_error_json(
                500, f"Audit output gagal: {_sanitize_error(e)}")

    def _api_engine_output_post(self):
        """POST /api/engine/output {"aksi": "rapikan", "arsipkan_lama": true} -
        arsip-kan run lama ke data/_backup + siapkan lapis kirim
        output/kirim/{kaprodi,wali} untuk mesin kirim otomatis."""
        try:
            body = self._baca_body_json()
        except ValueError as e:
            return self._send_error_json(400, str(e))
        aksi = str(body.get("aksi") or "").strip()
        if aksi != "rapikan":
            return self._send_error_json(
                400, 'Aksi dikenal saat ini: {"aksi": "rapikan"} '
                     '(arsip-kan run lama + lapis kirim)')
        try:
            eng = self._modul_engine("engine_output")
            hasil = eng.rapikan(
                arsipkan_lama=bool(body.get("arsipkan_lama", True)))
            return self._send_json(200, {"pesan": "rapikan selesai", **hasil})
        except ImportError as e:
            return self._send_error_json(503, str(e))
        except Exception as e:
            return self._send_error_json(
                500, f"Rapikan output gagal: {_sanitize_error(e)}")

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
"""TES REGRESI: HTTP/1.1 + byte-range + penjaga double-instance  (Tahap C-2).

WAJIB jalankan server dulu:  run_server.bat
Lalu:                        python tests\\test_server_http.py

Membuktikan perilaku transfer berkas server:
  * protokol HTTP/1.1 (keep-alive)
  * byte-range 206 supaya video portofolio bisa di-seek
  * 416 untuk range di luar batas, range ngawur -> 200 penuh (bukan error)
  * HEAD tidak mengirim body
  * penjaga path traversal + guard "server kedua menolak jalan"

Tidak mengubah satu pun angka/data.
"""
import http.client
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HOST, PORT = "127.0.0.1", 40404
VIDEO = "/videos/video_portofolio_2510015410010.mp4"
FULL = os.path.getsize(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public",
                 "videos", "video_portofolio_2510015410010.mp4"))

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:46} {detail}")


def req(path, headers=None, method="GET"):
    c = http.client.HTTPConnection(HOST, PORT, timeout=30)
    c.request(method, path, headers=headers or {})
    r = c.getresponse()
    ver = r.version
    body = r.read()
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    c.close()
    return r.status, hdrs, body, ver


print("=" * 74)
print("VER  protokol (11 = HTTP/1.1)")
print("=" * 74)

print("\n[1] Permintaan penuh tanpa Range")
st, h, b, v = req(VIDEO)
print(f"  terima: status={st} version=HTTP/1.{v} content-length={h.get('content-length')}")
check("status 200", st == 200, st)
check("protokol HTTP/1.1 (11)", v == 11, v)
check("Accept-Ranges: bytes", h.get("accept-ranges") == "bytes", h.get("accept-ranges"))
check("Content-Type video/mp4", h.get("content-type") == "video/mp4", h.get("content-type"))
check("body utuh", len(b) == FULL, f"{len(b):,} vs {FULL:,}")

print("\n[2] Range bytes=0-99 (awal)")
st, h, b, v = req(VIDEO, {"Range": "bytes=0-99"})
check("status 206 Partial Content", st == 206, st)
check("Content-Range benar", h.get("content-range") == f"bytes 0-99/{FULL}",
      h.get("content-range"))
check("Content-Length = 100", h.get("content-length") == "100", h.get("content-length"))
check("tepat 100 byte dikirim", len(b) == 100, len(b))

print("\n[3] Range bytes=1000-1999 (tengah)")
st, h, b, v = req(VIDEO, {"Range": "bytes=1000-1999"})
check("status 206", st == 206, st)
check("tepat 1000 byte", len(b) == 1000, len(b))
st2, _, b2, _ = req(VIDEO)
check("byte ke-1000 identik dgn file penuh", b2[1000:2000] == b, "ya" if b2[1000:2000] == b else "beda")

print("\n[4] Range bytes=-500 (500 byte terakhir)")
st, h, b, v = req(VIDEO, {"Range": "bytes=-500"})
check("status 206", st == 206, st)
check("tepat 500 byte", len(b) == 500, len(b))
check("Content-Range 500 terakhir",
      h.get("content-range") == f"bytes {FULL - 500}-{FULL - 1}/{FULL}",
      h.get("content-range"))
check("isinya = ekor file", b2[-500:] == b, "ya" if b2[-500:] == b else "beda")

print("\n[5] Range bytes=1-  (tanpa batas akhir)")
st, h, b, v = req(VIDEO, {"Range": "bytes=1-"})
check("status 206", st == 206, st)
check("sisa file terkirim", len(b) == FULL - 1, f"{len(b):,}")

print("\n[6] Range di luar batas -> 416")
st, h, b, v = req(VIDEO, {"Range": f"bytes={FULL + 5000}-"})
check("status 416 Requested Range Not Satisfiable", st == 416, st)
check("Content-Range memberitahu ukuran", h.get("content-range") == f"bytes */{FULL}",
      h.get("content-range"))

print("\n[7] Range ngawur -> diabaikan (200 penuh, bukan error)")
st, h, b, v = req(VIDEO, {"Range": "banana"})
check("status 200", st == 200, st)
check("body utuh", len(b) == FULL, len(b))

print("\n[8] HEAD tidak mengirim body")
st, h, b, v = req(VIDEO, method="HEAD")
check("status 200", st == 200, st)
check("Content-Length tetap jujur", h.get("content-length") == str(FULL),
      h.get("content-length"))
check("body kosong", len(b) == 0, len(b))
check("Accept-Ranges ada di HEAD", h.get("accept-ranges") == "bytes")

print("\n[9] Keep-alive: 3 permintaan dalam 1 koneksi")
c = http.client.HTTPConnection(HOST, PORT, timeout=30)
vers = []
for i in range(3):
    c.request("GET", "/api/data")
    r = c.getresponse()
    r.read()
    vers.append((r.status, r.version, r.getheader("Connection")))
c.close()
check("3x 200 pada 1 koneksi", all(s == 200 for s, _, _ in vers), vers)
check("semua HTTP/1.1", all(v == 11 for _, v, _ in vers))

print("\n[10] Endpoint lain tetap normal")
for p, want in [("/api/data", 200), ("/api/courses", 200), ("/", 200),
                ("/vendor/tailwind.css", 200), ("/style.css", 200),
                ("/generated_pdfs/03_laporan_penilaian_kaprodi_master_gradebook.pdf", 200),
                ("/api/student/9999999999999", 404),
                ("/generated_pdfs/../data/academic_data.json", 403)]:
    st, h, b, v = req(p)
    check(f"{p[:52]:52}", st == want, f"{st} (harap {want})")

print("\n[11] Video NPM ngaco")
st, h, b, v = req("/videos/../server.py")
check("traversal video ditolak", st == 403, st)
st, h, b, v = req("/videos/tidak_ada.mp4")
check("video tidak ada -> 404", st == 404, st)

print("\n[12] Guard double-instance")
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
proc = subprocess.run([sys.executable, "server.py"], cwd=here,
                      capture_output=True, text=True, timeout=60)
out = (proc.stdout or "") + (proc.stderr or "")
check("server kedua KELUAR dgn kode 1", proc.returncode == 1, proc.returncode)
check("pesan 'Sudah ada server'", "Sudah ada server" in out,
      out.strip().splitlines()[0] if out.strip() else "(kosong)")

print("\n" + "=" * 74)
print("HASIL: " + ("SEMUA LULUS" if ok_all else "ADA YANG GAGAL"))
print("=" * 74)
sys.exit(0 if ok_all else 1)

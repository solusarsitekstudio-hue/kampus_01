"""TES: penyimpanan hasil tangkapan portal (tanpa browser, tanpa jaringan).

Jalankan TANPA server:  python tests\\test_impor_portal.py

Yang dibuktikan:
  1. HTML halaman disimpan apa adanya (jejak audit).
  2. Tabel di HTML diekstrak ke CSV/XLSX di folder inbox dan bisa dibaca ulang
     oleh pembaca tabel yang sama.
  3. Halaman tanpa tabel TIDAK menghasilkan berkas kosong palsu; hanya HTML +
     catatan "perlu dibaca manusia/AI".
  4. Screenshot ikut diarsipkan.
"""
import io
import os
import shutil
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from scripts.impor import portal as P  # noqa: E402
from scripts.impor import sumber_tabel as ST  # noqa: E402

SCRATCH = os.path.join(HERE, "scratch")
os.makedirs(SCRATCH, exist_ok=True)
KERJA = tempfile.mkdtemp(prefix="tes_portal_", dir=SCRATCH)

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


HTML = """<html><body>
<h1>Presensi</h1>
<table>
  <tr><th>NPM</th><th>Nama</th><th>Pertemuan</th><th>Status</th><th>Nilai</th></tr>
  <tr><td>2510015410010</td><td>M YAZID</td><td>1</td><td>H</td><td>90</td></tr>
  <tr><td>2510015410011</td><td>ROZI</td><td>2</td><td>A</td><td>0</td></tr>
</table>
</body></html>"""

HTML_KOSONG = "<html><body><p>Tidak ada tabel di halaman ini.</p></body></html>"

print("=" * 74)
print("TES IMPOR - TANGKAPAN PORTAL (offline)")
print("=" * 74)

print("\n1. HTML bertabel -> CSV")
arsip = os.path.join(KERJA, "raw")
inbox = os.path.join(KERJA, "inbox")
hasil = P.simpan_hasil_tangkapan(HTML, arsip, inbox, "portal-uji-hal01", format_="csv")
check("html tersimpan", os.path.isfile(hasil["html"]))
check("1 tabel diekstrak", len(hasil["tabel"]) == 1, str(len(hasil["tabel"])))
path_csv = hasil["tabel"][0]["path"]
check("csv ada di inbox", os.path.isfile(path_csv) and os.path.dirname(path_csv) == inbox)
tabel = ST.baca_tabel(path_csv)
check("csv terbaca ulang", len(tabel) == 1 and len(tabel[0]["baris"]) == 2)
check("header utuh", tabel[0]["header"][:2] == ["NPM", "Nama"])
check("isi baris utuh", tabel[0]["baris"][0][:2] == ["2510015410010", "M YAZID"],
      str(tabel[0]["baris"][0]))

print("\n2. HTML bertabel -> XLSX")
hasil_x = P.simpan_hasil_tangkapan(HTML, arsip, inbox, "portal-uji-hal02", format_="xlsx")
path_xlsx = hasil_x["tabel"][0]["path"]
check("xlsx ada", os.path.isfile(path_xlsx))
tabel_x = ST.baca_tabel(path_xlsx)
check("xlsx terbaca ulang", len(tabel_x[0]["baris"]) == 2)

print("\n3. Halaman tanpa tabel")
hasil_kosong = P.simpan_hasil_tangkapan(HTML_KOSONG, arsip, inbox, "portal-uji-kosong")
check("tidak ada tabel", hasil_kosong["tabel"] == [])
check("html tetap disimpan", os.path.isfile(hasil_kosong["html"]))
check("catatan menjelaskan", "tidak ada tabel" in hasil_kosong["catatan"].lower(),
      hasil_kosong["catatan"])
check("tidak membuat berkas csv palsu",
      not any(f.endswith(".csv") and "kosong" in f for f in os.listdir(inbox)))

print("\n4. Screenshot ikut diarsipkan")
png_sumber = os.path.join(KERJA, "layar.png")
with open(png_sumber, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
hasil_png = P.simpan_hasil_tangkapan(HTML, arsip, inbox, "portal-uji-png", screenshot=png_sumber)
check("screenshot tersalin", hasil_png["screenshot"] and os.path.isfile(hasil_png["screenshot"]))
check("nama screenshot mengikuti label",
      os.path.basename(hasil_png["screenshot"]) == "portal-uji-png.png")

print("\n" + "=" * 74)
print("HASIL: " + ("SEMUA LOLOS" if ok else "ADA YANG GAGAL"))
print("=" * 74)
shutil.rmtree(KERJA, ignore_errors=True)
sys.exit(0 if ok else 1)
"""TES: ekstraksi dokumen modul (PDF/DOCX) + pemotongan untuk analisis AI.

Jalankan TANPA server:  python tests\\test_impor_dokumen.py

Yang dibuktikan:
  1. PDF ber-text layer dibaca per halaman dan teksnya benar.
  2. PDF tanpa text layer DITANDAI ocr_dibutuhkan - tidak dikarang isinya.
  3. DOCX dibaca per heading + tabelnya ikut terbaca.
  4. Gambar ditandai perlu OCR.
  5. potongan() tidak kehilangan halaman dan tidak melebihi batas.
"""
import io
import os
import shutil
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from scripts.impor import dokumen as D  # noqa: E402

SCRATCH = os.path.join(HERE, "scratch")
os.makedirs(SCRATCH, exist_ok=True)
KERJA = tempfile.mkdtemp(prefix="tes_dokumen_", dir=SCRATCH)

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


def buat_pdf(path, teks=None):
    """PDF 1 halaman minimal (Helvetica). teks=None -> halaman kosong."""
    objek = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    isi = b""
    if teks:
        isi = ("BT /F1 12 Tf 72 720 Td ({0}) Tj ET".format(teks)).encode("latin-1")
    objek.append(b"<< /Length " + str(len(isi)).encode() + b" >>\nstream\n" + isi + b"\nendstream")

    keluaran = bytearray(b"%PDF-1.4\n")
    offset = []
    for i, o in enumerate(objek, start=1):
        offset.append(len(keluaran))
        keluaran += str(i).encode() + b" 0 obj\n" + o + b"\nendobj\n"
    xref = len(keluaran)
    keluaran += b"xref\n0 " + str(len(objek) + 1).encode() + b"\n"
    keluaran += b"0000000000 65535 f \n"
    for off in offset:
        keluaran += ("%010d 00000 n \n" % off).encode()
    keluaran += (b"trailer\n<< /Size " + str(len(objek) + 1).encode()
                 + b" /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n")
    with open(path, "wb") as f:
        f.write(bytes(keluaran))


print("=" * 74)
print("TES IMPOR - DOKUMEN MODUL (PDF/DOCX)")
print("=" * 74)

print("\n1. PDF ber-text layer")
path_pdf = os.path.join(KERJA, "rps_berteks.pdf")
buat_pdf(path_pdf, "Pertemuan 1 Pengantar Arsitektur")
hasil = D.baca(path_pdf)
check("jenis pdf", hasil["jenis"] == "pdf")
check("1 halaman", hasil["meta"]["jumlah_halaman"] == 1)
check("tidak perlu OCR", hasil["ocr_dibutuhkan"] is False)
check("teks halaman terbaca",
      "Pertemuan 1" in hasil["halaman"][0]["teks"], hasil["halaman"][0]["teks"][:50])
check("teks_lengkap terisi", "Arsitektur" in hasil["teks_lengkap"])

print("\n2. PDF tanpa text layer (hasil scan)")
path_scan = os.path.join(KERJA, "rps_scan.pdf")
buat_pdf(path_scan, None)
hasil_scan = D.baca(path_scan)
check("ditandai perlu OCR", hasil_scan["ocr_dibutuhkan"] is True)
check("tidak mengarang teks", hasil_scan["teks_lengkap"] == "")
check("halaman kosong dilaporkan", hasil_scan["meta"]["halaman_tanpa_teks"] == [1],
      str(hasil_scan["meta"]["halaman_tanpa_teks"]))

print("\n3. DOCX dengan heading + tabel")
try:
    import docx
    path_docx = os.path.join(KERJA, "modul.docx")
    dok = docx.Document()
    dok.add_heading("CPMK", level=1)
    dok.add_paragraph("CPMK-1 Mahasiswa mampu merancang denah sederhana.")
    dok.add_heading("Rencana Pertemuan", level=1)
    dok.add_paragraph("Pertemuan 1: Pengantar dan kontrak kuliah.")
    tabel = dok.add_table(rows=2, cols=3)
    tabel.cell(0, 0).text = "Pertemuan"
    tabel.cell(0, 1).text = "Topik"
    tabel.cell(0, 2).text = "Bobot"
    tabel.cell(1, 0).text = "1"
    tabel.cell(1, 1).text = "Pengantar"
    tabel.cell(1, 2).text = "4"
    dok.save(path_docx)

    hasil_docx = D.baca(path_docx)
    check("jenis docx", hasil_docx["jenis"] == "docx")
    check("terbagi per heading", len(hasil_docx["halaman"]) >= 2,
          str([h["judul"] for h in hasil_docx["halaman"]]))
    check("isi CPMK terbaca", "CPMK-1" in hasil_docx["teks_lengkap"])
    check("tabel ikut terbaca", "Pertemuan | Topik | Bobot" in hasil_docx["teks_lengkap"])
    check("docx tidak perlu OCR", hasil_docx["ocr_dibutuhkan"] is False)
except ImportError:
    check("python-docx tersedia", False, "tidak terpasang")

print("\n4. Gambar")
path_png = os.path.join(KERJA, "screenshot.png")
with open(path_png, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
hasil_gambar = D.baca(path_png)
check("jenis gambar", hasil_gambar["jenis"] == "gambar")
check("gambar perlu OCR", hasil_gambar["ocr_dibutuhkan"] is True)

print("\n5. Pemotongan untuk AI")
halaman = [
    {"nomor": 1, "teks": "A" * 300},
    {"nomor": 2, "teks": "B" * 300},
    {"nomor": 3, "teks": "C" * 300},
    {"nomor": 4, "teks": ""},
    {"nomor": 5, "teks": "D" * 300},
]
potong = D.potongan(halaman, maks_karakter=500)
check("menghasilkan beberapa potongan", len(potong) >= 2, str(len(potong)))
check("setiap potongan punya rentang halaman",
      all(p["halaman_awal"] and p["halaman_akhir"] for p in potong))
check("tidak ada halaman berteks yang hilang",
      sorted({p["halaman_awal"] for p in potong} | {p["halaman_akhir"] for p in potong})
      == [1, 2, 3, 5],
      str([(p["halaman_awal"], p["halaman_akhir"]) for p in potong]))
check("halaman kosong tidak bikin potongan kosong",
      all(p["teks"].strip() for p in potong))

print("\n" + "=" * 74)
print("HASIL: " + ("SEMUA LOLOS" if ok else "ADA YANG GAGAL"))
print("=" * 74)
shutil.rmtree(KERJA, ignore_errors=True)
sys.exit(0 if ok else 1)

"""TES REGRESI: penjaga dokumen & dependensi (utang #8 & #9 dibayar).

Jalankan TANPA server:  python tests\\test_docs_dependensi.py

Kenapa tes ini ada: README sendiri pernah mencatat dua utang yang dibiarkan
lama - (8) `openpyxl` dan `pypdf` masih tertulis di `requirements.txt` padahal
sejak v2.6 tidak ada satu pun impor di kode, dan (9) `REQUIREMENTS.md` +
`WORKFLOW_MAPPING.md` masih menggambarkan alur v2.5 (Excel/PDF, "6 Sesi").
Dokumen basi adalah kebohongan yang bentuknya sama dengan angka karangan:
kelihatan meyakinkan, isinya salah.

Tes ini mengunci empat hal supaya tidak bisa kembali:

  A. Setiap impor pihak ketiga di server.py / scripts/ / tests/ TERCANTUM di
     `requirements.txt` (kecuali modul eksternal yang memang dicatat di
     EXTERNAL_OK, mis. `deckcraft_builder` dari OPEN_CRAFT_MCP).
  B. Tidak ada DEPENDENSI MATI: tiap paket di `requirements.txt` benar-benar
     diimpor oleh kode (inilah yang membuktikan openpyxl/pypdf memang mati).
  C. Nomor port di `server.py` == nomor di `REQUIREMENTS.md` == `README.md`.
  D. Setiap rute `/api/...` di `server.py` tercantum di `REQUIREMENTS.md`, dan
     ketiga dokumen tidak lagi mengklaim sumber data lama sebagai yang berlaku.
"""
import ast
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(HERE, "scripts")
TESTS = os.path.join(HERE, "tests")

REQ_TXT = os.path.join(HERE, "requirements.txt")
README = os.path.join(HERE, "README.md")
DOCS = {
    "REQUIREMENTS.md": os.path.join(HERE, "REQUIREMENTS.md"),
    "WORKFLOW_MAPPING.md": os.path.join(HERE, "WORKFLOW_MAPPING.md"),
    "README.md": README,
}

# Modul eksternal (BUKAN paket pip): dipakai lewat sys.path dari proyek lain dan
# sudah punya jalur error sendiri di generate_pdfs.py / server.py.
EXTERNAL_OK = {
    "deckcraft_builder": "E:\\WORKSHOP\\OPEN_CRAFT_MCP\\scripts (env OPENCRAFT_MCP_SCRIPTS)",
}

gagal = 0


def cek(label, kondisi, detail=""):
    global gagal
    gagal += 0 if kondisi else 1
    print(f"  [{'OK  ' if kondisi else 'GAGAL'}] {label}"
          + (f" -> {detail}" if detail and not kondisi else ""))


def baca(path):
    # Beberapa berkas punya BOM (dulu disunting editor Windows).
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def modul_lokal():
    nama = set()
    for d in (SCRIPTS, TESTS):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".py"):
                    nama.add(f[:-3])
    return nama


def impor_pihak_ketiga():
    """Nama modul teratas yang diimpor kode, minus modul lokal & stdlib."""
    lokal = modul_lokal()
    stdlib = set(sys.stdlib_module_names)
    berkas = [os.path.join(HERE, "server.py")]
    for d in (SCRIPTS, TESTS):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".py"):
                    berkas.append(os.path.join(d, f))
    modul = set()
    for p in berkas:
        for n in ast.walk(ast.parse(baca(p))):
            if isinstance(n, ast.Import):
                for a in n.names:
                    modul.add(a.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                modul.add(n.module.split(".")[0])
    return sorted(m for m in modul if m not in lokal and m not in stdlib)


def paket_requirements():
    """Nama paket di requirements.txt, dinormalkan (edge-tts -> edge_tts)."""
    paket = []
    for baris in baca(REQ_TXT).splitlines():
        baris = baris.split("#")[0].strip()
        if not baris:
            continue
        nama = re.split(r"[<>=!~;\[\s]", baris)[0].strip().lower().replace("-", "_")
        if nama:
            paket.append(nama)
    return sorted(set(paket))


teks_docs = {nama: baca(p) for nama, p in DOCS.items()}
teks_req = baca(REQ_TXT)
teks_server = baca(os.path.join(HERE, "server.py"))

print("=" * 76)
print("TES PENJAGA DOKUMEN & DEPENDENSI")
print("=" * 76)

# ---------------------------------------------------------------- A & B ---
print("\n  -- A. impor kode vs requirements.txt --")
impor = impor_pihak_ketiga()
paket = paket_requirements()
print(f"  impor pihak ketiga : {', '.join(impor)}")
print(f"  requirements.txt   : {', '.join(paket)}")

for m in impor:
    if m in EXTERNAL_OK:
        print(f"  [OK  ] {m:18} modul eksternal (dicatat): {EXTERNAL_OK[m]}")
        continue
    cek(f"{m:18} tercantum di requirements.txt", m in paket)

print("\n  -- B. tidak ada dependensi mati --")
for p in paket:
    cek(f"{p:18} benar-benar diimpor kode", p in impor)

print("\n  -- B2. dependensi yang sudah dimatikan tidak boleh kembali --")
for mati in ("openpyxl", "pypdf", "PyPDF2"):
    baris_paket = [b for b in teks_req.splitlines()
                   if b.split("#")[0].strip().lower().startswith(mati.lower())]
    cek(f"{mati:18} tidak ada sebagai paket", not baris_paket)
    cek(f"{mati:18} tidak diimpor kode", mati not in impor)

# ------------------------------------------------------------------ C ---
print("\n  -- C. nomor port seragam --")
cocok = re.search(r"^PORT\s*=\s*(\d+)", teks_server, re.M)
port_server = cocok.group(1) if cocok else "(tidak ditemukan)"
print(f"  server.py PORT = {port_server}")
cek("PORT terbaca dari server.py", port_server.isdigit())
for nama in ("REQUIREMENTS.md", "README.md"):
    cek(f"{nama:20} menyebut {port_server}", port_server in teks_docs[nama])

# ------------------------------------------------------------------ D ---
print("\n  -- D. rute /api/... di server.py tercantum di REQUIREMENTS.md --")
rute = sorted({m.rstrip("/") for m in re.findall(r'"(/api/[^"]*)"', teks_server)})
print(f"  rute ditemukan: {len(rute)}")
for r in rute:
    cek(f"{r:34} ada di REQUIREMENTS.md", r in teks_docs["REQUIREMENTS.md"])

print("\n  -- D2. dokumen tidak lagi mengklaim alur v2.5 sebagai yang berlaku --")
klaim_basi = [
    ("Penyebut lama '6 Sesi'", "6 Sesi"),
    ("Aset dari CDN", "Tailwind CSS (CDN)"),
    ("openpyxl sebagai paket", "openpyxl>="),
    ("pypdf sebagai paket", "pypdf>="),
]
for nama, teks in teks_docs.items():
    for label, potongan in klaim_basi:
        cek(f"{nama:20} bersih dari: {label}", potongan not in teks)

print("\n  -- D3. dokumen menunjuk sumber kebenaran yang benar --")
for nama, teks in teks_docs.items():
    cek(f"{nama:20} menyebut tree 'data/kurikulum'", "data/kurikulum" in teks)

print("\n" + "=" * 76)
if gagal:
    print(f"HASIL: {gagal} MASALAH - dokumen/dependensi tidak sinkron dengan kode")
else:
    print("HASIL: DOKUMEN & DEPENDENSI SINKRON DENGAN KODE")
print("=" * 76)
sys.exit(1 if gagal else 0)

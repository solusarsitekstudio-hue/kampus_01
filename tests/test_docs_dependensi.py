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
     EXTERNAL_OK, mis. `deckcraft_builder` dari OPEN_CRAFT_MCP dan
     `gemini_rotary_engine` milik engine Gemini rotary).
  B. Tidak ada DEPENDENSI MATI: tiap paket di `requirements.txt` benar-benar
     diimpor oleh kode.
  B2. Paket yang dulu dimatikan tidak boleh kembali sembarangan: `PyPDF2`
     dilarang selamanya; `openpyxl`/`pypdf`/`python-docx` HANYA boleh diimpor
     dari `scripts/impor/` (subsistem impor), bukan dari server/core.
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
# sudah punya jalur error sendiri di generate_pdfs.py / server.py / impor.
EXTERNAL_OK = {
    "deckcraft_builder": "E:\\WORKSHOP\\OPEN_CRAFT_MCP\\scripts (env OPENCRAFT_MCP_SCRIPTS)",
    "gemini_rotary_engine": "E:\\WORKSHOP\\CORE_SYSTEM_ENGINE (env EOS_GEMINI_ENGINE)",
}

IMPOR_DIR = os.path.join(SCRIPTS, "impor")

# Impor pihak ketiga yang HANYA boleh hidup di subsistem impor, beserta nama
# paket pip-nya (nama impor != nama paket untuk python-docx).
PAKET_KHUSUS_IMPOR = {
    "openpyxl": "openpyxl",
    "pypdf": "pypdf",
    "docx": "python_docx",
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


def berkas_py():
    """Semua .py yang diaudit: server.py + scripts/ + tests/ (REKURSIF)."""
    hasil = [os.path.join(HERE, "server.py")]
    for base in (SCRIPTS, TESTS):
        if not os.path.isdir(base):
            continue
        for akar, _dirs, files in os.walk(base):
            for f in sorted(files):
                if f.endswith(".py"):
                    hasil.append(os.path.join(akar, f))
    return hasil


def nama_relatif(path):
    return os.path.relpath(path, HERE).replace("\\", "/")


def modul_lokal():
    """Modul yang bukan pihak ketiga: nama berkas + nama paket lokal."""
    nama = {"scripts", "impor"}  # paket yang kita buat sendiri
    for base in (SCRIPTS, TESTS):
        if not os.path.isdir(base):
            continue
        for akar, dirs, files in os.walk(base):
            for f in files:
                if f.endswith(".py"):
                    nama.add(f[:-3])
            for d in dirs:
                if os.path.isfile(os.path.join(akar, d, "__init__.py")):
                    nama.add(d)
    return nama


def impor_pihak_ketiga():
    """dict: nama modul teratas -> daftar berkas yang mengimpornya.

    Modul lokal & stdlib dibuang. Nama paket dipakai apa adanya (mis. impor
    `docx` tetap `docx`); penerjemahan ke nama pip ada di PAKET_KHUSUS_IMPOR.
    """
    lokal = modul_lokal()
    stdlib = set(sys.stdlib_module_names)
    modul = {}
    for p in berkas_py():
        for n in ast.walk(ast.parse(baca(p))):
            if isinstance(n, ast.Import):
                for a in n.names:
                    modul.setdefault(a.name.split(".")[0], set()).add(nama_relatif(p))
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                modul.setdefault(n.module.split(".")[0], set()).add(nama_relatif(p))
    return {m: sorted(v) for m, v in modul.items() if m not in lokal and m not in stdlib}


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
print(f"  impor pihak ketiga : {', '.join(sorted(impor))}")
print(f"  requirements.txt   : {', '.join(paket)}")


def nama_paket(impor_nama):
    """Nama pip untuk satu nama impor (docx -> python_docx)."""
    return PAKET_KHUSUS_IMPOR.get(impor_nama, impor_nama)


def boleh_sensitif(berkas):
    """Paket khusus impor boleh diimpor dari subsistem impor & tesnya saja."""
    return berkas.startswith("scripts/impor/") or berkas.startswith("tests/test_impor_")


for m in sorted(impor):
    if m in EXTERNAL_OK:
        print(f"  [OK  ] {m:18} modul eksternal (dicatat): {EXTERNAL_OK[m]}")
        continue
    if m in PAKET_KHUSUS_IMPOR:
        cek(f"{m:18} hanya di scripts/impor/ + tesnya",
            all(boleh_sensitif(f) for f in impor[m]),
            ", ".join(impor[m]))
        cek(f"{m:18} tercantum di requirements.txt", PAKET_KHUSUS_IMPOR[m] in paket)
        continue
    cek(f"{m:18} tercantum di requirements.txt", m in paket)

print("\n  -- B. tidak ada dependensi mati --")


def dipakai(p):
    return p in impor or any(nama_paket(m) == p for m in impor)


for p in paket:
    cek(f"{p:18} benar-benar diimpor kode", dipakai(p))

print("\n  -- B2. paket sensitif hanya hidup di subsistem impor --")
for mati in ("PyPDF2",):
    baris_paket = [b for b in teks_req.splitlines()
                   if b.split("#")[0].strip().lower().startswith(mati.lower())]
    cek(f"{mati:18} tidak ada sebagai paket", not baris_paket)
    cek(f"{mati:18} tidak diimpor kode", mati not in impor)

for m, p in PAKET_KHUSUS_IMPOR.items():
    lokasi = impor.get(m, [])
    cek(f"{m:18} hanya di scripts/impor/ + tesnya",
        all(boleh_sensitif(f) for f in lokasi),
        ", ".join(lokasi) or "(tidak diimpor)")
    cek(f"{p:18} tercantum di requirements.txt", p in paket)

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

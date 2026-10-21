"""TES: skema baris kanonik subsistem impor (fail-closed, bukan menebak).

Jalankan TANPA server:  python tests\\test_impor_kanonik.py

Yang dibuktikan:
  1. Status portal (H/A/HS/S/I, 'hadir sebagian') dinormalkan ke kosakata resmi.
  2. Alpha wajib skor 0 - tidak ada nilai gratis untuk ketidakhadiran.
  3. NPM dari Excel (float) tetap string digit; NPM pecahan ditolak.
  4. Pertemuan/slot/skor di luar rentang DITOLAK dengan pesan yang menyebut kolom.
  5. NPM yang tidak ada di mahasiswa.json ditolak.
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from scripts.impor import kanonik as K  # noqa: E402

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


def tolak(label, fn, potongan_pesan=""):
    try:
        fn()
    except ValueError as exc:
        lolos = potongan_pesan.lower() in str(exc).lower() if potongan_pesan else True
        check(label, lolos, str(exc)[:90])
        return
    check(label, False, "tidak melempar ValueError")


print("=" * 74)
print("TES IMPOR - SKEMA KANONIK")
print("=" * 74)

print("\n1. Normalisasi status")
for masukan, harap in (
    ("Hadir", "Hadir"), ("H", "Hadir"), ("hadir", "Hadir"),
    ("Hadir Sebagian", "Hadir Sebagian"), ("HS", "Hadir Sebagian"),
    ("sebagian", "Hadir Sebagian"), ("S", "Sakit"), ("sakit", "Sakit"),
    ("I", "Izin"), ("ijin", "Izin"), ("A", "Alpha"), ("alpa", "Alpha"),
    ("tanpa keterangan", "Alpha"),
):
    check(f"status {masukan!r} -> {harap}", K.normalisasi_status(masukan) == harap)
tolak("status 'libur' tidak dikenal", lambda: K.normalisasi_status("libur"), "tidak dikenal")
tolak("status kosong ditolak", lambda: K.normalisasi_status(""), "kosong")

print("\n2. NPM & angka")
check("NPM float Excel -> string digit",
      K.normalisasi_npm(2510015410010.0) == "2510015410010")
check("NPM string berspasi -> bersih", K.normalisasi_npm(" 2510015410010 ") == "2510015410010")
tolak("NPM pecahan ditolak", lambda: K.normalisasi_npm(123.45), "pecahan")
tolak("NPM bukan angka ditolak", lambda: K.normalisasi_npm("ABC123"), "bukan angka")
check("skor '95' -> 95", K.normalisasi_skor("95") == 95)
check("skor '95,0' -> 95", K.normalisasi_skor("95,0") == 95)
tolak("skor 101 ditolak", lambda: K.normalisasi_skor(101), "0..100")
tolak("Alpha dengan skor 80 ditolak",
      lambda: K.normalisasi_skor(80, "Alpha"), "wajib skor 0")

print("\n3. Baris kanonik")
baris = K.baris_kanonik({
    "npm": "2510015410010", "pertemuan": "3", "slot": "1",
    "status": "H", "skor": "92", "alasan": "  hadir  tepat waktu ",
})
check("bentuk keluaran lengkap",
      set(baris) == {"npm", "pertemuan", "slot", "status", "alasan", "skor"})
check("pertemuan jadi int", baris["pertemuan"] == 3)
check("status jadi 'Hadir'", baris["status"] == "Hadir")
check("alasan dirapikan", baris["alasan"] == "hadir tepat waktu")
check("alasan kosong -> '-'", K.baris_kanonik({
    "npm": "2510015410010", "pertemuan": 1, "slot": 1,
    "status": "Sakit", "skor": 78,
})["alasan"] == "-")

print("\n4. Validasi terhadap tree")
mahasiswa = {"2510015410010"}
slot_map = {1: 2, 2: 2, 3: 1}
valid = {"npm": "2510015410010", "pertemuan": 1, "slot": 2,
         "status": "Hadir", "alasan": "-", "skor": 90}
check("baris valid tidak punya masalah",
      K.validasi_baris(valid, mahasiswa=mahasiswa, slot_map=slot_map) == [])

kasus = [
    ("pertemuan 17 ditolak",
     {**valid, "pertemuan": 17}, "pertemuan"),
    ("slot 3 padahal pertemuan 3 hanya 1 slot",
     {**valid, "pertemuan": 3, "slot": 2}, "hanya punya 1 slot"),
    ("npm asing ditolak",
     {**valid, "npm": "9999999999999"}, "tidak ada di mahasiswa.json"),
    ("status tidak resmi ditolak",
     {**valid, "status": "Bolos"}, "tidak resmi"),
    ("skor 120 ditolak",
     {**valid, "skor": 120}, "0..100"),
    ("Alpha skor 70 ditolak",
     {**valid, "status": "Alpha", "skor": 70}, "wajib skor 0"),
]
for label, data, pesan in kasus:
    masalah = K.validasi_baris(data, mahasiswa=mahasiswa, slot_map=slot_map)
    gabung = " | ".join(masalah)
    check(label, bool(masalah) and pesan.lower() in gabung.lower(), gabung[:90])

print("\n" + "=" * 74)
print("HASIL: " + ("SEMUA LOLOS" if ok else "ADA YANG GAGAL"))
print("=" * 74)
sys.exit(0 if ok else 1)

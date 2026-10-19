"""TES REGRESI: angka di README harus sama dengan angka di data.

Jalankan TANPA server:  python tests\\test_readme_accuracy.py

Kenapa tes ini ada: README pernah memuat angka yang diketik manual dan salah
("Tingkat Kelulusan 71.4% (25 lulus)", "Site Architect 87.0%", "Grade A 91.8"
untuk mahasiswa yang sebenarnya 91.7). Angka karangan di dokumen resmi adalah
persis hal yang paling merusak kepercayaan pada sistem ini.

Tes ini menurunkan setiap klaim dari data/academic_data.json, lalu memastikan
klaim itu benar-benar tertulis di README.md. Kalau angkanya tidak cocok, tes
GAGAL - jadi README tidak bisa lagi diam-diam berbohong.

Sejak v2.6 klaim "porsi kehadiran" memakai satuan PERTEMUAN + SLOT (bukan
penyebut 6 yang lama), dan tes ikut mengunci bahwa angka-angka salah versi lama
("6 Sesi Praktikum", benchmark 83.3%, keselarasan 96.0%, grafik P1-P6) tidak
boleh muncul lagi.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(HERE, "README.md")
DATA = os.path.join(HERE, "data", "academic_data.json")

with open(README, "r", encoding="utf-8") as f:
    teks = f.read()
with open(DATA, "r", encoding="utf-8") as f:
    d = json.load(f)

cs = d["class_summary"]
dist = cs["distribusi_grade"]


def mhs(npm):
    return next(s for s in d["students"] if s["npm"] == npm)


def karir(s, kunci):
    for c in s["ai_diagnosis"]["matriks_karier_10"]:
        if kunci in c["profesi"]:
            return c["kecocokan_persen"]
    raise LookupError(f"profesi '{kunci}' tidak ada untuk {s['nama']}")


YAZID, ROZI, ALSA = mhs("2510015410010"), mhs("2510015410011"), mhs("2510015410001")
modus = cs["grade_modus"]
pct_lulus = round(cs["total_lulus"] / cs["total_mahasiswa"] * 100, 1)

klaim = [
    ("Total mahasiswa",            f"| Total Mahasiswa | {cs['total_mahasiswa']} |"),
    ("Rata-rata kehadiran",        f"| Rata-rata Kehadiran | {cs['rata_kehadiran']}%"),
    ("Rata-rata nilai studio",     f"**{cs['rata_nilai_studio']}**"),
    ("Predikat dominan + jumlah",  f"predikat dominan {modus}, {dist[modus]} mahasiswa"),
    ("Jumlah at-risk",             f"| Mahasiswa At-Risk | **{cs['total_at_risk']}**"),
    ("Distribusi grade",           f"A={dist['A']}, A-={dist['A-']}, B+={dist['B+']}, B={dist['B']}, C={dist['C']}, D={dist['D']}"),
    ("Tingkat kelulusan",          f"{pct_lulus}% ({cs['total_lulus']} dari {cs['total_mahasiswa']}"),
    ("Versi master",               f"`{d['metadata']['versi']}`"),
    ("Standar pertemuan",          f"satu semester = **{d['metadata']['pertemuan_total']} pertemuan**"),
    ("Yazid kehadiran",            f"Kehadiran {int(YAZID['kehadiran']['persentase'])}%"),
    ("Yazid nilai + grade",        f"Grade {YAZID['akademik']['grade']} ({YAZID['akademik']['nilai_rata_rata']})"),
    ("Yazid indeks kesiapan",      f"Indeks Kesiapan {YAZID['akademik']['indeks_kesiapan']}%"),
    ("Rozi kehadiran + porsi",     f"Kehadiran {ROZI['kehadiran']['persentase']}% "
                                   f"(**{ROZI['kehadiran']['hadir']} pertemuan penuh + "
                                   f"{ROZI['kehadiran']['hadir_sebagian']} pertemuan hadir sebagian**, "
                                   f"{ROZI['kehadiran']['slot_hadir']}/{ROZI['kehadiran']['slot_total']} slot)"),
    ("Rozi jumlah alpha",          f"{ROZI['kehadiran']['alpha']}x Alpha"),
    ("Rozi jumlah sakit",          f"{ROZI['kehadiran']['sakit']}x Sakit"),
    ("Rozi grade + nilai",         f"Grade {ROZI['akademik']['grade']} ({ROZI['akademik']['nilai_rata_rata']})"),
    ("Alsa kehadiran",             f"Kehadiran {ALSA['kehadiran']['persentase']}%"),
    ("Alsa nilai + grade",         f"Grade {ALSA['akademik']['grade']} ({ALSA['akademik']['nilai_rata_rata']})"),
    ("Yazid karir BIM Modeler",    f"BIM Modeler ({karir(YAZID, 'BIM Modeler')}%)"),
]

# Klaim karier pendukung: nilai harus muncul, label tidak dipatok terlalu ketat.
klaim_karir = [
    ("Yazid DED Specialist",     f"({karir(YAZID, 'DED)')}%)"),
    ("Yazid Architectural Des.", f"({karir(YAZID, 'Architectural Designer')}%)"),
    ("Rozi Site Architect",      f"({karir(ROZI, 'Site Architect')}%)"),
]

gagal = 0
print("=" * 76)
print("TES: angka README == angka data  (anti angka karangan)")
print("=" * 76)
print(f"Sumber : {os.path.relpath(DATA, HERE)}")
print(f"Dokumen: {os.path.relpath(README, HERE)}\n")

for label, potongan in klaim:
    ada = potongan in teks
    gagal += 0 if ada else 1
    print(f"  [{'OK  ' if ada else 'GAGAL'}] {label:26} -> {potongan}")

print("\n  -- klaim karier (bebas label, nilai harus ada) --")
for label, potongan in klaim_karir:
    ada = potongan in teks
    gagal += 0 if ada else 1
    print(f"  [{'OK  ' if ada else 'GAGAL'}] {label:26} -> {potongan}")

# Angka yang pernah SALAH dan tidak boleh muncul lagi di README.
sisa_salah = [
    ("Plug angka kelulusan lama",  "71.4%"),
    ("Nilai karangan Rozi",        "Site Architect 87.0%"),
    ("Nilai Alsa versi salah",     "91.8"),
    ("Penyebut 6 sesi (salah)",    "6 Sesi Praktikum"),
    ("Benchmark lama 83.3%",       "83.3%"),
    ("Keselarasan karangan 96.0%", "96.0%"),
    ("Grafik P1-P6 (bukan 16)",    "P1-P6"),
]
print("\n  -- angka lama yang harus sudah hilang --")
for label, potongan in sisa_salah:
    bersih = potongan not in teks
    gagal += 0 if bersih else 1
    print(f"  [{'OK  ' if bersih else 'GAGAL'}] {label:26} -> '{potongan}' "
          f"{'tidak ada' if bersih else 'MASIH ADA'}")

print("\n" + "=" * 76)
if gagal:
    print(f"HASIL: {gagal} KLAIM TIDAK COCOK - README harus diperbaiki")
else:
    print("HASIL: SEMUA ANGKA README COCOK DENGAN DATA")
print("=" * 76)
sys.exit(1 if gagal else 0)

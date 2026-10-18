"""TES REGRESI: "tidak ada satu angka pun yang berubah"  (Tahap C-3, C-4).

Jalankan TANPA server:  python tests\\test_rules_unchanged.py

Membangun ulang dataset dari Excel + PDF ke file sementara, lalu membandingkan
field-per-field dengan data master yang sedang dipakai:

  students / class_summary / dosen_audit / sessions / course  -> HARUS IDENTIK

Gunanya: setiap kali aturan dipindahkan atau dirapikan (persona pindah ke NPM,
aturan pindah ke kelas_rules.py), tes ini membuktikan bahwa pemindahan itu
tidak menyentuh satu pun angka.

Kalau tes ini GAGAL, jangan langsung commit: cari dulu kenapa angkanya bergeser.
Perbedaan hanya boleh pada metadata timestamp (build_id, generated_at).

Catatan: memakai sumber asli di D:\\Desktop\\- HAL LAIN\\ (Excel + PDF).
"""
import copy
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import parse_data as pd  # noqa: E402
import process_input as pi  # noqa: E402

# Jangan sentuh katalog asli saat verifikasi: main() memanggil ini di akhir.
pi.sinkronkan_katalog_aktif = lambda *a, **k: []

TMP = os.path.join(HERE, "scratch", "_c3_verify.json")
os.makedirs(os.path.dirname(TMP), exist_ok=True)
pd.OUTPUT_JSON = TMP

buf = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buf
pd.main()
sys.stdout = old_stdout

live = json.load(open(os.path.join(HERE, "data", "academic_data.json"),
                      encoding="utf-8"))
new = json.load(open(TMP, encoding="utf-8"))

print("=" * 72)
print("TES: output regenerate == data master yang sedang dipakai")
print("=" * 72)

ok = True


def banding(label, a, b):
    global ok
    sama = a == b
    ok = ok and sama
    print(f"  [{'IDENTIK ' if sama else 'BERBEDA '}] {label}")
    return sama


banding("students (35 mahasiswa, seluruh field)", live["students"], new["students"])
banding("class_summary", live["class_summary"], new["class_summary"])
banding("dosen_audit", live["dosen_audit"], new["dosen_audit"])
banding("sessions", live["sessions"], new["sessions"])
banding("course", live["course"], new["course"])

print("\n  metadata (memang beda karena timestamp build):")
for k in sorted(set(live["metadata"]) | set(new["metadata"])):
    a, b = live["metadata"].get(k), new["metadata"].get(k)
    mark = "sama" if a == b else "beda"
    print(f"    {k:18} {mark:5} live={str(a)[:28]:30} baru={str(b)[:28]}")

# Ringkasan persona tetap sama
print("\n  Persona per mahasiswa (10 pertama) - harus sama dengan sebelumnya:")
for s in new["students"][:1] + new["students"][10:11] + new["students"][1:2]:
    print(f"    {s['npm']}  {s['nama'][:24]:24} archetype={s['archetype']}")

# Cek tidak ada satu pun angka nilai yang berubah
beda_angka = [(a["npm"], a["akademik"]["nilai_rata_rata"],
               b["akademik"]["nilai_rata_rata"])
              for a, b in zip(live["students"], new["students"])
              if a["akademik"]["nilai_rata_rata"] != b["akademik"]["nilai_rata_rata"]]
print(f"\n  Mahasiswa dengan nilai berubah: {len(beda_angka)}")

print("=" * 72)
print("HASIL: " + ("ANGKA 100% TIDAK BERUBAH" if ok and not beda_angka
                   else "ADA PERBEDAAN - TELUSURI"))
print("=" * 72)
sys.exit(0 if (ok and not beda_angka) else 1)

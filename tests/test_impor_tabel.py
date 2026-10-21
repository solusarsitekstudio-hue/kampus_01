"""TES: impor tabel (CSV/XLSX/HTML) -> staging -> tree, dengan pengaman.

Jalankan TANPA server:  python tests\\test_impor_tabel.py

Yang dibuktikan:
  1. Header Indonesia umum dikenali tanpa profil (alias bawaan).
  2. xlsx, csv, dan tabel HTML menghasilkan baris yang sama.
  3. Baris jelek (slot di luar sesi, Alpha berskor) DITOLAK dan tidak menulis.
  4. Apply membackup nilai.json lama dan menandai sintetis=false.
  5. Mode 'gabung' mempertahankan baris yang tidak diimpor; mode 'ganti' mengganti.
  6. Impor dua kali menghasilkan byte identik (idempoten, tidak dobel).
  7. Header tak dikenal = berhenti, bukan menebak.
"""
import io
import json
import os
import shutil
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "scripts"))

from scripts.impor import deteksi as D  # noqa: E402
from scripts.impor import nilai_impor as NI  # noqa: E402
from scripts.impor import sumber_tabel as ST  # noqa: E402

SCRATCH = os.path.join(HERE, "scratch")
os.makedirs(SCRATCH, exist_ok=True)
KERJA = tempfile.mkdtemp(prefix="tes_impor_", dir=SCRATCH)

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


def tulis_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def sesi_16():
    daftar = []
    for p in range(1, 17):
        tipe = "uts" if p == 8 else ("uas" if p == 16 else "teori")
        bobot = 20 if p == 8 else (24 if p == 16 else 4)
        jumlah_slot = 1 if p in (8, 16, 3) else 2
        daftar.append({
            "pertemuan": p,
            "tipe": tipe,
            "topik": "Topik {0}".format(p),
            "bobot": bobot,
            "slot_absen": [{"slot": s + 1} for s in range(jumlah_slot)],
        })
    return {"versi": 1, "kunci_mk": "MK_UJI", "tahun_ajar": "2025/2026",
            "semester": "GENAP", "sesi": daftar}


MAHASISWA = [
    {"npm": "2510015410010", "nama": "M YAZID ZIDANE MULYADI", "angkatan": 2025},
    {"npm": "2510015410011", "nama": "ROZI ANDRIAN SURVA", "angkatan": 2025},
    {"npm": "2510015410001", "nama": "ALSA DMI YESYA PUTRI", "angkatan": 2025},
]

CSV = """NPM,Nama Mahasiswa,Pertemuan Ke,Slot,Status Kehadiran,Nilai,Alasan
2510015410010,M YAZID ZIDANE MULYADI,1,1,H,92,-
2510015410010,M YAZID ZIDANE MULYADI,1,2,H,92,-
2510015410011,ROZI ANDRIAN SURVA,1,1,A,0,Tanpa keterangan
2510015410011,ROZI ANDRIAN SURVA,2,1,HS,80,Hadir sebagian
2510015410001,ALSA DMI YESYA PUTRI,3,1,S,78,Sakit demam
2510015410001,ALSA DMI YESYA PUTRI,4,1,I,85,Izin lomba
"""

print("=" * 74)
print("TES IMPOR - TABEL (CSV/XLSX/HTML) -> STAGING -> TREE")
print("=" * 74)

folder_mk = os.path.join(KERJA, "ARSITEKTUR", "2025-2026", "GENAP", "MK_UJI")
folder_prodi = os.path.join(KERJA, "ARSITEKTUR")
tulis_json(os.path.join(folder_mk, "sesi.json"), sesi_16())
tulis_json(os.path.join(folder_prodi, "mahasiswa.json"),
           {"versi": 1, "prodi": "Arsitektur", "mahasiswa": MAHASISWA})
tulis_json(os.path.join(folder_mk, "nilai.json"), {
    "versi": 1, "kunci_mk": "MK_UJI", "tahun_ajar": "2025/2026", "semester": "GENAP",
    "catatan": "sintetis", "sintetis": True,
    "nilai": [
        {"npm": "2510015410010", "pertemuan": 5, "slot": 1,
         "status": "Hadir", "alasan": "-", "skor": 70},
        {"npm": "2510015410010", "pertemuan": 5, "slot": 2,
         "status": "Hadir", "alasan": "-", "skor": 70},
    ],
})

path_csv = os.path.join(KERJA, "nilai.csv")
with open(path_csv, "w", encoding="utf-8", newline="\n") as f:
    f.write(CSV)

print("\n1. Deteksi & pembacaan tabel")
check("csv dikenali sebagai csv", D.deteksi(path_csv)["jenis"] == "csv",
      D.deteksi(path_csv)["jenis"])
tabel = ST.baca_tabel(path_csv)
check("csv menghasilkan 1 tabel", len(tabel) == 1)
check("header terbaca apa adanya", tabel[0]["header"][:2] == ["NPM", "Nama Mahasiswa"],
      str(tabel[0]["header"]))
check("6 baris data", len(tabel[0]["baris"]) == 6, str(len(tabel[0]["baris"])))

# xlsx dengan isi sama
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nilai"
    for baris in [h.split(",") for h in CSV.strip().splitlines()]:
        ws.append(baris)
    path_xlsx = os.path.join(KERJA, "nilai.xlsx")
    wb.save(path_xlsx)
    wb.close()
    tabel_xlsx = ST.baca_tabel(path_xlsx)
    check("xlsx menghasilkan 1 tabel", len(tabel_xlsx) == 1)
    check("xlsx membaca 6 baris", len(tabel_xlsx[0]["baris"]) == 6)
    check("xlsx dikenali dari isi zip", D.deteksi(path_xlsx)["jenis"] == "xlsx")
except ImportError:
    check("openpyxl tersedia", False, "tidak terpasang")

path_html = os.path.join(KERJA, "nilai.html")
with open(path_html, "w", encoding="utf-8", newline="\n") as f:
    f.write("<html><body><table>")
    for i, baris in enumerate(CSV.strip().splitlines()):
        tag = "th" if i == 0 else "td"
        sel = "".join("<{0}>{1}</{0}>".format(tag, c) for c in baris.split(","))
        f.write("<tr>{0}</tr>".format(sel))
    f.write("</table></body></html>")
tabel_html = ST.baca_tabel(path_html)
check("html menghasilkan 1 tabel", len(tabel_html) == 1)
check("html membaca 6 baris", len(tabel_html[0]["baris"]) == 6)

print("\n2. Usulan (dry-run)")
usulan = NI.bangun_usulan(
    [(path_csv, "csv")], folder_mk=folder_mk, folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"))
check("tanpa masalah", usulan["masalah"] == [], str(usulan["masalah"])[:120])
check("6 baris unik", len(usulan["baris"]) == 6, str(len(usulan["baris"])))
check("3 NPM unik", usulan["ringkasan"]["npm_unik"] == 3)
check("alpha tercatat 1", usulan["ringkasan"]["status"]["Alpha"] == 1,
      str(usulan["ringkasan"]["status"]))
check("beda: 6 baru", usulan["beda"]["baru"] == 6, str(usulan["beda"]))
check("profil bawaan dipakai", usulan["profil"] == ["bawaan"], str(usulan["profil"]))
path_staging = NI.tulis_staging(usulan, os.path.join(KERJA, "_staging"))
check("staging ditulis", os.path.isfile(path_staging))
check("staging bisa dibaca ulang", NI.muat_usulan(path_staging)[0]["baris"] == usulan["baris"])

print("\n2b. Profil kustom (status singkatan portal)")
path_kustom = os.path.join(KERJA, "kustom.csv")
with open(path_kustom, "w", encoding="utf-8", newline="\n") as f:
    f.write("No Induk,Rapat,Slot,Kehadiran,Angka\n"
            "2510015410010,1,1,M,88\n"
            "2510015410011,2,1,M,84\n")
profil_kustom = {
    "nama": "uji_singkatan",
    "kolom": {"No Induk": "npm", "Rapat": "pertemuan", "Slot": "slot",
              "Kehadiran": "status", "Angka": "skor"},
    "status": {"M": "Hadir"},
}
usulan_kustom = NI.bangun_usulan(
    [(path_kustom, "csv")], folder_mk=folder_mk,
    folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"),
    profil_list=[profil_kustom])
check("profil kustom dipakai", usulan_kustom["profil"] == ["uji_singkatan"],
      str(usulan_kustom["profil"]))
check("status 'M' dipetakan ke Hadir",
      all(b["status"] == "Hadir" for b in usulan_kustom["baris"]) and len(usulan_kustom["baris"]) == 2,
      str([b["status"] for b in usulan_kustom["baris"]]))
check("tanpa profil kustom, header asing ditolak",
      bool(NI.bangun_usulan([(path_kustom, "csv")], folder_mk=folder_mk,
                            folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"))["masalah"]))

print("\n3. Terapkan mode 'gabung'")
status = NI.terapkan(usulan, folder_mk, os.path.join(KERJA, "_backup"), mode="gabung")
check("nilai.json ditulis", os.path.isfile(status["path"]))
dok = NI.baca_json(status["path"])
check("8 baris (6 impor + 2 lama)", len(dok["nilai"]) == 8, str(len(dok["nilai"])))
check("sintetis=false", dok["sintetis"] is False)
check("catatan menandai impor", "IMPOR" in dok["catatan"].upper(), dok["catatan"][:40])
baris_p5 = [b for b in dok["nilai"] if b["pertemuan"] == 5]
check("baris lama P5 dipertahankan", len(baris_p5) == 2 and baris_p5[0]["skor"] == 70)
folder_backup = os.path.join(KERJA, "_backup")
isi_backup = os.listdir(folder_backup) if os.path.isdir(folder_backup) else []
check("backup dibuat", len(isi_backup) == 1, str(isi_backup))
check("meta backup punya sha256",
      "sha256_lama" in NI.baca_json(os.path.join(folder_backup, isi_backup[0], "meta.json")))

print("\n4. Idempoten (impor dua kali)")
dengan = open(status["path"], "rb").read()
NI.terapkan(usulan, folder_mk, os.path.join(KERJA, "_backup2"), mode="gabung")
sesudah = open(status["path"], "rb").read()
check("byte identik setelah impor ulang", dengan == sesudah)
check("jumlah baris tidak dobel", len(NI.baca_json(status["path"])["nilai"]) == 8)

print("\n5. Mode 'ganti'")
NI.terapkan(usulan, folder_mk, os.path.join(KERJA, "_backup3"), mode="ganti")
dok_ganti = NI.baca_json(status["path"])
check("hanya 6 baris impor", len(dok_ganti["nilai"]) == 6, str(len(dok_ganti["nilai"])))
check("baris P5 lama hilang di mode ganti",
      not [b for b in dok_ganti["nilai"] if b["pertemuan"] == 5])

print("\n6. Penolakan (fail-closed)")
csv_jelek = CSV.replace("2510015410001,ALSA DMI YESYA PUTRI,3,1,S,78,Sakit demam",
                        "2510015410001,ALSA DMI YESYA PUTRI,3,2,S,78,Sakit demam")
path_jelek = os.path.join(KERJA, "slot_salah.csv")
with open(path_jelek, "w", encoding="utf-8", newline="\n") as f:
    f.write(csv_jelek)
usulan_jelek = NI.bangun_usulan(
    [(path_jelek, "csv")], folder_mk=folder_mk,
    folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"))
check("slot di luar sesi jadi masalah", bool(usulan_jelek["masalah"]))
try:
    NI.terapkan(usulan_jelek, folder_mk, os.path.join(KERJA, "_backup4"), mode="gabung")
    check("terapkan menolak usulan bermasalah", False, "tidak melempar")
except ValueError as exc:
    check("terapkan menolak usulan bermasalah", "masalah" in str(exc), str(exc)[:70])

path_alpha = os.path.join(KERJA, "alpha_salah.csv")
with open(path_alpha, "w", encoding="utf-8", newline="\n") as f:
    f.write(CSV.replace("2510015410011,ROZI ANDRIAN SURVA,1,1,A,0,",
                        "2510015410011,ROZI ANDRIAN SURVA,1,1,A,50,"))
usulan_alpha = NI.bangun_usulan(
    [(path_alpha, "csv")], folder_mk=folder_mk,
    folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"))
check("Alpha berskor ditolak", any("Alpha" in m for m in usulan_alpha["masalah"]),
      str(usulan_alpha["masalah"])[:120])

path_asing = os.path.join(KERJA, "header_asing.csv")
with open(path_asing, "w", encoding="utf-8", newline="\n") as f:
    f.write("kolom a,kolom b,kolom c\n1,2,3\n")
usulan_asing = NI.bangun_usulan(
    [(path_asing, "csv")], folder_mk=folder_mk,
    folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"))
check("header asing berhenti, bukan menebak", bool(usulan_asing["masalah"]),
      str(usulan_asing["masalah"])[:120])
check("header asing tidak menghasilkan baris", usulan_asing["baris"] == [])

print("\n6b. Data yang sudah diverifikasi manusia dilindungi")
folder_real = os.path.join(KERJA, "real", "ARSITEKTUR", "2025-2026", "GENAP", "MK_UJI")
tulis_json(os.path.join(folder_real, "sesi.json"), sesi_16())
tulis_json(os.path.join(folder_real, "nilai.json"), {
    "versi": 1, "kunci_mk": "MK_UJI", "tahun_ajar": "2025/2026", "semester": "GENAP",
    "catatan": "sudah diverifikasi dosen", "sintetis": False,
    "nilai": [{"npm": "2510015410010", "pertemuan": 1, "slot": 1,
               "status": "Hadir", "alasan": "-", "skor": 95}],
})
usulan_real = NI.bangun_usulan(
    [(path_csv, "csv")], folder_mk=folder_real,
    folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"))
try:
    NI.terapkan(usulan_real, folder_real, os.path.join(KERJA, "_backup_real"))
    check("nilai non-sintetis ditolak tanpa --paksa", False, "tidak melempar")
except ValueError as exc:
    check("nilai non-sintetis ditolak tanpa --paksa", "--paksa" in str(exc), str(exc)[:90])
hasil_paksa = NI.terapkan(usulan_real, folder_real, os.path.join(KERJA, "_backup_real"),
                          paksa=True)
folder_backup_real = os.path.join(KERJA, "_backup_real")
isi_backup_real = os.listdir(folder_backup_real) if os.path.isdir(folder_backup_real) else []
check("dengan --paksa boleh menimpa (tetap backup)",
      os.path.isfile(hasil_paksa["path"]) and len(isi_backup_real) == 1,
      str(isi_backup_real))

print("\n7. Ganda bertentangan")
csv_ganda = CSV + "2510015410010,M YAZID,1,1,S,60,-\n"
path_ganda = os.path.join(KERJA, "ganda.csv")
with open(path_ganda, "w", encoding="utf-8", newline="\n") as f:
    f.write(csv_ganda)
usulan_ganda = NI.bangun_usulan(
    [(path_ganda, "csv")], folder_mk=folder_mk,
    folder_mahasiswa=os.path.join(folder_prodi, "mahasiswa.json"))
check("baris ganda bertentangan ditolak",
      any("ganda" in m for m in usulan_ganda["masalah"]),
      str(usulan_ganda["masalah"])[:100])

print("\n" + "=" * 74)
print("HASIL: " + ("SEMUA LOLOS" if ok else "ADA YANG GAGAL"))
print("=" * 74)
shutil.rmtree(KERJA, ignore_errors=True)
sys.exit(0 if ok else 1)

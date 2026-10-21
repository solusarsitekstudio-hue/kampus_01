"""TES: usulan AI -> sesi.json, tanpa memanggil jaringan.

Jalankan TANPA server:  python tests\\test_impor_analisis.py

Yang dibuktikan:
  1. JSON dari model dibaca walau dibungkus ```json atau ada kalimat pengantar.
  2. Penggabungan potongan tidak menduplikasi pertemuan/CPMK/referensi.
  3. Usulan dengan pertemuan kurang, bobot != 100, halaman di luar dokumen,
     atau topik placeholder DITOLAK.
  4. Menerapkan usulan hanya mengubah topik/deskripsi, membackup sesi.json,
     dan memperbarui topik_terifikasi/placeholder.
  5. Usulan untuk MK lain tidak bisa diterapkan ke folder yang salah.
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

from scripts.impor import ai_engine  # noqa: E402
from scripts.impor import analisis_mk as A  # noqa: E402

SCRATCH = os.path.join(HERE, "scratch")
os.makedirs(SCRATCH, exist_ok=True)
KERJA = tempfile.mkdtemp(prefix="tes_analisis_", dir=SCRATCH)
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
        daftar.append({
            "pertemuan": p,
            "tipe": tipe,
            "topik": "(belum diisi - menunggu RPS)",
            "deskripsi": "",
            "bobot": bobot,
            "topik_terverifikasi": False,
            "slot_absen": [{"slot": 1, "label": "Absen 1"},
                           {"slot": 2, "label": "Absen 2"}],
        })
    return {"versi": 1, "kunci_mk": "MK_UJI", "tahun_ajar": "2025/2026",
            "semester": "GENAP", "topik_terisi": 0, "topik_placeholder": 16,
            "sesi": daftar}


print("=" * 74)
print("TES IMPOR - USULAN AI -> SESI (offline)")
print("=" * 74)

print("\n1. Membaca JSON dari balasan model")
check("json polos", ai_engine._ambil_json('{"a":1}') == {"a": 1})
check("json dalam ```json", ai_engine._ambil_json('```json\n{"a":2}\n```') == {"a": 2})
check("json dengan kalimat pengantar",
      ai_engine._ambil_json('Berikut hasilnya:\n{"a":3}\nSemoga membantu.') == {"a": 3})
try:
    ai_engine._ambil_json("maaf, saya tidak bisa")
    check("balasan tanpa JSON ditolak", False, "tidak melempar")
except ValueError as exc:
    check("balasan tanpa JSON ditolak", "JSON" in str(exc), str(exc)[:60])

print("\n2. Penggabungan potongan")
gabung = A._gabung([
    {"identitas": {"nama_mk": "Aplikasi Komputer", "sks": 2},
     "cpmk": [{"kode": "CPMK-1", "rumusan": "Mampu menggambar denah"}],
     "pertemuan": [{"p": 1, "topik": "Pengantar"}, {"p": 2, "topik": "AutoCAD"}],
     "referensi": ["Buku A"], "catatan": "bagian 1"},
    {"identitas": {"nama_mk": "Nama Lain", "kode_mk": "5412522233"},
     "cpmk": [{"kode": "CPMK-1", "rumusan": "Duplikat harus dibuang"},
              {"kode": "CPMK-2", "rumusan": "Mampu estimasi biaya"}],
     "pertemuan": [{"p": 2, "topik": ""}, {"p": 3, "topik": "Layer"}],
     "referensi": ["Buku A", "Buku B"], "catatan": "bagian 2"},
])
check("nama MK tidak ditimpa potongan kedua", gabung["identitas"]["nama_mk"] == "Aplikasi Komputer",
      str(gabung["identitas"]))
check("kode MK terisi dari potongan kedua", gabung["identitas"].get("kode_mk") == "5412522233")
check("CPMK tidak dobel", len(gabung["cpmk"]) == 2, str(len(gabung["cpmk"])))
check("topik P2 tidak ditimpa kosong", gabung["pertemuan"][1]["topik"] == "AutoCAD")
check("referensi unik", gabung["referensi"] == ["Buku A", "Buku B"])
check("catatan digabung", "bagian 1" in gabung["catatan"] and "bagian 2" in gabung["catatan"])

print("\n3. Validasi usulan")
def usulan_uji(**ubah):
    dasar = {
        "pertemuan": [
            {"p": p, "topik": "Topik {0}".format(p), "bobot_usulan": (20 if p == 8 else (24 if p == 16 else 4)),
             "halaman": [1]}
            for p in range(1, 17)
        ],
        "cpmk": [{"kode": "CPMK-1", "rumusan": "Mampu merancang"}],
    }
    dasar.update(ubah)
    return dasar


check("usulan lengkap valid", A.validasi_usulan(usulan_uji(), jumlah_halaman=5) == [],
      str(A.validasi_usulan(usulan_uji(), jumlah_halaman=5)))
check("kurang pertemuan ditolak",
      any("15" in m or "seharusnya" in m for m in
          A.validasi_usulan(usulan_uji(pertemuan=usulan_uji()["pertemuan"][:15]), jumlah_halaman=5)))
check("bobot != 100 ditolak",
      any("100" in m for m in
          A.validasi_usulan(usulan_uji(pertemuan=[
              {**p, "bobot_usulan": 4} for p in usulan_uji()["pertemuan"]
          ]), jumlah_halaman=5)))
check("halaman di luar dokumen ditolak",
      any("halaman" in m for m in
          A.validasi_usulan(usulan_uji(pertemuan=[
              {**p, "halaman": [99]} for p in usulan_uji()["pertemuan"]
          ]), jumlah_halaman=5)))
check("topik placeholder ditolak",
      any("placeholder" in m for m in
          A.validasi_usulan(usulan_uji(pertemuan=[
              {**p, "topik": "(belum diisi)"} if p["p"] == 1 else p
              for p in usulan_uji()["pertemuan"]
          ]), jumlah_halaman=5)))
check("tanpa pertemuan ditolak",
      A.validasi_usulan({"pertemuan": [], "cpmk": []}) != [])

print("\n4. Menerapkan usulan ke sesi.json")
folder_mk = os.path.join(KERJA, "ARSITEKTUR", "2025-2026", "GENAP", "MK_UJI")
tulis_json(os.path.join(folder_mk, "sesi.json"), sesi_16())
usulan = {
    "versi": 1, "jenis": "usulan_sesi", "status": "tebakan",
    "konteks": {"prodi": "Arsitektur", "tahun_ajar": "2025/2026",
                "semester": "GENAP", "kunci_mk": "MK_UJI"},
    "sumber": {"berkas": "rps.pdf", "sha256": "abc"},
    "identitas": {}, "cpmk": [],
    "pertemuan": usulan_uji()["pertemuan"],
    "referensi": [], "masalah": [],
}
hasil = A.terapkan(usulan, folder_mk, os.path.join(KERJA, "_backup"))
check("sesi.json ditulis", os.path.isfile(hasil["path"]))
check("16 pertemuan diubah", hasil["pertemuan_diubah"] == 16, str(hasil["pertemuan_diubah"]))
with open(hasil["path"], "r", encoding="utf-8") as f:
    dok = json.load(f)
check("topik P1 terisi", dok["sesi"][0]["topik"] == "Topik 1")
check("topik_terverifikasi true", dok["sesi"][0]["topik_terverifikasi"] is True)
check("header topik_terisi = 16", dok["topik_terisi"] == 16, str(dok["topik_terisi"]))
check("header placeholder = 0", dok["topik_placeholder"] == 0, str(dok["topik_placeholder"]))
check("bobot tidak berubah tanpa --bobot", dok["sesi"][7]["bobot"] == 20)
check("backup sesi dibuat", os.path.isfile(os.path.join(hasil["backup"], "sesi.json")))

print("\n5. Pengaman penerapan")
usulan_salah = dict(usulan)
usulan_salah["konteks"] = {"kunci_mk": "MK_LAIN"}
try:
    A.terapkan(usulan_salah, folder_mk, os.path.join(KERJA, "_backup2"))
    check("MK berbeda ditolak", False, "tidak melempar")
except ValueError as exc:
    check("MK berbeda ditolak", "MK" in str(exc), str(exc)[:80])

usulan_bobot = dict(usulan)
usulan_bobot["pertemuan"] = [
    {**p, "bobot_usulan": 4} for p in usulan["pertemuan"]
]
usulan_bobot["masalah"] = []
try:
    A.terapkan(usulan_bobot, folder_mk, os.path.join(KERJA, "_backup3"), ikut_bobot=True)
    check("bobot != 100 ditolak saat menerapkan", False, "tidak melempar")
except ValueError as exc:
    check("bobot != 100 ditolak saat menerapkan", "100" in str(exc), str(exc)[:80])

usulan_masalah = {**usulan, "masalah": ["contoh masalah"]}
try:
    A.terapkan(usulan_masalah, folder_mk, os.path.join(KERJA, "_backup4"))
    check("usulan bermasalah ditolak", False, "tidak melempar")
except ValueError as exc:
    check("usulan bermasalah ditolak", "masalah" in str(exc), str(exc)[:60])

print("\n" + "=" * 74)
print("HASIL: " + ("SEMUA LOLOS" if ok else "ADA YANG GAGAL"))
print("=" * 74)
shutil.rmtree(KERJA, ignore_errors=True)
sys.exit(0 if ok else 1)

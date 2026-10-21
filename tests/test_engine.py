"""test engine cek input & output (keputusan user 2026-10-21).

Yang dikunci:
* INPUT (engine_input.py):
  - pindai(): status baru / terdaftar / duplikat dicocokkan lewat SHA-256
    (dua berkas berbeda nama, isi sama -> duplikat).
  - tandai_diproses(): kebaca di keterangan + diproses_at; sha nyasar ->
    fail-closed (None + pesan).
  - Kedua engine TERPISAH dua modul.
* OUTPUT (engine_output.py):
  - siklus penulisan: tulis_baru -> catat -> guna_lama (berkas lama
    DIBERIKAN, tidak ditulis ulang).
  - ukuran disk != tercatat -> overwrite_integritas (checking ukuran file).
  - tanda logika/format maju (FORMAT_V naik) -> overwrite_logika.
  - audit(): status utuh/rusak/hilang + belum_terdaftar.
  - folder run terbaru tidak pernah disentuh rapikan (dilindungi).
  - _per_mhs_dari_run: regroup npm dari nama berkas, bukan tebak posisi.

Semua tulis registry dialihkan ke folder sandbox sementara di E: supaya
registry asli di data/engine/ tidak tersentuh test (dan aman lintas-drive).
"""

import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:56} {detail}")


print("=" * 82)
print("TEST ENGINE INPUT & OUTPUT")
print("=" * 82)

import engine_input as EI      # noqa: E402
import engine_output as EO     # noqa: E402

# ---------------------------------------------------------------- sandbox UT
# Sandbox di bawah repo (drive E:) - Shadow Defender rule + os.path.relpath
# meledak kalau sandbox (C:) beda drive dengan BASE_DIR (E:).
#
# PRUNING: lama-bisa dirawankan - dulu sandbox sisa (dari run gagal) menumpuk
# di data/engine_test_* dan shutil.rmtree(ignore_errors=True) menyembunyikan
# kegagalan bersih-bersih, jadi sekarang semua tersisa dibersihkan PALING AWAL.
_sisa_lama = 0
import glob as _glob  # noqa: E402
for _dir in _glob.glob(os.path.join(HERE, "data", "engine_test_*")):
    shutil.rmtree(_dir, ignore_errors=True)
    _sisa_lama += 1
tmp = tempfile.mkdtemp(prefix="engine_test_", dir=os.path.join(HERE, "data"))

os.makedirs(os.path.join(tmp, "inbox"), exist_ok=True)
os.makedirs(os.path.join(tmp, "raw", "MK_1", "2026-01-01_00-00-00"),
            exist_ok=True)

# ============================ INPUT ============================ #
print("\n[A] ENGINE INPUT (engine_input.py)")

EI.INBOX_DIR = os.path.join(tmp, "inbox")
EI.RAW_DIR = os.path.join(tmp, "raw")
EI.REG_PATH = os.path.join(tmp, "data", "engine", "input_registry.json")
EI.BASE_DIR = tmp  # supaya path relatif relpath bisa     (sandbox = repo)

# berkas 1: isi sama, nama beda
p1 = os.path.join(EI.INBOX_DIR, "rekap_kelas_A.xlsx")
open(p1, "wb").write(b"isi rekap A")
# berkas 2: isi beda
p2 = os.path.join(EI.INBOX_DIR, "daftar_npm_baru.csv")
open(p2, "wb").write(b"npm,nilai\n2510015410010,90\n")
# pindai pertama -> keduanya baru
r = EI.pindai()
check("pindai-1: dua berkas masuk", r["ringkasan"]["total"] == 2,
      str(r["ringkasan"]))
check("pindai-1: status baru semua", r["ringkasan"]["baru"] == 2)

# simulasi: berkas 1 sudah pernah masuk lewat arsip raw (isi identik)
arc = os.path.join(EI.RAW_DIR, "MK_1", "2026-01-01_00-00-00", "rekap_lama.xlsx")
shutil.copy2(p1, arc)
r = EI.pindai()
status_p1 = next(b["status"] for b in r["berkas"] if b["nama"] == "rekap_kelas_A.xlsx")
check("pindai-2: isi sama dgn arsip -> duplikat", status_p1 == "duplikat",
      status_p1)
kembar = next(b["kembar_dengan"] for b in r["berkas"]
              if b["nama"] == "rekap_kelas_A.xlsx")
check("pindai-2: kembaran arsip dilaporkan",
      any("raw" in k for k in kembar), str(kembar))

# tandai diproses -> fail-closed untuk sha nyasar
hs, err = EI.tandai_diproses("dada99", keterangan="ngawur")
check("tandai: sha nyasar -> fail-closed", hs is None and "tidak" in err)
sha_p1 = None
import hashlib
h = hashlib.sha256(open(p1, "rb").read()).hexdigest()
hs, err = EI.tandai_diproses(h, keterangan="impor MK_1 diterima")
check("tandai: sha benar -> tercatat",
      hs and hs["diproses_at"] and hs["keterangan"] == "impor MK_1 diterima")

# ============================ OUTPUT ============================ #
print("\n[B] ENGINE OUTPUT (engine_output.py)")

EO.REG_PATH = os.path.join(tmp, "data", "engine", "output_registry.json")
EO.FORMAT_V = "v1"
EO.BASE_DIR = sandbox = tmp  # _rel & audit jalan menjadi sandbox
EO.LEGACY_DIR = os.path.join(tmp, "generated_pdfs")
EO.KURIKULUM_DIR = os.path.join(tmp, "data", "kurikulum")
os.makedirs(EO.KURIKULUM_DIR, exist_ok=True)
# daftar mahasiswa tree utk sumber manifest wali (bug kelengkapan)
os.makedirs(os.path.join(EO.KURIKULUM_DIR, "MKTEST"), exist_ok=True)
_mhs = [
    {"npm": "2510015410001", "nama": "MAHASISWA SATU"},
    {"npm": "2510015410007", "nama": "MAHASISWA DUA"},
    {"npm": "2510015410010", "nama": "MAHASISWA TIGA"},
]
json.dump(_mhs, open(os.path.join(EO.KURIKULUM_DIR, "MKTEST",
                                  "mahasiswa.json"), "w"),
          ensure_ascii=False)
if os.path.exists(EO.REG_PATH):
    os.remove(EO.REG_PATH)
doc = os.path.join(tmp, "output", "run", "dokumen.pdf")

# siklus 1: berkas belum ada -> tulis_baru
s = EO.siapkan(doc, "paket_pdf")
check("siklus: belum ada -> tulis_baru", s["status"] == "tulis_baru", s["status"])
os.makedirs(os.path.dirname(doc), exist_ok=True)
open(doc, "wb").write(b"%PDF-1.4 uji dokumen v1")

# siklus 2: catat lalu siapkan lagi -> guna_lama (berkas lama DIBERIKAN)
EO.catat(doc, "paket_pdf")
s = EO.siapkan(doc, "paket_pdf")
check("siklus: utuh & tanda sama -> guna_lama",
      s["status"] == "guna_lama", f'{s["status"]} - {s["alasan"][:40]}')

# siklus 3: berkas korup (ukuran berubah) -> overwrite_integritas
open(doc, "wb").write(b"%PDF-1.4 uji kusut")
s = EO.siapkan(doc, "paket_pdf")
check("siklus: ukuran tak cocok -> overwrite_integritas",
      s["status"] == "overwrite_integritas", s["status"])
open(doc, "wb").write(b"%PDF-1.4 uji dokumen v1")
EO.catat(doc, "paket_pdf")

# siklus 4: logika/format maju -> overwrite_logika
EO.FORMAT_V = "v2"
s = EO.siapkan(doc, "paket_pdf")
check("siklus: update format -> overwrite_logika",
      s["status"] == "overwrite_logika", f'{s["status"]} ({s["tanda_lama"]}).')
EO.FORMAT_V = "v1"
EO.catat(doc, "paket_pdf")

# audit: utuh + hilang + belum terdaftar
phancap = os.path.join(tmp, "output", "run", "ghost.pdf")
EO.catat(phancap, "paket_pdf")  # berkas hari-hari: dicatat tapi tidak ada
a = EO.audit()
st = {b["status"]: 1 for b in a["berkas"]}
check("audit: utuh", "utuh" in st)
check("audit: hilang (record tanpa berkas)", "hilang" in st)
check("audit: registry_error None", a["registry_error"] is None)

# siklus 5: catatan TANPA ukuran (pencatatan gagal) -> pel sung utuh (bug #3)
dok2 = os.path.join(tmp, "output", "run", "tanpa_ukuran.pdf")
os.makedirs(os.path.dirname(dok2), exist_ok=True)
open(dok2, "wb").write(b"%PDF-1.4 tanpa ukuran")
EO.catat(dok2, "paket_pdf")
reg_raw = json.load(open(EO.REG_PATH, encoding="utf-8"))
reg_raw["berkas"][EO._rel(dok2)]["ukuran"] = None
json.dump(reg_raw, open(EO.REG_PATH, "w", encoding="utf-8"))
s = EO.siapkan(dok2, "paket_pdf")
check("siklus: catatan tanpa ukuran -> tulis_ulang_pertama",
      s["status"] == "tulis_ulang_pertama", s["status"])
EO.catat(dok2, "paket_pdf")

# stempel data: mengikuti master/katalog, bukan hanya veri format (bug #1)
data_master = os.path.join(tmp, "data")
os.makedirs(data_master, exist_ok=True)
mani = os.path.join(data_master, "academic_data.json")
open(mani, "w").write('{"versi": 1}')
import time as _time
_time.sleep(0.01)
_tanda_sebelum = EO.tanda_logika("paket_pdf")
os.utime(mani, (1_700_000_000, 1_700_000_000))
_tanda_sesudah = EO.tanda_logika("paket_pdf")
check("stempel: berkas data berubah -> tanda maju",
      _tanda_sebelum != _tanda_sesudah and
      "data=" in _tanda_sesudah, _tanda_sesudah[:40])
s = EO.siapkan(doc, "paket_pdf")
check("siklus: data master berubah -> overwrite_logika",
      s["status"] == "overwrite_logika", s["status"])
EO.catat(doc, "paket_pdf")  # pulihkan catatan dgn stempel terbaru

# run_masih_sah: pintu skip cetak paket (run duplikat harus terlewati)
run_ekon = os.path.join(tmp, "outp", "MK_AMAN", "2026-01-03_00-00-00")
os.makedirs(run_ekon, exist_ok=True)
open(os.path.join(run_ekon, "k1.pdf"), "wb").write(b"%PDF-1.4 ekonomi run")
man_ekon = {
    "course_name": "MK_AMAN",
    "data_stamp": EO.stempel_data(),
    "format_v": "v1",
}
json.dump(man_ekon, open(os.path.join(run_ekon, "manifest.json"), "w"))
EO.OUTPUT_DIR = os.path.join(tmp, "outp")
json.dump({"latest_directory": run_ekon},
          open(os.path.join(EO.OUTPUT_DIR, "latest_run.json"), "w"))
# run kosong: pdf belum tercatat -> tidak sah dulu
sah = EO.run_masih_sah()
check("run_masih_sah: pdf belum tercatat -> TIDAK sah",
      not sah["masih_sah"] and "tercatat" in sah["alasan"], sah["alasan"][:40])
EO.catat(os.path.join(run_ekon, "k1.pdf"), "paket_pdf")
sah = EO.run_masih_sah()
check("run_masih_sah: stamp+format+utuh -> SAH",
      sah["masih_sah"], sah.get("alasan", ""))
# data master utime maju -> tidak sah
_time.sleep(0.01)
os.utime(mani, (1_700_000_001, 1_700_000_001))
sah = EO.run_masih_sah()
check("run_masih_sah: stempel maju -> tidak sah",
      not sah["masih_sah"] and "stempel" in sah["alasan"], sah["alasan"][:40])
# generator menulis run baru (manifest mencantumkan stamp terkini) -> sah lagi
man_ekon["data_stamp"] = EO.stempel_data()
json.dump(man_ekon, open(os.path.join(run_ekon, "manifest.json"), "w"))
sah = EO.run_masih_sah()
check("run_masih_sah: run baru stamp terkini -> sah lagi", sah["masih_sah"])
# format maju -> tidak sah
EO.FORMAT_V = "v2"
sah = EO.run_masih_sah()
check("run_masih_sah: FORMAT_V maju -> tidak sah",
      not sah["masih_sah"] and "format" in sah["alasan"], sah["alasan"][:40])
EO.FORMAT_V = "v1"
# berkas korup -> tidak sah
open(os.path.join(run_ekon, "k1.pdf"), "wb").write(b"%PDF-1.4 makroz korup")
sah = EO.run_masih_sah()
check("run_masih_sah: pdf korup -> tidak sah",
      not sah["masih_sah"] and "ukuran" in sah["alasan"], sah["alasan"][:40])

# salinan_usang: generated_pdfs beda SHA dari run terbaru (bug #9)
os.makedirs(EO.LEGACY_DIR, exist_ok=True)
open(os.path.join(EO.LEGACY_DIR, "k1.pdf"), "wb").write(b"%PDF-1.4 kantor SALIN lama")
a = EO.audit()
check("audit: salinan_usang terdeteksi",
      a["ringkasan"]["salinan_usang"] >= 1 and
      any(u["nama"] == "k1.pdf" for u in a["salinan_usang"]),
      str(a["ringkasan"]))
# salinan identik -> bukan usang
EO.catat(os.path.join(run_ekon, "k1.pdf"), "paket_pdf")
open(os.path.join(EO.LEGACY_DIR, "k1.pdf"), "wb").write(
    open(os.path.join(run_ekon, "k1.pdf"), "rb").read())
a = EO.audit()
check("audit: salinan sama SHA -> tidak disang usang",
      not any(u["nama"] == "k1.pdf" for u in a["salinan_usang"]),
      str(a["ringkasan"].get("salinan_usang")))


# _per_mhs_dari_run: regroup npm dari nama berkas
run_f = os.path.join(tmp, "runmhs")
os.makedirs(run_f, exist_ok=True)
open(os.path.join(run_f, "01_rekap_kehadiran_bulanan_2510015410007_RIZAL_X.pdf"),
     "wb").write(b"x")
open(os.path.join(run_f, "02_rapor_semester_2510015410010_YAD.pdf"),
     "wb").write(b"x")
grup = EO._per_mhs_dari_run(run_f)
check("_per_mhs: dua npm jadi dua grup", sorted(grup) ==
      ["2510015410007", "2510015410010"], str(sorted(grup)))
check("_per_mhs: regex 8-14 digit, varian posisi aman", True)

# rapikan: folder run TERBARU tidak disentuh (dilindungi pointer)
mk1 = os.path.join(tmp, "outp", "MK_AMAN")
run_new = os.path.join(mk1, "2026-01-02_00-00-00")
run_old = os.path.join(mk1, "2026-01-01_00-00-00")
sisa = os.path.join(mk1, "2025-12-31_11-11-11")
for d in (run_new, run_old, sisa):
    os.makedirs(d, exist_ok=True)
open(os.path.join(run_new, "manifest.json"), "w").write("{}")
open(os.path.join(run_new, "a.pdf"), "wb").write(b"%PDF aman")
open(os.path.join(run_old, "manifest.json"), "w").write("{}")
open(os.path.join(run_old, "b.pdf"), "wb").write(b"%PDF lama")
open(os.path.join(sisa, "c.pdf"), "wb").write(b"%PDF sisa tanpa manifest")
with open(os.path.join(tmp, "outp", "latest_run.json"), "w") as f:
    json.dump({"latest_directory": run_new}, f)

EO_BACKUP, EO_OUTPUT, EO_BASE = EO.BACKUP_DIR, EO.OUTPUT_DIR, EO.BASE_DIR
EO.BACKUP_DIR = os.path.join(tmp, "backup")
EO.OUTPUT_DIR = os.path.join(tmp, "outp")
EO.BASE_DIR = tmp
EO.LEGACY_DIR = os.path.join(tmp, "generated_pdfs")
_hasil = EO.rapikan(arsipkan_lama=True)
check("rapikan: run terbaru SELAMAT di tempatnya",
      os.path.isfile(os.path.join(run_new, "a.pdf")))
check("rapikan: run lama pindah ke backup",
      not os.path.isdir(run_old) and
      any(f["dari"].endswith("2026-01-01_00-00-00") for f in _hasil["dipindah"]))
check("rapikan: sisa tanpa manifest ikut diarsipkan",
      not os.path.isdir(sisa) and
      _hasil.get("dipindah_sisa_tanpa_manifest", 0) >= 1)
check("rapikan: lapis kirim kaprodi + wali dibuat",
      os.path.isfile(os.path.join(EO.OUTPUT_DIR, "kirim", "kaprodi",
                                  "manifest.json")) and
      os.path.isfile(os.path.join(EO.OUTPUT_DIR, "kirim", "wali",
                                  "manifest.json")))
man_k = json.load(open(os.path.join(EO.OUTPUT_DIR, "kirim", "kaprodi",
                                    "manifest.json"), encoding="utf-8"))
check("rapikan: manifest kaprodi merujuk run terbaru",
      man_k["sumber_run"].endswith("2026-01-02_00-00-00"), man_k["sumber_run"])

man_wali = json.load(open(os.path.join(EO.OUTPUT_DIR, "kirim", "wali",
                                       "manifest.json"), encoding="utf-8"))
check("rapikan: manifest wali = SEMUA mahasiswa tree (bug #4)",
      man_wali.get("total_mahasiswa") == 3 and
      "2510015410001" in man_wali["mahasiswa"] and
      "2510015410010" in man_wali["mahasiswa"],
      str(man_wali.get("total_mahasiswa")))
check("rapikan: manifest wali bawa nama & status jujur",
      man_wali["mahasiswa"]["2510015410001"]["nama"] == "MAHASISWA SATU" and
      man_wali["mahasiswa"]["2510015410001"]["catatan"] != "",
      man_wali["mahasiswa"]["2510015410001"]["catatan"][:30])

# --- [C] sapu brokat root output -------------------------------------------
stray_pdf = os.path.join(EO.OUTPUT_DIR, "stray_root_test.pdf")
stray_html = os.path.join(EO.OUTPUT_DIR, "stray_root_test.html")
open(stray_pdf, "wb").write(b"%PDF-1.4 stray")
open(stray_html, "w").write("<html></html>")
hasil_root = EO.rapikan(arsipkan_lama=False)
check("rapikan: brokat root pindah ke _backup (bug #8)",
      sorted(hasil_root["dipindah_root"]) ==
      ["stray_root_test.html", "stray_root_test.pdf"] and
      not os.path.isfile(stray_pdf), str(hasil_root["dipindah_root"]))
check("rapikan: latest_run.json TIDAK ikut disapu",
      os.path.isfile(os.path.join(EO.OUTPUT_DIR, "latest_run.json")))
check("rapikan: sisa root tersisa (audit)",
      EO.audit()["ringkasan"]["sisa_root"] == 0)

# restore konstanta supaya modul tetap aman kalau diimpor lagi
EO.BACKUP_DIR, EO.OUTPUT_DIR, EO.BASE_DIR = EO_BACKUP, EO_OUTPUT, EO_BASE
EO.KURIKULUM_DIR = os.path.join(EO_BASE, "data", "kurikulum")

# bersih-bersih sandbox
shutil.rmtree(tmp, ignore_errors=True)

print()
print("SEMUA LULUS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)

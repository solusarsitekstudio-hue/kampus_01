"""test_parse_stempel.py - Tangga A + B: kompilasi master ber-stempel per-MK.

Dijaga (keputusan user 2026-10-21, zona optimasi 1):
1. Stempel sumber master DETERMINISTIK (dipanggil dua kali = sama) dan
   BEDA antar MK (kunci >= folder tree + identitas per MK).
2. Jalur SEGAR: stempel sama + snapshot ada -> subprocess parse_data
   BERAKHIR CEPAT (< 5 s) dan mencetak tanda "masih SEGAR" + salinan
   bit-identik snapshot, BUKAN kompilasi 12 detik.
3. Jalur PAKSA (--compile-ulang): kompilasi penuh berjalan, master ditulis,
   snapshot + stempel diperbarui (selesai ~12 s, timeout 180 s).

Catatan jujur: test ini menyentuh berkas server data NYATA (master dipindah-
tahkan oleh build deterministik-nya sendiri), tapi tidak pernah menulis
tree/aturan/identitas - sumber kebenaran tidak disentuh.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(HERE, "scripts")
PARSE = os.path.join(SCRIPTS, "parse_data.py")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:56} {detail}")


print("=" * 82)
print("TEST: KOMPILASI MASTER BER-STEMPEL (Tangga A + B)")
print("=" * 82)

sys.path.insert(0, SCRIPTS)
import parse_data as PD  # noqa: E402

# ------------------------------------------------------------- 1. determinisme
k1, s1 = PD.stempel_kompilasi()
k2, s2 = PD.stempel_kompilasi()
check("stempel: dipanggil 2x = deterministik", s1 == s2)
check("stempel: kunci aktif teridentifikasi", bool(k1 and s1), k1)

k_lain = "STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1"
try:
    _k3, s3 = PD.stempel_kompilasi(k_lain)
    check("stempel: MK lain = stamp beda", s3 != s1 and _k3 == k_lain)
except Exception as e:  # noqa: BLE001
    check("stempel: MK lain = stamp beda", False, f"gagal hitung MK lain: {e}")

# reg stempel harus atomik & pembacaan rusak ->kosong (fail-closed)
# (isi registry asli disimpan & dipulihkan - jangan menghapus stamp kunci
#  aktif, nanti jalur segar di bawah justru jadi basi palsu)
REG_ASLI = PD.STAMPEL_PATH
with open(REG_ASLI, "r", encoding="utf-8") as f:
    REG_BACKUP = f.read()
PD.tulis_reg_stempel({"x": {"stamp": "abc"}})
check("reg stempel: tulis->muat konsisten", PD.muat_reg_stempel().get(
    "x", {}).get("stamp") == "abc")
bad = REG_ASLI + ".tmp"
with open(bad, "w", encoding="utf-8") as f:
    f.write("{rusak!!")
PD.STAMPEL_PATH = bad
check("reg stempel: berkas rusak -> fail-closed {}",
      PD.muat_reg_stempel() == {})
PD.STAMPEL_PATH = REG_ASLI  # pulihkan pointer modul
os.remove(bad)
with open(REG_ASLI, "w", encoding="utf-8", newline="\n") as f:
    f.write(REG_BACKUP)  # pulihkan isi registry asli

# ------------------------------------------------- 2. jalur segar (Tangga B)
t0 = time.perf_counter()
h1 = subprocess.run([sys.executable, PARSE], cwd=HERE, capture_output=True,
                    text=True, encoding="utf-8", errors="replace", timeout=60)
dur1 = time.perf_counter() - t0
fresh = "masih SEGAR" in (h1.stdout or "") and "salinan bit-identik" in (
    h1.stdout or "")
check("jalur segar: stempel sama -> salin, BUKAN kompilasi", fresh
      and h1.returncode == 0,
      f"{dur1:.1f}s rc={h1.returncode}")
check("jalur segar: cepat (< 5 s, bukan 12 s)", dur1 < 5.0, f"{dur1:.1f}s")

# ------------------------------------------------ 3. jalur paksa (--compile-ulang)
t0 = time.perf_counter()
h2 = subprocess.run([sys.executable, PARSE, "--compile-ulang"], cwd=HERE,
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=180)
dur2 = time.perf_counter() - t0
full = "dikompilasi & snapshot disimpan" in (h2.stdout or "")
check("jalur paksa: kompilasi penuh -> snapshot + stempel diperbarui",
      full and h2.returncode == 0, f"{dur2:.1f}s rc={h2.returncode}")
# setelah paksa, stempel harus kembali segar
_k, stamp_sesudah = PD.stempel_kompilasi()
reg = PD.muat_reg_stempel()
check("jalur paksa: stempel registry sinkron lagi",
      reg.get(_k, {}).get("stamp") == stamp_sesudah)

print()
print("SEMUA LULUS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)

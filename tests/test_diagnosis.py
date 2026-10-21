"""tes diagnosis.py v3 - klasifikasi & radar dari SINYAL NYATA (bukan NPM).

Kasus utama:
* Kontradiksi lama (ULYA-like: alpha 2x + hadir rendah -> HARUS at_risk,
  BUKAN "KOMPETENSI STABIL" seperti versi persona NPM).
* Deterministik tanpa RNG (sinyal sama -> tanda sama).
* Fail-closed data belum lengkap -> belum_lengkap, radar berlabel estimasi.
* Matriks karier: skema lama utuh, kecocokan dari profil, tanpa angka RNG.
* persona.py TIDAK boleh rusak (dipakai seed pipeline) - diuji sekilas.
"""

import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:56} {detail}")


print("=" * 82)
print("TEST DIAGNOSIS V3 - SINYAL NYATA")
print("=" * 82)

import diagnosis as DIAG  # noqa: E402
import persona as PS  # noqa: E402

# --------------------------------------------------------------------------- #
print("\n[1] Kontradiksi lama dibunuh: alpha 2x + hadir rendah -> at_risk")
arc, radar, ai, meta = DIAG.hasil(
    "ULYA", 74.0, 68.8, 2, [80, 70, 75, 65, 72], nama_mk="ARS101")
check("archetype = at_risk", arc == "at_risk", arc)
check("status konsisten dengan badge", ai["status_alert"] == "POTENSI BESAR BUTUH PENDAMPINGAN",
      ai["status_alert"])
check("alert_color rose (bukan biru generik)", ai["alert_color"] == "rose", ai["alert_color"])
check("narasi menyebut angka bukti", "68.8%" in ai["analisis_karakter_spasial"], "")
check("radar disiplin = kehadiran nyata", radar["kedisiplinan_asistensi"] == 69,
      radar["kedisiplinan_asistensi"])

# --------------------------------------------------------------------------- #
print("\n[2] Klasifikasi penuh dari sinyal")
def klas(nilai, pct, alpha, skor):
    return DIAG.klasifikasi(DIAG.sinyal(nilai, pct, alpha, skor))

check("star (92/95, konsisten)", klas(92.0, 95.0, 0, [90, 91, 93, 92, 94]) == "star")
check("high (82/87)", klas(82.0, 87.0, 0, [85, 80, 84, 82]) == "high")
check("nilai rendah tapi hadir baik -> perlu_penguatan",
      klas(65.0, 88.0, 0, [70, 60, 68, 62]) == "perlu_penguatan")
check("alpha 1 -> moderate_absent", klas(78.0, 90.0, 1, [80, 78, 82, 76]) == "moderate_absent")
check("normal (75/80)", klas(75.0, 80.0, 0, [76, 74, 77, 75]) == "normal")
check("belum lengkap -> belum_lengkap",
      DIAG.klasifikasi(DIAG.sinyal(72.0, None, 0, [80, None], data_lengkap=False)) == "belum_lengkap")

# --------------------------------------------------------------------------- #
print("\n[3] Deterministik tanpa RNG")
a = DIAG.hasil("X", 80.0, 87.0, 0, [85, 80, 82, 84])
b = DIAG.hasil("X", 80.0, 87.0, 0, [85, 80, 82, 84])
check("tanda sinyal sama", a[3]["tanda_sinyal"] == b[3]["tanda_sinyal"],
      f"{a[3]['tanda_sinyal']}")
check("narasi identik byte-per-byte", a[2] == b[2], "")
c = DIAG.hasil("X", 90.0, 95.0, 0, [90, 91, 92, 93, 94])
check("sinyal beda -> tanda beda", c[3]["tanda_sinyal"] != a[3]["tanda_sinyal"], "")

# --------------------------------------------------------------------------- #
print("\n[4] Radar terukur dengan label jujur")
_, radar_a, _, _ = DIAG.hasil("A", 80.0, 80.0, 0, [85, 80, 82, 84, 76])
_, radar_b, _, _ = DIAG.hasil("B", 80.0, 95.0, 0, [85, 80, 82, 84, 76])
check("disiplin naik saat kehadiran naik",
      radar_b["kedisiplinan_asistensi"] > radar_a["kedisiplinan_asistensi"], "")
check("semua dim ada sumbernya",
      all(v in ("terukur", "estimasi") for v in a[2]["radar_sumber"].values()), "")
check("penguasaan = nilai terbobot", radar_a["penguasaan_cad"] == 80,
      radar_a["penguasaan_cad"])

# --------------------------------------------------------------------------- #
print("\n[5] Matriks karier: skema lama utuh, peringkat dari profil")
top = a[2]["matriks_karier_10"]
kunci_wajib = {"id", "profesi", "bidang_industri", "kecocokan_persen",
               "kategori_kecocokan", "analisis_potensi", "keterampilan_kunci",
               "saran_pengembangan"}
check("10 karier", len(top) == 10, len(top))
check("skema item utuh untuk PDF/video", all(kunci_wajib <= set(c) for c in top), "")
check("urut kecocokan menurun",
      all(top[i]["kecocokan_persen"] >= top[i + 1]["kecocokan_persen"] for i in range(9)), "")
check("tidak ada 100% pasti (cap aktif)",
      all(c["kecocokan_persen"] < 100 for c in top), "")
check("profil kuat -> kecocokan tinggi",
      DIAG.hasil("S", 95.0, 98.0, 0, [95, 94, 96, 95, 97])[2]
      ["matriks_karier_10"][0]["kecocokan_persen"] >= 90, "")

# --------------------------------------------------------------------------- #
print("\n[6] persona.py tidak tersentuh (generator nilai sintetis tetap jalan)")
check("rng_untuk masih deterministik",
      PS.rng_untuk("2510015410010", "ARS101").random()
      == PS.rng_untuk("2510015410010", "ARS101").random(), "")
check("tentukan_archetype masih dari NPM",
      PS.tentukan_archetype(0, "2510015410010", "ARS101") == "star",
      PS.tentukan_archetype(0, "2510015410010", "ARS101"))

print()
print("SEMUA LULUS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)

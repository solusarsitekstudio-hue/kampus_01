"""TES: aturan akademik sekarang HIDUP DI CONFIG, bukan dipaku di kode.

Jalankan TANPA server:  python tests\\test_aturan.py

Yang dibuktikan:
  1. config/aturan.json ada, valid, dan angkanya SAMA dengan angka lama.
  2. Memindahkan aturan dari kode ke config TIDAK mengubah hasil apa pun.
  3. Aturan kehadiran (slot vs pertemuan) berjalan sesuai keputusan.
  4. Config rusak DITOLAK (fail-closed), bukan diam-diam dipakai.
  5. Mengubah angka di config benar-benar mengubah hasil.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import aturan as AT  # noqa: E402
import kelas_rules as KR  # noqa: E402

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


print("=" * 72)
print("TES ATURAN: satu sumber yang bisa diatur (config/aturan.json)")
print("=" * 72)

cfg = AT.muat(force=True)
check("config/aturan.json terbaca", isinstance(cfg, dict))
check("config valid", AT.validasi(cfg) == [], str(AT.validasi(cfg))[:80])

print("\n1. Angka default = angka lama (tidak ada perubahan hasil)")
check("at_risk alpha_min = 2", AT.nilai_aturan("alpha_min") == 2, str(AT.nilai_aturan("alpha_min")))
check("at_risk kehadiran_min = 75.0", AT.nilai_aturan("kehadiran_min") == 75.0,
      str(AT.nilai_aturan("kehadiran_min")))
check("teks at-risk = teks lama", AT.teks_at_risk() == "Alpha >= 2x ATAU Kehadiran < 75%",
      AT.teks_at_risk())
check("jam teori 50 / studio 120",
      AT.jam_untuk("teori") == 50 and AT.jam_untuk("studio") == 120,
      f"{AT.jam_untuk('teori')} / {AT.jam_untuk('studio')}")
check("standar 16 pertemuan, UTS 8, UAS 16",
      AT.pertemuan_total() == 16 and AT.pertemuan_ujian() == {"uts": 8, "uas": 16},
      f"{AT.pertemuan_total()} {AT.pertemuan_ujian()}")
b = AT.standar_kampus()["bobot_template"]
check("bobot template -> total 100",
      b["per_pertemuan"] * 14 + b["uts"] + b["uas"] == 100, str(b))

print("\n2. Grade & at-risk lewat kelas_rules masih sama seperti sebelumnya")
check("grade 90/85 -> A", KR.grade_dari_skor(90, 85)[0] == "A", KR.grade_dari_skor(90, 85))
check("grade 80/75 -> A-", KR.grade_dari_skor(80, 75)[0] == "A-", KR.grade_dari_skor(80, 75))
check("grade 70 -> B", KR.grade_dari_skor(70, 90)[0] == "B", KR.grade_dari_skor(70, 90))
check("grade 59 -> D / Evaluasi", KR.grade_dari_skor(59, 90)[0] == "D / Evaluasi",
      KR.grade_dari_skor(59, 90))
check("nilai 85 tapi hadir 70 -> tidak dapat A", KR.grade_dari_skor(85, 70)[0] != "A",
      KR.grade_dari_skor(85, 70))
check("alpha 2 -> at-risk", KR.is_at_risk(2, 90.0) is True, str(KR.at_risk_reasons(2, 90.0)))
check("hadir 74.9 -> at-risk", KR.is_at_risk(0, 74.9) is True, str(KR.at_risk_reasons(0, 74.9)))
check("alpha 1 & hadir 75 -> aman", KR.is_at_risk(1, 75.0) is False, str(KR.at_risk_reasons(1, 75.0)))
check("teks grade ada untuk semua ambang config",
      all(g["grade"] in KR.TEKS_GRADE for g in AT.grade_bounds()),
      str([g["grade"] for g in AT.grade_bounds() if g["grade"] not in KR.TEKS_GRADE]))

print("\n3. Kehadiran: tampilan pertemuan, persen berbasis slot (keputusan user)")
check("2 dari 4 slot -> pertemuan memenuhi ambang", KR.pertemuan_memenuhi_ambang(2, 4) is True)
check("1 dari 4 slot -> belum memenuhi ambang", KR.pertemuan_memenuhi_ambang(1, 4) is False)
check("2 dari 2 slot -> memenuhi ambang", KR.pertemuan_memenuhi_ambang(2, 2) is True)
check("0 slot -> tidak memenuhi (tanpa pembagian nol)",
      KR.pertemuan_memenuhi_ambang(0, 0) is False)
check("persen slot jujur: 1/4 = 25%", KR.persentase_kehadiran(1, 4) == 25.0,
      str(KR.persentase_kehadiran(1, 4)))
check("label jujur: 1/4 -> Hadir Sebagian", KR.status_pertemuan(1, 4) == "Hadir Sebagian",
      KR.status_pertemuan(1, 4))
check("label jujur: 0/4 -> Alpha", KR.status_pertemuan(0, 4) == "Alpha")
# DUA ukuran "hadir" memang boleh berbeda, tetapi harus tetap berbeda arti:
# 2 dari 4 slot = memenuhi ambang (longgar) TAPI bukan "Hadir" penuh (ketat).
check("2/4 slot: memenuhi ambang tapi BUKAN hadir penuh",
      KR.pertemuan_memenuhi_ambang(2, 4) is True
      and KR.status_pertemuan(2, 4) == "Hadir Sebagian",
      KR.status_pertemuan(2, 4))
check("4/4 slot: kedua ukuran sepakat",
      KR.pertemuan_memenuhi_ambang(4, 4) is True
      and KR.status_pertemuan(4, 4) == "Hadir")

print("\n4. Bobot 16 pertemuan divalidasi (keputusan user: total 100)")
bobot_ok = [b["per_pertemuan"]] * 14 + [b["uts"], b["uas"]]
check("bobot 14x4+20+24 = 100 -> lolos", KR.validasi_bobot(bobot_ok) == [],
      str(KR.validasi_bobot(bobot_ok)))
check("bobot berjumlah 99 -> ditolak", any("100" in m for m in KR.validasi_bobot(bobot_ok[:-1] + [23])),
      str(KR.validasi_bobot(bobot_ok[:-1] + [23])))

print("\n5. Config rusak DITOLAK (fail-closed)")
rusak = json.loads(json.dumps(cfg))
rusak["kehadiran"]["basis_persen"] = "ngawur"
check("basis_persen ngawur -> ditolak", AT.validasi(rusak) != [], str(AT.validasi(rusak))[:70])
rusak = json.loads(json.dumps(cfg))
rusak["at_risk"]["aturan"] = [{"tipe": "entahlah", "nilai": 5}]
check("tipe aturan asing -> ditolak", AT.validasi(rusak) != [], str(AT.validasi(rusak))[:70])
rusak = json.loads(json.dumps(cfg))
del rusak["grade"]
check("grade hilang -> ditolak", AT.validasi(rusak) != [], str(AT.validasi(rusak))[:70])
rusak = json.loads(json.dumps(cfg))
rusak["kehadiran"]["min_slot_ratio_hadir"] = 3
check("min_slot_ratio di luar 0..1 -> ditolak", AT.validasi(rusak) != [],
      str(AT.validasi(rusak))[:70])
# Template bobot adalah nilai awal 16 pertemuan: kalau totalnya bukan 100, seluruh
# nilai kelas akan salah. Dulu ini baru ketahuan setelah sesi.json ditulis.
rusak = json.loads(json.dumps(cfg))
rusak["standar_kampus"]["bobot_template"]["uts"] = 30
check("template bobot total != 100 -> ditolak", AT.validasi(rusak) != [],
      str(AT.validasi(rusak))[:70])
rusak = json.loads(json.dumps(cfg))
rusak["standar_kampus"]["pertemuan_total"] = 18
check("pertemuan_total 18 tapi template tetap 16 -> ditolak", AT.validasi(rusak) != [],
      str(AT.validasi(rusak))[:70])

print("\n6. Ubah angka di config -> hasil ikut berubah (bukti aturan benar-benar hidup)")
ubah = json.loads(json.dumps(cfg))
ubah["at_risk"]["aturan"] = [{"tipe": "alpha_min", "nilai": 1}]
_old = (AT._cache["data"], AT._cache["mtime"])
AT._cache["data"] = ubah
AT._cache["mtime"] = os.path.getmtime(AT.CONFIG_PATH)
try:
    check("alpha_min 2 -> 1: alpha 1x sekarang at-risk", KR.is_at_risk(1, 90.0) is True,
          str(KR.at_risk_reasons(1, 90.0)))
finally:
    AT._cache["data"], AT._cache["mtime"] = _old
check("setelah dipulihkan: alpha 1x aman lagi", KR.is_at_risk(1, 90.0) is False)

print("\n7. Config asli tidak tersentuh tes ini")
check("config/aturan.json masih versi 1 & alpha_min 2",
      AT.muat(force=True)["at_risk"]["aturan"][0]["nilai"] == 2)

print("=" * 72)
print("HASIL: " + ("SEMUA OK" if ok else "ADA YANG GAGAL"))
print("=" * 72)
sys.exit(0 if ok else 1)

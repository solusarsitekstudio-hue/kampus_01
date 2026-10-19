"""TES: pertemuan yang presensinya BELUM DIINPUT tidak dihitung Alpha / nilai 0.

Jalankan TANPA server:  python tests\\test_belum_diinput.py

Konteks (kenapa tes ini ada):
  Dulu `ringkas_kehadiran()` menghitung nilai satu pertemuan sebagai
  `sum(skor) / slot_total`. Kalau baris slot absen belum ada (portal baru
  mengirim sebagian, atau data memang belum masuk), slot kosong itu dihitung
  NILAI 0 dan pertemuannya otomatis jadi "Alpha". Akibatnya data yang belum
  ada dihukum seperti mahasiswa tidak hadir.

Yang dibuktikan sekarang:
  1. Aturan hidup di config: `kehadiran.slot_belum_diisi` (default belum_diinput).
  2. Pertemuan dengan slot belum lengkap -> "Belum Diinput", skor None.
  3. Alpha TIDAK bertambah karenanya (0 nilai tetap dihitung seperti biasa).
  4. Sesi belum-diinput keluar dari rata-rata terbobot; bobot dinormalisasi ulang.
  5. Grade ditahan "Belum Lengkap" selama masih ada yang belum diinput.
  6. Bisa dibalik ke perilaku lama ("alpha") lewat config, tanpa ubah kode.
  7. Data nyata saat ini lengkap -> seluruh langkah ini tidak mengubah angka.
"""
import copy
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import aturan as AT  # noqa: E402
import kelas_rules as KR  # noqa: E402
import parse_data as PD  # noqa: E402

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


print("=" * 76)
print("TES: 'belum diinput' tidak lagi dihitung Alpha / nilai 0")
print("=" * 76)

print("\n1. Aturan hidup di config")
cfg = AT.muat(force=True)
check("kehadiran.slot_belum_diisi ada", "slot_belum_diisi" in cfg.get("kehadiran", {}))
check("nilainya 'belum_diinput'", AT.slot_belum_diisi() == "belum_diinput",
      AT.slot_belum_diisi())
check("config valid", AT.validasi(cfg) == [], str(AT.validasi(cfg))[:80])
rusak = copy.deepcopy(cfg)
rusak["kehadiran"]["slot_belum_diisi"] = "ngawur"
check("nilai ngawur DITOLAK (fail-closed)", AT.validasi(rusak) != [],
      str(AT.validasi(rusak))[:70])

print("\n2. status_pertemuan + helper (slot terisi vs slot seharusnya)")
check("0 dari 2 slot terisi -> Belum Diinput",
      KR.status_pertemuan(0, 2, 0) == "Belum Diinput")
check("1 dari 2 slot terisi -> Belum Diinput",
      KR.status_pertemuan(1, 2, 1) == "Belum Diinput")
check("2 dari 2 lengkap & hadir -> Hadir", KR.status_pertemuan(2, 2, 2) == "Hadir")
check("2 dari 2 lengkap tapi 1 hadir -> Hadir Sebagian",
      KR.status_pertemuan(1, 2, 2) == "Hadir Sebagian")
check("tanpa slot_terisi (pemanggil lama) -> tetap Alpha (kompatibel)",
      KR.status_pertemuan(0, 2) == "Alpha")
check("pertemuan_belum_diinput(1,2) True", KR.pertemuan_belum_diinput(1, 2) is True)
check("pertemuan_belum_diinput(2,2) False", KR.pertemuan_belum_diinput(2, 2) is False)
check("pertemuan tanpa slot (0,0) bukan belum-diinput",
      KR.pertemuan_belum_diinput(0, 0) is False)

print("\n3. Nilai: sesi None dikeluarkan, bobot dinormalisasi; Alpha tetap dihitung")
check("None dibuang, bobot dinormalisasi -> 85.0",
      KR.hitung_nilai_terbobot([80, None, 90], [4, 20, 4]) == 85.0,
      str(KR.hitung_nilai_terbobot([80, None, 90], [4, 20, 4])))
check("cakupan bobot kebaca -> 28.6% (bukan 100)",
      KR.cakupan_bobot([80, None, 90], [4, 20, 4]) == 28.6,
      str(KR.cakupan_bobot([80, None, 90], [4, 20, 4])))
check("data lengkap -> cakupan 100.0", KR.cakupan_bobot([80, 90, 70], [4, 20, 4]) == 100.0)
check("Alpha (nilai 0) TETAP dihitung -> 24.3 (beda dari None)",
      KR.hitung_nilai_terbobot([80, 0, 90], [4, 20, 4]) == 24.3,
      str(KR.hitung_nilai_terbobot([80, 0, 90], [4, 20, 4])))
check("grade 'Belum Lengkap' punya kalimat resmi",
      KR.teks_grade(KR.GRADE_BELUM_LENGKAP)[0] != "",
      KR.teks_grade(KR.GRADE_BELUM_LENGKAP)[0])

print("\n4. ringkas_kehadiran: P1 lengkap, P2 kosong")
sessions = [
    {"pertemuan": 1, "slot_absen": ["a", "b"], "tanggal": "2026-06-03",
     "tanggal_display": "03 Juni 2026", "topik": "T1", "tipe": "teori"},
    {"pertemuan": 2, "slot_absen": ["a", "b"], "tanggal": "2026-06-10",
     "tanggal_display": "10 Juni 2026", "topik": "T2", "tipe": "studio"},
]
rows = [
    {"pertemuan": 1, "slot": 0, "status": "Hadir", "skor": 90},
    {"pertemuan": 1, "slot": 1, "status": "Hadir", "skor": 80},
    # pertemuan 2: sengaja tidak ada baris (presensi belum masuk)
]
detail, hitung, ph, sh, st = PD.ringkas_kehadiran(rows, sessions)
check("P1 tetap 'Hadir'", detail[0]["status"] == "Hadir")
check("P2 -> 'Belum Diinput'", detail[1]["status"] == "Belum Diinput",
      detail[1]["status"])
check("skor P2 = None (bukan 0)", detail[1]["skor"] is None, str(detail[1]["skor"]))
check("slot_terisi P2 = 0", detail[1]["slot_terisi"] == 0)
check("Alpha TIDAK bertambah", hitung["Alpha"] == 0, str(hitung))
check("keranjang 'Belum Diinput' = 1", hitung["Belum Diinput"] == 1)
check("P2 tidak dihitung hadir", ph == 1, str(ph))

print("\n5. Dibalik ke perilaku lama lewat config ('alpha') - tanpa ubah kode")
_old = (AT._cache["data"], AT._cache["mtime"])
ubah = copy.deepcopy(cfg)
ubah["kehadiran"]["slot_belum_diisi"] = "alpha"
AT._cache["data"] = ubah
AT._cache["mtime"] = os.path.getmtime(AT.CONFIG_PATH)
try:
    d2, h2, _, _, _ = PD.ringkas_kehadiran(rows, sessions)
    check("mode 'alpha': P2 jadi Alpha (perilaku lama)",
          d2[1]["status"] == "Alpha" and h2["Alpha"] == 1, str(d2[1]["status"]))
finally:
    AT._cache["data"], AT._cache["mtime"] = _old
d3, h3, _, _, _ = PD.ringkas_kehadiran(rows, sessions)
check("kembali 'belum_diinput': P2 Belum Diinput lagi",
      d3[1]["status"] == "Belum Diinput")

print("\n6. End-to-end dengan data nyata (satu mahasiswa kehilangan 1 pertemuan)")
ctx = PD.muat_kurikulum()
nilai_awal = PD.kelompokkan_nilai(ctx["nilai_dokumen"])
base = PD.generate_student_profiles(ctx["mahasiswa"], ctx["sessions"], nilai_awal, ctx)["students"]

# Pilih mahasiswa yang pertemuan 1-nya HADIR - biar perbedaannya jelas.
target = next(s for s in base if s["kehadiran"]["detail"][0]["status"] == "Hadir")
npm_target = target["npm"]

nilai_baru = {k: list(v) for k, v in nilai_awal.items()}
nilai_baru[npm_target] = [r for r in nilai_baru[npm_target]
                          if int(r.get("pertemuan") or 0) != 1]
hasil = PD.generate_student_profiles(
    ctx["mahasiswa"], ctx["sessions"], nilai_baru, ctx)["students"]
baru = next(s for s in hasil if s["npm"] == npm_target)

check("data_lengkap = False", baru["kehadiran"]["data_lengkap"] is False)
check("P1 jadi 'Belum Diinput'", baru["kehadiran"]["detail"][0]["status"] == "Belum Diinput",
      baru["kehadiran"]["detail"][0]["status"])
check("Alpha TIDAK bertambah vs baseline",
      baru["kehadiran"]["alpha"] == target["kehadiran"]["alpha"],
      f"{target['kehadiran']['alpha']} -> {baru['kehadiran']['alpha']}")
check("grade ditahan 'Belum Lengkap'",
      baru["akademik"]["grade"] == "Belum Lengkap", baru["akademik"]["grade"])
check("cakupan_bobot < 100%", baru["akademik"]["cakupan_bobot"] < 100,
      str(baru["akademik"]["cakupan_bobot"]))
check("nilai tetap masuk akal (bukan 0)",
      0 < baru["akademik"]["nilai_rata_rata"] < 100, str(baru["akademik"]["nilai_rata_rata"]))

# Mahasiswa lain tidak boleh terpengaruh sama sekali.
lain_base = next(s for s in base if s["npm"] != npm_target)
lain_baru = next(s for s in hasil if s["npm"] == lain_base["npm"])
check("mahasiswa lain tidak berubah",
      json.dumps(lain_base, sort_keys=True) == json.dumps(lain_baru, sort_keys=True))

print("\n7. Data nyata saat ini LENGKAP -> tidak ada angka yang berubah")
check("semua mahasiswa baseline data_lengkap True",
      all(s["kehadiran"]["data_lengkap"] for s in base))
check("tidak ada keranjang 'Belum Lengkap' pada baseline",
      all(s["akademik"]["grade"] != "Belum Lengkap" for s in base))

print("\n" + "=" * 76)
print("HASIL: " + ("SEMUA OK" if ok else "ADA YANG GAGAL"))
print("=" * 76)
sys.exit(0 if ok else 1)

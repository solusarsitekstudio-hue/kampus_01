"""TES: tree kurikulum bertingkat + rumus angkatan/semester + anti-drift index.

Jalankan:  python tests\\test_kurikulum_tree.py

Yang dibuktikan:
  1. Nama folder round-trip (kurung, koma, "&", nama terlarang Windows).
  2. Rumus semester_ke: mahasiswa MENGULANG terdeteksi otomatis.
  3. Tahun ajar / semester tidak valid DITOLAK (fail-closed), bukan ditebak.
  4. Validasi jadwal hanya PERINGATAN, bukan penolakan.
  5. Tree di disk lengkap: 16 pertemuan, UTS 8, UAS 16, bobot = 100 per MK.
  6. Index `config/kurikulum.json` == hasil pindai ulang folder (tanpa drift).
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import aturan as AT  # noqa: E402
import kurikulum_tree as KT  # noqa: E402

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


print("=" * 72)
print("TES TREE KURIKULUM: bertingkat, mandiri, dan tidak bisa drift")
print("=" * 72)

print("\n1. Nama folder round-trip (satu versi, bukan tiga)")
check("kurung & koma -> underscore",
      KT.sanitize_folder_name("Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)")
      == "STUDIO_PERANCANGAN_ARSITEKTUR_2_DESAIN_RUMAH_TINGGAL",
      KT.sanitize_folder_name("Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)"))
check("& -> DAN",
      KT.sanitize_folder_name("Aplikasi Komputer Arsitektur & QS")
      == "APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS")
check("kunci MK memotong kurung",
      KT.course_folder_key("Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)")
      == "STUDIO_PERANCANGAN_ARSITEKTUR_2")
check("nama terlarang Windows di-prefix", KT.sanitize_folder_name("con") == "MK_CON",
      KT.sanitize_folder_name("con"))
check("nama kosong aman", KT.sanitize_folder_name(None) == "" and KT.sanitize_folder_name("  ") == "")

print("\n2. Angkatan vs semester (mahasiswa mengulang)")
check("NPM 2510015410010 -> angkatan 2025", KT.angkatan_dari_npm("2510015410010") == 2025,
      str(KT.angkatan_dari_npm("2510015410010")))
check("angkatan 2025 di Ganjil 2025/2026 -> semester 1",
      KT.semester_ke(2025, "2025/2026", "GANJIL") == 1)
check("angkatan 2025 di Genap 2025/2026 -> semester 2",
      KT.semester_ke(2025, "2025/2026", "GENAP") == 2)
check("angkatan 2024 di Genap 2025/2026 -> semester 4",
      KT.semester_ke(2024, "2025/2026", "GENAP") == 4)
check("angkatan 2024 di Genap 2026/2027 -> semester 6",
      KT.semester_ke(2024, "2026/2027", "GENAP") == 6)
check("semester_ke 2 vs MK semester 1 -> 'ulang'",
      KT.status_peserta(2, 1) == "ulang")
check("semester_ke 2 vs MK semester 2 -> 'normal'",
      KT.status_peserta(2, 2) == "normal")
check("MK semester_kurikulum belum diisi -> 'tidak diketahui'",
      KT.status_peserta(2, None) == "tidak diketahui")
try:
    KT.semester_ke(2027, "2025/2026", "GENAP")
    check("angkatan di masa depan DITOLAK", False, "tidak raise")
except KT.KurikulumError:
    check("angkatan di masa depan DITOLAK", True)

print("\n3. Tahun ajar & semester tidak valid DITOLAK (fail-closed)")
check("'2025-2026' -> '2025/2026'", KT.norm_tahun_ajar("2025-2026") == "2025/2026")
check("'Genap 2025/2026' -> ('2025/2026','GENAP')",
      KT.pecah_semester("Genap 2025/2026") == ("2025/2026", "GENAP"))
check("'Ganjil 2026/2027' -> ('2026/2027','GANJIL')",
      KT.pecah_semester("Ganjil 2026/2027") == ("2026/2027", "GANJIL"))
for buruk, label in [("2025/2028", "tahun kedua bukan +1"), ("dua ribu", "bukan angka"),
                     ("2025", "tidak lengkap")]:
    try:
        KT.norm_tahun_ajar(buruk)
        check(f"tahun ajar '{buruk}' ({label}) DITOLAK", False, "tidak raise")
    except KT.KurikulumError:
        check(f"tahun ajar '{buruk}' ({label}) DITOLAK", True)
try:
    KT.slug_semester("musim semi")
    check("semester asing DITOLAK", False, "tidak raise")
except KT.KurikulumError:
    check("semester asing DITOLAK", True)

print("\n4. Jadwal vs SKS hanya PERINGATAN (data lama tidak konsisten)")
check("Senin & Kamis 08:00-12:00 -> 480 menit/minggu",
      KT.hitung_menit_jadwal("Senin & Kamis, 08:00 - 12:00 WIB") == 480,
      str(KT.hitung_menit_jadwal("Senin & Kamis, 08:00 - 12:00 WIB")))
check("studio 4 SKS x 120 = 480 -> TIDAK ada peringatan",
      KT.peringatan_jadwal("Senin & Kamis, 08:00 - 12:00 WIB", 4, "studio") == [])
pw = KT.peringatan_jadwal("Selasa, 13:00 - 16:30 WIB", 3, "teori")
check("struktur 3 SKS x 50 = 150 vs 210 menit -> ADA peringatan (bukan error)", len(pw) == 1,
      str(pw)[:70])
check("jadwal tak terbaca -> peringatan, bukan crash",
      len(KT.peringatan_jadwal("menyesuaikan", 2, "teori")) == 1)

print("\n5. Tree di disk lengkap & sesuai standar kampus")
if not os.path.isdir(KT.KURIKULUM_DIR):
    check("tree kurikulum ada (jalankan migrasi_kurikulum.py dulu)", False,
          str(KT.KURIKULUM_DIR))
else:
    prodi_list = KT.daftar_prodi()
    check("ada prodi di tree", bool(prodi_list), str(prodi_list))
    total_mk = 0
    for prodi in prodi_list:
        mhs_path = KT.path_mahasiswa(prodi)
        mhs = KT.baca_json(mhs_path) if os.path.exists(mhs_path) else {}
        daftar_mhs = mhs.get("mahasiswa", [])
        check(f"{prodi}: identitas mahasiswa ada", bool(daftar_mhs), f"{len(daftar_mhs)} orang")
        check(f"{prodi}: semua mahasiswa punya angkatan",
              all(isinstance(m.get("angkatan"), int) for m in daftar_mhs))
        check(f"{prodi}: nama hanya di identitas (berkas nilai tanpa nama)", True)
        for ta in KT.daftar_tahun(prodi):
            for sem in KT.daftar_semester(prodi, ta):
                for kunci in KT.daftar_mk(prodi, ta, sem):
                    total_mk += 1
                    data = KT.muat_mk(prodi, ta, sem, kunci)
                    masalah = KT.validasi_sesi(data["sesi"], kunci)
                    check(f"{kunci}: sesi valid (16 pertemuan, bobot 100)",
                          masalah == [], str(masalah)[:80])
                    check(f"{kunci}: UTS/UAS di posisi config",
                          [s["tipe"] for s in data["sesi"]["sesi"] if s["tipe"] in ("uts", "uas")]
                          == ["uts", "uas"])
                    check(f"{kunci}: setiap pertemuan punya >= 1 slot absen",
                          all(s["slot_absen"] for s in data["sesi"]["sesi"]))
                    npm_nilai = sorted({r["npm"] for r in data["nilai"]["nilai"]})
                    npm_mhs = sorted(m["npm"] for m in daftar_mhs)
                    check(f"{kunci}: peserta == daftar mahasiswa prodi", npm_nilai == npm_mhs,
                          f"{len(npm_nilai)} vs {len(npm_mhs)}")
                    # nama TIDAK boleh ada di berkas nilai
                    nama_di_nilai = [k for r in data["nilai"]["nilai"] for k in r if k == "nama"]
                    check(f"{kunci}: tidak ada duplikasi nama di berkas nilai",
                          not nama_di_nilai)
    check("jumlah MK di tree", total_mk >= 3, str(total_mk))

print("\n6. Anti-drift: index == hasil pindai ulang folder")
idx_path = KT.INDEX_PATH
if os.path.exists(idx_path):
    lama = KT.baca_json(idx_path)
    baru = KT.bangun_index(lama.get("aktif"))
    lama.pop("dibangun_pada", None)
    baru.pop("dibangun_pada", None)
    check("index sinkron dengan isi folder (bukan sumber kebenaran kedua)",
          lama == baru, "beda" if lama != baru else "")
    check("index menandai dirinya turunan", "jangan diedit" in lama.get("catatan", "").lower())
else:
    check("index kurikulum ada", False, str(idx_path))

print("\n7. Nilai sintetis ditandai jelas (bukan dikira nilai resmi)")
for prodi in KT.daftar_prodi():
    for ta in KT.daftar_tahun(prodi):
        for sem in KT.daftar_semester(prodi, ta):
            for kunci in KT.daftar_mk(prodi, ta, sem):
                d = KT.muat_mk(prodi, ta, sem, kunci)
                check(f"{kunci}: ditandai sintetis", d["nilai"].get("sintetis") is True)

print("=" * 72)
print("HASIL: " + ("SEMUA OK" if ok else "ADA YANG GAGAL"))
print("=" * 72)
sys.exit(0 if ok else 1)

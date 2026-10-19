"""TES: `migrasi_kurikulum.py --force` TIDAK menimpa hasil edit dashboard.

Jalankan TANPA server:  python tests\\test_migrasi_non_destruktif.py

Konteks (kenapa tes ini ada):
  `--force` dulu menulis ulang SELURUH isi tree:
    * bobot tiap pertemuan dikembalikan ke template (suntingan kaprodi hilang),
    * jenis_mk & semester_kurikulum dikembalikan ke tebakan mesin
      ("tebakan-awal-dari-nama-dan-ruang"), walau kaprodi sudah mengonfirmasi,
    * nilai.json ditimpa nilai sintetis baru.
  Jadi hanya untuk "merapikan struktur", pekerjaan manusia ikut terhapus.

Yang dibuktikan sekarang:
  1. Helper: bobot/slot dari tree dibaca dan dibatasi ke rentang wajar.
  2. `sudah_dikonfirmasi()` membedakan nilai manusia ("dikonfirmasi-dashboard")
     dari tebakan mesin ("...tebakan...").
  3. `bangun_sesi()` mempertahankan bobot + slot absen hanya bila barisnya
     berasal dari tree (`pertahankan_suntingan=True`).
  4. INTEGRASI: `migrasi_kurikulum.py --force` dijalankan sungguhan pada tree
     yang sengaja disunting, lalu dibuktikan semua suntingan bertahan,
     nilai.json byte-identik, dan cetak biru + index ikut mencatat nilai
     terkonfirmasi. Setelah tes, tree dipulihkan byte-per-byte dari snapshot.
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import aturan as AT  # noqa: E402
import identitas as IDENT  # noqa: E402
import kurikulum_tree as KT  # noqa: E402
import migrasi_kurikulum as MG  # noqa: E402
import parse_data as PD  # noqa: E402

ok = True
PERINGATAN_PULIH = []


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


def hash_tree():
    """Hash deterministik seluruh tree kurikulum + index. Bukti byte-identik."""
    target = [os.path.join(KT.KURIKULUM_DIR, d) for d in KT.daftar_prodi()]
    berkas = []
    for root in target:
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                p = os.path.join(dirpath, f)
                berkas.append(p)
    if os.path.exists(KT.INDEX_PATH):
        berkas.append(KT.INDEX_PATH)
    h = hashlib.sha256()
    for p in sorted(berkas):
        rel = os.path.relpath(p, HERE).replace("\\", "/")
        h.update(rel.encode("utf-8"))
        with open(p, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest(), sorted(berkas)


print("=" * 76)
print("TES: migrasi --force tidak menimpa hasil edit dashboard")
print("=" * 76)

# ---------------------------------------------------------------------------
print("\n1. Helper preservasi")
check("bobot_lama() angka wajar -> dipakai", MG.bobot_lama({"bobot": 7}) == 7)
check("bobot_lama() kosong -> None", MG.bobot_lama({}) is None)
check("bobot_lama() tidak masuk akal -> None", MG.bobot_lama({"bobot": "x"}) is None)
check("bobot_lama() di luar 0..100 -> None", MG.bobot_lama({"bobot": 400}) is None)
check("slot_absen_lama() daftar dict -> dipakai",
      len(MG.slot_absen_lama({"slot_absen": [{"slot": 1}, {"slot": 2}, {"slot": 3}]}) or []) == 3)
check("slot_absen_lama() kosong -> None", MG.slot_absen_lama({"slot_absen": []}) is None)
check("slot_absen_lama() bentuk rusak -> None", MG.slot_absen_lama({"slot_absen": "dua"}) is None)
check("baca_json_aman() berkas tidak ada -> None",
      MG.baca_json_aman(os.path.join(HERE, "tidak-ada-ini.json")) is None)

konfirm = {"jenis_mk": "studio", "sumber_jenis_mk": "dikonfirmasi-dashboard"}
tebakan = {"jenis_mk": "studio", "sumber_jenis_mk": "tebakan-awal-dari-nama-dan-ruang"}
check("sudah_dikonfirmasi() -> True untuk dikonfirmasi-dashboard",
      MG.sudah_dikonfirmasi(konfirm, "jenis_mk", "sumber_jenis_mk") is True)
check("sudah_dikonfirmasi() -> False untuk tebakan",
      MG.sudah_dikonfirmasi(tebakan, "jenis_mk", "sumber_jenis_mk") is False)
check("sudah_dikonfirmasi() -> False kalau sumber kosong",
      MG.sudah_dikonfirmasi({"jenis_mk": "studio", "sumber_jenis_mk": ""},
                            "jenis_mk", "sumber_jenis_mk") is False)
check("pilih_nilai() pilih nilai manusia",
      MG.pilih_nilai("teori", "tebakan-x", konfirm, "jenis_mk", "sumber_jenis_mk")
      == ("studio", "dikonfirmasi-dashboard"))
check("pilih_nilai() jatuh ke tebakan kalau belum dikonfirmasi",
      MG.pilih_nilai("teori", "tebakan-x", tebakan, "jenis_mk", "sumber_jenis_mk")
      == ("teori", "tebakan-x"))

# ---------------------------------------------------------------------------
print("\n2. bangun_sesi(): pertahankan suntingan hanya dari tree")
ujian = AT.pertemuan_ujian()
total = AT.pertemuan_total()
bobot_t = AT.standar_kampus()["bobot_template"]
sesi_lama = []
for i in range(1, total + 1):
    sesi_lama.append({
        "pertemuan": i,
        "tipe": "teori",
        "tanggal": "2026-06-03",
        "topik": "Topik lama P{0}".format(i),
        "deskripsi": "desk",
        "bobot": 9 if i == 1 else (1 if i == 2 else 98 // (total - 2)),
        "slot_absen": [{"slot": 1, "label": "A1"}, {"slot": 2, "label": "A2"},
                       {"slot": 3, "label": "A3"}],
    })
# pastikan total bobot lama = 100 supaya validasi sesi lolos
bobot_manual = {1: 5, 2: 3}
for i in range(3, total + 1):
    bobot_manual[i] = (100 - 5 - 3) // (total - 2)
sisa = 100 - sum(bobot_manual.values())
if sisa:
    bobot_manual[3] += sisa
for s in sesi_lama:
    s["bobot"] = bobot_manual[s["pertemuan"]]

penawaran = {"jenis_mk": "teori"}
doc_dari_tree = MG.bangun_sesi("DUMMY", penawaran, sesi_lama, ujian,
                               pertahankan_suntingan=True)
doc_bukan_tree = MG.bangun_sesi("DUMMY", penawaran, sesi_lama, ujian,
                                pertahankan_suntingan=False)
p1_tree = doc_dari_tree["sesi"][0]
p1_bukan = doc_bukan_tree["sesi"][0]
check("dari tree: bobot P1 (5) dipertahankan", p1_tree["bobot"] == 5, str(p1_tree["bobot"]))
check("dari tree: bobot P2 (3) dipertahankan", doc_dari_tree["sesi"][1]["bobot"] == 3)
check("dari tree: 3 slot P1 dipertahankan", len(p1_tree["slot_absen"]) == 3)
check("dari tree: topik lama tetap dipakai", p1_tree["topik"] == "Topik lama P1")
check("BUKAN dari tree: bobot kembali ke template",
      p1_bukan["bobot"] == bobot_t["per_pertemuan"], str(p1_bukan["bobot"]))
check("BUKAN dari tree: slot kembali ke default 2", len(p1_bukan["slot_absen"]) == 2)
check("BUKAN dari tree: topik lama tetap dipakai", p1_bukan["topik"] == "Topik lama P1")
check("total bobot dokumen dari tree tetap 100",
      abs(sum(s["bobot"] for s in doc_dari_tree["sesi"]) - 100) < 0.001)
check("validasi_sesi() lolos untuk dokumen dari tree",
      KT.validasi_sesi(doc_dari_tree, "DUMMY") == [])

# ---------------------------------------------------------------------------
print("\n3. INTEGRASI: jalankan migrasi --force pada tree yang disunting")

prodi = IDENT.institusi().get("prodi", "")
kunci = IDENT.mk_aktif()
ta, sem = KT.pecah_semester(IDENT.mk(kunci).get("semester"))
path_penawaran = KT.path_berkas(prodi, ta, sem, kunci, "penawaran.json")
path_sesi = KT.path_berkas(prodi, ta, sem, kunci, "sesi.json")
path_nilai = KT.path_berkas(prodi, ta, sem, kunci, "nilai.json")

stempel = datetime.now().strftime("%Y%m%d_%H%M%S")
snap = os.path.join(HERE, "data", "_backup", "migrasi_test_{0}".format(stempel))
snap_tree = os.path.join(snap, "kurikulum")
snap_index = os.path.join(snap, "config_kurikulum.json")
os.makedirs(snap, exist_ok=True)

baseline_hash, berkas_awal = hash_tree()
shutil.copytree(KT.KURIKULUM_DIR, snap_tree)
shutil.copy2(KT.INDEX_PATH, snap_index)
print("  snapshot: {0} berkas -> {1}".format(len(berkas_awal), os.path.relpath(snap, HERE)))

try:
    # --- buat "suntingan dashboard" buatan ---
    sesi_dok = KT.baca_json(path_sesi)
    by_p = {int(s["pertemuan"]): s for s in sesi_dok["sesi"]}
    bobot_template = bobot_t["per_pertemuan"]
    # P1 naik, P2 turun -> total tetap 100 (dulu keduanya direset ke 4).
    by_p[1]["bobot"] = bobot_template + 1
    by_p[2]["bobot"] = bobot_template - 1
    by_p[3]["slot_absen"] = [{"slot": j + 1, "label": "Absen {0}".format(j + 1)}
                             for j in range(3)]
    topik_mark = "SUNTIKAN-TES: topik hasil edit dashboard"
    by_p[4]["topik"] = topik_mark
    sesi_dok["sesi"] = [by_p[i] for i in sorted(by_p)]
    KT.tulis_json(path_sesi, sesi_dok)

    pw = KT.baca_json(path_penawaran)
    tebakan_mesin = MG.tebak_jenis_mk(kunci, IDENT.mk(kunci))
    jenis_konfirm = "studio" if tebakan_mesin != "studio" else "teori"
    pw["jenis_mk"] = jenis_konfirm
    pw["sumber_jenis_mk"] = "dikonfirmasi-dashboard"
    pw["semester_kurikulum"] = 7
    pw["sumber_semester_kurikulum"] = "dikonfirmasi-dashboard"
    KT.tulis_json(path_penawaran, pw)

    nilai_hash_sebelum = hashlib.sha256(open(path_nilai, "rb").read()).hexdigest()

    # --- jalankan migrasi sungguhan ---
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "scripts", "migrasi_kurikulum.py"), "--force"],
        cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    check("migrasi --force keluar dengan kode 0", proc.returncode == 0,
          (proc.stdout or "")[-300:] + (proc.stderr or "")[-200:])

    # --- bukti suntingan bertahan ---
    sesi_baru = KT.baca_json(path_sesi)
    by_p2 = {int(s["pertemuan"]): s for s in sesi_baru["sesi"]}
    check("bobot P1 (suntingan) bertahan", by_p2[1]["bobot"] == bobot_template + 1,
          str(by_p2[1]["bobot"]))
    check("bobot P2 (suntingan) bertahan", by_p2[2]["bobot"] == bobot_template - 1,
          str(by_p2[2]["bobot"]))
    check("3 slot absen P3 bertahan", len(by_p2[3]["slot_absen"]) == 3)
    check("topik suntingan P4 bertahan", by_p2[4]["topik"] == topik_mark)
    check("total bobot tetap 100",
          abs(sum(s["bobot"] for s in sesi_baru["sesi"]) - 100) < 0.001)

    pw_baru = KT.baca_json(path_penawaran)
    check("jenis_mk terkonfirmasi bertahan", pw_baru["jenis_mk"] == jenis_konfirm,
          "{0} (tebakan mesin: {1})".format(pw_baru["jenis_mk"], tebakan_mesin))
    check("sumber_jenis_mk tetap 'dikonfirmasi-dashboard'",
          pw_baru["sumber_jenis_mk"] == "dikonfirmasi-dashboard",
          str(pw_baru.get("sumber_jenis_mk")))
    check("tidak ada 'tebakan_jenis_mk' yang ditulis ulang",
          "tebakan_jenis_mk" not in pw_baru)
    check("semester_kurikulum terkonfirmasi bertahan",
          pw_baru.get("semester_kurikulum") == 7, str(pw_baru.get("semester_kurikulum")))
    check("sumber_semester_kurikulum tetap 'dikonfirmasi-dashboard'",
          pw_baru.get("sumber_semester_kurikulum") == "dikonfirmasi-dashboard")

    nilai_hash_sesudah = hashlib.sha256(open(path_nilai, "rb").read()).hexdigest()
    check("nilai.json BYTE-IDENTIK (tidak ditimpa)",
          nilai_hash_sebelum == nilai_hash_sesudah,
          nilai_hash_sebelum[:12] + " vs " + nilai_hash_sesudah[:12])

    cb = KT.baca_json(KT.path_cetak_biru(prodi))
    cb_mk = next((c for c in cb.get("mata_kuliah", []) if c["kunci_mk"] == kunci), {})
    check("cetak_biru: jenis_mk terkonfirmasi ikut tercatat",
          cb_mk.get("jenis_mk") == jenis_konfirm and
          cb_mk.get("sumber_jenis_mk") == "dikonfirmasi-dashboard",
          str(cb_mk.get("jenis_mk")) + " / " + str(cb_mk.get("sumber_jenis_mk")))
    check("cetak_biru: catatan tidak lagi bilang 'masih tebakan'",
          "masih TEBakan awal" not in str(cb.get("catatan", "")),
          str(cb.get("catatan", ""))[:90])

    index = KT.muat_index()
    entri = None
    prodi_key = KT.sanitize_folder_name(prodi)
    tahun_map = ((index or {}).get("prodi", {}).get(prodi_key, {}) or {}).get("tahun_ajar", {}) or {}
    for ta_map in tahun_map.values():
        for sem_map in (ta_map or {}).values():
            for e in (sem_map or {}).get("mata_kuliah", []):
                if e.get("kunci_mk") == kunci:
                    entri = e
    check("index turunan memuat jenis_mk terkonfirmasi",
          bool(entri) and entri.get("jenis_mk") == jenis_konfirm,
          json.dumps(entri, ensure_ascii=False)[:120] if entri else "entri tidak ditemukan")

    # Data turunan harus tetap bisa dibangun (tidak ada yang rusak).
    ctx = PD.muat_kurikulum()
    check("parse_data masih bisa membaca tree setelah migrasi",
          len(ctx.get("sessions") or []) == total)

finally:
    # --- pulihkan tree byte-per-byte ---
    try:
        if os.path.isdir(KT.KURIKULUM_DIR):
            shutil.rmtree(KT.KURIKULUM_DIR)
        shutil.copytree(snap_tree, KT.KURIKULUM_DIR)
        shutil.copy2(snap_index, KT.INDEX_PATH)
        shutil.rmtree(snap, ignore_errors=True)
    except OSError as e:  # pragma: no cover - jalur darurat
        PERINGATAN_PULIH.append(str(e))

print("\n4. Pemulihan snapshot")
if PERINGATAN_PULIH:
    check("pemulihan tanpa error", False, "; ".join(PERINGATAN_PULIH))
    print("     [DARURAT] Pulihkan manual: git checkout -- data/kurikulum config/kurikulum.json")
else:
    hash_sekarang, _ = hash_tree()
    check("tree kembali BYTE-IDENTIK dengan sebelum tes",
          hash_sekarang == baseline_hash,
          baseline_hash[:12] + " vs " + hash_sekarang[:12])
    check("folder snapshot sudah dibersihkan", not os.path.isdir(snap))

print("\n" + "=" * 76)
print("HASIL: " + ("SEMUA OK" if ok else "ADA YANG GAGAL"))
print("=" * 76)
sys.exit(0 if ok else 1)

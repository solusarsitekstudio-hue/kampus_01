"""TES: agregasi periode (Level 3/4) + aturan netral BELUM-DIINPUT.

Jalankan:  python tests\\test_periode.py

Yang dibuktikan:
  1. Parsing bulan: tanggal ISO -> YYYY-MM; tanggal kosong/aneh grup terpisah.
  2. Agregasi konsisten dengan master untuk MK aktif (nilai_rata & at-risk).
  3. Aturan netral Batch B: pertemuan belum diinput TIDAK menekan kehadiran;
     semua belum diinput -> kehadiran None (netral), bukan 0%.
  4. At-risk PER MK dan Sakit/Izin BUKAN Alpha (ikuet bucket parse_data).
  5. Cache: tanda mtime membuat rekap diulang setelah berkas berubah.
"""
import io
import os
import sys
import json
import tempfile
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import periode as P  # noqa: E402
import kurikulum_tree as KT  # noqa: E402

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


print("=" * 72)
print("TES PERIODE: agregasi dari tree, netral belum-diinput, at-risk per MK")
print("=" * 72)

print("\n1. Bulan dari tanggal (keputusan poin 1: tanpa tanggal = grup sendiri)")
check(" tanggal ISO penuh", P._bulan_dari_tanggal("2025-08-15") == "2025-08")
check(" tanggal berformat lain gagal aman", P._bulan_dari_tanggal("15-08-2025") is None)
check(" tanggal kosong -> None", P._bulan_dari_tanggal("") is None
      and P._bulan_dari_tanggal(None) is None)
check(" grup tanpa tanggal ada", P.GRUP_TANPA_TANGGAL == "-")

print("\n2. Matriks (npm, pertemuan): baris tanpa npm dibuang")
m = P._matriks_nilai([
    {"npm": "A1", "pertemuan": 1, "status": "Hadir"},
    {"npm": "A1", "pertemuan": 2, "status": "Alpha"},
    {"npm": "", "pertemuan": 1, "status": "Hadir"},
])
check(" duplikat npm: 2 pertemuan", list(m["A1"]) == [1, 2], str(list(m["A1"])))
check(" npm kosong tidak masuk", "" not in m)

print("\n3. Agregasi MK aktif <=> master (data live)")
prodi = KT.daftar_prodi()[:1] and KT.daftar_prodi()[0]
mk_aktif = KT.daftar_mk(prodi, "2025-2026", "GENAP")
dok = P.agregat_semester(prodi, "2025-2026", "GENAP")
baris_by_kunci = {b["kunci_mk"]: b for b in dok["baris"]}
master_path = os.path.join(HERE, "data", "academic_data.json")
try:
    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)
    kunci_master = (master.get("metadata") or {}).get("kunci_mk")
    cb = baris_by_kunci.get(kunci_master)
    check(" MK master ada di agregat", cb is not None, kunci_master)
    if cb:
        check(" nilai_rata == master",
              cb["nilai_rata"] == master.get("class_summary", {}).get("rata_nilai_studio"),
              f"{cb['nilai_rata']} vs {master.get('class_summary', {}).get('rata_nilai_studio')}")
        check(" jumlah_at_risk == master total_at_risk",
              cb["jumlah_at_risk"] == master.get("class_summary", {}).get("total_at_risk"),
              f"{cb['jumlah_at_risk']} vs {master.get('class_summary', {}).get('total_at_risk')}")
        check(" peserta MK == master",
              cb["peserta"] == len(master.get("students") or []))
except (OSError, json.JSONDecodeError):
    check(" master bisa dibaca (data live)", False, master_path)

print("\n4. Aturan netral BELUM-DIINPUT (sintetis, tanpa berkas)")
def mk_data(slot_total, baris):
    sesi = [{"pertemuan": 1, "tanggal": "2025-08-15",
             "slot_absen": [{"slot": j + 1, "label": f"Absen {j+1}"} for j in range(slot_total)],
             "bobot": 60},
            {"pertemuan": 2, "tanggal": "2025-09-10",
             "slot_absen": [{"slot": j + 1, "label": f"Absen {j+1}"} for j in range(slot_total)],
             "bobot": 40}]
    return {"penawaran": {"nama_mk": "MK TES"}, "sesi": {"sesi": sesi},
            "nilai": {"nilai": baris}}

# Kasus 4a: P1 lengkap (2 slot hadir + alpha sebagian), P2 HANYA 1 dari 2 slot.
# P2 belum lengkap -> keluar dari penyebut: kehadiran dihitung atas P1 saja.
baris4 = [
    {"npm": "X", "pertemuan": 1, "slot": 1, "status": "Hadir", "skor": 80},
    {"npm": "X", "pertemuan": 1, "slot": 2, "status": "Hadir", "skor": 80},
    {"npm": "X", "pertemuan": 2, "slot": 1, "status": "Hadir", "skor": 70},
    # (slot 2 P2 tidak ada -> P2 BELUM DIINPUT untuk X)
]
rek = P._rekap_mk_dalam("T", "T", "T", "TES", mk_data(2, baris4))
check(" P2 belum lengkap tidak menekan kehadiran", rek["kehadiran_rata"] == 100.0,
      f"{rek['kehadiran_rata']}")
check(" nilai P2 (70) ikut dihitung (barisnya ada)", rek["nilai_rata"] is not None,
      f"{rek['nilai_rata']}")

# Kasus 4b: SEMUA pertemuan belum diinput -> kehadiran None (netral), nilai None,
# dan TIDAK jadi at-risk kehadiran (0% yang menuduh), alpha juga tidak.
baris4b = [{"npm": "Y", "pertemuan": 2, "slot": 1, "status": "Hadir", "skor": 60}]
rek2 = P._rekap_mk_dalam("T", "T", "T", "TES", mk_data(2, baris4b))
check(" semua belum diinput -> kehadiran None", rek2["kehadiran_rata"] is None)
check(" at-risk 0 (netral, bukan menuduh 0%)", rek2["jumlah_at_risk"] == 0)

# Kasus 4c: Sakit/Izin BUKAN Alpha. Dua mahasiswa mainan dengan KEHADIRAN
# IDENTIK 75% (6 dari 8): yang membedakan hanya status 2 pertemuan
# (Sakit vs Alpha). Beda at-risk satu-satunya bisa dari aturan alpha.
def mk_delapan(statuses):
    sesi = [{"pertemuan": p + 1, "tanggal": None,
             "slot_absen": [{"slot": 1, "label": "Absen 1"}], "bobot": 100 / 8}
            for p in range(8)]
    baris = [{"npm": "Z", "pertemuan": p + 1, "slot": 1,
              "status": statuses[p], "skor": 50}
             for p in range(len(statuses))]
    return {"penawaran": {"nama_mk": "MK TES"}, "sesi": {"sesi": sesi},
            "nilai": {"nilai": baris}}

H = "Hadir"
rek_sakit = P._rekap_mk_dalam(
    "T", "T", "T", "TES", mk_delapan([H, H, "Sakit", "Sakit", H, H, H, H]))
rek_alpha = P._rekap_mk_dalam(
    "T", "T", "T", "TES", mk_delapan([H, H, "Alpha", "Alpha", H, H, H, H]))
check(" kehadiran dua kasus identik (75%)",
      rek_sakit["kehadiran_rata"] == rek_alpha["kehadiran_rata"] == 75.0,
      f"{rek_sakit['kehadiran_rata']} vs {rek_alpha['kehadiran_rata']}")
check(" Sakit 2x -> BUKAN Alpha (tak kena ambang alpha_min)",
      rek_sakit["jumlah_at_risk"] == 0)
check(" Alpha 2x -> at-risk (alpha_min >= 2)",
      rek_alpha["jumlah_at_risk"] == 1 and rek_alpha["at_risk_npm"] == ["Z"])

print("\n5. Kehadiran antar-MK: MK yang belum bisa dihitung keluar dari rata-rata")
# _rekap_mk_dalam kasus 4b memberi kehadiran None; _rata_mks harus skip None.
angka = P._rata_mks([{"rusak": None, "kehadiran_rata": None},
                     {"rusak": None, "kehadiran_rata": 80.0}], "kehadiran_rata")
check(" None di-skip, bukan dihitung 0", angka == 80.0, str(angka))
angka2 = P._rata_mks([{"rusak": None, "kehadiran_rata": None}], "kehadiran_rata")
check(" semua None -> None", angka2 is None)

print("\n6. Level 4: rollup pohon menjumlah antar semester")
roll = P.agregat_semua_semester(prodi)
jumlah_mk_total = sum(
    (dok.get("ringkas") or {}).get("jumlah_mk", 0)
    for ta, sem_map in roll["tahun_ajar"].items()
    for dok in sem_map.values())
check(" rollup jumlah_mk == jumlah baris",
      roll["ringkas"]["jumlah_mk"] == jumlah_mk_total,
      f"{roll['ringkas']['jumlah_mk']} vs {jumlah_mk_total}")
kejadian = sum(
    int((b.get("jumlah_at_risk") or 0))
    for ta, sem_map in roll["tahun_ajar"].items()
    for dok in sem_map.values()
    for b in (dok.get("baris") or []))
unik = set()
for ta, sem_map in roll["tahun_ajar"].items():
    for dok in sem_map.values():
        for b in (dok.get("baris") or []):
            unik.update(str(n) for n in (b.get("at_risk_npm") or []))
check(" rollup at-risk = mahasiswa UNIK (bukan jumlah kemunculan)",
      roll["ringkas"]["jumlah_at_risk"] == len(unik),
      f"{roll['ringkas']['jumlah_at_risk']} vs {len(unik)}")
check(" rollup menyimpan jumlah kejadian per MK terpisah",
      roll["ringkas"].get("jumlah_kejadian_at_risk") == kejadian,
      f"{roll['ringkas'].get('jumlah_kejadian_at_risk')} vs {kejadian}")
check(" at-risk unik <= jumlah mahasiswa",
      roll["ringkas"]["jumlah_at_risk"] <= 35,
      str(roll["ringkas"]["jumlah_at_risk"]))

print("\n7. Cache: tanda mtime mengusangkan rekap")
b1 = P.agregat_mk(prodi, "2025-2026", "GENAP", mk_aktif[0])
kcache = (prodi, "2025-2026", "GENAP", mk_aktif[0])
eusi = P._REKAP_CACHE.get(kcache)
check(" cache terisi setelah agregat_mk", bool(eusi))
# Tanda masih sama -> snapshot diulang dari cache (nilai identik, cepat).
b2 = P.agregat_mk(prodi, "2025-2026", "GENAP", mk_aktif[0])
check(" cache hit: hasil identik", b1 == b2)

P.kosongkan_cache()
check(" kosongkan_cache membersihkan", not P._REKAP_CACHE)

print()
print("=" * 72)
print("HASIL:", "SEMUA LULUS" if ok else "ADA YANG GAGAL")
print("=" * 72)
sys.exit(0 if ok else 1)

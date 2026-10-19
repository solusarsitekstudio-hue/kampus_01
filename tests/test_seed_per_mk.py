"""TES: nilai sintetis harus BEDA per mata kuliah (dan tetap reproducible).

Jalankan TANPA server:  python tests\\test_seed_per_mk.py

Konteks (kenapa tes ini ada):
  Dulu benih RNG nilai sintetis hanya `42 + npm`. Karena ketiga MK punya
  struktur sesi yang sama (16 pertemuan, 2 slot), ketiga nilai.json berisi
  catatan yang PERSIS SAMA - 1120 baris yang sama untuk tiga mata kuliah yang
  berbeda. Di dashboard itu terlihat seperti sistem yang menyalin data.

Yang dibuktikan sekarang:
  1. `konteks=""` = perilaku lama (`42 + npm`) - jadi bisa dibandingkan.
  2. `konteks=<MK>` -> deret RNG berbeda, tetap deterministic.
  3. Persona mahasiswa TIDAK ikut berpindah kalau konteks berubah.
  4. Bukti bug lama: dengan konteks kosong, dua MK menghasilkan baris identik;
     dengan konteks MK, tidak identik lagi.
  5. Data nyata: tiga nilai.json punya SHA berbeda DAN bisa dibangkitkan ulang
     persis dari sesi.json + mahasiswa.json (tidak ada data tersembunyi).
  6. Profil at-risk tetap utuh (jumlah alpha tidak hilang) di semua MK.
  7. Script seed menolak menulis tanpa `--force` (dry run benar-benar kering).
"""
import hashlib
import io
import json
import os
import random
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import kurikulum_tree as KT  # noqa: E402
import parse_data as PD  # noqa: E402
import persona as PS  # noqa: E402

PRODI = "ARSITEKTUR"
TA = "2025-2026"
SEM = "GENAP"
MK_DIKENAL = [
    "APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS",
    "STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1",
    "STUDIO_PERANCANGAN_ARSITEKTUR_2",
]
NPM_STAR = "2510015410010"
NPM_AT_RISK = "2510015410011"

ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label}" + (f"  ({detail})" if detail else ""))


def _path(nama, kunci):
    return KT.path_berkas(PRODI, TA, SEM, kunci, nama)


def _sha_baris(baris):
    teks = json.dumps(baris, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(teks.encode("utf-8")).hexdigest()[:12].upper()


def _hitung(baris):
    """jumlah status per mahasiswa -> {(npm, status): n}"""
    hasil = {}
    for b in baris:
        k = (str(b.get("npm")), b.get("status"))
        hasil[k] = hasil.get(k, 0) + 1
    return hasil


print("=" * 76)
print("TES: nilai sintetis beda per mata kuliah (seed per MK)")
print("=" * 76)

print("\n1. `konteks=''` = perilaku lama (42 + npm), bukan mesin RNG baru")
check("_benih(npm) == 42 + npm", PS._benih(NPM_STAR) == 42 + int(NPM_STAR),
      str(PS._benih(NPM_STAR)))
check("rng_untuk(npm) == random.Random(42 + npm)",
      PS.rng_untuk(NPM_STAR).random() == random.Random(42 + int(NPM_STAR)).random())
check("_benih(npm, konteks) != _benih(npm)",
      PS._benih(NPM_STAR, MK_DIKENAL[0]) != PS._benih(NPM_STAR))

print("\n2. Konteks MK -> deret berbeda, tapi deterministic")
a1 = [PS.rng_untuk(NPM_STAR, MK_DIKENAL[0]).random() for _ in range(5)]
a2 = [PS.rng_untuk(NPM_STAR, MK_DIKENAL[0]).random() for _ in range(5)]
b = [PS.rng_untuk(NPM_STAR, MK_DIKENAL[1]).random() for _ in range(5)]
check("panggil ulang konteks sama -> sama", a1 == a2)
check("konteks beda -> deret beda", a1 != b)
check("mahasiswa beda tetap beda", PS._benih(NPM_STAR, MK_DIKENAL[0])
      != PS._benih(NPM_AT_RISK, MK_DIKENAL[0]))

print("\n3. Persona mahasiswa TIDAK berpindah karena konteks MK")
check("star tetap star di MK lain",
      PS.tentukan_archetype(0, NPM_STAR, MK_DIKENAL[2]) == "star",
      PS.tentukan_archetype(0, NPM_STAR, MK_DIKENAL[2]))
check("at_risk tetap at_risk di MK lain",
      PS.tentukan_archetype(9, NPM_AT_RISK, MK_DIKENAL[0]) == "at_risk",
      PS.tentukan_archetype(9, NPM_AT_RISK, MK_DIKENAL[0]))
check("persona tidak bergantung idx",
      PS.tentukan_archetype(1, NPM_AT_RISK) == PS.tentukan_archetype(33, NPM_AT_RISK))

print("\n4. Bukti bug lama vs sesudah perbaikan (dua MK, struktur sesi sama)")
mahasiswa = KT.baca_json(os.path.join(KT.path_prodi(PRODI), "mahasiswa.json"))["mahasiswa"]
sesi_a = KT.baca_json(_path("sesi.json", MK_DIKENAL[0]))
sesi_b = KT.baca_json(_path("sesi.json", MK_DIKENAL[1]))
lama_a = PS.bangun_nilai_satu_mk(mahasiswa, sesi_a, konteks="")
lama_b = PS.bangun_nilai_satu_mk(mahasiswa, sesi_b, konteks="")
check("konteks kosong -> dua MK IDENTIK (bug lama) ", lama_a == lama_b,
      f"{len(lama_a)} baris")
baru_a = PS.bangun_nilai_satu_mk(mahasiswa, sesi_a, konteks=MK_DIKENAL[0])
baru_b = PS.bangun_nilai_satu_mk(mahasiswa, sesi_b, konteks=MK_DIKENAL[1])
check("konteks MK -> dua MK BEDA", baru_a != baru_b,
      f"{_sha_baris(baru_a)} vs {_sha_baris(baru_b)}")
check("jumlah baris tetap sama (struktur tidak berubah)", len(baru_a) == len(lama_a))
check("reproducible: bangun dua kali = baris sama",
      PS.bangun_nilai_satu_mk(mahasiswa, sesi_a, konteks=MK_DIKENAL[0]) == baru_a)

print("\n5. Data nyata di tree: tiga nilai.json berbeda & bisa dibangkitkan ulang")
sha_berkas = {}
for kunci in MK_DIKENAL:
    path = _path("nilai.json", kunci)
    with open(path, "rb") as f:
        sha_berkas[kunci] = hashlib.sha256(f.read()).hexdigest()[:12].upper()
check("tiga SHA berbeda (tidak lagi kembar)", len(set(sha_berkas.values())) == 3,
      str(sha_berkas))
check("konteks kosong menghasilkan kembar (pembanding)", len({
    _sha_baris(PS.bangun_nilai_satu_mk(mahasiswa, KT.baca_json(_path("sesi.json", k)), konteks=""))
    for k in MK_DIKENAL}) == 1)

for kunci in MK_DIKENAL:
    dok = KT.baca_json(_path("nilai.json", kunci))
    ulang = PS.bangun_nilai_satu_mk(mahasiswa, KT.baca_json(_path("sesi.json", kunci)),
                                   konteks=kunci)
    check(f"{kunci[:34]}: nilai.json = hasil bangkit ulang",
          dok.get("nilai") == ulang and dok.get("kunci_mk") == kunci,
          f"{len(ulang)} baris")
    check(f"{kunci[:34]}: ditandai sintetis", dok.get("sintetis") is True)
    check(f"{kunci[:34]}: kepala sinkron kontrak tree (tahun/semester)",
          (dok.get("tahun_ajar"), dok.get("semester"))
          == (KT.norm_tahun_ajar(TA), KT.slug_semester(SEM)),
          f"{dok.get('tahun_ajar')} / {dok.get('semester')}")

print("\n6. Kehadiran & profil at-risk lintas MK")
sesi_doc = KT.baca_json(_path("sesi.json", MK_DIKENAL[0]))
ujian = {s["pertemuan"] for s in sesi_doc["sesi"] if s["tipe"] in ("uts", "uas")}
persona = {str(m["npm"]): PS.tentukan_archetype(i, m["npm"]) for i, m in enumerate(mahasiswa)}
persona = {n: a for n, a in persona.items() if a != "normal"}
check("ada mahasiswa berpersona (bukan acak) untuk diperiksa", len(persona) >= 3,
      f"{len(persona)} mahasiswa")

alpha_per_mk, pola, di_ujian = {}, {}, []
for kunci in MK_DIKENAL:
    baris = KT.baca_json(_path("nilai.json", kunci))["nilai"]
    hitung = _hitung(baris)
    alpha_per_mk[kunci] = {n: hitung.get((n, "Alpha"), 0) for n in persona}
    milik_persona = [b for b in baris if str(b["npm"]) in persona and b["status"] != "Hadir"]
    pola[kunci] = _sha_baris(sorted((b["pertemuan"], b["slot"], b["status"]) for b in milik_persona))
    di_ujian += [b for b in milik_persona if b["pertemuan"] in ujian]

check(f"{NPM_AT_RISK} tetap Alpha ≥ 2x di setiap MK (syarat At-Risk)",
      all(alpha_per_mk[k][NPM_AT_RISK] >= 2 for k in MK_DIKENAL),
      str({k[:12]: alpha_per_mk[k][NPM_AT_RISK] for k in MK_DIKENAL}) + " slot")
check("jumlah absen per mahasiswa berpersona SAMA di semua MK (profil utuh)",
      len({json.dumps(v, sort_keys=True) for v in alpha_per_mk.values()}) == 1)
check("letak absen berbeda di ketiga MK (tiga sidik jari)",
      len(set(pola.values())) == 3, str(sorted(pola.values())))
check("absen persona tidak mendarat di pertemuan UTS/UAS", not di_ujian,
      f"{len(di_ujian)} baris di pertemuan {sorted(ujian)}")

print("\n7. Script seed: dry run tidak menulis apa pun")
BACKUP = os.path.join(HERE, "data", "_backup")
sebelum = {k: os.path.getmtime(_path("nilai.json", k)) for k in MK_DIKENAL}
bak_sebelum = set(os.listdir(BACKUP)) if os.path.isdir(BACKUP) else set()
proc = subprocess.run(
    [sys.executable, os.path.join(HERE, "scripts", "seed_nilai_sintetis.py")],
    capture_output=True, text=True, cwd=HERE,
)
keluaran = (proc.stdout or "") + (proc.stderr or "")
check("keluar dengan kode 0", proc.returncode == 0, f"rc={proc.returncode}")
check("menyebut DRY RUN", "DRY RUN" in keluaran)
check("melaporkan ketiga MK", all(k[:20] in keluaran for k in MK_DIKENAL))
check("mtime nilai.json tidak berubah",
      sebelum == {k: os.path.getmtime(_path("nilai.json", k)) for k in MK_DIKENAL})
bak_sesudah = set(os.listdir(BACKUP)) if os.path.isdir(BACKUP) else set()
check("tidak ada folder backup baru", bak_sesudah == bak_sebelum,
      f"{len(bak_sesudah)} folder backup")

print("\n8. Pindah mata kuliah di dashboard -> KPI ikut berubah (bukan salinan)")
kpi, kunci_terbaca = {}, {}
for kunci in MK_DIKENAL:
    ds = PD.bangun_dataset(kunci)
    cs = ds["class_summary"]
    kpi[kunci] = (cs["rata_kehadiran"], cs["rata_nilai_studio"], cs["total_at_risk"])
    kunci_terbaca[kunci] = ds["course"].get("kode_mk")
check("tiga MK -> tiga KPI berbeda", len(set(kpi.values())) == 3, str(kpi))
check("dataset tiap MK melaporkan kode MK-nya sendiri (bukan MK aktif yang nyangkut)",
      all(kunci_terbaca[k] == KT.baca_json(_path("penawaran.json", k))["kode_mk"]
          for k in MK_DIKENAL), str(kunci_terbaca))

print("\n" + "=" * 76)
print("HASIL: " + ("SEMUA OK" if ok else "ADA YANG GAGAL"))
print("=" * 76)
sys.exit(0 if ok else 1)

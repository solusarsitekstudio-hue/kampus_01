"""persona.py - persona mahasiswa + pembangkit catatan kehadiran sintetis.

KENAPA DIPISAH
--------------
Dua hal ini dulu menumpang di dalam `parse_data.py` dan tersambung ke RNG
global (`random.seed(42)`). Akibatnya satu baris baru di Excel menggeser nilai
SELURUH kelas (utang #1). Sekarang:

  * persona terikat NPM (bukan nomor baris),
  * RNG dibuat PER MAHASISWA (`random.Random(42 + npm)`), jadi menambah atau
    menghapus mahasiswa lain TIDAK menggeser angka siapa pun,
  * catatan kehadiran/nilai disimpan sebagai DATA (data/kurikulum/.../nilai.json)
    lewat `scripts/migrasi_kurikulum.py`, bukan dikarang saat compile.

Perubahan perilaku ini disengaja (keputusan user Tahap E): angka memang
berubah, jadi sekalian utang #1 dibayar.
"""

import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kelas_rules as KR  # noqa: E402

# =============================================================================
# PERSONA - TERIKAT KE NPM, BUKAN KE NOMOR BARIS
# =============================================================================
# Sebelumnya persona ditentukan dari posisi baris:
#     if idx == 0 -> "star";  elif idx == 10 -> "at_risk";  elif idx % 7 == 0 ...
# Begitu satu mahasiswa ditambah/dihapus/diurutkan ulang, SEMUA posisi bergeser
# satu langkah dan mahasiswa yang sama berubah persona tanpa ada yang sadar.
ARCHETYPE_BY_NPM = {
    "2510015410010": "star",      # M YAZID ZIDANE MULYADI
    "2510015410011": "at_risk",   # ROZI ANDRIAN SURVA
    "2510015410001": "high",      # ALSA DMI YESYA PUTRI
}


def tentukan_archetype(idx: int, npm: str) -> str:
    """Persona mahasiswa: MURNI dari NPM. `idx` hanya dipertahankan untuk
    pemanggil lama dan TIDAK dipakai lagi.

    Dulu cadangannya `idx % 7` / `idx % 4` - artinya mahasiswa yang sama bisa
    berubah persona hanya karena satu baris lain ditambah di atasnya. Sekarang
    polanya dari angka NPM sendiri, jadi posisi tidak berpengaruh sama sekali.
    """
    if str(npm) in ARCHETYPE_BY_NPM:
        return ARCHETYPE_BY_NPM[str(npm)]
    digit = re.sub(r"\D", "", str(npm or ""))
    angka = int(digit) if digit else 0
    if angka % 7 == 0:
        return "moderate_absent"
    if angka % 4 == 0:
        return "good"
    return "normal"


def rng_untuk(npm):
    """RNG per mahasiswa. Menambah mahasiswa lain TIDAK menggeser angkanya."""
    digit = re.sub(r"\D", "", str(npm or ""))
    return random.Random(42 + (int(digit) if digit else 0))


# =============================================================================
# CATATAN KEHADIRAN SINTETIS
# =============================================================================
ALASAN_SAKIT = [
    "Sakit demam & flu (surat dokter terlampir)",
    "Sakit radang tenggorokan & istirahat dokter",
    "Kondisi fisik drop pasca asistensi studio malam",
    "Sakit tifus rawat jalan (ada konfirmasi dokter)",
]
ALASAN_IZIN = [
    "Izin delegasi Sayembara Desain Arsitektur Nasional",
    "Izin kegiatan studi banding Ikatan Mahasiswa Arsitektur (IMA)",
    "Izin urusan keluarga mendesak di luar kota",
    "Izin servis laptop kendala hardware crash AutoCAD",
]


def _pos(rasio, total):
    """Pecahan semester (0.15) -> nomor pertemuan (2). Aman utk total berapa pun."""
    return max(1, min(total, int(round(rasio * total))))


# Profil absensi per persona, dinyatakan sebagai PECAHAN semester (bukan nomor
# pertemuan), supaya tetap masuk akal kalau `pertemuan_total` di config diubah.
#   "alpha" / "izin" / "sakit" = 1 pertemuan penuh tidak hadir
#   "sebagian"                 = hanya separuh slot yang diisi
PROFIL_ABSENSI = {
    "high": [("izin", 0.30)],
    "good": [("sakit", 0.40), ("izin", 0.75)],
    # Absensi sedang: bolong, tapi masih di sekitar ambang 75% kehadiran.
    "moderate_absent": [
        ("alpha", 0.20), ("sebagian", 0.35), ("izin", 0.45),
        ("sakit", 0.65), ("alpha", 0.80), ("sebagian", 0.90),
    ],
    # Absensi berat: beberapa alpha tanpa keterangan.
    "at_risk": [
        ("alpha", 0.15), ("sebagian", 0.25), ("alpha", 0.35), ("izin", 0.50),
        ("sakit", 0.60), ("alpha", 0.75), ("sebagian", 0.85),
    ],
}


def rencana_pertemuan(archetype, total_pertemuan):
    """{nomor_pertemuan: (rasio_slot_hadir, alasan)} untuk persona non-acak.

    Rasio 0.0 = tidak hadir satu slot pun; 0.5 = separuh slot (tampil
    "Hadir Sebagian"); 1.0 = hadir penuh.
    """
    if archetype == "star":
        return {}
    rencana = {}
    for alasan, rasio_posisi in PROFIL_ABSENSI.get(archetype, []):
        p = _pos(rasio_posisi, total_pertemuan)
        if alasan == "sebagian":
            rencana[p] = (0.5, "Hadir Sebagian")
        else:
            rencana[p] = (0.0, alasan.capitalize())
    return rencana


def _skor_persona(archetype, rng, jenis):
    """Skor satu pertemuan sesuai persona. `jenis`: 'biasa' | 'ujian'."""
    if archetype == "star":
        return rng.randint(92, 98)
    if archetype == "at_risk":
        return rng.randint(68, 75) if jenis == "biasa" else rng.randint(66, 74)
    if archetype == "moderate_absent":
        return rng.randint(80, 88) if jenis == "biasa" else rng.randint(78, 86)
    if archetype == "high":
        return rng.randint(88, 95) if jenis == "biasa" else rng.randint(86, 93)
    return rng.randint(75, 90) if jenis == "biasa" else rng.randint(72, 88)


def bangun_nilai_sintetis(npm, idx, sesi_dokumen):
    """Catatan nilai + kehadiran sintetis PER SLOT untuk satu mahasiswa.

    Balikkan list baris: {pertemuan, slot, status, alasan, skor}.

    Aturan yang dipakai:
      * Satu pertemuan bisa punya beberapa slot absen (mis. 2 sesi sehari).
      * Status per slot: Hadir / Sakit / Izin / Alpha.
      * Pertemuan yang butuh N slot dan hanya sebagian dihadiri tampil apa
        adanya ("Hadir Sebagian") - tidak dibulatkan jadi hadir/alpha.
    """
    archetype = tentukan_archetype(idx, npm)
    rng = rng_untuk(npm)
    sesi = (sesi_dokumen or {}).get("sesi", [])
    total = len(sesi)
    rencana = rencana_pertemuan(archetype, total)

    baris = []
    for s in sesi:
        p = s.get("pertemuan")
        slots = s.get("slot_absen") or []
        n_slot = len(slots)
        if n_slot == 0:
            continue
        tipe = s.get("tipe")
        jenis = "ujian" if tipe in ("uts", "uas") else "biasa"

        if p in rencana:
            rasio, alasan_jenis = rencana[p]
        elif archetype == "normal":
            roll = rng.random()
            if roll < 0.85:
                rasio, alasan_jenis = 1.0, "Hadir"
            elif roll < 0.90:
                rasio, alasan_jenis = 0.5, "Hadir Sebagian"
            elif roll < 0.95:
                rasio, alasan_jenis = 0.0, "Izin"
            elif roll < 0.99:
                rasio, alasan_jenis = 0.0, "Sakit"
            else:
                rasio, alasan_jenis = 0.0, "Alpha"
        else:
            rasio, alasan_jenis = 1.0, "Hadir"

        n_hadir = int(round(rasio * n_slot))
        skor = _skor_persona(archetype, rng, jenis)

        for i, sl in enumerate(slots):
            if alasan_jenis == "Sakit":
                status, alasan, nilai = "Sakit", rng.choice(ALASAN_SAKIT), skor
            elif alasan_jenis == "Izin":
                status, alasan, nilai = "Izin", rng.choice(ALASAN_IZIN), skor
            elif alasan_jenis == "Alpha":
                status, alasan, nilai = "Alpha", "Tanpa keterangan / tidak hadir di presensi portal", 0
            elif i < n_hadir:
                status, alasan, nilai = "Hadir", "-", skor
            else:
                status, alasan, nilai = "Alpha", "Tanpa keterangan / tidak hadir di presensi portal", 0
            baris.append({
                "npm": str(npm),
                "pertemuan": p,
                "slot": sl.get("slot", i + 1),
                "status": status,
                "alasan": alasan,
                "skor": nilai,
            })
    return baris

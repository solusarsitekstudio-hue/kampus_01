"""persona.py - persona mahasiswa + pembangkit catatan kehadiran sintetis.

KENAPA DIPISAH
--------------
Dua hal ini dulu menumpang di dalam `parse_data.py` dan tersambung ke RNG
global (`random.seed(42)`). Akibatnya satu baris baru di Excel menggeser nilai
SELURUH kelas (utang #1). Sekarang:

  * persona terikat NPM (bukan nomor baris),
  * RNG dibuat PER MAHASISWA + PER MATA KULIAH (`random.Random(_benih(npm,
    konteks))`), jadi menambah atau menghapus mahasiswa lain TIDAK menggeser
    angka siapa pun, dan dua mata kuliah tidak lagi menghasilkan catatan yang
    persis sama (utang #2: kelas yang sama, angka yang sama di semua MK),
  * catatan kehadiran/nilai disimpan sebagai DATA (data/kurikulum/.../nilai.json)
    lewat `scripts/migrasi_kurikulum.py`, bukan dikarang saat compile.

KONTEKS MATA KULIAH
-------------------
`konteks` = kunci mata kuliah (mis. "ARSITEKTUR/2025-2026/GENAP/Aplikasi Komputer").
Nilainya hanya "bumbu" benih RNG lewat CRC32, jadi:

  * `konteks=""`  -> angka PERSIS seperti perilaku lama (42 + npm). Berguna
    untuk membuktikan bahwa perubahan itu memang datang dari konteks, bukan
    dari RNG yang dibongkar.
  * `konteks=<MK>` -> angka berbeda antar mata kuliah, tapi tetap deterministic
    dan tidak bergantung pada urutan baris mahasiswa.

Yang SENGAJA tidak diubah oleh konteks: `tentukan_archetype` (persona melekat
pada mahasiswa, bukan pada mata kuliah). Kalau "bintang" jadi "at-risk" hanya
karena pindah MK, seluruh analisis kasus di README tidak lagi bisa dirujuk.

Perubahan perilaku ini disengaja (keputusan user Tahap E): angka memang
berubah, jadi sekalian utang #1 dibayar.
"""

import os
import random
import re
import sys
import zlib

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
    "2510015410010": "star",      # M YAZID ZIDANE MULYADI (Angkatan 2025)
    "2510015410011": "at_risk",   # ROZI ANDRIAN SURVA (Angkatan 2025)
    "2510015410001": "high",      # ALSA DMI YESYA PUTRI (Angkatan 2025)
    "2410015410001": "star",      # FAJAR ADITYA PRATAMA (Angkatan 2024)
    "2410015410002": "at_risk",   # DINA SALSABILA PUTRI (Angkatan 2024 - Retake)
    "2410015410005": "at_risk",   # BAGAS WICAKSONO (Angkatan 2024 - Retake)
    "2610015410001": "star",      # ARKAN NAUFAL FIRDAUS (Angkatan 2026)
    "2610015410003": "at_risk",   # RANGGA ADIPUTRA NUGROHO (Angkatan 2026)
    "2610015410007": "at_risk",   # ALIF RAMADHAN SUPRIADI (Angkatan 2026)
}


def tentukan_archetype(idx: int, npm: str, konteks: str = "") -> str:
    """Persona mahasiswa: MURNI dari NPM. `idx` dan `konteks` hanya
    dipertahankan agar tanda tangan fungsi seragam dengan `rng_untuk` dan
    `bangun_nilai_sintetis`; KEDUANYA TIDAK DIPAKAI.

    Dulu cadangannya `idx % 7` / `idx % 4` - artinya mahasiswa yang sama bisa
    berubah persona hanya karena satu baris lain ditambah di atasnya. Sekarang
    polanya dari angka NPM sendiri, jadi posisi tidak berpengaruh sama sekali.

    `konteks` (kunci mata kuliah) juga sengaja DIABAIKAN: persona adalah
    identitas mahasiswa. Kalau konteks MK dipakai menentukan persona, satu
    mahasiswa bisa "bintang" di Studio Perancangan dan "at-risk" di Struktur &
    Konstruksi - analisis per kasus lalu tidak bisa dirujuk antar MK. Variasi
    antar MK diambil dari letak absen + angkanya (lihat `rencana_pertemuan` dan
    `_benih`).
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


def _benih(npm, konteks: str = "") -> int:
    """Benih RNG: `42 + npm` (perilaku lama) atau +CRC32(konteks) kalau ada.

    `konteks=""` WAJIB menghasilkan angka yang persis sama dengan versi lama,
    supaya "sebelum vs sesudah" bisa dibandingkan tanpa mengganti mesin RNG.
    """
    digit = re.sub(r"\D", "", str(npm or ""))
    dasar = 42 + (int(digit) if digit else 0)
    if konteks:
        dasar += zlib.crc32(str(konteks).encode("utf-8")) % 1000000
    return dasar


def rng_untuk(npm, konteks: str = ""):
    """RNG per mahasiswa PER MATA KULIAH.

    Menambah mahasiswa lain tidak menggeser angkanya, dan dua mata kuliah
    menghasilkan deret angka yang berbeda (`konteks` = kunci MK).
    """
    return random.Random(_benih(npm, konteks))


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


def _posisi_acak(posisi, total, rng, jendela=2, ujian=()):
    """Sebar ulang posisi absen: tetap di sekitar posisi profil, tapi antar MK beda.

    Jumlah dan bauran alasan (alpha/izin/sakit/sebagian) DIPERTAHANKAN - itu
    yang menjaga profil "at-risk" tetap at-risk. Yang bergerak hanya letaknya,
    supaya mahasiswa yang sama tidak absen di pertemuan yang persis sama di
    semua mata kuliah.

    Pertemuan UTS/UAS (`ujian`) TIDAK dipakai sebagai tempat absen: bobotnya 20
    dan 24, jadi satu Alpha yang tidak sengaja mendarat di sana menjatuhkan grade
    dari C ke D hanya karena hasil undian - cerita demo jadi tidak stabil dan
    tidak mencerminkan "bolong di pertemuan biasa" yang dimaksud profil.

    Tiap posisi memilih acak dari jendela +-`jendela` pertemuan (pertama-tama
    dari yang belum terpakai), jadi pola awal/tengah/akhir semester tetap
    terbaca dan tidak ada pertemuan yang dobel.
    """
    larangan = set(ujian or ())
    terpakai = set()
    hasil = []
    for p in posisi:
        jendela_kandidat = [q for q in range(max(1, p - jendela), min(total, p + jendela) + 1)
                            if q not in terpakai and q not in larangan]
        if not jendela_kandidat:  # jendela penuh/kena ujian: pakai pertemuan bebas mana pun
            jendela_kandidat = [q for q in range(1, total + 1)
                                if q not in terpakai and q not in larangan]
        if not jendela_kandidat:  # semua pertemuan bukan-ujian sudah terpakai
            jendela_kandidat = [q for q in range(1, total + 1) if q not in terpakai]
        pilih = rng.choice(jendela_kandidat)
        terpakai.add(pilih)
        hasil.append(pilih)
    return hasil


def rencana_pertemuan(archetype, total_pertemuan, rng=None, ujian=()):
    """{nomor_pertemuan: (rasio_slot_hadir, alasan)} untuk persona non-acak.

    Rasio 0.0 = tidak hadir satu slot pun; 0.5 = separuh slot (tampil
    "Hadir Sebagian"); 1.0 = hadir penuh.

    `rng` (opsional, dari `rng_untuk(npm, konteks)`) menggeser LETAK absen per
    mata kuliah; `ujian` = nomor pertemuan UTS/UAS yang dijauhi. Tanpa `rng`
    hasilnya persis seperti versi lama.
    """
    if archetype == "star":
        return {}
    rencana = {}
    profil = PROFIL_ABSENSI.get(archetype, [])
    posisi = [_pos(rasio_posisi, total_pertemuan) for _alasan, rasio_posisi in profil]
    if rng is not None and posisi:
        posisi = _posisi_acak(posisi, total_pertemuan, rng, ujian=ujian)
    for (alasan, _rasio_posisi), p in zip(profil, posisi):
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


def bangun_nilai_sintetis(npm, idx, sesi_dokumen, konteks=""):
    """Catatan nilai + kehadiran sintetis PER SLOT untuk satu mahasiswa.

    Balikkan list baris: {pertemuan, slot, status, alasan, skor}.

    `konteks` = kunci mata kuliah. Dua MK menghasilkan catatan yang BERBEDA
    (letak absen + skor), tapi masing-masing tetap deterministic: panggil ulang
    dengan konteks yang sama -> byte yang sama.

    Aturan yang dipakai:
      * Satu pertemuan bisa punya beberapa slot absen (mis. 2 sesi sehari).
      * Status per slot: Hadir / Sakit / Izin / Alpha.
      * Pertemuan yang butuh N slot dan hanya sebagian dihadiri tampil apa
        adanya ("Hadir Sebagian") - tidak dibulatkan jadi hadir/alpha.
    """
    archetype = tentukan_archetype(idx, npm, konteks)
    rng = rng_untuk(npm, konteks)
    sesi = (sesi_dokumen or {}).get("sesi", [])
    total = len(sesi)
    # Pertemuan UTS/UAS dijauhi saat menggeser letak absen (bobotnya 20 & 24).
    ujian = [s.get("pertemuan") for s in sesi if s.get("tipe") in ("uts", "uas")]
    rencana = rencana_pertemuan(archetype, total, rng, ujian=ujian)

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


# =============================================================================
# DOKUMEN NILAI SINTETIS - SATU SUMBER UNTUK MIGRASI & SEED
# =============================================================================
# Sebelumnya catatan + bentuk dokumen ini ditulis ulang di
# scripts/migrasi_kurikulum.py. Sekarang dipakai bersama supaya script seed
# (scripts/seed_nilai_sintetis.py) dan migrasi tidak bisa berbeda bentuk.
CATATAN_NILAI_SINTETIS = (
    "NILAI SINTETIS (bukan nilai resmi dosen). Dibangkitkan sekali supaya "
    "dashboard punya isi, dengan RNG per NPM + per mata kuliah sehingga "
    "menambah mahasiswa lain tidak menggeser angka siapa pun dan dua MK tidak "
    "berisi angka yang sama. Ganti dengan data portal begitu tersedia."
)


def bangun_nilai_satu_mk(daftar_mahasiswa, sesi_dokumen, konteks=""):
    """Baris nilai sintetis untuk SATU mata kuliah (seluruh mahasiswa).

    `daftar_mahasiswa`: list NPM (str) atau list dict berisi kunci "npm".
    `konteks` = kunci MK; WAJIB diisi supaya antar MK tidak kembar.
    """
    baris = []
    for idx, m in enumerate(daftar_mahasiswa):
        npm = m.get("npm") if isinstance(m, dict) else m
        baris.extend(bangun_nilai_sintetis(npm, idx, sesi_dokumen, konteks=konteks))
    return baris


def dokumen_nilai_sintetis(kunci, tahun_ajar, semester, baris):
    """Bentuk dokumen `nilai.json` (versi 1) - satu bentuk, satu sumber."""
    return {
        "versi": 1,
        "kunci_mk": kunci,
        "tahun_ajar": tahun_ajar,
        "semester": semester,
        "catatan": CATATAN_NILAI_SINTETIS,
        "sintetis": True,
        "nilai": baris,
    }

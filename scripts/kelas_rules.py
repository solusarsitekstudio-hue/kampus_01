"""
kelas_rules.py - SATU-SATUNYA SUMBER ATURAN AKADEMIK
====================================================
Modul ini berisi aturan yang HARUS sama di seluruh sistem: cara menghitung
nilai akhir, siapa yang masuk kategori at-risk, cara menghitung kehadiran,
dan bagaimana kategori kecocokan karier ditentukan.

Kenapa modul terpisah?
----------------------
Aturan-aturan ini dipakai di TIGA tempat:
  1. scripts/parse_data.py      -> membangun data/academic_data.json
  2. scripts/process_input.py   -> menghitung ulang saat ganti mata kuliah
  3. scripts/generate_pdfs.py   -> menulis PDF resmi

Sebelumnya isinya DISALIN-TEMPEL ke tiap file. Akibatnya, ketika aturan
at-risk diseragamkan, konstanta yang sama muncul tiga kali. Itu persis
jenis duplikasi yang dulu melahirkan 4 aturan at-risk berbeda dalam satu
aplikasi. Modul ini memastikan tidak terulang: ubah di sini, berubah di
semua tempat.

SEJAK TAHAP E (kurikulum bertingkat): ANGKANYA TIDAK LAGI DIPAKU DI FILE INI.
Ambang at-risk, ambang grade, aturan kehadiran, dan jam per SKS dibaca dari
`config/aturan.json` lewat `scripts/aturan.py`. Modul ini tinggal menyediakan
FUNGSI-nya, sehingga mengubah kebijakan tidak perlu menyentuh kode.

Catatan: dashboard (public/app.js) memakai aturan yang SAMA, tetapi angka
hasil hitungannya dibaca dari data/academic_data.json (field `at_risk` dan
`alasan_at_risk`), jadi tidak ada logika yang diduplikasi ke JavaScript.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aturan as AT  # noqa: E402


# =============================================================================
# 1. DETEKSI DINI AT-RISK  (ambang dari config/aturan.json)
# =============================================================================
def at_risk_alpha_min():
    """Ambang alpha (mis. 2). None kalau aturan ini tidak dipakai."""
    return AT.nilai_aturan("alpha_min")


def at_risk_kehadiran_min():
    """Ambang kehadiran % (mis. 75.0). None kalau aturan ini tidak dipakai."""
    return AT.nilai_aturan("kehadiran_min")


def at_risk_reasons(alpha: int, persentase: float) -> list:
    """Alasan kenapa mahasiswa masuk kategori at-risk (bisa lebih dari satu).

    Aturan dibaca dari config, jadi menambah/mengubah aturan tidak perlu
    mengubah fungsi ini.
    """
    if not AT.at_risk_aktif():
        return []
    reasons = []
    for a in AT.at_risk_rules():
        tipe, nilai = a.get("tipe"), float(a.get("nilai", 0))
        if tipe == "alpha_min" and alpha >= nilai:
            reasons.append("Alpha {0:g}x".format(alpha))
        elif tipe == "kehadiran_min" and persentase is not None and persentase < nilai:
            # persentase None = kehadiran belum bisa dihitung (semua pertemuan
            # belum diinput) - netral, tidak menuduh mahasiswa 0%.
            reasons.append("Kehadiran {0}%".format(persentase))
    return reasons


def is_at_risk(alpha: int, persentase: float) -> bool:
    """True bila minimal satu aturan di config/aturan.json terpenuhi."""
    return bool(at_risk_reasons(alpha, persentase))


# =============================================================================
# 2. KEHADIRAN: SLOT vs PERTEMUAN  (aturan dari config/aturan.json)
# =============================================================================
# Aturan user (Tahap E):
#   * Satu pertemuan bisa punya lebih dari satu slot absen (mis. kuliah 2 sesi
#     pagi sampai sore -> 4x ambil absen).
#   * yang DITAMPILKAN adalah pertemuan, tetapi PERSEN dihitung dari slot -
#     jadi mahasiswa yang hadir 1 dari 4 slot tampil JUJUR (1/4), tidak
#     dibulatkan diam-diam menjadi "hadir" atau "alpha".
def persentase_kehadiran(total_slot_hadir: int, total_slot: int) -> float:
    """Persen kehadiran berbasis slot. 0 slot = 0.0 (tidak ada pembagian nol)."""
    if not total_slot:
        return 0.0
    return round((total_slot_hadir / total_slot) * 100, 1)


def pertemuan_memenuhi_ambang(slot_hadir: int, slot_total: int) -> bool:
    """True bila 1 pertemuan MEMENUHI AMBANG kehadiran (definisi longgar).

    Ambangnya `kehadiran.min_slot_ratio_hadir` di config (default 50%):
    2 dari 4 slot = memenuhi ambang; 1 dari 4 = belum.

    PENTING - ada DUA ukuran "hadir" dan keduanya sah, jadi jangan disatukan:
      * `status_pertemuan()` -> "Hadir" = SEMUA slot pertemuan itu hadir (ketat).
        Ini yang ditampilkan di rapor/PDF dan dihitung sebagai `pertemuan_penuh`.
      * fungsi ini -> pertemuan "memenuhi ambang" (longgar, >= 50% slot).
    Dashboard wajib menampilkan dua-duanya terpisah supaya tidak ada satu angka
    "hadir" yang bisa dibaca dua cara. Persen kehadiran sendiri selalu berbasis
    SLOT (`persentase_kehadiran`), bukan salah satu dari dua ukuran di atas.

    Dulu fungsi ini bernama `pertemuan_dihitung_hadir` dan angkanya tampil di
    dashboard sebagai "X / 16 Pertemuan" - sebelah baris yang menulis "hadir
    sebagian", sehingga satu baris bisa membantah dirinya sendiri.
    """
    if not slot_total:
        return False
    return (slot_hadir / slot_total) >= AT.min_slot_ratio_hadir()


def slot_dianggap_hadir(status) -> bool:
    """True bila satu BARIS slot menandakan mahasiswa benar-benar hadir.

    "Hadir Sebagian" adalah status per slot yang sah (mis. portal mencatat
    mahasiswa masuk separuh sesi). Dulu fungsi agregasi hanya menghitung
    status == "Hadir", sehingga pertemuan yang SEMUA slotnya "Hadir Sebagian"
    jatuh ke bucket Alpha - mahasiswa yang hadir dan punya nilai tetap dicap
    Alpha, alpha ikut membengkak, dan At-Risk bisa salah tuduh.

    Satu sumber aturan ini dipakai parse_data.py dan periode.py.
    """
    return str(status or "").strip() in ("Hadir", "Hadir Sebagian")


def status_pertemuan_dari_status(status_isi, slot_total: int) -> str:
    """Bucket satu pertemuan dari daftar status slot (vocabulary resmi).

    Aturan:
      * semua slot "Hadir"                  -> "Hadir"
      * ada slot hadir (termasuk sebagian)  -> "Hadir Sebagian"
      * tidak ada yang hadir, ada Sakit      -> "Sakit"
      * tidak ada yang hadir, ada Izin       -> "Izin"
      * selain itu                           -> "Alpha"

    "Hadir Sebagian" TIDAK boleh jatuh menjadi Alpha hanya karena tidak ada
    slot yang berstatus persis "Hadir".
    """
    if not slot_total:
        return "-"
    status = [str(s or "").strip() for s in (status_isi or [])]
    jumlah_hadir = sum(1 for s in status if slot_dianggap_hadir(s))
    jumlah_penuh = sum(1 for s in status if s == "Hadir")
    if jumlah_penuh >= slot_total:
        return "Hadir"
    if jumlah_hadir > 0:
        return "Hadir Sebagian"
    if "Sakit" in status:
        return "Sakit"
    if "Izin" in status:
        return "Izin"
    return "Alpha"


def pertemuan_belum_diinput(slot_terisi: int, slot_total: int) -> bool:
    """True bila baris slot absen satu pertemuan BELUM lengkap.

    `slot_total` = jumlah slot yang seharusnya ada (dari sesi.json).
    `slot_terisi` = jumlah baris catatan yang benar-benar ada di nilai.json.

    Kalau kurang, pertemuan itu bukan Alpha - datanya memang belum masuk.
    Dipakai supaya "belum diinput" tidak diam-diam dinilai 0.
    """
    if not slot_total:
        return False
    return slot_terisi < slot_total


def status_pertemuan(slot_hadir: int, slot_total: int, slot_terisi=None) -> str:
    """Label jujur untuk satu pertemuan.

    `slot_terisi` (opsional) = jumlah baris catatan yang ada. Bila diberikan dan
    kurang dari `slot_total`, pertemuan ditandai "Belum Diinput" - bukan Alpha.
    Tanpa argumen ini, perilaku lama dipertahankan (kompatibel).
    """
    if not slot_total:
        return "-"
    if slot_terisi is not None and pertemuan_belum_diinput(slot_terisi, slot_total):
        return "Belum Diinput"
    if slot_hadir >= slot_total:
        return "Hadir"
    if slot_hadir <= 0:
        return "Alpha"
    return "Hadir Sebagian"


# =============================================================================
# 3. PERHITUNGAN NILAI AKHIR
# =============================================================================
def hitung_nilai_terbobot(session_scores, bobot_sesi):
    """Rata-rata TERBEBOT per sesi.

    Aturan:
      * Nilai 0 (Alpha) IKUT dihitung - mahasiswa tidak hadir tidak mendapat
        nilai gratis. (Dulu nilai 0 dibuang dengan `if sc > 0`.)
      * Sesi Sakit/Izin tetap dinilai 70-85, jadi mahasiswa yang sakit tidak
        dihukum atas hal yang bukan akibatnya.
      * Sesi dengan nilai None (pertemuan yang datanya BELUM DIINPUT) TIDAK
        dihitung, dan bobotnya ikut dikeluarkan lalu totalnya dinormalisasi.
        Jadi data yang belum masuk tidak menekan nilai - beda dari Alpha.
      * Bobot sesi dipakai. Sesi tersibuk dihargai lebih tinggi.

    Bila bobot tidak lengkap/tidak cocok jumlahnya, jatuh ke rata-rata
    sederhana supaya tidak crash - dan itu memang bukan jalur normal.
    """
    if not session_scores:
        return 0.0

    # Buang sesi yang belum diinput; kalau tidak ada satu pun bobot yang cocok,
    # pakai rata-rata sederhana atas sesi yang punya nilai.
    ada_filter = bobot_sesi and len(bobot_sesi) == len(session_scores)
    pasangan = [
        (s, b if ada_filter else None)
        for s, b in zip(session_scores, bobot_sesi or [None] * len(session_scores))
        if s is not None
    ]
    if not pasangan:
        return 0.0
    nilai_pakai = [s for s, _ in pasangan]

    # FIX BUG CRASH: dulu total_bobot hanya menjumlah bobot numeric, tapi jalur
    # terbobot tetap mengiterasi SEMUA pasangan -> s * None = TypeError, dan satu
    # "bobot: null" hasil suntingan manual menumbangkan seluruh pipeline
    # compile (bukan hanya MK itu). Sekarang entri bobot non-numeric di-skip
    # (sama seperti sesi None), dengan fallback rata-rata sederhana.
    pasangan_bobot = [
        (s, b) for s, b in pasangan
        if isinstance(b, (int, float)) and not isinstance(b, bool)
    ]
    total_bobot = sum(b for _, b in pasangan_bobot)
    if not pasangan_bobot or total_bobot <= 0:
        return round(sum(nilai_pakai) / len(nilai_pakai), 1)
    return round(
        sum(s * b for s, b in pasangan_bobot) / total_bobot, 1
    )


def cakupan_bobot(session_scores, bobot_sesi):
    """Persen bobot yang benar-benar punya catatan (100 = lengkap).

    Dipakai untuk menahan grade selama masih ada pertemuan yang belum diinput.
    """
    if not bobot_sesi:
        terisi = sum(1 for s in session_scores if s is not None)
        return round((terisi / len(session_scores)) * 100, 1) if session_scores else 0.0
    total = sum(b for b in bobot_sesi if isinstance(b, (int, float)))
    if total <= 0:
        return 0.0
    terisi = sum(
        b for s, b in zip(session_scores, bobot_sesi)
        if s is not None and isinstance(b, (int, float))
    )
    return round((terisi / total) * 100, 1)


def validasi_bobot(bobot_sesi, keterangan=""):
    """Bobot per pertemuan harus ada, angka >= 0, dan berjumlah 100.

    Dipakai sebelum dataset dibangun supaya salah isi bobot ketahuan di depan,
    bukan diam-diam menghasilkan nilai akhir yang salah.
    """
    masalah = []
    if not bobot_sesi:
        return ["bobot sesi kosong" + (": " + keterangan if keterangan else "")]
    for i, b in enumerate(bobot_sesi, start=1):
        if not isinstance(b, (int, float)) or b < 0:
            masalah.append(
                "bobot pertemuan {0} harus angka >= 0 (dapat {1})".format(i, b)
            )
    total = sum(b for b in bobot_sesi if isinstance(b, (int, float)))
    if abs(total - 100) > 0.001:
        masalah.append(
            "total bobot harus 100, sekarang {0}".format(total)
            + (": " + keterangan if keterangan else "")
        )
    return masalah


# =============================================================================
# 4. PREDIKAT / GRADE  (ambang dari config/aturan.json)
# =============================================================================
def grade_dari_skor(avg_score: float, attendance_pct: float):
    """Kembalikan (grade, pengali_indeks_kesiapan) sesuai ambang di config."""
    for g in AT.grade_bounds():
        min_nilai = float(g.get("min_nilai", 0))
        min_hadir = g.get("min_kehadiran", None)
        if avg_score >= min_nilai and (min_hadir is None or attendance_pct >= min_hadir):
            return str(g.get("grade")), float(g.get("pengali_kesiapan", 1.0))
    bounds = AT.grade_bounds()
    if bounds:
        g = bounds[-1]
        return str(g.get("grade")), float(g.get("pengali_kesiapan", 1.0))
    return "D / Evaluasi", 0.70


class GradeTanpaTeks(KeyError):
    """Grade dari config tidak punya kalimat resminya di TEKS_GRADE."""


# Teks resmi per predikat: (predikat, status_kompetensi, kesiapan_profesi).
# Ditaruh di sini supaya satu grade tidak mungkin tampil dengan dua kalimat
# berbeda di dashboard dan di PDF.
TEKS_GRADE = {
    "A": (
        "Sangat Memuaskan / Kompeten Unggul",
        "Kompeten Unggul (Standar Rancang Bangun & Industri Kreatif)",
        "Sangat Siap & Siap Magang di Konsultan Arsitektur",
    ),
    "A-": (
        "Memuaskan / Kompeten Sangat Baik",
        "Kompeten Sangat Baik (Rekomendasi Lanjut Studio Perancangan)",
        "Siap & Menguasai Standar Gambar Kerja DED",
    ),
    "B+": (
        "Baik / Kompeten",
        "Kompeten Baik (Perlu Akselerasi Detail Struktur)",
        "Cukup Siap & Memerlukan Penguatan Volume QS",
    ),
    "B": (
        "Cukup Baik",
        "Kompeten Cukup (Asistensi Mandiri Lanjutan)",
        "Perlu Pengayaan Praktik Pemodelan Digital",
    ),
    "C": (
        "Kurang (Perlu Remidi & Asistensi)",
        "Perlu Bimbingan Intensif Studio",
        "Memerlukan Pengulangan Modul Dasar CAD",
    ),
    "D / Evaluasi": (
        "Kritis (Rentan Evaluasi)",
        "Intervensi Pembinaan Khusus Jurusan",
        "Fokus Peningkatan Disiplin Waktu Belajar",
    ),
    # Dipakai saat masih ada pertemuan yang datanya BELUM DIINPUT. Grade sengaja
    # ditahan supaya nilai tidak dihitung dari data yang belum lengkap.
    "Belum Lengkap": (
        "Belum Dinilai (Data Presensi Belum Lengkap)",
        "Menunggu Kelengkapan Data Nilai",
        "Grade ditahan sampai seluruh pertemuan terisi",
    ),
}

# Nama grade untuk mahasiswa yang datanya belum lengkap.
GRADE_BELUM_LENGKAP = "Belum Lengkap"


def teks_grade(grade):
    """Kalimat resmi satu grade. Fail-closed kalau grade tidak punya teks."""
    try:
        return TEKS_GRADE[grade]
    except KeyError:
        raise GradeTanpaTeks(
            "Grade '{0}' ada di config/aturan.json tetapi tidak punya kalimat "
            "resmi di TEKS_GRADE (scripts/kelas_rules.py). Tambahkan dulu, "
            "jangan biarkan dokumen resmi tanpa predikat.".format(grade)
        )


# =============================================================================
# 5. BADGE KECOCOKAN KARIER
# =============================================================================
def kategori_kecocokan_dari_skor(persen: float) -> str:
    """Satu angka -> satu label. Badge, warna, dan lebar bar selalu sama sumber.

    Dulu kategori ini diketik manual per baris matriks karier, sehingga bisa
    muncul "Sangat Tinggi" untuk skor 67%.
    """
    if persen >= 95:
        return "Sangat Tinggi"
    if persen >= 85:
        return "Tinggi"
    if persen >= 70:
        return "Sedang"
    return "Rendah"

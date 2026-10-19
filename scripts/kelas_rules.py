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
        elif tipe == "kehadiran_min" and persentase < nilai:
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


def pertemuan_dihitung_hadir(slot_hadir: int, slot_total: int) -> bool:
    """True bila 1 pertemuan dihitung "hadir".

    Ambangnya `kehadiran.min_slot_ratio_hadir` di config (default 50%):
    2 dari 4 slot = hadir; 1 dari 4 = belum.
    """
    if not slot_total:
        return False
    return (slot_hadir / slot_total) >= AT.min_slot_ratio_hadir()


def status_pertemuan(slot_hadir: int, slot_total: int) -> str:
    """Label jujur untuk satu pertemuan: Hadir / Sebagian / Alpha."""
    if not slot_total:
        return "-"
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
      * Bobot sesi dipakai. Sesi tersibuk dihargai lebih tinggi.

    Bila bobot tidak lengkap/tidak cocok jumlahnya, jatuh ke rata-rata
    sederhana supaya tidak crash - dan itu memang bukan jalur normal.
    """
    if not session_scores:
        return 0.0
    if not bobot_sesi or len(bobot_sesi) != len(session_scores):
        return round(sum(session_scores) / len(session_scores), 1)
    total_bobot = sum(bobot_sesi)
    if total_bobot <= 0:
        return round(sum(session_scores) / len(session_scores), 1)
    return round(
        sum(s * b for s, b in zip(session_scores, bobot_sesi)) / total_bobot, 1
    )


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
        "Kompeten Unggul (Memenuhi Standar Studio IAI)",
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
}


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

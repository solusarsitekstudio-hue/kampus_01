"""
kelas_rules.py - SATU-SATUNYA SUMBER ATURAN AKADEMIK
====================================================
Modul ini berisi aturan yang HARUS sama di seluruh sistem: cara menghitung
nilai akhir, siapa yang masuk kategori at-risk, dan bagaimana kategori
kecocokan karier ditentukan.

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

Catatan: dashboard (public/app.js) memakai aturan yang SAMA, tetapi angka
hasil hitungannya dibaca dari data/academic_data.json (field `at_risk` dan
`alasan_at_risk`), jadi tidak ada logika yang diduplikasi ke JavaScript.
"""

# =============================================================================
# 1. DETEKSI DINI AT-RISK
# =============================================================================
# At-Risk  <=>  (Alpha >= 2x)  ATAU  (Kehadiran < 75%)
AT_RISK_ALPHA_MIN = 2
AT_RISK_KEHADIRAN_MIN = 75.0


def at_risk_reasons(alpha: int, persentase: float) -> list:
    """Alasan kenapa mahasiswa masuk kategori at-risk (bisa lebih dari satu)."""
    reasons = []
    if alpha >= AT_RISK_ALPHA_MIN:
        reasons.append(f"Alpha {alpha}x")
    if persentase < AT_RISK_KEHADIRAN_MIN:
        reasons.append(f"Kehadiran {persentase}%")
    return reasons


def is_at_risk(alpha: int, persentase: float) -> bool:
    """True bila Alpha >= 2x ATAU kehadiran < 75%."""
    return bool(at_risk_reasons(alpha, persentase))


# =============================================================================
# 2. PERHITUNGAN NILAI AKHIR
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


# =============================================================================
# 3. PREDIKAT / GRADE
# =============================================================================
# Rantai ambang batas, dipakai di scripts/parse_data.py.
# Urutan penting: cek dari nilai tertinggi ke terendah.
GRADE_BOUNDARIES = [
    # (min nilai, min kehadiran, grade, pengali indeks kesiapan)
    (85, 80, "A", 0.98),
    (80, 75, "A-", 0.96),
    (75, 75, "B+", 0.92),
    (70, None, "B", 0.88),
    (60, None, "C", 0.80),
    (0, None, "D / Evaluasi", 0.70),
]


def grade_dari_skor(avg_score: float, attendance_pct: float):
    """Kembalikan (grade, pengali_indeks_kesiapan) sesuai ambang batas."""
    for min_nilai, min_hadir, grade, pengali in GRADE_BOUNDARIES:
        if avg_score >= min_nilai and (min_hadir is None or attendance_pct >= min_hadir):
            return grade, pengali
    return "D / Evaluasi", 0.70


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


# =============================================================================
# 4. BADGE KECOCOKAN KARIER
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

"""bidang.py - KATEGORI BIDANG MK + DIMENSI KHAS BIDANG (keputusan user 2026-10-21).

KONSEP "MK TERKUAT -> AI ANALISIS -> POTENSI"
---------------------------------------------
Analisis potensi mahasiswa TIDAK lagi murni rata-rata semua MK. Urutannya:
  1) MK dikelompokkan ke 5 KANAL BIDANG desain (DESAIN, TEKNOLOGI, STRUKTUR,
     LINGKUNGAN, HUMANAS) via keyword kunci/nama MK di tree.
  2) Cluster terkuat = kanal dengan rata-rata nilai tertinggi (dedup MK
     duplikat antar-tahun berdasar nama MK, jadi MK kembar tidak menimbang
     ganda).
  3) MK teratas di kanal itu jadi "kasus utama" narasi.
  4) DIMENSI KHAS BIDANG (3 dim per kanal) dihitung dengan TRAFO estimasi
     jujur: 70% rata nilai MK sekanal + 30% refleksi ke radar generik
     (diagnosis v3). SEMUA dilabel "estimasi" - tidak pernah tampil sebagai
     fakta terukur.
  5) Matriks karier sepanjang kuliah diberi BONUS SEBIDANG (+4 kecocokan
     untuk karier sekanal, clamp cap karier) - karier lain tetap tampil.

ATURAN
------
* Pemetaan keyword WAJIB kunci/nama MK NYATA di tree (30 MK - diperiksa
  2026-10-21). MK baru yang tidak kena keyword apapun -> fallback HUMANAS
  (sistem tetap jalan, tidak fail).
* Dimensi khas SELALU sumber "estimasi" (keputusan user). Nilai generik
  radar yang benar-benar terukur tidak digantikan, hanya didekati lebih.
* Kanal & label dim di sini dipakai diagnosis.py (matriks karier) dan
  portofolio.py (analisis potensi) - SATU SUMBER.
"""

# --------------------------------------------------------------------------- #
# Dimensi khas bidang: (id_dim, label_indonesia, dim_radal_generik_refleksi)
# --------------------------------------------------------------------------- #
_DIM_BIDANG = {
    "DESAIN": [
        ("konsep_form_program", "Konsep Form & Program", "logika_ruang_struktur"),
        ("estetika_tampak", "Estetika Tampak", "penguasaan_cad"),
        ("spasial_fungsional", "Spasial & Fungsional", "logika_ruang_struktur"),
    ],
    "TEKNOLOGI": [
        ("presisi_cad", "Presisi CAD & Dokumentasi", "ketelitian_detail"),
        ("manajemen_layer", "Manajemen Layer & Standar", "penguasaan_cad"),
        ("volume_qs", "Perhitungan Volume QS", "ketelitian_detail"),
    ],
    "STRUKTUR": [
        ("logika_beban", "Logika Distribusi Beban", "logika_ruang_struktur"),
        ("material_konstruksi", "Material & Metode Konstruksi", "ketelitian_detail"),
        ("detail_praktik", "Detail Praktik Lapangan", "kedisiplinan_asistensi"),
    ],
    "LINGKUNGAN": [
        ("kenyamanan_termal", "Kenyamanan Termal & Alami", "logika_ruang_struktur"),
        ("sistem_utilitas", "Sistem Utilitas Bangunan", "logika_ruang_struktur"),
        ("berkelanjutan", "Desain Berkelanjutan", "manajemen_waktu"),
    ],
    "HUMANAS": [
        ("nalar_sejarah", "Nalar Historis & Sejarah", "manajemen_waktu"),
        ("etika_regulasi", "Etika & Regulasi Profesi", "kedisiplinan_asistensi"),
        ("riset_komunikasi", "Penelitian & Komunikasi", "ketelitian_detail"),
    ],
}

_TANPA_KANAL = "HUMANAS"  # fallback MK yang tidak kena keyword apapun

# Keyword urutan penting: kanal pertama yang kena menang. DESAIN ditaruh
# duluan supaya "Pengantar Lingkungan Binaan" (teori perancangan) masuk
# DESAIN, bukan LINGKUNGAN yang keyword-nya "LINGKUNGAN".
_KEYWORDS = [
    ("DESAIN", ("STUDIO", "DESAIN", "PERANCANGAN", "TATA RUANG", "LAMSKAP",
                "LANSKAP", "PENGANTAR", "SKRIPSI", "TUGAS AKHIR", "INTERIOR")),
    ("HUMANAS", ("SEJARAH", "HUKUM", "ETIKA", "EKONOMI", "METODOLOGI",
                 "PRAKTIK PROFESI", "MAGANG")),
    ("STRUKTUR", ("STRUKTUR", "KONSTRUKSI")),
    ("LINGKUNGAN", ("FISIKA", "MATEMATIKA", "TROPIS", "UTILITAS", "LINGKUNGAN")),
    ("TEKNOLOGI", ("APLIKASI", "GAMBAR TEKNIK", "BIM", "DIGITAL", "MATERIAL")),
]

# Kanal biar bisa dipetakan sama dengan tag karier di diagnosis.py.
DISPLAY_KANAL = {
    "DESAIN": "Studio Desain & Perancangan",
    "TEKNOLOGI": "Teknologi & Komputer Arsitektur",
    "STRUKTUR": "Struktur & Konstruksi",
    "LINGKUNGAN": "Bangunan, Lingkungan & Sains",
    "HUMANAS": "Humaniora, Profesi & Manajemen",
}

BONUS_KARIER_SEBIDANG = 4.0  # +4 kecocokan karier sekanal (clamp cap karier)

def kanal_dari_mk(kunci_mk, nama_mk=""):
    """Kanal bidang dari kunci/nama MK. Fallback HUMANAS + keyword bulat."""
    teks = "{0} {1}".format(kunci_mk or "", nama_mk or "").upper()
    for kanal, kw in _KEYWORDS:
        for k in kw:
            if k in teks:
                return kanal
    return _TANPA_KANAL


def dimensi_kanal(kanal):
    """Daftar dim khas: [(id, label, dim_radal_refleksi), ...]."""
    return _DIM_BIDANG.get(kanal, _DIM_BIDANG[_TANPA_KANAL])


def nama_kanal(kanal):
    return DISPLAY_KANAL.get(kanal, DISPLAY_KANAL[_TANPA_KANAL])

"""diagnosis.py - Mesin Diagnosis v3: 100% SINYAL NYATA (keputusan user 2026-10-21).

KENAPA MODUL INI ADA
--------------------
Dulu "AI diagnosis" di parse_data.py diangkat dari PERSONA NPM
(scripts/persona.py -> tentukan_archetype: digit NPM mod 7/mod 4 + 3 override
manual), lalu tiap archetype mendapat 4 paragraf tetap + radar angka tetap.
Akibatnya: mahasiswa dengan alpha 2x & hadir 68% bisa diberi label
"KOMPETENSI STABIL & BERKEMBANG" - kontradiksi dengan badge AT-RISK karena dua
sistem (persona vs data) tidak pernah berbicara.

Sekarang klasifikasi, radar kompetensi, dan matriks karier dihitung dari
SINYAL KINERJA AKTUAL: nilai terbobot, kehadiran slot, alpha, konsistensi skor
sesi, dan kelengkapan data. Aturan at-risk & grade TETAP satu sumber di
kelas_rules. persona.py TIDAK disentuh - masih dipakai generator nilai
sintetis + tests/test_seed_per_mk.py.

ATURAN
------
* Deterministik: RNG SAMA SEKALI tidak dipakai. Mahasiswa dengan sinyal sama
  selalu mendapat diagnosis sama - ditandai hash "tanda_sinyal".
* Fail-closed: data belum lengkap -> grade/archetype "menyala" (ditahan),
  radar turun ke nilai estimasi yang DILABELI, bukan berpura-pura terukur.
* Sumber jujur: tiap dim radar menyertakan "terukur" / "estimasi" supaya UI
  bisa menandain - tidak ada dimensi yang karangan tapi dipamerkan sebagai
  fakta.
* Narasi: templat v2 - kalimat disusun DARI ANGKA (bukti, arah, rekomendasi
  spesifik ke dim terlemah), bukan paragraf slot yang identik semua anak.
"""

import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kelas_rules as KR  # noqa: E402
import bidang as BIDANG  # noqa: E402  (kanal bidang - bonus karier sebidang)

# --------------------------------------------------------------------------- #
# Ambang klasifikasi (konsentrasi di sini, BUKAN disebarkan di template).
# Nilai = nilai terbobot (0-100), kehadiran = persen slot (0-100).
# --------------------------------------------------------------------------- #
AMBANG = {
    "star":      {"nilai": 85.0, "kehadiran": 90.0},
    "high":      {"nilai": 80.0, "kehadiran": 85.0},
    "normal":    {"nilai": 70.0, "kehadiran": 75.0},
    # Deviasi baku skor sesi di bawah ini = konsisten (kualitas, bukan keberuntungan).
    "konsistensi": {"deviasi": 8.0},
    # Pertemuan dengan skor valid kurang dari ini tidak layak jadi dasar konsistensi.
    "min_skor_konsistensi": 4,
}

_CATAT = {
    "star": "PRESTASI OPTIMAL",
    "high": "PRESTASI SANGAT BAIK",
    "normal": "KOMPETENSI STABIL & BERKEMBANG",
    "moderate_absent": "KEHADIRAN PERLU DIPERKOKOH",
    "perlu_penguatan": "TEKNIS GAMBAR PERLU DIPERKUAT",
    "at_risk": "POTENSI BESAR BUTUH PENDAMPINGAN",
    "belum_lengkap": "MENUNGGU PELAPORAN LENGKAP",
}
_COLOR = {
    "star": "emerald", "high": "sky", "normal": "emerald",
    "moderate_absent": "amber", "perlu_penguatan": "amber",
    "at_risk": "rose", "belum_lengkap": "slate",
}

_LABEL_DIM = {
    "penguasaan_cad": "penguasaan lingkungan CAD",
    "ketelitian_detail": "ketelitian detail gambar",
    "kedisiplinan_asistensi": "kedisiplinan asistensi",
    "logika_ruang_struktur": "logika ruang & struktur",
    "manajemen_waktu": "manajemen waktu",
}


# --------------------------------------------------------------------------- #
# Perekat angka
# --------------------------------------------------------------------------- #
def _rapat(v, lo=0.0, hi=100.0):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return max(lo, min(hi, v))


def _deviasi(skor):
    """Deviasi baku (populasi) dari skor valid. Butuh >= ambang sampel."""
    bersih = [float(s) for s in (skor or []) if s is not None]
    if len(bersih) < AMBANG["min_skor_konsistensi"]:
        return None
    rata = sum(bersih) / len(bersih)
    return math.sqrt(sum((s - rata) ** 2 for s in bersih) / len(bersih))


# --------------------------------------------------------------------------- #
# 1) SINYAL - kumpulan angka kinerja satu mahasiswa pada satu MK
# --------------------------------------------------------------------------- #
def sinyal(nilai, kehadiran, alpha, skor_sesi=None, data_lengkap=True,
           cakupan_bobot=None):
    """Sinyal kinerja terkanonik. Input None -> ditahan, tidak ditebak."""
    sig = {
        "nilai": _rapat(nilai),
        "kehadiran": _rapat(kehadiran),
        "alpha": int(alpha or 0),
        "deviasi_skor": _deviasi(skor_sesi),
        "data_lengkap": bool(data_lengkap),
        "cakupan_bobot": _rapat(cakupan_bobot, 0, 1),
    }
    tanda = hashlib.sha1(
        json.dumps(sig, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    sig["tanda_sinyal"] = tanda
    return sig


# --------------------------------------------------------------------------- #
# 2) KLASIFIKASI - archetype DARI SINYAL (urutan keputusan fail-closed)
# --------------------------------------------------------------------------- #
def klasifikasi(sig):
    """Urutan keputusan:
    1. belum_lengkap - data belum diinput semua (tak menuduh, ditahan)
    2. at_risk      - ATURAN tunggal kelas_rules (alpha>=2 ATAU hadir<75%)
    3. star         - nilai & kehadiran tinggi sekaligus + konsisten
    4. high         - nilai & kehadiran baik
    5. perlu_penguatan - hasil belajar rendah tapi disiplin tidak bermasalah
    6. moderate_absent - kehadiran menengah (alpha kecil ATAU pct di bawah 85)
    7. normal       - sisanya
    """
    if not sig["data_lengkap"] and (sig["kehadiran"] is None or sig["nilai"] is None):
        return "belum_lengkap"
    if KR.is_at_risk(sig["alpha"], sig["kehadiran"]):
        return "at_risk"
    if sig["nilai"] is None:
        return "belum_lengkap"
    nilai = sig["nilai"]
    pct = sig["kehadiran"] if sig["kehadiran"] is not None else 0.0

    if nilai >= AMBANG["star"]["nilai"] and pct >= AMBANG["star"]["kehadiran"]:
        # Syarat ekstra star: konsisten (deviasi rendah) bila sampel cukup -
        # nilai tinggi hasil keberuntungan 1-2 pertemuan tidak langsung dicap star.
        dev = sig["deviasi_skor"]
        if dev is None or dev <= AMBANG["konsistensi"]["deviasi"]:
            return "star"
    if nilai >= AMBANG["high"]["nilai"] and pct >= AMBANG["high"]["kehadiran"]:
        return "high"
    if nilai < AMBANG["normal"]["nilai"]:
        return "perlu_penguatan"
    if sig["alpha"] >= 1 or pct < AMBANG["normal"]["kehadiran"]:
        return "moderate_absent"
    if nilai >= AMBANG["normal"]["nilai"] and pct >= AMBANG["normal"]["kehadiran"]:
        return "normal"
    return "moderate_absent"


# --------------------------------------------------------------------------- #
# 3) RADAR KOMPETENSI TERUKUR (nilai int + label sumber per dim)
# --------------------------------------------------------------------------- #
def radar(sig):
    """Dimensi diturunkan dari sinyal yang memang punya bukti datanya.

    Kembalian: (nilai_dict, sumber_dict). nilai_dict tetap int murni supaya
    generate_radar_svg (PDF) & akademik.kompetensi tidak berubah skema;
    sumber_dict untuk kejujuran di UI ("terukur"/"estimasi").
    """
    nilai = sig["nilai"]
    pct = sig["kehadiran"]
    dev = sig["deviasi_skor"]
    alpha = sig["alpha"]

    sumber = {}
    keluar = {}

    # Penguasaan CAD: langsung dari nilai terbobot studio (gabungan tugas lab).
    if nilai is not None:
        keluar["penguasaan_cad"] = int(round(_rapat(nilai)))
        sumber["penguasaan_cad"] = "terukur"
    else:
        keluar["penguasaan_cad"] = 60
        sumber["penguasaan_cad"] = "estimasi"

    # Ketelitian: kestabilan hasil (deviasi rendah = kerja rapi sistematis).
    if dev is not None:
        keluar["ketelitian_detail"] = int(round(_rapat(85.0 - dev * 1.5)))
        sumber["ketelitian_detail"] = "terukur"
    else:
        keluar["ketelitian_detail"] = 70
        sumber["ketelitian_detail"] = "estimasi"

    # Disiplin asistensi: kehadiran slot sesungguhnya (terukur). Alpha sudah
    # terbawa di persen; tanpa data kehadiran sama sekali -> estimasi netral,
    # BUKAN 0% (tidak menuduh tanpa bukti).
    if pct is not None:
        keluar["kedisiplinan_asistensi"] = int(round(_rapat(pct)))
        sumber["kedisiplinan_asistensi"] = "terukur"
    else:
        keluar["kedisiplinan_asistensi"] = 65
        sumber["kedisiplinan_asistensi"] = "estimasi"

    # Logika ruang-struktur: belum ada data khusus struktur pada kelas dasar ->
    # cubit rata-rata nilai & kehadiran sebagai proksi, JELAS dilabel estimasi.
    dasar = [v for v in (nilai, pct) if v is not None]
    if dasar:
        keluar["logika_ruang_struktur"] = int(round(_rapat(sum(dasar) / len(dasar))))
        sumber["logika_ruang_struktur"] = "estimasi"
    else:
        keluar["logika_ruang_struktur"] = 60
        sumber["logika_ruang_struktur"] = "estimasi"

    # Manajemen waktu: kehadiran tinggi + hasil konsisten = waktu terpakai baik.
    if dev is not None and pct is not None:
        keluar["manajemen_waktu"] = int(
            round(_rapat(pct * 0.6 + (100.0 - min(100.0, dev * 5.0)) * 0.4)))
        sumber["manajemen_waktu"] = "terukur"
    elif pct is not None:
        keluar["manajemen_waktu"] = int(round(_rapat(pct * 0.5 + 30.0)))
        sumber["manajemen_waktu"] = "estimasi"
    else:
        keluar["manajemen_waktu"] = 60
        sumber["manajemen_waktu"] = "estimasi"

    return keluar, sumber


# --------------------------------------------------------------------------- #
# 4) MATRIKS KARIER 10 - kecocokan dari profil radar (bukan RNG)
# --------------------------------------------------------------------------- #
# Skema item TIDAK berubah (id, profesi, bidang_industri, kecocokan_persen,
# kategori_kecocokan, analisis_potensi, keterampilan_kunci, saran_pengembangan)
# supaya PDF, video, dan tests lama tetap utuh. Yang berubah: sumber angka -
# campuran berbobot dimensi, cap per profesi agar tidak pernah "100% pasti".
_KARIER = [
    (1, "Architectural Designer (Arsitek Perancang Pratama)",
     "Biro Konsultan Perencana Arsitektur & Desain",
     (("nilai", 0.45), ("penguasaan_cad", 0.25), ("logika_ruang_struktur", 0.15),
      ("ketelitian_detail", 0.15)), 98,
     "Ananda {nama} memiliki kepekaan proporsi spasial dan kemampuan memadukan fungsi denah dengan estetika tampak yang harmonis.",
     "Konsep Tata Ruang, Denah Fungsi, Sketsa Arsitektur, AutoCAD 2D",
     "Aktif mengikuti sayembara arsitektur mahasiswa dan eksplorasi gubahan massa kontemporer."),
    (2, "BIM Modeler & Coordinator (Building Information Modeling)",
     "Kontraktor EPC Multinasional / Konsultan Rekayasa Digital",
     (("penguasaan_cad", 0.60), ("ketelitian_detail", 0.20),
      ("manajemen_waktu", 0.20)), 99,
     "Kerapian manajemen layer dan kedisiplinan koordinasi gambar digital menjadi modal kuat dalam adopsi teknologi BIM 3D/4D industri konstruksi modern.",
     "Manajemen Layer Standar IAI, Kolaborasi Xref, Logika Elemen 3D, Presisi Grid",
     "Mulai mempelajari dasar Revit Architecture dan integrasi clash detection antar disiplin struktur."),
    (3, "Quantity Surveyor (QS) & Cost Estimator Bangunan",
     "BUMN Karya / Developer Properti Skala Besar",
     (("ketelitian_detail", 0.55), ("penguasaan_cad", 0.20),
      ("nilai", 0.25)), 96,
     "Kemampuan membaca dimensi gambar dan mengekstraksi volume pekerjaan secara teliti sangat dicari di bidang estimasi anggaran proyek.",
     "Kalkulasi Volume Galian/Pondasi, Penyusunan BQ, Analisis Satuan Harga (AHSP)",
     "Perdalam rumus rekapitulasi volume otomatis menggunakan spreadsheet dan integrasi data CAD."),
    (4, "Detail Engineering Drawing (DED) Specialist",
     "Konsultan Perancangan Teknis & Rekayasa Gambar Kerja",
     (("ketelitian_detail", 0.60), ("penguasaan_cad", 0.20),
      ("manajemen_waktu", 0.20)), 97,
     "Karakter gambar yang teliti menampilkan garis potongan dan detail pondasi membuktikan kesiapan memproduksi dokumen tender konstruksi resmi.",
     "Potongan Vertikal Bangunan, Detail Sambungan Pondasi, Standar Notasi PUPR",
     "Pelajari standar etiket lembar kerja konsultan dan variasi detail sambungan struktur baja/kayu."),
    (5, "Interior Architect & Space Planner",
     "Studio Interior Arsitektur & Desain Hunian Komersial",
     (("nilai", 0.45), ("penguasaan_cad", 0.20), ("ketelitian_detail", 0.20),
      ("manajemen_waktu", 0.15)), 95,
     "Sentuhan detail pada denah hunian dan pemahaman ergonomi sirkulasi manusia menjadi modal unggul di sektor desain interior.",
     "Sirkulasi Mikro, Ergonomi Ruang Tamu/Kamar, Detail Kusen & Pintu, Material Finishing",
     "Eksplorasi katalog material lokal, tekstur finishing dinding, dan pencahayaan aksen ruang dalam."),
    (6, "3D Architectural Visualizer & CG Artist",
     "Creative Architectural Media & Studio Rendering Internasional",
     (("penguasaan_cad", 0.55), ("nilai", 0.25),
      ("manajemen_waktu", 0.20)), 95,
     "Daya bayang visual bentuk bangunan yang kuat memungkinkan transformasi gambar kerja 2D menjadi visualisasi 3D fotorealistik yang memukau klien.",
     "Pemodelan 3D Isometrik/Aksonometrik, Komposisi Kamera, Pencahayaan Alami, Visual Storytelling",
     "Tingkatkan portofolio visual dengan software render real-time (Enscape/Twinmotion/Lumion)."),
    (7, "Site Architect & Pengawas Lapangan Konstruksi",
     "Kontraktor Pelaksana Bangunan / Manajemen Konstruaksi (MK)",
     (("logika_ruang_struktur", 0.50), ("ketelitian_detail", 0.25),
      ("kedisiplinan_asistensi", 0.25)), 94,
     "Pemahaman sistem kolom praktis dan elevasi muka tanah memudahkan verifikasi kesesuaian fisik lapangan dengan dokumen gambar kerja.",
     "Verifikasi Gambar As-Built, Pengawasan Mutu Beton, Deteksi Kesalahan Elevasi Lapangan",
     "Ikuti magang lapangan di proyek konstruksi bertingkat untuk mengasah ketegasan supervisi."),
    (8, "Landscape Architect Assistant",
     "Studio Arsitektur Lansekap & Perencanaan Wilayah",
     (("nilai", 0.40), ("logika_ruang_struktur", 0.30),
      ("manajemen_waktu", 0.15), ("kedisiplinan_asistensi", 0.15)), 92,
     "Kepekaan terhadap kontur tapak dan transisi ruang luar ke ruang dalam mendukung perancangan lansekap tapak berkelanjutan.",
     "Tata Hijau, Analisis Orientasi Matahari & Angin, Drainase Tapak, Desain Hardscape",
     "Pelajari jenis tanaman tropis arsitektural dan sistem perkerasan ramah serapan air tanah."),
    (9, "Green Building & Sustainable Design Specialist",
     "Konsultan Bangunan Hijau & Sertifikasi Efisiensi Energi",
     (("logika_ruang_struktur", 0.45), ("nilai", 0.30),
      ("ketelitian_detail", 0.25)), 93,
     "Penerapan ventilasi silang pada denah dan perlindungan bukaan dinding menunjukkan intuisi desain pasif hemat energi yang dibutuhkan industri saat ini.",
     "Desain Pasif Tropis, Pencahayaan Alami Optimal, Shading Fasad, Efisiensi Energi",
     "Pahami pedoman Greenship GBCI dan simulasi komputasi aliran udara dalam bangunan."),
    (10, "Project Planner & Kontraktor Mandiri (Design & Build)",
     "Wirausaha Kreatif Sektor Jasa Rancang Bangun",
     (("nilai", 0.35), ("penguasaan_cad", 0.25), ("logika_ruang_struktur", 0.20),
      ("manajemen_waktu", 0.20)), 95,
     "Penguasaan paket lengkap dari gambar arsitektur, potongan struktur, hingga perhitungan volume biaya memberikan modal independen untuk mendirikan biro sendiri.",
     "Penguasaan End-to-End Desain ke Konstruksi, Komunikasi Klien, Negosiasi Anggaran, Manajemen Tim",
     "Bangun jejaring dengan rekan sipil/mekanikal dan kumpulkan portofolio proyek riil sejak masa kuliah."),
]


# Kanal bidang tiap karier (SATU SUMBER scripts/bidang.py) - dasar bonus
# sebidang (keputusan user 2026-10-21): karier sekanal +4, selainnya tetap.
_KANAL_KARIER = {
    1: "DESAIN", 5: "DESAIN", 8: "DESAIN",
    2: "TEKNOLOGI", 3: "TEKNOLOGI", 4: "TEKNOLOGI", 6: "TEKNOLOGI",
    7: "STRUKTUR", 9: "LINGKUNGAN", 10: "HUMANAS",
}


def matriks_karier(radar_nilai, nama, bidang_terkuat=None):
    """Kecocokan = campuran berbobot dimensi radar, cap per profesi. Tanpa RNG:
    profil sama -> peringkat sama. Kategori tetap dari satu sumber kelas_rules.

    `bidang_terkuat` kanal dari bidang.py: karier SEKANAL dapat bonus
    BIDANG.BONUS_KARIER_SEBIDANG (dichalk sebelum cap karier), karier kanal
    lain tetap tampil dengan bobot dasarnya.
    """
    hasil = []
    for _id, profesi, bidang, bobot, cap, analisis, keterampilan, saran in _KARIER:
        skor = 0.0
        for dim, koef in bobot:
            skor += float(radar_nilai.get(dim, 0)) * koef
        if bidang_terkuat and _KANAL_KARIER.get(_id) == bidang_terkuat:
            skor += BIDANG.BONUS_KARIER_SEBIDANG
        kecocokan = min(cap, max(1.0, round(skor, 1)))
        hasil.append({
            "id": _id,
            "profesi": profesi,
            "bidang_industri": bidang,
            "kecocokan_persen": kecocokan,
            "kategori_kecocokan": KR.kategori_kecocokan_dari_skor(kecocokan),
            "analisis_potensi": analisis.format(nama=nama),
            "keterampilan_kunci": keterampilan,
            "saran_pengembangan": saran,
        })
    hasil.sort(key=lambda c: (-c["kecocokan_persen"], c["id"]))
    return hasil


# --------------------------------------------------------------------------- #
# 5) NARASI TEMPLAT v2 - kalimat DIBANGUN dari angka, bukan slot tetap
# --------------------------------------------------------------------------- #
def _fmt(v, satuan=""):
    if v is None:
        return "belum lengkap"
    return "{0:g}{1}".format(float(v), satuan)


def _dim_ujung(radar_nilai):
    rapi = sorted(radar_nilai.items(), key=lambda kv: (-kv[1], kv[0]))
    kuat = rapi[0]
    lemah = rapi[-1]
    return (_LABEL_DIM[kuat[0]], kuat[1], _LABEL_DIM[lemah[0]], lemah[1])


def suara_sebab_at_risk(sig):
    """Sebab at-risk dari ATURAN yang sama (kelas_rules), bukan tebakan."""
    sebab = KR.at_risk_reasons(sig["alpha"], sig["kehadiran"])
    if sebab:
        return "; ".join(sebab)
    return "indikator risiko terbaca dari catatan kehadiran"


def narasi(arc, sig, radar_nilai, nama, nama_mk=""):
    """Paragraf dinamis: nama + angka bukti + arah + langkah konkret.
    Gaya formal seperti versi lama supaya dokumen resmi tetap patut."""
    pct = sig["kehadiran"]
    nilai = sig["nilai"]
    alpha = sig["alpha"]
    dev = sig["deviasi_skor"]
    d_kuat, v_kuat, d_lemah, v_lemah = _dim_ujung(radar_nilai)
    mk = f" pada mata kuliah {nama_mk}" if nama_mk else ""

    # --- analisis karakter spasial -------------------------------------------
    kalimat_kualitas = (
        f"stabilitas hasil belajarnya terjaga (deviasi skor {dev:.1f})"
        if dev is not None else "konsistensi antar pertemuan masih diuji"
    )
    if arc == "star":
        karakter = (
            f"Ananda {nama} menunjukkan penguasaan lingkungan CAD yang cemerlang{mk} "
            f"({_fmt(nilai)} nilai terbobot) dengan kehadiran studio {_fmt(pct, '%')} slot "
            f"dan {kalimat_kualitas}. Daya tangkap konsep denah hingga detail tampak dikerjakan "
            f"dengan presisi, dan {d_kuat} (skor {v_kuat}) menjadi penanda terkuat "
            f"profil kompetensinya."
        )
    elif arc == "at_risk":
        sebab = suara_sebab_at_risk(sig)
        karakter = (
            f"Ananda {nama} memiliki potensi yang layak disiapkan, tetapi capaian semester ini "
            f"belum mengikuti ritme yang diharapkan ({sebab}). Nilai terbobot {_fmt(nilai)} "
            f"dengan kehadiran {_fmt(pct, '%')} slot dan {alpha} hari alpha; "
            f"{d_lemah} saat ini mencatat skor {v_lemah}, sementara modal terbaiknya masih "
            f"pada {d_kuat} (skor {v_kuat})."
        )
    elif arc == "perlu_penguatan":
        karakter = (
            f"Ananda {nama} hadir baik di studio ({_fmt(pct, '%')} slot, {alpha} hari alpha), "
            f"tetapi nilai terbobot {_fmt(nilai)} menunjukkan penguasaan teknik gambar perlu "
            f"diperkuat. Indikasi terbaca jelas: {d_lemah} (skor {v_lemah}) turut menahan "
            f"ketajaman hasil akhirnya."
        )
    else:
        sifat = ("stabil" if (dev is not None and dev <= AMBANG["konsistensi"]["deviasi"])
                 else "sedang berkembang")
        karakter = (
            f"Ananda {nama} memperlihatkan hasil belajar yang {sifat}{mk}: nilai terbobot "
            f"{_fmt(nilai)}, kehadiran {_fmt(pct, '%')} slot, dan {alpha} hari alpha. "
            f"Kekuatan utamanya pada {d_kuat} (skor {v_kuat}); sisi yang perlu diasah adalah "
            f"{d_lemah} (skor {v_lemah})."
        )

    # --- potensi ke depan -------------------------------------------------------
    if arc == "star":
        potensi = (
            f"Fondasi gambar kerja digital yang matang{mk} membuka peluang menjadi asisten studio "
            f"perancangan, delegasi sayembara desain arsitektur tingkat nasional, dan melompat ke "
            f"teknologi BIM/Revit. Diproyeksikan mampu memimpin tim studio dan menghasilkan karya "
            f"akhir bertaraf sayembara."
        )
    elif arc == "at_risk":
        potensi = (
            f"Dengan pendampingan yang tepat, modal {d_kuat} ananda dapat cepat pulih; "
            f"begitu kehadiran dan ritme latihan diperbaiki, peluang pada bidang perancangan "
            f"maupun koordinasi gambar teknis tetap terbuka lebar."
        )
    elif arc == "perlu_penguatan":
        potensi = (
            f"Disiplin hadir yang sudah baik adalah modal utama: begitu {d_lemah} naik lewat "
            f"latihan terstruktur, ananda berpeluang menanjak ke bidang yang menuntut presisi dokumen."
        )
    else:
        potensi = (
            f"Perkembangan konsisten tiap pertemuan akan membawa ananda ke bidang yang selaras "
            f"dengan {d_kuat}-nya; skor hasil yang stabil adalah prasyarat menuju karier "
            f"profesional yang ketat menuntut ketepatan waktu pekerjaan gambar."
        )

    # --- catatan untuk mahasiswa -------------------------------------------------
    target_lemah = min(95, max(70, int(v_lemah or 0) + 10))
    ambang_hadir = "di atas 90%" if (pct or 0) >= 90 else "di atas 85%"
    catatan = (
        f"Prioritas latihan: tingkatkan {d_lemah} hingga minimal {target_lemah} pada radar "
        f"berikutnya, lalu jaga kehadiran {ambang_hadir}. Dokumentasikan setiap karya gambar kerja "
        f"ke portofolio digital profesional sejak dini."
    )

    # --- panduan wali murid --------------------------------------------------------
    if arc in ("at_risk", "perlu_penguatan"):
        imbuhan = (
            "Hasil yang belum membaik perlu dipantau bersama: komunikasi rutin dengan dosen "
            "pengasuh serta pendampingan jam belajar di rumah sangat membantu."
        )
    else:
        imbuhan = (
            "Di rumah, dukung suasana belajar yang kondusif dan pastikan perangkat kerja digital "
            "memadai; setiap kemajuan kecil layak diapresiasi agar motivasi terjaga."
        )
    panduan = (
        f"Bapak/Ibu diberi rangkuman angka terpenting: kehadiran {_fmt(pct, '%')}, "
        f"{alpha} hari alpha, dan nilai terbobot {_fmt(nilai)}. {imbuhan} "
        f"Doa dan kehangatan keluarga adalah energi terbesar bagi ananda."
    )

    kekuatan = karakter[:180] + "..." if len(karakter) > 180 else karakter
    return karakter, potensi, catatan, panduan, kekuatan


# --------------------------------------------------------------------------- #
# 6) HASIL SATU PAKET - dipakai parse_data.py (skema ai_diagnosis tetap)
# --------------------------------------------------------------------------- #
def hasil(nama, nilai, kehadiran, alpha, skor_sesi=None, data_lengkap=True,
          cakupan_bobot=None, nama_mk=""):
    """Satu panggilan -> (archetype, radar_int, ai_diagnosis_dict, meta).

    Skema ai_diagnosis SAMA seperti versi lama (analisis_karakter_spasial,
    potensi_kedepan, catatan_khusus_mahasiswa, panduan_wali_murid, kekuatan,
    status_alert, alert_color, matriks_karier_10) plus tambahan yang TIDAK
    merusak konsumen lama: radar_sumber dan mesin (sumber + tanda_sinyal).
    """
    sig = sinyal(nilai, kehadiran, alpha, skor_sesi, data_lengkap, cakupan_bobot)
    arc = klasifikasi(sig)
    radar_nilai, radar_sumber = radar(sig)
    karakter, potensi, catatan, panduan, kekuatan = narasi(
        arc, sig, radar_nilai, nama, nama_mk=nama_mk)

    ai_diagnosis = {
        "analisis_karakter_spasial": karakter,
        "potensi_kedepan": potensi,
        "catatan_khusus_mahasiswa": catatan,
        "panduan_wali_murid": panduan,
        "kekuatan": kekuatan,
        "status_alert": _CATAT[arc],
        "alert_color": _COLOR[arc],
        "matriks_karier_10": matriks_karier(radar_nilai, nama),
        "radar_sumber": radar_sumber,
        "mesin": {"sumber": "templat_v3", "tanda_sinyal": sig["tanda_sinyal"],
                  "archetype": arc},
    }
    meta = {"archetype": arc, "tanda_sinyal": sig["tanda_sinyal"],
            "sumber": "templat_v3"}
    return arc, radar_nilai, ai_diagnosis, meta

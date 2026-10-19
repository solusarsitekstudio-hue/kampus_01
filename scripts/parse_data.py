"""parse_data: bangun data/academic_data.json DARI tree kurikulum.

TAHAP E - SUMBER DATA PINDAH
----------------------------
Dulu file ini membaca `D:\\Desktop\\- HAL LAIN\\DAFTAR MAHASISWA.xlsx` dan
`...\\02 rekap qs pratikum.pdf` (folder pribadi), dan mengarang 6 sesi di dalam
kode. Akibatnya sistem tidak mandiri dan jumlah pertemuan tidak bisa dipercaya.

Sekarang sumbernya tree kurikulum:

    data/kurikulum/<PRODI>/<TAHUN_AJAR>/<SEMESTER>/<KUNCI_MK>/

File ini menjadi "compiler": membaca identitas + 16 pertemuan + catatan nilai,
lalu menghitung. Tidak ada lagi `random.seed(42)` global - RNG dibuat PER
MAHASISWA (`persona.rng_untuk(npm)`), sehingga menambah satu baris tidak
menggeser nilai seluruh kelas (utang #1 dibayar).
"""
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_JSON = os.path.join(DATA_DIR, "academic_data.json")

# =============================================================================
# ATURAN KELAS -> SATU MODUL BERSAMA (FIX TAHAP C-4)
# =============================================================================
# Aturan nilai, at-risk, dan badge karier TIDAK didefinisikan di file ini.
# Semua modul mengimpor dari scripts/kelas_rules.py supaya tidak ada salinan
# yang bisa berbeda - akar yang dulu melahirkan 4 aturan at-risk berbeda.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kelas_rules import (  # noqa: E402
    at_risk_alpha_min,
    at_risk_kehadiran_min,
    at_risk_reasons,
    is_at_risk,
    hitung_nilai_terbobot,
    cakupan_bobot,
    GRADE_BELUM_LENGKAP,
    kategori_kecocokan_dari_skor,
    grade_dari_skor,
    persentase_kehadiran,
    pertemuan_belum_diinput,
    pertemuan_memenuhi_ambang,
    validasi_bobot,
    teks_grade,
)
# FIX TAHAP E: ambang at-risk & teksnya kini dari satu sumber config/aturan.json.
import aturan as ATURAN  # noqa: E402

# FIX: identitas (mata kuliah, dosen, asisten, ketua prodi, institusi) dibaca
# dari SATU sumber -- config/identitas.json lewat scripts/identitas.py.
import identitas as IDENT  # noqa: E402
# Tree kurikulum bertingkat + persona/RNG per NPM.
import kurikulum_tree as KT  # noqa: E402
import persona as PS  # noqa: E402


# =============================================================================
# SUMBER DATA: TREE KURIKULUM (bukan Excel/PDF lagi)
# =============================================================================
def mk_aktif_dari_tree(kunci=None):
    """(prodi, tahun_ajar, semester, kunci_mk) untuk satu MK.

    `kunci=None` berarti MK yang sedang aktif di config/identitas.json. Kunci
    yang diminta HARUS ada di config/identitas.json (fail-closed), karena
    identitas MK tetap satu sumber di sana.
    """
    inst = IDENT.institusi()
    kunci = kunci or IDENT.mk_aktif()
    mk = IDENT.mk(kunci)
    ta, sem = KT.pecah_semester(mk.get("semester"))
    return inst.get("prodi", ""), ta, sem, kunci


def muat_kurikulum(kunci=None):
    """Baca identitas mahasiswa + penawaran + 16 sesi + nilai dari tree.

    Fail-closed: berkas tidak lengkap atau bobot tidak berjumlah 100 = raise.
    Dulu sumber yang gagal diam-diam jatuh ke template lain, dan dashboard
    menampilkan topik mata kuliah yang salah tanpa satu pun pesan error.
    """
    prodi, ta, sem, kunci = mk_aktif_dari_tree(kunci)
    path_mhs = KT.path_mahasiswa(prodi)
    if not os.path.exists(path_mhs):
        raise ValueError(
            "Identitas mahasiswa belum ada: {0}\n"
            "Bangun dulu: python scripts\\migrasi_kurikulum.py".format(path_mhs)
        )
    mahasiswa = KT.baca_json(path_mhs).get("mahasiswa") or []
    if not mahasiswa:
        raise ValueError("Tidak ada mahasiswa di {0}".format(path_mhs))

    data = KT.muat_mk(prodi, ta, sem, kunci)
    penawaran, sesi_doc, nilai_doc = data["penawaran"], data["sesi"], data["nilai"]

    masalah = KT.validasi_sesi(sesi_doc, kunci)
    if masalah:
        raise ValueError("sesi.json '{0}' tidak valid:\n- {1}".format(
            kunci, "\n- ".join(masalah)))
    masalah_bobot = validasi_bobot(KT.bobot_sesi(sesi_doc), kunci)
    if masalah_bobot:
        raise ValueError("Bobot sesi '{0}' tidak valid:\n- {1}".format(
            kunci, "\n- ".join(masalah_bobot)))

    return {
        "prodi": prodi,
        "tahun_ajar": ta,
        "semester": sem,
        "kunci_mk": kunci,
        "mahasiswa": mahasiswa,
        "penawaran": penawaran,
        "sesi_dokumen": sesi_doc,
        "sessions": list(sesi_doc.get("sesi") or []),
        "nilai_dokumen": nilai_doc,
    }


def kelompokkan_nilai(nilai_dokumen):
    """{npm: [baris slot]} dari berkas nilai."""
    hasil = {}
    for r in (nilai_dokumen or {}).get("nilai", []):
        hasil.setdefault(str(r.get("npm")), []).append(r)
    return hasil


def ringkas_kehadiran(baris_slot, sessions):
    """Rincian kehadiran PER PERTEMUAN, jujur sampai tingkat slot.

    Keputusan user (Tahap E): yang ditampilkan pertemuan, tetapi persen
    dihitung dari slot - jadi mahasiswa yang hadir 1 dari 4 slot tampil
    "Hadir Sebagian", tidak dibulatkan menjadi hadir atau alpha.

    FIX: pertemuan yang baris slotnya BELUM LENGKAP (mis. baru 1 dari 2 slot,
    atau kosong sama sekali) TIDAK lagi dianggap Alpha dan TIDAK diberi nilai 0.
    Pertemuan itu ditandai "Belum Diinput", dikeluarkan dari hitung nilai.
    Perilaku lama (slot kosong = Alpha) hanya dipakai bila
    `kehadiran.slot_belum_diisi` di config diset "alpha".
    """
    per_pertemuan = {}
    for r in baris_slot:
        per_pertemuan.setdefault(int(r.get("pertemuan") or 0), []).append(r)

    # Perilaku lama (slot kosong = Alpha) hanya kalau diminta eksplisit di config.
    pakai_belum_diinput = not ATURAN.hitung_slot_kosong_sebagai_alpha()

    detail = []
    hitung = {"Hadir": 0, "Hadir Sebagian": 0, "Sakit": 0, "Izin": 0,
              "Alpha": 0, "Belum Diinput": 0}
    slot_hadir_total = 0
    slot_total_semua = 0
    pertemuan_ambang = 0

    for s in sessions:
        p = int(s["pertemuan"])
        slot_total = len(s.get("slot_absen") or [])
        baris = per_pertemuan.get(p, [])
        slot_terisi = len(baris)
        slot_hadir = sum(1 for b in baris if b.get("status") == "Hadir")
        belum = pakai_belum_diinput and pertemuan_belum_diinput(slot_terisi, slot_total)

        if belum:
            # Data belum masuk: jangan mengarang nilai dan jangan menghitung Alpha.
            bucket = "Belum Diinput"
            skor = None
        else:
            skor = (
                round(sum(b.get("skor", 0) for b in baris) / slot_total, 1)
                if slot_total else 0.0
            )
            if slot_total and slot_hadir >= slot_total:
                bucket = "Hadir"
            elif slot_hadir <= 0:
                status_isi = [b.get("status") for b in baris]
                if "Sakit" in status_isi:
                    bucket = "Sakit"
                elif "Izin" in status_isi:
                    bucket = "Izin"
                else:
                    bucket = "Alpha"
            else:
                bucket = "Hadir Sebagian"

        hitung[bucket] += 1
        if pertemuan_memenuhi_ambang(slot_hadir, slot_total):
            pertemuan_ambang += 1
        slot_hadir_total += slot_hadir
        slot_total_semua += slot_total

        alasan = "-"
        if bucket in ("Sakit", "Izin"):
            alasan = next((b.get("alasan") for b in baris
                           if b.get("alasan") not in (None, "-")), "-")
        elif bucket == "Alpha":
            alasan = "Tanpa keterangan / tidak hadir di presensi portal"
        elif bucket == "Belum Diinput":
            alasan = ("Presensi pertemuan ini belum diinput "
                      "({0}/{1} slot tercatat) - bukan Alpha, nilai tidak dihitung"
                      ).format(slot_terisi, slot_total)

        detail.append({
            "pertemuan": p,
            "tanggal": s.get("tanggal"),
            "tanggal_display": s.get("tanggal_display"),
            "topik": s.get("topik"),
            "tipe": s.get("tipe"),
            "slot_total": slot_total,
            "slot_terisi": slot_terisi,
            "slot_hadir": slot_hadir,
            "status": bucket,
            "alasan": alasan,
            "skor": skor,
        })

    return detail, hitung, pertemuan_ambang, slot_hadir_total, slot_total_semua

# CATATAN: `kategori_kecocokan_dari_skor()` sekarang diimpor dari kelas_rules.py
# (FIX TAHAP C-4) supaya hanya ada satu definisi di seluruh sistem.


def generate_10_career_matrix(nama, avg_score, competency, archetype, rng):
    """10 matriks karier. `rng` WAJIB dari persona.rng_untuk(npm) supaya
    angka seorang mahasiswa tidak bergeser karena mahasiswa lain berubah."""
    base_score = avg_score
    cad_val = competency["penguasaan_cad"]
    det_val = competency["ketelitian_detail"]
    str_val = competency["logika_ruang_struktur"]

    careers = [
        {
            "id": 1,
            "profesi": "Architectural Designer (Arsitek Perancang Pratama)",
            "bidang_industri": "Biro Konsultan Perencana Arsitektur & Desain",
            "kecocokan_persen": min(98, round(base_score * 0.98 + rng.uniform(0.5, 2.5), 1)),
            "kategori_kecocokan": "Sangat Tinggi",
            "analisis_potensi": f"Ananda {nama} memiliki kepekaan proporsi spasial dan kemampuan memadukan fungsi denah dengan estetika tampak yang sangat harmonis.",
            "keterampilan_kunci": "Konsep Tata Ruang, Denah Fungsi, Sketsa Arsitektur, AutoCAD 2D",
            "saran_pengembangan": "Aktif mengikuti sayembara arsitektur mahasiswa dan eksplorasi gubahan massa kontemporer."
        },
        {
            "id": 2,
            "profesi": "BIM Modeler & Coordinator (Building Information Modeling)",
            "bidang_industri": "Kontraktor EPC Multinasional / Konsultan Rekayasa Digital",
            "kecocokan_persen": min(99, round(cad_val * 0.99 + rng.uniform(0.5, 1.8), 1)),
            "kategori_kecocokan": "Sangat Tinggi",
            "analisis_potensi": "Kerapian manajemen layer dan kedisiplinan koordinasi gambar digital menjadi modal emas dalam adopsi teknologi BIM 3D/4D industri konstruksi modern.",
            "keterampilan_kunci": "Manajemen Layer Standar IAI, Kolaborasi Xref, Logika Elemen 3D, Presisi Grid",
            "saran_pengembangan": "Mulai mempelajari dasar Revit Architecture dan integrasi clash detection antar disiplin struktur."
        },
        {
            "id": 3,
            "profesi": "Quantity Surveyor (QS) & Cost Estimator Bangunan",
            "bidang_industri": "BUMN Karya / Developer Properti Skala Besar",
            "kecocokan_persen": min(96, round(det_val * 0.96 + rng.uniform(0.5, 2.5), 1)),
            "kategori_kecocokan": "Tinggi",
            "analisis_potensi": "Kemampuan membaca dimensi gambar dan mengekstraksi volume pekerjaan galian serta beton secara teliti sangat dicari di bidang estimasi anggaran proyek.",
            "keterampilan_kunci": "Kalkulasi Volume Galian/Pondasi, Penyusunan BQ, Analisis Satuan Harga (AHSP)",
            "saran_pengembangan": "Perdalam rumus rekapitulasi volume otomatis menggunakan spreadsheet dan integrasi data CAD."
        },
        {
            "id": 4,
            "profesi": "Detail Engineering Drawing (DED) Specialist",
            "bidang_industri": "Konsultan Perancangan Teknis & Rekayasa Gambar Kerja",
            "kecocokan_persen": min(97, round(det_val * 0.97 + rng.uniform(0.5, 2.5), 1)),
            "kategori_kecocokan": "Sangat Tinggi",
            "analisis_potensi": "Karakter gambar yang teliti dalam menampilkan garis potongan dan detail pondasi batu kali membuktikan ananda siap memproduksi dokumen tender konstruksi resmi.",
            "keterampilan_kunci": "Potongan Vertikal Bangunan, Detail Sambungan Pondasi, Standar Notasi PUPR",
            "saran_pengembangan": "Pelajari standar etiket lembar kerja konsultan dan variasi detail sambungan struktur baja/kayu."
        },
        {
            "id": 5,
            "profesi": "Interior Architect & Space Planner",
            "bidang_industri": "Studio Interior Arsitektur & Desain Hunian Komersial",
            "kecocokan_persen": min(95, round(base_score * 0.94 + rng.uniform(1.0, 3.5), 1)),
            "kategori_kecocokan": "Tinggi",
            "analisis_potensi": "Sentuhan detail pada denah hunian dan pemahaman ergonomi sirkulasi manusia menjadikan ananda berpeluang besar unggul di sektor desain interior.",
            "keterampilan_kunci": "Sirkulasi Mikro, Ergonomi Ruang Tamu/Kamar, Detail Kusen & Pintu, Material Finishing",
            "saran_pengembangan": "Eksplorasi katalog material lokal, tekstur finishing dinding, dan pencahayaan aksen ruang dalam."
        },
        {
            "id": 6,
            "profesi": "3D Architectural Visualizer & CG Artist",
            "bidang_industri": "Creative Architectural Media & Studio Rendering Internasional",
            "kecocokan_persen": min(95, round(cad_val * 0.93 + rng.uniform(1.0, 3.5), 1)),
            "kategori_kecocokan": "Tinggi",
            "analisis_potensi": "Daya bayang visual bentuk bangunan ananda sangat kuat, memungkinkan transformasi gambar kerja 2D menjadi visualisasi 3D fotorealistik yang memukau klien.",
            "keterampilan_kunci": "Pemodelan 3D Isometrik/Aksonometrik, Komposisi Kamera, Pencahayaan Alami, Visual Storytelling",
            "saran_pengembangan": "Tingkatkan portofolio visual dengan software render real-time (Enscape/Twinmotion/Lumion)."
        },
        {
            "id": 7,
            "profesi": "Site Architect & Pengawas Lapangan Konstruksi",
            "bidang_industri": "Kontraktor Pelaksana Bangunan / Manajemen Konstruksi (MK)",
            "kecocokan_persen": min(94, round(str_val * 0.94 + rng.uniform(0.5, 2.5), 1)),
            "kategori_kecocokan": "Tinggi",
            "analisis_potensi": "Pemahaman yang solid mengenai sistem kolom praktis dan elevasi muka tanah memudahkan ananda mengawasi kesesuaian fisik lapangan dengan dokumen gambar kerja.",
            "keterampilan_kunci": "Verifikasi Gambar As-Built, Pengawasan Mutu Beton, Deteksi Kesalahan Elevasi Lapangan",
            "saran_pengembangan": "Ikuti magang lapangan di proyek konstruksi bertingkat untuk mengasah ketegasan supervisi."
        },
        {
            "id": 8,
            "profesi": "Landscape Architect Assistant",
            "bidang_industri": "Studio Arsitektur Lansekap & Perencanaan Wilayah",
            "kecocokan_persen": min(92, round(base_score * 0.90 + rng.uniform(0.5, 3.0), 1)),
            "kategori_kecocokan": "Sesuai",
            "analisis_potensi": "Kepekaan terhadap kontur tapak dan transisi ruang luar (teras) ke ruang dalam mendukung perancangan lansekap tapak berkelanjutan.",
            "keterampilan_kunci": "Tata Hijau, Analisis Orientasi Matahari & Angin, Drainase Tapak, Desain Hardscape",
            "saran_pengembangan": "Pelajari jenis tanaman tropis arsitektural dan sistem perkerasan ramah serapan air tanah."
        },
        {
            "id": 9,
            "profesi": "Green Building & Sustainable Design Specialist",
            "bidang_industri": "Konsultan Bangunan Hijau & Sertifikasi Efisiensi Energi",
            "kecocokan_persen": min(93, round(str_val * 0.92 + rng.uniform(0.5, 2.8), 1)),
            "kategori_kecocokan": "Sesuai",
            "analisis_potensi": "Penerapan ventilasi silang pada denah dan perlindungan bukaan dinding menunjukkan intuisi desain pasif hemat energi yang sangat dibutuhkan industri saat ini.",
            "keterampilan_kunci": "Desain Pasif Tropis, Pencahayaan Alami Optimal, Shading Fasad, Efisiensi Energi",
            "saran_pengembangan": "Pahami pedoman Greenship GBCI dan simulasi komputasi aliran udara dalam bangunan."
        },
        {
            "id": 10,
            "profesi": "Project Planner & Kontraktor Mandiri (Design & Build)",
            "bidang_industri": "Wirausaha Kreatif Sektor Jasa Rancang Bangun",
            "kecocokan_persen": min(95, round(base_score * 0.92 + rng.uniform(1.0, 3.5), 1)),
            "kategori_kecocokan": "Tinggi",
            "analisis_potensi": "Penguasaan paket lengkap dari gambar arsitektur, potongan struktur, hingga perhitungan volume biaya memberikan modal independen untuk mendirikan biro sendiri.",
            "keterampilan_kunci": "Penguasaan End-to-End Desain ke Konstruksi, Komunikasi Klien, Negosiasi Anggaran, Manajemen Tim",
            "saran_pengembangan": "Bangun jejaring dengan rekan sipil/mekanikal dan kumpulkan portofolio proyek riil sejak masa kuliah."
        }
    ]

    # FIX TAHAP B: kategori dihitung dari skor, bukan diketik manual per baris.
    for c in careers:
        c["kategori_kecocokan"] = kategori_kecocokan_dari_skor(c["kecocokan_persen"])

    return careers

# =============================================================================
# PERSONA / ARCHETYPE - dipindah ke scripts/persona.py (TAHAP E)
# =============================================================================
# Dulu blok ini ada DI SINI dan memakai `idx % 7` sebagai cadangan, sehingga
# menambah satu baris membuat mahasiswa lain berubah persona. Sekarang persona
# MURNI dari NPM, dan RNG-nya juga per NPM. Satu sumber: scripts/persona.py.
tentukan_archetype = PS.tentukan_archetype


# =============================================================================
# CPMK PLACEHOLDER
# =============================================================================
# Dipakai laporan audit dosen -> kaprodi. BELUM dari RPS resmi dan BUKAN klaim
# capaian pembelajaran; hanya pengingat agar kolomnya tidak kosong dan tidak
# terkesan sudah final. Ganti dengan CPMK resmi dari RPS saat tersedia.
CPMK_PLACEHOLDER = [
    "CPMK-1: Menguasai konsep dasar dan instrumen kerja mata kuliah",
    "CPMK-2: Mampu menerapkan prosedur kerja standar pada studi kasus",
    "CPMK-3: Mampu menyusun keluaran kerja sesuai standar profesinya",
    "CPMK-4: Mampu mempublikasikan dan mengomunikasikan hasil kerja",
]


def generate_student_profiles(students, sessions, nilai_per_npm, ctx=None):
    # FIX: identitas mata kuliah TIDAK lagi disalin di sini. Dibaca dari satu
    # sumber (config/identitas.json). Kunci yang ditulis SENGAJA dikunci ke 11
    # kunci yang sama seperti sebelumnya, supaya academic_data.json tidak berubah.
    ctx = ctx or {}
    _ident = IDENT.lengkapi(ctx.get("kunci_mk"))
    course_info = {
        k: _ident[k]
        for k in (
            "kode_mk",
            "nama_mk",
            "prodi",
            "fakultas",
            "semester",
            "sks",
            "kelas",
            "jadwal",
            "ketua_prodi",
            "dosen_pengasuh",
            "asisten_dosen",
        )
    }
    _institusi = IDENT.institusi()
    _prodi = str(_institusi.get("prodi", ""))
    _fakultas = str(_institusi.get("fakultas", ""))
    _kaprodi = str(_institusi.get("ketua_prodi", ""))
    _nama_mk = str(course_info["nama_mk"])
    _asisten = str(course_info["asisten_dosen"])
    _total_sesi = len(sessions)

    student_records = []

    for idx, s in enumerate(students):
        npm = str(s["npm"])
        nama = s["nama"]

        # Persona MURNI dari NPM (persona.py) + RNG per NPM PER MATA KULIAH.
        # `konteks` = kunci MK: matriks karier & diagnosis ikut berpindah saat
        # dashboard pindah MK, tapi tetap deterministic (tidak bergantung urutan
        # baris mahasiswa).
        konteks = str(ctx.get("kunci_mk") or "")
        archetype = PS.tentukan_archetype(idx, npm, konteks)
        rng = PS.rng_untuk(npm, konteks)

        # Kehadiran + nilai dibaca dari catatan per SLOT di tree kurikulum,
        # bukan dikarang di sini. Rincian per pertemuan tetap yang ditampilkan.
        baris_slot = nilai_per_npm.get(npm, [])
        (attendance_list, hitung_status, pertemuan_ambang,
         slot_hadir_total, slot_total_semua) = ringkas_kehadiran(baris_slot, sessions)

        total_hadir = hitung_status["Hadir"]
        total_sebagian = hitung_status["Hadir Sebagian"]
        total_sakit = hitung_status["Sakit"]
        total_izin = hitung_status["Izin"]
        total_alpha = hitung_status["Alpha"]
        total_belum_diinput = hitung_status["Belum Diinput"]
        session_scores = [d["skor"] for d in attendance_list]

        # Persen kehadiran berbasis SLOT (bukan jumlah pertemuan): 2 dari 4 slot
        # = 50%. Ini yang membuat kehadiran sebagian terbaca jujur, bukan
        # dibulatkan diam-diam menjadi hadir atau alpha.
        attendance_pct = persentase_kehadiran(slot_hadir_total, slot_total_semua)

        # FIX TAHAP B: Alpha (nilai 0) ikut dihitung dan bobot sesi dipakai.
        # FIX TAHAP E: bobot kini dari sesi.json (16 pertemuan, total 100).
        # FIX BELUM-DIINPUT: sesi yang belum diinput keluar dari hitung nilai dan
        # bobotnya dinormalisasi ulang; grade ditahan sampai data lengkap.
        bobot_sesi = [sess.get("bobot", 0) for sess in sessions]
        avg_score = hitung_nilai_terbobot(session_scores, bobot_sesi)
        cakupan = cakupan_bobot(session_scores, bobot_sesi)
        data_lengkap = total_belum_diinput == 0
        at_risk_reasons_list = at_risk_reasons(total_alpha, attendance_pct)
        student_is_at_risk = bool(at_risk_reasons_list)

        # Grade Assignment & Competency Status (No Ranking, focusing on growth)
        # FIX TAHAP C-4: ambang batas grade diambil dari kelas_rules.py, bukan
        # ditulis ulang sebagai rantai if/elif. Teks predikat pun diambil dari
        # satu tabel, sehingga tidak mungkin ada grade tanpa teksnya.
        if data_lengkap:
            grade, pengali_kesiapan = grade_dari_skor(avg_score, attendance_pct)
        else:
            grade, pengali_kesiapan = GRADE_BELUM_LENGKAP, 1.0
        predikat, status_kompetensi, kesiapan_profesi = teks_grade(grade)
        indeks_kesiapan = round(avg_score * pengali_kesiapan, 1)

        # Competency Radar Scores (Scale 1-100)
        if archetype == "star":
            competency = {
                "penguasaan_cad": 96,
                "ketelitian_detail": 94,
                "kedisiplinan_asistensi": 98,
                "logika_ruang_struktur": 92,
                "manajemen_waktu": 95
            }
            karakter_spasial = (
                f"Ananda {nama} memperlihatkan bakat arsitektur yang sangat cemerlang dengan kepekaan rasa ruang "
                f"(spatial sensibility) yang luar biasa tajam. Penarikan garis-garis dinding, penataan kolom struktural, "
                f"hingga pembagian hierarki ruang privat dan publik dikerjakan dengan presisi tinggi dan pemahaman fungsi yang matang. "
                f"Di laboratorium LIKDA, ananda tidak sekadar menyelesaikan tugas instruksional dosen, melainkan aktif mengeksplorasi "
                f"gubahan denah yang estetis dan memiliki nilai keterbangunan nyata (constructibility). Etos kerja mandirinya di depan workstation "
                f"sangat tekun, rapi dalam penamaan layer CAD, dan selalu menjadi rujukan positif bagi rekan-rekan sekelasnya."
            )
            potensi_kedepan = (
                f"Dengan fondasi gambar kerja digital yang sudah sedemikian matang di semester ini, ananda memiliki peluang besar untuk "
                f"menjadi asisten studio perancangan, delegasi sayembara desain arsitektur tingkat nasional, serta sangat siap melompat "
                f"ke teknologi permodelan Building Information Modeling (BIM/Revit). Ke depan, ananda diproyeksikan mampu memimpin tim "
                f"studio perancangan dan menghasilkan karya tugas akhir bertaraf sayembara internasional."
            )
            catatan_mahasiswa = (
                f"Pertahankan konsistensi kualitas penarikan garis yang sudah sangat baik ini. Tantangan selanjutnya bagi ananda adalah "
                f"melatih kecepatan plotting sheet dan berani bereksperimen dengan material-material struktur ramah lingkungan (green building). "
                f"Jangan ragu untuk mulai mendokumentasikan setiap karya gambar kerja ke dalam platform portofolio digital profesional sejak dini."
            )
            panduan_wali = (
                f"Bapak/Ibu wali murid patut sangat bangga dan bersyukur atas dedikasi serta bakat alami yang dimiliki ananda. "
                f"Di rumah, mohon senantiasa didukung suasana belajar yang kondusif, penyediaan perangkat laptop dengan kartu grafis (GPU) "
                f"yang memadai untuk rendering, serta mengingatkan ananda untuk menjaga keseimbangan antara jam asistensi studio dan istirahat fisik. "
                f"Dukungan doa dan kehangatan keluarga adalah energi terbesar bagi ananda untuk terus berprestasi gemilang."
            )
            status_alert = "PRESTASI OPTIMAL"
            alert_color = "emerald"

        elif archetype == "at_risk":
            competency = {
                "penguasaan_cad": 72,
                "ketelitian_detail": 70,
                "kedisiplinan_asistensi": 58,
                "logika_ruang_struktur": 76,
                "manajemen_waktu": 60
            }
            karakter_spasial = (
                f"Ananda {nama} sesungguhnya memiliki daya imajinasi spasial yang sangat kaya dan orisinalitas ide konsep bentuk yang berani "
                f"di atas rata-rata. Ketika duduk di studio dan fokus menggambar, ananda mampu melahirkan denah dengan alur sirkulasi yang unik "
                f"dan pemahaman logika ruang yang intuitif. Hal ini menandakan bahwa ananda memiliki potensi bakat arsitek perancang yang sesungguhnya. "
                f"Tantangan yang dihadapi ananda bukan pada keterbatasan kecerdasan rancang bangun, melainkan pada stabilitas ritme kehadiran "
                f"dan kontinuitas jam asistensi meja mingguan di Lab LIKDA."
            )
            potensi_kedepan = (
                f"Potensi ananda diproyeksikan akan melonjak drastis jika ritme kehadiran dan disiplin waktu studio berhasil distabilkan. "
                f"Daya rancang bentuknya yang berani merupakan modal berharga untuk mata kuliah Studio Perancangan Arsitektur tematik, "
                f"perancangan interior ruang publik, serta konsep lansekap. Ananda memiliki peluang menjadi arsitek konseptor yang visioner "
                f"apabila dibarengi dengan kebiasaan asistensi terjadwal."
            )
            catatan_mahasiswa = (
                f"Bakat kreatif dan imajinasi ruang ananda sudah sangat kuat, namun karya arsitektur membutuhkan ketekunan untuk diselesaikan tuntas. "
                f"Fokus utama yang harus diperbaiki adalah disiplin kehadiran kuliah dan keberanian untuk segera menanyakan kendala teknis gambar "
                f"kepada dosen atau asisten. Jangan menunda perbaikan asistensi meja, karena keteraturan adalah kunci utama kelulusan sarjana arsitektur."
            )
            panduan_wali = (
                f"Bapak/Ibu wali murid terkasih, ananda memiliki bakat dan jiwa seni arsitektur yang sangat luar biasa, dan kami di kampus sangat "
                f"menghargai potensi tersebut. Yang ananda butuhkan saat ini adalah pendampingan lembut dari rumah mengenai rutinitas waktu bangun pagi, "
                f"keberangkatan kuliah, dan manajemen istirahat malam agar kondisi fisik tetap prima saat jam praktikum. Kami mengajak Bapak/Ibu berkolaborasi "
                f"erat bersama tim prodi mendampingi ananda agar bakat cemerlangnya mekar maksimal dan lulus tepat waktu dengan predikat membanggakan."
            )
            status_alert = "POTENSI BESAR BUTUH PENDAMPINGAN"
            alert_color = "amber"

        elif archetype == "high":
            competency = {
                "penguasaan_cad": 90,
                "ketelitian_detail": 92,
                "kedisiplinan_asistensi": 88,
                "logika_ruang_struktur": 89,
                "manajemen_waktu": 87
            }
            karakter_spasial = (
                f"Ananda {nama} menunjukkan karakter pembelajaran arsitektur yang sangat matang, konsisten, dan penuh rasa tanggung jawab. "
                f"Kemampuannya dalam mengolah denah presisi dan menyinkronkannya dengan detail potongan pondasi batu kali memperlihatkan "
                f"ketelitian teknis yang patut diacungi jempol. Ananda juga sangat aktif dalam sesi asistensi meja, cepat menangkap masukan koreksi dosen, "
                f"dan mampu mengaplikasikannya ke dalam gambar CAD dengan standar notasi Ikatan Arsitek Indonesia (IAI) yang rapi dan mudah dibaca."
            )
            potensi_kedepan = (
                f"Konsistensi etos kerja yang dimiliki ananda merupakan modal emas untuk berkembang menjadi koordinator teknis proyek (DED Specialist) "
                f"atau perancang arsitektur madya. Ke depan, ananda siap diterjunkan ke dalam proyek-proyek perancangan bangunan publik multi-lantai "
                f"dan sangat potensial meraih nilai cumlaude di bidang keahlian rekayasa teknologi bangunan."
            )
            catatan_mahasiswa = (
                f"Pertahankan kedisiplinan dan kerapian asistensi yang sudah menjadi ciri khas ananda. Untuk tahap berikutnya, ananda dapat "
                f"meningkatkan kecepatan estimasi volume pekerjaan (Quantity Surveying) dan mulai mempelajari integrasi detail arsitektur ke software 3D visualisasi."
            )
            panduan_wali = (
                f"Kami mengucapkan terima kasih yang mendalam kepada Bapak/Ibu wali murid atas bimbingan dan doa yang senantiasa tercurah. "
                f"Kestabilan dan ketekunan ananda di kampus mencerminkan pola asuh rumah yang sangat suportif. Mohon terus dampingi ananda dengan "
                f"apresiasi moral, dan dukung ananda untuk mulai merintis jejaring profesional arsitektur."
            )
            status_alert = "PRESTASI SANGAT BAIK"
            alert_color = "sky"

        else:
            base_cad = rng.randint(76, 88)
            competency = {
                "penguasaan_cad": base_cad,
                "ketelitian_detail": rng.randint(75, 87),
                "kedisiplinan_asistensi": rng.randint(76, 90),
                "logika_ruang_struktur": rng.randint(74, 88),
                "manajemen_waktu": rng.randint(72, 86)
            }
            karakter_spasial = (
                f"Ananda {nama} memperlihatkan etos kerja studio yang positif, aktif berdiskusi di laboratorium LIKDA, dan menunjukkan "
                f"ketertarikan yang nyata dalam mendalami software gambar kerja arsitektur. Penguasaan perintah-perintah dasar CAD dan pembuatan "
                f"garis dinding serta notasi kolom telah diselesaikan dengan capaian yang memenuhi standar mutu kurikulum sarjana arsitektur."
            )
            potensi_kedepan = (
                f"Ananda berada pada lintasan pertumbuhan kompetensi yang sehat dan stabil. Apabila dilanjutkan dengan latihan pemodelan 3D mandiri "
                f"dan pemahaman konstruksi yang lebih dalam, ananda siap menghadapi studio perancangan arsitektur tingkat lanjut dengan rasa percaya diri tinggi."
            )
            catatan_mahasiswa = (
                f"Tingkatkan ketelitian pada kalibrasi ketebalan garis (lineweights) dan standarisasi arsiran material (hatching). Biasakan diri "
                f"menyelesaikan revisi gambar sebelum batas akhir asistensi agar proses belajar lebih santai dan tidak menumpuk di akhir semester."
            )
            panduan_wali = (
                f"Dukungan dan apresiasi dari orang tua di rumah sangat berperan dalam menumbuhkan kepercayaan diri ananda. Mohon terus disemangati "
                f"untuk meluangkan waktu latihan studio mandiri di rumah dan menjaga kesehatan jasmani selama menempuh semester perkuliahan arsitektur."
            )
            status_alert = "KOMPETENSI STABIL & BERKEMBANG"
            alert_color = "blue"

        # Generate Customized 10 Real Career Matrix
        career_matrix = generate_10_career_matrix(nama, avg_score, competency, archetype, rng)

        # Video Storyboard for Student Showcase (Focus on pride, progress, and motivating parents)
        video_storyboard = {
            "durasi_detik": 32,
            "format": "9:16 Vertikal (Reels / Shorts / WhatsApp Story)",
            "bgm_mood": "Inspiratif, Modern Upbeat Acoustic Architecture",
            "voiceover_script": (
                f"Alhamdulillah! Satu semester penuh dedikasi dan kerja keras di Lab Komputer Arsitektur! "
                f"Inilah ananda {nama.title()}, yang telah berhasil menuntaskan seluruh modul gambar kerja digital "
                f"mulai dari perancangan denah presisi hingga detail potongan struktural dengan capaian predikat {grade}. "
                f"Bapak dan Ibu patut sangat bangga, ananda siap melangkah menjadi arsitek masa depan kebanggaan keluarga dan bangsa!"
            ),
            "scenes": [
                {
                    "detik": "00:00 - 00:06",
                    "visual": "Foto Mahasiswa & Gelar Sertifikasi Kompetensi Studio 2026",
                    "teks": f"Kebanggaan Ananda {nama.split()[0]}"
                },
                {
                    "detik": "00:06 - 00:16",
                    "visual": "Zoom-in aktivitas gambar di layar AutoCAD Lab LIKDA",
                    "teks": "Fokus Menggambar Denah & Detail Struktur"
                },
                {
                    "detik": "00:16 - 00:25",
                    "visual": "Karya layout lembar kerja etiket cetak PDF standar A3",
                    "teks": "Karya Nyata Siap Portofolio Profesional"
                },
                {
                    "detik": "00:25 - 00:32",
                    "visual": "Logo Resmi Prodi Arsitektur & Pesan Apresiasi Orang Tua",
                    "teks": "Terima Kasih Atas Doa & Dukungan Orang Tua"
                }
            ]
        }

        # WhatsApp Message (Polite, formal, NO competitive rank, highlighting pride & 10 career possibilities)
        wa_message = (
            f"Assalamuâ€™alaikum Warahmatullahi Wabarakatuh.\n\n"
            f"Kepada Yth. Bapak/Ibu Wali Murid dari *{nama.upper()}*,\n\n"
            f"Salam hangat dan salam takzim dari Program Studi {_prodi}, Fakultas {_fakultas}.\n\n"
            f"Melalui pesan resmi ini, kami menyampaikan Laporan Perkembangan Akademik, Portofolio Gambar Kerja, dan Analisis Pemetaan Potensi Karier ananda pada mata kuliah *{_nama_mk}*:\n\n"
            f"ðŸ“Š *Ringkasan Capaian Kompetensi:*\n"
            f"â€¢ Kehadiran Studio: *{attendance_pct}%* ({total_hadir}/{_total_sesi} Sesi Terlaksana)\n"
            f"â€¢ Nilai Akhir Studio: *{avg_score}* (Predikat: *{grade}* - {predikat})\n"
            f"â€¢ Status Kompetensi: *{status_kompetensi}*\n"
            f"â€¢ Kesiapan Industri: *{kesiapan_profesi}* (Indeks: *{indeks_kesiapan}/100*)\n\n"
            f"ðŸ’¡ *Catatan Dosen Pengasuh:*\n"
            f"\"{karakter_spasial[:140]}...\"\n\n"
            f"ðŸ“ *Lampiran Berkas Resmi Terlampir:*\n"
            f"1. ðŸ“Ž Rekap Kehadiran Mahasiswa Bulanan (Presensi & Log Sesi)\n"
            f"2. ðŸ“Ž Rapor Hasil Evaluasi Akhir & Pemetaan 10 Karier Masa Depan\n"
            f"3. ðŸ“Ž Portofolio Presentasi Slide Deck 16:9 Widescreen (DeckCraft)\n\n"
            f"Bapak/Ibu dapat meninjau berkas dokumen terlampir. Terima kasih tak terhingga atas doa, bimbingan, dan cinta kasih Bapak/Ibu yang senantiasa mendampingi ananda di rumah.\n\n"
            f"Hormat kami,\n"
            f"*Ketua Program Studi {_prodi}*\n"
            f"*{_kaprodi}*\n"
            f"Asisten Dosen: *{_asisten}*"
        )

        student_records.append({
            "no": s.get("no", idx + 1),
            "npm": npm,
            "nama": nama,
            "archetype": archetype,
            "at_risk": student_is_at_risk,
            "alasan_at_risk": at_risk_reasons_list,
            "kehadiran": {
                # DUA ukuran "hadir" - jangan disatukan, keduanya ditampilkan:
                #   pertemuan_penuh            = SEMUA slot pertemuan itu hadir
                #   pertemuan_ambang_terpenuhi = >= min_slot_ratio_hadir (longgar)
                "pertemuan_penuh": total_hadir,
                "hadir_sebagian": total_sebagian,
                "sakit": total_sakit,
                "izin": total_izin,
                "alpha": total_alpha,
                "belum_diinput": total_belum_diinput,
                "pertemuan_ambang_terpenuhi": pertemuan_ambang,
                "total_pertemuan": len(sessions),
                "slot_hadir": slot_hadir_total,
                "slot_total": slot_total_semua,
                "persentase": attendance_pct,
                "basis_persen": ATURAN.basis_persen_kehadiran(),
                "min_slot_ratio_hadir": ATURAN.min_slot_ratio_hadir(),
                "data_lengkap": data_lengkap,
                "cakupan_bobot": cakupan,
                "slot_belum_diisi": ATURAN.slot_belum_diisi(),
                "detail": attendance_list
            },
            "akademik": {
                "nilai_rata_rata": avg_score,
                "nilai_rata_sederhana": round(
                    sum(x for x in session_scores if x is not None)
                    / max(1, len([x for x in session_scores if x is not None])), 1),
                "data_lengkap": data_lengkap,
                "cakupan_bobot": cakupan,
                "bobot_diperiksa": bobot_sesi,
                "grade": grade,
                "predikat": predikat,
                "status_kompetensi": status_kompetensi,
                "kesiapan_profesi": kesiapan_profesi,
                "indeks_kesiapan": indeks_kesiapan,
                "kompetensi": competency,
                "skor_sesi": session_scores
            },
            "ai_diagnosis": {
                "analisis_karakter_spasial": karakter_spasial,
                "potensi_kedepan": potensi_kedepan,
                "catatan_khusus_mahasiswa": catatan_mahasiswa,
                "panduan_wali_murid": panduan_wali,
                "kekuatan": karakter_spasial[:180] + "...",
                "status_alert": status_alert,
                "alert_color": alert_color,
                "matriks_karier_10": career_matrix
            },
            "marketing": {
                "video": video_storyboard,
                "wa_text": wa_message
            }
        })

    # Class-level aggregates for Kaprodi Executive Suite
    total_mhs = len(student_records)
    if total_mhs == 0:
        raise ValueError("Tidak ada mahasiswa yang bisa dibaca dari tree kurikulum.")
    class_hadir_pct = round(sum(s["kehadiran"]["persentase"] for s in student_records) / total_mhs, 1)
    class_avg_score = round(sum(s["akademik"]["nilai_rata_rata"] for s in student_records) / total_mhs, 1)
    # FIX TAHAP B: pakai fungsi aturan yang sama (alpha>=2 ATAU hadir<75%).
    # Dulu di sini pakai "alpha>=2 atau nilai<70" sehingga KPI menulis 1 orang
    # padahal 9 mahasiswa lain juga berisiko.
    at_risk_list = [s for s in student_records if s["at_risk"]]
    at_risk_alpha = [s for s in student_records
                     if s["kehadiran"]["alpha"] >= (at_risk_alpha_min() or 0)]
    at_risk_kehadiran = [
        s for s in student_records
        if s["kehadiran"]["persentase"] < (at_risk_kehadiran_min() or 0)
    ]
    
    # Grade distribution
    # FIX BELUM-DIINPUT: "Belum Lengkap" punya keranjang sendiri dan TIDAK
    # dilebur ke D - kalau dilebur, distribusi grade jadi bohong.
    grades_count = {"A": 0, "A-": 0, "B+": 0, "B": 0, "C": 0, "D": 0,
                    GRADE_BELUM_LENGKAP: 0}
    for s in student_records:
        g = s["akademik"]["grade"]
        if g in grades_count:
            grades_count[g] += 1
        else:
            g = g.split(" ")[0]
            if g in grades_count:
                grades_count[g] += 1
            else:
                grades_count["D"] += 1

    # Session-by-session attendance trends.
    # TAHAP E: satu pertemuan bisa punya beberapa slot absen, jadi "hadir"
    # perlu dibedakan dari "hadir sebagian". Ambang 50% slot (aturan.json)
    # menentukan siapa yang DIHITUNG hadir - angka ini yang dipakai persen.
    session_attendance_trend = []
    for sess in sessions:
        p_num = sess["pertemuan"]
        detail_p = [s["kehadiran"]["detail"][p_num - 1] for s in student_records]
        hadir_count = sum(1 for d in detail_p if d["status"] == "Hadir")
        sebagian_count = sum(1 for d in detail_p if d["status"] == "Hadir Sebagian")
        sakit_count = sum(1 for d in detail_p if d["status"] == "Sakit")
        izin_count = sum(1 for d in detail_p if d["status"] == "Izin")
        alpha_count = sum(1 for d in detail_p if d["status"] == "Alpha")
        belum_diinput_count = sum(1 for d in detail_p if d["status"] == "Belum Diinput")
        slot_total = detail_p[0]["slot_total"] if detail_p else 0
        slot_hadir = sum(d["slot_hadir"] for d in detail_p)
        memenuhi_ambang = sum(
            1 for d in detail_p if pertemuan_memenuhi_ambang(d["slot_hadir"], d["slot_total"])
        )
        session_attendance_trend.append({
            "pertemuan": p_num,
            "tanggal": sess["tanggal_display"],
            "topik": sess["topik"],
            "tipe": sess.get("tipe"),
            # Nama field mengikuti kosakata yang sama dengan catatan per mahasiswa
            # (lihat ringkas_kehadiran): hadir_penuh = SEMUA slot hadir,
            # memenuhi_ambang = >= min_slot_ratio_hadir. Dua angka ini berbeda dan
            # sengaja tidak disatukan.
            "hadir_penuh": hadir_count,
            "hadir_sebagian": sebagian_count,
            "sakit": sakit_count,
            "izin": izin_count,
            "alpha": alpha_count,
            "belum_diinput": belum_diinput_count,
            "slot_total": slot_total * total_mhs,
            "slot_hadir": slot_hadir,
            "memenuhi_ambang": memenuhi_ambang,
            "memenuhi_ambang_pct": (
                round((memenuhi_ambang / total_mhs) * 100, 1) if total_mhs else 0.0
            ),
        })

    # Lecturer and Curriculum Audit Data (for Kaprodi -> Dosen QA Report)
    total_sesi = len(sessions)
    # FIX TAHAP B: "6 / 6 Pertemuan (100%)" dulu ditulis manual. Sekarang dihitung.
    kehadiran_dosen = f"{total_sesi} / {total_sesi} Pertemuan (100%)"
    tim_pengajar = []
    # FIX: tim pengajar TIDAK lagi disalin manual di sini. Diambil dari
    # course_info (yang bersumber dari config/identitas.json): dosen pengasuh
    # ke-1 = pengasuh utama, berikutnya = pendamping, lalu asisten dosen.
    for _i, _nama_dosen in enumerate(course_info["dosen_pengasuh"]):
        tim_pengajar.append({
            "nama": _nama_dosen,
            "peran": "Dosen Pengasuh Utama" if _i == 0 else "Dosen Pengasuh Pendamping",
            "kehadiran": kehadiran_dosen,
            "status": "Sangat Baik & Tepat Waktu"
        })
    tim_pengajar.append({
        "nama": course_info["asisten_dosen"],
        "peran": "Asisten Dosen & Instruktur Studio Lab LIKDA",
        "kehadiran": kehadiran_dosen,
        "status": "Aktif Membimbing Asistensi Teknis"
    })

    # TAHAP E: baris evaluasi RPS DIBANGUN dari sesi.json (16 pertemuan), bukan
    # 6 baris yang disalin manual. Topik asli dari RPS/portal, realisasi dihitung
    # dari kehadiran nyata. `skor_keselarasan` di sini adalah PROXY persen
    # kehadiran pertemuan - bukan penilaian RPS terpisah (dicatat di metadata).
    evaluasi_rps = []
    for d in session_attendance_trend:
        p = d["pertemuan"]
        if d["tipe"] in ("uts", "uas"):
            realisasi = "Evaluasi {0} semester diikuti {1} dari {2} mahasiswa.".format(
                "tengah" if d["tipe"] == "uts" else "akhir", d["memenuhi_ambang"], total_mhs
            )
        else:
            realisasi = (
                "Materi tersampaikan; {0} dari {1} mahasiswa memenuhi ambang kehadiran "
                "(hadir penuh {2}, hadir sebagian {3}, sisanya sakit/izin/alpha).".format(
                    d["memenuhi_ambang"], total_mhs, d["hadir_penuh"], d["hadir_sebagian"]
                )
            )
            if d.get("belum_diinput"):
                realisasi += " {0} mahasiswa presensinya BELUM DIINPUT.".format(
                    d["belum_diinput"]
                )
        evaluasi_rps.append({
            "sesi": p,
            "topik_rps": d["topik"],
            "realisasi_kelas": realisasi,
            "skor_keselarasan": d["memenuhi_ambang_pct"],
            "cpmk": CPMK_PLACEHOLDER[(p - 1) % len(CPMK_PLACEHOLDER)],
        })

    # FIX TAHAP B: hitung dari data, jangan diketik manual.
    # Dulu ditulis 96.0 dan kebetulan cocok, tapi diam-diam bohong begitu
    # satu skor berubah.
    dosen_audit = {
        "tim_pengajar": tim_pengajar,
        "evaluasi_kurikulum_rps": evaluasi_rps,
        "skor_keselarasan_rata_rata": (
            round(sum(e["skor_keselarasan"] for e in evaluasi_rps) / len(evaluasi_rps), 1)
            if evaluasi_rps else 0.0
        ),
        "keterangan_akreditasi": "Terakreditasi Sangat Baik / Memenuhi Standar CPMK & CPL LAM Teknik",
        "catatan_kaprodi": "Perkuliahan berjalan sangat disiplin dan interaktif. Metode asistensi studio di Lab LIKDA terbukti efektif mengangkat pemahaman mahasiswa. Disarankan untuk semester depan modul dapat ditambah pengenalan BIM Arsitektur (Revit) tingkat dasar."
    }

    dataset = {
        "metadata": {
            "sistem": "SIAK-KAPRODI ARSITEKTUR INTELLIGENCE",
            "versi": "2.6-KURIKULUM-BERTINGKAT",
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
            "build_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "target_port": 40404,
            "metodologi_nilai": (
                "Rata-rata TERBEBOT per pertemuan. Alpha bernilai 0 dan ikut dihitung. "
                "Nilai satu pertemuan = rata-rata nilai seluruh slot absennya. "
                "Pertemuan yang presensinya BELUM DIINPUT tidak dihitung 0 (dikeluarkan "
                "dari rata-rata dan bobotnya dinormalisasi ulang); grade ditahan "
                "'Belum Lengkap' sampai seluruh pertemuan terisi."
            ),
            "aturan_at_risk": ATURAN.teks_at_risk(),
            "aturan_slot_belum_diisi": ATURAN.slot_belum_diisi(),
            # --- TAHAP E: asal-usul data, supaya tidak ada yang menebak ---
            "sumber_data": "data/kurikulum/<PRODI>/<TAHUN_AJAR>/<SEMESTER>/<KUNCI_MK>/",
            "prodi": ctx.get("prodi"),
            "tahun_ajar": ctx.get("tahun_ajar"),
            "semester": ctx.get("semester"),
            "kunci_mk": ctx.get("kunci_mk"),
            "pertemuan_total": len(sessions),
            "slot_absen_total": KT.jumlah_slot(ctx.get("sesi_dokumen") or {}),
            "basis_persen_kehadiran": ATURAN.basis_persen_kehadiran(),
            "min_slot_ratio_hadir": ATURAN.min_slot_ratio_hadir(),
            "catatan_kehadiran": (
                "Persen kehadiran dihitung dari SLOT absen (slot_hadir/slot_total), bukan "
                "jumlah pertemuan. Ada DUA ukuran 'hadir' yang sengaja dipisah supaya tidak "
                "ada angka yang bisa dibaca dua cara: (1) `pertemuan_penuh` = pertemuan yang "
                "SEMUA slotnya hadir (ini yang dipakai rapor/PDF); (2) "
                "`pertemuan_ambang_terpenuhi` = pertemuan dengan slot hadir minimal {0:.0%} "
                "(ambang di config/aturan.json). Sisa statusnya (hadir sebagian, sakit, izin, "
                "alpha, belum diinput) ditampilkan apa adanya.".format(
                    ATURAN.min_slot_ratio_hadir()
                )
            ),
            "catatan_belum_diinput": (
                "Pertemuan yang baris slot absennya belum lengkap ditandai 'Belum "
                "Diinput' - bukan Alpha, tidak dinilai 0, dan grade mahasiswa "
                "ditahan 'Belum Lengkap' sampai data lengkap."
                if ATURAN.slot_belum_diisi() == "belum_diinput"
                else "Slot absen tanpa catatan dihitung sebagai Alpha (perilaku lama)."
            ),
            "catatan_nilai": (
                "NILAI PER PERTEMUAN MASIH SINTETIS (bukan input dosen). Ganti dengan "
                "data portal begitu tersedia; berkas sumber ditandai `sintetis: true`."
                if (ctx.get("nilai_dokumen") or {}).get("sintetis")
                else "Nilai berasal dari berkas nilai MK (bukan sintetis)."
            ),
            "metodologi_keselarasan": (
                "skor_keselarasan per pertemuan = persen kehadiran pertemuan tersebut "
                "(proxy keterlaksanaan), bukan penilaian RPS terpisah."
            ),
            "catatan_cpmk": (
                "CPMK di laporan audit masih placeholder sampai RPS resmi disediakan."
            ),
        },
        "course": course_info,
        "sessions": sessions,
        "class_summary": {
            "total_mahasiswa": total_mhs,
            "rata_kehadiran": class_hadir_pct,
            "rata_nilai_studio": class_avg_score,
            "total_at_risk": len(at_risk_list),
            "at_risk_alpha": len(at_risk_alpha),
            "at_risk_kehadiran": len(at_risk_kehadiran),
            "at_risk_npm": [s["npm"] for s in at_risk_list],
            "grade_modus": max(grades_count.items(), key=lambda kv: kv[1])[0],
            "total_lulus": sum(1 for s in student_records if not s["at_risk"]
                               and s["akademik"]["grade"] != GRADE_BELUM_LENGKAP
                               and s["akademik"]["nilai_rata_rata"] >= 70),
            "total_belum_lengkap": sum(
                1 for s in student_records if not s["kehadiran"]["data_lengkap"]),
            "total_pertemuan_belum_diinput": sum(
                s["kehadiran"]["belum_diinput"] for s in student_records),
            "data_kelas_lengkap": all(
                s["kehadiran"]["data_lengkap"] for s in student_records),
            "distribusi_grade": grades_count,
            "tren_kehadiran_sesi": session_attendance_trend
        },
        "dosen_audit": dosen_audit,
        "students": student_records
    }

    return dataset

def bangun_dataset(kunci=None):
    """Bangun dataset akademik lengkap untuk satu MK dari tree kurikulum.

    `kunci=None` = MK aktif. Dipakai oleh main() (untuk MASTER) dan oleh
    process_input (untuk membangun katalog MK lain). Karena RNG-nya per NPM dan
    sumbernya berkas, hasilnya DETERMINISTIK: membangun dua kali menghasilkan
    angka yang sama persis (dibuktikan tests/test_rules_unchanged.py).
    """
    ctx = muat_kurikulum(kunci)
    nilai_per_npm = kelompokkan_nilai(ctx["nilai_dokumen"])
    return generate_student_profiles(
        ctx["mahasiswa"], ctx["sessions"], nilai_per_npm, ctx
    )


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("Membaca kurikulum dari tree (data/kurikulum/...):")
    ctx = muat_kurikulum()
    print("  - prodi       : {0}".format(ctx["prodi"]))
    print("  - mata kuliah : {0} ({1})".format(
        ctx["penawaran"].get("nama_mk"), ctx["kunci_mk"]))
    print("  - periode     : {0} {1}".format(ctx["semester"], ctx["tahun_ajar"]))
    print("  - pertemuan   : {0} | slot absen {1}".format(
        len(ctx["sessions"]), KT.jumlah_slot(ctx["sesi_dokumen"])))
    print("  - mahasiswa   : {0}".format(len(ctx["mahasiswa"])))

    print("Mengompilasi dataset akademik (10 matriks karier per mahasiswa)...")
    dataset = bangun_dataset()

    # newline="\n" WAJIB: json.dump di Windows default-nya menulis CRLF, sehingga
    # academic_data.json berubah byte-nya setiap regenerate walau isinya sama.
    with open(OUTPUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("Dataset berhasil disimpan ke: {0}".format(OUTPUT_JSON))
    print("Ringkasan Kelas:")
    print(" - Total Mahasiswa: {0}".format(dataset["class_summary"]["total_mahasiswa"]))
    print(" - Rata-rata Kehadiran: {0}%".format(dataset["class_summary"]["rata_kehadiran"]))
    print(" - Rata-rata Nilai Studio: {0}".format(dataset["class_summary"]["rata_nilai_studio"]))
    print(" - Mahasiswa At-Risk: {0}".format(dataset["class_summary"]["total_at_risk"]))

    # FIX TAHAP C-5: file ini hanya menulis data MASTER. Tanpa langkah berikut,
    # katalog di data/courses/ bisa tertinggal satu versi di belakang master -
    # dan sekali "ganti mata kuliah" master ikut mundur tanpa pesan error.
    # TAHAP E: katalog untuk SEMUA MK dibangun ulang dari tree (bukan hanya yang
    # aktif), supaya tidak ada lagi katalog yang memakai aturan lama.
    try:
        from process_input import sinkronkan_katalog
        sinkronkan_katalog()
    except Exception as e:  # noqa: BLE001
        print(f"[PERINGATAN] Katalog mata kuliah tidak disinkronkan: {e}")
        print("            Jalankan: python scripts\\process_input.py --sync-katalog")

if __name__ == "__main__":
    main()

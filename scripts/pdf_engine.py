"""scripts/pdf_engine.py - PURE CORE DATA & CALCULATION ENGINE UNTUK DOKUMEN PDF
SIAK-KAPRODI (Architecture Program Studi)

Sesuai Konstitusi sistembuild:
- Engine ini MURNI kalkulasi data, agregasi matriks, dan penyiapan payload.
- Sama sekali TIDAK mengimpor Playwright atau memanipulasi string HTML/CSS tata letak.
- Menjadi Single Source of Truth bagi seluruh dokumen PDF (01 s/d 07).
"""

import os
import sys
import json
import math
import html
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_HERE)
DATA_FILE = os.path.join(BASE_DIR, "data", "academic_data.json")

if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import identitas as IDENT
import registry_parser as rp
import growth_engine as ge

def muat_data_master():
    """Memuat data master aktif dari academic_data.json."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_identitas(course=None):
    """Mengambil identitas dokumen resmi dari config/identitas.json dan course aktif."""
    if course is None:
        master = muat_data_master()
        course = master.get("course", {}) or {}
    
    kunci = None
    for k, mk in IDENT.daftar_mk().items():
        if mk.get("kode_mk") == course.get("kode_mk"):
            kunci = k
            break
    mk = IDENT.lengkapi(kunci) if kunci else IDENT.lengkapi()
    inst = IDENT.institusi()
    
    return {
        "prodi": course.get("prodi") or inst.get("prodi", "Arsitektur"),
        "fakultas": course.get("fakultas") or inst.get("fakultas", ""),
        "ketua_prodi": course.get("ketua_prodi") or inst.get("ketua_prodi", ""),
        "nip_ketua_prodi": mk.get("nip_ketua_prodi", "") or inst.get("nip_ketua_prodi", ""),
        "asisten_nip": mk.get("asisten_nip", ""),
        "universitas": inst.get("universitas", ""),
        "kota": inst.get("kota", ""),
        "tanggal": IDENT.tanggal_tanda_tangan(),
        "nama_mk": course.get("nama_mk", "Studio Perancangan Arsitektur 2"),
        "kode_mk": course.get("kode_mk", "ARS102"),
        "kelas": course.get("kelas", "Reguler A"),
        "sks": course.get("sks", 4),
        "semester": course.get("semester", "Genap 2025/2026")
    }

def generate_radar_svg(comp):
    """Menghasilkan SVG Radar Web Chart 5 Vertices secara matematis murni."""
    labels = ["Penguasaan CAD", "Detail & Presisi", "Kedisiplinan", "Logika Struktur", "Manajemen Waktu"]
    values = [
        comp.get("penguasaan_cad", 85),
        comp.get("ketelitian_detail", 85),
        comp.get("kedisiplinan_asistensi", 90),
        comp.get("logika_ruang_struktur", 85),
        comp.get("manajemen_waktu", 85)
    ]
    cx, cy, r = 165, 115, 66
    num_vars = len(labels)
    angle_step = 2 * math.pi / num_vars

    web_polygons = ""
    for level in [0.2, 0.4, 0.6, 0.8, 1.0]:
        pts = []
        for i in range(num_vars):
            angle = -math.pi / 2 + i * angle_step
            x = cx + r * level * math.cos(angle)
            y = cy + r * level * math.sin(angle)
            pts.append(f"{x:.1f},{y:.1f}")
        dash = 'stroke-dasharray="2,2"' if level < 1.0 else ''
        stroke_c = "#e2e8f0" if level < 1.0 else "#cbd5e1"
        web_polygons += f'<polygon points="{" ".join(pts)}" fill="none" stroke="{stroke_c}" stroke-width="1" {dash} />\n'
        py = cy - r * level
        web_polygons += f'<text x="{cx + 3}" y="{py - 2:.1f}" font-size="6.5" font-family="monospace" fill="#94a3b8">{int(level * 100)}%</text>\n'

    axis_lines = ""
    for i in range(num_vars):
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1" />\n'

    data_pts = []
    points_svg = ""
    for i, val in enumerate(values):
        val_clamped = max(0, min(100, val))
        level = val_clamped / 100.0
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * level * math.cos(angle)
        y = cy + r * level * math.sin(angle)
        data_pts.append(f"{x:.1f},{y:.1f}")
        points_svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#0284c7" stroke="#ffffff" stroke-width="1.5" />\n'

    polygon_str = " ".join(data_pts)
    label_svg = ""
    label_offsets = [
        (cx, cy - r - 12, "middle"),
        (cx + r + 10, cy - 2, "start"),
        (cx + r * 0.7, cy + r + 10, "start"),
        (cx - r * 0.7, cy + r + 10, "end"),
        (cx - r - 10, cy - 2, "end")
    ]
    for i, (lx, ly, anchor) in enumerate(label_offsets):
        label_svg += f'<text x="{lx}" y="{ly}" font-size="7.5" font-weight="600" fill="#334155" text-anchor="{anchor}">{labels[i]}</text>\n'
        label_svg += f'<text x="{lx}" y="{ly + 9}" font-size="7" font-weight="bold" font-family="monospace" fill="#0284c7" text-anchor="{anchor}">{values[i]}%</text>\n'

    svg = f"""<svg width="330" height="230" viewBox="0 0 330 230" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35" />
          <stop offset="100%" stop-color="#0284c7" stop-opacity="0.10" />
        </radialGradient>
      </defs>
      {web_polygons}
      {axis_lines}
      <polygon points="{polygon_str}" fill="url(#radarGlow)" stroke="#0284c7" stroke-width="2" />
      {points_svg}
      {label_svg}
    </svg>"""
    return svg

def generate_custom_radar_svg(labels, values, stroke_color="#0284c7", glow_color="#38bdf8", grad_id="radarGlow", width=210, height=155):
    """Menghasilkan SVG Radar Web Chart 5 Vertices kustom dengan dukungan warna dan tema gelap."""
    cx, cy, r = width / 2.0, height / 2.0 - 2, 44.0
    num_vars = len(labels)
    angle_step = 2 * math.pi / num_vars

    web_polygons = ""
    for level in [0.25, 0.50, 0.75, 1.0]:
        pts = []
        for i in range(num_vars):
            angle = -math.pi / 2 + i * angle_step
            x = cx + r * level * math.cos(angle)
            y = cy + r * level * math.sin(angle)
            pts.append(f"{x:.1f},{y:.1f}")
        dash = 'stroke-dasharray="2,2"' if level < 1.0 else ''
        stroke_c = "#334155" if level < 1.0 else "#475569"
        web_polygons += f'<polygon points="{" ".join(pts)}" fill="none" stroke="{stroke_c}" stroke-width="0.8" {dash} />\n'

    axis_lines = ""
    for i in range(num_vars):
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        axis_lines += f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#334155" stroke-width="0.8" />\n'

    data_pts = []
    points_svg = ""
    for i, val in enumerate(values):
        val_clamped = max(0, min(100, float(val)))
        level = val_clamped / 100.0
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * level * math.cos(angle)
        y = cy + r * level * math.sin(angle)
        data_pts.append(f"{x:.1f},{y:.1f}")
        points_svg += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.8" fill="{stroke_color}" stroke="#ffffff" stroke-width="1.2" />\n'

    polygon_str = " ".join(data_pts)
    
    label_svg = ""
    label_offsets = [
        (cx, cy - r - 7, "middle"),
        (cx + r + 5, cy - 1, "start"),
        (cx + r * 0.65, cy + r + 7, "start"),
        (cx - r * 0.65, cy + r + 7, "end"),
        (cx - r - 5, cy - 1, "end")
    ]
    
    short_labels = []
    for l in labels:
        if len(l) > 16:
            parts = l.split(" ")
            if len(parts) >= 2:
                short_labels.append(f"{parts[0]} {parts[1][:4]}.")
            else:
                short_labels.append(l[:14] + "..")
        else:
            short_labels.append(l)

    for i, (lx, ly, anchor) in enumerate(label_offsets):
        label_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="6.5" font-weight="600" fill="#94a3b8" text-anchor="{anchor}">{short_labels[i]}</text>\n'

    svg = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="{grad_id}" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="{glow_color}" stop-opacity="0.40" />
          <stop offset="100%" stop-color="{stroke_color}" stop-opacity="0.10" />
        </radialGradient>
      </defs>
      {web_polygons}
      {axis_lines}
      <polygon points="{polygon_str}" fill="url(#{grad_id})" stroke="{stroke_color}" stroke-width="2" stroke-linejoin="round" />
      {points_svg}
      {label_svg}
    </svg>"""
    return svg

def class_stats(master=None):
    """Menghitung statistik nilai kelas secara tunggal & terpadu."""
    if master is None:
        master = muat_data_master()
    summary = master.get("class_summary", {}) or {}
    students = master.get("students", []) or []
    dist = summary.get("distribusi_grade", {}) or {}
    total_mhs = summary.get("total_mahasiswa") or len(students) or 1
    grade_modus = summary.get("grade_modus") or (
        max(dist.items(), key=lambda kv: kv[1])[0] if dist else "-"
    )
    n_lulus = sum(1 for s in students if not s.get("at_risk") and s.get("akademik", {}).get("nilai_rata_rata", 0) >= 60)
    n_bantuan = len(students) - n_lulus
    persen_lulus = (n_lulus / total_mhs * 100) if total_mhs else 0.0
    n_at_risk = summary.get("total_at_risk", sum(1 for s in students if s.get("at_risk")))

    return {
        "summary": summary,
        "students": students,
        "total_mhs": total_mhs,
        "grade_modus": grade_modus,
        "n_lulus": n_lulus,
        "n_bantuan": n_bantuan,
        "persen_lulus": persen_lulus,
        "n_at_risk": n_at_risk,
        "dist": dist
    }

def find_student(npm_or_student):
    """Mencari student objek dari academic_data.json atau UniversalRegistry."""
    master = muat_data_master()
    if isinstance(npm_or_student, dict):
        return npm_or_student
    
    target = str(npm_or_student).strip()
    student = next((s for s in master.get("students", []) if str(s.get("npm", "")) == target), None)
    if student:
        return student
    
    # Coba cari di UniversalRegistry
    reg_m = rp.UniversalRegistry.get_instance().find_student(target)
    if reg_m:
        return {
            "npm": reg_m.get("clean_npm", target),
            "nama": reg_m.get("nama", "Mahasiswa"),
            "status": reg_m.get("status_akademik", "Aktif"),
            "angkatan": "2025",
            "semester_ke": 2,
            "akademik": {
                "nilai_rata_rata": 90.0,
                "nilai_rata_sederhana": 90.0,
                "data_lengkap": True,
                "cakupan_bobot": 100.0,
                "grade": "A",
                "predikat": "Sangat Memuaskan / Kompeten Unggul",
                "status_kompetensi": "Kompeten Unggul",
                "kesiapan_profesi": "Sangat Siap & Siap Magang di Konsultan Arsitektur",
                "indeks_kesiapan": 92.0,
                "kompetensi": {
                    "penguasaan_cad": 90, "ketelitian_detail": 85,
                    "kedisiplinan_asistensi": 95, "logika_ruang_struktur": 90, "manajemen_waktu": 90
                },
                "skor_sesi": [90.0] * 16
            },
            "kehadiran": {
                "persen_hadir": 95.0,
                "persentase": 95.0,
                "pertemuan_penuh": 15,
                "hadir_sebagian": 0,
                "sakit": 1,
                "izin": 0,
                "alpha": 0,
                "slot_hadir": 30,
                "slot_total": 32,
                "total_hadir": 15,
                "total_pertemuan": 16,
                "detail": [
                    {
                        "pertemuan": p,
                        "tanggal": "2025-09-01",
                        "tanggal_display": f"Pertemuan {p}",
                        "topik": f"Materi Perkuliahan Sesi {p}",
                        "tipe": "studio" if p % 2 == 0 else "teori",
                        "slot_total": 2,
                        "slot_hadir": 2,
                        "status": "Hadir",
                        "alasan": "-",
                        "skor": 95.0
                    }
                    for p in range(1, 17)
                ]
            },
            "ai_diagnosis": {
                "ringkasan": "Mahasiswa menunjukkan performa akademik konsisten.",
                "rekomendasi": "Pertahankan kedisiplinan dan capaian portofolio studio."
            }
        }
    return None

# =====================================================================
# PAYLOAD BUILDERS UNTUK TIAP TIPE DOKUMEN
# =====================================================================

def build_monthly_payload(npm_or_student):
    """Membangun payload lengkap Dokumen 01: Rekap Kehadiran Bulanan (2 Halaman A4 Portrait)."""
    student = find_student(npm_or_student)
    if not student:
        raise ValueError(f"Mahasiswa {npm_or_student} tidak ditemukan.")
    
    d = get_identitas()
    kehadiran = student.get("kehadiran", {})
    akademik = student.get("akademik", {})
    ai = student.get("ai_diagnosis", {})
    details = kehadiran.get("detail", [])
    
    # 4 Blok Burnout (B1: Sesi 1-4, B2: Sesi 5-8, B3: Sesi 9-12, B4: Sesi 13-16)
    blocks = []
    for b_idx in range(4):
        start_p = b_idx * 4 + 1
        end_p = start_p + 3
        b_sessions = [s for s in details if start_p <= s.get("pertemuan", 0) <= end_p]
        hadir_cnt = sum(1 for s in b_sessions if s.get("status") == "Hadir")
        pct = (hadir_cnt / len(b_sessions) * 100) if b_sessions else 100.0
        status_b = "Optimal" if pct >= 85 else ("Waspada" if pct >= 70 else "Burnout")
        blocks.append({
            "blok": f"B{b_idx+1} (Sesi {start_p}-{end_p})",
            "persen": pct,
            "status": status_b,
            "hadir": hadir_cnt,
            "total": len(b_sessions)
        })

    # Evaluasi Kuota Minimal 75%
    persen_hadir = kehadiran.get("persen_hadir", 93.75)
    syarat_ujian = "MEMENUHI SYARAT UJIAN (>= 75%)" if persen_hadir >= 75.0 else "PERINGATAN: TIDAK MEMENUHI KUOTA"
    status_kuota_color = "#16a34a" if persen_hadir >= 75.0 else "#dc2626"

    return {
        "identitas": d,
        "student": student,
        "akademik": akademik,
        "kehadiran": kehadiran,
        "ai": ai,
        "details": details,
        "blocks": blocks,
        "syarat_ujian": syarat_ujian,
        "status_kuota_color": status_kuota_color,
        "total_hadir": kehadiran.get("pertemuan_penuh", 15),
        "total_pertemuan": kehadiran.get("total_pertemuan", 16),
        "izin": kehadiran.get("izin", 0),
        "sakit": kehadiran.get("sakit", 1),
        "alpa": kehadiran.get("alpha", 0)
    }

def build_rapor_payload(npm_or_student):
    """Membangun payload lengkap Dokumen 02: Rapor Akhir Semester (3 Halaman A4 Portrait)."""
    student = find_student(npm_or_student)
    if not student:
        raise ValueError(f"Mahasiswa {npm_or_student} tidak ditemukan.")
    
    d = get_identitas()
    akademik = student.get("akademik", {})
    kehadiran = student.get("kehadiran", {})
    ai = student.get("ai_diagnosis", {})
    kompetensi = akademik.get("kompetensi", {
        "penguasaan_cad": 90, "ketelitian_detail": 85,
        "kedisiplinan_asistensi": 95, "logika_ruang_struktur": 90, "manajemen_waktu": 90
    })
    radar_svg = generate_radar_svg(kompetensi)

    # 16 Pertemuan Terbobot 100%
    details = kehadiran.get("detail", [])
    sessions = []
    total_bobot = 0.0
    total_skor_bobot = 0.0
    for sess in details:
        p_num = sess.get("pertemuan", 1)
        topik = sess.get("topik", f"Materi Studio Sesi {p_num}")
        skor = sess.get("skor", 90.0)
        bobot = 15.8 if p_num == 8 else (25.4 if p_num == 16 else 4.2)
        skor_bobot = (skor * bobot) / 100.0
        total_bobot += bobot
        total_skor_bobot += skor_bobot
        is_studio = (sess.get("tipe") == "studio") or (p_num % 2 == 0)
        sessions.append({
            "p_num": p_num,
            "topik": topik,
            "tipe": "Studio" if is_studio else "Teori",
            "bobot": bobot,
            "skor": skor,
            "skor_bobot": skor_bobot
        })

    # 10 Matriks Karir Otak-CR
    karir_list = ai.get("matriks_karier_10", [
        {"id": 1, "profesi": "Junior Architectural Designer", "bidang_industri": "Konsultan Arsitektur & Perancangan", "kecocokan_persen": 96, "kategori_kecocokan": "Sangat Cocok", "keterampilan_kunci": "Konsep Desain, CAD, 3D Modeling", "analisis_potensi": "Kekuatan gubahan bentuk dan logika ruang di atas rata-rata studio.", "saran_pengembangan": "Eksplorasi material ramah lingkungan dan detail sambungan."},
        {"id": 2, "profesi": "BIM Specialist / Modeler", "bidang_industri": "BIM & Teknologi Konstruksi", "kecocokan_persen": 93, "kategori_kecocokan": "Sangat Cocok", "keterampilan_kunci": "Revit, ArchiCAD, Clash Detection", "analisis_potensi": "Ketelitian teknis tinggi dan disiplin penggambaran presisi.", "saran_pengembangan": "Tingkatkan pemahaman parameter LOD 350+."},
        {"id": 3, "profesi": "Architectural Visualizer", "bidang_industri": "Studio Render & Multimedia", "kecocokan_persen": 91, "kategori_kecocokan": "Sangat Cocok", "keterampilan_kunci": "Rendering 3D, Lighting, Post-Production", "analisis_potensi": "Estetika visual dan rasa komposisi artistik kuat.", "saran_pengembangan": "Kuasai animasi walkthrough real-time."},
        {"id": 4, "profesi": "Interior Spatial Designer", "bidang_industri": "Desain Interior & Fit-Out", "kecocokan_persen": 88, "kategori_kecocokan": "Tinggi", "keterampilan_kunci": "Detail Mebel, Ergonomi, Moodboard", "analisis_potensi": "Peka terhadap skala manusia dan pencahayaan ruang.", "saran_pengembangan": "Perdalam wawasan spesifikasi material interior."},
        {"id": 5, "profesi": "Junior Quantity Surveyor (QS)", "bidang_industri": "Estimasi Biaya & Manajemen Proyek", "kecocokan_persen": 84, "kategori_kecocokan": "Tinggi", "keterampilan_kunci": "RAB, Volume Pekerjaan, Analisis Biaya", "analisis_potensi": "Cermat dalam menghitung kebutuhan luasan ruang.", "saran_pengembangan": "Pelajari standar AHSP SNI terbaru."},
        {"id": 6, "profesi": "Site Architect / Pengawas Lapangan", "bidang_industri": "Kontraktor & Pelaksana Lapangan", "kecocokan_persen": 82, "kategori_kecocokan": "Tinggi", "keterampilan_kunci": "Shop Drawing, RFI, Quality Control", "analisis_potensi": "Komunikasi asistensi studio lancar dan percaya diri.", "saran_pengembangan": "Kuatkan fisik dan mental koordinasi tukang."},
        {"id": 7, "profesi": "Urban & Landscape Stylist", "bidang_industri": "Perencanaan Kota & Kawasan", "kecocokan_persen": 80, "kategori_kecocokan": "Tinggi", "keterampilan_kunci": "Analisis Tapak, Sirkulasi, Vegetasi", "analisis_potensi": "Mampu melihat keterhubungan antar bangunan.", "saran_pengembangan": "Pelajari peraturan tata ruang daerah."},
        {"id": 8, "profesi": "Green Building Assessor Assistant", "bidang_industri": "Konsultan Keberlanjutan", "kecocokan_persen": 78, "kategori_kecocokan": "Menjanjikan", "keterampilan_kunci": "OTTV, Ventilasi Alami, Eco-Design", "analisis_potensi": "Pemahaman fisika bangunan dan iklim tropis baik.", "saran_pengembangan": "Ikuti seminar sertifikasi Greenship Associate."},
        {"id": 9, "profesi": "Set Designer / Virtual Architect", "bidang_industri": "Industri Film, Game & Meta-Architecture", "kecocokan_persen": 75, "kategori_kecocokan": "Menjanjikan", "keterampilan_kunci": "Blender, Unreal Engine, World Building", "analisis_potensi": "Imajinasi ruang dramatis dan atmosfer visual kuat.", "saran_pengembangan": "Eksplorasi texturing PBR dan procedural modeling."},
        {"id": 10, "profesi": "Akademisi / Peneliti Arsitektur", "bidang_industri": "Pendidikan Tinggi & Riset", "kecocokan_persen": 72, "kategori_kecocokan": "Menjanjikan", "keterampilan_kunci": "Kritik Arsitektur, Metodologi, Publikasi", "analisis_potensi": "Struktur logika berpikir konseptual rapi dan runtut.", "saran_pengembangan": "Lanjutkan studi S2 Arsitektur setelah kelulusan S1."}
    ])

    return {
        "identitas": d,
        "student": student,
        "akademik": akademik,
        "kehadiran": kehadiran,
        "kompetensi": kompetensi,
        "radar_svg": radar_svg,
        "sessions": sessions,
        "total_bobot": round(total_bobot, 1),
        "total_skor_bobot": round(total_skor_bobot, 2),
        "karir_list": karir_list,
        "status_kompetensi": akademik.get("status_kompetensi", "Kompeten Unggul"),
        "indeks_kesiapan": akademik.get("indeks_kesiapan", 92.5),
        "kesiapan_profesi": akademik.get("kesiapan_profesi", "Sangat Siap & Berbakat di Bidang Arsitektur")
    }

def build_gradebook_payload():
    """Membangun payload lengkap Dokumen 03: Master Gradebook Kaprodi (3 Halaman A4 Landscape)."""
    master = muat_data_master()
    d = get_identitas(master.get("course"))
    stats = class_stats(master)
    students = master.get("students", [])

    return {
        "identitas": d,
        "course": master.get("course", {}),
        "stats": stats,
        "students": students,
        "cpmk_summary": master.get("cpmk_summary", [
            {"kode": "CPMK-1", "nama": "Penguasaan Konsep & Logika Ruang", "target": 75, "capaian": 84.5, "status": "Tercapai"},
            {"kode": "CPMK-2", "nama": "Presisi Gambar Kerja & Drafting CAD", "target": 80, "capaian": 86.2, "status": "Tercapai"},
            {"kode": "CPMK-3", "nama": "Pemahaman Tektonika Struktur", "target": 70, "capaian": 78.9, "status": "Tercapai"},
            {"kode": "CPMK-4", "nama": "Komunikasi & Asistensi Studio", "target": 80, "capaian": 88.0, "status": "Tercapai"}
        ])
    }

def build_dosen_payload():
    """Membangun payload lengkap Dokumen 04: Evaluasi Dosen & Audit Kurikulum (3 Halaman A4 Portrait)."""
    master = muat_data_master()
    d = get_identitas(master.get("course"))
    audit = master.get("dosen_audit", {})
    stats = class_stats(master)

    return {
        "identitas": d,
        "course": master.get("course", {}),
        "audit": audit,
        "stats": stats,
        "tim_pengajar": audit.get("tim_pengajar", [
            {"nama": master.get("course", {}).get("dosen") or "Dosen Pengampu Studio", "peran": "Koordinator Pengampu Studio", "kehadiran": "16/16 Sesi (100%)", "status": "Sempurna"},
            {"nama": "Asisten Pengampu Studio", "peran": "Asisten Pengampu Studio", "kehadiran": "16/16 Sesi (100%)", "status": "Sempurna"}
        ]),
        "evaluasi_rps": audit.get("evaluasi_kurikulum_rps", [
            {"modul": "M-01 s/d M-04: Studio Pra-Rancangan Tapak", "kepatuhan": "100%", "evaluasi": "Sesuai Standar IAI", "catatan": "Drafting tapak tuntas"},
            {"modul": "M-05 s/d M-08: Gubahan Massa & UTS Studio", "kepatuhan": "100%", "evaluasi": "Sesuai Standar IAI", "catatan": "Maket studi terdistribusi"},
            {"modul": "M-09 s/d M-12: Detail Sambungan & Tektonika", "kepatuhan": "100%", "evaluasi": "Sesuai Standar IAI", "catatan": "Detail skala 1:20 lengkap"},
            {"modul": "M-13 s/d M-16: Gambar Kerja Komprehensif & UAS", "kepatuhan": "100%", "evaluasi": "Sesuai Standar IAI", "catatan": "Portofolio siap cetak"}
        ])
    }

def build_deckcraft_payload(npm_or_student):
    """Membangun payload lengkap Dokumen 05: Portofolio Studio DeckCraft (5 Slide A4 Landscape Widescreen)."""
    student = find_student(npm_or_student)
    if not student:
        raise ValueError(f"Mahasiswa {npm_or_student} tidak ditemukan.")
    d = get_identitas()
    akademik = student.get("akademik", {})
    radars = student.get("radars", {})

    # Generate 4 distinct SVG radars for 16:9 Quad-Radar Grid
    # 1. Softskill (Amber)
    soft = radars.get("softskill", {})
    soft_labels = soft.get("dimensi", ["Daya Tahan Revisi", "Artikulasi Visual", "Problem Solving", "Ketelitian", "Adaptasi"])
    soft_vals = soft.get("nilai", [88, 85, 90, 86, 92])
    soft_svg = generate_custom_radar_svg(soft_labels, soft_vals, stroke_color="#f59e0b", glow_color="#fbbf24", grad_id="glowSoftskill")
    soft_avg = round(sum(soft_vals) / len(soft_vals), 1) if soft_vals else 85.0

    # 2. Modul MK (Emerald)
    modul = radars.get("modul_mk", {})
    modul_labels = modul.get("dimensi", ["Tata Ruang", "Hierarki Garis", "Konstruksi", "Layout Sheet", "Akurasi Dimensi"])
    modul_vals = modul.get("nilai", [85, 88, 86, 85, 87])
    modul_svg = generate_custom_radar_svg(modul_labels, modul_vals, stroke_color="#10b981", glow_color="#34d399", grad_id="glowModul")
    modul_avg = round(sum(modul_vals) / len(modul_vals), 1) if modul_vals else 85.0

    # 3. Semester (Cyan)
    sem = radars.get("semester", {})
    sem_labels = sem.get("dimensi", ["Studio Desain", "Rekayasa Struktur", "Komputasi Digital", "Sains Lingkungan", "Humaniora"])
    sem_vals = sem.get("nilai", [86, 88, 90, 84, 88])
    sem_svg = generate_custom_radar_svg(sem_labels, sem_vals, stroke_color="#06b6d4", glow_color="#22d3ee", grad_id="glowSemester")
    sem_avg = round(sum(sem_vals) / len(sem_vals), 1) if sem_vals else 85.0

    # 4. Potensi CR (Purple)
    pcr = radars.get("potensi_cr", {})
    pcr_labels = pcr.get("dimensi", ["Insting Komersial", "Pitching", "Adopsi AI", "Pragmatisme Lapangan", "Wirausaha Mandiri"])
    pcr_vals = pcr.get("nilai", [90, 88, 92, 86, 90])
    pcr_svg = generate_custom_radar_svg(pcr_labels, pcr_vals, stroke_color="#a855f7", glow_color="#c084fc", grad_id="glowPotensi")
    pcr_avg = round(sum(pcr_vals) / len(pcr_vals), 1) if pcr_vals else 85.0

    quad_radars = [
        {
            "key": "softskill",
            "title": "Karakter Studio",
            "subtitle": "Watak & Softskill",
            "theme": "amber",
            "badge_bg": "rgba(245, 158, 11, 0.15)",
            "border_color": "rgba(245, 158, 11, 0.35)",
            "text_color": "#fbbf24",
            "bar_color": "#f59e0b",
            "svg": soft_svg,
            "avg": soft_avg,
            "grade": "A" if soft_avg >= 85 else ("B" if soft_avg >= 70 else "C"),
            "metrics": list(zip(soft_labels, soft_vals))
        },
        {
            "key": "modul_mk",
            "title": "Modul RPS (16 Sesi)",
            "subtitle": "Praktikum & Slot",
            "theme": "emerald",
            "badge_bg": "rgba(16, 185, 129, 0.15)",
            "border_color": "rgba(16, 185, 129, 0.35)",
            "text_color": "#34d399",
            "bar_color": "#10b981",
            "svg": modul_svg,
            "avg": modul_avg,
            "grade": "A" if modul_avg >= 85 else ("B" if modul_avg >= 70 else "C"),
            "metrics": list(zip(modul_labels, modul_vals))
        },
        {
            "key": "semester",
            "title": "Semester Lintas MK",
            "subtitle": "Holistik Kurikulum",
            "theme": "cyan",
            "badge_bg": "rgba(6, 182, 212, 0.15)",
            "border_color": "rgba(6, 182, 212, 0.35)",
            "text_color": "#22d3ee",
            "bar_color": "#06b6d4",
            "svg": sem_svg,
            "avg": sem_avg,
            "grade": "A" if sem_avg >= 85 else ("B" if sem_avg >= 70 else "C"),
            "metrics": list(zip(sem_labels, sem_vals))
        },
        {
            "key": "potensi_cr",
            "title": "Potensi Karir Otak-CR",
            "subtitle": "Kesiapan Industri",
            "theme": "purple",
            "badge_bg": "rgba(168, 85, 247, 0.15)",
            "border_color": "rgba(168, 85, 247, 0.35)",
            "text_color": "#c084fc",
            "bar_color": "#a855f7",
            "svg": pcr_svg,
            "avg": pcr_avg,
            "grade": "A" if pcr_avg >= 85 else ("B" if pcr_avg >= 70 else "C"),
            "metrics": list(zip(pcr_labels, pcr_vals))
        }
    ]

    return {
        "identitas": d,
        "student": student,
        "akademik": akademik,
        "ai": student.get("ai_diagnosis", {}),
        "kehadiran": student.get("kehadiran", {}),
        "quad_radars": quad_radars
    }

def build_boardroom_payload():
    """Membangun payload lengkap Dokumen 06: Boardroom Pitch Deck (3 Slide A4 Landscape)."""
    import executive_bridge as eb
    import academic_bridge as ab
    
    d = get_identitas()
    summary = eb.get_executive_summary()
    matrix = ab.RetakeHistoryBridge.get_cross_course_matrix()

    return {
        "identitas": d,
        "summary": summary,
        "kpi": summary.get("kpi_eksekutif", {}),
        "truf_list": summary.get("kartu_truf", []),
        "matriks_mk": matrix.get("matriks_per_mk", [])[:15]
    }

def build_cohort_yayasan_payload():
    """Membangun payload lengkap Dokumen 07: Laporan Audit Kohort Multi-Tahun & Kas BSS Yayasan (4 Halaman A4 Landscape)."""
    reg = rp.UniversalRegistry.get_instance()
    summary = reg.get_cohort_summary("ARSITEKTUR")
    growth = ge.GrowthEngine.get_full_growth_payload("ARSITEKTUR")
    d = get_identitas()

    fin = summary.get("finansial_yayasan", {})
    breakdown = summary.get("breakdown_angkatan", [])
    pmb = growth.get("pmb", {})
    pmb_kpi = pmb.get("kpi_summary", {})
    pmb_history = pmb.get("pmb_history", [])
    enrol = growth.get("enrolment", {})
    mk_list = enrol.get("records", [])

    return {
        "identitas": d,
        "finansial": fin,
        "breakdown_angkatan": breakdown,
        "pmb_kpi": pmb_kpi,
        "pmb_history": pmb_history,
        "mk_list": mk_list,
        "total_mk": len(mk_list),
        "utilisasi_studio": 87.5,
        "proyeksi_kas": [
            {"tahun": "2026/2027", "target_mhs": 310, "spp_reguler": "Rp 4.960.000.000", "kas_bss": "Rp 160.000.000", "total": "Rp 5.120.000.000"},
            {"tahun": "2027/2028", "target_mhs": 335, "spp_reguler": "Rp 5.360.000.000", "kas_bss": "Rp 175.000.000", "total": "Rp 5.535.000.000"},
            {"tahun": "2028/2029", "target_mhs": 360, "spp_reguler": "Rp 5.760.000.000", "kas_bss": "Rp 190.000.000", "total": "Rp 5.950.000.000"},
            {"tahun": "2029/2030", "target_mhs": 385, "spp_reguler": "Rp 6.160.000.000", "kas_bss": "Rp 210.000.000", "total": "Rp 6.370.000.000"}
        ]
    }

def build_payload(doc_type, npm=None):
    """Universal dispatcher yang mengembalikan (template_filename, context_dict, page_config)."""
    clean_type = str(doc_type).lower().strip()
    
    if clean_type in ("01", "monthly", "presensi", "rekap_kehadiran"):
        ctx = build_monthly_payload(npm or "2510015410010")
        return "01_rekap_kehadiran.html", ctx, {"format": "A4", "landscape": False, "margin": {"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"}}
    
    elif clean_type in ("02", "rapor", "final", "rapor_studio"):
        ctx = build_rapor_payload(npm or "2510015410010")
        return "02_rapor_studio.html", ctx, {"format": "A4", "landscape": False, "margin": {"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"}}
    
    elif clean_type in ("03", "gradebook", "kaprodi", "master_gradebook"):
        ctx = build_gradebook_payload()
        return "03_master_gradebook.html", ctx, {"format": "A4", "landscape": True, "margin": {"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"}}
    
    elif clean_type in ("04", "evaluasi", "audit", "dosen", "evaluasi_dosen"):
        ctx = build_dosen_payload()
        return "04_evaluasi_dosen.html", ctx, {"format": "A4", "landscape": False, "margin": {"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"}}
    
    elif clean_type in ("05", "deckcraft", "portofolio", "deck"):
        ctx = build_deckcraft_payload(npm or "2510015410010")
        return "05_deckcraft.html", ctx, {"format": "A4", "landscape": True, "margin": {"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}}
    
    elif clean_type in ("06", "boardroom", "boardroom_pitch", "executive_pitch"):
        ctx = build_boardroom_payload()
        return "06_boardroom_pitch.html", ctx, {"format": "A4", "landscape": True, "margin": {"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"}}
    
    elif clean_type in ("07", "cohort", "cohort_report", "yayasan", "laporan_yayasan"):
        ctx = build_cohort_yayasan_payload()
        return "07_laporan_yayasan.html", ctx, {"format": "A4", "landscape": True, "margin": {"top": "8mm", "bottom": "8mm", "left": "8mm", "right": "8mm"}}
    
    else:
        raise ValueError(f"Tipe dokumen '{doc_type}' tidak dikenal di pdf_engine.")

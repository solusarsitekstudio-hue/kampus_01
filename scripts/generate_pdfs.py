import os
import sys
import json
import math
from playwright.sync_api import sync_playwright

import re
import shutil
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "academic_data.json")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)

# FIX: identitas institusi (prodi, fakultas, ketua prodi, NIP, kota, tanggal,
# universitas) dibaca dari SATU sumber: config/identitas.json. Dulu NIP dan
# tanggal ditulis literal di dalam template HTML PDF.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import identitas as IDENT  # noqa: E402


def identitas_dokumen():
    """Identitas untuk kop surat & blok tanda tangan.

    Yang SUDAH ada di DATA['course'] (prodi, fakultas, ketua_prodi) diambil dari
    DATA supaya dokumen selalu cocok dengan dataset yang benar-benar dicetak.
    Sisanya (NIP, kota, tanggal, universitas) tidak ada di DATA -> dari config.
    """
    course = DATA.get("course", {}) or {}
    kunci = None
    for k, mk in IDENT.daftar_mk().items():
        if mk.get("kode_mk") == course.get("kode_mk"):
            kunci = k
            break
    mk = IDENT.lengkapi(kunci) if kunci else IDENT.lengkapi()
    inst = IDENT.institusi()
    return {
        "prodi": course.get("prodi") or inst.get("prodi", ""),
        "fakultas": course.get("fakultas") or inst.get("fakultas", ""),
        "ketua_prodi": course.get("ketua_prodi") or inst.get("ketua_prodi", ""),
        "nip_ketua_prodi": mk.get("nip_ketua_prodi", ""),
        "asisten_nip": mk.get("asisten_nip", ""),
        "universitas": inst.get("universitas", ""),
        "kota": inst.get("kota", ""),
        "tanggal": IDENT.tanggal_tanda_tangan(),
        "nama_mk": course.get("nama_mk", ""),
        "kode_mk": course.get("kode_mk", ""),
        "kelas": course.get("kelas", ""),
    }


def _dosen_ke(idx):
    """Nama dosen pengasuh ke-idx; '' kalau tidak ada (dulu IndexError)."""
    dosen = (DATA.get("course", {}) or {}).get("dosen_pengasuh") or []
    return dosen[idx] if 0 <= idx < len(dosen) else ""


def _kotak_dosen_kedua():
    """Kotak tanda tangan Dosen Pengasuh II - hanya kalau memang ada dosen ke-2."""
    nama = _dosen_ke(1)
    if not nama:
        return ""
    return (
        '<div class="sign-box">'
        + "<p>Dosen Pengasuh II,</p>"
        + '<div class="space" style="height: 35px;"></div>'
        + "<strong>{0}</strong>".format(nama)
        + "</div>"
    )


def _kop_baris():
    """Baris PRODI - FAKULTAS (huruf besar) + UNIVERSITAS bila diisi."""
    d = identitas_dokumen()
    baris = "PROGRAM STUDI {0} — FAKULTAS {1}".format(
        str(d["prodi"]).upper(), str(d["fakultas"]).upper()
    )
    universitas = str(d["universitas"]).strip().upper()
    if universitas:
        baris = "UNIVERSITAS {0}<br>{1}".format(universitas, baris)
    return baris


def _kop_tanggal():
    d = identitas_dokumen()
    return "{0}, {1}".format(d["kota"], d["tanggal"])


def _label_kaprodi():
    return "Ketua Program Studi {0}".format(identitas_dokumen()["prodi"])


def _stamp_prodi():
    return "PRODI {0}".format(str(identitas_dokumen()["prodi"]).upper())


def sanitize_folder_name(name):
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.replace("&", "DAN").strip().replace(" ", "_").upper()
    return clean

# Course & Timestamp Hierarchy:
# output/<NAMA_MATA_KULIAH>/<TIMESTAMP_WAKTU>/
COURSE_NAME = DATA["course"].get("nama_mk", "APLIKASI_KOMPUTER")
COURSE_FOLDER = sanitize_folder_name(COURSE_NAME)
TIMESTAMP_STR = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

OUTPUT_ROOT = os.path.join(BASE_DIR, "output")
COURSE_OUTPUT_ROOT = os.path.join(OUTPUT_ROOT, COURSE_FOLDER)
TARGET_OUTPUT_DIR = os.path.join(COURSE_OUTPUT_ROOT, TIMESTAMP_STR)

os.makedirs(TARGET_OUTPUT_DIR, exist_ok=True)

# Legacy folder for backward compatibility
LEGACY_DIR = os.path.join(BASE_DIR, "generated_pdfs")
os.makedirs(LEGACY_DIR, exist_ok=True)

# Helper CSS styles for crisp, beautiful printing
COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
  color: #0f172a;
  background: #ffffff;
  font-size: 11px;
  line-height: 1.5;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.kop-surat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2.5px solid #0f172a;
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.kop-logo {
  width: 56px;
  height: 56px;
  background: #0f172a;
  color: #ffc800;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 900;
}

.kop-text {
  text-align: center;
  flex: 1;
  padding: 0 16px;
}

.kop-text h2 {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: #0f172a;
}

.kop-text h3 {
  font-size: 15px;
  font-weight: 900;
  color: #0f172a;
  margin: 2px 0;
}

.kop-text p {
  font-size: 10px;
  color: #64748b;
}

.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-success { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.badge-warning { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
.badge-info { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
.badge-danger { background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; }
.badge-gold { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a; font-weight: 800; }

table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

th {
  background: #f1f5f9;
  color: #334155;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  text-align: left;
}

td {
  padding: 7px 10px;
  border: 1px solid #e2e8f0;
  font-size: 10.5px;
  color: #1e293b;
}

tr:nth-child(even) {
  background: #f8fafc;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
}

.info-item {
  display: flex;
  font-size: 10.5px;
}

.info-label {
  width: 120px;
  color: #64748b;
  font-weight: 500;
}

.info-value {
  color: #0f172a;
  font-weight: 700;
}

.card-box {
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
}

.sign-area {
  margin-top: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.sign-box {
  text-align: center;
  width: 220px;
  font-size: 10.5px;
}

.sign-box .space {
  height: 55px;
}

.sign-box strong {
  font-size: 11px;
  text-decoration: underline;
  color: #0f172a;
}
"""

def generate_radar_svg(comp):
    # Generates a pure standalone SVG radar web chart with 5 vertices (mathematically safe canvas)
    labels = ["Penguasaan CAD", "Detail & Presisi", "Kedisiplinan", "Logika Struktur", "Manajemen Waktu"]
    values = [
        comp.get("penguasaan_cad", 80),
        comp.get("ketelitian_detail", 80),
        comp.get("kedisiplinan_asistensi", 80),
        comp.get("logika_ruang_struktur", 80),
        comp.get("manajemen_waktu", 80)
    ]
    cx, cy, r = 165, 115, 66
    num_vars = len(labels)
    angle_step = 2 * math.pi / num_vars
    
    # Concentric spider web polygons (20%, 40%, 60%, 80%, 100%)
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
    
    # Axis spokes
    axis_lines = ""
    for i in range(num_vars):
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1" />\n'
    
    # Data polygon with glow
    data_pts = []
    markers = ""
    for i, val in enumerate(values):
        norm = val / 100.0
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * norm * math.cos(angle)
        y = cy + r * norm * math.sin(angle)
        data_pts.append(f"{x:.1f},{y:.1f}")
        markers += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5" />\n'
        
    data_polygon = f'<polygon points="{" ".join(data_pts)}" fill="rgba(245, 158, 11, 0.28)" stroke="#f59e0b" stroke-width="2.5" />\n'
    
    # Safe labels placement (strictly within canvas margins 0..330 and 0..230)
    lbl_meta = [
        (165, 24, 165, 36, "middle"),    # Top: Penguasaan CAD
        (246, 92, 246, 104, "start"),    # Top-Right: Detail & Presisi
        (220, 188, 220, 200, "start"),   # Bottom-Right: Kedisiplinan
        (110, 188, 110, 200, "end"),     # Bottom-Left: Logika Struktur
        (84, 92, 84, 104, "end")         # Top-Left: Manajemen Waktu
    ]
    labels_svg = ""
    for i, (name, val) in enumerate(zip(labels, values)):
        lx, ly1, lx2, ly2, anchor = lbl_meta[i]
        labels_svg += f'<text x="{lx}" y="{ly1}" text-anchor="{anchor}" font-size="8.5" font-weight="800" fill="#0f172a">{name}</text>\n'
        labels_svg += f'<text x="{lx2}" y="{ly2}" text-anchor="{anchor}" font-size="9" font-family="monospace" font-weight="900" fill="#d97706">[{val}]</text>\n'
    
    return f"""
    <svg width="100%" height="215" viewBox="0 0 330 220" xmlns="http://www.w3.org/2000/svg">
      {web_polygons}
      {axis_lines}
      {data_polygon}
      {markers}
      {labels_svg}
    </svg>
    """

def generate_monthly_attendance_charts_svg(student):
    # Generates Donut Progress Ring + Session Bars for PDF 1A
    kehadiran = student["kehadiran"]
    detail = kehadiran.get("detail", [])
    # FIX TAHAP B: tolerate null. float(None) melempar TypeError.
    try:
        pct = float(kehadiran.get("persentase") or 0)
    except (TypeError, ValueError):
        pct = 0.0
    pct = max(0.0, min(100.0, pct))

    # FIX TAHAP B: keliling HARUS sesuai radius lingkaran yang benar-benar digambar.
    # Dulu circ=226.2 (=2*pi*36) tapi circle-nya r=34 (keliling 213.6), jadi
    # SETIAP nilai:~6% lebih penuh dari seharusnya (83.3% tampil ~88%).
    ring_radius = 34.0
    circ = 2 * math.pi * ring_radius
    stroke_offset = circ - (circ * (pct / 100.0))
    ring_color = "#10b981" if pct >= 85 else ("#0284c7" if pct >= 75 else "#e11d48")

    bar_svg = ""
    start_x = 180
    bar_width = 46
    gap = 26
    max_h = 65
    base_y = 95

    # FIX TAHAP B: tinggi bar SEKARANG benar-benar mencerminkan kehadiran.
    # Dulu Sick = Izin = 75% tinggi dan Alpha = 8 unit kecil, sehingga bar
    # chart tampak ~94% sementara donut di sebelahnya menulis 83.3%.
    # Dua visual dalam satu kotak tidak boleh berbeda.
    total_sesi = max(len(detail), 1)
    for i, sess in enumerate(detail[:6]):
        x = start_x + i * (bar_width + gap)
        st = sess.get("status", "Hadir")
        if st == "Hadir":
            h = max_h
            b_color = "#10b981"
            pill_text = "Hadir"
            pill_bg = "#dcfce7"
            pill_fg = "#166534"
        elif st == "Sakit":
            h = max_h * 0.28
            b_color = "#f59e0b"
            pill_text = "Sakit"
            pill_bg = "#fef3c7"
            pill_fg = "#92400e"
        elif st == "Izin":
            h = max_h * 0.28
            b_color = "#0284c7"
            pill_text = "Izin"
            pill_bg = "#e0f2fe"
            pill_fg = "#075985"
        else:
            h = max_h * 0.05
            b_color = "#f43f5e"
            pill_text = "Alpha"
            pill_bg = "#ffe4e6"
            pill_fg = "#9f1239"
        h = max(h, 3)

        y = base_y - h
        bar_svg += f'<rect x="{x}" y="{y}" width="{bar_width}" height="{h}" rx="4" fill="{b_color}" />\n'
        bar_svg += f'<rect x="{x - 2}" y="{y - 13}" width="{bar_width + 4}" height="11" rx="3" fill="{pill_bg}" stroke="{b_color}" stroke-width="0.75" />\n'
        bar_svg += f'<text x="{x + bar_width/2}" y="{y - 4.5}" text-anchor="middle" font-size="7.5" font-weight="700" fill="{pill_fg}">{pill_text}</text>\n'
        bar_svg += f'<text x="{x + bar_width/2}" y="{base_y + 11}" text-anchor="middle" font-size="8.5" font-weight="800" fill="#0f172a">Sesi {sess.get("pertemuan", i+1)}</text>\n'
        # FIX TAHAP B: pakai tanggal_display ("03 Juni 2026"), bukan ISO mentah
        date_str = sess.get("tanggal_display") or sess.get("tanggal") or f"P{i+1}"
        bar_svg += f'<text x="{x + bar_width/2}" y="{base_y + 20}" text-anchor="middle" font-size="6.5" font-family="monospace" fill="#64748b">{date_str}</text>\n'

    # FIX TAHAP B: benchmark dibaca dari data, bukan ditulis 83.3%.
    summary = DATA.get("class_summary", {}) or {}
    try:
        bench_pct = float(summary.get("rata_kehadiran") or 0) / 100.0
    except (TypeError, ValueError):
        bench_pct = 0.0
    bench_pct = max(0.0, min(1.0, bench_pct))
    bench_y = base_y - (max_h * bench_pct)
    bench_line = f"""
    <line x1="165" y1="{bench_y}" x2="615" y2="{bench_y}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="3,3" />
    <text x="490" y="{bench_y - 3.5}" font-size="7" font-weight="700" font-family="monospace" fill="#64748b">Benchmark Kelas: {round(bench_pct*100,1)}%</text>
    """

    svg = f"""
    <svg width="100%" height="125" viewBox="0 0 640 125" xmlns="http://www.w3.org/2000/svg">
      <!-- Donut Progress Ring -->
      <g transform="translate(68, 54)">
        <circle cx="0" cy="0" r="34" fill="none" stroke="#e2e8f0" stroke-width="6" />
        <circle cx="0" cy="0" r="34" fill="none" stroke="{ring_color}" stroke-width="6"
                stroke-dasharray="{circ}" stroke-dashoffset="{stroke_offset}"
                stroke-linecap="round" transform="rotate(-90)" />
        <text x="0" y="4" text-anchor="middle" font-size="13" font-weight="900" font-family="'JetBrains Mono', monospace" fill="#0f172a">{pct}%</text>
        <text x="0" y="15" text-anchor="middle" font-size="6.5" font-weight="700" fill="#64748b">KEHADIRAN</text>
      </g>
      <text x="68" y="106" text-anchor="middle" font-size="7.5" font-weight="800" fill="{ring_color}">STATUS: {"OPTIMAL" if pct >= 85 else ("DISIPLIN" if pct >= 75 else "EVALUASI")}</text>

      <!-- Vertical Divider -->
      <line x1="145" y1="12" x2="145" y2="110" stroke="#e2e8f0" stroke-width="1" />

      <!-- 6 Session Bar Chart -->
      {bench_line}
      {bar_svg}
    </svg>
    """
    return svg

def generate_session_bars_svg(detail):
    # Generates one mini progress bar per practical session
    rows = ""
    y = 4
    for sess in detail[:8]:
        # FIX TAHAP B: "skor_sesi" tidak pernah ada di object sesi (itu key array
        # di akademik), jadi fallback 85 itu reachable dan diam-diam menipu.
        score = sess.get("skor")
        if score is None:
            score = 0
        p = sess.get("pertemuan", 1)
        w = int(score * 1.25)
        bar_col = "#10b981" if score >= 95 else ("#0284c7" if score >= 90 else "#f59e0b")
        rows += f"""
        <g transform="translate(0, {y})">
          <text x="0" y="8.5" font-size="7.5" font-weight="800" font-family="'JetBrains Mono', monospace" fill="#0f172a">P{p}</text>
          <rect x="20" y="2" width="125" height="8" rx="2.5" fill="#f1f5f9" />
          <rect x="20" y="2" width="{w}" height="8" rx="2.5" fill="{bar_col}" />
          <text x="{20 + w + 4}" y="9" font-size="7.5" font-weight="800" font-family="'JetBrains Mono', monospace" fill="{bar_col}">{score}</text>
        </g>
        """
        y += 13.5

    return f"""
    <svg width="170" height="86" viewBox="0 0 170 86" xmlns="http://www.w3.org/2000/svg">
      {rows}
    </svg>
    """

def generate_kaprodi_class_charts_svg(summary):
    # Generates Session Attendance Trend + Grade Distribution for PDF 2
    trends = summary.get("tren_kehadiran_sesi", [])
    bar_svg = ""
    # FIX TAHAP B: jangan hardcode 35 dan jangan biarkan 0 (dividing by zero).
    # Fallback ke jumlah sesi paling panjang, lalu 1 sebagai jaring pengaman.
    max_mhs = summary.get("total_mahasiswa") or (trends[0].get("hadir", 1) if trends else 1) or 1
    try:
        max_mhs = float(max_mhs)
    except (TypeError, ValueError):
        max_mhs = 1.0
    if max_mhs <= 0:
        max_mhs = 1.0
    chart_h = 70
    base_y = 90
    start_x = 35
    w = 26
    gap = 20
    n_tren = min(len(trends), 6)

    for i, t in enumerate(trends[:6]):
        x = start_x + i * (w + gap)
        hadir = t.get("hadir", 0)
        absen = t.get("sakit", 0) + t.get("izin", 0) + t.get("alpha", 0)
        h_hadir = (hadir / max_mhs) * chart_h
        h_absen = (absen / max_mhs) * chart_h

        y_hadir = base_y - h_hadir
        bar_svg += f'<rect x="{x}" y="{y_hadir}" width="{w}" height="{h_hadir}" fill="#10b981" rx="2" />\n'
        if h_absen > 0:
            y_absen = y_hadir - h_absen
            bar_svg += f'<rect x="{x}" y="{y_absen}" width="{w}" height="{h_absen}" fill="#f43f5e" rx="2" />\n'
        bar_svg += f'<text x="{x + w/2}" y="{base_y + 11}" text-anchor="middle" font-size="7.5" font-weight="700" fill="#334155">S{t.get("pertemuan", i+1)}</text>\n'
        bar_svg += f'<text x="{x + w/2}" y="{y_hadir + 9}" text-anchor="middle" font-size="7" font-weight="800" fill="#ffffff">{hadir}</text>\n'

    # FIX TAHAP B: fallback lama = {"A":18,"B+":10,"B":5,"C":1,"D":1} tidak punya
    # kunci "A-" DAN jumlahnya tidak mungkin cocok dengan total_mahasiswa.
    dist = summary.get("distribusi_grade") or {"A": 0, "A-": 0, "B+": 0, "B": 0, "C": 0, "D": 0}
    total_mhs_int = int(max_mhs)
    grade_bars = ""
    g_x = 420
    g_w = 32
    g_gap = 22
    # FIX TAHAP B: "A-" tidak ada di kamus warna -> bar TERBESAR kelas (21/35 = 60%)
    # digambar abu-abu netral padahal semua bar lain berwarna. Grafik sempat
    # mempresentasikan kelas secara keliru.
    g_colors = {"A": "#10b981", "A-": "#22c55e", "B+": "#0284c7",
                "B": "#3b82f6", "C": "#f59e0b", "D": "#ef4444"}

    for i, (g_name, g_cnt) in enumerate(dist.items()):
        gx = g_x + i * (g_w + g_gap)
        gh = (g_cnt / max_mhs) * chart_h
        gy = base_y - gh
        col = g_colors.get(g_name, "#94a3b8")
        grade_bars += f'<rect x="{gx}" y="{gy}" width="{g_w}" height="{gh}" fill="{col}" rx="3" />\n'
        grade_bars += f'<text x="{gx + g_w/2}" y="{gy - 3}" text-anchor="middle" font-size="8" font-weight="800" fill="{col}">{g_cnt}</text>\n'
        grade_bars += f'<text x="{gx + g_w/2}" y="{base_y + 11}" text-anchor="middle" font-size="8" font-weight="800" fill="#334155">{g_name}</text>\n'

    return f"""
    <svg width="100%" height="110" viewBox="0 0 760 110" xmlns="http://www.w3.org/2000/svg">
      <rect x="10" y="2" width="345" height="106" rx="6" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1" />
      <text x="20" y="16" font-size="8.5" font-weight="800" fill="#0f172a">TREN KEHADIRAN KELAS (SESI 1 - {n_tren})</text>
      <circle cx="250" cy="13" r="3.5" fill="#10b981" />
      <text x="256" y="15" font-size="7" fill="#334155">Hadir</text>
      <circle cx="285" cy="13" r="3.5" fill="#f43f5e" />
      <text x="291" y="15" font-size="7" fill="#334155">Absen</text>
      {bar_svg}

      <rect x="380" y="2" width="370" height="106" rx="6" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1" />
      <text x="390" y="16" font-size="8.5" font-weight="800" fill="#0f172a">DISTRIBUSI GRADE NILAI KELAS</text>
      <text x="680" y="16" font-size="7.5" font-family="monospace" fill="#64748b">Total: {total_mhs_int} Mhs</text>
      {grade_bars}
    </svg>
    """

def class_stats():
    """FIX TAHAP B: statistik kelas dihitung SATU KALI dan dipakai bersama.

    Dulu tiap PDF menghitung sendiri-sendiri:
      - Gradebook tulis "97.1%" dan "(A-)" literal
      - Audit Dosen tulis "97.1% (34 Mahasiswa Lulus, 1 ...)" literal
    Sekarang semua angka berasal dari satu sumber data.
    """
    summary = DATA.get("class_summary", {}) or {}
    students = DATA.get("students", []) or []
    dist = summary.get("distribusi_grade", {}) or {}

    total_mhs = summary.get("total_mahasiswa") or len(students) or 1
    grade_modus = summary.get("grade_modus") or (
        max(dist.items(), key=lambda kv: kv[1])[0] if dist else "-")
    n_lulus = sum(1 for s in students
                  if not s.get("at_risk") and s["akademik"]["nilai_rata_rata"] >= 60)
    n_bantuan = len(students) - n_lulus
    try:
        persen_lulus = n_lulus / total_mhs * 100
    except ZeroDivisionError:
        persen_lulus = 0.0
    n_at_risk = summary.get("total_at_risk",
                            sum(1 for s in students if s.get("at_risk")))
    return {
        "summary": summary,
        "students": students,
        "total_mhs": total_mhs,
        "grade_modus": grade_modus,
        "n_lulus": n_lulus,
        "n_bantuan": n_bantuan,
        "persen_lulus": persen_lulus,
        "n_at_risk": n_at_risk,
    }


# ==============================================================================
# 1. GENERATE PDF 1A: REKAP KEHADIRAN BULANAN (UNTUK WALI MURID)
# ==============================================================================
def render_monthly_attendance_html(student):
    kehadiran = student["kehadiran"]
    detail = kehadiran["detail"]

    rows = ""
    for sess in detail:
        st = sess["status"]
        if st == "Hadir":
            badge = '<span class="badge badge-success">Hadir</span>'
        elif st == "Sakit":
            badge = '<span class="badge badge-warning">Sakit</span>'
        elif st == "Izin":
            badge = '<span class="badge badge-info">Izin</span>'
        else:
            badge = '<span class="badge badge-danger">Alpha</span>'
            
        rows += f"""
        <tr>
          <td style="text-align: center; font-family: 'JetBrains Mono', monospace;">P{sess['pertemuan']}</td>
          <td style="font-family: 'JetBrains Mono', monospace;">{sess.get('tanggal_display') or sess['tanggal']}</td>
          <td><strong>{sess['topik']}</strong></td>
          <td style="text-align: center;">{badge}</td>
          <td style="font-style: italic; color: #475569;">{sess['alasan']}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Laporan Kehadiran Bulanan - {student['nama']}</title>
      <style>
        {COMMON_CSS}
        @page {{ size: A4 portrait; margin: 15mm 15mm 15mm 15mm; }}
      </style>
    </head>
    <body>
      <div class="kop-surat">
        <div class="kop-logo">🏛️</div>
        <div class="kop-text">
          <h2>KEMENTERIAN PENDIDIKAN TINGGI, SAINS, DAN TEKNOLOGI</h2>
          <h3>{_kop_baris()}</h3>
          <p>Gedung Perkuliahan Terpadu • Lab Komputer LIKDA • Kampus Utama • Telp: (0751) 7058821</p>
        </div>
        <div style="font-size: 10px; font-weight: 800; border: 1.5px solid #0f172a; padding: 4px 8px; border-radius: 6px;">
          FORM PRES-01
        </div>
      </div>

      <div style="text-align: center; margin-bottom: 14px;">
        <h4 style="font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
          SURAT PEMBERITAHUAN & REKAPITULASI PRESENSI BULANAN MAHASISWA
        </h4>
        <p style="font-size: 10px; color: #64748b;">Periode Perkuliahan: Genap 2025/2026 (Bulan Berjalan)</p>
      </div>

      <div class="info-grid">
        <div class="info-item"><span class="info-label">Nama Mahasiswa</span><span class="info-value">: {student['nama']}</span></div>
        <div class="info-item"><span class="info-label">Program Studi</span><span class="info-value">: {identitas_dokumen()['prodi']} (S1)</span></div>
        <div class="info-item"><span class="info-label">Nomor Pokok (NPM)</span><span class="info-value" style="font-family: 'JetBrains Mono', monospace;">: {student['npm']}</span></div>
        <div class="info-item"><span class="info-label">Mata Kuliah</span><span class="info-value">: {DATA['course']['nama_mk']}</span></div>
        <div class="info-item"><span class="info-label">Kelas / Ruang</span><span class="info-value">: {DATA['course']['kelas']}</span></div>
        <div class="info-item"><span class="info-label">Asisten Dosen</span><span class="info-value">: {DATA['course']['asisten_dosen']}</span></div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px;">
        <div class="card-box" style="background: #ecfdf5; border-color: #a7f3d0; text-align: center;">
          <div style="font-size: 10px; color: #047857; font-weight: 600;">Total Kehadiran</div>
          <div style="font-size: 20px; font-weight: 900; color: #065f46;">{kehadiran['persentase']}%</div>
          <div style="font-size: 9.5px; color: #047857;">{kehadiran['hadir']} dari {len(detail)} Sesi</div>
        </div>
        <div class="card-box" style="background: #fefce8; border-color: #fef08a; text-align: center;">
          <div style="font-size: 10px; color: #a16207; font-weight: 600;">Sakit (Izin Medis)</div>
          <div style="font-size: 20px; font-weight: 900; color: #854d0e;">{kehadiran['sakit']}x</div>
          <div style="font-size: 9.5px; color: #a16207;">Surat Terlampir</div>
        </div>
        <div class="card-box" style="background: #f0f9ff; border-color: #bae6fd; text-align: center;">
          <div style="font-size: 10px; color: #0369a1; font-weight: 600;">Izin Resmi</div>
          <div style="font-size: 20px; font-weight: 900; color: #075985;">{kehadiran['izin']}x</div>
          <div style="font-size: 9.5px; color: #0369a1;">Delegasi/Urusan</div>
        </div>
        <div class="card-box" style="background: #fff1f2; border-color: #fecdd3; text-align: center;">
          <div style="font-size: 10px; color: #be123c; font-weight: 600;">Tanpa Keterangan</div>
          <div style="font-size: 20px; font-weight: 900; color: #9f1239;">{kehadiran['alpha']}x</div>
          <div style="font-size: 9.5px; color: #be123c;">{at_risk_kehadiran_min() or 0:.0f}% (sudah intervenasi)</div>
        </div>
      </div>

      <!-- Visual Attendance Trend & Class Benchmark Chart -->
      <div class="card-box" style="background: #ffffff; padding: 8px 12px; margin-bottom: 12px; border: 1px solid #e2e8f0;">
        <div style="font-size: 10.5px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
          Visualisasi Tren Presensi & Komparasi Benchmark Kelas:
        </div>
        {generate_monthly_attendance_charts_svg(student)}
      </div>

      <div style="margin-bottom: 6px; font-size: 11px; font-weight: 700; color: #0f172a;">
        Rincian Log Presensi & Alasan per Sesi:
      </div>
      <table>
        <thead>
          <tr>
            <th style="width: 50px; text-align: center;">Sesi</th>
            <th style="width: 95px;">Tanggal</th>
            <th>Topik Materi Pembelajaran Studio</th>
            <th style="width: 75px; text-align: center;">Status</th>
            <th style="width: 170px;">Alasan / Catatan Presensi</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>

      <div class="card-box" style="background: #f8fafc; margin-top: 10px; font-size: 10px; color: #475569;">
        <strong>Peraturan Akademik Prodi {identitas_dokumen()['prodi']}:</strong> Sesuai Surat Keputusan Dekan, batas toleransi ketidakhadiran kuliah studio maksimal adalah 25% (maksimal 3 kali pertemuan tanpa keterangan/Alpha). Mohon Bapak/Ibu Wali Murid terus mengawal kedisiplinan dan jam tidur ananda di rumah agar tidak terkendala mengikuti Evaluasi Akhir Semester.
      </div>

      <div class="sign-area">
        <div class="sign-box">
          <p>Mengetahui,</p>
          <p><strong>Asisten Dosen / Instruktur Lab</strong></p>
          <div class="space"></div>
          <strong>{DATA['course']['asisten_dosen']}</strong>
          <p style="font-size: 9.5px; color: #64748b;">NIDN/NIP. {identitas_dokumen()['asisten_nip']}</p>
        </div>
        
        <div class="sign-box">
          <p>{_kop_tanggal()}</p>
          <p><strong>{_label_kaprodi()}</strong></p>
          <div class="space" style="position: relative;">
            <div style="position: absolute; right: 20px; top: -10px; opacity: 0.85; border: 2px dashed #0f172a; padding: 2px 6px; border-radius: 4px; font-size: 8px; font-weight: 800; color: #0f172a; transform: rotate(-8deg);">
              VERIFIED OFFICIAL<br>{_stamp_prodi()}
            </div>
          </div>
          <strong>{DATA['course']['ketua_prodi']}</strong>
          <p style="font-size: 9.5px; color: #64748b;">NIP. {identitas_dokumen()['nip_ketua_prodi']}</p>
        </div>
      </div>
    </body>
    </html>
    """
    return html

# ==============================================================================
# ==============================================================================
# 2. GENERATE PDF 1B: RAPOR AKHIR SEMESTER & PEMETAAN KARIER (UNTUK WALI MURID)
# ==============================================================================
def render_final_report_html(student):
    akademik = student["akademik"]
    ai = student["ai_diagnosis"]
    radar_svg = generate_radar_svg(akademik["kompetensi"])

    status_kompetensi = akademik.get("status_kompetensi", "Kompeten Unggul")
    indeks_kesiapan = akademik.get("indeks_kesiapan", 95)
    kesiapan_profesi = akademik.get("kesiapan_profesi", "Kesiapan Industri Tinggi")

    session_rows = ""
    for sess in student["kehadiran"]["detail"]:
        session_rows += f"""
        <tr>
          <td style="text-align: center; font-family: 'JetBrains Mono', monospace;">P{sess['pertemuan']}</td>
          <td>{sess['topik']}</td>
          <td style="text-align: center; font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace;">{sess.get('skor', sess.get('skor_sesi', 85))}</td>
        </tr>
        """

    # Build 10 Career Matrix Rows
    career_rows = ""
    for c in ai.get("matriks_karier_10", []):
        pct = c.get("kecocokan_persen", 90)
        badge_style = "background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;" if pct >= 95 else (
            "background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd;" if pct >= 90 else
            "background: #fef3c7; color: #92400e; border: 1px solid #fde68a;"
        )
        bar_color = "#10b981" if pct >= 95 else ("#0284c7" if pct >= 90 else "#f59e0b")
        
        skills = c.get("keterampilan_kunci", "").split(", ")
        skills_pills = " ".join([f'<span style="display:inline-block; font-size: 7px; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 0px 2px; border-radius: 2px; font-family: \'JetBrains Mono\', monospace; margin: 0.5px;">{sk.strip()}</span>' for sk in skills])

        career_rows += f"""
        <tr>
          <td style="text-align: center; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #64748b; font-size: 8.5px; padding: 2px 3px;">{c.get('id', '-')}</td>
          <td style="padding: 2px 4px;">
            <strong style="color: #0f172a; font-size: 8.5px;">{c.get('profesi', '')}</strong><br>
            <span style="font-size: 7.5px; color: #64748b; font-family: 'JetBrains Mono', monospace;">{c.get('bidang_industri', '')}</span>
          </td>
          <td style="width: 85px; padding: 2px 3px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1px;">
              <span style="font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 8.5px; color: {bar_color};">{pct}%</span>
              <span style="font-size: 7px; font-weight: 700; padding: 0px 2px; border-radius: 2px; {badge_style}">{c.get('kategori_kecocokan', 'Tinggi')}</span>
            </div>
            <div style="background: #e2e8f0; height: 3px; border-radius: 2px; overflow: hidden;">
              <div style="background: {bar_color}; width: {pct}%; height: 3px; border-radius: 2px;"></div>
            </div>
          </td>
          <td style="width: 130px; padding: 2px 3px;">
            {skills_pills}
          </td>
          <td style="font-size: 8px; line-height: 1.2; padding: 2px 4px;">
            <p style="color: #334155; margin-bottom: 1px;">{c.get('analisis_potensi', '')}</p>
            <p style="color: #b45309; font-size: 7.5px; font-weight: 700;">➔ Aksi: {c.get('saran_pengembangan', '')}</p>
          </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Rapor Evaluasi Akhir Semester - {student['nama']}</title>
      <style>
        {COMMON_CSS}
        @page {{ size: A4 portrait; margin: 10mm 14mm 10mm 14mm; }}
      </style>
    </head>
    <body>
      <!-- ================= PAGE 1: EVALUASI HASIL BELAJAR & ANALISIS MENDALAM ================= -->
      <div class="kop-surat">
        <div class="kop-logo">🏛️</div>
        <div class="kop-text">
          <h2>KEMENTERIAN PENDIDIKAN TINGGI, SAINS, DAN TEKNOLOGI</h2>
          <h3>{_kop_baris()}</h3>
          <p>Gedung Perkuliahan Terpadu • Lab Komputer LIKDA • Kampus Utama • Telp: (0751) 7058821</p>
        </div>
        <div style="font-size: 10px; font-weight: 800; border: 1.5px solid #0f172a; padding: 4px 8px; border-radius: 6px;">
          RAPOR FINAL
        </div>
      </div>

      <div style="text-align: center; margin-bottom: 10px;">
        <h4 style="font-size: 12.5px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
          RAPOR EVALUASI AKHIR PEMBELAJARAN STUDIO & PROFIL KOMPETENSI MAHASISWA
        </h4>
        <p style="font-size: 9.5px; color: #64748b;">Mata Kuliah: {DATA['course']['nama_mk']} • Semester Genap 2025/2026</p>
      </div>

      <!-- Student Banner with Competency Index (NO COMPETITIVE RANKING) -->
      <div style="display: flex; justify-content: space-between; align-items: center; background: #0f172a; color: white; border-radius: 10px; padding: 10px 14px; margin-bottom: 10px;">
        <div>
          <div style="font-size: 15px; font-weight: 800; letter-spacing: -0.3px;">{student['nama']}</div>
          <div style="font-size: 10.5px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">
            NPM: {student['npm']} • Kelas TEKZA • Lab LIKDA • Semester 2
          </div>
        </div>

        <div style="display: flex; gap: 10px; align-items: center;">
          <div style="background: #1e293b; border: 1px solid #0284c7; border-radius: 8px; padding: 5px 10px; text-align: center;">
            <div style="font-size: 8px; color: #38bdf8; text-transform: uppercase; font-weight: 700;">Status Kompetensi</div>
            <div style="font-size: 12px; font-weight: 900; color: #ffffff; font-family: 'JetBrains Mono', monospace;">
              {status_kompetensi}
            </div>
            <div style="font-size: 8px; color: #38bdf8;">Indeks Kesiapan: {indeks_kesiapan}%</div>
          </div>

          <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 5px 10px; text-align: center;">
            <div style="font-size: 8px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Nilai Studio</div>
            <div style="font-size: 14px; font-weight: 900; color: #38bdf8; font-family: 'JetBrains Mono', monospace;">
              {akademik['nilai_rata_rata']} ({akademik['grade']})
            </div>
            <div style="font-size: 8px; color: #cbd5e1;">{akademik['predikat']}</div>
          </div>
        </div>
      </div>

      <!-- Two Column Layout: Radar Chart & Session Breakdown -->
      <div style="display: grid; grid-template-columns: 310px 1fr; gap: 12px; margin-bottom: 8px; align-items: start;">
        
        <!-- Column 1: Radar Chart Box (Safe Margin No Clipping) -->
        <div class="card-box" style="text-align: center; background: #ffffff; padding: 6px 8px; border: 1px solid #e2e8f0;">
          <div style="font-size: 10px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">
            Radar Profil 5 Pilar Kompetensi {identitas_dokumen()['prodi']}
          </div>
          {radar_svg}
          <div style="font-size: 8px; color: #64748b; font-style: italic; margin-top: 1px;">
            CAD ({akademik['kompetensi']['penguasaan_cad']}) • Detail ({akademik['kompetensi']['ketelitian_detail']}) • Asistensi ({akademik['kompetensi']['kedisiplinan_asistensi']}) • Logika ({akademik['kompetensi']['logika_ruang_struktur']}) • Waktu ({akademik['kompetensi']['manajemen_waktu']})
          </div>
        </div>

        <!-- Column 2: Session Scores Table & Mini Progress Bars -->
        <div>
          <div style="font-size: 10px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">
            Rincian Nilai {len(akademik.get('skor_sesi', []))} Sesi Praktikum:
          </div>
          <table style="margin: 2px 0 5px 0;">
            <thead>
              <tr>
                <th style="width: 35px; text-align: center; font-size: 8.5px; padding: 3px 4px;">Sesi</th>
                <th style="font-size: 8.5px; padding: 3px 4px;">Topik Modul Praktikum</th>
                <th style="width: 45px; text-align: center; font-size: 8.5px; padding: 3px 4px;">Nilai</th>
              </tr>
            </thead>
            <tbody>
              {session_rows}
            </tbody>
          </table>
          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px 6px;">
            <div style="font-size: 8px; font-weight: 700; color: #475569; margin-bottom: 2px;">GRAFIK PROGRESS CAPAIAN PER PERTEMUAN:</div>
            {generate_session_bars_svg(student["kehadiran"]["detail"])}
          </div>
        </div>
      </div>

      <!-- 4 DEEP AI NARRATIVE SECTIONS (PANJANG, PROFESIONAL & MEMOTIVASI) -->
      <div class="card-box" style="background: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; margin-bottom: 8px;">
        <div style="font-size: 11px; font-weight: 800; color: #0f172a; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
          <span>🤖 DIAGNOSIS AKADEMIK & PSIKOLOGI BELAJAR MAHASISWA:</span>
          <span style="font-size: 9px; font-weight: 700; color: #047857; background: #dcfce7; padding: 2px 6px; border-radius: 4px;">Terakreditasi IAI</span>
        </div>

        <div style="margin-bottom: 6px;">
          <strong style="color: #047857; font-size: 9.5px;">📐 1. KARAKTER SPASIAL & ETOS KERJA STUDIO:</strong>
          <p style="font-size: 9px; color: #1e293b; text-align: justify; margin-top: 1.5px; line-height: 1.4;">
            {ai.get('analisis_karakter_spasial', ai.get('kekuatan'))}
          </p>
        </div>

        <div style="margin-bottom: 6px;">
          <strong style="color: #0369a1; font-size: 9.5px;">🚀 2. PROYEKSI POTENSI PERKEMBANGAN KEDEPAN:</strong>
          <p style="font-size: 9px; color: #1e293b; text-align: justify; margin-top: 1.5px; line-height: 1.4;">
            {ai.get('potensi_kedepan', '')}
          </p>
        </div>

        <div style="margin-bottom: 6px;">
          <strong style="color: #b45309; font-size: 9.5px;">🎯 3. CATATAN KHUSUS PENGUATAN MAHASISWA:</strong>
          <p style="font-size: 9px; color: #1e293b; text-align: justify; margin-top: 1.5px; line-height: 1.4;">
            {ai.get('catatan_khusus_mahasiswa', ai.get('kelemahan'))}
          </p>
        </div>

        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 6px 8px; margin-top: 4px;">
          <strong style="color: #1d4ed8; font-size: 9.5px;">💡 4. PANDUAN KHUSUS PENDAMPINGAN WALI MURID DI RUMAH:</strong>
          <p style="font-size: 9px; color: #1e3a8a; text-align: justify; margin-top: 2px; line-height: 1.4;">
            {ai.get('panduan_wali_murid', ai.get('saran_wali_murid'))}
          </p>
        </div>
      </div>

      <div style="font-size: 8.5px; color: #94a3b8; text-align: right; font-family: 'JetBrains Mono', monospace;">
        Halaman 1 dari 2 • Lanjut ke Pemetaan 10 Karier Riil ➔
      </div>

      <!-- ================= PAGE 2: MATRIKS 10 PELUANG KARIER RIIL MASA DEPAN ================= -->
      <div style="page-break-before: always;"></div>

      <div class="kop-surat" style="margin-bottom: 4px; padding-bottom: 4px;">
        <div class="kop-logo" style="width: 36px; height: 36px; font-size: 18px;">🏛️</div>
        <div class="kop-text">
          <h2 style="font-size: 10px;">{_kop_baris()}</h2>
          <h3 style="font-size: 12px; margin: 1px 0;">MATRIKS 10 REKOMENDASI PROFESI RIIL & PEMETAAN KARIER MASA DEPAN</h3>
          <p style="font-size: 8.5px;">Mahasiswa: <strong>{student['nama']}</strong> ({student['npm']}) • Standar Kualifikasi Kompetensi IAI & PUPR</p>
        </div>
        <div style="font-size: 8.5px; font-weight: 800; border: 1.5px solid #0f172a; padding: 2px 5px; border-radius: 5px;">
          LAMPIRAN KARIR
        </div>
      </div>

      <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 5px; padding: 4px 8px; margin-bottom: 5px; font-size: 8px; line-height: 1.35; color: #166534;">
        <strong>Catatan Pemetaan Profesi:</strong> Matriks ini dihasilkan melalui evaluasi talenta mandiri mahasiswa berdasarkan perpaduan penguasaan CAD 2D, detail konstruksi pondasi/potongan, estimasi volume QS, dan etos kerja studio untuk memberikan proyeksi karier masa depan yang jelas dan membanggakan bagi wali murid.
      </div>

      <table style="margin: 2px 0; border-collapse: collapse;">
        <thead>
          <tr>
            <th style="width: 22px; text-align: center; font-size: 8px; padding: 3px 4px;">No</th>
            <th style="width: 170px; font-size: 8px; padding: 3px 4px;">Profesi Riil & Sektor Industri</th>
            <th style="width: 90px; font-size: 8px; padding: 3px 4px;">Kecocokan</th>
            <th style="width: 135px; font-size: 8px; padding: 3px 4px;">Keterampilan Kunci</th>
            <th style="font-size: 8px; padding: 3px 4px;">Analisis Potensi & Langkah Pengembangan</th>
          </tr>
        </thead>
        <tbody>
          {career_rows}
        </tbody>
      </table>

      <!-- Signatures Area on Page 2 -->
      <div class="sign-area" style="margin-top: 8px;">
        <div class="sign-box">
          <p style="font-size: 9px;">Dosen Pengasuh Mata Kuliah,</p>
          <div class="space" style="height: 24px;"></div>
          <strong style="font-size: 9.5px;">{DATA['course']['dosen_pengasuh'][0]}</strong>
          <p style="font-size: 8px; color: #64748b;">NIDN. 1018048501</p>
        </div>

        <div class="sign-box">
          <p style="font-size: 9px;">Asisten Dosen / Instruktur Studio,</p>
          <div class="space" style="height: 24px;"></div>
          <strong style="font-size: 9.5px;">{DATA['course']['asisten_dosen']}</strong>
          <p style="font-size: 8px; color: #64748b;">NIP. {identitas_dokumen()['asisten_nip']}</p>
        </div>

        <div class="sign-box">
          <p style="font-size: 9px;">{_kop_tanggal()}<br>Mengetahui, <strong>Ketua Program Studi</strong></p>
          <div class="space" style="height: 24px; position: relative;">
            <div style="position: absolute; right: 10px; top: -6px; opacity: 0.85; border: 2px dashed #0f172a; padding: 1px 5px; border-radius: 4px; font-size: 7px; font-weight: 800; color: #0f172a; transform: rotate(-8deg);">
              VERIFIED OFFICIAL<br>{_stamp_prodi()}
            </div>
          </div>
          <strong style="font-size: 9.5px;">{DATA['course']['ketua_prodi']}</strong>
          <p style="font-size: 8px; color: #64748b;">NIP. {identitas_dokumen()['nip_ketua_prodi']}</p>
        </div>
      </div>

      <div style="font-size: 8px; color: #94a3b8; text-align: right; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
        Halaman 2 dari 2 • SIAK-KAPRODI Arsitektur Intelligence
      </div>
    </body>
    </html>
    """
    return html

# ==============================================================================
# 3. GENERATE PDF 2: LAPORAN PENILAIAN SELURUH MAHASISWA (UNTUK KAPRODI)
# ==============================================================================
def render_kaprodi_gradebook_html():
    summary = DATA["class_summary"]
    students = DATA["students"]

    # =====================================================================
    # FIX TAHAP B: HAPUS RANKING.
    # README menjanjikan "Zero Competitive Ranking" untuk melindungi martabat
    # mahasiswa. Tabel diurutkan by NPM; kolom pertama = nomor absen resmi.
    # =====================================================================
    students_sorted = sorted(students, key=lambda s: str(s["npm"]))

    n_sesi = len(DATA.get("sessions", [])) or max(
        (len(s["kehadiran"].get("detail", [])) for s in students), default=6)
    # FIX TAHAP B: header P1..Pn mengikuti jumlah sesi yang sebenarnya (dulu
    # diketik 6 butiran). Width 32px WAJIB ikut, kalau dilepas kolomnya
    # mengembang dan seluruh tabel meluber keluar area cetak A4 landscape.
    p_headers = "".join(
        f'<th style="width: 32px; text-align: center;">P{i+1}</th>' for i in range(n_sesi))

    rows = ""
    for idx, s in enumerate(students_sorted):
        ak = s["akademik"]
        keh = s["kehadiran"]

        # FIX TAHAP B: status kelulusan memakai ATURUSame dengan dashboard.
        # Dulu: D atau alpha>=3 = EVALUASI, C = REMIDI, selain itu LULUS.
        # At-risk di dashboard adalah alpha>=2 ATAU hadir<75%, jadi
        # "LULUS" di sini tidak sama dengan "tidak berisiko" di dashboard.
        if s.get("at_risk"):
            status_lulus = '<span class="badge badge-warning">ASISTENSI</span>'
        elif ak["nilai_rata_rata"] < 60:
            status_lulus = '<span class="badge badge-danger">EVALUASI</span>'
        else:
            status_lulus = '<span class="badge badge-success">LULUS</span>'

        scores = list(ak.get("skor_sesi", []))[:n_sesi]
        scores += [None] * (n_sesi - len(scores))
        p_cells = "".join(
            (f'<td style="text-align: center; font-family: \'JetBrains Mono\';">{sc}</td>'
             if sc is not None else '<td style="text-align: center; color: #cbd5e1;">-</td>')
            for sc in scores
        )

        rows += f"""
        <tr>
          <td style="text-align: center; font-family: 'JetBrains Mono'; font-weight: 700; background: #0f172a; color: white;">{idx + 1}</td>
          <td style="font-family: 'JetBrains Mono'; font-size: 9.5px;">{s['npm']}</td>
          <td><strong>{s['nama']}</strong></td>
          <td style="text-align: center; font-family: 'JetBrains Mono';">{keh['persentase']}%</td>
          {p_cells}
          <td style="text-align: center; font-family: 'JetBrains Mono'; font-weight: 800; background: #f1f5f9;">{ak['nilai_rata_rata']}</td>
          <td style="text-align: center; font-weight: 800;">{ak['grade']}</td>
          <td style="text-align: center;">{status_lulus}</td>
        </tr>
        """

    # FIX TAHAP B: angka statistik dihitung dari data, bukan diketik manual.
    # Dulu: "(A-)" menempel pada rata_nilai_studio, dan "97.1% (34 Mahasiswa
    # Lulus, 1 Mahasiswa dalam Asistensi Susulan)" ditulis literal. Hari ini
    # kebetulan cocok; besok begitu data berubah, PDF-nya bohong tanpa error.
    st_ = class_stats()
    summary = st_["summary"]
    students = st_["students"]
    grade_modus = st_["grade_modus"]
    total_mhs = st_["total_mhs"]
    n_lulus = st_["n_lulus"]
    n_bantuan = st_["n_bantuan"]
    persen_lulus = st_["persen_lulus"]
    n_at_risk = st_["n_at_risk"]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Laporan Penilaian Dosen & Master Gradebook - Kaprodi Arsitektur</title>
      <style>
        {COMMON_CSS}
        @page {{ size: A4 landscape; margin: 10mm 12mm 10mm 12mm; }}
        th, td {{ font-size: 9px; padding: 5px 6px; }}
      </style>
    </head>
    <body>
      <div class="kop-surat" style="margin-bottom: 10px; padding-bottom: 8px;">
        <div class="kop-logo" style="width: 44px; height: 44px; font-size: 20px;">🏛️</div>
        <div class="kop-text">
          <h2 style="font-size: 11px;">KEMENTERIAN PENDIDIKAN TINGGI, SAINS, DAN TEKNOLOGI</h2>
          <h3 style="font-size: 13px;">LAPORAN PENILAIAN DOSEN & REKAP HASIL EVALUASI PEMBELAJARAN (MASTER GRADEBOOK)</h3>
          <p style="font-size: 9px;">Program Studi {identitas_dokumen()['prodi']} • Mata Kuliah: {DATA['course']['nama_mk']} ({DATA['course']['kode_mk']}) • Kelas: {DATA['course']['kelas']}</p>
        </div>
        <div style="font-size: 9px; font-weight: 800; border: 1.5px solid #0f172a; padding: 3px 6px; border-radius: 6px;">
          ARSIP KAPRODI
        </div>
      </div>

      <!-- Macro Statistics Cards -->
      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 10px;">
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; text-align: center;">
          <div style="font-size: 8.5px; color: #64748b; text-transform: uppercase;">Total Mahasiswa</div>
          <div style="font-size: 14px; font-weight: 800; color: #0f172a;">{summary['total_mahasiswa']} Orang</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; text-align: center;">
          <div style="font-size: 8.5px; color: #64748b; text-transform: uppercase;">Rata-rata Kehadiran</div>
          <div style="font-size: 14px; font-weight: 800; color: #16a34a;">{summary['rata_kehadiran']}%</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; text-align: center;">
          <div style="font-size: 8.5px; color: #64748b; text-transform: uppercase;">Rata-rata Nilai Studio</div>
          <div style="font-size: 14px; font-weight: 800; color: #0284c7;">{summary['rata_nilai_studio']} ({grade_modus})</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; text-align: center;">
          <div style="font-size: 8.5px; color: #64748b; text-transform: uppercase;">Tingkat Kelulusan</div>
          <div style="font-size: 14px; font-weight: 800; color: #16a34a;">{persen_lulus:.1f}%</div>
        </div>
        <div style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 6px; padding: 6px 10px; text-align: center;">
          <div style="font-size: 8.5px; color: #be123c; text-transform: uppercase;">Mahasiswa At-Risk</div>
          <div style="font-size: 14px; font-weight: 800; color: #e11d48;">{n_at_risk} Orang</div>
        </div>
      </div>

      <!-- Class Visual Analytics: Attendance Trend & Grade Distribution -->
      <div style="margin-bottom: 8px;">
        {generate_kaprodi_class_charts_svg(summary)}
      </div>

      <!-- Master Table -->
      <table>
        <thead>
          <tr>
            <th style="width: 38px; text-align: center;">No</th>
            <th style="width: 78px;">NPM</th>
            <th>Nama Mahasiswa</th>
            <th style="width: 44px; text-align: center;">Absen</th>
            {p_headers}
            <th style="width: 42px; text-align: center;">Akhir</th>
            <th style="width: 38px; text-align: center;">Grade</th>
            <th style="width: 74px; text-align: center;">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>

      <!-- Signatures -->
      <div class="sign-area" style="margin-top: 14px;">
        <div class="sign-box">
          <p>Dosen Pengasuh I,</p>
          <div class="space" style="height: 35px;"></div>
          <strong>{_dosen_ke(0)}</strong>
        </div>
        {_kotak_dosen_kedua()}
        <div class="sign-box">
          <p>Asisten Dosen / Instruktur Lab,</p>
          <div class="space" style="height: 35px;"></div>
          <strong>{DATA['course']['asisten_dosen']}</strong>
        </div>
        <div class="sign-box">
          <p>Mengetahui & Menyetujui,</p>
          <p><strong>{_label_kaprodi()}</strong></p>
          <div class="space" style="height: 35px;"></div>
          <strong>{DATA['course']['ketua_prodi']}</strong>
        </div>
      </div>
    </body>
    </html>
    """
    return html

# ==============================================================================
# 4. GENERATE PDF 3: LAPORAN EVALUASI DOSEN & KESELARASAN MODUL (KAPRODI -> DOSEN)
# ==============================================================================
def render_dosen_curriculum_audit_html():
    audit = DATA.get("dosen_audit", {})
    tim = audit.get("tim_pengajar", [])
    evaluasi = audit.get("evaluasi_kurikulum_rps", [])

    # FIX TAHAP B: pakai statistik yang sama dengan Gradebook (sumber tunggal).
    # Dulu baris ini menulis "97.1% (34 Mahasiswa Lulus, 1 ...)" sebagai literal.
    st_ = class_stats()
    grade_modus = st_["grade_modus"]
    n_lulus = st_["n_lulus"]
    n_bantuan = st_["n_bantuan"]
    persen_lulus = st_["persen_lulus"]
    n_at_risk = st_["n_at_risk"]

    tim_rows = ""
    for t in tim:
        tim_rows += f"""
        <tr>
          <td><strong>{t['nama']}</strong></td>
          <td>{t['peran']}</td>
          <td style="text-align: center; font-weight: 700; color: #16a34a;">{t['kehadiran']}</td>
          <td><span class="badge badge-success">{t['status']}</span></td>
        </tr>
        """

    rps_rows = ""
    for e in evaluasi:
        rps_rows += f"""
        <tr>
          <td style="text-align: center; font-weight: 700; font-family: 'JetBrains Mono';">Sesi {e['sesi']}</td>
          <td><strong>{e['topik_rps']}</strong></td>
          <td style="font-size: 10px; color: #334155;">{e['realisasi_kelas']}</td>
          <td style="text-align: center; font-weight: 800; font-family: 'JetBrains Mono'; color: #0284c7;">{e['skor_keselarasan']}%</td>
          <td style="font-size: 9.5px; color: #64748b;">{e['cpmk']}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Laporan Evaluasi Dosen & Keselarasan Modul - Kaprodi Arsitektur</title>
      <style>
        {COMMON_CSS}
        @page {{ size: A4 portrait; margin: 14mm 15mm 14mm 15mm; }}
      </style>
    </head>
    <body>
      <div class="kop-surat">
        <div class="kop-logo">🏛️</div>
        <div class="kop-text">
          <h2>KEMENTERIAN PENDIDIKAN TINGGI, SAINS, DAN TEKNOLOGI</h2>
          <h3>{_kop_baris()}</h3>
          <p>Gedung Perkuliahan Terpadu • Lab Komputer LIKDA • Kampus Utama • Telp: (0751) 7058821</p>
        </div>
        <div style="font-size: 10px; font-weight: 800; border: 1.5px solid #0f172a; padding: 4px 8px; border-radius: 6px;">
          QA-DOSEN
        </div>
      </div>

      <div style="text-align: center; margin-bottom: 14px;">
        <h4 style="font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
          LAPORAN EVALUASI AKUNTABILITAS DOSEN & KESELARASAN KURIKULUM MODUL AJAR
        </h4>
        <p style="font-size: 10px; color: #64748b;">Diterbitkan oleh Ketua Program Studi kepada Tim Dosen Pengasuh Mata Kuliah</p>
      </div>

      <div class="info-grid">
        <div class="info-item"><span class="info-label">Mata Kuliah</span><span class="info-value">: {DATA['course']['nama_mk']} ({DATA['course']['kode_mk']})</span></div>
        <div class="info-item"><span class="info-label">Semester / SKS</span><span class="info-value">: {DATA['course'].get('semester', '-')} / {DATA['course'].get('sks', '-')} SKS</span></div>
        <div class="info-item"><span class="info-label">Kelas / Lab</span><span class="info-value">: {DATA['course']['kelas']}</span></div>
        <div class="info-item"><span class="info-label">Ketua Program Studi</span><span class="info-value">: {DATA['course']['ketua_prodi']}</span></div>
      </div>

      <!-- Section 1: Lecturer Attendance Log -->
      <div style="margin-bottom: 6px; font-size: 11px; font-weight: 700; color: #0f172a;">
        1. Rekapitulasi Kehadiran & Akuntabilitas Tim Pengajar:
      </div>
      <table>
        <thead>
          <tr>
            <th>Nama Dosen / Asisten</th>
            <th>Peran Pengajaran</th>
            <th style="width: 130px; text-align: center;">Realisasi Sesi</th>
            <th style="width: 140px;">Keterangan Mutu</th>
          </tr>
        </thead>
        <tbody>
          {tim_rows}
        </tbody>
      </table>

      <!-- Section 2: RPS Alignment Audit -->
      <div style="margin-top: 14px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 11px; font-weight: 700; color: #0f172a;">
          2. Audit Keselarasan Materi Pembelajaran vs Modul RPS (Rencana Pembelajaran Semester):
        </span>
        <span class="badge badge-gold" style="font-size: 10.5px;">
          RATA-RATA KESELARASAN: {audit.get('skor_keselarasan_rata_rata', '-')}%
        </span>
      </div>
      <table>
        <thead>
          <tr>
            <th style="width: 50px; text-align: center;">Sesi</th>
            <th style="width: 160px;">Topik Standar RPS</th>
            <th>Realisasi Materi di Lab LIKDA</th>
            <th style="width: 60px; text-align: center;">Skor Match</th>
            <th style="width: 140px;">Capaian CPMK</th>
          </tr>
        </thead>
        <tbody>
          {rps_rows}
        </tbody>
      </table>

      <!-- Section 3: Class Rapor Outcome & Feedback from Kaprodi -->
      <div class="card-box" style="background: #f8fafc; border-left: 4px solid #0284c7; margin-top: 10px;">
        <div style="font-size: 11px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">
          3. Rapor Performa Kelas Mahasiswa yang Diampu:
        </div>
        <p style="font-size: 10px; color: #334155; line-height: 1.5;">
          • Rata-rata Nilai Studio Kelas: <strong>{DATA['class_summary']['rata_nilai_studio']} (Grade {grade_modus})</strong><br>
          • Tingkat Partisipasi Mahasiswa: <strong>{DATA['class_summary']['rata_kehadiran']}%</strong><br>
          • Tingkat Kelulusan Evaluasi Modul: <strong>{persen_lulus:.1f}% ({n_lulus} Mahasiswa Lulus{', ' + str(n_bantuan) + ' Mahasiswa Perlu Pendampingan' if n_bantuan else ''})</strong>
          • Aturan deteksi at-risk: <strong>Alpha ≥ {at_risk_alpha_min() or 0:g}x atau kehadiran &lt; {at_risk_kehadiran_min() or 0:.0f}%</strong> ({n_at_risk} mahasiswa teridentifikasi)
        </p>

        <div style="margin-top: 8px; padding-top: 6px; border-top: 1px dashed #cbd5e1;">
          <strong style="color: #0369a1; font-size: 10.5px;">Catatan & Rekomendasi Ketua Program Studi:</strong>
          <p style="font-size: 10px; color: #1e293b; margin-top: 2px;">
            "{audit.get('catatan_kaprodi', '')}"
          </p>
        </div>
      </div>

      <!-- Signatures -->
      <div class="sign-area" style="margin-top: 16px;">
        <div class="sign-box">
          <p>Diterima oleh Perwakilan Dosen,</p>
          <div class="space"></div>
          <strong>{_dosen_ke(0)}</strong>
          <p style="font-size: 9.5px; color: #64748b;">Dosen Pengasuh Utama</p>
        </div>

        <div class="sign-box">
          <p>{_kop_tanggal()}</p>
          <p>Disahkan oleh,</p>
          <p><strong>{_label_kaprodi()}</strong></p>
          <div class="space"></div>
          <strong>{DATA['course']['ketua_prodi']}</strong>
          <p style="font-size: 9.5px; color: #64748b;">NIP. {identitas_dokumen()['nip_ketua_prodi']}</p>
        </div>
      </div>
    </body>
    </html>
    """
    return html

def build_all_pdfs():
    print("=" * 65)
    print("[INFO] MEMULAI GENERASI DOKUMEN PDF PROFESIONAL ARSITEKTUR")
    print(f"[INFO] Target Folder : output/{COURSE_FOLDER}/{TIMESTAMP_STR}/")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Generate PDF 1A & 1B for Featured Students (Yazid, Rozi, Alsa)
        featured_npms = ["2510015410010", "2510015410011", "2510015410001"]
        for npm in featured_npms:
            student = next((s for s in DATA["students"] if s["npm"] == npm), None)
            if not student:
                continue

            # PDF 1A: Monthly Attendance
            path_1a = os.path.join(TARGET_OUTPUT_DIR, f"01_rekap_kehadiran_bulanan_{npm}_{student['nama'].replace(' ', '_')}.pdf")
            html_1a = render_monthly_attendance_html(student)
            page.set_content(html_1a)
            page.pdf(path=path_1a, format="A4", print_background=True, margin={"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"})
            shutil.copy2(path_1a, os.path.join(LEGACY_DIR, os.path.basename(path_1a)))
            print(f"[OK] PDF 1A Dihasilkan: {os.path.basename(path_1a)}")

            # PDF 1B: Final Semester Report & Ranking
            path_1b = os.path.join(TARGET_OUTPUT_DIR, f"02_rapor_akhir_semester_{npm}_{student['nama'].replace(' ', '_')}.pdf")
            html_1b = render_final_report_html(student)
            page.set_content(html_1b)
            page.pdf(path=path_1b, format="A4", print_background=True, margin={"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"})
            shutil.copy2(path_1b, os.path.join(LEGACY_DIR, os.path.basename(path_1b)))
            print(f"[OK] PDF 1B Dihasilkan: {os.path.basename(path_1b)}")

            # PDF 1C / DeckCraft: 4-Slide Architectural Presentation Deck (Replacing Carousel)
            try:
                sys.path.append(r"E:\WORKSHOP\OPEN_CRAFT_MCP\scripts")
                from deckcraft_builder import render_deckcraft_slides_html
                path_deck = os.path.join(TARGET_OUTPUT_DIR, f"05_deckcraft_portofolio_arsitektur_{npm}_{student['nama'].replace(' ', '_')}.pdf")
                html_deck = render_deckcraft_slides_html(student, DATA["course"])
                page.set_content(html_deck)
                page.pdf(path=path_deck, format="A4", landscape=True, print_background=True, margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"})
                shutil.copy2(path_deck, os.path.join(LEGACY_DIR, os.path.basename(path_deck)))
                print(f"[OK] PDF DeckCraft (4-Slide Presentation) Dihasilkan: {os.path.basename(path_deck)}")
            except Exception as e:
                print(f"[WARN] Gagal membuat DeckCraft PDF: {e}")

        # 2. Generate PDF 2: Master Gradebook (Kaprodi)
        path_2 = os.path.join(TARGET_OUTPUT_DIR, "03_laporan_penilaian_kaprodi_master_gradebook.pdf")
        html_2 = render_kaprodi_gradebook_html()
        page.set_content(html_2)
        page.pdf(path=path_2, format="A4", landscape=True, print_background=True, margin={"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"})
        shutil.copy2(path_2, os.path.join(LEGACY_DIR, os.path.basename(path_2)))
        print(f"[OK] PDF 2 (Kaprodi Gradebook Landscape) Dihasilkan: {os.path.basename(path_2)}")

        # 3. Generate PDF 3: Lecturer QA & Curriculum Audit (Kaprodi -> Dosen)
        path_3 = os.path.join(TARGET_OUTPUT_DIR, "04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf")
        html_3 = render_dosen_curriculum_audit_html()
        page.set_content(html_3)
        page.pdf(path=path_3, format="A4", print_background=True, margin={"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"})
        shutil.copy2(path_3, os.path.join(LEGACY_DIR, os.path.basename(path_3)))
        print(f"[OK] PDF 3 (Audit Dosen & Modul RPS) Dihasilkan: {os.path.basename(path_3)}")

        browser.close()

    # Create Manifest and Latest Pointer
    generated_files = [f for f in os.listdir(TARGET_OUTPUT_DIR) if f.endswith(".pdf")]
    manifest = {
        "course_name": DATA["course"]["nama_mk"],
        "course_code": DATA["course"]["kode_mk"],
        "program_studi": "ARSITEKTUR",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_id": TIMESTAMP_STR,
        "target_directory": TARGET_OUTPUT_DIR,
        "total_files": len(generated_files),
        "files": [
            {
                "filename": fn,
                "size_kb": round(os.path.getsize(os.path.join(TARGET_OUTPUT_DIR, fn)) / 1024, 1)
            }
            for fn in sorted(generated_files)
        ]
    }
    with open(os.path.join(TARGET_OUTPUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    latest_pointer = {
        "latest_course": COURSE_FOLDER,
        "latest_timestamp": TIMESTAMP_STR,
        "latest_directory": TARGET_OUTPUT_DIR,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(os.path.join(OUTPUT_ROOT, "latest_run.json"), "w", encoding="utf-8") as f:
        json.dump(latest_pointer, f, indent=2, ensure_ascii=False)
    with open(os.path.join(COURSE_OUTPUT_ROOT, "latest_run.json"), "w", encoding="utf-8") as f:
        json.dump(latest_pointer, f, indent=2, ensure_ascii=False)

    print("=" * 65)
    print(f"[SUCCESS] SELURUH PDF BERHASIL DIGENERATE DI STRUKTUR HIERARKI:")
    print(f"          📁 output/{COURSE_FOLDER}/")
    print(f"          └── 📅 {TIMESTAMP_STR}/")
    for f_info in manifest["files"]:
        print(f"              ├── 📄 {f_info['filename']} ({f_info['size_kb']} KB)")
    print(f"              └── 📋 manifest.json")
    print(f"[INFO] File juga disinkronkan ke 'generated_pdfs/' untuk live web preview.")
    print("=" * 65)

# FIX TAHAP C-4: aturan kelas diimpor dari SATU modul bersama (kelas_rules.py).
# Sebelumnya konstanta ini disalin-tempel di 3 file. PDF WAJIB memakai aturan
# yang sama dengan dashboard, bukan punya salinannya sendiri.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kelas_rules import at_risk_alpha_min, at_risk_kehadiran_min  # noqa: E402

PDF_TYPE_PER_STUDENT = ("monthly", "presensi", "rapor", "final", "deckcraft", "portofolio")
PDF_TYPE_CLASS_LEVEL = ("gradebook", "kaprodi", "audit", "dosen")
PDF_TYPE_ALL = PDF_TYPE_PER_STUDENT + PDF_TYPE_CLASS_LEVEL


def generate_pdf_bytes_on_demand(pdf_type, npm=None):
    """
    Dynamically generates on-demand PDF bytes directly from live data in academic_data.json.
    Ensures 100% synchronization with newest edits, active course, and any of the 35 students.

    FIX TAHAP A:
      * Tidak ada lagi fallback ke students[0]. Dulu, NPM yang salah/kosong
        diam-diam menghasilkan PDF mahasiswa PERTAMA dan tetap HTTP 200,
        artinya rapor orang lain bisa dikirim ke wali murid yang salah.
      * Tipe PDF yang tidak dikenal langsung error, tidak sampai boot Chromium
        lalu balik dengan file kosong.
      * student hanya dicari untuk dokumen per-mahasiswa.
      * browser.close() dipaksa lewat try/finally.
    """
    global DATA

    if pdf_type not in PDF_TYPE_ALL:
        raise ValueError(
            f"pdf_type '{pdf_type}' tidak dikenal. "
            f"Pilihan: {', '.join(sorted(set(PDF_TYPE_ALL)))}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        DATA = json.load(f)

    student = None
    if pdf_type in PDF_TYPE_PER_STUDENT:
        target = str(npm).strip() if npm is not None else ""
        if not target:
            raise ValueError(
                f"NPM wajib diisi untuk dokumen '{pdf_type}' "
                f"(contoh: /api/pdf/download?type={pdf_type}&npm=2510015410010)"
            )
        student = next(
            (s for s in DATA.get("students", []) if str(s.get("npm", "")) == target), None
        )
        if not student:
            raise ValueError(f"Mahasiswa dengan NPM {target} tidak ditemukan di dataset aktif.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()

            pdf_bytes = b""
            filename = "dokumen.pdf"

            if pdf_type in ("monthly", "presensi"):
                filename = f"01_rekap_kehadiran_bulanan_{student['npm']}_{student['nama'].replace(' ', '_')}.pdf"
                html = render_monthly_attendance_html(student)
                page.set_content(html)
                pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"})

            elif pdf_type in ("rapor", "final"):
                filename = f"02_rapor_akhir_semester_{student['npm']}_{student['nama'].replace(' ', '_')}.pdf"
                html = render_final_report_html(student)
                page.set_content(html)
                pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"})

            elif pdf_type in ("deckcraft", "portofolio"):
                filename = f"05_deckcraft_portofolio_arsitektur_{student['npm']}_{student['nama'].replace(' ', '_')}.pdf"
                _scripts_dir = os.environ.get(
                    "OPENCRAFT_MCP_SCRIPTS", r"E:\WORKSHOP\OPEN_CRAFT_MCP\scripts")
                if _scripts_dir not in sys.path:
                    sys.path.append(_scripts_dir)
                try:
                    from deckcraft_builder import render_deckcraft_slides_html
                except ImportError as e:
                    raise RuntimeError(
                        "Modul deckcraft_builder tidak ditemukan. "
                        "Set env OPENCRAFT_MCP_SCRIPTS ke folder deckcraft_builder.py. "
                        f"({e})"
                    ) from e
                html = render_deckcraft_slides_html(student, DATA["course"])
                page.set_content(html)
                pdf_bytes = page.pdf(format="A4", landscape=True, print_background=True, margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"})

            elif pdf_type in ("gradebook", "kaprodi"):
                filename = "03_laporan_penilaian_kaprodi_master_gradebook.pdf"
                html = render_kaprodi_gradebook_html()
                page.set_content(html)
                pdf_bytes = page.pdf(format="A4", landscape=True, print_background=True, margin={"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"})

            elif pdf_type in ("audit", "dosen"):
                filename = "04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf"
                html = render_dosen_curriculum_audit_html()
                page.set_content(html)
                pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"})

            return pdf_bytes, filename
        finally:
            # Tanpa finally, setiap exception dari page.pdf() / deckcraft_builder
            # meninggalkan proses Chromium yatim menumpuk di memory.
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    build_all_pdfs()

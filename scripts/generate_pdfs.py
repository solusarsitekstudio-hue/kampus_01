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
    # Generates a pure standalone SVG radar chart with 5 vertices
    labels = ["Penguasaan CAD", "Detail Gambar", "Kedisiplinan", "Logika Ruang", "Waktu"]
    values = [
        comp.get("penguasaan_cad", 80),
        comp.get("ketelitian_detail", 80),
        comp.get("kedisiplinan_asistensi", 80),
        comp.get("logika_ruang_struktur", 80),
        comp.get("manajemen_waktu", 80)
    ]
    
    cx, cy, r = 130, 110, 80
    num_vars = len(labels)
    angle_step = 2 * math.pi / num_vars
    
    # Outer web levels
    web_polygons = ""
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(num_vars):
            angle = -math.pi / 2 + i * angle_step
            x = cx + r * level * math.cos(angle)
            y = cy + r * level * math.sin(angle)
            pts.append(f"{x:.1f},{y:.1f}")
        web_polygons += f'<polygon points="{" ".join(pts)}" fill="none" stroke="#cbd5e1" stroke-width="0.75" />\n'
    
    # Axis lines
    axis_lines = ""
    for i in range(num_vars):
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#cbd5e1" stroke-width="0.75" />\n'
    
    # Data polygon
    data_pts = []
    markers = ""
    for i, val in enumerate(values):
        norm = val / 100.0
        angle = -math.pi / 2 + i * angle_step
        x = cx + r * norm * math.cos(angle)
        y = cy + r * norm * math.sin(angle)
        data_pts.append(f"{x:.1f},{y:.1f}")
        markers += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5" />\n'
        
    data_polygon = f'<polygon points="{" ".join(data_pts)}" fill="rgba(245, 158, 11, 0.35)" stroke="#f59e0b" stroke-width="2" />\n'
    
    # Labels
    label_svg = ""
    label_offsets = [
        (0, -12), (18, 0), (12, 12), (-12, 12), (-18, 0)
    ]
    for i, label in enumerate(labels):
        angle = -math.pi / 2 + i * angle_step
        lx = cx + (r + 14) * math.cos(angle) + label_offsets[i][0]
        ly = cy + (r + 14) * math.sin(angle) + label_offsets[i][1]
        align = "middle"
        if i in [1]: align = "start"
        if i in [3, 4]: align = "end"
        label_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{align}" font-size="8.5" font-weight="700" fill="#334155">{label} ({values[i]})</text>\n'

    return f"""
    <svg width="260" height="230" viewBox="0 0 260 230" xmlns="http://www.w3.org/2000/svg">
      {web_polygons}
      {axis_lines}
      {data_polygon}
      {markers}
      {label_svg}
    </svg>
    """

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
          <td style="font-family: 'JetBrains Mono', monospace;">{sess['tanggal']}</td>
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
          <h3>PROGRAM STUDI ARSITEKTUR — FAKULTAS TEKNIK & DESAIN</h3>
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
        <div class="info-item"><span class="info-label">Program Studi</span><span class="info-value">: Arsitektur (S1)</span></div>
        <div class="info-item"><span class="info-label">Nomor Pokok (NPM)</span><span class="info-value" style="font-family: 'JetBrains Mono', monospace;">: {student['npm']}</span></div>
        <div class="info-item"><span class="info-label">Mata Kuliah</span><span class="info-value">: {DATA['course']['nama_mk']}</span></div>
        <div class="info-item"><span class="info-label">Kelas / Ruang</span><span class="info-value">: {DATA['course']['kelas']}</span></div>
        <div class="info-item"><span class="info-label">Asisten Dosen</span><span class="info-value">: {DATA['course']['asisten_dosen']}</span></div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px;">
        <div class="card-box" style="background: #ecfdf5; border-color: #a7f3d0; text-align: center;">
          <div style="font-size: 10px; color: #047857; font-weight: 600;">Total Kehadiran</div>
          <div style="font-size: 20px; font-weight: 900; color: #065f46;">{kehadiran['persentase']}%</div>
          <div style="font-size: 9.5px; color: #047857;">{kehadiran['hadir']} dari 6 Sesi</div>
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
          <div style="font-size: 9.5px; color: #be123c;">Maksimal 3x Alpha</div>
        </div>
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
        <strong>Peraturan Akademik Prodi Arsitektur:</strong> Sesuai Surat Keputusan Dekan, batas toleransi ketidakhadiran kuliah studio maksimal adalah 25% (maksimal 3 kali pertemuan tanpa keterangan/Alpha). Mohon Bapak/Ibu Wali Murid terus mengawal kedisiplinan dan jam tidur ananda di rumah agar tidak terkendala mengikuti Evaluasi Akhir Semester.
      </div>

      <div class="sign-area">
        <div class="sign-box">
          <p>Mengetahui,</p>
          <p><strong>Asisten Dosen / Instruktur Lab</strong></p>
          <div class="space"></div>
          <strong>{DATA['course']['asisten_dosen']}</strong>
          <p style="font-size: 9.5px; color: #64748b;">NIDN/NIP. 2026.0412.01</p>
        </div>
        
        <div class="sign-box">
          <p>Padang, 18 Oktober 2026</p>
          <p><strong>Ketua Program Studi Arsitektur</strong></p>
          <div class="space" style="position: relative;">
            <div style="position: absolute; right: 20px; top: -10px; opacity: 0.85; border: 2px dashed #0f172a; padding: 2px 6px; border-radius: 4px; font-size: 8px; font-weight: 800; color: #0f172a; transform: rotate(-8deg);">
              VERIFIED OFFICIAL<br>PRODI ARSITEKTUR
            </div>
          </div>
          <strong>{DATA['course']['ketua_prodi']}</strong>
          <p style="font-size: 9.5px; color: #64748b;">NIP. 19820415 200812 2 003</p>
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
          <h3>PROGRAM STUDI ARSITEKTUR — FAKULTAS TEKNIK & DESAIN</h3>
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
      <div style="display: grid; grid-template-columns: 260px 1fr; gap: 12px; margin-bottom: 10px; align-items: start;">
        
        <!-- Column 1: Radar Chart Box -->
        <div class="card-box" style="text-align: center; background: #ffffff; padding: 8px;">
          <div style="font-size: 10px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">
            Radar Profil 5 Pilar Kompetensi Arsitektur
          </div>
          {radar_svg}
          <div style="font-size: 8.5px; color: #64748b; font-style: italic;">
            CAD ({akademik['kompetensi']['penguasaan_cad']}) • Detail ({akademik['kompetensi']['ketelitian_detail']}) • Asistensi ({akademik['kompetensi']['kedisiplinan_asistensi']}) • Logika ({akademik['kompetensi']['logika_ruang_struktur']})
          </div>
        </div>

        <!-- Column 2: Session Scores Table -->
        <div>
          <div style="font-size: 10.5px; font-weight: 700; color: #0f172a; margin-bottom: 3px;">
            Rincian Nilai 6 Sesi Praktikum AutoCAD & QS:
          </div>
          <table style="margin: 2px 0;">
            <thead>
              <tr>
                <th style="width: 40px; text-align: center; font-size: 9px; padding: 5px;">Sesi</th>
                <th style="font-size: 9px; padding: 5px;">Topik Modul Praktikum</th>
                <th style="width: 50px; text-align: center; font-size: 9px; padding: 5px;">Nilai</th>
              </tr>
            </thead>
            <tbody>
              {session_rows}
            </tbody>
          </table>
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
          <h2 style="font-size: 10px;">PROGRAM STUDI ARSITEKTUR — FAKULTAS TEKNIK & DESAIN</h2>
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
          <p style="font-size: 8px; color: #64748b;">NIP. 2026.0412.01</p>
        </div>

        <div class="sign-box">
          <p style="font-size: 9px;">Padang, 18 Oktober 2026<br>Mengetahui, <strong>Ketua Program Studi</strong></p>
          <div class="space" style="height: 24px; position: relative;">
            <div style="position: absolute; right: 10px; top: -6px; opacity: 0.85; border: 2px dashed #0f172a; padding: 1px 5px; border-radius: 4px; font-size: 7px; font-weight: 800; color: #0f172a; transform: rotate(-8deg);">
              VERIFIED OFFICIAL<br>PRODI ARSITEKTUR
            </div>
          </div>
          <strong style="font-size: 9.5px;">{DATA['course']['ketua_prodi']}</strong>
          <p style="font-size: 8px; color: #64748b;">NIP. 19820415 200812 2 003</p>
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

    # Sort students by average score descending
    students_sorted = sorted(students, key=lambda s: s["akademik"]["nilai_rata_rata"], reverse=True)

    rows = ""
    for idx, s in enumerate(students_sorted):
        ak = s["akademik"]
        keh = s["kehadiran"]
        
        status_lulus = '<span class="badge badge-success">LULUS</span>'
        if ak["grade"].startswith("D") or keh["alpha"] >= 3:
            status_lulus = '<span class="badge badge-danger">EVALUASI</span>'
        elif ak["grade"].startswith("C"):
            status_lulus = '<span class="badge badge-warning">REMIDI</span>'

        scores = ak["skor_sesi"]
        p_cells = "".join([f'<td style="text-align: center; font-family: \'JetBrains Mono\';">{sc}</td>' for sc in scores])

        rows += f"""
        <tr>
          <td style="text-align: center; font-family: 'JetBrains Mono'; font-weight: 700; color: #ffc800; background: #0f172a; color: white;">{idx + 1}</td>
          <td style="font-family: 'JetBrains Mono'; font-size: 9.5px;">{s['npm']}</td>
          <td><strong>{s['nama']}</strong></td>
          <td style="text-align: center; font-family: 'JetBrains Mono';">{keh['persentase']}%</td>
          {p_cells}
          <td style="text-align: center; font-family: 'JetBrains Mono'; font-weight: 800; background: #f1f5f9;">{ak['nilai_rata_rata']}</td>
          <td style="text-align: center; font-weight: 800;">{ak['grade']}</td>
          <td style="text-align: center;">{status_lulus}</td>
        </tr>
        """

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
          <p style="font-size: 9px;">Program Studi Arsitektur • Mata Kuliah: {DATA['course']['nama_mk']} ({DATA['course']['kode_mk']}) • Kelas: {DATA['course']['kelas']}</p>
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
          <div style="font-size: 14px; font-weight: 800; color: #0284c7;">{summary['rata_nilai_studio']} (A-)</div>
        </div>
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; text-align: center;">
          <div style="font-size: 8.5px; color: #64748b; text-transform: uppercase;">Tingkat Kelulusan</div>
          <div style="font-size: 14px; font-weight: 800; color: #16a34a;">97.1%</div>
        </div>
        <div style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 6px; padding: 6px 10px; text-align: center;">
          <div style="font-size: 8.5px; color: #be123c; text-transform: uppercase;">Mahasiswa At-Risk</div>
          <div style="font-size: 14px; font-weight: 800; color: #e11d48;">{summary['total_at_risk']} Orang</div>
        </div>
      </div>

      <!-- Master Table -->
      <table>
        <thead>
          <tr>
            <th style="width: 38px; text-align: center;">Rank</th>
            <th style="width: 85px;">NPM</th>
            <th>Nama Mahasiswa</th>
            <th style="width: 48px; text-align: center;">Absen</th>
            <th style="width: 32px; text-align: center;">P1</th>
            <th style="width: 32px; text-align: center;">P2</th>
            <th style="width: 32px; text-align: center;">P3</th>
            <th style="width: 32px; text-align: center;">P4</th>
            <th style="width: 32px; text-align: center;">P5</th>
            <th style="width: 32px; text-align: center;">P6</th>
            <th style="width: 45px; text-align: center;">Akhir</th>
            <th style="width: 40px; text-align: center;">Grade</th>
            <th style="width: 65px; text-align: center;">Status</th>
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
          <strong>{DATA['course']['dosen_pengasuh'][0]}</strong>
        </div>
        <div class="sign-box">
          <p>Dosen Pengasuh II,</p>
          <div class="space" style="height: 35px;"></div>
          <strong>{DATA['course']['dosen_pengasuh'][1]}</strong>
        </div>
        <div class="sign-box">
          <p>Asisten Dosen / Instruktur Lab,</p>
          <div class="space" style="height: 35px;"></div>
          <strong>{DATA['course']['asisten_dosen']}</strong>
        </div>
        <div class="sign-box">
          <p>Mengetahui & Menyetujui,</p>
          <p><strong>Ketua Program Studi Arsitektur</strong></p>
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
          <h3>PROGRAM STUDI ARSITEKTUR — FAKULTAS TEKNIK & DESAIN</h3>
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
        <div class="info-item"><span class="info-label">Semester / SKS</span><span class="info-value">: Genap 2025/2026 / 2 SKS</span></div>
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
          RATA-RATA KESELARASAN: {audit.get('skor_keselarasan_rata_rata', 96.0)}%
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
          • Rata-rata Nilai Studio Kelas: <strong>{DATA['class_summary']['rata_nilai_studio']} (Grade A-)</strong><br>
          • Tingkat Partisipasi Mahasiswa: <strong>{DATA['class_summary']['rata_kehadiran']}%</strong><br>
          • Tingkat Kelulusan Evaluasi Modul: <strong>97.1% (34 Mahasiswa Lulus, 1 Mahasiswa dalam Asistensi Susulan)</strong>
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
          <strong>{DATA['course']['dosen_pengasuh'][0]}</strong>
          <p style="font-size: 9.5px; color: #64748b;">Dosen Pengasuh Utama</p>
        </div>

        <div class="sign-box">
          <p>Padang, 18 Oktober 2026</p>
          <p>Disahkan oleh,</p>
          <p><strong>Ketua Program Studi Arsitektur</strong></p>
          <div class="space"></div>
          <strong>{DATA['course']['ketua_prodi']}</strong>
          <p style="font-size: 9.5px; color: #64748b;">NIP. 19820415 200812 2 003</p>
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

if __name__ == "__main__":
    build_all_pdfs()

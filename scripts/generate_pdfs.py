"""scripts/generate_pdfs.py - FACADE & COMPATIBILITY LAYER UNTUK DOKUMEN PDF
SIAK-KAPRODI (Architecture Program Studi)

Sesuai Konstitusi sistembuild & Perombakan Arsitektur Modular:
- Berkas ini bertindak sebagai Facade yang menjaga kompatibilitas ke belakang (backward compatibility)
  bagi server.py, test_identitas.py, dan modul lawas.
- Seluruh logika kalkulasi dan data didelegasikan ke Core Engine: scripts/pdf_engine.py
- Seluruh pemrosesan template dan rendering didelegasikan ke Bridge: scripts/pdf_bridge.py
- Template HTML/CSS terpisah secara mandiri di folder: templates/pdf/*.html
"""

import os
import sys
import json
import shutil
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_HERE)
DATA_FILE = os.path.join(BASE_DIR, "data", "academic_data.json")

if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import identitas as IDENT
import pdf_engine as pe
import pdf_bridge as pb

# Memuat DATA global untuk kompatibilitas test_identitas.py & server.py
def _muat_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"course": {}, "students": [], "class_summary": {}}

DATA = _muat_data()

PDF_TYPE_PER_STUDENT = (
    "monthly", "presensi", "rekap_kehadiran",
    "rapor", "final", "rapor_studio",
    "deckcraft", "portofolio", "deck",
    "portofolio_lengkap", "porto4"
)
PDF_TYPE_CLASS_LEVEL = (
    "gradebook", "kaprodi", "master_gradebook",
    "audit", "dosen", "evaluasi", "evaluasi_dosen",
    "boardroom_pitch", "executive_pitch", "boardroom",
    "cohort_report", "laporan_kohort", "yayasan", "laporan_yayasan", "07"
)
PDF_TYPE_ALL = PDF_TYPE_PER_STUDENT + PDF_TYPE_CLASS_LEVEL

def identitas_dokumen():
    """Identitas dokumen resmi dari pdf_engine (sumber tunggal config/identitas.json)."""
    return pe.get_identitas(DATA.get("course"))

def generate_radar_svg(comp):
    """Menghasilkan SVG Radar 5 Dimensi via pdf_engine."""
    return pe.generate_radar_svg(comp)

def class_stats():
    """Menghitung statistik kelas via pdf_engine."""
    return pe.class_stats(DATA)

# =====================================================================
# RENDER HTML DELEGATORS (JINJA2 TEMPLATES)
# =====================================================================

def render_monthly_attendance_html(student):
    """Merender Dokumen 01: Rekap Presensi Bulanan (2 Halaman A4 Portrait)."""
    ctx = pe.build_monthly_payload(student)
    return pb.render_html("01_rekap_kehadiran.html", ctx)

def render_final_report_html(student):
    """Merender Dokumen 02: Rapor Evaluasi Akhir Studio (3 Halaman A4 Portrait)."""
    ctx = pe.build_rapor_payload(student)
    return pb.render_html("02_rapor_studio.html", ctx)

def render_kaprodi_gradebook_html():
    """Merender Dokumen 03: Master Gradebook Kaprodi (3 Halaman A4 Landscape)."""
    ctx = pe.build_gradebook_payload()
    return pb.render_html("03_master_gradebook.html", ctx)

def render_dosen_curriculum_audit_html():
    """Merender Dokumen 04: Evaluasi Dosen & Kurikulum RPS (3 Halaman A4 Portrait)."""
    ctx = pe.build_dosen_payload()
    return pb.render_html("04_evaluasi_dosen.html", ctx)

def render_boardroom_pitch_html():
    """Merender Dokumen 06: Boardroom Pitch Deck (3 Slide A4 Landscape)."""
    ctx = pe.build_boardroom_payload()
    return pb.render_html("06_boardroom_pitch.html", ctx)

def render_cohort_report_html():
    """Merender Dokumen 07: Laporan Audit Kohort Multi-Tahun & Kas BSS Yayasan (4 Halaman A4 Landscape)."""
    ctx = pe.build_cohort_yayasan_payload()
    return pb.render_html("07_laporan_yayasan.html", ctx)

# =====================================================================
# ON-DEMAND & BATCH RUNNERS
# =====================================================================

def generate_pdf_bytes_on_demand(pdf_type, npm=None):
    """Menghasilkan buffer PDF langsung on-demand via pdf_bridge."""
    clean_type = str(pdf_type).lower().strip()
    if clean_type not in PDF_TYPE_ALL:
        raise ValueError(
            f"pdf_type '{pdf_type}' tidak dikenal. Pilihan: {', '.join(sorted(set(PDF_TYPE_ALL)))}"
        )
    return pb.generate_pdf_bytes_bridge(clean_type, npm)

def build_all_pdfs():
    """Menjalankan generasi 7 master dokumen via pdf_bridge."""
    target_dir = os.path.join(BASE_DIR, "output", "sample_master")
    results = pb.generate_all_masters(target_dir)
    return target_dir

if __name__ == "__main__":
    print("[INFO] Menjalankan scripts/generate_pdfs.py (Facade)...")
    build_all_pdfs()

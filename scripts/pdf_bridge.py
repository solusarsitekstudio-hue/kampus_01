"""scripts/pdf_bridge.py - RENDERER & ADAPTER UNTUK DOKUMEN PDF (JINJA2 + PLAYWRIGHT)
SIAK-KAPRODI (Architecture Program Studi)

Sesuai Konstitusi sistembuild:
- Bridge ini bertindak sebagai Adapter Protokol antara Core Data Engine (pdf_engine.py)
  dan Presentasi Visual (templates/pdf/*.html via Playwright Chromium).
- Mendukung:
  1. CLI 1 Berkas Master per Tipe: python pdf_bridge.py --type 07
  2. CLI Cetak Seluruh Master: python pdf_bridge.py --all-master
  3. API Web On-Demand Bytes: generate_pdf_bytes_bridge(doc_type, npm)
"""

import os
import sys
import json
import argparse
import time
import re
import threading
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_HERE)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates", "pdf")

if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import pdf_engine as pe
import jinja2
from playwright.sync_api import sync_playwright

# CYBERSECURITY GUARD: Pembatas konkurensi Chromium untuk mencegah OOM / Resource Starvation
_PLAYWRIGHT_SEMAPHORE = threading.BoundedSemaphore(2)

# CYBERSECURITY GUARD: Whitelist NPM murni angka (8-14 digit) untuk mencegah Path Traversal / Injection
NPM_RE = re.compile(r"^\d{8,14}$")

def is_valid_npm(npm):
    """Memvalidasi NPM murni digit angka tanpa karakter path traversal atau injection."""
    if not npm:
        return False
    return bool(NPM_RE.match(str(npm).strip()))

# Setup Jinja2 Environment
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True
)

def render_html(template_name, context):
    """Merender template Jinja2 menjadi string HTML murni."""
    template = _jinja_env.get_template(template_name)
    return template.render(**context)

def get_filename(doc_type, context):
    """Menghasilkan nama berkas standar berdasarkan tipe dan konteks."""
    clean_type = str(doc_type).lower().strip()
    student = context.get("student", {})
    npm = student.get("npm", "")
    nama_clean = student.get("nama", "").replace(" ", "_")
    course = context.get("course", {})
    identitas = context.get("identitas", {})

    if clean_type in ("01", "monthly", "presensi", "rekap_kehadiran"):
        return f"01_rekap_kehadiran_bulanan_{npm}_{nama_clean}.pdf"
    elif clean_type in ("02", "rapor", "final", "rapor_studio"):
        return f"02_rapor_akhir_semester_{npm}_{nama_clean}.pdf"
    elif clean_type in ("03", "gradebook", "kaprodi", "master_gradebook"):
        return "03_laporan_penilaian_kaprodi_master_gradebook.pdf"
    elif clean_type in ("04", "evaluasi", "audit", "dosen", "evaluasi_dosen"):
        return "04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf"
    elif clean_type in ("05", "deckcraft", "deck"):
        return f"05_deckcraft_portofolio_arsitektur_{npm}_{nama_clean}.pdf"
    elif clean_type in ("05b", "portofolio_lengkap", "porto4", "porto_lengkap", "portofolio"):
        return f"05b_portofolio_lengkap_{npm}_{nama_clean}.pdf"
    elif clean_type in ("06", "boardroom", "boardroom_pitch", "executive_pitch"):
        return "06_boardroom_pitch_deck_yayasan.pdf"
    elif clean_type in ("07", "cohort", "cohort_report", "yayasan", "laporan_yayasan"):
        return "07_laporan_audit_kohort_multitahun_dan_kas_bss.pdf"
    else:
        return f"dokumen_{clean_type}.pdf"

def render_pdf(doc_type, npm=None, output_path=None, page=None):
    """
    Merender PDF menggunakan Playwright Chromium.
    Dilindungi dengan Semaphore konkurensi (maks 2 instance aktif) dan SSRF route interceptor.
    """
    if npm is not None and not is_valid_npm(npm):
        raise ValueError(f"Format NPM tidak valid: '{npm}'. Hanya diperbolehkan 8-14 digit angka.")

    template_name, context, page_config = pe.build_payload(doc_type, npm)
    html_content = render_html(template_name, context)
    filename = get_filename(doc_type, context)

    if output_path is None:
        target_dir = os.path.join(BASE_DIR, "output", "sample_master")
        os.makedirs(target_dir, exist_ok=True)
        output_path = os.path.join(target_dir, filename)

    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    def _do_render(p_obj):
        # SSRF Guard: Blokir panggilan keluar ke domain publik saat render dokumen lokal
        try:
            p_obj.route("**/*", lambda route: route.abort() if route.request.url.startswith("http") and not ("127.0.0.1" in route.request.url or "localhost" in route.request.url) else route.continue_())
        except Exception:
            pass
        p_obj.set_content(html_content)
        pdf_bytes = p_obj.pdf(
            path=output_path,
            format=page_config.get("format", "A4"),
            landscape=page_config.get("landscape", False),
            print_background=True,
            margin=page_config.get("margin", {"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
        )
        return pdf_bytes

    if page is not None:
        pdf_bytes = _do_render(page)
    else:
        with _PLAYWRIGHT_SEMAPHORE:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    pg = browser.new_page()
                    pdf_bytes = _do_render(pg)
                finally:
                    browser.close()

    return pdf_bytes, filename, output_path

def generate_pdf_bytes_bridge(doc_type, npm=None):
    """Menghasilkan buffer bytes PDF untuk stream download API web tanpa menulis file fisik."""
    if npm is not None and not is_valid_npm(npm):
        raise ValueError(f"Format NPM tidak valid: '{npm}'. Hanya diperbolehkan 8-14 digit angka.")

    template_name, context, page_config = pe.build_payload(doc_type, npm)
    html_content = render_html(template_name, context)
    filename = get_filename(doc_type, context)

    with _PLAYWRIGHT_SEMAPHORE:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                pg = browser.new_page()
                try:
                    pg.route("**/*", lambda route: route.abort() if route.request.url.startswith("http") and not ("127.0.0.1" in route.request.url or "localhost" in route.request.url) else route.continue_())
                except Exception:
                    pass
                pg.set_content(html_content)
                pdf_bytes = pg.pdf(
                    format=page_config.get("format", "A4"),
                    landscape=page_config.get("landscape", False),
                    print_background=True,
                    margin=page_config.get("margin", {"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
                )
            finally:
                browser.close()

    return pdf_bytes, filename

def generate_single_master(doc_type, npm=None, output_dir=None):
    """Menghasilkan 1 file master PDF untuk tipe tertentu dalam hitungan detik."""
    t0 = time.time()
    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, "output", "sample_master")
    os.makedirs(output_dir, exist_ok=True)

    template_name, context, _ = pe.build_payload(doc_type, npm)
    filename = get_filename(doc_type, context)
    out_file = os.path.join(output_dir, filename)

    print(f"[PDF-BRIDGE] Merender 1 File Master: {filename}...")
    pdf_bytes, fn, pth = render_pdf(doc_type, npm, output_path=out_file)
    dt = time.time() - t0
    size_kb = os.path.getsize(pth) / 1024.0
    print(f"  [OK] Master Dihasilkan: {fn} ({size_kb:.1f} KB) dalam {dt:.2f} detik")
    print(f"       Lokasi: {pth}")
    return pth

def generate_all_masters(output_dir=None):
    """Menghasilkan 1 file master untuk masing-masing dari 7 tipe dokumen."""
    t_start = time.time()
    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, "output", "sample_master")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 72)
    print("[INFO] MEMULAI GENERASI 7 MASTER DOKUMEN PDF (1 FILE PER TIPE)")
    print(f"   Target Folder: {output_dir}")
    print("=" * 72)

    master_types = [
        ("01", "2510015410010", "Rekap Kehadiran Bulanan Mahasiswa (2 Hal Portrait)"),
        ("02", "2510015410010", "Rapor Hasil Belajar Studio (3 Hal Portrait)"),
        ("03", None, "Master Gradebook Kaprodi (3 Hal Landscape)"),
        ("04", None, "Evaluasi Kinerja Dosen & Audit Modul RPS (3 Hal Portrait)"),
        ("05", "2510015410010", "Portofolio Studio DeckCraft (5 Slide Landscape Widescreen)"),
        ("05b", "2510015410010", "Portofolio Mahasiswa 4 Lapis Lengkap (2 Hal Portrait)"),
        ("06", None, "Boardroom Pitch Deck Yayasan (3 Slide Landscape)"),
        ("07", None, "Laporan Audit Kohort & Kas BSS Yayasan (4 Hal Landscape)")
    ]

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            for doc_type, sample_npm, desc in master_types:
                t0 = time.time()
                template_name, context, _ = pe.build_payload(doc_type, sample_npm)
                fn = get_filename(doc_type, context)
                out_path = os.path.join(output_dir, fn)
                
                _, _, pth = render_pdf(doc_type, sample_npm, output_path=out_path, page=page)
                dt = time.time() - t0
                size_kb = os.path.getsize(pth) / 1024.0
                
                # Hitung jumlah halaman tanpa impor pypdf (menjaga aturan dependensi arsitektur)
                page_count = "-"
                try:
                    import re
                    with open(pth, "rb") as _bf:
                        raw_bytes = _bf.read()
                        matches = re.findall(rb"/Type\s*/Page\b", raw_bytes)
                        if matches:
                            page_count = len(matches)
                except Exception:
                    pass

                print(f"  [OK] Dokumen {doc_type}: {fn:<50} | {page_count} Hal | {size_kb:6.1f} KB | {dt:.2f}s")
                results.append({
                    "doc_type": doc_type,
                    "filename": fn,
                    "halaman": page_count,
                    "size_kb": round(size_kb, 1),
                    "waktu_detik": round(dt, 2),
                    "deskripsi": desc,
                    "path": pth
                })
        finally:
            browser.close()

    total_dt = time.time() - t_start
    print("=" * 72)
    print(f"[SUCCESS] SELESAI 7 MASTER DOKUMEN DALAM {total_dt:.2f} DETIK")
    print("=" * 72)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF Bridge Renderer & CLI Adapter")
    parser.add_argument("--type", type=str, help="Tipe dokumen yang akan dicetak (01 s/d 07)")
    parser.add_argument("--npm", type=str, default=None, help="NPM mahasiswa untuk dokumen perorangan")
    parser.add_argument("--all-master", action="store_true", help="Cetak seluruh 7 tipe berkas master")
    parser.add_argument("--outdir", type=str, default=None, help="Direktori target output")

    args = parser.parse_args()

    if args.all_master:
        generate_all_masters(args.outdir)
    elif args.type:
        generate_single_master(args.type, args.npm, args.outdir)
    else:
        # Default: generate single master Dokumen 07 jika tanpa argumen
        print("[INFO] Tanpa argumen spesifik, menjalankan --type 07 default...")
        generate_single_master("07", args.npm, args.outdir)

"""tests/test_static_exporter.py - Test Suite for Static Showcase Bundle (Track 1)
SIAK-KAPRODI (Architecture Program Studi)
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist_gh_pages")
STATIC_API_DIR = os.path.join(DIST_DIR, "static_api")

ok_all = True

def check(label: str, cond: bool, detail: str = ""):
    global ok_all
    ok_all = ok_all and bool(cond)
    status_str = "OK  " if cond else "FAIL"
    print(f"  [{status_str}] {label:50} {detail}")

print("=" * 76)
print("UNIT PROBE: STATIC SHOWCASE EXPORTER (GITHUB PAGES BUNDLE VERIFICATION)")
print("=" * 76)

# 1. Cek folder dist_gh_pages
check("Folder dist_gh_pages ada", os.path.isdir(DIST_DIR), DIST_DIR)
check("File .nojekyll ada", os.path.isfile(os.path.join(DIST_DIR, ".nojekyll")))
check("File index.html ada", os.path.isfile(os.path.join(DIST_DIR, "index.html")))
check("File app.js ada", os.path.isfile(os.path.join(DIST_DIR, "app.js")))
check("File gh_pages_mock.js ada", os.path.isfile(os.path.join(DIST_DIR, "gh_pages_mock.js")))
check("File style.css ada", os.path.isfile(os.path.join(DIST_DIR, "style.css")))
check("Folder vendor ada", os.path.isdir(os.path.join(DIST_DIR, "vendor")))

# 2. Cek index.html memuat gh_pages_mock.js sebelum app.js
with open(os.path.join(DIST_DIR, "index.html"), "r", encoding="utf-8") as f:
    html = f.read()
idx_mock = html.find("gh_pages_mock.js")
idx_app = html.find('src="app.js"')
check("index.html memuat gh_pages_mock.js", idx_mock != -1)
check("gh_pages_mock.js dimuat SEBELUM app.js", idx_mock < idx_app, f"mock={idx_mock} vs app={idx_app}")
check("index.html memuat Gatekeeper Modal (UI-AUTH-01)", "gatekeeper-modal" in html)
check("index.html memuat Lock Session Button (UI-AUTH-02)", "btn-lock-session" in html)

# 2.1 Cek mock interceptor mendukung verifikasi PIN (SYS-SEC-10)
with open(os.path.join(DIST_DIR, "gh_pages_mock.js"), "r", encoding="utf-8") as f:
    mock_code = f.read()
check("gh_pages_mock.js menangani /api/auth/verify_pin", "/api/auth/verify_pin" in mock_code)
check("gh_pages_mock.js menangani PIN 404040", "404040" in mock_code)

# 3. Cek integritas seluruh JSON di static_api/
expected_jsons = [
    "data.json", "courses.json", "kurikulum.json", "identitas.json",
    "registry_cohorts.json", "analytics_growth.json", "analytics_overview.json",
    "bridge_summary.json", "bridge_retakes.json", "executive_cockpit.json",
    "runs.json", "periode.json", "perkembangan.json", "portofolio.json",
    "student_sample.json", "registry_student.json", "kurikulum_detail.json",
    "bridge_presensi.json", "bridge_nilai.json"
]

print("\n[2] Verifikasi Format & Parsing 19 Berkas JSON...")
for j_name in expected_jsons:
    p = os.path.join(STATIC_API_DIR, j_name)
    exists = os.path.isfile(p)
    valid_json = False
    size_kb = 0
    if exists:
        try:
            with open(p, "r", encoding="utf-8") as f:
                json.load(f)
            valid_json = True
            size_kb = os.path.getsize(p) / 1024.0
        except Exception:
            pass
    check(f"static_api/{j_name}", exists and valid_json, f"{size_kb:.1f} KB")

# 4. Cek master PDFs
print("\n[3] Verifikasi Sample Master PDFs...")
pdf_dir = os.path.join(DIST_DIR, "generated_pdfs")
check("Folder generated_pdfs ada", os.path.isdir(pdf_dir))
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
check("Minimal 7 master PDF terangkut", len(pdf_files) >= 7, f"total={len(pdf_files)}")

print("\n" + "=" * 76)
print("HASIL: " + ("SEMUA LULUS (BUNDLE SIAP DEPLOY)" if ok_all else "ADA YANG GAGAL"))
print("=" * 76)

sys.exit(0 if ok_all else 1)

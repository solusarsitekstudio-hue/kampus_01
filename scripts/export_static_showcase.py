"""scripts/export_static_showcase.py - STATIC SHOWCASE COMPILER FOR GITHUB PAGES
SIAK-KAPRODI (Architecture Program Studi)

Sesuai Konstitusi sistembuild (Kabel SYS-ENG-20 & SYS-DAT-09):
- Membekukan seluruh dataset dan API backend ke file JSON statis lokal.
- Menyalin seluruh antarmuka web (HTML, CSS, JS, Vendor) ke folder dist_gh_pages/.
- Menyuntikkan gh_pages_mock.js untuk intersep fetch transparan (zero modification pada public/app.js).
- Menyediakan bundle mandiri yang siap di-push ke branch gh-pages di GitHub.
"""

import os
import sys
import shutil
import json
import urllib.request
import urllib.error
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_HERE)
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DIST_DIR = os.path.join(BASE_DIR, "dist_gh_pages")
STATIC_API_DIR = os.path.join(DIST_DIR, "static_api")
GENERATED_PDFS_DIR = os.path.join(DIST_DIR, "generated_pdfs")
SAMPLE_MASTER_DIR = os.path.join(BASE_DIR, "output", "sample_master")

LOCAL_SERVER_URL = "http://127.0.0.1:40404"

API_ENDPOINTS = [
    ("/api/data", "data.json"),
    ("/api/courses", "courses.json"),
    ("/api/kurikulum", "kurikulum.json"),
    ("/api/identitas", "identitas.json"),
    ("/api/registry/cohorts", "registry_cohorts.json"),
    ("/api/analytics/growth", "analytics_growth.json"),
    ("/api/analytics/overview", "analytics_overview.json"),
    ("/api/bridge/summary", "bridge_summary.json"),
    ("/api/bridge/retakes", "bridge_retakes.json"),
    ("/api/executive_cockpit", "executive_cockpit.json"),
    ("/api/runs", "runs.json"),
    ("/api/periode?prodi=ARSITEKTUR&semua_semester=1", "periode.json"),
    ("/api/perkembangan?prodi=ARSITEKTUR&npm=2410015410001", "perkembangan.json"),
    ("/api/portofolio?npm=2410015410001", "portofolio.json"),
    ("/api/student/2410015410001", "student_sample.json"),
    ("/api/registry/student?npm=2510015410010", "registry_student.json"),
    ("/api/kurikulum/detail?prodi=ARSITEKTUR&tahun_ajar=2024-2025&semester=GANJIL&kunci_mk=ARS101", "kurikulum_detail.json"),
    ("/api/bridge/presensi?npm=2410015410001", "bridge_presensi.json"),
    ("/api/bridge/nilai?npm=2410015410001", "bridge_nilai.json"),
]

def fetch_json(endpoint):
    url = f"{LOCAL_SERVER_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "StaticExporter/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def build_showcase():
    t0 = time.time()
    print("=" * 74)
    print("[EXPORT-STATIC] MEMBANGUN STATIC SHOWCASE UNTUK GITHUB PAGES (TRACK 1)")
    print("=" * 74)

    # 1. Bersihkan & buat direktori tujuan
    if os.path.exists(DIST_DIR):
        print(f"[CLEAN] Membersihkan folder lama: {DIST_DIR}")
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(STATIC_API_DIR, exist_ok=True)
    os.makedirs(GENERATED_PDFS_DIR, exist_ok=True)

    # 2. Ambil data dari server lokal
    print("\n[STEP 1] Mengambil dan membekukan API response ke JSON...")
    berhasil_api = 0
    for endpoint, out_name in API_ENDPOINTS:
        try:
            data = fetch_json(endpoint)
            out_path = os.path.join(STATIC_API_DIR, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            size_kb = os.path.getsize(out_path) / 1024.0
            print(f"  [OK] {endpoint:45} -> static_api/{out_name} ({size_kb:.1f} KB)")
            berhasil_api += 1
        except Exception as e:
            print(f"  [WARN] Gagal fetch {endpoint}: {e}")

    # 3. Salin aset frontend dari public/
    print("\n[STEP 2] Menyalin aset antarmuka publik...")
    for item in os.listdir(PUBLIC_DIR):
        s = os.path.join(PUBLIC_DIR, item)
        d = os.path.join(DIST_DIR, item)
        if os.path.isdir(s):
            # Jangan salin folder video berukuran raksasa jika ada
            if item == "videos":
                continue
            shutil.copytree(s, d)
            print(f"  [DIR]  public/{item}/ -> dist_gh_pages/{item}/")
        else:
            shutil.copy2(s, d)
            print(f"  [FILE] public/{item} -> dist_gh_pages/{item}")

    # 4. Injeksi gh_pages_mock.js ke index.html
    print("\n[STEP 3] Menyuntikkan Mock Interceptor ke index.html...")
    index_path = os.path.join(DIST_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Pastikan gh_pages_mock.js dimuat SEBELUM app.js
    if "gh_pages_mock.js" not in html:
        if '<script src="app.js"' in html:
            html = html.replace(
                '<script src="app.js"',
                '<script src="gh_pages_mock.js"></script>\n  <script src="app.js"'
            )
            print("  [OK] gh_pages_mock.js berhasil disuntikkan sebelum app.js")
        elif '<script src="/app.js"' in html:
            html = html.replace(
                '<script src="/app.js"',
                '<script src="gh_pages_mock.js"></script>\n  <script src="app.js"'
            )
            print("  [OK] gh_pages_mock.js berhasil disuntikkan sebelum /app.js")
        else:
            html = html.replace("</body>", '  <script src="gh_pages_mock.js"></script>\n</body>')
            print("  [OK] gh_pages_mock.js disuntikkan sebelum </body>")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 5. Salin master PDF representatif untuk tombol download di demo
    print("\n[STEP 4] Menyalin sample master PDF untuk tombol download demo...")
    if os.path.exists(SAMPLE_MASTER_DIR):
        for f_name in os.listdir(SAMPLE_MASTER_DIR):
            if f_name.endswith(".pdf"):
                src = os.path.join(SAMPLE_MASTER_DIR, f_name)
                dst = os.path.join(GENERATED_PDFS_DIR, f_name)
                shutil.copy2(src, dst)
                print(f"  [PDF]  {f_name}")
                # Buat alias sample master jika dibutuhkan
                if f_name.startswith("01_"):
                    shutil.copy2(src, os.path.join(GENERATED_PDFS_DIR, "01_sample_master.pdf"))
                elif f_name.startswith("02_"):
                    shutil.copy2(src, os.path.join(GENERATED_PDFS_DIR, "02_sample_master.pdf"))
                elif f_name.startswith("05_"):
                    shutil.copy2(src, os.path.join(GENERATED_PDFS_DIR, "05_sample_master.pdf"))

    # 6. Buat .nojekyll agar GitHub Pages tidak memfilter aset tertentu
    nojekyll_path = os.path.join(DIST_DIR, ".nojekyll")
    with open(nojekyll_path, "w", encoding="utf-8") as f:
        f.write("")
    print("  [OK] Berkas .nojekyll dibuat (GitHub Pages compatibility)")

    # 7. Hitung total ukuran bundle
    total_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(DIST_DIR)
        for filename in filenames
    )
    dt = time.time() - t0
    print("\n" + "=" * 74)
    print(f"[SUCCESS] STATIC SHOWCASE BUNDLE SELESAI ({dt:.2f} detik)!")
    print(f"  Direktori Output: {DIST_DIR}")
    print(f"  Total Ukuran    : {total_size / (1024.0 * 1024.0):.2f} MB")
    print(f"  Endpoint Beku   : {berhasil_api} file JSON")
    print("=" * 74)

if __name__ == "__main__":
    build_showcase()

"""
fetch_vendor.py - Kunci aset pihak ketiga ke dalam public/vendor/
=================================================================
TAHAP C-1: MENGHAPUS KETERGANTUNGAN CDN.

Masalah lama: index.html memuat 4 sumber internet (Tailwind, ApexCharts,
Lucide, Google Fonts). Kalau WiFi ngadat / koneksi kampus diblokir, seluruh
dashboard tampil sebagai layar putih. Prototype akademik juga sering dipakai
di ruang rapat yang internetnya tidak bisa diandalkan.

Setelah script ini dijalankan, seluruh aset ada di dalam repo dan
dashboard berjalan 100% OFFLINE.

Cara pakai:
    python scripts/fetch_vendor.py            # unduh yang belum ada
    python scripts/fetch_vendor.py --force     # unduh ulang semua

Catatan:
  * Versi di-PIN (bukan "latest") supaya tampilan tidak berubah diam-diam.
  * Tailwind TIDAK diunduh di sini, karena yang benar adalah membangun CSS
    statis. Pakai scripts/build_tailwind.bat (butuh Node.js sekali saja).
  * Hash SHA-256 setiap file dicatat di public/vendor/VENDOR.md untuk audit.
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR_DIR = os.path.join(BASE_DIR, "public", "vendor")
FONT_DIR = os.path.join(VENDOR_DIR, "fonts")

# User-Agent modern supaya Google Fonts mengirim woff2, bukan ttf lama
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# --- Versi yang DI-PIN. Jangan ganti ke "latest". -----------------------------
APEXCHARTS_URL = (
    "https://cdn.jsdelivr.net/npm/apexcharts@3.54.1/dist/apexcharts.min.js"
)
LUCIDE_URL = "https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js"
GFONTS_CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800"
    "&family=JetBrains+Mono:wght@400;500;600&display=swap"
)

JS_ASSETS = [
    ("apexcharts.min.js", APEXCHARTS_URL, "ApexCharts 3.54.1 (MIT)"),
    ("lucide.min.js", LUCIDE_URL, "Lucide 0.460.0 (ISC)"),
]


def fetch(url: str, binary: bool = True):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": CHROME_UA,
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read()
    return raw if binary else raw.decode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_file(path: str, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def download_js(force: bool, manifest: list) -> int:
    count = 0
    for name, url, label in JS_ASSETS:
        dest = os.path.join(VENDOR_DIR, name)
        if os.path.exists(dest) and not force:
            size = os.path.getsize(dest)
            print(f"  [skip]    {name:22} sudah ada ({size:,} B)")
            with open(dest, "rb") as f:
                manifest.append((name, label, url, size, sha256_bytes(f.read())))
            continue
        try:
            data = fetch(url)
        except Exception as e:
            print(f"  [GAGAL]   {name:22} {type(e).__name__}: {e}")
            continue
        write_file(dest, data)
        manifest.append((name, label, url, len(data), sha256_bytes(data)))
        print(f"  [unduh]   {name:22} {len(data):,} B")
        count += 1
    return count


def download_fonts(force: bool, manifest: list) -> int:
    """Ambil CSS Google Fonts lalu lokalkan seluruh file woff2-nya."""
    css_path = os.path.join(VENDOR_DIR, "fonts.css")
    try:
        css = fetch(GFONTS_CSS_URL, binary=False)
    except Exception as e:
        print(f"  [GAGAL]   fonts.css  {type(e).__name__}: {e}")
        return 0

    urls = re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)
    # urls() bisa duplikat antar blok unicode-range; dedup tapi pertahankan urutan
    seen, ordered = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)

    mapping = {}
    downloaded = 0
    for url in ordered:
        fname = url.rsplit("/", 1)[-1]
        # Beberapa family bisa punya nama file sama; prefix hash pendek bila bentrok
        if fname in mapping.values():
            fname = sha256_bytes(url.encode())[:6] + "-" + fname
        dest = os.path.join(FONT_DIR, fname)
        if os.path.exists(dest) and not force:
            with open(dest, "rb") as f:
                data = f.read()
        else:
            try:
                data = fetch(url)
            except Exception as e:
                print(f"  [GAGAL]   font {fname}  {type(e).__name__}: {e}")
                continue
            write_file(dest, data)
            downloaded += 1
        mapping[url] = fname
        manifest.append(
            (f"fonts/{fname}", "Google Fonts woff2 (OFL)", url, len(data),
             sha256_bytes(data))
        )

    for url, fname in mapping.items():
        css = css.replace(url, f"fonts/{fname}")

    # Buang preconnect/comment yang tidak relevan, simpan @font-face saja
    write_file(css_path, css.encode("utf-8"))
    print(f"  [unduh]   fonts.css              {len(css):,} B "
          f"({len(mapping)} file woff2, {downloaded} baru)")
    manifest.append(
        ("fonts.css", "Google Fonts CSS (lokalisasi)", GFONTS_CSS_URL,
         len(css.encode("utf-8")), sha256_bytes(css.encode("utf-8")))
    )
    return downloaded


def write_manifest(manifest: list):
    lines = [
        "# Aset Vendor (Offline)",
        "",
        "Folder ini dihasilkan oleh `python scripts/fetch_vendor.py`.",
        "Jangan diedit manual. Untuk memperbarui versi, ubah pin di dalam",
        "script tersebut lalu jalankan dengan `--force`.",
        "",
        "| File | Keterangan | Ukuran | SHA-256 (12) |",
        "| --- | --- | --- | --- |",
    ]
    for name, label, _url, size, digest in sorted(manifest):
        lines.append(f"| `{name}` | {label} | {size:,} B | `{digest[:12]}` |")
    lines += [
        "",
        "## Sumber",
        "",
    ]
    for name, _label, url, _size, _digest in sorted(manifest):
        lines.append(f"- `{name}` <- {url}")
    lines += [
        "",
        "## Tailwind CSS",
        "",
        "CSS Tailwind **tidak** diunduh dari internet pada saat runtime.",
        "Dibangun sekali menjadi `tailwind.css` (statis) lewat",
        "`scripts/build_tailwind.bat`, sehingga halaman tidak lagi memakai",
        "JIT compiler di browser.",
        "",
    ]
    write_file(
        os.path.join(VENDOR_DIR, "VENDOR.md"),
        "\n".join(lines).encode("utf-8"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="unduh ulang walau file sudah ada")
    args = ap.parse_args()

    os.makedirs(FONT_DIR, exist_ok=True)
    print("=" * 66)
    print("KUNCI ASET VENDOR -> public/vendor/")
    print("=" * 66)

    manifest = []
    print("[1/2] Library JavaScript")
    n_js = download_js(args.force, manifest)
    print("[2/2] Google Fonts (Plus Jakarta Sans + JetBrains Mono)")
    n_font = download_fonts(args.force, manifest)

    write_manifest(manifest)
    print("-" * 66)
    print(f"Selesai: {n_js} library baru, {n_font} file font baru.")
    print(f"Manifest: public/vendor/VENDOR.md")
    print("=" * 66)


if __name__ == "__main__":
    main()

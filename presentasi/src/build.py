"""Bangun deck proposal SIAK-KAPRODI: PDF 16:9 + PNG per slide.

Jalankan dari root repo:
    python presentasi/src/build.py

Output:
    presentasi/SIAK-KAPRODI_Proposal_2026_16x9.pdf
    presentasi/png/slide-1.png ... slide-5.png   (1920x1080)
"""
import os
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "deck.html")
OUT_PDF = os.path.join(ROOT, "SIAK-KAPRODI_Proposal_2026_16x9.pdf")
OUT_PNG = os.path.join(ROOT, "png")


def count_pdf_pages(path):
    with open(path, "rb") as fh:
        data = fh.read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def pdf_mediabox(path):
    with open(path, "rb") as fh:
        data = fh.read()
    m = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", data)
    return (float(m.group(1)), float(m.group(2))) if m else None


def main():
    os.makedirs(OUT_PNG, exist_ok=True)
    external = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)

        def track(req):
            if req.url.startswith(("http://", "https://")):
                external.append(req.url)

        page.on("request", track)
        page.goto("file:///" + SRC.replace("\\", "/"), wait_until="load")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(1200)

        # Pastikan font lokal benar-benar terpakai (bukan fallback sistem)
        font_ok = page.evaluate(
            """() => ({
                jakarta: document.fonts.check('800 48px "Plus Jakarta Sans"'),
                mono: document.fonts.check('400 12px "JetBrains Mono"'),
                loaded: document.fonts.status
            })"""
        )
        print("[INFO] font:", font_ok)

        slides = page.locator(".slide")
        n = slides.count()
        print(f"[INFO] slide ditemukan: {n}")

        page.pdf(
            path=OUT_PDF,
            width="13.333in",
            height="7.5in",
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            print_background=True,
            prefer_css_page_size=False,
        )

        for i in range(n):
            el = slides.nth(i)
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(180)
            el.screenshot(path=os.path.join(OUT_PNG, f"slide-{i + 1}.png"))

        browser.close()

    pages = count_pdf_pages(OUT_PDF)
    box = pdf_mediabox(OUT_PDF)
    size_mb = os.path.getsize(OUT_PDF) / (1024 * 1024)
    print(f"[OK] PDF: {os.path.basename(OUT_PDF)} | {pages} halaman | {size_mb:.2f} MB | MediaBox {box}")
    print(f"[OK] PNG: {n} berkas di presentasi/png")
    print(f"[INFO] request eksternal: {len(external)}")
    if external:
        for u in external[:5]:
            print("   ", u)

    expected = (960.0, 540.0)
    errors = []
    if pages != n:
        errors.append(f"jumlah halaman {pages} != {n}")
    if box is None or abs(box[0] - expected[0]) > 1 or abs(box[1] - expected[1]) > 1:
        errors.append(f"MediaBox {box} bukan 16:9 (960x540 pt)")
    if external:
        errors.append(f"ada {len(external)} request eksternal")
    if not (font_ok.get("jakarta") and font_ok.get("mono")):
        errors.append("font lokal tidak termuat")
    if errors:
        for e in errors:
            print("[FAIL]", e)
        return 1
    print("[PASS] deck valid: 16:9, font lokal, offline")
    return 0


if __name__ == "__main__":
    sys.exit(main())

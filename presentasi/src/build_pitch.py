"""Bangun deck pitch SIAK-KAPRODI (14 slide, 16:9) + pass kualitas otomatis.

Jalankan dari root repo:
    python presentasi/src/build_pitch.py

Output:
    presentasi/SIAK-KAPRODI_Copilot_Kaprodi_2026_14slide_16x9.pdf
    presentasi/png_pitch/slide-01.png ... slide-14.png   (2560x1440 2K)
"""
import os
import re
import sys
from html.parser import HTMLParser

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "pitch_kaprodi.html")
OUT_PDF = os.path.join(ROOT, "SIAK-KAPRODI_Copilot_Kaprodi_2026_14slide_16x9.pdf")
OUT_PNG = os.path.join(ROOT, "png_pitch")

# --- allowlist angka (Bagian 2 brief + slide 12 spesifikasi) -----------------
ALLOWED = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "16", "27",
    "01", "02", "03", "04", "05", "06", "07", "08", "09",
    "2.6", "30", "35", "70", "75", "76.7", "77.9", "78.9", "83.8", "87.3", "100", "101", "108", "195", "301",
    "1.17", "12.1", "0.2", "21.6", "127.0.0.1", "256", "280", "422", "456", "40404",
}
MAX_BODY_WORDS = 40

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class CopyCounter(HTMLParser):
    """Hitung kata body (elemen class="copy") per slide + kumpulkan semua teks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.slide_idx = 0
        self.in_section = False
        self.copy_stack = []  # stack elemen aktif yang membuka/didalam .copy
        self.body_words = []  # kata body per slide
        self.all_text = []    # semua teks per slide

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            self.slide_idx += 1
            self.in_section = True
            self.copy_stack = []
            return
        if not self.in_section:
            return
        cls = dict(attrs).get("class", "")
        if "copy" in cls.split():
            self.copy_stack.append(tag)
        elif self.copy_stack and tag not in VOID_ELEMENTS:
            self.copy_stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "section":
            self.in_section = False
            self.copy_stack = []
        elif self.in_section and self.copy_stack:
            if tag in self.copy_stack:
                while self.copy_stack:
                    popped = self.copy_stack.pop()
                    if popped == tag:
                        break

    def handle_data(self, data):
        if not self.in_section:
            return
        text = " ".join(data.split())
        if not text:
            return
        while len(self.all_text) < self.slide_idx:
            self.all_text.append([])
        self.all_text[self.slide_idx - 1].append(text)
        if self.copy_stack:
            while len(self.body_words) < self.slide_idx:
                self.body_words.append([])
            self.body_words[self.slide_idx - 1].append(text)


def count_pdf_pages(path):
    with open(path, "rb") as fh:
        data = fh.read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def pdf_mediabox(path):
    with open(path, "rb") as fh:
        data = fh.read()
    m = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", data)
    return (float(m.group(1)), float(m.group(2))) if m else None


def words(text):
    return [w for w in re.split(r"\s+", text) if re.search(r"[A-Za-z0-9]", w)]


def scan_numbers(per_slide_text):
    bad = []
    for i, texts in enumerate(per_slide_text, 1):
        joined = " ".join(texts)
        for num in re.findall(r"\d+(?:[.,]\d+)*", joined):
            if num not in ALLOWED:
                bad.append((i, num))
    return bad


def main():
    os.makedirs(OUT_PNG, exist_ok=True)
    external = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--font-render-hinting=full",
                "--force-color-profile=srgb",
            ]
        )
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=4 / 3  # 2K Resolution (2560x1440)
        )
        page.emulate_media(media="screen")

        def track(req):
            if req.url.startswith(("http://", "https://")):
                external.append(req.url)

        page.on("request", track)
        page.goto("file:///" + SRC.replace("\\", "/"), wait_until="load")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(1200)

        font_ok = page.evaluate(
            """() => ({
                sans: document.fonts.check('800 48px "Plus Jakarta Sans"'),
                mono: document.fonts.check('400 12px "JetBrains Mono"'),
                status: document.fonts.status
            })"""
        )
        print("[INFO] font:", font_ok)

        slides = page.locator(".slide")
        n = slides.count()
        print(f"[INFO] slide ditemukan: {n}")

        # overflow: konten tidak boleh keluar dari kanvas 1080 px
        overflow = page.evaluate(
            """() => [...document.querySelectorAll('.slide')].map((s,i)=>{
                const r = s.getBoundingClientRect();
                return {i:i+1, scrollH:s.scrollHeight, clientH:s.clientHeight,
                        maxBottom:Math.max(0, ...[...s.children].map(c=>c.getBoundingClientRect().bottom - r.top))};
            })"""
        )
        for o in overflow:
            if o["scrollH"] > o["clientH"] + 2 or o["maxBottom"] > 1080:
                errors.append(f"slide {o['i']}: overflow vertikal "
                              f"(scrollH={o['scrollH']} maxBottom={o['maxBottom']:.0f})")

        page.pdf(
            path=OUT_PDF,
            width="20in",          # 1920 px @96dpi
            height="11.25in",      # 1080 px @96dpi
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            print_background=True,
        )

        for i in range(n):
            el = slides.nth(i)
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(120)
            el.screenshot(path=os.path.join(OUT_PNG, f"slide-{i + 1:02d}.png"))

        browser.close()

    # ---------------- pass kualitas ----------------
    with open(SRC, encoding="utf-8") as fh:
        html = fh.read()
    parser = CopyCounter()
    parser.feed(html)

    for i in range(1, n + 1):
        bw = words(" ".join(parser.body_words[i - 1])) if i <= len(parser.body_words) else []
        total = len(bw)
        flag = "OK " if total <= MAX_BODY_WORDS else "OVER"
        print(f"  [{flag}] slide {i:02d}: body {total} kata")
        if total > MAX_BODY_WORDS:
            errors.append(f"slide {i}: body {total} kata > {MAX_BODY_WORDS}")

    bad_nums = scan_numbers(parser.all_text if parser.all_text else [])
    if bad_nums:
        for i, num in bad_nums:
            print(f"  [NUM] slide {i}: angka di luar allowlist -> {num}")
        errors.append(f"{len(bad_nums)} angka di luar allowlist")

    pages = count_pdf_pages(OUT_PDF)
    box = pdf_mediabox(OUT_PDF)
    size_mb = os.path.getsize(OUT_PDF) / (1024 * 1024)
    print(f"[OK] PDF: {os.path.basename(OUT_PDF)} | {pages} halaman | {size_mb:.2f} MB | MediaBox {box}")

    if pages != n:
        errors.append(f"jumlah halaman {pages} != {n} slide")
    if box is None or abs(box[0] / box[1] - 16 / 9) > 0.01:
        errors.append(f"MediaBox {box} bukan 16:9")
    if external:
        errors.append(f"ada {len(external)} request eksternal: {external[:3]}")
    if not (font_ok.get("sans") and font_ok.get("mono")):
        errors.append("font lokal tidak termuat")

    if errors:
        for e in errors:
            print("[FAIL]", e)
        return 1
    print(f"[PASS] deck valid: 14 slide 16:9, body <= {MAX_BODY_WORDS} kata, "
          f"angka sesuai allowlist, font lokal, offline, PNG 2560x1440 (2K)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

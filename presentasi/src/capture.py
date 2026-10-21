"""Ambil tangkapan layar dashboard untuk aset deck proposal.

Dijalankan saat server 127.0.0.1:40404 hidup:
    python presentasi/src/capture.py

Output: presentasi/assets/shot-*.png (1600x1000 CSS px, 2x DPR).
"""
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE, "assets")
URL = "http://127.0.0.1:40404/"

HIDE_SCROLLBARS = """
html, body { scrollbar-width: none !important; }
::-webkit-scrollbar { display: none !important; }
"""


def _click_tab(page, label):
    page.evaluate(
        """(label) => {
            const el = [...document.querySelectorAll('button, [role=tab], a')]
                .find(b => (b.textContent || '').trim().startsWith(label));
            if (el) el.click();
            return !!el;
        }""",
        label,
    )
    page.wait_for_timeout(1400)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
        page.goto(URL, wait_until="networkidle")
        page.add_style_tag(content=HIDE_SCROLLBARS)
        page.wait_for_timeout(1800)

        # Tab 1 - Dashboard Kaprodi
        _click_tab(page, "1.")
        page.wait_for_timeout(900)
        page.screenshot(path=os.path.join(ASSETS, "shot-dashboard.png"))

        # Tab 2 - Rapor wali murid (pilih mahasiswa pertama)
        _click_tab(page, "2.")
        page.evaluate(
            """() => {
                const sel = document.querySelector('#student-select, select[id*=student]');
                if (sel && sel.options.length > 1) {
                    sel.selectedIndex = 1;
                    sel.dispatchEvent(new Event('change', { bubbles: true }));
                }
                return sel ? sel.id : 'no-select';
            }"""
        )
        page.wait_for_timeout(1600)
        page.screenshot(path=os.path.join(ASSETS, "shot-rapor.png"))

        # Tab 3 - Portofolio & video
        _click_tab(page, "3.")
        page.wait_for_timeout(2200)
        page.screenshot(path=os.path.join(ASSETS, "shot-portofolio.png"))

        browser.close()

    for name in ("shot-dashboard.png", "shot-rapor.png", "shot-portofolio.png"):
        path = os.path.join(ASSETS, name)
        print(f"[OK] {name}: {os.path.getsize(path) // 1024} KB" if os.path.exists(path) else f"[MISS] {name}")


if __name__ == "__main__":
    sys.exit(main())

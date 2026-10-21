"""Capture slide DeckCraft mahasiswa (HTML interaktif) untuk aset pitch deck."""
import os

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE, "assets")
URL = "http://127.0.0.1:40404/api/deckcraft_html?npm=2510015410001"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=2)
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    slides = page.locator(".slide")
    count = slides.count()
    print("slides:", count)
    for i in range(min(count, 2)):
        el = slides.nth(i)
        el.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        el.screenshot(path=os.path.join(ASSETS, f"deck-slide-{i + 1}.png"))
        print("[OK]", f"deck-slide-{i + 1}.png")
    browser.close()

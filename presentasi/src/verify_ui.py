from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:40404/", wait_until="networkidle")
    pg.wait_for_timeout(2000)

    vp = pg.evaluate('document.querySelector("meta[name=viewport]")?.content')
    cs = pg.evaluate('document.querySelector("meta[name=color-scheme]")?.content')
    print("viewport:", vp)
    print("color-scheme:", cs)

    fs = pg.evaluate('getComputedStyle(document.documentElement).webkitFontSmoothing')
    print("font-smoothing:", fs)

    sb = pg.evaluate('getComputedStyle(document.documentElement).scrollBehavior')
    print("scroll-behavior:", sb)

    rm = pg.evaluate('window.matchMedia("(prefers-reduced-motion: reduce)").matches')
    print("prefers-reduced-motion:", rm)

    cc = pg.evaluate('window.matchMedia("(prefers-contrast: more)").matches')
    print("prefers-contrast:", cc)

    # Check some touch targets
    btns = pg.locator(".touch-target")
    print("touch-target elements:", btns.count())

    for i in range(min(btns.count(), 5)):
        btn = btns.nth(i)
        box = btn.bounding_box()
        if box:
            txt = btn.text_content()[:30] if btn.text_content() else "no-text"
            print("  [%d] %dx%d - %s" % (i, box["width"], box["height"], txt))

    b.close()
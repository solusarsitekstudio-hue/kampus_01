"""Script untuk membangun dan menguji Interactive Animated Web Deck SIAK-KAPRODI (16:9).

Output:
    presentasi/src/pitch_interactive.html
    presentasi/pitch_interactive.html  (copy root untuk akses cepat)
"""
import os
import re
import sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_STATIC = os.path.join(ROOT, "src", "pitch_kaprodi.html")
OUT_INTERACTIVE_SRC = os.path.join(ROOT, "src", "pitch_interactive.html")
OUT_INTERACTIVE_ROOT = os.path.join(ROOT, "pitch_interactive.html")

def build_interactive_deck():
    with open(SRC_STATIC, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update Title & Fonts href
    html = html.replace("<title>SIAK-KAPRODI — Co-pilot Kaprodi (Pitch 14 slide)</title>",
                        "<title>SIAK-KAPRODI — Interactive Animated Deck (14 Slide)</title>")

    # 2. Extract slides sections
    sections = re.findall(r"(<section class=\"slide s-\d+\">.*?</section>)", html, re.DOTALL)
    if len(sections) != 14:
        raise ValueError(f"Diharapkan 14 slide, tetapi ditemukan {len(sections)}")

    # Mark animatable SVG in slide 5 & 6
    # In slide 5: trendline polyline & radar polygon
    sections[4] = sections[4].replace(
        '<polyline fill="none" stroke="#fbbf24" stroke-width="3" stroke-linejoin="round"',
        '<polyline class="anim-trend" fill="none" stroke="#fbbf24" stroke-width="3" stroke-linejoin="round"'
    )
    sections[4] = sections[4].replace(
        '<polygon points="0,-62 50.6,-16.4 34.0,46.8 -26.8,37.0 -47.8,-15.4"',
        '<polygon class="anim-radar" points="0,-62 50.6,-16.4 34.0,46.8 -26.8,37.0 -47.8,-15.4"'
    )
    # In slide 6: radar polygon
    sections[5] = sections[5].replace(
        '<polygon points="0,-120 97.2,-31.6 65.2,89.8 -51.5,70.9 -91.6,-29.7"',
        '<polygon class="anim-radar" points="0,-120 97.2,-31.6 65.2,89.8 -51.5,70.9 -91.6,-29.7"'
    )

    # 3. Interactive Deck CSS
    interactive_css = """
/* ========================================================
   INTERACTIVE ANIMATED DECK ENGINE (OTAK-CR & OPENCODE)
======================================================== */
html, body {
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #020409;
  user-select: none;
}
#deck-viewport {
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
#deck-stage {
  position: absolute;
  width: 1920px;
  height: 1080px;
  transform-origin: center center;
  transition: transform 0.1s ease-out;
}
#deck-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--amber), var(--cyan) 50%, var(--violet));
  z-index: 1000;
  transition: width 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.7);
}

/* Slide Transition Engine */
.slide {
  position: absolute;
  inset: 0;
  width: 1920px;
  height: 1080px;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: scale(0.97) translateY(14px);
  transition: opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.4s cubic-bezier(0.16, 1, 0.3, 1),
              visibility 0.4s;
}
.slide.active {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: scale(1) translateY(0);
  z-index: 10;
}
.slide.past {
  opacity: 0;
  visibility: hidden;
  transform: scale(1.02) translateY(-14px);
}

/* Staggered Element Reveals inside Active Slide */
.slide .card,
.slide .panel,
.slide .kpi,
.slide .node,
.slide .out,
.slide .quote {
  opacity: 0;
  transform: translateY(18px);
  transition: opacity 0.45s cubic-bezier(0.16, 1, 0.3, 1), transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide.active .card,
.slide.active .panel,
.slide.active .kpi,
.slide.active .node,
.slide.active .out,
.slide.active .quote {
  opacity: 1;
  transform: translateY(0);
}
.slide.active .c4 .card:nth-child(1) { transition-delay: 0.08s; }
.slide.active .c4 .card:nth-child(2) { transition-delay: 0.16s; }
.slide.active .c4 .card:nth-child(3) { transition-delay: 0.24s; }
.slide.active .c4 .card:nth-child(4) { transition-delay: 0.32s; }

.slide.active .kpis .kpi:nth-child(1) { transition-delay: 0.06s; }
.slide.active .kpis .kpi:nth-child(2) { transition-delay: 0.14s; }
.slide.active .kpis .kpi:nth-child(3) { transition-delay: 0.22s; }
.slide.active .kpis .kpi:nth-child(4) { transition-delay: 0.30s; }

.slide.active .pipe .node:nth-child(1) { transition-delay: 0.08s; }
.slide.active .pipe .node:nth-child(3) { transition-delay: 0.20s; }
.slide.active .pipe .node:nth-child(5) { transition-delay: 0.32s; }
.slide.active .pipe .node:nth-child(7) { transition-delay: 0.44s; }

.slide.active .outs .out:nth-child(1) { transition-delay: 0.10s; }
.slide.active .outs .out:nth-child(2) { transition-delay: 0.20s; }
.slide.active .outs .out:nth-child(3) { transition-delay: 0.30s; }
.slide.active .outs .out:nth-child(4) { transition-delay: 0.40s; }

/* SVG Dynamic Plotting Animation */
@keyframes drawPolyline {
  from { stroke-dashoffset: 1400; }
  to { stroke-dashoffset: 0; }
}
.slide.active polyline.anim-trend {
  stroke-dasharray: 1400;
  stroke-dashoffset: 1400;
  animation: drawPolyline 1.3s cubic-bezier(0.16, 1, 0.3, 1) forwards 0.25s;
}

@keyframes bloomRadar {
  0% { transform: scale(0.2); opacity: 0; }
  70% { transform: scale(1.04); opacity: 0.9; }
  100% { transform: scale(1); opacity: 1; }
}
.slide.active polygon.anim-radar {
  transform-origin: 0 0;
  animation: bloomRadar 0.9s cubic-bezier(0.34, 1.56, 0.64, 1) forwards 0.2s;
}

/* Floating Architectural Control HUD */
#deck-hud {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(10, 16, 28, 0.88);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  padding: 8px 18px;
  z-index: 2000;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.12);
  transition: opacity 0.3s ease, transform 0.3s ease;
}
#deck-hud button {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #f8fafc;
  font-family: var(--sans);
  font-size: 13.5px;
  font-weight: 600;
  padding: 7px 15px;
  border-radius: 999px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.18s ease;
}
#deck-hud button:hover {
  background: rgba(56, 189, 248, 0.2);
  border-color: var(--cyan);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
}
#hud-counter {
  font-family: var(--mono);
  font-size: 14.5px;
  color: var(--tert);
  letter-spacing: 0.12em;
  padding: 0 8px;
}
#hud-counter span#current-slide {
  color: var(--amber);
  font-weight: 700;
  font-size: 16px;
}
.hud-sep {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.14);
}
#deck-hud button.active {
  background: rgba(251, 191, 36, 0.2);
  border-color: var(--amber);
  color: var(--amber);
}

/* Keyboard hint chip */
#key-hints {
  position: fixed;
  bottom: 28px;
  right: 28px;
  font-family: var(--mono);
  font-size: 12px;
  color: rgba(148, 163, 184, 0.6);
  letter-spacing: 0.1em;
  z-index: 1500;
  pointer-events: none;
}
"""

    # 4. Interactive JavaScript Engine
    interactive_js = """
<script>
(function() {
  const stage = document.getElementById('deck-stage');
  const slides = Array.from(document.querySelectorAll('.slide'));
  const progress = document.getElementById('deck-progress');
  const curSlideEl = document.getElementById('current-slide');
  const totalSlideEl = document.getElementById('total-slides');
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnFs = document.getElementById('btn-fs');
  const btnAutoplay = document.getElementById('btn-autoplay');

  let currentIndex = 0;
  let autoplayTimer = null;
  const total = slides.length;

  totalSlideEl.textContent = String(total).padStart(2, '0');

  // Responsive Fit 16:9 Stage scaling
  function resizeStage() {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const scale = Math.min(vw / 1920, vh / 1080);
    stage.style.transform = `scale(${scale})`;
  }
  window.addEventListener('resize', resizeStage);
  resizeStage();

  // Number Counter Animation for KPI Slide (Slide 5)
  function animateNumbers(slideEl) {
    const kpiValues = slideEl.querySelectorAll('.kpi .v');
    kpiValues.forEach(el => {
      const targetStr = el.textContent.trim();
      const targetNum = parseFloat(targetStr);
      if (isNaN(targetNum)) return;
      const isDecimal = targetStr.includes('.');
      const duration = 850;
      const startTime = performance.now();

      function update(now) {
        const elapsed = now - startTime;
        const progressRate = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progressRate, 3);
        const current = targetNum * easeOut;
        el.textContent = isDecimal ? current.toFixed(1) : Math.round(current);
        if (progressRate < 1) {
          requestAnimationFrame(update);
        } else {
          el.textContent = targetStr;
        }
      }
      requestAnimationFrame(update);
    });
  }

  function goToSlide(index) {
    if (index < 0) index = 0;
    if (index >= total) index = total - 1;
    currentIndex = index;

    slides.forEach((s, i) => {
      s.classList.remove('active', 'past');
      if (i === currentIndex) {
        s.classList.add('active');
        if (i === 4) { // Slide 5: Tab 1 KPI
          setTimeout(() => animateNumbers(s), 100);
        }
      } else if (i < currentIndex) {
        s.classList.add('past');
      }
    });

    // Update Counter & Progress
    curSlideEl.textContent = String(currentIndex + 1).padStart(2, '0');
    progress.style.width = `${((currentIndex + 1) / total) * 100}%`;
  }

  function nextSlide() { goToSlide(currentIndex + 1); }
  function prevSlide() { goToSlide(currentIndex - 1); }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  function toggleAutoplay() {
    if (autoplayTimer) {
      clearInterval(autoplayTimer);
      autoplayTimer = null;
      btnAutoplay.classList.remove('active');
      btnAutoplay.textContent = '▶ Auto';
    } else {
      btnAutoplay.classList.add('active');
      btnAutoplay.textContent = '⏸ Pause';
      autoplayTimer = setInterval(() => {
        if (currentIndex < total - 1) {
          nextSlide();
        } else {
          goToSlide(0);
        }
      }, 7000);
    }
  }

  // Keyboard Navigation
  window.addEventListener('keydown', (e) => {
    switch(e.key) {
      case 'ArrowRight':
      case 'Space':
      case 'PageDown':
        e.preventDefault();
        nextSlide();
        break;
      case 'ArrowLeft':
      case 'Backspace':
      case 'PageUp':
        e.preventDefault();
        prevSlide();
        break;
      case 'Home':
        e.preventDefault();
        goToSlide(0);
        break;
      case 'End':
        e.preventDefault();
        goToSlide(total - 1);
        break;
      case 'f':
      case 'F':
        toggleFullscreen();
        break;
    }
  });

  // Button Listeners
  btnNext.addEventListener('click', nextSlide);
  btnPrev.addEventListener('click', prevSlide);
  btnFs.addEventListener('click', toggleFullscreen);
  btnAutoplay.addEventListener('click', toggleAutoplay);

  // Initialize Slide 1
  goToSlide(0);
})();
</script>
"""

    # 5. Build Final HTML Document
    # Inject CSS
    body_idx = html.find("</style>")
    html_with_css = html[:body_idx] + interactive_css + html[body_idx:]

    # Replace slides inside a deck-viewport and deck-stage container
    slides_combined = "\n".join(sections)
    deck_markup = f"""
<div id="deck-viewport">
  <div id="deck-progress"></div>
  <div id="deck-stage">
{slides_combined}
  </div>
  <div id="deck-hud">
    <button id="btn-prev" title="Sebelumnya (Panah Kiri)">◀ Prev</button>
    <div id="hud-counter"><span id="current-slide">01</span> / <span id="total-slides">14</span></div>
    <button id="btn-next" title="Berikutnya (Panah Kanan / Spasi)">Next ▶</button>
    <div class="hud-sep"></div>
    <button id="btn-fs" title="Layar Penuh (F)">⛶ Fullscreen</button>
    <button id="btn-autoplay" title="Auto-Play 7 detik">▶ Auto</button>
  </div>
  <div id="key-hints">KONTROL: [◀ / ▶] GANTI SLIDE · [F] FULLSCREEN · [SPACE] LANJUT</div>
</div>
{interactive_js}
"""

    # Replace original sections in body
    body_start = html_with_css.find("<body>") + len("<body>")
    body_end = html_with_css.rfind("</body>")
    final_html = html_with_css[:body_start] + deck_markup + html_with_css[body_end:]

    # Save to both paths
    with open(OUT_INTERACTIVE_SRC, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    # In ROOT copy, adjust font css path
    root_html = final_html.replace("../../public/vendor/fonts.css", "public/vendor/fonts.css")
    with open(OUT_INTERACTIVE_ROOT, "w", encoding="utf-8") as f:
        f.write(root_html)

    print(f"[OK] Generated: {OUT_INTERACTIVE_SRC}")
    print(f"[OK] Generated: {OUT_INTERACTIVE_ROOT}")

def test_interactive_deck():
    print("[TEST] Menjalankan verifikasi Playwright untuk Interactive Deck...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        
        page.goto("file:///" + OUT_INTERACTIVE_SRC.replace("\\", "/"), wait_until="load")
        page.wait_for_timeout(800)

        # 1. Cek slide awal
        cur = page.evaluate("document.getElementById('current-slide').textContent")
        print(f"  [CHECK] Slide awal: {cur}")
        if cur != "01":
            raise AssertionError(f"Slide awal harus '01', tetapi '{cur}'")

        # 2. Cek navigasi ke slide 2 via tombol Next
        page.click("#btn-next")
        page.wait_for_timeout(300)
        cur = page.evaluate("document.getElementById('current-slide').textContent")
        print(f"  [CHECK] Slide setelah Next: {cur}")
        if cur != "02":
            raise AssertionError(f"Slide harus '02', tetapi '{cur}'")

        # 3. Cek navigasi via keyboard arrow
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        cur = page.evaluate("document.getElementById('current-slide').textContent")
        print(f"  [CHECK] Slide setelah ArrowRight: {cur}")
        if cur != "03":
            raise AssertionError(f"Slide harus '03', tetapi '{cur}'")

        # 4. Navigasi ke Slide 5 (KPI & Radar)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(200)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        cur = page.evaluate("document.getElementById('current-slide').textContent")
        print(f"  [CHECK] Slide ke-5 (Tab 1 Hero): {cur}")
        if cur != "05":
            raise AssertionError(f"Slide harus '05', tetapi '{cur}'")

        # 5. Cek animasi SVG dan numbers di Slide 5
        slide5_active = page.evaluate("document.querySelector('.slide.s-05').classList.contains('active')")
        print(f"  [CHECK] Slide 5 aktif: {slide5_active}")
        if not slide5_active:
            raise AssertionError("Slide 5 harus memiliki class 'active'")

        # Tunggu counter animation
        page.wait_for_timeout(1000)
        kpi_val = page.evaluate("document.querySelector('.slide.s-05 .kpi .v').textContent")
        print(f"  [CHECK] Nilai KPI di Slide 5 setelah animasi: {kpi_val}")
        if kpi_val != "77.9":
            raise AssertionError(f"KPI harus selesai di '77.9', tetapi '{kpi_val}'")

        browser.close()

        if errors:
            raise RuntimeError(f"Ada error di browser console: {errors}")
        print("[PASS] Interactive Animated Web Deck 100% tervalidasi dan siap digunakan!")

if __name__ == "__main__":
    build_interactive_deck()
    test_interactive_deck()

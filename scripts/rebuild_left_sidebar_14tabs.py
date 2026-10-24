# -*- coding: utf-8 -*-
"""
scripts/rebuild_left_sidebar_14tabs.py
Master Rebuilder for SIAK-KAPRODI Left Sidebar Enterprise Layout (14 Tabs)
Equipped with Gatekeeper PIN Auth Shield, Global Angkatan Selector, and Hotkeys.
"""

import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "public", "index.html")

def rebuild():
    print("[1] Reading current public/index.html...")
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # --- 1. HEADER WIDESCREEN & CONTROLS ---
    old_hdr_container = '<div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">'
    new_hdr_container = '<div class="w-full max-w-[1850px] mx-auto flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">'
    if old_hdr_container in html:
        html = html.replace(old_hdr_container, new_hdr_container, 1)
        print("  -> Header container widened to max-w-[1850px]")

    # Inject #sel-angkatan if missing
    if 'id="sel-angkatan"' not in html:
        target_mk = '<select id="course-selector"'
        sel_angkatan_html = """<select id="sel-angkatan" onchange="onKonteksBerubah('angkatan')" title="Filter Angkatan"
            class="touch-target bg-slate-900 text-cyan-300 text-xs font-bold rounded px-2 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-400 cursor-pointer">
            <option value="SEMUA">Semua Angkatan</option>
            <option value="2026">Angkatan 2026</option>
            <option value="2025">Angkatan 2025</option>
            <option value="2024">Angkatan 2024</option>
            <option value="SENIOR">🚨 Senior Kritis (Sem 9+)</option>
          </select>
          """
        if target_mk in html:
            html = html.replace(target_mk, sel_angkatan_html + target_mk, 1)
            print("  -> Injected #sel-angkatan into Context Bar")

    # Inject #btn-lock-session if missing
    if 'id="btn-lock-session"' not in html:
        asisten_badge_end = '<span>Asisten: <strong class="text-white" id="header-asisten">-</strong></span>\n        </div>'
        btn_lock_html = """<span>Asisten: <strong class="text-white" id="header-asisten">-</strong></span>
        </div>
        <button id="btn-lock-session" onclick="kunciSesiDashboard()" title="Kunci Dashboard (Gatekeeper)" class="px-2.5 py-1.5 rounded-lg bg-slate-800/90 hover:bg-rose-950/80 border border-slate-700 hover:border-rose-500/50 text-slate-300 hover:text-rose-400 text-xs font-semibold flex items-center gap-1.5 transition shadow-sm cursor-pointer">
          <i data-lucide="lock" class="w-3.5 h-3.5 text-amber-400"></i>
          <span>Kunci Sesi</span>
        </button>"""
        if asisten_badge_end in html:
            html = html.replace(asisten_badge_end, btn_lock_html, 1)
            print("  -> Injected #btn-lock-session into Header Governance Bar")
        else:
            # Fallback regex if whitespace differs
            pattern = re.compile(r'(<div[^>]*>\s*<i data-lucide="shield"[\s\S]*?id="header-asisten"[\s\S]*?</div>)')
            m = pattern.search(html)
            if m:
                lock_snippet = """\n        <button id="btn-lock-session" onclick="kunciSesiDashboard()" title="Kunci Dashboard (Gatekeeper)" class="px-2.5 py-1.5 rounded-lg bg-slate-800/90 hover:bg-rose-950/80 border border-slate-700 hover:border-rose-500/50 text-slate-300 hover:text-rose-400 text-xs font-semibold flex items-center gap-1.5 transition shadow-sm cursor-pointer">
          <i data-lucide="lock" class="w-3.5 h-3.5 text-amber-400"></i>
          <span>Kunci Sesi</span>
        </button>"""
                html = html[:m.end()] + lock_snippet + html[m.end():]
                print("  -> Injected #btn-lock-session via regex")

    # --- 2. REPLACE SUBHEADER WITH LEFT SIDEBAR ---
    sub_start = html.find('<!-- SUBHEADER / TAB NAVIGATION -->')
    assert sub_start != -1, "<!-- SUBHEADER / TAB NAVIGATION --> not found"
    main_start = html.find('<main id="app-main"', sub_start)
    assert main_start != -1, "<main id=\"app-main\" not found after subheader"
    main_open_end = html.find('>', main_start) + 1

    sidebar_and_main_start = """<!-- BODY SHELL: LEFT SIDEBAR + MAIN CONTENT VIEWPORT -->
  <div class="flex-1 flex w-full min-h-[calc(100vh-69px)] relative">
    
    <!-- LEFT SIDEBAR NAVIGATION (14 TABS IN 4 CATEGORIES) -->
    <aside id="sidebar-nav" class="w-64 xl:w-72 shrink-0 bg-[#070d1e] border-r border-slate-800/80 p-3.5 flex flex-col justify-between sticky top-[69px] h-[calc(100vh-69px)] overflow-y-auto scrollbar-none z-40">
      <nav id="nav-tabs" class="space-y-4">
        
        <!-- GROUP 1: AKADEMIK & MAHASISWA -->
        <div>
          <div class="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400/80 px-2.5 mb-1.5 flex items-center gap-1.5">
            <i data-lucide="graduation-cap" class="w-3.5 h-3.5 text-cyan-400"></i> Akademik &amp; Perkuliahan
          </div>
          <div class="space-y-1" id="nav-group-akademik">
            <button onclick="switchTab('kaprodi')" id="tab-btn-kaprodi" class="tab-btn active-tab touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all text-left">
              <i data-lucide="layout-dashboard" class="w-4 h-4 text-amber-400 shrink-0"></i>
              <span>1. Dashboard Kaprodi</span>
            </button>
            <button onclick="switchTab('wali')" id="tab-btn-wali" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="users" class="w-4 h-4 text-cyan-400 shrink-0"></i>
              <span>2. Portal Wali Murid</span>
            </button>
            <button onclick="switchTab('kurikulum')" id="tab-btn-kurikulum" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="book-marked" class="w-4 h-4 text-violet-400 shrink-0"></i>
              <span>3. Pohon Kurikulum &amp; RPS</span>
            </button>
            <button onclick="switchTab('dosen')" id="tab-btn-dosen" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="user-check" class="w-4 h-4 text-indigo-400 shrink-0"></i>
              <span>4. Audit Kinerja Dosen</span>
            </button>
            <button onclick="switchTab('rekap')" id="tab-btn-rekap" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="clipboard-list" class="w-4 h-4 text-fuchsia-400 shrink-0"></i>
              <span>5. Evaluasi &amp; Rekap Silabus</span>
            </button>
            <button onclick="switchTab('portofolio')" id="tab-btn-portofolio" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="award" class="w-4 h-4 text-lime-400 shrink-0"></i>
              <span>6. Portofolio 4 Lapis</span>
            </button>
          </div>
        </div>

        <!-- GROUP 2: EKSEKUTIF & ANALITIK -->
        <div>
          <div class="text-[10px] font-mono font-bold uppercase tracking-wider text-purple-400/80 px-2.5 mb-1.5 flex items-center gap-1.5">
            <i data-lucide="pie-chart" class="w-3.5 h-3.5 text-purple-400"></i> Eksekutif &amp; Analitik
          </div>
          <div class="space-y-1" id="nav-group-eksekutif">
            <button onclick="switchTab('yayasan')" id="tab-btn-yayasan" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="landmark" class="w-4 h-4 text-purple-400 shrink-0"></i>
              <span>7. Cockpit Yayasan &amp; Investor</span>
            </button>
            <button onclick="switchTab('pertumbuhan')" id="tab-btn-pertumbuhan" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="trending-up" class="w-4 h-4 text-emerald-400 shrink-0"></i>
              <span>8. Pertumbuhan PMB &amp; 30 MK</span>
            </button>
            <button onclick="switchTab('analytics')" id="tab-btn-analytics" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="bar-chart-3" class="w-4 h-4 text-cyan-400 shrink-0"></i>
              <span>9. Observatorium Grafik</span>
            </button>
          </div>
        </div>

        <!-- GROUP 3: KOMUNIKASI & PUBLIKASI -->
        <div>
          <div class="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400/80 px-2.5 mb-1.5 flex items-center gap-1.5">
            <i data-lucide="share-2" class="w-3.5 h-3.5 text-emerald-400"></i> Komunikasi &amp; Publikasi
          </div>
          <div class="space-y-1" id="nav-group-komunikasi">
            <button onclick="switchTab('marketing')" id="tab-btn-marketing" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="megaphone" class="w-4 h-4 text-emerald-400 shrink-0"></i>
              <span>10. Showcase Marketing &amp; Sosmed</span>
            </button>
            <button onclick="switchTab('whatsapp')" id="tab-btn-whatsapp" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="message-square" class="w-4 h-4 text-green-400 shrink-0"></i>
              <span>11. WhatsApp Broadcast Simulator</span>
            </button>
          </div>
        </div>

        <!-- GROUP 4: SISTEM & MESIN DATA -->
        <div>
          <div class="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400/80 px-2.5 mb-1.5 flex items-center gap-1.5">
            <i data-lucide="cpu" class="w-3.5 h-3.5 text-amber-400"></i> Sistem &amp; Mesin Data
          </div>
          <div class="space-y-1" id="nav-group-sistem">
            <button onclick="switchTab('pengaturan')" id="tab-btn-pengaturan" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="settings" class="w-4 h-4 text-slate-400 shrink-0"></i>
              <span>12. Pengaturan Identitas</span>
            </button>
            <button onclick="switchTab('info')" id="tab-btn-info" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="info" class="w-4 h-4 text-sky-400 shrink-0"></i>
              <span>13. Panduan &amp; SOP Kaprodi</span>
            </button>
            <button onclick="switchTab('engine')" id="tab-btn-engine" class="tab-btn touch-target w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all text-left">
              <i data-lucide="cpu" class="w-4 h-4 text-amber-400 shrink-0"></i>
              <span>14. Engine Diagnostics</span>
            </button>
          </div>
        </div>

      </nav>

      <!-- SIDEBAR FOOTER: QUICK ARCHETYPES & SYSTEM STATUS -->
      <div class="pt-3 border-t border-slate-800/80 space-y-2.5">
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-2.5">
          <div class="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <i data-lucide="zap" class="w-3 h-3 text-amber-400"></i> Demo Cepat Mahasiswa
          </div>
          <div class="grid grid-cols-1 gap-1.5 text-xs">
            <button onclick="selectQuickStudent('2510015410010')" class="touch-target px-2.5 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 rounded-lg border border-amber-500/30 font-medium transition text-left flex items-center justify-between">
              <span>🌟 Yazid</span>
              <span class="text-[10px] font-mono opacity-70">Top Star</span>
            </button>
            <button onclick="selectQuickStudent('2510015410011')" class="touch-target px-2.5 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 rounded-lg border border-rose-500/30 font-medium transition text-left flex items-center justify-between">
              <span>⚠️ Rozi</span>
              <span class="text-[10px] font-mono opacity-70">At-Risk</span>
            </button>
            <button onclick="selectQuickStudent('2510015410001')" class="touch-target px-2.5 py-1.5 bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 rounded-lg border border-sky-500/30 font-medium transition text-left flex items-center justify-between">
              <span>✨ Alsa</span>
              <span class="text-[10px] font-mono opacity-70">Konsisten</span>
            </button>
          </div>
        </div>

        <!-- HOTKEY SHORTCUTS (UI-HK-01 - 04) -->
        <div class="grid grid-cols-2 gap-1 text-[11px]">
          <button id="btn-quick-at-risk" onclick="bukaModalAtRisk()" class="touch-target px-2 py-1.5 bg-rose-950/40 hover:bg-rose-900/50 border border-rose-800/40 text-rose-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Buka modal 3 mhs at-risk">
            <i data-lucide="alert-triangle" class="w-3 h-3 text-rose-400 shrink-0"></i>
            <span>At-Risk</span>
          </button>
          <button id="btn-quick-gradebook" onclick="downloadKaprodiGradebook()" class="touch-target px-2 py-1.5 bg-amber-950/40 hover:bg-amber-900/50 border border-amber-800/40 text-amber-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Unduh PDF Gradebook Master">
            <i data-lucide="file-text" class="w-3 h-3 text-amber-400 shrink-0"></i>
            <span>Gradebook</span>
          </button>
        </div>

        <div class="px-1 flex items-center justify-between text-[11px] font-mono text-slate-500">
          <span class="flex items-center gap-1.5 text-emerald-400">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> PORT 40404
          </span>
          <span>v2.6 Enterprise</span>
        </div>
      </div>
    </aside>

    <!-- MAIN VIEWPORT CONTAINER (WIDE WORKSPACE) -->
    <main id="app-main" class="flex-1 min-w-0 px-4 lg:px-8 py-6 space-y-8 safe-bottom overflow-x-hidden">"""

    html = html[:sub_start] + sidebar_and_main_start + html[main_open_end:]
    print("  -> Subheader successfully replaced by Left Sidebar & main viewport")

    # --- 3. WRAP MAIN CONTENT & CLOSE BODY SHELL ---
    main_close = html.find('</main>')
    assert main_close != -1, "</main> not found"

    # --- 4. INJECT MISSING SECTIONS BEFORE </main> ---
    # We need: section-dosen, section-yayasan, section-pertumbuhan, section-analytics
    with open(os.path.join(BASE_DIR, "scratch", "build_opsi_a_sidebar.py"), "r", encoding="utf-8") as f:
        src_opsi_a = f.read()

    # Read section_pertumbuhan_html directly from scratch file to avoid AST import detection
    with open(os.path.join(BASE_DIR, "scratch", "preview_section_html.py"), "r", encoding="utf-8") as f_prev:
        prev_code = f_prev.read()
    m_p = re.search(r"section_pertumbuhan_html\s*=\s*'''([\s\S]*?)'''", prev_code)
    section_pertumbuhan_html = m_p.group(1) if m_p else ""

    def extract_sec(sec_id):
        m = re.search(rf'(<!--\s*={5,}[\s\S]*?<section\s+id="{sec_id}"[\s\S]*?</section>)', src_opsi_a)
        if not m:
            m = re.search(rf'(<section\s+id="{sec_id}"[\s\S]*?</section>)', src_opsi_a)
        assert m, f"Section {sec_id} not found in build_opsi_a_sidebar.py"
        return m.group(1)

    sec_dosen = extract_sec("section-dosen")
    sec_yayasan = extract_sec("section-yayasan")
    sec_analytics = extract_sec("section-analytics")

    injections = []
    if 'id="section-dosen"' not in html:
        injections.append(sec_dosen)
        print("  -> Prepared section-dosen injection")
    if 'id="section-yayasan"' not in html:
        injections.append(sec_yayasan)
        print("  -> Prepared section-yayasan injection")
    if 'id="section-pertumbuhan"' not in html:
        injections.append(section_pertumbuhan_html)
        print("  -> Prepared section-pertumbuhan injection")
    if 'id="section-analytics"' not in html:
        injections.append(sec_analytics)
        print("  -> Prepared section-analytics injection")

    if injections:
        joined_injections = "\n\n" + "\n\n".join(injections) + "\n"
        html = html[:main_close] + joined_injections + html[main_close:]
        # Update main_close index
        main_close = html.find('</main>')

    # Now close the wrapper right after </main>
    wrapper_close = "\n  </div> <!-- END BODY SHELL: LEFT SIDEBAR + MAIN CONTENT -->"
    insert_pos = main_close + len('</main>')
    html = html[:insert_pos] + wrapper_close + html[insert_pos:]
    print("  -> Body shell wrapper closed after </main>")

    # --- 5. INJECT MODALS (ASISTENSI, AT-RISK, GATEKEEPER) BEFORE </body> ---
    body_close = html.find('</body>')
    assert body_close != -1, "</body> not found"

    modals_to_inject = []

    # Check modals snippet (#modal-asistensi-mk, #modal-at-risk)
    with open(os.path.join(BASE_DIR, "scratch", "modals_snippet.html"), "r", encoding="utf-8") as f:
        modals_snippet = f.read()

    if 'id="modal-asistensi-mk"' not in html and 'id="modal-at-risk"' not in html:
        modals_to_inject.append(modals_snippet)
        print("  -> Prepared modal-asistensi-mk & modal-at-risk injection")

    # Check Gatekeeper Modal
    with open(os.path.join(BASE_DIR, "scratch", "gatekeeper_modal_snippet.html"), "r", encoding="utf-8") as f:
        gatekeeper_snippet = f.read()

    if 'id="gatekeeper-modal"' not in html:
        modals_to_inject.append(gatekeeper_snippet)
        print("  -> Prepared gatekeeper-modal injection")

    if modals_to_inject:
        script_ctrl = html.find('<!-- Script Controller -->')
        if script_ctrl != -1:
            html = html[:script_ctrl] + "\n" + "\n\n".join(modals_to_inject) + "\n\n  " + html[script_ctrl:]
        else:
            html = html[:body_close] + "\n" + "\n\n".join(modals_to_inject) + "\n" + html[body_close:]
        print("  -> Injected root modals before scripts")

    # --- 6. WRITE BACK ---
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n[SUCCESS] public/index.html fully rebuilt with Left Sidebar 14-Tab & Gatekeeper Auth Shield!")

if __name__ == "__main__":
    rebuild()

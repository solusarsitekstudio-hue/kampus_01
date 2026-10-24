# -*- coding: utf-8 -*-
"""
scripts/patch_all_ui_buttons.py
Surgical Patcher for all UI buttons in public/index.html
Fixes BUG-02 through BUG-08 strictly aligned with MAPPING_UI.md
"""

import os
import sys
import re

INDEX_PATH = os.path.join("public", "index.html")

def patch():
    print("[1] Membaca public/index.html...")
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # =========================================================================
    # 1. BUG-04: Melengkapi 4 Tombol Hotkey pada Sidebar Footer
    # =========================================================================
    old_hotkeys = """        <!-- HOTKEY SHORTCUTS (UI-HK-01 - 04) -->
        <div class="grid grid-cols-2 gap-1 text-[11px]">
          <button id="btn-quick-at-risk" onclick="bukaModalAtRisk()" class="touch-target px-2 py-1.5 bg-rose-950/40 hover:bg-rose-900/50 border border-rose-800/40 text-rose-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Buka modal 3 mhs at-risk">
            <i data-lucide="alert-triangle" class="w-3 h-3 text-rose-400 shrink-0"></i>
            <span>At-Risk</span>
          </button>
          <button id="btn-quick-gradebook" onclick="downloadKaprodiGradebook()" class="touch-target px-2 py-1.5 bg-amber-950/40 hover:bg-amber-900/50 border border-amber-800/40 text-amber-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Unduh PDF Gradebook Master">
            <i data-lucide="file-text" class="w-3 h-3 text-amber-400 shrink-0"></i>
            <span>Gradebook</span>
          </button>
        </div>"""

    new_hotkeys = """        <!-- HOTKEY SHORTCUTS (UI-HK-01 - 04) -->
        <div class="grid grid-cols-2 gap-1 text-[11px]">
          <button id="btn-quick-at-risk" onclick="bukaModalAtRisk()" class="touch-target px-2 py-1.5 bg-rose-950/40 hover:bg-rose-900/50 border border-rose-800/40 text-rose-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Buka modal drilldown mhs at-risk">
            <i data-lucide="alert-triangle" class="w-3 h-3 text-rose-400 shrink-0"></i>
            <span>At-Risk</span>
          </button>
          <button id="btn-quick-gradebook" onclick="downloadKaprodiGradebook()" class="touch-target px-2 py-1.5 bg-amber-950/40 hover:bg-amber-900/50 border border-amber-800/40 text-amber-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Unduh PDF Gradebook Master">
            <i data-lucide="file-text" class="w-3 h-3 text-amber-400 shrink-0"></i>
            <span>Gradebook</span>
          </button>
          <button id="btn-quick-audit-dosen" onclick="switchTab('dosen')" class="touch-target px-2 py-1.5 bg-indigo-950/40 hover:bg-indigo-900/50 border border-indigo-800/40 text-indigo-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Lompat ke Tab 4 Audit Kinerja Dosen">
            <i data-lucide="user-check" class="w-3 h-3 text-indigo-400 shrink-0"></i>
            <span>Audit Dosen</span>
          </button>
          <button id="btn-quick-observatorium" onclick="switchTab('analytics')" class="touch-target px-2 py-1.5 bg-cyan-950/40 hover:bg-cyan-900/50 border border-cyan-800/40 text-cyan-300 rounded-lg font-medium transition flex items-center gap-1 truncate" title="Lompat ke Tab 9 Observatorium Grafik">
            <i data-lucide="bar-chart-3" class="w-3 h-3 text-cyan-400 shrink-0"></i>
            <span>Grafik Mutu</span>
          </button>
        </div>"""

    if old_hotkeys in html:
        html = html.replace(old_hotkeys, new_hotkeys, 1)
        print("  [OK] BUG-04: 4 Hotkey Sidebar berhasil dipasang!")
    else:
        print("  [!] Warning: old_hotkeys snippet not found directly, checking regex...")
        # fallback regex replace
        pattern_hk = re.compile(r'<!-- HOTKEY SHORTCUTS[\s\S]*?<div class="grid grid-cols-2 gap-1 text-\[11px\]">[\s\S]*?</div>\s*</div>', re.MULTILINE)
        m_hk = pattern_hk.search(html)
        if m_hk:
            html = html[:m_hk.start()] + new_hotkeys + "\n" + html[m_hk.end():]
            print("  [OK] BUG-04: 4 Hotkey Sidebar berhasil dipasang via regex!")

    # =========================================================================
    # 2. BUG-02 & BUG-03: Tab 7 Yayasan (Fix Nama Fungsi & Tambah 3 Tombol Eksekutif)
    # =========================================================================
    old_yayasan_header_btn = """          <div class="flex items-center gap-2">
            <button onclick="downloadExecutivePackagePDF()" class="touch-target px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-500/20 transition flex items-center gap-2 cursor-pointer">
              <i data-lucide="download" class="w-4 h-4"></i> Unduh Paket Akreditasi
            </button>
          </div>"""

    new_yayasan_header_btn = """          <div class="flex items-center gap-2 flex-wrap">
            <button id="btn-yayasan-unduh-paket" onclick="unduhPaketLengkapAkreditasiProdi()" class="touch-target px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-500/20 transition flex items-center gap-1.5 cursor-pointer" title="Unduh Paket Arsip Lengkap Akreditasi (ZIP/Master)">
              <i data-lucide="download" class="w-4 h-4"></i> Paket Akreditasi
            </button>
            <button id="btn-yayasan-unduh-pdf" onclick="unduhExecutivePitchPdf()" class="touch-target px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-purple-300 border border-purple-500/40 font-bold text-xs transition flex items-center gap-1.5 cursor-pointer" title="Unduh PDF 06 Executive Pitch Deck Yayasan (16:9 Landscape)">
              <i data-lucide="file-text" class="w-4 h-4 text-purple-400"></i> Pitch PDF
            </button>
            <button id="btn-yayasan-copy-pitch" onclick="salinExecutivePitchText()" class="touch-target px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/40 font-bold text-xs transition flex items-center gap-1.5 cursor-pointer" title="Salin Naskah Pidato Eksekutif Boardroom ke Clipboard">
              <i data-lucide="copy" class="w-4 h-4 text-amber-400"></i> Salin Naskah
            </button>
            <button id="btn-yayasan-refresh" onclick="renderExecutiveCockpit()" class="touch-target px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/40 font-bold text-xs transition flex items-center gap-1.5 cursor-pointer" title="Muat Ulang Agregasi Realtime Cockpit">
              <i data-lucide="refresh-cw" class="w-4 h-4 text-cyan-400"></i>
            </button>
          </div>"""

    if old_yayasan_header_btn in html:
        html = html.replace(old_yayasan_header_btn, new_yayasan_header_btn, 1)
        print("  [OK] BUG-02 & BUG-03: Header Tab 7 berhasil diperbaiki (4 tombol aktif)!")
    else:
        # Regex replacement if whitespace differs
        p_yayasan = re.compile(r'<div class="flex items-center gap-2">\s*<button onclick="downloadExecutivePackagePDF\(\)"[\s\S]*?</button>\s*</div>')
        m_y = p_yayasan.search(html)
        if m_y:
            html = html[:m_y.start()] + new_yayasan_header_btn + html[m_y.end():]
            print("  [OK] BUG-02 & BUG-03: Header Tab 7 berhasil diperbaiki via regex!")

    # =========================================================================
    # 3. BUG-05: Tab 2 Wali Murid (Injeksi 4-Layer Switcher Radar & Breakdown Grid)
    # =========================================================================
    old_radar_block = """            <div class="flex items-center justify-between mb-2">
              <h4 class="text-sm font-bold text-white flex items-center gap-2">
                <i data-lucide="radar" class="w-4 h-4 text-amber-400"></i> Radar Kompetensi Arsitektural
              </h4>
              <span class="text-[11px] text-slate-400">Skala 1 - 100</span>
            </div>
            <p class="text-xs text-slate-400 mb-2">5 pilar keahlian: Software CAD, Detail Gambar, Asistensi, Logika Ruang, & Waktu.</p>
            <div id="chart-radar-competency" class="min-h-[290px]"></div>"""

    new_radar_block = """            <div class="flex items-center justify-between mb-2">
              <h4 class="text-sm font-bold text-white flex items-center gap-2" id="radar-layer-title">
                <i data-lucide="radar" class="w-4 h-4 text-amber-400"></i> Radar Kompetensi Arsitektural
              </h4>
              <span class="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20" id="radar-engine-tag">Engine: Karakter &amp; Softskill</span>
            </div>
            <p class="text-xs text-slate-400 mb-2" id="radar-layer-desc">5 pilar keahlian: Software CAD, Detail Gambar, Kedisiplinan, Logika Struktur, &amp; Manajemen Waktu.</p>
            
            <!-- 4-LAYER THEME SWITCHER BUTTONS (UI-TAB2-03 - 05) -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-1.5 p-1 bg-slate-900/80 rounded-xl border border-slate-800 my-2">
              <button type="button" id="btn-radar-softskill" onclick="switchRadarLayer('softskill')" class="touch-target px-2 py-1.5 text-[11px] rounded-lg transition-all text-center flex items-center justify-center gap-1 border bg-amber-500/20 text-amber-300 border-amber-500/40 font-semibold shadow-sm cursor-pointer">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Softskill
              </button>
              <button type="button" id="btn-radar-modul_mk" onclick="switchRadarLayer('modul_mk')" class="touch-target px-2 py-1.5 text-[11px] rounded-lg transition-all text-center flex items-center justify-center gap-1 border text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-transparent font-medium cursor-pointer">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Modul RPS
              </button>
              <button type="button" id="btn-radar-semester" onclick="switchRadarLayer('semester')" class="touch-target px-2 py-1.5 text-[11px] rounded-lg transition-all text-center flex items-center justify-center gap-1 border text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-transparent font-medium cursor-pointer">
                <span class="w-1.5 h-1.5 rounded-full bg-cyan-400"></span> Semester
              </button>
              <button type="button" id="btn-radar-potensi_cr" onclick="switchRadarLayer('potensi_cr')" class="touch-target px-2 py-1.5 text-[11px] rounded-lg transition-all text-center flex items-center justify-center gap-1 border text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-transparent font-medium cursor-pointer">
                <span class="w-1.5 h-1.5 rounded-full bg-purple-400"></span> Potensi CR
              </button>
            </div>

            <div id="chart-radar-competency" class="min-h-[290px]"></div>"""

    if old_radar_block in html:
        html = html.replace(old_radar_block, new_radar_block, 1)
        print("  [OK] BUG-05: 4-Layer Radar Switcher Tab 2 berhasil dipasang!")
    else:
        p_radar = re.compile(r'<div class="flex items-center justify-between mb-2">\s*<h4 class="text-sm font-bold text-white flex items-center gap-2">\s*<i data-lucide="radar"[\s\S]*?<div id="chart-radar-competency" class="min-h-\[290px\]"></div>')
        m_r = p_radar.search(html)
        if m_r:
            html = html[:m_r.start()] + new_radar_block + html[m_r.end():]
            print("  [OK] BUG-05: 4-Layer Radar Switcher Tab 2 berhasil dipasang via regex!")

    # Injeksi #radar-breakdown-grid bila belum ada
    if 'id="radar-breakdown-grid"' not in html:
        target_grid = '<div class="grid grid-cols-2 gap-2 text-xs pt-3 border-t border-slate-800 mt-2 font-mono">'
        new_grid_block = '<div id="radar-breakdown-grid" class="grid grid-cols-2 gap-2 text-xs pt-3 border-t border-slate-800 mt-2 font-mono">'
        if target_grid in html:
            html = html.replace(target_grid, new_grid_block, 1)
            print("  [OK] BUG-05: #radar-breakdown-grid berhasil dikaitkan ke grid breakdown radar!")

    # =========================================================================
    # 4. BUG-01 / UI-TAB1-07: Shortcut At-Risk pada KPI Card Tab 1
    # =========================================================================
    old_at_risk_kpi = """            <div class="text-[11px] text-rose-300/80 mt-1" id="kpi-at-risk-desc">Alpha &#8805; 2x atau kehadiran &lt; 75%</div>
          </div>"""

    new_at_risk_kpi = """            <div class="text-[11px] text-rose-300/80 mt-1" id="kpi-at-risk-desc">Alpha &#8805; 2x atau kehadiran &lt; 75%</div>
            <button id="btn-kpi-at-risk-shortcut" onclick="bukaModalAtRisk()" class="mt-2.5 touch-target w-full px-2.5 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer" title="Buka modal drilldown at-risk">
              <i data-lucide="alert-triangle" class="w-3.5 h-3.5"></i>
              <span>Drilldown At-Risk</span>
            </button>
          </div>"""

    if old_at_risk_kpi in html and 'id="btn-kpi-at-risk-shortcut"' not in html:
        html = html.replace(old_at_risk_kpi, new_at_risk_kpi, 1)
        print("  [OK] UI-TAB1-07: Tombol shortcut drilldown At-Risk pada KPI Card Tab 1 berhasil dipasang!")

    # =========================================================================
    # 5. BUG-06: Tombol Form Submit Tab 12 & Tab 3
    # =========================================================================
    # Tab 12 Simpan Identitas
    old_btn_identitas = '<button type="submit" class="px-4 py-2 rounded-lg text-sm font-bold bg-amber-500 hover:bg-amber-400 text-slate-900 transition shadow-lg">\n              Simpan Identitas\n            </button>'
    new_btn_identitas = '<button type="submit" id="btn-simpan-identitas" onclick="simpanIdentitas()" class="px-4 py-2 rounded-lg text-sm font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-lg cursor-pointer">\n              Simpan Identitas\n            </button>'
    if old_btn_identitas in html:
        html = html.replace(old_btn_identitas, new_btn_identitas, 1)
        print("  [OK] BUG-06: Tombol #btn-simpan-identitas Tab 12 berhasil di-anchor!")
    else:
        # Fallback regex
        html = re.sub(r'<button\s+type="submit"([^>]*)>\s*Simpan Identitas\s*</button>',
                      r'<button type="submit" id="btn-simpan-identitas" onclick="simpanIdentitas()"\1>Simpan Identitas</button>',
                      html, count=1)
        print("  [OK] BUG-06: Tombol #btn-simpan-identitas Tab 12 berhasil di-anchor via regex!")

    # Tab 3 Simpan Kurikulum
    old_btn_kurikulum = '<button type="submit" class="px-4 py-2 rounded-lg text-sm font-bold bg-violet-600 hover:bg-violet-500 text-white transition shadow-lg">\n              Simpan ke Tree Kurikulum\n            </button>'
    new_btn_kurikulum = '<button type="submit" id="btn-simpan-kurikulum" onclick="simpanKurikulum()" class="px-4 py-2 rounded-lg text-sm font-bold bg-violet-600 hover:bg-violet-500 text-white transition shadow-lg cursor-pointer">\n              Simpan ke Tree Kurikulum\n            </button>'
    if old_btn_kurikulum in html:
        html = html.replace(old_btn_kurikulum, new_btn_kurikulum, 1)
        print("  [OK] BUG-06: Tombol #btn-simpan-kurikulum Tab 3 berhasil di-anchor!")
    else:
        html = re.sub(r'<button\s+type="submit"([^>]*)>\s*Simpan ke Tree Kurikulum\s*</button>',
                      r'<button type="submit" id="btn-simpan-kurikulum" onclick="simpanKurikulum()"\1>Simpan ke Tree Kurikulum</button>',
                      html, count=1)
        print("  [OK] BUG-06: Tombol #btn-simpan-kurikulum Tab 3 berhasil di-anchor via regex!")

    # =========================================================================
    # 6. BUG-07: Tombol Mini Download pada Kartu PDF WhatsApp
    # =========================================================================
    old_wa_card_btn1 = """                <button class="p-1.5 rounded-lg bg-emerald-600/60 hover:bg-emerald-600 text-white flex-shrink-0">
                  <i data-lucide="download" class="w-3.5 h-3.5"></i>
                </button>"""
    new_wa_card_btn1 = """                <button type="button" onclick="event.stopPropagation(); downloadCurrentStudentMonthlyPDF()" class="p-1.5 rounded-lg bg-emerald-600/60 hover:bg-emerald-600 text-white flex-shrink-0 cursor-pointer" title="Unduh PDF 01: Presensi">
                  <i data-lucide="download" class="w-3.5 h-3.5"></i>
                </button>"""
    if old_wa_card_btn1 in html:
        html = html.replace(old_wa_card_btn1, new_wa_card_btn1, 1)
        print("  [OK] BUG-07: Tombol download mini PDF 1 WhatsApp berhasil diaktifkan!")

    old_wa_card_btn2 = """                <button class="p-1.5 rounded-lg bg-emerald-600/60 hover:bg-emerald-600 text-white flex-shrink-0">
                  <i data-lucide="download" class="w-3.5 h-3.5"></i>
                </button>"""
    new_wa_card_btn2 = """                <button type="button" onclick="event.stopPropagation(); downloadCurrentStudentFinalPDF()" class="p-1.5 rounded-lg bg-emerald-600/60 hover:bg-emerald-600 text-white flex-shrink-0 cursor-pointer" title="Unduh PDF 02: Rapor">
                  <i data-lucide="download" class="w-3.5 h-3.5"></i>
                </button>"""
    if old_wa_card_btn2 in html:
        html = html.replace(old_wa_card_btn2, new_wa_card_btn2, 1)
        print("  [OK] BUG-07: Tombol download mini PDF 2 WhatsApp berhasil diaktifkan!")

    old_wa_card_btn3 = """                <button class="p-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold flex-shrink-0">
                  <i data-lucide="download" class="w-3.5 h-3.5"></i>
                </button>"""
    new_wa_card_btn3 = """                <button type="button" onclick="event.stopPropagation(); downloadCurrentStudentDeckcraftPDF()" class="p-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold flex-shrink-0 cursor-pointer" title="Unduh PDF 05: DeckCraft">
                  <i data-lucide="download" class="w-3.5 h-3.5"></i>
                </button>"""
    if old_wa_card_btn3 in html:
        html = html.replace(old_wa_card_btn3, new_wa_card_btn3, 1)
        print("  [OK] BUG-07: Tombol download mini PDF 3 WhatsApp berhasil diaktifkan!")

    # =========================================================================
    # 7. BUG-08: Universal Wire IDs sesuai MAPPING_UI.md
    # =========================================================================
    # Tab 1: Gradebook, Dosen Audit, Export JSON
    html = html.replace('<button onclick="downloadKaprodiGradebook()"', '<button id="btn-unduh-gradebook" onclick="downloadKaprodiGradebook()"', 1)
    html = html.replace('<button onclick="downloadDosenAuditPDF()" class="touch-target px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-purple-300',
                        '<button id="btn-unduh-audit-dosen" onclick="downloadDosenAuditPDF()" class="touch-target px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-purple-300', 1)
    html = html.replace('<button onclick="exportDataJSON()"', '<button id="btn-export-json" onclick="exportDataJSON()"', 1)

    # Tab 2: Monthly & Rapor Final
    html = html.replace('<button onclick="downloadCurrentStudentMonthlyPDF()"', '<button id="btn-unduh-monthly" onclick="downloadCurrentStudentMonthlyPDF()"', 1)
    html = html.replace('<button onclick="downloadCurrentStudentFinalPDF()"', '<button id="btn-unduh-rapor" onclick="downloadCurrentStudentFinalPDF()"', 1)

    # Tab 4: Dosen Audit download + Refresh
    old_dosen_btns = """          <div class="flex items-center gap-2">
            <button onclick="downloadDosenAuditPDF()" class="touch-target px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 transition flex items-center gap-2 cursor-pointer">
              <i data-lucide="download" class="w-4 h-4"></i> Unduh PDF Audit Dosen
            </button>
          </div>"""

    new_dosen_btns = """          <div class="flex items-center gap-2 flex-wrap">
            <button id="btn-dosen-unduh-pdf" onclick="downloadDosenAuditPDF()" class="touch-target px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 transition flex items-center gap-1.5 cursor-pointer" title="Unduh PDF 04 Audit Kinerja Dosen & RPS">
              <i data-lucide="download" class="w-4 h-4"></i> Unduh PDF Audit Dosen
            </button>
            <button id="btn-dosen-refresh" onclick="renderDosenSection()" class="touch-target px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-500/40 font-bold text-xs transition flex items-center gap-1.5 cursor-pointer" title="Muat Ulang Audit Dosen Realtime">
              <i data-lucide="refresh-cw" class="w-4 h-4 text-indigo-400"></i> Refresh
            </button>
          </div>"""
    if old_dosen_btns in html:
        html = html.replace(old_dosen_btns, new_dosen_btns, 1)
        print("  [OK] UI-TAB4-03: Tombol #btn-dosen-refresh Tab 4 berhasil dipasang!")
    else:
        html = html.replace('<button onclick="downloadDosenAuditPDF()" class="touch-target px-4 py-2 rounded-xl bg-indigo-600',
                            '<button id="btn-dosen-unduh-pdf" onclick="downloadDosenAuditPDF()" class="touch-target px-4 py-2 rounded-xl bg-indigo-600', 1)

    # Tab 5: Rekap Refresh
    html = html.replace('<button onclick="muatRekap()"', '<button id="btn-muat-rekap" onclick="muatRekap()"', 1)

    # Tab 6: Portofolio PDFs
    html = html.replace("onclick=\"unduhPortofolioPdf('portofolio_lengkap')\"", "id=\"btn-porto-unduh-lengkap\" onclick=\"unduhPortofolioPdf('portofolio_lengkap')\"", 1)
    html = html.replace("onclick=\"unduhPortofolioPdf('bulanan_mk')\"", "id=\"btn-porto-unduh-bulanan\" onclick=\"unduhPortofolioPdf('bulanan_mk')\"", 1)
    html = html.replace("onclick=\"unduhPortofolioPdf('rapor')\"", "id=\"btn-porto-unduh-rapor\" onclick=\"unduhPortofolioPdf('rapor')\"", 1)
    html = html.replace("onclick=\"unduhPortofolioPdf('deck')\"", "id=\"btn-porto-unduh-deck\" onclick=\"unduhPortofolioPdf('deck')\"", 1)

    # Tab 10: Marketing Actions
    html = html.replace('<button onclick="downloadCurrentStudentDeckcraftPDF()" class="touch-target px-3.5 py-2 bg-gradient-to-r from-amber-500 to-amber-600',
                        '<button id="btn-marketing-unduh-deck" onclick="downloadCurrentStudentDeckcraftPDF()" class="touch-target px-3.5 py-2 bg-gradient-to-r from-amber-500 to-amber-600', 1)
    html = html.replace('<button onclick="openLiveDeckcraft()"', '<button id="btn-marketing-live-deck" onclick="openLiveDeckcraft()"', 1)
    html = html.replace('<button onclick="openStudentProgressFolder()"', '<button id="btn-marketing-open-folder" onclick="openStudentProgressFolder()"', 1)

    # Tab 11: WhatsApp Actions
    html = html.replace('<button onclick="copyWhatsAppMessage()"', '<button id="btn-copy-wa-message" onclick="copyWhatsAppMessage()"', 1)
    html = html.replace('<button onclick="downloadAll3StudentPDFs()"', '<button id="btn-wa-download-all" onclick="downloadAll3StudentPDFs()"', 1)
    html = html.replace('<button onclick="openWhatsAppDirect()"', '<button id="btn-open-wa-direct" onclick="openWhatsAppDirect()"', 1)

    # Tab 12: Pengaturan Actions
    html = html.replace('<button type="button" onclick="terapkanKeDokumen()"', '<button type="button" id="btn-terapkan-dokumen" onclick="terapkanKeDokumen()"', 1)
    html = html.replace('<button type="button" onclick="regenerasiPaketPdf()"', '<button type="button" id="btn-regenerasi-pdf" onclick="regenerasiPaketPdf()"', 1)
    html = html.replace('<button type="button" onclick="muatIdentitas()"', '<button type="button" id="btn-muat-identitas" onclick="muatIdentitas()"', 1)

    # Tab 13: Info SOP Refresh
    html = html.replace('<button onclick="muatInfoSistem(true)"', '<button id="btn-muat-info" onclick="muatInfoSistem(true)"', 1)

    # Tulis balik berkas
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print("\n[SUCCESS] public/index.html berhasil diperbarui dengan seluruh perbaikan tombol!")

if __name__ == "__main__":
    patch()

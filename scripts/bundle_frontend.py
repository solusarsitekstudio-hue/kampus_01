"""scripts/bundle_frontend.py - MODULAR FRONTEND MANAGER & BUNDLER
SIAK-KAPRODI / AL-ANALISIS (Architecture Intelligence)

Memecah monolith public/app.js menjadi modul-modul independen di public/js/
dan menyatukannya kembali secara teratur ke public/app.js (Zero-Regression & Zero-NPM).
"""

import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_HERE)
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
JS_DIR = os.path.join(PUBLIC_DIR, "js")
APP_JS = os.path.join(PUBLIC_DIR, "app.js")

MODULES_SPEC = [
    ("01_core.js", 1, 1913, "Core State, Gatekeeper PIN, Utils & Navigation Controller"),
    ("02_tab_portofolio_ai.js", 1914, 4753, "Tab Portofolio 4-Lapis, Radar 5 Dimensi & Karier AI"),
    ("03_tab_presensi_nilai.js", 4754, 9059, "Tab Monitoring Presensi & Evaluasi Nilai Studio"),
    ("04_tab_kurikulum_rps.js", 9060, 14470, "Tab Kurikulum Bertingkat, Tree 30 MK & RPS Editor"),
    ("05_tab_deckcraft.js", 14471, 16313, "DeckCraft 5-Slide Presenter, Quad-Radar & WhatsApp Kit"),
    ("06_tab_engine_audit.js", 16314, 19009, "Tab Engine: Audit Berkas Masukan & Status Keluaran"),
    ("07_tab_growth_yayasan.js", 19010, 22894, "Tab Pertumbuhan PMB, Matriks 30 MK & Modal Asistensi"),
    ("08_mobile_drawer.js", 22895, 99999, "Mobile Drawer & Context Filter Toggle"),
]

def clean_newlines(text: str) -> str:
    """Mengompresi 3+ baris kosong berturut-turut menjadi 1 baris kosong."""
    return re.sub(r'\n{3,}', '\n\n', text)

def split_modules():
    """Mengekstrak app.js menjadi modul-modul di public/js/"""
    os.makedirs(JS_DIR, exist_ok=True)
    with open(APP_JS, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"[SPLIT] Membaca {APP_JS} ({total_lines} baris)...")

    for fname, start_l, end_l, desc in MODULES_SPEC:
        start_idx = max(0, start_l - 1)
        end_idx = min(total_lines, end_l)
        chunk = "".join(lines[start_idx:end_idx])
        cleaned_chunk = clean_newlines(chunk)
        
        header = f"/* =============================================================================\n" \
                 f" * MODUL: public/js/{fname}\n" \
                 f" * DESKRIPSI: {desc}\n" \
                 f" * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)\n" \
                 f" * ============================================================================= */\n\n"
        
        target_path = os.path.join(JS_DIR, fname)
        with open(target_path, "w", encoding="utf-8") as out:
            out.write(header + cleaned_chunk.strip() + "\n")
        
        size_kb = os.path.getsize(target_path) / 1024.0
        line_count = cleaned_chunk.count("\n") + 1
        print(f"  [OK] {fname:26} ({line_count:4d} baris, {size_kb:5.1f} KB) - {desc[:40]}")

def build_bundle():
    """Menggabungkan kembali seluruh modul di public/js/ ke public/app.js"""
    print(f"\n[BUILD] Menyusun bundle dari {JS_DIR} ke {APP_JS}...")
    parts = []
    for fname, _, _, desc in MODULES_SPEC:
        fpath = os.path.join(JS_DIR, fname)
        if not os.path.isfile(fpath):
            print(f"  [ERROR] Berkas modul {fpath} tidak ditemukan!")
            return False
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            # Hilangkan header file jika ada
            clean_content = re.sub(r'/\* =============================================================================\s*\* MODUL:.*?\* ============================================================================= \*/\s*', '', content, flags=re.DOTALL)
            parts.append(clean_content.strip())

    bundle_text = "\n\n".join(parts) + "\n"
    bundle_text = clean_newlines(bundle_text)

    with open(APP_JS, "w", encoding="utf-8") as f:
        f.write(bundle_text)

    size_kb = os.path.getsize(APP_JS) / 1024.0
    line_count = bundle_text.count("\n") + 1
    print(f"[SUCCESS] {APP_JS} berhasil disusun ({line_count} baris, {size_kb:.1f} KB)!")

    # Verifikasi sintaks via node -c
    try:
        res = subprocess.run(["node", "-c", APP_JS], capture_output=True, text=True)
        if res.returncode == 0:
            print("[VERIFY] Node.js syntax check: 100% VALID (0 errors)!")
            return True
        else:
            print(f"[ERROR] Node.js syntax error:\n{res.stderr}")
            return False
    except Exception as e:
        print(f"[WARN] Tidak dapat menjalankan node -c: {e}")
        return True

if __name__ == "__main__":
    split_modules()
    success = build_bundle()
    if not success:
        sys.exit(1)

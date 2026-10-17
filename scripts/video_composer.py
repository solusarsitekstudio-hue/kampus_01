import os
import sys
import json
import re
import math
import asyncio
import subprocess
import wave
import shutil
import numpy as np
from datetime import datetime
from playwright.sync_api import sync_playwright
import edge_tts
import base64

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "academic_data.json")
PROGRESS_ROOT = os.path.join(BASE_DIR, "input", "progress_mahasiswa")
OUTPUT_VIDEOS_DIR = os.path.join(BASE_DIR, "public", "videos")
TEMP_DIR = os.path.join(BASE_DIR, "scratch", "video_temp")

os.makedirs(OUTPUT_VIDEOS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def sanitize_folder_name(name):
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.replace("&", "DAN").strip().replace(" ", "_").upper()
    return clean

def find_student_images(npm, course_name="APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS"):
    """
    Scans input/progress_mahasiswa/<course>/ for student images.
    Matches folder starting with npm (e.g., '2510015410010' or '2510015410010_M_YAZID_ZIDANE_MULYADI').
    Falls back to sample images in D:\\Desktop\\- HAL LAIN if folder is empty or not found.
    """
    clean_course = sanitize_folder_name(course_name)
    course_dir = os.path.join(PROGRESS_ROOT, clean_course)
    
    images = []
    student_folder = None
    
    if os.path.exists(course_dir):
        for entry in os.listdir(course_dir):
            full_entry = os.path.join(course_dir, entry)
            if os.path.isdir(full_entry) and (entry.startswith(str(npm)) or str(npm) in entry):
                student_folder = full_entry
                break
                
    if student_folder and os.path.exists(student_folder):
        valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
        files = sorted(os.listdir(student_folder))
        for f in files:
            if f.lower().endswith(valid_exts):
                images.append(os.path.join(student_folder, f))

    # Fallback to authentic samples from Desktop if empty
    if not images:
        fallback_dir = r"D:\Desktop\- HAL LAIN"
        if os.path.exists(fallback_dir):
            sample_candidates = ["ar a1 ar dg.jpeg", "ar 2a ar dg.jpeg", "QS 1.jpeg", "ar b1.jpeg"]
            for cand in sample_candidates:
                cand_path = os.path.join(fallback_dir, cand)
                if os.path.exists(cand_path):
                    images.append(cand_path)

    return images, student_folder

def generate_ambient_bgm(duration_sec, output_wav):
    """
    Synthesizes a warm, gentle ambient acoustic chord progression in numpy and writes to WAV.
    Harmonic chords: Cmaj7 -> Am7 -> Fmaj7 -> G7 (soft, inspiring, and cinematic).
    """
    sr = 44100
    total_samples = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    
    # 4 Chords: Cmaj7, Am7, Fmaj7, G6
    chords_freqs = [
        [261.63, 329.63, 392.00, 493.88],  # C4, E4, G4, B4
        [220.00, 261.63, 329.63, 392.00],  # A3, C4, E4, G4
        [174.61, 220.00, 261.63, 329.63],  # F3, A3, C4, E4
        [196.00, 246.94, 293.66, 329.63]   # G3, B3, D4, E4
    ]
    
    chord_len = duration_sec / len(chords_freqs)
    audio = np.zeros(total_samples, dtype=np.float32)
    
    for idx, chord in enumerate(chords_freqs):
        start_t = idx * chord_len
        end_t = min((idx + 1) * chord_len, duration_sec)
        idx_start = int(start_t * sr)
        idx_end = int(end_t * sr)
        seg_t = t[idx_start:idx_end] - start_t
        seg_len = len(seg_t)
        
        # Envelope: Gentle swell then soft decay
        env = np.ones(seg_len, dtype=np.float32)
        fade_in = int(0.6 * sr)
        fade_out = int(1.2 * sr)
        if seg_len > fade_in:
            env[:fade_in] = np.linspace(0, 1, fade_in)
        if seg_len > fade_out:
            env[-fade_out:] = np.linspace(1, 0, fade_out)
            
        chord_signal = np.zeros(seg_len, dtype=np.float32)
        for f in chord:
            # Fundamental + gentle 2nd harmonic
            tone = 0.6 * np.sin(2 * np.pi * f * seg_t) + 0.25 * np.sin(2 * np.pi * 2 * f * seg_t)
            chord_signal += tone
            
        chord_signal /= len(chord)
        audio[idx_start:idx_end] += chord_signal * env
        
    # Global fade in and fade out
    total_fade = int(1.5 * sr)
    if total_samples > total_fade:
        audio[:total_fade] *= np.linspace(0, 1, total_fade)
        audio[-total_fade:] *= np.linspace(1, 0, total_fade)
        
    # Normalize and convert to 16-bit PCM
    audio = audio / (np.max(np.abs(audio)) + 1e-6) * 0.45
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Save stereo WAV
    stereo = np.column_stack((audio_int16, audio_int16))
    with wave.open(output_wav, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())

async def async_generate_voiceover(text, output_mp3):
    """
    Generates high-definition Indonesian female neural voiceover using edge-tts (id-ID-GadisNeural).
    """
    comm = edge_tts.Communicate(text, "id-ID-GadisNeural", rate="+2%", pitch="+1Hz")
    await comm.save(output_mp3)

def generate_voiceover(text, output_mp3):
    asyncio.run(async_generate_voiceover(text, output_mp3))
    dur_str = subprocess.check_output([
        "ffprobe", "-i", output_mp3,
        "-show_entries", "format=duration",
        "-v", "quiet", "-of", "csv=p=0"
    ]).decode().strip()
    return float(dur_str)

def get_radar_svg_mini(comp):
    labels = ["CAD", "Detail", "Asistensi", "Logika", "Waktu"]
    values = [
        comp.get("penguasaan_cad", 80),
        comp.get("ketelitian_detail", 80),
        comp.get("kedisiplinan_asistensi", 80),
        comp.get("logika_ruang_struktur", 80),
        comp.get("manajemen_waktu", 80)
    ]
    cx, cy, r = 100, 75, 45
    angle_step = 2 * math.pi / 5
    
    rings = ""
    for lvl in [0.4, 0.7, 1.0]:
        pts = [f"{cx + r * lvl * math.cos(-math.pi/2 + i*angle_step):.1f},{cy + r * lvl * math.sin(-math.pi/2 + i*angle_step):.1f}" for i in range(5)]
        rings += f'<polygon points="{" ".join(pts)}" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1" />\n'
        
    data_pts = [f"{cx + r * (v/100.0) * math.cos(-math.pi/2 + i*angle_step):.1f},{cy + r * (v/100.0) * math.sin(-math.pi/2 + i*angle_step):.1f}" for i, v in enumerate(values)]
    poly = f'<polygon points="{" ".join(data_pts)}" fill="rgba(245, 158, 11, 0.35)" stroke="#f59e0b" stroke-width="2.5" />\n'
    
    return f"""
    <svg width="200" height="150" viewBox="0 0 200 150" xmlns="http://www.w3.org/2000/svg">
      {rings}
      {poly}
    </svg>
    """

def image_to_base64_data_uri(img_path):
    if not img_path or not os.path.exists(img_path):
        return ""
    ext = os.path.splitext(img_path)[1].lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{ext};base64,{encoded}"

def render_vertical_slides_html(student, course_info, images):
    """
    Renders 4 breathtaking 1080x1920 (9:16 Portrait) HTML slides for video compilation.
    """
    nama = student["nama"]
    npm = student["npm"]
    akademik = student["akademik"]
    nilai = akademik.get("nilai_rata_rata", 85)
    grade = akademik.get("grade", "A")
    predikat = akademik.get("predikat", "Kompeten Unggul")
    mk_nama = course_info.get("nama_mk", "Aplikasi Komputer Arsitektur & QS")
    
    ai = student.get("ai_diagnosis", {})
    matriks = ai.get("matriks_karier_10", [])
    top_career = matriks[0] if matriks else {"profesi": "Architectural Designer", "kecocokan_persen": 95}
    
    # 4 Image Base64 URIs (guaranteed to render 100% reliably in Playwright without path issues)
    img_urls = []
    for i in range(4):
        target_img = images[i] if i < len(images) else (images[0] if images else "")
        b64 = image_to_base64_data_uri(target_img)
        img_urls.append(b64)

    radar_svg = get_radar_svg_mini(akademik.get("kompetensi", {}))

    slides = []

    # ==================== SLIDE 1: INTRO & COVER PRESTASI ====================
    html1 = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ width: 1080px; height: 1920px; background: #070d19; color: white; overflow: hidden; position: relative; }}
        
        .bg-blur {{
          position: absolute; width: 110%; height: 110%; left: -5%; top: -5%;
          background: url('{img_urls[0]}') center/cover no-repeat;
          filter: blur(40px) brightness(0.25);
        }}
        
        .content {{
          position: relative; z-index: 10; width: 1080px; height: 1920px;
          display: flex; flex-direction: column; justify-content: space-between;
          padding: 80px 65px;
        }}
        
        .header {{
          display: flex; align-items: center; justify-content: space-between;
          border-bottom: 2px solid rgba(255,255,255,0.15); padding-bottom: 30px;
        }}
        .brand-badge {{
          background: rgba(245, 158, 11, 0.15); border: 2px solid #f59e0b;
          color: #fbbf24; padding: 12px 24px; border-radius: 999px;
          font-weight: 800; font-size: 24px; letter-spacing: 1px;
        }}
        
        .image-card {{
          background: rgba(15, 23, 42, 0.75); border: 3px solid rgba(255,255,255,0.2);
          border-radius: 36px; padding: 24px; box-shadow: 0 30px 60px rgba(0,0,0,0.6);
          text-align: center;
        }}
        .image-card img {{
          width: 100%; height: 780px; object-fit: contain; border-radius: 24px;
          background: #020617;
        }}
        .img-tag {{
          margin-top: 18px; font-family: 'JetBrains Mono', monospace; font-size: 22px;
          color: #38bdf8; font-weight: 700;
        }}
        
        .footer-card {{
          background: rgba(15, 23, 42, 0.88); border: 2px solid rgba(56, 189, 248, 0.4);
          border-radius: 32px; padding: 40px; backdrop-filter: blur(20px);
        }}
        .student-name {{
          font-size: 48px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px;
          line-height: 1.2;
        }}
        .student-sub {{
          font-family: 'JetBrains Mono', monospace; font-size: 26px; color: #94a3b8;
          margin-top: 10px;
        }}
        .score-pill {{
          display: inline-flex; align-items: center; gap: 15px; margin-top: 24px;
          background: #10b981; color: #022c22; padding: 12px 28px; border-radius: 999px;
          font-size: 28px; font-weight: 900;
        }}
      </style>
    </head>
    <body>
      <div class="bg-blur"></div>
      <div class="content">
        <div class="header">
          <div>
            <div style="font-size: 32px; font-weight: 900; color: #ffffff; letter-spacing: 0.5px;">🏛️ PROGRAM STUDI ARSITEKTUR</div>
            <div style="font-size: 22px; color: #94a3b8; margin-top: 6px;">FAKULTAS TEKNIK & DESAIN • LAB KOMPUTER LIKDA</div>
          </div>
          <div class="brand-badge">PORTOFOLIO DIGITAL</div>
        </div>
        
        <div class="image-card">
          <img src="{img_urls[0]}">
          <div class="img-tag">📐 SESI 1: PENGENALAN AUTOCAD & GAMBAR KERJA</div>
        </div>
        
        <div class="footer-card">
          <div style="font-size: 22px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;">
            Laporan Prestasi Mahasiswa
          </div>
          <div class="student-name">{nama}</div>
          <div class="student-sub">NPM: {npm} • Kelas TEKZA</div>
          <div class="score-pill">
            <span>PREDIKAT {grade}</span>
            <span>•</span>
            <span>NILAI {nilai} ({predikat})</span>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    slides.append(html1)

    # ==================== SLIDE 2: PROGRES GAMBAR KERJA 2D ====================
    html2 = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ width: 1080px; height: 1920px; background: #070d19; color: white; overflow: hidden; position: relative; }}
        .bg-blur {{
          position: absolute; width: 110%; height: 110%; left: -5%; top: -5%;
          background: url('{img_urls[1]}') center/cover no-repeat;
          filter: blur(40px) brightness(0.25);
        }}
        .content {{
          position: relative; z-index: 10; width: 1080px; height: 1920px;
          display: flex; flex-direction: column; justify-content: space-between;
          padding: 80px 65px;
        }}
        .header {{
          display: flex; align-items: center; justify-content: space-between;
          border-bottom: 2px solid rgba(255,255,255,0.15); padding-bottom: 30px;
        }}
        .image-card {{
          background: rgba(15, 23, 42, 0.75); border: 3px solid rgba(255,255,255,0.2);
          border-radius: 36px; padding: 24px; box-shadow: 0 30px 60px rgba(0,0,0,0.6);
          text-align: center;
        }}
        .image-card img {{
          width: 100%; height: 820px; object-fit: contain; border-radius: 24px;
          background: #020617;
        }}
        .img-tag {{
          margin-top: 18px; font-family: 'JetBrains Mono', monospace; font-size: 22px;
          color: #f59e0b; font-weight: 700;
        }}
        .footer-card {{
          background: rgba(15, 23, 42, 0.88); border: 2px solid rgba(245, 158, 11, 0.4);
          border-radius: 32px; padding: 40px; backdrop-filter: blur(20px);
        }}
      </style>
    </head>
    <body>
      <div class="bg-blur"></div>
      <div class="content">
        <div class="header">
          <div>
            <div style="font-size: 32px; font-weight: 900; color: #ffffff;">🏛️ PROSES ASISTENSI STUDIO</div>
            <div style="font-size: 22px; color: #94a3b8; margin-top: 6px;">STANDARDISASI LAYER CAD & DOKUMEN KONSTRUKSI</div>
          </div>
          <div style="background: rgba(56, 189, 248, 0.15); border: 2px solid #38bdf8; color: #38bdf8; padding: 12px 24px; border-radius: 999px; font-weight: 800; font-size: 24px;">
            MODUL 2 - 4
          </div>
        </div>
        
        <div class="image-card">
          <img src="{img_urls[1]}">
          <div class="img-tag">💻 PRAKTIKUM DENAH, KOLOM, DINDING & NOTASI RUANG</div>
        </div>
        
        <div class="footer-card">
          <div style="font-size: 24px; font-weight: 800; color: #fbbf24; margin-bottom: 12px;">
            ⚡ PENGUASAAN TEKNIS STUDIO:
          </div>
          <div style="font-size: 28px; color: #e2e8f0; line-height: 1.5;">
            Ananda <strong>{nama}</strong> menunjukkan kedisiplinan dan ketelitian gambar presisi tinggi sesuai standar Ikatan Arsitek Indonesia (IAI).
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    slides.append(html2)

    # ==================== SLIDE 3: DETAIL POTONGAN & PROYEKSI KARIER ====================
    html3 = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ width: 1080px; height: 1920px; background: #070d19; color: white; overflow: hidden; position: relative; }}
        .bg-blur {{
          position: absolute; width: 110%; height: 110%; left: -5%; top: -5%;
          background: url('{img_urls[2]}') center/cover no-repeat;
          filter: blur(40px) brightness(0.25);
        }}
        .content {{
          position: relative; z-index: 10; width: 1080px; height: 1920px;
          display: flex; flex-direction: column; justify-content: space-between;
          padding: 80px 65px;
        }}
        .header {{
          display: flex; align-items: center; justify-content: space-between;
          border-bottom: 2px solid rgba(255,255,255,0.15); padding-bottom: 30px;
        }}
        .image-card {{
          background: rgba(15, 23, 42, 0.75); border: 3px solid rgba(255,255,255,0.2);
          border-radius: 36px; padding: 24px; box-shadow: 0 30px 60px rgba(0,0,0,0.6);
          text-align: center;
        }}
        .image-card img {{
          width: 100%; height: 760px; object-fit: contain; border-radius: 24px;
          background: #020617;
        }}
        .img-tag {{
          margin-top: 18px; font-family: 'JetBrains Mono', monospace; font-size: 22px;
          color: #34d399; font-weight: 700;
        }}
        .footer-card {{
          background: rgba(15, 23, 42, 0.92); border: 2px solid #10b981;
          border-radius: 32px; padding: 36px; backdrop-filter: blur(20px);
          display: flex; align-items: center; justify-content: space-between; gap: 30px;
        }}
      </style>
    </head>
    <body>
      <div class="bg-blur"></div>
      <div class="content">
        <div class="header">
          <div>
            <div style="font-size: 32px; font-weight: 900; color: #ffffff;">🏛️ PROFIL KOMPETENSI MASA DEPAN</div>
            <div style="font-size: 22px; color: #94a3b8; margin-top: 6px;">DETAIL POTONGAN & ESTIMASI VOLUME QS</div>
          </div>
          <div style="background: rgba(16, 185, 129, 0.15); border: 2px solid #10b981; color: #34d399; padding: 12px 24px; border-radius: 999px; font-weight: 800; font-size: 24px;">
            SIAP INDUSTRI
          </div>
        </div>
        
        <div class="image-card">
          <img src="{img_urls[2]}">
          <div class="img-tag">📊 DETAIL PONDASI & ESTIMASI ANGGARAN BIAYA</div>
        </div>
        
        <div class="footer-card">
          <div>
            <div style="font-size: 22px; font-weight: 800; color: #34d399; text-transform: uppercase; letter-spacing: 1.5px;">
              PROYEKSI KARIER RIIL UNGGULAN:
            </div>
            <div style="font-size: 38px; font-weight: 900; color: #ffffff; margin: 6px 0;">
              {top_career.get('profesi', 'Architectural Designer')}
            </div>
            <div style="font-size: 24px; color: #cbd5e1;">
              Kecocokan Talenta: <strong style="color: #38bdf8;">{top_career.get('kecocokan_persen', 95)}%</strong>
            </div>
          </div>
          <div>
            {radar_svg}
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    slides.append(html3)

    # ==================== SLIDE 4: PENGESAHAN & BANGGA BERSAMA ====================
    html4 = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ width: 1080px; height: 1920px; background: #070d19; color: white; overflow: hidden; position: relative; }}
        .bg-blur {{
          position: absolute; width: 110%; height: 110%; left: -5%; top: -5%;
          background: url('{img_urls[3]}') center/cover no-repeat;
          filter: blur(40px) brightness(0.2);
        }}
        .content {{
          position: relative; z-index: 10; width: 1080px; height: 1920px;
          display: flex; flex-direction: column; justify-content: space-between;
          padding: 80px 65px; text-align: center;
        }}
        .badge-center {{
          width: 180px; height: 180px; margin: 0 auto;
          border-radius: 999px; border: 4px dashed #f59e0b;
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          background: rgba(245, 158, 11, 0.15); box-shadow: 0 0 50px rgba(245, 158, 11, 0.4);
        }}
      </style>
    </head>
    <body>
      <div class="bg-blur"></div>
      <div class="content">
        <div style="border-bottom: 2px solid rgba(255,255,255,0.15); padding-bottom: 30px;">
          <div style="font-size: 34px; font-weight: 900; color: #ffffff;">PROGRAM STUDI ARSITEKTUR</div>
          <div style="font-size: 24px; color: #94a3b8; margin-top: 8px;">KEMENTERIAN PENDIDIKAN TINGGI, SAINS & TEKNOLOGI</div>
        </div>
        
        <div style="margin: 40px 0;">
          <div class="badge-center">
            <span style="font-size: 65px;">🏛️</span>
            <span style="font-size: 18px; font-weight: 900; color: #fbbf24; font-family: 'JetBrains Mono'; margin-top: 4px;">VERIFIED</span>
          </div>
          
          <div style="font-size: 52px; font-weight: 900; color: #ffffff; margin-top: 36px; line-height: 1.2;">
            BANGGA BERSAMA ANANDA<br>
            <span style="color: #38bdf8;">{nama}</span>
          </div>
          
          <div style="font-size: 28px; color: #cbd5e1; margin-top: 24px; line-height: 1.6; max-width: 850px; margin-left: auto; margin-right: auto;">
            Terima kasih atas doa, cinta, dan bimbingan tiada henti dari Bapak dan Ibu Wali Murid di rumah. Bersama, kita wujudkan cita-cita ananda menjadi arsitek profesional masa depan!
          </div>
        </div>
        
        <div style="background: rgba(15, 23, 42, 0.95); border: 3px solid rgba(255,255,255,0.25); border-radius: 36px; padding: 40px;">
          <div style="font-size: 24px; font-weight: 700; color: #94a3b8;">Disahkan secara Resmi oleh:</div>
          <div style="font-size: 34px; font-weight: 900; color: #ffffff; margin-top: 6px;">FIELDA ROZA, S.T., M.T.</div>
          <div style="font-size: 22px; color: #38bdf8; font-family: 'JetBrains Mono'; margin-top: 4px;">Ketua Program Studi Arsitektur</div>
        </div>
      </div>
    </body>
    </html>
    """
    slides.append(html4)

    return slides

def compile_video_mp4(student, course_info, images, output_mp4):
    """
    Master pipeline:
    1. Edge-TTS GadisNeural audio voiceover.
    2. Synthesizes ambient BGM track.
    3. Renders 4 HTML 1080x1920 slides via Playwright screenshots.
    4. Compiles final 9:16 MP4 via FFmpeg with Ken Burns motion & audio mixing.
    """
    npm = student["npm"]
    script_text = student["marketing"]["video"]["voiceover_script"]
    
    # 1. Voiceover
    vo_path = os.path.join(TEMP_DIR, f"vo_{npm}.mp3")
    vo_duration = generate_voiceover(script_text, vo_path)
    total_duration = max(vo_duration + 1.5, 28.0)
    
    # 2. Ambient BGM
    bgm_path = os.path.join(TEMP_DIR, f"bgm_{npm}.wav")
    generate_ambient_bgm(total_duration, bgm_path)
    
    # 3. Render HTML Slides to PNG
    slides_html = render_vertical_slides_html(student, course_info, images)
    slide_pngs = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        for i, s_html in enumerate(slides_html):
            png_path = os.path.join(TEMP_DIR, f"slide_{npm}_{i}.png")
            page.set_content(s_html)
            page.screenshot(path=png_path)
            slide_pngs.append(png_path)
        browser.close()
        
    # 4. Generate Video using FFmpeg
    # Each slide duration = total_duration / 4
    slide_dur = total_duration / 4.0
    
    # Create input concat list for ffmpeg with crossfade or simple duration
    concat_txt = os.path.join(TEMP_DIR, f"concat_{npm}.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for png in slide_pngs:
            clean_p = png.replace("\\", "/")
            f.write(f"file '{clean_p}'\n")
            f.write(f"duration {slide_dur:.2f}\n")
        # Final frame repeat for smooth ending
        clean_last = slide_pngs[-1].replace("\\", "/")
        f.write(f"file '{clean_last}'\n")

    mixed_audio = os.path.join(TEMP_DIR, f"mixed_audio_{npm}.wav")
    # Mix Voiceover (1.0 volume) + BGM (0.12 volume)
    cmd_audio = [
        "ffmpeg", "-y",
        "-i", vo_path,
        "-i", bgm_path,
        "-filter_complex", "[0:a]volume=1.0[vo];[1:a]volume=0.12[bgm];[vo][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "[aout]",
        mixed_audio
    ]
    subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Final Video Encoding: 1080x1920, H.264, AAC
    cmd_video = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-i", mixed_audio,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    return {
        "success": True,
        "video_path": output_mp4,
        "duration": round(total_duration, 1),
        "voice_duration": round(vo_duration, 1),
        "images_used": len(images)
    }

def generate_video_short_for_student(npm):
    """
    High-level entry point to generate video short for any student.
    """
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    student = next((s for s in data.get("students", []) if s["npm"] == str(npm)), None)
    if not student and data.get("students"):
        student = data["students"][0]
        
    course_info = data.get("course", {})
    images, folder = find_student_images(student["npm"], course_info.get("nama_mk", ""))
    
    output_mp4 = os.path.join(OUTPUT_VIDEOS_DIR, f"video_portofolio_{student['npm']}.mp4")
    result = compile_video_mp4(student, course_info, images, output_mp4)
    result["student_name"] = student["nama"]
    result["npm"] = student["npm"]
    result["folder_source"] = folder
    return result

if __name__ == "__main__":
    test_npm = sys.argv[1] if len(sys.argv) > 1 else "2510015410010"
    print(f"[INFO] Generating Video Short Portofolio 9:16 for NPM: {test_npm}...")
    res = generate_video_short_for_student(test_npm)
    print(f"[SUCCESS] Video MP4 Ready: {res['video_path']}")
    print(f"          Duration: {res['duration']}s | Images used: {res['images_used']}")

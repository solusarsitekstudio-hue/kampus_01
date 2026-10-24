"""Generator Video Pitch 16:9 SIAK-KAPRODI: Co-pilot Kaprodi (14 Slide).

Memanfaatkan:
  - 14 Slide PNG 2K dari presentasi/png_pitch/slide-01.png ... slide-14.png
  - Edge-TTS AI Neural Voiceover (id-ID-GadisNeural)
  - Architectural BGM dari E:\\WORKSHOP\\BGM\\bgm_chill_03_minimal.mp3 (auto-ducking)
  - FFmpeg 1080p H.264 / AAC High-Fidelity Render

Output:
  presentasi/SIAK-KAPRODI_Pitch_Video_16x9.mp4
"""
import os
import sys
import json
import asyncio
import subprocess
import shutil
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG_DIR = os.path.join(ROOT, "png_pitch")
OUT_MP4 = os.path.join(ROOT, "SIAK-KAPRODI_Pitch_Video_16x9.mp4")
BGM_SRC = r"E:\WORKSHOP\BGM\bgm_chill_03_minimal.mp3"

# 14 Naskah Narasi Presisi Otak-CR (Bukan Robot, Penuh Jiwa Arsitektur)
SLIDE_SCRIPTS = [
    # S1
    "SIAK-KAPRODI. Bukan sekadar sistem informasi, ini adalah arsitektur intelijen dan executive cockpit. "
    "Satu pohon kurikulum dipasang sekali, seluruh capaian semester dan dokumen resmi dibangun darinya.",
    # S2
    "Empat friksi utama kaprodi hari ini: data taburan di Excel, laporan tiga puluh mata kuliah yang disusun manual, "
    "hingga absensi yang mengaburkan mutu capaian pembelajaran.",
    # S3
    "Satu sumber kebenaran. Dari pohon kurikulum lokal, sistem membangun master bersegmen, "
    "melahirkan executive cockpit sebelas tab, sebelas berkas PDF resmi, simulator WhatsApp tiga persona, dan video tanpa salin tempel.",
    # S4
    "Metodologi nilai yang bisa dipertahankan di forum. Nilai terbobot dari satu jurnal, "
    "total bobot wajib seratus, pertemuan belum diinput bersifat netral, dan alpha nol tetap dihitung jujur.",
    # S5
    "Peta Kompetensi Kelas. Muka dashboard yang menjawab mutu, bukan presensi. "
    "Rata-rata nilai studio tujuh puluh tujuh koma sembilan, kehadiran delapan puluh tiga koma delapan persen, dua puluh tujuh mahasiswa lulus, dan tujuh mahasiswa at-risk untuk pendampingan presisi.",
    # S6
    "Diagnosis mahasiswa dengan empat lapis modular radar tanpa perangkingan kompetitif. Menghargai keunikan tiap mahasiswa "
    "dari karakter softskill studio, modul enam belas sesi, lintas semester, hingga potensi masa depan.",
    # S7
    "Portofolio empat lapis berkecepatan tinggi, dipadukan matriks sepuluh peluang karier riil "
    "yang ditimbang tujuh puluh persen radar dan tiga puluh persen bukti kanal nyata.",
    # S8
    "Lapis AI cerdas dengan rintangan mutlak. Fleksibel menggunakan API, Agent otonom, hingga model lokal LLM untuk merapikan narasi. "
    "Tetap terkunci sistem fail-closed: jika ada angka karangan di luar bukti, hasil dibuang dan kembali ke template.",
    # S9
    "Satu hit data kurikulum, seluruh dokumen senada. Dari sebelas PDF resmi, pitch deck boardroom enam belas banding sembilan, "
    "video sembilan banding enam belas, hingga WhatsApp Hub tiga persona.",
    # S10
    "Integritas arsip terjaga. Setiap file masuk dipindai SHA-256 anti-duplikat, "
    "output diaudit utuh, dan arsip diserahkan rapi ke manifest pengiriman.",
    # S11
    "Kejujuran data adalah fondasi utama. Nilai demo dinyatakan sintetis secara transparan, "
    "seraya menyiapkan pipa impor portal dengan review manusia di garda depan.",
    # S12
    "Bukan janji, tapi angka kinerja terukur. Kompilasi bersegmen sub-detik, "
    "penarikan portofolio satu sampai tiga puluh lima milidetik, berjalan seratus persen offline di server Python lokal sebelas tab.",
    # S13
    "Tab sebelas: Executive Boardroom Cockpit Yayasan dan Investor. Menyajikan lima kartu truf eksekutif: "
    "valuasi SPP satu koma tujuh belas miliar, mitigasi lost cashflow seratus sembilan puluh lima juta rupiah, kesiapan akreditasi delapan puluh tujuh koma tiga persen, dan standardisasi tiga puluh mata kuliah.",
    # S14
    "SIAK-KAPRODI. Bukan absen digital, ini adalah co-pilot mutu capaian dan executive cockpit. "
    "Bawa satu pertanyaan kaprodi atau yayasan yang paling membebani, mari kita jawab bersama dari data yang sama."
]

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

async def generate_all_vo(temp_dir):
    import edge_tts
    print("[1/4] Men-generate 14 file Voiceover AI (id-ID-GadisNeural)...")
    vo_files = []
    durations = []
    
    for i, script in enumerate(SLIDE_SCRIPTS, 1):
        out_vo = os.path.join(temp_dir, f"vo_{i:02d}.mp3")
        
        # Retry logic: Inisialisasi Communicate BARU di tiap percobaan
        success = False
        for attempt in range(4):
            try:
                comm = edge_tts.Communicate(script, "id-ID-GadisNeural")
                await comm.save(out_vo)
                if os.path.exists(out_vo) and os.path.getsize(out_vo) > 1000:
                    success = True
                    break
            except Exception as e:
                print(f"    [RETRY] Slide {i:02d} attempt {attempt+1} gagal: {e}, mencoba lagi...")
                await asyncio.sleep(1.5)
        
        if not success:
            raise RuntimeError(f"Gagal generate voiceover untuk Slide {i:02d}")
                
        dur = get_audio_duration(out_vo)
        vo_files.append(out_vo)
        durations.append(dur)
        print(f"  - Slide {i:02d}: {dur:.2f}s | {script[:45]}...")
        await asyncio.sleep(0.3)
        
    return vo_files, durations

def build_pitch_video():
    temp_dir = tempfile.mkdtemp(prefix="siak_pitch_vid_")
    try:
        # 1. Generate Voiceovers
        vo_files, durations = asyncio.run(generate_all_vo(temp_dir))
        
        # 2. Build Slide Concat List & Calculate Total Duration
        print("[2/4] Menyusun durasi visual slide dan sequence...")
        slide_pause = 0.45  # Jeda nafas antar slide
        total_duration = 0.0
        
        concat_slides_txt = os.path.join(temp_dir, "slides_concat.txt")
        with open(concat_slides_txt, "w", encoding="utf-8") as f:
            for i, dur in enumerate(durations, 1):
                png_path = os.path.join(PNG_DIR, f"slide-{i:02d}.png")
                if not os.path.exists(png_path):
                    raise FileNotFoundError(f"File slide tidak ditemukan: {png_path}")
                
                slide_display_dur = dur + slide_pause
                total_duration += slide_display_dur
                
                # Format concat FFmpeg (forward slash)
                clean_path = png_path.replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{clean_path}'\n")
                f.write(f"duration {slide_display_dur:.3f}\n")
                
            # Ulangi frame terakhir sebagai anchor
            last_png = os.path.join(PNG_DIR, "slide-14.png").replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{last_png}'\n")

        print(f"  [INFO] Total durasi video: {total_duration:.2f} detik (~{int(total_duration // 60)}m {int(total_duration % 60)}s)")

        # 3. Concatenate and Pad Audio Voiceover Sequence
        print("[3/4] Menggabungkan Voiceover dan mixing BGM dengan auto-ducking...")
        
        # Buat audio track VO dengan jeda presisi
        concat_audio_txt = os.path.join(temp_dir, "audio_concat.txt")
        # Buat file silence 0.45 detik
        silence_wav = os.path.join(temp_dir, "silence.wav")
        subprocess.run([
            "ffmpeg", "-y", "-nostdin",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", f"{slide_pause:.3f}",
            silence_wav
        ], capture_output=True, check=True)

        with open(concat_audio_txt, "w", encoding="utf-8") as f:
            for vo in vo_files:
                clean_vo = vo.replace("\\", "/").replace("'", "'\\''")
                clean_silence = silence_wav.replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{clean_vo}'\n")
                f.write(f"file '{clean_silence}'\n")

        vo_full = os.path.join(temp_dir, "vo_full.wav")
        subprocess.run([
            "ffmpeg", "-y", "-nostdin",
            "-f", "concat", "-safe", "0", "-i", concat_audio_txt,
            "-c:a", "pcm_s16le",
            vo_full
        ], capture_output=True, check=True)

        # Mix with BGM
        mixed_audio = os.path.join(temp_dir, "mixed_audio.wav")
        # Filter: BGM di-loop, volume ducked 0.11, fade in 1s, fade out 2.5s di akhir
        fade_out_start = max(0, total_duration - 2.5)
        
        filter_audio = (
            f"[0:a]volume=1.0,apad=pad_dur={total_duration:.2f}[vo];"
            f"[1:a]aloop=loop=-1:size=2e+09,volume=0.11,afade=t=in:ss=0:d=1.0,afade=t=out:st={fade_out_start:.2f}:d=2.5[bgm];"
            f"[vo][bgm]amix=inputs=2:duration=first:dropout_transition=2,"
            f"atrim=0:{total_duration:.2f}[aout]"
        )

        subprocess.run([
            "ffmpeg", "-y", "-nostdin",
            "-i", vo_full,
            "-i", BGM_SRC,
            "-filter_complex", filter_audio,
            "-map", "[aout]",
            mixed_audio
        ], capture_output=True, check=True)

        # 4. Render Final MP4 Widescreen 1080p
        print("[4/4] Me-render video MP4 1080p Full HD via FFmpeg...")
        part_mp4 = OUT_MP4 + ".part.mp4"
        
        cmd_render = [
            "ffmpeg", "-y", "-nostdin",
            "-f", "concat", "-safe", "0", "-i", concat_slides_txt,
            "-i", mixed_audio,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "256k",
            "-t", f"{total_duration:.3f}",
            "-movflags", "+faststart",
            part_mp4
        ]
        
        subprocess.run(cmd_render, capture_output=True, check=True)
        os.replace(part_mp4, OUT_MP4)

        size_mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
        print("=" * 60)
        print(f"[SUCCESS] Video Pitch 16:9 SIAK-KAPRODI Selesai!")
        print(f"Path   : {OUT_MP4}")
        print(f"Ukuran : {size_mb:.2f} MB")
        print(f"Durasi : {total_duration:.2f} detik")
        print("=" * 60)
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    build_pitch_video()

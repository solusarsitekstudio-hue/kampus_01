@echo off
chcp 65001 >nul
title SIAK-KAPRODI - Video Short Portofolio 9:16 Generator
color 0b

echo =======================================================================
echo    🏛️ SIAK-KAPRODI: GENERATOR VIDEO SHORT PORTOFOLIO 9:16 (FULL HD)
echo    Program Studi Arsitektur - Fakultas Teknik & Desain
echo    Voiceover: id-ID-GadisNeural (AI Voice) • Engine: FFmpeg
echo =======================================================================
echo.

set TARGET_NPM=%1
if "%TARGET_NPM%"=="" (
    set TARGET_NPM=2510015410010
    echo [INFO] Tidak ada NPM spesifik, menggunakan mahasiswa default: %TARGET_NPM% (M Yazid Zidane)
) else (
    echo [INFO] Menjalankan generator video untuk NPM: %TARGET_NPM%
)

echo [INFO] Memeriksa folder foto input/progress_mahasiswa/ ...
python scripts\video_composer.py %TARGET_NPM%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================================
    echo [SUKSES] Video Portofolio 9:16 Berhasil Dihasilkan!
    echo          Lokasi: public\videos\video_portofolio_%TARGET_NPM%.mp4
    echo          Dapat diputar langsung di Dashboard Web: http://localhost:40404
    echo =======================================================================
) else (
    echo.
    echo [GAGAL] Terjadi kesalahan saat merender video. Periksa dependensi FFmpeg dan Edge-TTS.
)

echo.
pause

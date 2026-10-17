@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title SIAK-KAPRODI - Video Short Portofolio 9:16 Generator
cd /d "%~dp0"
color 0b

echo =======================================================================
echo  SIAK-KAPRODI: GENERATOR VIDEO SHORT PORTOFOLIO 9:16 (FULL HD)
echo  Program Studi Arsitektur - Fakultas Teknik ^& Desain
echo  Voiceover: id-ID-GadisNeural (AI Voice) - Engine: FFmpeg
echo =======================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

REM FIX: pakai !VAR! (delayed expansion). Dulu %TARGET_NPM% ditulis di dalam
REM blok if/else, sehingga di-parse SEBELUM nilainya di-set -> selalu kosong.
set "TARGET_NPM=%~1"
if "!TARGET_NPM!"=="" (
    set "TARGET_NPM=2510015410010"
    echo [INFO] Tidak ada NPM spesifik, memakai mahasiswa default: !TARGET_NPM!
) else (
    echo [INFO] Menjalankan generator video untuk NPM: !TARGET_NPM!
)

echo [INFO] Memeriksa folder foto input\progress_mahasiswa\ ...
echo [INFO] Render bisa memakan 1-3 menit. Jangan tutup jendela ini.
echo.
%PY% scripts\video_composer.py "!TARGET_NPM!"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" goto :ok
goto :fail

:ok
echo =======================================================================
echo [SUKSES] Video Portofolio 9:16 Berhasil Dihasilkan!
echo          Lokasi: public\videos\video_portofolio_!TARGET_NPM!.mp4
echo          Dashboard Web: http://localhost:40404
echo =======================================================================
goto :end

:fail
echo =======================================================================
echo [GAGAL] Video tidak berhasil dirender.
echo         Penyebab umum:
echo           - NPM tidak ada di data\academic_data.json
echo           - Folder foto mahasiswa kosong
echo             input\progress_mahasiswa\[MATA_KULIAH]\!TARGET_NPM!_NAMA\
echo           - FFmpeg belum ada di PATH
echo         Pesan error lengkap ada di baris di atas.
echo =======================================================================

:end
echo.
pause
endlocal
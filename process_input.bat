@echo off
setlocal EnableExtensions
chcp 65001 >nul
TITLE SIAK-KAPRODI Ingest & Process Input Data
cd /d "%~dp0"
echo =====================================================================
echo  SIAK-KAPRODI: PIPELINE INGESTION & PROCESSING DATA INPUT
echo =====================================================================
echo.
echo Struktur Input:
echo  1. Letakkan berkas mentah portal/absensi di:
echo     input\raw\[NAMA_MATA_KULIAH]\[TIMESTAMP]\
echo.
echo  2. Script ini akan menormalisasi data ke:
echo     input\processed\[NAMA_MATA_KULIAH]\[TIMESTAMP]\
echo.
echo  3. Sekaligus memperbarui katalog course data\courses\ dan
echo     meng-generate dokumen di:
echo     output\[NAMA_MATA_KULIAH]\[TIMESTAMP]\
echo =====================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

REM Reset dulu supaya tidak mewarisi variabel dari sesi sebelumnya
set "COURSE_CHOICE="
set /p "COURSE_CHOICE=Pilih Mata Kuliah [1=Aplikasi Komputer, 2=Studio Perancangan 2, 3=Struktur 1] (Default: 1): "
if not defined COURSE_CHOICE set "COURSE_CHOICE=1"

if "%COURSE_CHOICE%"=="2" (
    set "COURSE_NAME=STUDIO_PERANCANGAN_ARSITEKTUR_2"
) else if "%COURSE_CHOICE%"=="3" (
    set "COURSE_NAME=STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1"
) else (
    set "COURSE_NAME=APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS"
)

echo.
echo [1/2] Memproses Input untuk: %COURSE_NAME% ...
%PY% scripts\process_input.py --course "%COURSE_NAME%"
if errorlevel 1 (
    echo.
    echo [GAGAL] Proses input BERHENTI. Master dataset tidak diubah.
    pause
    exit /b 1
)

echo.
echo [2/2] Men-generate Dokumen PDF Resmi dan DeckCraft Widescreen...
%PY% scripts\generate_pdfs.py
if errorlevel 1 (
    echo.
    echo [GAGAL] Generate PDF BERHENTI. Data input tetap tersimpan di input\processed\.
    pause
    exit /b 1
)

echo.
echo =====================================================================
echo [SELESAI] Pipeline Ingest, Olah Input, dan Generate Output Tuntas!
echo =====================================================================
pause
endlocal
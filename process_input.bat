@echo off
TITLE SIAK-KAPRODI Ingest & Process Input Data
echo =====================================================================
echo  SIAK-KAPRODI: PIPELINE INGESTION & PROCESSING DATA INPUT
echo =====================================================================
echo.
echo Struktur Input:
echo  1. Letakkan berkas mentah portal/absensi di:
echo     input\raw\^<NAMA_MATA_KULIAH^>\^<TIMESTAMP^>\
echo.
echo  2. Script ini akan menormalisasi data ke:
echo     input\processed\^<NAMA_MATA_KULIAH^>\^<TIMESTAMP^>\
echo.
echo  3. Sekaligus mengupdate katalog course dan men-generate dokumen di:
echo     output\^<NAMA_MATA_KULIAH^>\^<TIMESTAMP^>\
echo =====================================================================
echo.

set /p COURSE_CHOICE="Pilih Mata Kuliah [1=Aplikasi Komputer, 2=Studio Perancangan 2, 3=Struktur 1] (Default: 1): "

if "%COURSE_CHOICE%"=="2" (
    set COURSE_NAME=STUDIO_PERANCANGAN_ARSITEKTUR_2
) else if "%COURSE_CHOICE%"=="3" (
    set COURSE_NAME=STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1
) else (
    set COURSE_NAME=APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS
)

echo.
echo [1/2] Memproses Input untuk: %COURSE_NAME% ...
python scripts\process_input.py --course "%COURSE_NAME%"

echo.
echo [2/2] Men-generate Dokumen PDF Resmi dan DeckCraft Widescreen...
python scripts\generate_pdfs.py

echo.
echo =====================================================================
echo [SELESAI] Pipeline Ingest, Olah Input, dan Generate Output Tuntas!
echo =====================================================================
pause

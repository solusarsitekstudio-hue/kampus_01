@echo off
TITLE SIAK-KAPRODI Arsitektur Intelligence Server
set PORT=40404

echo =====================================================================
echo  SIAK-KAPRODI ARSITEKTUR INTELLIGENCE SYSTEM
echo =====================================================================
echo  Mengecek dependensi data...

if not exist "data\academic_data.json" (
    echo Mengompilasi data akademik dari Excel dan PDF...
    python scripts\parse_data.py
)

if not exist "generated_pdfs\03_laporan_penilaian_kaprodi_master_gradebook.pdf" (
    echo Menggenerate paket dokumen PDF resmi arsitektur...
    python scripts\generate_pdfs.py
)

echo Membuka browser ke http://localhost:%PORT% ...
start http://localhost:%PORT%

echo Menjalankan Web Server di port %PORT%...
python server.py

pause

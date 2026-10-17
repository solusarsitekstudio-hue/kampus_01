@echo off
TITLE Setup SIAK-KAPRODI Environment
echo =====================================================================
echo  MENYIAPKAN ENVIRONMENT & DEPENDENSI PYTHON
echo =====================================================================

python --version
if errorlevel 1 (
    echo [ERROR] Python tidak terdeteksi di PATH system!
    pause
    exit /b 1
)

echo Menginstall dependensi yang dibutuhkan (openpyxl, pypdf)...
pip install -r requirements.txt

echo Mengompilasi data awal dari file Excel & PDF...
python scripts\parse_data.py

echo =====================================================================
echo [SUKSES] Setup selesai! Anda bisa menjalankan run_server.bat sekarang.
echo =====================================================================
pause

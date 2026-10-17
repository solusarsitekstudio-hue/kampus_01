@echo off
setlocal EnableExtensions
chcp 65001 >nul
TITLE Setup SIAK-KAPRODI Environment
cd /d "%~dp0"
echo =====================================================================
echo  MENYIAPKAN ENVIRONMENT & DEPENDENSI PYTHON
echo =====================================================================
echo  Root Proyek : %CD%

REM --- Interpreter: pakai .venv kalau ada, kalau tidak Python sistem ---
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

%PY% --version
if errorlevel 1 (
    echo [ERROR] Python tidak terdeteksi di PATH system!
    pause
    exit /b 1
)

%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Butuh Python 3.10 atau lebih baru.
    pause
    exit /b 1
)

echo.
echo [1/3] Menginstall dependensi Python (openpyxl, pypdf, playwright, numpy, edge-tts)...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Gagal install dependensi Python.
    pause
    exit /b 1
)

echo.
echo [2/3] Mengunduh browser Chromium untuk Playwright...
%PY% -m playwright install chromium
if errorlevel 1 (
    echo [WARN] Gagal install Chromium. Fitur PDF On-Demand & Video akan error.
    echo        Jalankan ulang: %PY% -m playwright install chromium
)

echo.
echo [3/3] Mengompilasi data awal dari file Excel & PDF...
if exist "data\academic_data.json" (
    echo [SKIP] data\academic_data.json sudah ada, tidak ditimpa.
) else (
    %PY% scripts\parse_data.py
    if errorlevel 1 (
        echo [ERROR] Gagal parse data. Periksa sumber Excel/PDF di scripts\parse_data.py
        pause
        exit /b 1
    )
)

echo.
echo =====================================================================
echo [SUKSES] Setup selesai! Jalankan run_server.bat sekarang.
echo =====================================================================
pause
endlocal
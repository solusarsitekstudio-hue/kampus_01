@echo off
setlocal EnableExtensions
chcp 65001 >nul
TITLE Run SIAK-KAPRODI Arsitektur Intelligence Server
cd /d "%~dp0"
set PORT=40404

echo =====================================================================
echo  SIAK-KAPRODI ARSITEKTUR INTELLIGENCE SYSTEM
echo =====================================================================
echo  Root Proyek : %CD%

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo Mengecek dependensi data...
if not exist "data\academic_data.json" (
    echo [INFO] academic_data.json belum ada, mengompilasi dari Excel + PDF...
    %PY% scripts\parse_data.py
    if errorlevel 1 (
        echo [ERROR] Gagal parse data. Master dataset TIDAK berubah.
        pause
        exit /b 1
    )
) else (
    echo [OK] data\academic_data.json ditemukan.
)

echo.
echo Membuka browser ke http://localhost:%PORT% ...
REM Tunggu server siap dulu, kalau tidak user lihat ERR_CONNECTION_REFUSED
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start "" http://localhost:%PORT%"

echo Menjalankan Web Server di port %PORT%...
%PY% server.py
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo [ERROR] Server berhenti dengan kode %RC%.

pause
endlocal
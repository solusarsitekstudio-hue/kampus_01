@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
TITLE SIAK-KAPRODI (Arsitektur Intelligence System)
cd /d "%~dp0"
set PORT=40404

echo =====================================================================
echo  [SISTEMBUILD] MENJALANKAN SIAK-KAPRODI SERVER (PORT %PORT%)
echo =====================================================================
echo  Direktori Kerja: %CD%

REM 1. Deteksi Python Interpreter
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

REM 2. Cek Data Master
if not exist "data\academic_data.json" (
    echo [INFO] academic_data.json belum ada. Membangun dari tree kurikulum...
    %PY% scripts\parse_data.py
    if errorlevel 1 (
        echo [ERROR] Gagal kompilasi data master!
        pause
        exit /b 1
    )
) else (
    echo [OK] Dataset master academic_data.json terverifikasi siap.
)

REM 3. Launcher Browser Chrome (Maximized di Desktop Interaktif)
echo.
echo [BROWSER] Membuka antarmuka dashboard ke http://localhost:%PORT% ...
start "" /b cmd /c "ping 127.0.0.1 -n 3 >nul & start "" chrome --start-maximized http://localhost:%PORT% || start "" http://localhost:%PORT%"

REM 4. Jalankan Server Utama
echo [SERVER] Memulai Threaded HTTP/1.1 Server pada port %PORT%...
%PY% server.py
set RC=%ERRORLEVEL%
if not "%RC%"=="0" echo [ERROR] Server berhenti dengan kode status %RC%.

pause
endlocal

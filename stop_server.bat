@echo off
TITLE Stop SIAK-KAPRODI Server
set PORT=40404

echo =====================================================================
echo  MENGHENTIKAN SERVER SIAK-KAPRODI (PORT %PORT%)
echo =====================================================================

set FOUND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /R /C:":%PORT% *LISTENING"') do (
    set FOUND=1
    echo Menemukan proses server dengan PID %%a di port %PORT%...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 0 (
        echo [OK] Proses PID %%a berhasil dihentikan.
    ) else (
        echo [FAIL] Gagal mematikan proses %%a.
    )
)

if "%FOUND%"=="0" (
    echo Tidak ada proses aktif yang berjalan di port %PORT%.
) else (
    echo [SUKSES] Semua service di port %PORT% telah bersih.
)

echo =====================================================================
echo Selesai.
timeout /t 3

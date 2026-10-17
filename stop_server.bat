@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
TITLE Stop SIAK-KAPRODI Server
cd /d "%~dp0"
set PORT=40404

echo =====================================================================
echo  MENGHENTIKAN SERVER SIAK-KAPRODI (PORT %PORT%)
echo =====================================================================

set FOUND=0
REM Filter hanya baris LISTENING milik 127.0.0.1 / 0.0.0.0 pada port ini.
REM Dulu: findstr /R /C:":%PORT% *LISTENING" juga cocok ke baris IPv6 [::]:40404
REM sehingga token=5 bisa jadi PID 0 / System.
for /f "tokens=5" %%a in ('netstat -ano -p TCP ^| findstr /R /C:"[ ]%PORT%[ ].*LISTENING"') do (
    set "PIDNUM=%%a"
    if not "!PIDNUM!"=="0" (
        echo Menemukan proses dengan PID !PIDNUM! di port %PORT%...
        REM /T = matikan juga anak prosesnya (Chromium dari Playwright)
        taskkill /F /T /PID !PIDNUM! >nul 2>&1
        if errorlevel 1 (
            echo [WARN] Gagal mematikan PID !PIDNUM!.
        ) else (
            echo [OK] PID !PIDNUM! berhasil dihentikan.
        )
        set FOUND=1
    )
)

if "%FOUND%"=="0" (
    echo Tidak ada proses aktif yang berjalan di port %PORT%.
) else (
    echo [SUKSES] Semua service di port %PORT% telah bersih.
)

echo =====================================================================
echo Selesai.
timeout /t 4 /nobreak >nul
pause
endlocal
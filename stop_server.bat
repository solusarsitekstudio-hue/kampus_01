@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
TITLE Stop SIAK-KAPRODI Server
cd /d "%~dp0"
set PORT=40404

echo =====================================================================
echo  [SISTEMBUILD] MENGHENTIKAN SERVER SIAK-KAPRODI (PORT %PORT%)
echo =====================================================================

set FOUND=0
REM Filter hanya baris LISTENING milik 127.0.0.1 / 0.0.0.0 pada port ini.
for /f "tokens=5" %%a in ('netstat -ano -p TCP ^| findstr /R /C:"[ ]%PORT%[ ].*LISTENING"') do (
    set "PIDNUM=%%a"
    if not "!PIDNUM!"=="0" (
        echo Menemukan proses aktif dengan PID !PIDNUM! di port %PORT%...
        REM /T = matikan juga anak prosesnya secara tuntas (zero zombie process)
        taskkill /F /T /PID !PIDNUM! >nul 2>&1
        if errorlevel 1 (
            echo [WARN] Gagal mematikan PID !PIDNUM!.
        ) else (
            echo [OK] PID !PIDNUM! berhasil dihentikan secara bersih.
        )
        set FOUND=1
    )
)

if "%FOUND%"=="0" (
    echo [INFO] Tidak ada proses aktif yang berjalan di port %PORT%.
) else (
    echo [SUKSES] Semua service di port %PORT% telah bersih dan siap dijalankan ulang.
)

echo =====================================================================
echo Selesai.
ping 127.0.0.1 -n 4 >nul
endlocal

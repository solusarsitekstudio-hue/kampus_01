@echo off
title PUSH SIAK-KAPRODI KE GITHUB
color 0E
cls
echo =========================================================================
echo   SIAK-KAPRODI ENTERPRISE v2.6 -- GITHUB PUSH LAUNCHER
echo =========================================================================
echo.
echo Sedang mengunggah branch 'main' ke:
echo https://github.com/solusarsitekstudio-hue/kampus_01.git
echo.
echo * JIKA MUNCUL JENDELA LOGIN GITHUB:
echo   Silakan klik "Sign in with your browser" untuk otorisasi sekali klik.
echo.
echo =========================================================================
echo.

cd /d "e:\WORKSPACE\KAMPUS_01"
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================================================
    echo   [BERHASIL] Seluruh kode SIAK-KAPRODI sukses terunggah ke GitHub!
    echo =====================================================================
    echo.
    echo Menjalankan auto-release static showcase ke branch gh-pages...
    call "DEPLOY_GHPAGES.bat"
) else (
    echo.
    echo =====================================================================
    echo   [PERINGATAN] Push belum selesai. Jika butuh login manual,
    echo   silakan masukkan kredensial atau gunakan Personal Access Token.
    echo =====================================================================
)

echo.
echo Tekan sembarang tombol untuk menutup jendela ini...
pause >nul

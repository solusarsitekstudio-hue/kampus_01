@echo off
title SIAK-KAPRODI - DEPLOY GITHUB PAGES (TRACK 1)
color 0A
cls

echo ==============================================================================
echo [SIAK-KAPRODI] 1-CLICK DEPLOY STATIC SHOWCASE TO GITHUB PAGES (TRACK 1)
echo ==============================================================================
echo.

:: 1. Periksa remote Git
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [PERINGATAN] Remote 'origin' belum terpasang di repositori ini.
    echo.
    echo [PANDUAN SETUP AWAL]:
    echo 1. Buat repository kosong di GitHub: https://github.com/new
    echo    (Contoh nama: siak-kaprodi)
    echo 2. Buka terminal di folder ini dan jalankan perintah:
    echo    git remote add origin https://github.com/USERNAME_ANDA/siak-kaprodi.git
    echo 3. Jalankan kembali DEPLOY_GHPAGES.bat ini!
    echo.
    echo ==============================================================================
    pause
    exit /b 1
)

echo [LANGKAH 1/4] Mengompilasi bundle static showcase (Freeze 19 Endpoints)...
python scripts\export_static_showcase.py
if errorlevel 1 (
    echo [ERROR] Gagal mengompilasi bundle static showcase!
    pause
    exit /b 1
)
echo.

echo [LANGKAH 2/4] Verifikasi kelengkapan berkas bundle...
python tests\test_static_exporter.py
if errorlevel 1 (
    echo [ERROR] Verifikasi bundle gagal!
    pause
    exit /b 1
)
echo.

echo [LANGKAH 3/4] Mendorong pembaruan ke branch main...
git add .
git commit -m "chore: update showcase bundle and documentation" >nul 2>&1
git push origin main
echo [OK] Branch main berhasil diperbarui!
echo.

echo [LANGKAH 4/4] Mendorong folder dist_gh_pages ke branch gh-pages...
git subtree push --prefix dist_gh_pages origin gh-pages
if errorlevel 1 (
    echo [INFO] Subtree push biasa gagal (mungkin branch remote belum ada). Mencoba force split...
    git push origin `git subtree split --prefix dist_gh_pages main`:gh-pages --force
)

echo.
echo ==============================================================================
echo [SUCCESS] DEPLOY GITHUB PAGES SELESAI!
echo Showcase Anda akan aktif dalam 1-2 menit di GitHub Pages.
echo ==============================================================================
echo.
pause

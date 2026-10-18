@echo off
REM ============================================================================
REM build_tailwind.bat - Bangun CSS Tailwind statis untuk SIAK-KAPRODI
REM ----------------------------------------------------------------------------
REM TAHAP C-1: dashboard tidak lagi memakai JIT compiler Tailwind di browser.
REM CSS-nya dibangun SEKALI di sini (30-70 KB), lalu halaman memuat file statis.
REM
REM Butuh Node.js/npm (hanya saat build). Setelah selesai, runtime 100%% offline.
REM Hasil: public\vendor\tailwind.css
REM
REM Jalankan ulang script ini setiap kali menambah/mengubah class Tailwind
REM di public\index.html atau public\app.js.
REM ============================================================================
setlocal
cd /d "%~dp0.."
chcp 65001 >nul

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm tidak ditemukan. Pasang Node.js dulu: https://nodejs.org
  exit /b 1
)

set "BUILD_DIR=scratch\vendor_build"
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

echo [1/3] Menyiapkan folder build...
copy /y "scripts\tailwind\tailwind.config.js" "%BUILD_DIR%\tailwind.config.js" >nul
copy /y "scripts\tailwind\input.css"           "%BUILD_DIR%\input.css"           >nul
if not exist "%BUILD_DIR%\package.json" (
  > "%BUILD_DIR%\package.json" echo {"private":true,"name":"siak-vendor-build"}
)

echo [2/3] Memasang tailwindcss@3.4.17 ^(sekali saja, ~15 MB^)...
pushd "%BUILD_DIR%"
call npm install --no-audit --no-fund tailwindcss@3.4.17
if errorlevel 1 (
  echo [ERROR] npm install gagal. Periksa koneksi internet.
  popd & exit /b 1
)

echo [3/3] Mengompilasi CSS...
call npx tailwindcss -c tailwind.config.js -i input.css -o "..\..\public\vendor\tailwind.css" --minify
set "RC=%ERRORLEVEL%"
popd

if not "%RC%"=="0" (
  echo [ERROR] Kompilasi Tailwind gagal.
  exit /b %RC%
)

for %%F in ("public\vendor\tailwind.css") do echo [OK] public\vendor\tailwind.css -^> %%~zF bytes
echo [OK] Selesai. Jalankan ulang bila ada class Tailwind baru.
exit /b 0

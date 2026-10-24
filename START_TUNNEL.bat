@echo off
title SIAK-KAPRODI - CLOUDFLARE SECURE TUNNEL (TRACK 2)
color 0B
cls

echo ==============================================================================
echo [SIAK-KAPRODI] CLOUDFLARE SECURE QUICK TUNNEL LAUNCHER (TRACK 2)
echo ==============================================================================
echo.

set "BIN_DIR=%~dp0bin"
set "CLOUDFLARED=%BIN_DIR%\cloudflared.exe"

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

if not exist "%CLOUDFLARED%" (
    echo [INFO] cloudflared.exe belum ditemukan di folder bin\.
    echo [INFO] Mengunduh cloudflared.exe resmi dari Cloudflare Releases...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe', '%CLOUDFLARED%')"
    if not exist "%CLOUDFLARED%" (
        echo [ERROR] Gagal mengunduh cloudflared.exe secara otomatis.
        echo [SOLUSI] Unduh manual dari https://github.com/cloudflare/cloudflared/releases
        echo          dan simpan sebagai: %CLOUDFLARED%
        pause
        exit /b 1
    )
    echo [OK] cloudflared.exe berhasil diunduh!
    echo.
)

echo [STATUS] Menghubungkan server lokal (http://127.0.0.1:40404) ke internet...
echo [INFO] Domain publik HTTPS instan (*.trycloudflare.com) akan muncul di bawah.
echo [INFO] Bagikan link tersebut ke Yayasan, Dekanat, atau buka langsung dari HP!
echo.
echo ==============================================================================

"%CLOUDFLARED%" tunnel --url http://127.0.0.1:40404
pause

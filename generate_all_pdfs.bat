@echo off
setlocal EnableExtensions
chcp 65001 >nul
TITLE Generator Paket PDF Resmi SIAK-KAPRODI Arsitektur
cd /d "%~dp0"
echo =====================================================================
echo  GENERATOR DOKUMEN PDF RESMI ARSITEKTUR (4 PAKET DOKUMEN)
echo =====================================================================
echo  1. PDF 1A: Rekap Kehadiran Mahasiswa Bulanan (Wali Murid)
echo  2. PDF 1B: Rapor Akhir Semester & Matriks Karier (Wali Murid)
echo  3. PDF 2:  Laporan Penilaian Master Gradebook (Kaprodi Landscape)
echo  4. PDF 3:  Laporan Evaluasi Akuntabilitas Dosen & Modul RPS (Untuk Dosen)
echo =====================================================================
echo  Root Proyek : %CD%

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

%PY% scripts\generate_pdfs.py
if errorlevel 1 (
    echo.
    echo =====================================================================
    echo [GAGAL] Generate PDF gagal. Dokumen lama TIDAK diubah.
    echo =====================================================================
    pause
    exit /b 1
)

echo.
echo =====================================================================
echo [SUKSES] Dokumen PDF tersimpan di: output\[MATA_KULIAH]\[TIMESTAMP]\
echo         Salinan live preview : generated_pdfs\
echo =====================================================================
pause
endlocal
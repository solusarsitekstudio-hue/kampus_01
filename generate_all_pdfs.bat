@echo off
TITLE Generator Paket PDF Resmi SIAK-KAPRODI Arsitektur
echo =====================================================================
echo  GENERATOR DOKUMEN PDF RESMI ARSITEKTUR (4 PAKET DOKUMEN)
echo =====================================================================
echo  1. PDF 1A: Rekap Kehadiran Mahasiswa Bulanan (Wali Murid)
echo  2. PDF 1B: Rapor Akhir Semester & Ranking Afirmatif (Wali Murid)
echo  3. PDF 2:  Laporan Penilaian Master Gradebook 35 Mhs (Kaprodi Landscape)
echo  4. PDF 3:  Laporan Evaluasi Akuntabilitas Dosen & Modul RPS (Untuk Dosen)
echo =====================================================================

python scripts\generate_pdfs.py

echo.
echo =====================================================================
echo [SUKSES] Dokumen PDF tersimpan di folder: generated_pdfs\
echo =====================================================================
pause

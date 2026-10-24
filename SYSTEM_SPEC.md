# ⚙️ SYSTEM SPECIFICATION: SYS_KAMPUS_01

- **System ID:** `SYS_KAMPUS_01`
- **Nama Sistem:** SIAK-KAPRODI (Arsitektur Intelligence & Executive Yayasan Cockpit)
- **Tipe Sistem:** Executive Web Dashboard, Modular Radar Competency Engine, Multi-Media PDF/Video Portofolio Suite
- **Port Alokasi:** `40404` (Wajib, terproteksi oleh `BIOS.md`)
- **URL Akses Lokal:** `http://127.0.0.1:40404` (atau `http://localhost:40404`)
- **Entry Point Server:** `server.py` (HTTP/1.1 Threaded socketserver, Byte-Range 206 support)
- **Launcher BAT:** `1_RUN_SERVER.bat` (Launcher utama, auto-minimize CMD + pop Chrome maximized)
- **Killer BAT:** `STOP_SERVER.bat` (Taskkill PID port 40404 tuntas, zero zombie process)
- **Runtime Environment:** Python 3.11+ / Windows PowerShell / UTF-8
- **UI Framework & Vendors:** Vanilla JS (ES6+), Tailwind CSS 3.4, ApexCharts 3.45, Lucide Icons
- **Status Katalog:** Tercatat resmi via skill `update-data-automasi`
- **Dependensi Kunci:** `reportlab`, `playwright`, `ffmpeg` (binary), `http.server`, `socketserver`

---

## 🗄️ ANATOMI DATA & ENGINE
- **Dataset Master:** `data/academic_data.json` (35 Mahasiswa, Rata-rata 77.7, Kehadiran 85.8%, 5 At-Risk)
- **Katalog MK:** `data/courses/*.json` (35 Mata Kuliah dalam pohon kurikulum bertingkat)
- **Pohon Kurikulum:** `data/kurikulum/ARSITEKTUR/<TA>/<SEMESTER>/<KUNCI_MK>/`
- **Konfigurasi Satu Sumber:** `config/aturan.json` & `config/identitas.json`
- **Output Dokumen PDF:** `output/<KUNCI_MK>/<TIMESTAMP>/` dan `generated_pdfs/`
- **Output Video 9:16:** `public/videos/video_portofolio_<NPM>.mp4`

---

## 📑 10 TAB RESMI ANTARMUKA (UI SECTIONS)
1. `section-kaprodi` : Cockpit Eksekutif Yayasan & Analisis Keuangan SPP (LTV Rp 1.17M, Churn Rp 195M)
2. `section-wali` : Center of the Universe (4-Layer Radar Switcher, Gamified Badges, Top Career Anchor)
3. `section-marketing` : DeckCraft Presentation Suite 16:9 & Video Vertikal 9:16 FFmpeg
4. `section-whatsapp` : Parent Pride Loop (3 Persona Adaptive Chat: Vanguard, Steady Builder, Turnaround)
5. `section-pengaturan` : Parameter Ambang At-Risk, Jam Teori/Studio, Dosen Pengampu & Asisten
6. `section-kurikulum` : Editor Pohon Kurikulum 16 Pertemuan RPS & Rebuild Trigger
7. `section-info` : Dokumentasi Metodologi & Transparansi Rumus Terbobot
8. `section-rekap` : Rollup Agregasi Periode Lintas MK (Level 3 Semester & Level 4 Sepanjang Kuliah)
9. `section-portofolio` : Pusat Unduh Dokumen PDF 4-Lapis & Portofolio Arsitektur
10. `section-engine` : Diagnostik Pemeriksa Input SHA-256 & Audit Integritas Output

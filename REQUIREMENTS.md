# REQUIREMENTS & SPESIFIKASI SISTEM
## SIAK-KAPRODI: Sistem Intelijen Akademik & Rekap Portofolio Arsitektur

Dokumen ini memuat daftar kebutuhan teknis, dependensi perangkat lunak, konfigurasi jaringan/port, serta prasyarat lingkungan untuk menjalankan sistem.

---

### 1. Spesifikasi Perangkat Lunak (Software Stack)
* **Runtime**: Python 3.10+ (Terverifikasi di Python 3.14.7)
* **Web UI Engine**: Vanilla HTML5, CSS3 Modern, Tailwind CSS (CDN), ApexCharts (CDN), Lucide Icons (CDN)
* **Web Server**: Native Python `socketserver` + `http.server` (Zero-bloat, tanpa server eksternal seperti Apache/Nginx untuk lokal)
* **Data Processing Libraries**:
  * `openpyxl`: Membaca format tabular portal kampus (`DAFTAR MAHASISWA.xlsx`)
  * `pypdf`: Mengekstrak silabus dan rekap log asistensi praktikum (`02 rekap qs pratikum.pdf`)

---

### 2. Konfigurasi Port & Jaringan
* **Port Standar**: `40404` (Khusus instance SIAK-KAPRODI)
* **Base URL**: `http://localhost:40404`
* **Protokol**: HTTP/1.1 RESTful JSON API
* **Endpoint API Utama**:
  * `GET /api/data`: Mengambil kompilasi penuh data akademik kelas, silabus, absensi, KPI, dan rekap mahasiswa.
  * `GET /api/student/<npm>`: Mengambil data mendalam 1 individu mahasiswa (profil, radar chart, SWOT AI, carousel, video script, pesan WhatsApp).

---

### 3. Struktur Direktori Proyek
```text
e:\WORKSPACE\KAMPUS_01\
├── data/
│   └── academic_data.json      # Dataset kompilasi hasil parsing & inferensi
├── public/
│   ├── index.html              # Antarmuka Dashboard Interaktif Utama
│   ├── app.js                  # Frontend Controller, Chart rendering, State management
│   └── style.css               # Styling custom, Glassmorphism & layout cetak
├── scripts/
│   └── parse_data.py           # Parser data Excel & PDF ke JSON terstruktur
├── .gitignore                  # Konfigurasi ignore file Git
├── README.md                   # Dokumentasi resmi proyek
├── REQUIREMENTS.md             # Dokumen kebutuhan teknis (file ini)
├── requirements.txt            # Daftar paket pip
├── WORKFLOW_MAPPING.md         # Peta alur kerja & arsitektur sistem
├── run_server.bat              # Script start server port 40404 & buka browser
├── stop_server.bat             # Script kill proses di port 40404
└── setup.bat                   # Script instalasi otomatis dependensi
```

---

### 4. Sumber Data Validasi (Ground Truth Data)
1. **Daftar Mahasiswa**: `D:\Desktop\- HAL LAIN\DAFTAR MAHASISWA.xlsx` (35 Mahasiswa Program Studi Arsitektur / TEK)
2. **Syllabus & Rekap Praktikum**: `D:\Desktop\- HAL LAIN\kirim\02 rekap qs pratikum.pdf` (6 Sesi Praktikum AutoCAD, Gambar Kerja, dan Quantity Surveying)
3. **Penyelenggara Perkuliahan**:
   * Program Studi: Arsitektur / Teknik Ekonomi Konstruksi
   * Ketua Program Studi: Fielda Roza, S.T., M.T.
   * Dosen Pengasuh: Aprilia Yunita, S.T., M.T. & Duddy Fajriansyah, S.T., M.T.
   * Asisten Dosen: Adrian Ridhoa, S.T.
   * Mata Kuliah: 5412522233 - Aplikasi Komputer (AutoCAD & Gambar Kerja)

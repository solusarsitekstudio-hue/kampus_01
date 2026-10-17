# 🏛️ SIAK-KAPRODI: Sistem Intelijen Akademik & Rekap Portofolio Arsitektur
> **Golden Demo v2.5** — Platform Otomasi Akademik, Rapor Interaktif & Pemetaan 10 Karier Masa Depan, Slide Deck Portofolio Arsitektur, serta Generator Dokumen PDF On-Demand untuk Program Studi Arsitektur.

---

## 📐 Metodologi & Aturan Resmi Sistem

Bagian ini adalah **sumber kebenaran tunggal**. Semua angka di dashboard, PDF, dan
pesan wali murid berasal dari sini — bukan dari teks yang diketik manual.

### 1. Perhitungan Nilai (Rata-rata TERBEBOT)

```
Nilai Akhir = Σ (Skor Sesi × Bobot Sesi) / Σ Bobot Sesi
Bobot: 15 / 15 / 15 / 20 / 15 / 20  (total 100)
```

* **Alpha bernilai 0 dan DIHITUNG** sebagai bagian dari rata-rata.
  Mahasiswa yang tidak hadir **tidak** mendapat nilai gratis.
* Sesi **Sakit** dan **Izin** tetap dinilai 70–85 (student tetap berkarya).
Sebelumnya kode memakai `valid_scores = [sc for sc in session_scores if sc > 0]`
  yang membuang nilai 0, sehingga mahasiswa dengan Alpha tidak kehilangan nilai.
* Kolom nilai Transparency: `akademik.nilai_rata_rata` (terbobot),
  `akademik.nilai_rata_sederhana` (rata-rata biasa) — untuk audit.

### 2. Predikat Grade

| Grade | Syarat | Arti |
|---|---|---|
| **A** | rata-rata ≥ 85 **dan** kehadiran ≥ 80% | Kompeten Unggul |
| **A-** | rata-rata ≥ 80 **dan** kehadiran ≥ 75% | Kompeten Sangat Baik |
| **B+** | rata-rata ≥ 75 **dan** kehadiran ≥ 75% | Kompeten Baik |
| **B** | rata-rata ≥ 70 | Kompeten Cukup |
| **C** | rata-rata ≥ 60 | Kurang (Perlu Bimbingan Intensif) |
| **D / Evaluasi** | rata-rata < 60 | Kritis (Rentan Evaluasi) |

### 3. Deteksi Dini At-Risk (ATURAN SATU-SATUNYA)

```
At-Risk  ⇔  (Alpha ≥ 2x)  ATAU  (Kehadiran < 75%)
```

> ⚠️ **Tidak ada lagi aturan lain.** Sebelumnya sistem punya 4 aturan berbeda
> dalam 1 aplikasi (KPI dashboard = 1 orang, README = 10 orang, badge tabel
> = alpha saja, PDF wali = "maksimal 3x alpha"). Sekarang fungsi
> `is_at_risk()` di `scripts/parse_data.py` adalah satu-satunya sumber, dan
> hasilnya disimpan per mahasiswa sebagai `at_risk` + `alasan_at_risk`.
> Dashboard, badge tabel, PDF Gradebook, dan PDF Audit membacanya dari sana.

### 4. Badge Kecocokan Karier (dihitung, bukan diketik)

| Skor | Kategoria | Warna |
|---|---|---|
| ≥ 95% | Sangat Tinggi | Hijau |
| ≥ 85% | Tinggi | Cyan |
| ≥ 70% | Sedang | Amber |
| < 70% | Rendah | Merah |

> Badge, warna bar, dan lebar bar **selalu berasal dari satu angka** yang sama.
> Sebelumnya tiap baris matriks karier punya kategori yang diketik manual
> sehingga bisa muncul "Sangat Tinggi" untuk skor 67%.

### 5. Zero Competitive Ranking — DIHORMATI SEPENUHNYA

Portal wali murid **dan** PDF Gradebook Kaprodi **tidak memuat peringkat**.
Tabel disortir berdasarkan NPM; kolom pertama adalah nomor urut absen resmi.
Tidak ada dokumen yang menampilkan peringkat mahasiswa.

---

## 📊 Angka Ril Demo Saat Ini (build `2026-10-18_04-12`)

| Metrik | Nilai |
|---|---|
| Total Mahasiswa | 35 |
| Rata-rata Kehadiran | 83.3% |
| Rata-rata Nilai Studio | **80.6** (predikat dominan A-, 19 mahasiswa) |
| Mahasiswa At-Risk | **10** (1 berdasarkan alpha, 10 berdasarkan kehadiran) |
| Distribusi Grade | A=3, A-=19, B+=0, B=10, C=2, D=1 |
| Tingkat Kelulusan | 71.4% (25 lulus / 10 perlu pendampingan) |

### 3 Kasus Studi (angka terbaru)

1. 🌟 **M Yazid Zidane Mulyadi (NPM 2510015410010)**
   * Kehadiran 100%, Grade A (94.2), Indeks Kesiapan 92.3%.
   * Cocok untuk BIM Modeler & Architectural Designer.
2. ⚠️ **Rozi Andrian Surva (NPM 2510015410011)**
   * Kehadiran 50% (3/6), **2x Alpha**, 1x Sakit.
   * **Grade D / Evaluasi (44.5)** — bobot 0 pada sesi Alpha menurunkan
     nilai secara signifikan. Teridentifikasi At-Risk.
   * Tujuan utama: demonstrate how the system **menjaga martabat** —
     tetap fokus pada talenta, dengan panduan pendampingan orang tua yang hangat.
3. ✨ **Alsa Dmi Yesya Putri (NPM 2510015410001)**
   * Kehadiran 83.3%, Grade A (91.7), izin delegasi lomba arsitektur.

---

## 🌟 Latar Belakang & Nilai Strategis
Sistem ini dirancang khusus untuk memecahkan beban administratif Ketua Program Studi (Kaprodi) dan Dosen, sekaligus mengubah data perkuliahan menjadi aset komunikasi bermartabat ke wali murid dan instrumen publikasi berkualitas tinggi bagi institusi kampus.

Sistem mengintegrasikan **4 Pilar Utama**:
1. **Pilar Presensi & Rekap Bulanan**:
   * Rekap absensi bulanan 35 mahasiswa lengkap per kelas dan per individu.
   * Pencatatan tanggal sesi, mata kuliah, status (Hadir, Sakit, Izin, Alpha), serta alasan ketidakhadiran otentik.
   * Deteksi dini mahasiswa berisiko (*At-Risk Intervention*) bagi yang memiliki Alpha $\ge 2$x atau kehadiran $< 75\%$.
   * Dilengkapi grafik web interaktif: Donut Progress Ring dan Bar Chart 6 Sesi Pertemuan dengan garis patokan Benchmark Kelas (83.3%).
2. **Pilar Rapor Interaktif & Pemetaan 10 Karier Masa Depan (Wali Murid)**:
   * **Zero Competitive Ranking**: Menghapus sistem ranking kompetitif kelas (seperti `#35 / 35`) untuk melindungi martabat mahasiswa dan perasaan wali murid. Digantikan dengan **Status Kompetensi**, **Indeks Kesiapan Profesi (%)**, dan **Predikat Capaian Individu**. Berlaku juga untuk **PDF Gradebook Kaprodi** — tabel disortir by NPM, kolom pertama = nomor absen.
   * **Visualisasi Spider-Web Radar 5 Dimensi**: Mengukur 5 pilar arsitektur (*AutoCAD*, *Detail & Presisi*, *Kedisiplinan Asistensi*, *Logika Ruang & Struktur*, dan *Manajemen Waktu*) dengan jaring laba-laba konsentris (20%, 40%, 60%, 80%, 100%).
   * **Diagnosis AI Mendalam (4 Kuadran Narasi)**:
     1. *Karakter Spasial & Etos Kerja Studio*
     2. *Proyeksi Potensi Perkembangan Kedepan*
     3. *Catatan Khusus Penguatan Mahasiswa*
     4. *Panduan Khusus Pendampingan Wali Murid di Rumah*
   * **Matriks 10 Rekomendasi Profesi Riil Masa Depan**: Analisis kecocokan talenta ke 10 profesi nyata industri (Architectural Designer, BIM Modeler & Coordinator, Quantity Surveyor, Detail Engineering Drawing Specialist, Interior Architect, 3D Architectural Visualizer, Site Architect, Landscape Architect Assistant, Green Building Specialist, Project Planner/Kontraktor Mandiri) lengkap dengan persentase skor, badge kecocokan, keterampilan kunci, dan langkah aksi riil.
3. **Pilar Portofolio Digital Slide Deck 16:9 (DeckCraft Visual Engine)**:
   * Menggantikan format carousel media sosial yang kaku menjadi **Dokumen Portofolio Slide Deck Widescreen 16:9** berstandar sayembara arsitektur:
     * *Slide 1*: Cover Progres & Identitas Mahasiswa
     * *Slide 2*: Matriks Layer CAD, Lineweight & Standar IAI
     * *Slide 3*: Karya Denah Arsitektur Skala 1:100 Lengkap dengan Notasi & Dimensi
     * *Slide 4*: Sertifikasi Kompetensi Resmi Studio Berstempel Emas Kaprodi
   * Dilengkapi penampil **Fullscreen Interaktif di Web** serta simulasi **Mockup Video Vertikal 9:16 (Shorts/Reels/WhatsApp Story)** dengan narasi AI untuk media sosial.
4. **Pilar Dispatcher WhatsApp & On-Demand PDF Stream**:
   * Generator pesan resmi sopan siap kirim ke nomor orang tua via WhatsApp Web dengan **3 Lampiran Berkas PDF Resmi Terverifikasi**.
   * Terintegrasi dengan engine rendering dokumen on-demand yang langsung menghasilkan file PDF sinkron secara instan.

---

## 📂 Sumber Data Riil (Ground Truth)
Sistem ini disimulasikan menggunakan data autentik perkuliahan:
* **Daftar Mahasiswa**: `D:\Desktop\- HAL LAIN\DAFTAR MAHASISWA.xlsx` (35 Mahasiswa Kelas TEKZA).
* **Silabus & Log Praktikum**: `D:\Desktop\- HAL LAIN\kirim\02 rekap qs pratikum.pdf`
  * Mata Kuliah: `5412522233 - Aplikasi Komputer (AutoCAD & Gambar Kerja Arsitektur)`
  * Semester: `Genap 2025/2026` • Ruang: `Lab LIKDA`
  * Ketua Prodi Arsitektur: `Fielda Roza, S.T., M.T.`
  * Dosen Pengasuh: `Aprilia Yunita, S.T., M.T.` & `Duddy Fajriansyah, S.T., M.T.`
  * Asisten Dosen: `Adrian Ridhoa, S.T.`

---

## ⚡ Cara Menjalankan Aplikasi

### 1. Menjalankan Server & Buka Dashboard
Cukup klik ganda (double-click) file batch:
```cmd
run_server.bat
```
* Server lokal akan aktif di port **`40404`**.
* Browser akan otomatis membuka alamat: **`http://localhost:40404`**.

### 2. Menghentikan Server
Jika ingin mematikan server secara bersih tanpa meninggalkan proses menggantung:
```cmd
stop_server.bat
```

### 3. Setup Ulang Dependensi & Kompilasi Data
```cmd
setup.bat
```

### 4. Memproses Input Baru & Mengompilasi Dokumen
```cmd
process_input.bat
```

---

## 🗺️ Peta Studi Kasus Demo
Untuk kemudahan demonstrasi di depan Kaprodi, gunakan tombol demo cepat di pojok kanan atas:
1. 🌟 **M Yazid Zidane Mulyadi (NPM 2510015410010)**:
   * Profil mahasiswa unggul (Kompeten Unggul), Kehadiran 100%, Grade A (94.2).
   * Contoh ideal untuk meninjau pemetaan profesi BIM Modeler (96.5%) dan Architectural Designer (93.3%).
2. ⚠️ **Rozi Andrian Surva (NPM 2510015410011)**:
   * Profil mahasiswa yang membutuhkan pendampingan (2x Alpha + 1x Sakit, Kehadiran 50%), **Grade D / Evaluasi (44.5)**.
   * Menunjukkan bagaimana sistem **menjaga martabat mahasiswa di depan orang tua**: tidak ada label ranking terbawah (#35), melainkan difokuskan pada talenta imajinasi spasialnya (Site Architect 87.0%) dengan panduan pendampingan orang tua yang hangat dan suportif di rumah.
3. ✨ **Alsa Dmi Yesya Putri (NPM 2510015410001)**:
   * Profil mahasiswa kreatif konsisten, Kehadiran 83.3% (izin delegasi lomba arsitektur), Grade A (91.8).

---

## 📄 Generator Dokumen PDF Resmi & Fitur Live On-Demand

Sistem dilengkapi endpoint **Dynamic On-Demand PDF Generation** (`/api/pdf/download?type=<TYPE>&npm=<NPM>`) di `server.py` yang langsung membaca live dataset master `data/academic_data.json`.
* **100% Selalu Sinkron**: Setiap kali data diedit atau mata kuliah di-switch, dokumen langsung terbit sesuai kondisi terbaru tanpa delay atau berkas statis basi.
* **Mendukung Seluruh 35 Mahasiswa**: Siapa pun mahasiswa yang dipilih di dashboard langsung dapat diunduh dokumennya tanpa kendala 404.
* **Grafik Web Ditanamkan ke PDF ("Grafik Web")**: Seluruh grafik analitik vector SVG resolusi tinggi disematkan langsung di dalam dokumen:

### 1. Dokumen untuk Wali Murid (3 Jenis Berkas):
* **PDF 1A: Rekap Kehadiran Mahasiswa Bulanan** (`01_rekap_kehadiran_bulanan_*.pdf`):
  * Dikirim rutin tiap 1 bulan sekali ke orang tua.
  * Memuat kop resmi fakultas, ringkasan persentase kehadiran, 4 kartu metrik (Hadir, Sakit, Izin, Alpha).
  * **Grafik Web**: **Donut Progress Ring Kehadiran** (warna adaptif hijau/biru/merah) serta **6-Session Bar Chart** dengan pill status kehadiran dan garis putus-putus **Benchmark Kehadiran Kelas (83.3%)**.
  * Rincian log per sesi, catatan peraturan akademik, dan stempel verifikasi Kaprodi.
* **PDF 1B: Rapor Capaian Studio & Matriks 10 Karier Masa Depan** (`02_rapor_akhir_semester_*.pdf`):
  * Dikirim di akhir semester (2 Halaman Format A4 Portrait).
  * **Halaman 1**: Banner profil mahasiswa dengan Indeks Kesiapan, **Spider-Web Radar Chart 5 Pilar Arsitektur** (5 cincin jaring laba-laba konsentris, bebas clipping teks), tabel rincian nilai 6 sesi praktikum, **Grafik Batang Progress Capaian P1-P6**, serta **4 Kuadran Narasi AI Mendalam**.
  * **Halaman 2**: **Matriks 10 Rekomendasi Profesi Riil Masa Depan** (Tabel bergradien dengan visual progress bar kecocokan, badge kategori, pills keterampilan kunci, analisis potensi, dan langkah aksi konkrit).
* **PDF 1C: Slide Deck Portofolio Arsitektur Mahasiswa (DeckCraft)** (`05_deckcraft_portofolio_arsitektur_*.pdf`):
  * Dokumen presentasi arsitektur 4 halaman landscape 16:9 widescreen beresolusi tinggi.
  * Visualisasi teknis: 3D Axonometric Wireframe Villa, Tabel Ketebalan Garis CAD, Denah Arsitektur Skala 1:100 dengan dimensi & notasi ruang, serta Sertifikasi Resmi Berstempel Emas.

### 2. Dokumen untuk Kaprodi:
* **PDF 2: Laporan Penilaian Dosen & Master Gradebook 35 Mahasiswa** (`03_laporan_penilaian_kaprodi_master_gradebook.pdf`):
  * Format **A4 Landscape** eksekutif untuk rapat yudisium dan arsip akreditasi BAN-PT/LAM Teknik.
  * Memuat 5 kartu statistik makro kelas.
  * **Grafik Web Analitik Kelas**:
    1. **Tren Kehadiran Sesi 1 s.d. 6**: Stacked bar chart mahasiswa Hadir vs Absen.
    2. **Distribusi Grade Nilai Kelas**: Histogram sebaran grade nilai huruf (A, A-, B+, B, C, D) seluruh 35 mahasiswa.
  * Master Table 35 mahasiswa **terurut berdasarkan NPM** (tanpa peringkat) dengan log nilai per sesi berbobot dan status kelulusan. Angka kelulusan, predikat modus, dan jumlah at-risk dihitung dari data, bukan ditulis manual.

### 3. Dokumen untuk Dosen dari Kaprodi:
* **PDF 3: Laporan Evaluasi Dosen & Keselarasan Kurikulum / Modul RPS** (`04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf`):
  * Laporan audit mutu pengajaran (QA Dosen) dari Kaprodi kepada tim pengampu.
  * Realisasi presensi tim pengajar (100% terlaksana).
  * **Audit Kesesuaian Materi vs Modul RPS**: Evaluasi materi per sesi terhadap capaian CPMK/CPL dengan skor keselarasan rata-rata **96.0% (Terakreditasi Sangat Baik / Unggul)**.

---

## 🏛️ Penyesuaian Dinamis Multi-Mata Kuliah (Any Course Adaptability)
Sistem tidak terkunci hanya pada satu mata kuliah, melainkan dapat memproses dan menyajikan mata kuliah apa pun di jurusan Arsitektur:
* **Dropdown Pilih Mata Kuliah di Dashboard**: Kaprodi dapat berganti mata kuliah secara real-time langsung dari navigasi atas.
* **Katalog Mata Kuliah Tersedia**:
  1. `APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS` (AutoCAD, Layer IAI, dan Estimasi Volume QS).
  2. `STUDIO_PERANCANGAN_ARSITEKTUR_2` (Desain Rumah Tinggal, Analisis Tapak & Maket Studi).
  3. `STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1` (Pondasi Dangkal, Kolom Beton & Kuda-kuda Kayu).
* **CLI Parameter**: Jalankan `python scripts\process_input.py --course "<NAMA_MK>"` untuk memproses mata kuliah apa pun.

---

## 📥 Manajemen Folder INPUT & OUTPUT Terpadu
Sistem menerapkan tata kelola direktori dua arah yang simetris dan rapi:

```text
e:\WORKSPACE\KAMPUS_01\
│
├── input/                                       <-- DIREKTORI INPUT
│   ├── raw/                                     <-- Penangkapan Mentah (Raw Captures)
│   │   └── <NAMA_MATA_KULIAH>/
│   │       └── <TIMESTAMP_PENANGKAPAN>/         <-- Berkas mentah dari scraper / Kaprodi
│   │           ├── daftar_mahasiswa_raw.xlsx
│   │           └── rekap_presensi_modul_raw.pdf
│   │
│   └── processed/                               <-- Hasil Olahan Matang (Normalized)
│       └── <NAMA_MATA_KULIAH>/
│           └── <TIMESTAMP_PENANGKAPAN>/
│               ├── academic_data.json           <-- Dataset master terstruktur
│               └── input_manifest.json          <-- Log validasi & metadata input
│
├── output/                                      <-- DIREKTORI OUTPUT
│   ├── latest_run.json                          <-- Pointer global sesi generate terakhir
│   └── <NAMA_MATA_KULIAH>/
│       ├── latest_run.json
│       └── <TIMESTAMP_WAKTU_DIBIKIN>/           <-- Seluruh PDF resmi siap kirim
│           ├── 01_rekap_kehadiran_bulanan_*.pdf
│           ├── 02_rapor_akhir_semester_*.pdf
│           ├── 03_laporan_penilaian_kaprodi_master_gradebook.pdf
│           ├── 04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf
│           ├── 05_deckcraft_portofolio_arsitektur_*.pdf (16:9 Widescreen)
│           └── manifest.json                    <-- Katalog file & ukuran KB
│
├── process_input.bat                            <-- 1-Klik Ingest, Olah Input & Generate PDF
├── run_server.bat                               <-- Menjalankan Server (Port 40404)
└── stop_server.bat                              <-- Mematikan Server Bersih
```

---

## 🎬 Rencana Arsitektur Video Short Portofolio (9:16 Vertikal)
Untuk memaksimalkan kebanggaan wali murid dan daya jangkau promosi jurusan (Word-of-Mouth), fitur **Video Short Portofolio 9:16** dirancang dengan spesifikasi:
1. **Format Output**: Video vertikal 1080x1920 (9:16) MP4 durasi 30–35 detik, optimal untuk WhatsApp Status, Instagram Reels, dan YouTube Shorts.
2. **Sumber Aset Riil**:
   * Foto/screenshot karya asli mahasiswa (gambar denah AutoCAD, 3D render, foto maket/asistensi studio di PC).
   * Logo resmi kampus dan identitas nama mahasiswa + program studi.
3. **Pipeline Audio & Narasi AI (TTS)**:
   * Narasi suara AI profesional (Bahasa Indonesia berwibawa, hangat, dan bangga).
   * Struktur narasi:
     * *Detik 00-06*: Apresiasi dedikasi dan kerja keras ananda.
     * *Detik 06-18*: Sorotan keterampilan teknis (AutoCAD, detail konstruksi, pondasi).
     * *Detik 18-28*: Apresiasi karya nyata dan potensi profesi masa depan.
     * *Detik 28-32*: Penutup kebanggaan keluarga & branding Program Studi Arsitektur.
   * Background music akustik/sinematik lembut bebas hak cipta.
4. **Engine Rendering**:
   * Otomasi assembly timeline via **FFmpeg Engine** atau **OpenCraft FilmCraft MCP** (`E:\WORKSHOP\OPEN_CRAFT_MCP`).

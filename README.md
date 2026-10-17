# 🏛️ SIAK-KAPRODI: Sistem Intelijen Akademik & Rekap Portofolio Arsitektur
> **Golden Demo v2.0** — Platform Otomasi Akademik, Rapor Interaktif Wali Murid, dan Mesin Viral Marketing untuk Program Studi Arsitektur.

---

## 🌟 Latar Belakang & Nilai Strategis
Sistem ini dirancang khusus untuk memecahkan beban administratif Ketua Program Studi (Kaprodi) dan Dosen, sekaligus mengubah data perkuliahan menjadi aset publikasi berdaya jangkau tinggi bagi institusi kampus.

Sistem mengintegrasikan **4 Pilar Utama**:
1. **Pilar Presensi & Rekap Bulanan**:
   * Rekap absensi bulanan 35 mahasiswa lengkap per kelas dan per individu.
   * Pencatatan tanggal sesi, mata kuliah, status (Hadir, Sakit, Izin, Alpha), serta alasan ketidakhadiran otentik.
   * Deteksi dini mahasiswa berisiko (*At-Risk Intervention*) bagi yang memiliki Alpha $\ge 2$x atau kehadiran $< 75\%$.
2. **Pilar Rapor Interaktif & Analisis AI (Wali Murid)**:
   * Portal digital yang ramah orang tua dengan visualisasi Radar Chart 5 dimensi kompetensi arsitektur.
   * Analisis AI komprehensif: **Kekuatan**, **Kelemahan/Area Peningkatan**, dan **Saran Spesifik untuk Wali Murid di Rumah**.
3. **Pilar Mesin Viral Marketing (Word-of-Mouth)**:
   * **4-Slide Instagram Carousel (4:5 Portrait)**: Slide 1 (Cover Prestasi), Slide 2 (Aktivitas Studio Lab LIKDA), Slide 3 (Karya Gambar Kerja A3), Slide 4 (Pride & Ajakan Kuliah di Arsitektur).
   * **Video Vertikal 9:16 (Reels/Shorts/WA Story)**: Video 32 detik dengan narasi suara AI (Voiceover) merayakan progres dan capaian anak.
   * *Outcome*: Wali murid bangga dan memposting pencapaian anaknya ke WhatsApp Status / Instagram Stories, menciptakan promosi organik gratis bagi kampus!
4. **Pilar Dispatcher WhatsApp**:
   * Generator pesan resmi siap kirim ke nomor orang tua via WhatsApp Web dengan tautan unik rapor digital.

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

---

## 🗺️ Peta Studi Kasus Demo
Untuk kemudahan demonstrasi di depan Kaprodi, gunakan tombol demo cepat di pojok kanan atas:
1. 🌟 **M Yazid Zidane Mulyadi (NPM 2510015410010)**:
   * Profil mahasiswa teladan (Top Star), Kehadiran 100%, Grade A (95.2).
   * Contoh ideal untuk meninjau hasil carousel 4-slide dan video viral status WhatsApp.
2. ⚠️ **Rozi Andrian Surva (NPM 2510015410011)**:
   * Profil mahasiswa yang membutuhkan perhatian (At-Risk Intervention), 2x Alpha & 1x Sakit.
   * Menunjukkan bagaimana AI memberikan diagnosis empati dan menyarankan bimbingan khusus sebelum terlambat.
3. ✨ **Alsa Dmi Yesya Putri (NPM 2510015410001)**:
   * Profil mahasiswa konsisten kreatif dengan riwayat izin delegasi lomba arsitektur.

---

## 📄 Generator Dokumen PDF Resmi (4 Paket Dokumen)
Sistem dilengkapi engine perender dokumen PDF berkualitas penerbitan (Playwright Engine) yang dapat digenerate kapan saja via `generate_all_pdfs.bat` atau tombol unduh di browser:

### 1. Dokumen untuk Wali Murid (2 Jenis PDF):
* **PDF 1A: Rekap Kehadiran Mahasiswa Bulanan** (`01_rekap_kehadiran_bulanan_*.pdf`):
  * Dikirim rutin tiap 1 bulan sekali ke orang tua.
  * Memuat kop resmi fakultas, ringkasan persentase kehadiran, rekap sakit/izin/alpha, rincian tanggal pertemuan, topik materi, alasan ketidakhadiran, serta stempel verifikasi Kaprodi.
* **PDF 1B: Rapor Evaluasi Akhir Semester & Ranking Afirmatif** (`02_rapor_akhir_semester_*.pdf`):
  * Dikirim di akhir semester sebagai laporan portofolio final.
  * **Peringkat/Ranking Kelas**: Menampilkan posisi mahasiswa di antara 35 mahasiswa kelas (misal: `#1 / 35`).
  * **Psikologi Afirmatif**: Walaupun mahasiswa berada di peringkat bawah (seperti studi kasus Rozi Andrian Surva), sistem secara elegan **menonjolkan kelebihan, daya imajinasi spasial, dan potensi uniknya**, serta membingkai kelemahan sebagai peluang akselerasi agar wali murid tetap bangga dan termotivasi mendampingi anaknya di rumah.
  * **Radar Chart Visual**: Profil kompetensi 5 pilar arsitektur (AutoCAD, Detail Gambar, Kedisiplinan, Logika Struktur, Waktu).

### 2. Dokumen untuk Kaprodi (1 Jenis PDF):
* **PDF 2: Laporan Penilaian Dosen & Master Gradebook 35 Mahasiswa** (`03_laporan_penilaian_kaprodi_master_gradebook.pdf`):
  * Format **A4 Landscape** eksekutif untuk arsip rapat yudisium dan akreditasi jurusan.
  * Rekap matriks 35 mahasiswa lengkap: presensi %, nilai sesi P1 s/d P6, nilai akhir, grade huruf, ranking kelas, dan status kelulusan (Lulus, Remidi, Evaluasi).
  * Statistik makro: rata-rata kelas (81.0 / A-), kelulusan 97.1%, dan daftar intervensi at-risk.

### 3. Dokumen untuk Dosen dari Kaprodi (1 Jenis PDF):
* **PDF 3: Laporan Evaluasi Dosen & Keselarasan Kurikulum / Modul RPS** (`04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf`):
  * Laporan audit mutu pengajaran (QA Dosen) dari Kaprodi kepada tim pengampu (Aprilia Yunita, Duddy Fajriansyah, dan Adrian Ridhoa).
  * Realisasi presensi tim pengajar (100% terlaksana).
  * **Audit Kesesuaian Materi vs Modul RPS**: Evaluasi materi per sesi terhadap capaian CPMK/CPL dengan skor keselarasan rata-rata **96.0% (Terakreditasi Sangat Baik / Unggul)**.
  * Rapor performa kelas yang diampu beserta catatan evaluasi peningkatan mutu dari Kaprodi.

### 4. Portofolio Presentasi 16:9 Widescreen (DeckCraft Engine):
* **PDF 1C: Slide Deck Portofolio Arsitektur Mahasiswa** (`05_deckcraft_portofolio_arsitektur_*.pdf`):
  * 4-Slide presentasi arsitektur format landscape 16:9 widescreen dirancang untuk dilampirkan via WhatsApp dan dipresentasikan di depan keluarga/rekan.
  * Berisi cover portofolio, dokumentasi studio CAD di Lab LIKDA, karya lembar kerja A3, dan sertifikat kelulusan kompetensi studio.

---

## 🗂️ Manajemen File & Folder Hierarkis (File & Folder Management)
Sistem menerapkan struktur penyimpanan dokumen yang rapi, terisolasi, dan berjenjang menurut nama mata kuliah dan waktu pembuatan:

```text
e:\WORKSPACE\KAMPUS_01\
│
├── output/                                      <-- Direktori Utama Arsip Output
│   ├── latest_run.json                          <-- Pointer Global Sesi Generate Terakhir
│   │
│   └── APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS/     <-- Subfolder per Nama Mata Kuliah
│       ├── latest_run.json                      <-- Pointer Sesi Terakhir Mata Kuliah
│       │
│       ├── 2026-10-18_01-30-08/                 <-- Subfolder Waktu Pembuatan (Timestamp)
│       │   ├── 01_rekap_kehadiran_bulanan_2510015410001_ALSA_DMI_YESYA_PUTRI.pdf
│       │   ├── 01_rekap_kehadiran_bulanan_2510015410010_M_YAZID_ZIDANE_MULYADI.pdf
│       │   ├── 01_rekap_kehadiran_bulanan_2510015410011_ROZI_ANDRIAN_SURVA.pdf
│       │   ├── 02_rapor_akhir_semester_2510015410001_ALSA_DMI_YESYA_PUTRI.pdf
│       │   ├── 02_rapor_akhir_semester_2510015410010_M_YAZID_ZIDANE_MULYADI.pdf
│       │   ├── 02_rapor_akhir_semester_2510015410011_ROZI_ANDRIAN_SURVA.pdf
│       │   ├── 03_laporan_penilaian_kaprodi_master_gradebook.pdf
│       │   ├── 04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf
│       │   ├── 05_deckcraft_portofolio_arsitektur_2510015410001_ALSA_DMI_YESYA_PUTRI.pdf
│       │   ├── 05_deckcraft_portofolio_arsitektur_2510015410010_M_YAZID_ZIDANE_MULYADI.pdf
│       │   ├── 05_deckcraft_portofolio_arsitektur_2510015410011_ROZI_ANDRIAN_SURVA.pdf
│       │   └── manifest.json                    <-- Metadata Run (Nama MK, Kode, Jam, Ukuran File)
│       │
│       └── [Timestamp_Sesi_Berikutnya]/         <-- Setiap kali batch dijalankan, folder baru dibuat
│
├── generated_pdfs/                              <-- Mirror Sinkronisasi Otomatis (Live Web Preview)
└── scripts/
    └── generate_pdfs.py                         <-- Engine Pembuat Folder & Perender PDF
```

### Keunggulan Struktur Ini:
1. **Tidak Ada File Tertimpa (Zero Overwrite)**: Setiap eksekusi pembuatan rapor atau dokumen arsip tersimpan dalam folder timestamp unik sehingga riwayat perkuliahan tersimpan utuh.
2. **Katalog Manifest JSON Otomatis**: Setiap folder mencatat file apa saja yang digenerate, kode mata kuliah, waktu eksekusi, dan ukuran berkas (KB).
3. **Penyajian Cepat via Web**: Dashboard menyediakan REST API `/api/runs` dan melayani rute berkas statis `/output/<mata_kuliah>/<timestamp>/<nama_file>`.

---

## 🔗 Keterhubungan dengan Framework OpenCraft MCP
Aplikasi ini dirancang modular agar terhubung langsung dengan engine otomasi di:
`E:\WORKSHOP\OPEN_CRAFT_MCP`
* `deckcraft`: Merender bahan tayang portofolio presentasi 16:9 widescreen (`scripts/deckcraft_builder.py`).
* `designcraft`: Desain tata letak visual dokumen PDF dan kartu rapor.
* `filmcraft / shorts-template`: Merender video vertikal 9:16 dengan background musik dan voiceover audio.
* `carousel-template`: Merender kartu slide media sosial resolusi tinggi.


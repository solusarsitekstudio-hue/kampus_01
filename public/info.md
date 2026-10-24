# SIAK-KAPRODI — Penjelasan Sistem

> **Sistem Intelijen Akademik & Rekap Portofolio Arsitektur.**  
> Dashboard lokal (port **40404**) yang mengubah data perkuliahan menjadi rekap Kaprodi,
> rapor wali murid, portofolio mahasiswa, cockpit pimpinan yayasan, dan paket PDF resmi — **tanpa internet**.  
> Termasuk analisis kekuatan/potensi tiap mahasiswa, kabar progres wali murid, audit RPS dosen, dan transparansi kasus remedial lintas 30 mata kuliah.

Versi dokumen: **v2.8 (12-Tab Enterprise Academic Suite)** — basis data tetap
`2.6-KURIKULUM-BERTINGKAT` per **23 Oktober 2026**. Halaman ini membaca langsung berkas
`public/info.md`, sehingga seluruh dokumentasi selalu sinkron secara *real-time* tanpa perlu merestart program.

---

## 1. Apa yang sistem ini kerjakan

Sistem ini mengambil **satu sumber kebenaran** (*single source of truth* dari folder tree kurikulum), lalu menurunkannya melalui arsitektur terisolasi (*Decoupled Bridge Engine*) menjadi berbagai keluaran terstruktur yang saling konsisten:

- **1. Rekap Dashboard Kaprodi** — kehadiran per slot absen, nilai terbobot, mahasiswa At-Risk, distribusi grade studio, dan peta MK rawan.
- **2. Rapor Wali Murid** — narasi humanis tanpa peringkat kompetitif, radar kompetensi 5 pilar, rekomendasi profesi berbukti, dan catatan bimbingan.
- **3. Showcase & Video Karya** — slide deck 16:9 DeckCraft widescreen, galeri foto karya riil, dan generator video portofolio vertikal 9:16 Full HD.
- **4. Simulator WhatsApp** — format pesan pembuka sopan siap salin ke orang tua, dilengkapi 3 dokumen lampiran PDF terverifikasi.
- **5. Pengaturan Identitas** — manajemen nama institusi, kaprodi, dosen pengasuh, dan asisten dosen tersentral di `config/identitas.json` dengan pengaman 3 tingkat.
- **6. Struktur Kurikulum** — editor struktur tree 16 pertemuan, validasi bobot total wajib 100%, dan status jenis MK (teori/studio).
- **7. Presensi & RPS Dosen** — audit pemantauan 16 sesi tatap muka perkuliahan dosen, kesesuaian modul RPS, CPMK, dan Berita Acara Perkuliahan (BAP) akreditasi.
- **8. Info & Dokumentasi** — buku panduan sistem, alur data, metodologi penilaian, dan transparansi arsitektur.
- **9. Rekap Periode & Perjalanan Akademik** — analisis 4 cakupan (per bulan, 1 MK semester, semua MK satu semester, semua semester) + panel potensi mahasiswa per MK dinamis lintas 30 katalog.
- **10. Portofolio Akademik 4 Lapis** — rekap komprehensif mahasiswa: Lapis 1 (Bulanan), Lapis 2 (Mata Kuliah + SKS + Dosen), Lapis 3 (Semester terbuka otomatis), Lapis 4 (Kumulatif & AI Review Karier Rotary).
- **11. Engine Input & Output** — sistem verifikasi berkas inbox anti-duplikat hash SHA-256, audit integritas dokumen cetak, dan pembersihan lapis kirim otomatis.
- **12. Cockpit Yayasan & Investor** — *Executive Boardroom*: valuasi efisiensi mutu, penyelamatan cashflow SPP, pitch deck akreditasi 1-klik, dan modal asistensi mahasiswa remedial per MK.

Prinsip utamanya: **angka dihitung secara deterministik, bukan diketik**. Semua dokumen membaca data yang sama, sehingga tidak ada kontradiksi antar dokumen.

---

## 2. Kelebihan sistem & nilai jual

Keunggulannya bukan sekadar "banyak tampilan", melainkan **satu sumber data yang sama diproses secara bertingkat untuk empat pemangku kepentingan sekaligus**: Kaprodi (kontrol mutu), Mahasiswa (portofolio rekam jejak), Wali Murid (kabar progres humanis), dan Yayasan/Rektorat (valuasi operasional & akreditasi).

### 2.1 Satu data, banyak keluaran yang konsisten
- Seluruh modul membaca data master dan katalog `data/kurikulum/` yang sama.
- Perubahan nilai atau topik pertemuan langsung mengalir ke seluruh keluaran saat dikompilasi ulang.
- Menghapus risiko kesalahan manusia (*human error*) akibat rekap Excel manual yang tercecer.

### 2.2 Portofolio otomatis per mahasiswa
Setiap mahasiswa memiliki bahan presentasi yang diproduksi otomatis oleh sistem:

| Keluaran | Spesifikasi | Kegunaan Praktis |
|---|---|---|
| **Deck 16:9 (4 Slide)** | PDF 16:9 Widescreen (Cover, Lineweight CAD, Denah 1:100, Sertifikat) | Presentasi studio, sidang magang, portofolio beasiswa |
| **Video 9:16 (MP4)** | Video vertikal 30 detik Full HD dengan narasi personal & foto karya | Media sosial (Instagram Reels, TikTok), branding mahasiswa |
| **Rapor PDF Lengkap** | Rekap bulanan, kehadiran jujur, narasi 4 kuadran, matriks profesi | Arsip wali murid, konseling dosen pembimbing akademik |
| **Transkrip 4 Lapis** | Riwayat bulanan, identitas MK, rollup semester, capaian kumulatif | Portofolio akademik menyeluruh untuk sertifikasi industri |

### 2.3 Analisis kekuatan & potensi berbukti
- **Matriks Karier Berbukti:** Setiap rekomendasi karier memiliki data `bukti` nyata (angka nilai MK dan kanal bidang terkait), narasinya dibangun dari angka tersebut, bukan template statis.
- **Perapian AI Rotary Fail-Closed:** Narasi 3 profesi teratas dapat dirapikan oleh klaster Gemini Rotary AI (tombol *"Rapikan dengan AI"* di Tab 10). Setiap angka dalam narasi hasil AI diverifikasi secara ketat terhadap data bukti asli — satu angka karangan langsung ditolak.
- **Radar 5 Pilar Kompetensi:** Penguasaan CAD, ketelitian detail, kedisiplinan asistensi, logika ruang & struktur, manajemen waktu.
- **Tanpa Peringkat Kompetitif (Zero Ranking):** Menghindari toxic comparison, berfokus penuh pada kurva pertumbuhan kompetensi personal.

### 2.4 Kemitraan transparan dengan orang tua (Wali Murid)
Tab 4 menyediakan draf pesan WhatsApp resmi siap salin ke wali murid, dilengkapi **3 dokumen lampiran PDF terverifikasi**:
1. Rekap Kehadiran Bulanan (Presensi Jujur).
2. Rapor Capaian Semester & Matriks Potensi Karier.
3. Slide Portofolio Presentasi 16:9 DeckCraft.

Pesan bersifat humanis, solutif, dan menyampaikan langkah pendampingan konkret yang dapat dilakukan keluarga di rumah.

### 2.5 Cockpit eksekutif yayasan & penyelamatan SPP
Tab 12 menyajikan dashboard *Boardroom*:
- **Peta Mutu 30 MK:** Pemantauan menyeluruh seluruh kurikulum arsitektur dalam satu matriks ringkas.
- **Modal Asistensi Remedial:** Transparansi data hingga ke level nama mahasiswa individual yang at-risk/remedial (grade C/D), absensi, serta draft WhatsApp pembinaan personal dari Ka Prodi.
- **Retensi Finansial:** Mencegah mahasiswa drop-out (DO) sejak dini demi menjaga keberlanjutan cashflow SPP institusi.

---

## 3. Alur data yang sudah berjalan

```text
data/kurikulum/<PRODI>/<TAHUN AJAR>/<SEMESTER>/<MK>/
├── penawaran.json   identitas MK: kode, SKS, dosen, kelas, jadwal, jenis_mk
├── sesi.json        16 pertemuan: topik, bobot, jumlah slot absen
└── nilai.json       presensi + nilai per mahasiswa per slot
        │
        ▼
scripts/parse_data.py  (kompilasi tanpa mengarang angka)
        │
        ├──▶ data/academic_data.json   master untuk MK aktif
        ├──▶ data/courses/<MK>.json    katalog tiap MK (30 MK kurikulum)
        └──▶ config/kurikulum.json     indeks tree navigasi
        │
        ▼
server.py (Python stdlib, port 40404) ──▶ REST API (15 Endpoints)
        │
        ├──▶ scripts/academic_bridge.py (Facade 4 Domain: Presensi, Nilai, Kurikulum, Retake)
        ├──▶ scripts/portofolio.py & fitur_mahasiswa.py (Portofolio 4 Lapis)
        ├──▶ scripts/ai_karier.py (Gemini Rotary Cluster Fail-Closed)
        │
        ▼
public/app.js (SPA Offline Terintegrasi 12 Tab)
        │
        ├──▶ 12 Tab Antarmuka Interaktif
        └──▶ output/<MK>/<TIMESTAMP>/ (Paket PDF Resmi + Manifest)
```

Yang **boleh dihapus kapan saja**: `data/academic_data.json`, `data/courses/`, `config/kurikulum.json`, dan isi `output/`. Semuanya merupakan artefak build yang dapat dibangun ulang dalam hitungan detik via `python scripts\parse_data.py`.  
Yang **tidak boleh hilang**: isi `data/kurikulum/` dan `config/identitas.json`.

---

## 4. Dua belas tab dashboard

| No | Tab Navigasi | Fungsi Utama | Sumber Data |
|:---:|---|---|---|
| **1** | **Dashboard Kaprodi** | **Kompetensi-First:** KPI rata-rata nilai, kesiapan industri, sebaran nilai studio, filter kelas, dan peta MK rawan lintas semester. | `data/academic_data.json` + tree kurikulum |
| **2** | **Rapor Wali Murid** | Evaluasi 360° individual per mahasiswa, grafik radar kompetensi 5 pilar, narasi perkembangan 4 kuadran, dan rekomendasi profesi. | `data/academic_data.json` |
| **3** | **Showcase & Video Karya** | Presenter slide deck 16:9 DeckCraft, deteksi folder karya riil mahasiswa, player video 9:16 Full HD, dan salin caption Instagram. | `output/`, `public/videos/` |
| **4** | **Simulator WhatsApp** | Simulator pesan resmi ke wali murid + tautan 3 lampiran dokumen PDF terverifikasi, fitur 1-klik salin teks ke clipboard. | `output/`, `config/identitas.json` |
| **5** | **Pengaturan** | Manajemen identitas kampus, pimpinan prodi, dosen pengasuh, asisten dosen, dan aturan bobot dengan pengaman 3 tingkat. | `config/identitas.json` |
| **6** | **Kurikulum** | Editor struktur tree kurikulum 16 pertemuan, validasi bobot total wajib 100%, konfigurasi jenis MK (teori/studio), dan jadwal. | `data/kurikulum/` |
| **7** | **Presensi & RPS Dosen** | Audit pemantauan 16 sesi tatap muka perkuliahan dosen, kesesuaian modul RPS, capaian CPMK, dan unduh PDF Berita Acara (BAP). | `scripts/academic_bridge.py` |
| **8** | **Info Sistem** | Buku panduan interaktif, dokumentasi cara kerja sistem, metodologi penilaian, dan transparansi status modul (*halaman ini*). | `public/info.md` |
| **9** | **Rekap Periode** | Rekap perjalanan akademik 4 cakupan (Bulan, 1 MK, Semester, Semua Semester) + panel potensi mahasiswa per MK dinamis (30 MK). | `/api/periode`, `/api/course_data` |
| **10** | **Portofolio 4 Lapis** | Transkrip kompetensi 4 lapis (Bulan → MK → Semester [Accordion Open] → Kumulatif) + tombol *Rapikan dengan AI* (Gemini Rotary). | `/api/portofolio`, `/api/portofolio/ai` |
| **11** | **Engine** | Pengendali integritas data: pindai inbox anti-duplikat SHA-256, audit output berkas PDF, perapian run lama, dan penyiapan lapis kirim. | `scripts/engine_input.py`, `scripts/engine_output.py` |
| **12** | **Cockpit Yayasan & Investor** | *Executive Pitch*: valuasi operasional kampus, mitigasi resiko SPP, matriks 30 MK prodi, dan modal asistensi mahasiswa remedial per MK. | `/api/executive_cockpit`, `/api/bridge/course_detail` |

---

## 5. Aturan akademik yang dipegang sistem

### 5.1 Nilai akhir terbobot
```text
Nilai Akhir = Σ (Skor Pertemuan × Bobot Pertemuan) / Σ Bobot Pertemuan
```
Satu semester = **16 pertemuan**. Bobot diatur per mata kuliah di `sesi.json` dan jumlahnya wajib **tepat 100**; jika tidak pas 100, sistem menolak penyimpanan (HTTP 422). Ketidakhadiran (Alpha) bernilai 0 dan tetap diperhitungkan ke dalam rata-rata.

### 5.2 Pertemuan yang belum diinput
Pertemuan yang slot absensinya belum diinput ditandai sebagai **"Belum Diinput"** — status ini netral (**bukan Alpha**, **bukan nilai 0**). Pertemuan ini tidak menekan rata-rata mahasiswa (bobot dinormalisasi ulang), dan status nilai sementara ditandai sebagai **"Belum Lengkap"**.

### 5.3 Predikat grade nilai
| Grade | Standar Nilai & Kehadiran |
|:---:|---|
| **A** | Rata-rata ≥ 85 dan Kehadiran ≥ 80% |
| **A-** | Rata-rata ≥ 80 dan Kehadiran ≥ 75% |
| **B+** | Rata-rata ≥ 75 dan Kehadiran ≥ 75% |
| **B** | Rata-rata ≥ 70 |
| **C** | Rata-rata ≥ 60 |
| **D / Evaluasi** | Rata-rata < 60 |
| **Belum Lengkap** | Terdapat sesi pertemuan yang presensinya belum diinput |

### 5.4 Deteksi dini At-Risk
```text
At-Risk  ⇔  (Alpha ≥ 2×)  ATAU  (Kehadiran < 75%)
```
Kriteria at-risk didefinisikan secara tunggal pada `scripts/kelas_rules.py`. Badge tabel, kartu KPI, laporan PDF, dan dashboard yayasan membaca logika yang sama.

---

## 6. Tata cara pengoperasian cepat

```cmd
:: 1. Menjalankan Server & Dashboard (Port 40404)
1_RUN_SERVER.bat

:: 2. Menghentikan Server Secara Bersih
STOP_SERVER.bat

:: 3. Membangun Ulang Master & Katalog dari Tree Kurikulum
python scripts\parse_data.py

:: 4. Mencetak Ulang Seluruh Paket Dokumen PDF
generate_all_pdfs.bat

:: 5. Menjalankan Suite Verifikasi Regresi
python tests\test_rules_unchanged.py
python tests\test_kurikulum_api.py
python tests\test_portofolio.py
python tests\test_engine.py
```

---

## 7. Batasan yang perlu diketahui

- **Offline-First:** Seluruh komponen bekerja 100% lokal tanpa ketergantungan koneksi internet. Vendor CSS/JS tersimpan lokal di `public/vendor/`.
- **Keamanan Port:** Server mendengarkan di `127.0.0.1:40404` dengan pengaman bentrok port (*clean taskkill*).
- **Integritas Nilai:** Nilai awal yang disertakan merupakan data demo sintetis yang dibangun secara deterministik per NPM. Data nilai resmi dapat diimpor langsung melalui modul `scripts/impor/`.
- **Render Video:** Pembuatan video portofolio vertikal 9:16 memerlukan pustaka FFmpeg yang terpasang di sistem operasi Windows.
- **Privasi Pengiriman:** Pesan WhatsApp dan caption Instagram disalin secara manual oleh dosen/asisten; sistem tidak pernah mengakses akun privat pengguna.

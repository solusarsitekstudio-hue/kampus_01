# 🏛️ SIAK-KAPRODI: Sistem Intelijen Akademik & Rekap Portofolio Arsitektur
> **Golden Demo v2.6 — Kurikulum Bertingkat** — Platform Otomasi Akademik, Rapor Interaktif & Pemetaan 10 Karier Masa Depan, Slide Deck Portofolio Arsitektur, serta Generator Dokumen PDF On-Demand untuk Program Studi Arsitektur.

> **Perubahan besar v2.6:** data perkuliahan tidak lagi dibaca dari berkas Excel/PDF
> mentah. Sumbernya sekarang **tree kurikulum bertingkat** di `data/kurikulum/`
> (PRODI → TAHUN AJAR → SEMESTER → MATA KULIAH → 16 PERTEMUAN), dan dashboard bisa
> **menyuntingnya** dari tab **6. Kurikulum**.

---

## 📐 Metodologi & Aturan Resmi Sistem

Bagian ini adalah **sumber kebenaran tunggal**. Semua angka di dashboard, PDF, dan
pesan wali murid berasal dari sini — bukan dari teks yang diketik manual.

### 1. Perhitungan Nilai (Rata-rata TERBEBOT)

```
Nilai Akhir = Σ (Skor Pertemuan × Bobot Pertemuan) / Σ Bobot Pertemuan
Bobot bawaan: 14 × 4 + UTS 20 + UAS 24 = 100   (P1..P7, P9..P15 = 4; P8 = UTS; P16 = UAS)
```

* **Satu semester = 16 pertemuan.** Nilai dihitung dari SELURUH 16 pertemuan,
  bukan dari "6 sesi" seperti versi lama — penyebut 6 itu memang salah tulis.
* Bobot **bisa berbeda per mata kuliah** dan diatur di
  `data/kurikulum/<PRODI>/<TA>/<SEMESTER>/<MK>/sesi.json`. Yang wajib: jumlah
  bobotnya **tepat 100**. Dashboard menolak simpan kalau tidak (HTTP 422).
* **Alpha bernilai 0 dan DIHITUNG** sebagai bagian dari rata-rata.
  Mahasiswa yang tidak hadir **tidak** mendapat nilai gratis.
* Pertemuan **Sakit** dan **Izin** tetap dinilai 70–85 (student tetap berkarya).
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

### 6. Aset Lokal — Dashboard Berjalan OFFLINE

Seluruh tampilan dikunci di dalam repo (`public/vendor/`). Tidak ada satu pun
permintaan ke internet saat dashboard dibuka.

| Aset | Bentuk | Ukuran |
|---|---|---|
| Tailwind CSS | **CSS statis** (dibangun, bukan JIT di browser) | 30 KB |
| ApexCharts | `vendor/apexcharts.min.js` | 527 KB |
| Lucide Icons | `vendor/lucide.min.js` | 348 KB |
| Plus Jakarta Sans + JetBrains Mono | `vendor/fonts/` (10 woff2) | 123 KB |

> Sebelumnya 4 sumber CDN dipakai. WiFi ruang rapat ngadat = **layar putih total**.
> Sekarang justru itu satu-satunya mode yang tidak bisa gagal.
>
> Catatan: font **Plus Jakarta Sans** dan **JetBrains Mono** sudah lama dimuat
> tetapi tidak pernah dipakai, karena `font-sans`/`font-mono` tidak didaftarkan
> ke tema Tailwind. Sekarang keduanya benar-benar dirender.

Perbarui aset bila perlu:

```cmd
python scripts\fetch_vendor.py --force
scripts\build_tailwind.bat
```

Wajib menjalankan `build_tailwind.bat` **setiap kali** ada class Tailwind baru
di `index.html` atau `app.js`, karena Tailwind kini di-compile, bukan dibaca
dari CDN.

### 7. Transfer Berkas: HTTP/1.1 + Byte-Range

Server memakai **HTTP/1.1** dan menghormati header `Range`.

* Video portofolio bisa **di-seek** (geser timeline) — sebelumnya tidak bisa,
  karena HTTP/1.0 tidak mendukung byte-range.
* Video 857 KB dikirim per potongan 64 KB, tidak lagi dibaca penuh ke RAM
  untuk setiap permintaan.
* Server menolak dijalankan dua kali di port yang sama (`run_server.bat` yang
  diklik dua kali hanya menampilkan pesan, bukan membuat dua server yang saling
  menimpa data).

### 8. Sumber Kebenaran Tunggal: Tree Kurikulum (sejak v2.6)

Sejak v2.6, **data perkuliahan tidak lagi diturunkan dari berkas Excel/PDF mentah
maupun dari berkas katalog**. Sumbernya satu: tree kurikulum di `data/kurikulum/`.

```
data/kurikulum/<PRODI>/<TAHUN AJAR>/<SEMESTER>/<MATA KULIAH>/
├── penawaran.json   <-- identitas MK di semester itu (nama, kode, SKS, dosen,
│                        kelas, jadwal, jenis_mk, semester_kurikulum)
├── sesi.json        <-- 16 pertemuan: topik, deskripsi, bobot, slot absen
└── nilai.json       <-- baris nilai & presensi per mahasiswa per pertemuan
```

Dari tree itu, `scripts/parse_data.py` **membangun**:

* `data/academic_data.json` — data master (yang dibaca dashboard, PDF, wali murid)
* `data/courses/<MK>.json` — katalog per MK
* `config/kurikulum.json` — indeks turunan (dibuat oleh `scripts/index_kurikulum.py`)

Semuanya **artefak build**. Menghapusnya tidak merusak apa pun — jalankan
`python scripts/parse_data.py` dan semuanya terbentuk kembali.

#### "Ganti Mata Kuliah" tidak lagi menimpa master

Dulu tombol ganti MK menyalin file katalog menjadi data master, dan salinan itu
**tidak diperiksa sama sekali**.

> **Kejadian nyata (v2.5):** katalog MK aktif tertinggal di versi `2.0` sementara
> master sudah `2.5`. Sekali ganti mata kuliah lalu kembali, data master ikut
> mundur ke `2.0` — At-Risk berubah `10 → 1` dan nilai `80.6 → 82.5` — tanpa
> satu pun pesan error.

Sekarang "ganti MK" hanya **memindahkan penunjuk** `mata_kuliah_aktif` di
`config/identitas.json`, lalu **membangun ulang master + seluruh katalog dari
tree**. Tidak ada lagi penyalinan katalog → master, jadi tidak ada lagi versi
yang bisa "mundur". Kalau pembangunan ulang gagal, penunjuk dikembalikan ke MK
semula supaya tidak ada keadaan setengah jalan.

Penjaga versi lama **tetap dipasang** sebagai jaring pengaman kalau-kalau ada
artefak katalog ber-aturan lama tertinggal di repo:

| Situasi | Tindakan |
| --- | --- |
| MK yang dipilih **sedang aktif** | Data master tidak disentuh. Tidak ada penulisan. Kode 200 + pesan penjelas. |
| MK lain, katalog **lebih lama** | Permintaan **ditolak (409)** dengan instruksi perbaikan. Data master tetap utuh. |
| MK lain, katalog seversi | Berjalan normal: penunjuk dipindah, master + katalog dibangun ulang. |

Perbaikan/penyelarasan katalog tanpa mengubah angka:

```cmd
python scripts\process_input.py --sync-katalog
```

`parse_data.py` juga memanggil penyelarasan ini otomatis di akhir setiap kali
master dibangun ulang, jadi katalog tidak akan tertinggal lagi.

> Catatan lama yang kini tidak berlaku: dulu isi katalog MK aktif harus disalin
> dari master (bukan dihitung ulang) karena master berasal dari Excel + PDF
> asli. Sejak v2.6 tidak ada Excel/PDF; master **memang** hasil hitung dari tree,
> jadi master dan katalog selalu sepakat karena keduanya dibangun dari sumber
> yang sama.

---

### 9. Identitas: Satu Sumber Nama (`config/identitas.json`)

Dulu nama mata kuliah, dosen pengasuh, asisten dosen, dan ketua prodi disalin manual
di **5 tempat** (`parse_data.py`, `process_input.py`, `generate_pdfs.py`,
`video_composer.py`, `index.html`) — dan nilainya ikut **tertanam** ke dalam data
turunan: 35 pesan wali murid, seluruh PDF, dan video.

> **Risikonya nyata:** dokumen resmi bertanda tangan bisa memuat nama dosen atau ketua
> prodi yang salah hanya karena satu dari lima salinan itu kelewat diganti.

Sekarang hanya ada satu tempat: `config/identitas.json`.

| Bagian | Isi |
| --- | --- |
| `institusi` | universitas *(opsional)*, fakultas, prodi, ketua prodi, NIP ketua prodi *(opsional)*, kota |
| `dokumen` | tanggal tanda tangan dokumen |
| `dashboard` | judul, sub judul, deskripsi (boleh memakai placeholder `{prodi}`) |
| `mata_kuliah` | identitas tiap MK: kode, nama, SKS, kelas, semester, jadwal, dosen pengasuh, asisten + NIP |

Yang **sengaja tetap di Python**, bukan di config: aturan nilai (`kelas_rules.py`) dan
aturan At-Risk. Sedangkan **daftar pertemuan/topik/bobot** bukan lagi di Python — sejak
v2.6 itu isi tree `data/kurikulum/.../sesi.json`, karena sifatnya materi perkuliahan
per semester, bukan identitas program studi.

> **Nama universitas dibiarkan kosong** karena memang belum pernah ada di project ini —
> tidak dikarang. Kalau diisi, barisnya otomatis muncul di kop surat; kalau kosong,
> kop tetap seperti sekarang.

#### Mengaturnya dari dashboard: tab **5. Pengaturan**

Tidak perlu mengedit file. Perubahannya sengaja dibagi **tiga tingkat** supaya tidak ada
satu klik yang diam-diam mengubah dokumen resmi:

| Tingkat | Tombol | Yang berubah | Berat |
| --- | --- | --- | --- |
| 1 | **Simpan Identitas** | Hanya label dashboard. Instan, tidak menyentuh data. | — |
| 2 | **Terapkan ke Dokumen** | Data master diregenerasi → nama ikut ke pesan wali murid + PDF | ~1 detik |
| 3 | **Cetak Ulang Paket PDF** | Paket PDF arsip dicetak ulang (membuka Chromium) | 1–2 menit |

> **"Sudah disimpan" tidak sama dengan "sudah diterapkan".** Selama Tingkat 2 belum
> dijalankan, dashboard sudah memakai nama baru sementara pesan wali murid dan PDF
> **masih nama lama**. Karena itu banner peringatan wajib muncul di tab 5, dan
> sistem menyebutkan field mana saja yang belum ikut.

Tingkat 3 **ditolak (409)** kalau masih ada identitas yang belum diterapkan ke data.
Kalau tidak ditolak, kop PDF akan memakai nama baru sementara isi tabelnya masih data
lama — dokumen yang tampak resmi tetapi tidak konsisten.

Endpoint (hanya `127.0.0.1`; JSON wajib, maks 512 KB):

```cmd
GET  /api/identitas                    -> config + label + daftar yang belum diterapkan
POST /api/identitas                    -> Tingkat 1
POST /api/identitas/terapkan           -> Tingkat 2
POST /api/identitas/regenerasi-pdf     -> Tingkat 3
```

`scripts/identitas.py` fail-closed: config hilang/rusak/tidak lengkap ⇒ proses
**berhenti** dengan pesan yang menyebut field mana yang salah — bukan menebak. Setiap
penyimpanan membackup dulu ke `data/_backup/identitas.<stempel>.json`, lalu menulis
atomic.

Dua hal yang dulu **beku** ikut pindah ke config dengan nilai yang sama persis, jadi
sekarang bisa diubah tanpa mengubah tampilan hari ini: **kota + tanggal tanda tangan**
(`Padang, 18 Oktober 2026` dulu ditulis literal di dalam template PDF) dan **NIP ketua
prodi / NIP asisten**.

Mengubah identitas **tidak mengubah angka**: nilai, kehadiran, At-Risk, predikat, dan
distribusi grade tetap sama. Yang berubah hanya teks/nama. Jumlah mahasiswa pada label
tombol "PDF Gradebook" juga tidak lagi diketik `35` — dihitung dari data.

---

## 📊 Angka Ril Demo Saat Ini (versi `2.6-KURIKULUM-BERTINGKAT`)

> Stempel build tidak lagi ditulis di sini (dulu sering tertinggal basi).
> Nilai terakhir ada di `data/academic_data.json` → `metadata.build_id`, dan
> berubah setiap kali data dibangun ulang. Yang stabil dan diuji adalah
> **angkanya**, bukan stempelnya.

| Metrik | Nilai |
|---|---|
| Total Mahasiswa | 35 |
| Rata-rata Kehadiran | 85.4% (dihitung per **slot** absen, 16 pertemuan) |
| Rata-rata Nilai Studio | **79.0** (predikat dominan B+, 13 mahasiswa) |
| Mahasiswa At-Risk | **6** (semuanya kehadiran < 75%; 5 di antaranya juga Alpha ≥ 2x) |
| Distribusi Grade | A=3, A-=10, B+=13, B=8, C=1, D=0 |
| Tingkat Kelulusan | 82.9% (29 dari 35 memenuhi: tidak At-Risk **dan** nilai ≥ 70) |

### 3 Kasus Studi (angka terbaru)

1. 🌟 **M Yazid Zidane Mulyadi (NPM 2510015410010)**
   * Kehadiran 100% (16/16 pertemuan, 32/32 slot), Grade A (94.7), Indeks Kesiapan 92.8%.
   * Cocok untuk BIM Modeler & Architectural Designer.
2. ⚠️ **Rozi Andrian Surva (NPM 2510015410011)**
   * Kehadiran 62.5% (**9 pertemuan penuh + 2 pertemuan hadir sebagian**, 20/32 slot),
     **3x Alpha**, 1x Sakit, 1x Izin.
   * **Grade C (60.0)** — bobot 0 pada pertemuan Alpha menurunkan nilai secara
     signifikan. Teridentifikasi At-Risk (Alpha 3x **dan** kehadiran 62.5%).
   * Tujuan utama: demonstrate how the system **menjaga martabat** —
     tetap fokus pada talenta, dengan panduan pendampingan orang tua yang hangat.
3. ✨ **Alsa Dmi Yesya Putri (NPM 2510015410001)**
   * Kehadiran 93.8% (15/16 pertemuan, 30/32 slot), Grade A (90.8), izin delegasi
     lomba arsitektur.

---

## 🌟 Latar Belakang & Nilai Strategis
Sistem ini dirancang khusus untuk memecahkan beban administratif Ketua Program Studi (Kaprodi) dan Dosen, sekaligus mengubah data perkuliahan menjadi aset komunikasi bermartabat ke wali murid dan instrumen publikasi berkualitas tinggi bagi institusi kampus.

Sistem mengintegrasikan **4 Pilar Utama**:
1. **Pilar Presensi & Rekap Bulanan**:
   * Rekap absensi bulanan 35 mahasiswa lengkap per kelas dan per individu.
   * Pencatatan tanggal sesi, mata kuliah, status (Hadir, Sakit, Izin, Alpha), serta alasan ketidakhadiran otentik.
   * Deteksi dini mahasiswa berisiko (*At-Risk Intervention*) bagi yang memiliki Alpha $\ge 2$x atau kehadiran $< 75\%$.
   * Dilengkapi grafik web interaktif: Donut Progress Ring dan Bar Chart **per Pertemuan (P1-P16)** dengan garis patokan **Benchmark Kelas** yang dibaca dari data (sekarang 85.4%).
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

## 📂 Sumber Data: Sistem Mandiri (Ground Truth)

> **v2.6: tidak ada lagi berkas Excel atau PDF mentah.** Dua berkas yang dulu
> dipakai (`DAFTAR MAHASISWA.xlsx` dan `02 rekap qs pratikum.pdf`) sekarang
> dianggap **tidak ada**: isinya sudah dipindahkan ke tree kurikulum, dan sistem
> dirancang supaya berjalan **tanpa** keduanya. Tidak ada kode yang membacanya.

Semua yang ditampilkan dashboard, PDF, dan pesan wali murid berasal dari
`data/kurikulum/`. Isi awalnya disemai **sekali** dari data perkuliahan nyata
(kelas TEKZA, Genap 2025/2026), lalu angka presensi/nilai yang belum ada diisi
penyemai sintetis (lihat keterangan di bawah).

* Program Studi: `Arsitektur` • Ruang praktik: `Lab LIKDA`
* Ketua Prodi Arsitektur: `Fielda Roza, S.T., M.T.`
* Dosen Pengasuh: `Aprilia Yunita, S.T., M.T.` & `Duddy Fajriansyah, S.T., M.T.`
* Asisten Dosen: `Adrian Ridhoa, S.T.`

### ⚠️ Keterangan jujur soal angka presensi & nilai

Nilai dan status kehadiran 35 mahasiswa **dibangkitkan secara sintetis**
(bukan nilai resmi dosen dan bukan hasil input portal). Setiap baris yang
disintesis diberi tanda `sintetis: true`, dan beberapa tempat di UI
menuliskannya terang-terangan sebagai "bukan nilai resmi dosen".

Angkanya **deterministik**: dibangkitkan dari `random.Random(42 + npm)` dengan
profil per arketipe (`scripts/persona.py`). Jadi untuk NPM yang sama, hasilnya
selalu sama — tidak berubah-ubah setiap kali dibangun ulang.

Ganti angka sintetis itu dengan data asli **tanpa mengubah kode**: tulis
barisnya ke `nilai.json` di tree MK (lihat kontrak di bawah).

### 📥 Kontrak Data Masuk (agar bisa diganti data portal)

Kalau nanti data asli datang dari portal akademik (satu MK per semester per
tahun ajar), cukup **menaruhnya di tempat yang sama**. Kontraknya sengaja
sederhana dan tidak berubah-ubah:

**Blok kepala** (sekali per berkas/MK):

| Field | Isi | Contoh |
| --- | --- | --- |
| `prodi` | nama program studi (huruf apa saja; jadi nama folder) | `Arsitektur` |
| `tahun_ajar` | tahun ajar | `2025-2026` |
| `semester` | `GANJIL` atau `GENAP` | `GENAP` |
| `kode_mk` | kode mata kuliah | `5412522233` |

**Baris data** (satu baris = satu mahasiswa × satu pertemuan × satu slot):

| Field | Isi | Contoh |
| --- | --- | --- |
| `npm` | Nomor Pokok Mahasiswa | `2510015410010` |
| `nama` | nama lengkap | `M YAZID ZIDANE MULYADI` |
| `pertemuan` | nomor pertemuan 1..16 | `3` |
| `slot` | nomor slot absen dalam pertemuan itu (mulai 1) | `1` |
| `status` | `Hadir`, `Hadir Sebagian`, `Sakit`, `Izin`, `Alpha` | `Hadir` |
| `skor` | nilai pertemuan itu, 0..100 | `95` |

Aturan yang **dijaga sistem** (akan menolak/mengoreksi sendiri):

* `pertemuan` harus 1..16; `slot` harus ada di dalam pertemuan itu (1..`jumlah_slot`).
* `skor` wajib 0..100. `Alpha` bernilai **0** dan tetap dihitung di rata-rata.
* Jumlah bobot seluruh pertemuan wajib **tepat 100**; dashboard menolak simpan
  kalau tidak (HTTP 422) dan menyebut total yang salah.

---

## ⚡ Cara Menjalankan Aplikasi

### 1. Menjalankan Server & Buka Dashboard
Cukup klik ganda (double-click) file batch:
```cmd
run_server.bat
```
* Server lokal akan aktif di port **`40404`**.
* Browser akan otomatis membuka alamat: **`http://localhost:40404`**.
* **Tidak butuh internet.** Seluruh aset ada di `public/vendor/`.
* Kalau server sudah berjalan, klik kedua akan berhenti dengan pesan
  peringatan (bukan membuat server kedua yang diam-diam menimpa data).

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

### 5. Memperbarui Aset Tampilan (Tailwind / ikon / font)
Hanya bila `index.html` atau `app.js` menambah class Tailwind baru, atau
bila ingin memperbarui versi library:
```cmd
scripts\build_tailwind.bat
python scripts\fetch_vendor.py --force
```
Butuh Node.js (hanya untuk build Tailwind). Runtime tetap 100% offline.

### 6. Menjalankan Tes Regresi

```cmd
REM tanpa server:
python tests\test_rules_unchanged.py
python tests\test_readme_accuracy.py
python tests\test_aturan.py
python tests\test_kurikulum_tree.py
python tests\test_identitas.py

REM dengan server aktif (run_server.bat dulu):
python tests\test_server_http.py
python tests\test_catalog_guard.py
python tests\test_kurikulum_api.py
```

| Tes | Membuktikan |
| --- | --- |
| `test_rules_unchanged.py` | Regenerasi data **tetap identik** dengan master — tidak ada angka yang bergeser |
| `test_readme_accuracy.py` | **Setiap angka di README ini cocok dengan data** — tidak ada lagi angka yang diketik manual dan salah |
| `test_aturan.py` | Ambang At-Risk & grade benar-benar **hidup**: angka bawaan = angka lama, dan mengubah `config/aturan.json` mengubah hasil |
| `test_kurikulum_tree.py` | Tree kurikulum konsisten **anti-drift**: indeks `config/kurikulum.json` == hasil pindai ulang folder |
| `test_identitas.py` | Config identitas sinkron dengan data, **tidak ada nama yang masih di-hardcode di kode**, `simpan()` menolak config rusak, dan template PDF benar-benar mengisi nama (tanpa placeholder bocor). Blok terakhirnya menguji endpoint dan berjalan otomatis kalau servernya hidup. |
| `test_server_http.py` | HTTP/1.1, byte-range video (206/416), path traversal, guard server ganda |
| `test_catalog_guard.py` | Ganti mata kuliah tidak bisa memundurkan data master (termasuk 409 untuk katalog versi lama) |
| `test_kurikulum_api.py` | API tree kurikulum: fail-closed 404/400, bobot ≠ 100 ditolak **tanpa** menulis berkas, suntingan masuk ke tree **dan** katalog, dan status "tebakan vs dikonfirmasi" tidak bisa naik sendiri |

---

## 🗺️ Peta Studi Kasus Demo
Untuk kemudahan demonstrasi di depan Kaprodi, gunakan tombol demo cepat di pojok kanan atas:
1. 🌟 **M Yazid Zidane Mulyadi (NPM 2510015410010)**:
   * Profil mahasiswa unggul (Kompeten Unggul), Kehadiran 100% (16/16 pertemuan), Grade A (94.7).
   * Contoh ideal untuk meninjau pemetaan profesi BIM Modeler (96.5%), Architectural Designer (94.7%), dan DED Specialist (93.2%).
2. ⚠️ **Rozi Andrian Surva (NPM 2510015410011)**:
   * Profil mahasiswa yang membutuhkan pendampingan (3x Alpha + 1x Sakit + 1x Izin, Kehadiran 62.5% — 9 pertemuan penuh + 2 pertemuan hadir sebagian dari 16), **Grade C (60.0)**.
   * Menunjukkan bagaimana sistem **menjaga martabat mahasiswa di depan orang tua**: tidak ada label ranking terbawah (#35), melainkan difokuskan pada talenta imajinasi spasialnya — Site Architect (72.3%), kategori **Sedang**. Angka ini dulu diketik manual sebagai 87% dan sekarang dihitung dari data — bukti bahwa angka yang bagus belum tentu angka yang benar.
3. ✨ **Alsa Dmi Yesya Putri (NPM 2510015410001)**:
   * Profil mahasiswa kreatif konsisten, Kehadiran 93.8% (izin delegasi lomba arsitektur), Grade A (90.8).

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
  * **Grafik Web**: **Donut Progress Ring Kehadiran** (warna adaptif hijau/biru/merah) serta **16-Pertemuan Bar Chart** dengan pill status kehadiran dan garis putus-putus **Benchmark Kehadiran Kelas** (angkanya dibaca dari data, sekarang 85.4%).
  * Rincian log per pertemuan (16 baris), catatan peraturan akademik, dan stempel verifikasi Kaprodi.
* **PDF 1B: Rapor Capaian Studio & Matriks 10 Karier Masa Depan** (`02_rapor_akhir_semester_*.pdf`):
  * Dikirim di akhir semester (2 Halaman Format A4 Portrait).
  * **Halaman 1**: Banner profil mahasiswa dengan Indeks Kesiapan, **Spider-Web Radar Chart 5 Pilar Arsitektur** (5 cincin jaring laba-laba konsentris, bebas clipping teks), tabel rincian nilai **16 pertemuan**, **Grafik Batang Progress Capaian P1-P16**, serta **4 Kuadran Narasi AI Mendalam**.
  * **Halaman 2**: **Matriks 10 Rekomendasi Profesi Riil Masa Depan** (Tabel bergradien dengan visual progress bar kecocokan, badge kategori, pills keterampilan kunci, analisis potensi, dan langkah aksi konkrit).
* **PDF 1C: Slide Deck Portofolio Arsitektur Mahasiswa (DeckCraft)** (`05_deckcraft_portofolio_arsitektur_*.pdf`):
  * Dokumen presentasi arsitektur 4 halaman landscape 16:9 widescreen beresolusi tinggi.
  * Visualisasi teknis: 3D Axonometric Wireframe Villa, Tabel Ketebalan Garis CAD, Denah Arsitektur Skala 1:100 dengan dimensi & notasi ruang, serta Sertifikasi Resmi Berstempel Emas.

### 2. Dokumen untuk Kaprodi:
* **PDF 2: Laporan Penilaian Dosen & Master Gradebook 35 Mahasiswa** (`03_laporan_penilaian_kaprodi_master_gradebook.pdf`):
  * Format **A4 Landscape** eksekutif untuk rapat yudisium dan arsip akreditasi BAN-PT/LAM Teknik.
  * Memuat 5 kartu statistik makro kelas.
  * **Grafik Web Analitik Kelas**:
    1. **Tren Kehadiran per Pertemuan (P1-P16)**: Stacked bar chart mahasiswa Hadir penuh / Hadir sebagian / Absen.
    2. **Distribusi Grade Nilai Kelas**: Histogram sebaran grade nilai huruf (A, A-, B+, B, C, D) seluruh 35 mahasiswa.
  * Master Table 35 mahasiswa **terurut berdasarkan NPM** (tanpa peringkat) dengan log nilai per pertemuan berbobot dan status kelulusan. Angka kelulusan, predikat modus, dan jumlah at-risk dihitung dari data, bukan ditulis manual.

### 3. Dokumen untuk Dosen dari Kaprodi:
* **PDF 3: Laporan Evaluasi Dosen & Keselarasan Kurikulum / Modul RPS** (`04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf`):
  * Laporan audit mutu pengajaran (QA Dosen) dari Kaprodi kepada tim pengampu.
  * Realisasi presensi tim pengajar (100% terlaksana).
  * **Audit Kesesuaian Materi vs Modul RPS**: Evaluasi 16 pertemuan terhadap capaian CPMK/CPL. Rata-rata **87.8%** — *"Terakreditasi Sangat Baik / Memenuhi Standar CPMK & CPL LAM Teknik"*.
  * ⚠️ **Jujur soal angkanya:** `skor_keselarasan` per pertemuan **belum** mengukur
    keselarasan materi yang sesungguhnya. Untuk sementara ia dipakai sebagai
    **proksi persen kehadiran** pertemuan itu (lihat `metodologi_keselarasan` di
    data master). Jadi angka 87.8% berarti "kehadiran kelas", bukan "mutu
    keselarasan RPS". Menggantinya dengan penilaian materi yang benar butuh
    rubrik dari dosen.

---

## 🏛️ Penyesuaian Dinamis Multi-Mata Kuliah (Any Course Adaptability)

Sistem tidak terkunci pada satu mata kuliah. Sejak v2.6, **mata kuliah adalah isi
tree**, bukan daftar yang ditulis tangan di HTML.

* **Empat dropdown berjenjang di header**: **PRODI → TAHUN AJAR → SEMESTER → MK**.
  Isinya dibaca dari `data/kurikulum/` (`GET /api/kurikulum`), jadi daftar yang
  tampil selalu sama dengan isi tree. Daftar MK di `index.html` yang dulu ditulis
  manual — dan sekali salah memuat topik AutoCAD di MK Struktur — **sudah dihapus**.
* **Menambah mata kuliah** = menambah satu folder di tree
  (`data/kurikulum/<PRODI>/<TA>/<SEMESTER>/<KUNCI_MK>/` dengan `penawaran.json`,
  `sesi.json`, `nilai.json`), lalu jalankan `python scripts\parse_data.py`.
  Tidak perlu mengubah kode maupun HTML.
* **Mengubah isi MK** (topik, bobot, jumlah slot absen, jenis MK, semester
  kurikulum) lewat tab **6. Kurikulum** di dashboard — langsung tertulis ke tree
  dan data master + katalog dibangun ulang.
* **Katalog yang tersedia sekarang** (PRODI `Arsitektur`, TA `2025/2026`, GENAP):
  1. `APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS` (AutoCAD, Layer IAI, dan Estimasi Volume QS).
  2. `STUDIO_PERANCANGAN_ARSITEKTUR_2` (Desain Rumah Tinggal, Analisis Tapak & Maket Studi).
  3. `STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1` (Pondasi Dangkal, Kolom Beton & Kuda-kuda Kayu).
* **CLI Parameter**: `python scripts\process_input.py --course "<NAMA_MK>"` masih
  tersedia untuk membangun katalog satu MK dari tree.

---

## 📥 Tata Kelola Folder: Sumber, Artefak, dan Output

Sejak v2.6 ada pemisahan yang jelas: **sumber** (ditulis manusia) vs **artefak build**
(boleh dihapus kapan saja) vs **output** (dokumen siap kirim).

```text
e:\WORKSPACE\KAMPUS_01\
│
├── config/                                      <-- PENGATURAN (ditulis manusia)
│   ├── identitas.json                           <-- satu sumber nama (prodi, dosen, kop)
│   ├── aturan.json                              <-- ambang At-Risk, grade, aturan kehadiran
│   └── kurikulum.json                           <-- indeks tree (DIBUAT, jangan diedit tangan)
│
├── data/
│   ├── kurikulum/                               <-- ★ SUMBER KEBENARAN (ditulis manusia)
│   │   └── <PRODI>/<TAHUN AJAR>/<SEMESTER>/<KUNCI_MK>/
│   │       ├── penawaran.json                   <-- identitas MK di semester ini
│   │       ├── sesi.json                        <-- 16 pertemuan: topik/bobot/slot absen
│   │       └── nilai.json                       <-- baris nilai & presensi per mahasiswa
│   │
│   ├── academic_data.json                       <-- [ARTEFAK] master; dibaca dashboard & PDF
│   ├── courses/<MK>.json                        <-- [ARTEFAK] katalog per MK
│   └── _backup/                                 <-- cadangan otomatis sebelum menulis
│
├── input/                                       <-- ARSIP LAMA (tidak lagi jadi sumber data)
│   └── raw|processed/                           <-- kerangka lama untuk Excel/PDF mentah
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
├── generated_pdfs/                              <-- Salinan PDF yang ikut disimpan di repo
├── process_input.bat                            <-- Bangun katalog / sinkron dari tree
├── run_server.bat                               <-- Menjalankan Server (Port 40404)
└── stop_server.bat                              <-- Mematikan Server Bersih
```

**Mau membangun ulang semuanya?** Cukup:

```cmd
python scripts\migrasi_kurikulum.py --force
python scripts\parse_data.py
```

`migrasi_kurikulum.py` merapikan isi tree (termasuk menandai topik yang masih
`(belum diisi - menunggu RPS)`), lalu `parse_data.py` membangun master + semua
katalog dari tree. Keduanya **idempoten** — boleh dijalankan berkali-kali tanpa
menggeser angka (dijaga `test_kurikulum_tree.py` dan `test_rules_unchanged.py`).

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

---

## 🧾 Catatan Teknis: Yang Sudah Dibetulkan & Sisa Utang

Ditulis apa adanya supaya angka di sistem ini tidak pernah "lebih pandai" dari
kenyataannya.

### Sudah dibetulkan

| Tahap | Isi | Mengubah angka? |
| --- | --- | --- |
| **A** | Server threading + bind `127.0.0.1`, path traversal ditutup, error JSON valid, penulisan atomic + lock, fallback `students[0]` dihapus | Tidak |
| **B** | Alpha (0) ikut dihitung, bobot sesi 15/15/15/20/15/20 dipakai *(digantikan bobot 16 pertemuan di E-1)*, satu aturan At-Risk (`Alpha ≥ 2x ATAU Kehadiran < 75%`), peringkat dihapus, predikat/grade dihitung ulang, kursus ganti tidak lagi kehilangan topik & tanggal | **Ya** (sudah diregenerasi) |
| **C-1** | Seluruh aset dikunci lokal (`public/vendor/`) — dashboard jalan offline; Tailwind dibangun statis; font `Plus Jakarta Sans` & `JetBrains Mono` akhirnya benar-benar terpakai | Tidak |
| **C-2** | HTTP/1.1 + byte-range: video bisa di-*seek*, dikirim per 64 KB; server menolak dijalankan dua kali | Tidak |
| **C-3** | Persona mahasiswa terikat **NPM**, bukan nomor baris Excel | Tidak (dibuktikan identik) |
| **C-4** | Aturan nilai/At-Risk/predikat dipindahkan ke satu modul `scripts/kelas_rules.py` — tidak ada lagi salinan yang bisa berbeda | Tidak (dibuktikan identik) |
| **C-5** | Penjaga katalog: katalog MK yang lebih lama tidak bisa lagi memundurkan data master | Tidak |
| **D-1** | Identitas (mata kuliah, dosen, asisten, ketua prodi, institusi) jadi **satu sumber** di `config/identitas.json` + tab **5. Pengaturan**. NIP, kota, dan tanggal tanda tangan yang dulu literal di dalam template PDF kini ikut config. Kotak tanda tangan "Dosen Pengasuh II" juga tidak lagi gagal (`IndexError`) kalau mata kuliah hanya punya satu dosen. Angka `35` pada label ikut dihitung dari data. | Tidak (dibuktikan identik) |
| **D-2** | Penulisan JSON memakai LF eksplisit — `data/academic_data.json` tidak lagi berubah byte-nya (LF→CRLF) setiap kali ditulis server/parse_data, sehingga "data master tidak tersentuh" bisa benar-benar dibuktikan | Tidak |
| **E-1** | Tree kurikulum bertingkat **PRODI → TAHUN AJAR → SEMESTER → MK**; satu semester = **16 pertemuan**; bobot per pertemuan diatur di tree (wajib Σ = 100). Satuan tampilan diseragamkan jadi **Pertemuan** — penyebut "6 sesi" yang lama memang salah dan dihapus | **Ya** (sudah diregenerasi) |
| **E-2** | Berkas Excel & PDF mentah **dilepas**. Sistem berdiri sendiri dari tree; README memuat kontrak data pengganti untuk input portal | Ya |
| **E-3** | RNG dibangkitkan **per NPM** (`random.Random(42 + npm)`) untuk absen **dan** nilai — menambah satu mahasiswa tidak lagi menggeser nilai seluruh kelas | **Ya** (sudah diregenerasi) |
| **E-4** | "Ganti MK" tidak lagi menyalin katalog ke master: penunjuk `mata_kuliah_aktif` dipindah, lalu master + seluruh katalog dibangun ulang dari tree. Penjaga katalog lama (409) tetap dipasang sebagai jaring pengaman | Tidak |
| **E-5** | Tab **6. Kurikulum**: ubah topik/bobot/slot/jenis_mk/semester_kurikulum dari dashboard, dengan validasi Σ bobot = 100 dan status "tebakan awal" yang tidak bisa naik sendiri jadi "dikonfirmasi" | Tidak |
| **E-6** | Ambang At-Risk & aturan grade dipindah ke `config/aturan.json` (angka bawaan = angka lama, jadi hasil tidak bergeser sampai diubah) | Tidak |
| **E-7** | "Hadir Sebagian" ditampilkan apa adanya — badge sendiri, filter sendiri, dan seri tersendiri di grafik tren — tidak lagi dibulatkan jadi Hadir/Alpha | Tidak |
| **E-8** | Tombol **"Cetak Ulang Paket PDF" (Tingkat 3) diuji ujung-ke-ujung**: 11 PDF arsip tercetak dari data v2.6 dalam 12,8 detik, tanpa error. `jenis_mk` & `semester_kurikulum` ketiga MK juga sudah dikonfirmasi kaprodi lewat tab 6 | Tidak |

### Sisa utang (belum dikerjakan)

1. **Nilai per pertemuan masih sintetis** (`rng.randint`), bukan hasil koreksi
   nyata dosen. Angkanya deterministik per NPM (E-3), tetapi tetap **bukan nilai
   resmi**. Ganti dengan data asli lewat kontrak di bagian *Sumber Data* — aturan
   di `kelas_rules.py` siap dipakai apa adanya.
2. **Alpha = 0 mutlak.** Belum ada jalur "tugas pengganti" bagi mahasiswa yang
   alpha. Ini keputusan akademik, bukan keputusan teknis — perlu kebijakan dosen
   sebelum dibuatkan fiturnya.
3. **Topik sebagian MK masih placeholder.** Dari tree sekarang: 6 pertemuan
   terisi, 10 masih `(belum diisi - menunggu RPS)`. Isinya menunggu RPS resmi
   dari dosen pengampu; jangan dikarang.
4. **`output/` menyimpan puluhan direktori run lama** (riwayat cetak PDF). Belum
   ada kebijakan retensi, jadi repo terus membesar setiap kali paket PDF dicetak.
   Yang terbaru selalu ditunjuk `output/latest_run.json`; direktori lama boleh
   dihapus manual kalau tidak diperlukan sebagai arsip.
5. **`sanitize_folder_name` masih ada salinan yang lebih longgar** di
   `generate_pdfs.py` (~baris 104) dan `video_composer.py` (~baris 43). Versi
   ketat sudah ada di `scripts/kurikulum_tree.py`, tetapi dua salinan itu belum
   diseragamkan — jadi nama MK dengan karakter aneh bisa dinormalisasi berbeda.
6. **`generate_pdfs.py` masih mengimpor `playwright` di baris paling atas.**
   Aman selama dependensi terpasang, tetapi membuat modul tidak bisa dipakai
   untuk sekadar membaca data.
7. **Baris kementerian dan alamat pada kop surat masih literal** di
   `generate_pdfs.py` (`KEMENTERIAN PENDIDIKAN TINGGI, SAINS, DAN TEKNOLOGI` dan
   baris Gedung/Lab/Telp). Itu bukan identitas prodi, jadi sengaja belum dipindahkan
   ke config; ubah di situ bila perlu.
8. **`openpyxl` dan `pypdf` sudah tidak dipakai** (tidak ada lagi impor di kode),
   tetapi masih tertulis di `requirements.txt`. Aman dibiarkan; menghapusnya
   mempercepat `setup.bat` sedikit. Belum dihapus karena itu keputusan dependensi.
9. **`REQUIREMENTS.md` dan `WORKFLOW_MAPPING.md` baru diberi catatan pembuka**,
   isinya belum ditulis ulang mengikuti alur tree. `README.md` yang berlaku.

> Status data demo: `versi 2.6-KURIKULUM-BERTINGKAT` (stempel build terakhir ada di
> `data/academic_data.json` → `metadata.build_id`).
> Angka pada README ini adalah angka data demo (presensi & nilai sintetis),
> bukan hasil penilaian resmi dosen.

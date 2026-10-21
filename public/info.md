# SIAK-KAPRODI — Penjelasan Sistem

> **Sistem Intelijen Akademik & Rekap Portofolio Arsitektur.**
> Dashboard lokal (port **40404**) yang mengubah data perkuliahan menjadi rekap Kaprodi,
> rapor wali murid, portofolio mahasiswa, dan paket PDF resmi — **tanpa internet**.
> Termasuk analisis kekuatan/potensi tiap mahasiswa dan kabar progres untuk wali murid.

Versi dokumen: **v2.7 (Kelebihan & Nilai Jual)** — basis data tetap
`2.6-KURIKULUM-BERTINGKAT`. Halaman ini membaca berkas `public/info.md`, jadi isinya
bisa diperbarui tanpa mengubah kode program.

---

## 1. Apa yang sistem ini kerjakan

Sistem ini mengambil **satu sumber data** (tree kurikulum), lalu menurunkannya menjadi
banyak keluaran yang saling konsisten:

- **Rekap Kaprodi** — kehadiran per slot absen, nilai terbobot, mahasiswa At-Risk, distribusi grade.
- **Rapor wali murid** — narasi humanis tanpa peringkat kompetitif, radar 5 pilar, 10 rekomendasi profesi.
- **Portofolio mahasiswa** — slide deck 16:9 dan video vertikal 9:16.
- **Paket PDF resmi** — 11 berkas arsip (rekap bulanan, rapor semester, deck portofolio, gradebook Kaprodi, evaluasi dosen/RPS).
- **Pesan WhatsApp** — format sopan siap kirim ke orang tua, dengan 3 lampiran PDF.

Prinsipnya: **angka dihitung, bukan diketik**. Semua dokumen membaca data yang sama,
jadi tidak ada dua dokumen yang saling bertentangan.

---

## 2. Kelebihan sistem & nilai jual

Keunggulannya bukan "banyak fitur", tetapi **satu data yang sama dipakai ulang untuk
tiga audiens sekaligus**: Kaprodi (kontrol), mahasiswa (portofolio), dan wali murid
(kabar progres). Tidak ada angka yang diketik dua kali, jadi tidak ada versi yang
saling bertentangan.

### 2.1 Satu data, banyak keluaran yang konsisten

- KPI, rapor, portofolio, PDF, dan pesan wali membaca `data/kurikulum/` yang sama.
- Ubah satu nilai atau topik → semua keluaran ikut berubah saat dikompilasi ulang.
- Tidak ada "rekap versi Excel" yang bisa berbeda dari dashboard.

### 2.2 Portofolio otomatis per mahasiswa

Setiap mahasiswa punya bahan presentasi yang dibuat sistem, bukan template kosong:

| Keluaran | Isi | Dipakai untuk |
|---|---|---|
| Deck 16:9 (4 slide) | identitas, capaian studio, radar kompetensi, pemetaan karier | presentasi studio, beasiswa, magang |
| Video 9:16 (MP4) | naskah voiceover + visual dari data yang sama, dirender per NPM | status media sosial, profil singkat |
| Rapor PDF | rekap pertemuan + narasi + lampiran | arsip wali/dosen |

Semua bisa dipratinjau di dashboard dan diunduh per mahasiswa. Tidak perlu desain
manual per anak — pekerjaan yang biasanya menghabiskan waktu asisten/dosen.

### 2.3 Analisis kekuatan & potensi (bukan sekadar nilai)

> Sejak 21 Oktober 2026 matriks karier **berbukti**: tiap baris karier punya
> field `bukti` (angka nyata MK/kanal yang mendasari skor), narasinya dibangun
> dari angka itu (bukan kalimat statis), dan karier sebidang ditimbang bukti
> kanal — bukan bonus datar. Narasi 3 karier teratas bisa dirapikan engine
> Gemini rotary (tombol "Rapikan dengan AI" di Tab 9); angka di hasil AI
> diverifikasi harus muncul di bukti — satu angka karangan = dibuang.

- **Radar 5 pilar**: penguasaan CAD, ketelitian detail, kedisiplinan asistensi,
  logika ruang & struktur, manajemen waktu.
- **Matriks 10 profesi**: persentase kecocokan, bidang industri, keterampilan kunci,
  dan saran pengembangan (BIM Modeler, QS, perancang DED, visualizer 3D, dst.).
- **Narasi 4 kuadran**: karakter spasial, proyeksi potensi, catatan penguatan, dan
  panduan pendampingan untuk wali.
- **Indeks Kesiapan Profesi** + predikat, dihitung dari nilai terbobot dan kehadiran.
- **Tanpa ranking**: fokus pada pertumbuhan, bukan membandingkan anak.

> Jujur: selama `nilai.json` masih sintetis, analisis ini **indikatif**. Persentase
> karier adalah indikator dari skor kompetensi (bukan tes psikometri), dan nilai
> radar berasal dari arketipe persona per NPM. Setelah nilai asli masuk, angkanya
> ikut menjadi nyata — rumusnya tidak berubah.

### 2.4 Wali murid tahu progres anaknya

Tab 4 menyiapkan pesan WhatsApp sopan + **3 lampiran PDF**: rekap kehadiran, rapor
akhir semester, dan deck portofolio.

- Wali menerima kabar konkret: kehadiran, nilai, kekuatan, dan saran pendampingan.
- Pengiriman **manual** (salin pesan → kirim sendiri). Tidak ada spam otomatis,
  tidak ada API pihak ketiga, dan tidak ada data anak yang diunggah ke layanan luar.
- Pesan menyebut apa yang bisa dibantu wali di rumah, bukan hanya angka.

### 2.5 Efek soft marketing (alami, bukan iklan berbayar)

Tab 3 menyediakan tombol **Salin Caption Instagram** (caption + hashtag) berdampingan
dengan video 9:16 dan deck PDF. Ketika wali membagikannya:

- prodi terlihat **transparan dan modern** — bukti proses belajar, bukan janji brosur;
- kontennya sudah berbentuk visual siap posting, tanpa perlu desain tambahan;
- biaya akuisisi nol: yang bekerja adalah kepuasan wali, bukan anggaran iklan;
- calon mahasiswa/orang tua lain melihat kualitas output prodi dari karya nyata.

Ini **efek**, bukan jaminan. Sistem tidak mengunggah apa pun ke media sosial dan
tidak mengklaim kenaikan pendaftaran; yang disediakan adalah bahan dan pesan yang
layak dibagikan.

### 2.6 Efisiensi & tata kelola

- Paket **11 PDF resmi** dibuat otomatis dan bisa dicetak ulang dari tab 5.
- Impor portal tervalidasi: staging → ditinjau → backup → tulis atomik; impor dua
  kali tidak menggandakan baris.
- **Offline**: aset lokal, data tidak keluar dari komputer kampus.
- **Fail-closed**: bobot ≠ 100, berkas rusak, atau data non-sintetis → berhenti dan
  lapor, bukan menimpa diam-diam.
- Jejak audit: SHA-256 berkas asli + backup bertanggal.

### 2.7 Ringkasan nilai untuk tiap audiens

| Audiens | Yang langsung didapat | Nilai jualnya |
|---|---|---|
| Kaprodi | kontrol kelas, daftar At-Risk, PDF resmi, audit impor | keputusan cepat, dokumen siap tanda tangan |
| Mahasiswa | portofolio + analisis potensi + saran karier | bekal presentasi, magang, beasiswa |
| Wali murid | kabar progres + rapor + portofolio | rasa dilibatkan, bukan hanya nilai akhir |
| Prodi (brand) | output visual konsisten dari setiap mahasiswa | bukti mutu yang bisa dibagikan tanpa biaya iklan |

### 2.8 Yang sengaja tidak diklaim

- Bukan sistem akreditasi dan tidak mencetak klaim akreditasi.
- Bukan pengganti penilaian dosen; nilai tetap berasal dari data perkuliahan.
- Bukan alat ranking/seleksi; tidak ada peringkat kompetitif.
- Bukan chatbot AI generatif untuk rapor; narasi dihitung dari aturan, bukan model.
- Belum mengirim WhatsApp otomatis; pengiriman tetap dilakukan manusia.

---

## 3. Alur data yang sudah berjalan

```text
data/kurikulum/<PRODI>/<TAHUN AJAR>/<SEMESTER>/<MK>/
├── penawaran.json   identitas MK: kode, SKS, dosen, kelas, jadwal, jenis_mk
├── sesi.json        16 pertemuan: topik, bobot, jumlah slot absen
└── nilai.json       presensi + nilai per mahasiswa per slot
        │
        ▼
scripts/parse_data.py  (kompilasi, tidak mengarang angka)
        │
        ├──▶ data/academic_data.json   master untuk MK aktif
        ├──▶ data/courses/<MK>.json    katalog tiap MK
        └──▶ config/kurikulum.json     indeks tree (turunan)
        │
        ▼
server.py (Python stdlib, port 40404) ──▶ REST API ──▶ public/app.js (SPA offline)
        │
        ├──▶ 10 tab dashboard (lihat bagian 4)
        └──▶ output/<MK>/<TIMESTAMP>/  11 PDF + manifest.json
```

Yang **boleh dihapus kapan saja**: `data/academic_data.json`, `data/courses/`,
`config/kurikulum.json`, dan isi `output/`. Semuanya artefak build — jalankan
`python scripts\parse_data.py` dan terbentuk kembali. Yang **tidak boleh hilang**:
isi `data/kurikulum/` dan `config/identitas.json`.

---

## 4. Sepuluh tab dashboard

| Tab | Nama | Fungsi utama | Sumber data |
|---|---|---|---|
| 1 | Dashboard Kaprodi | **Kompetensi-first ( reposisi 2026-10-21)**: KPI Nilai/Kesiapan/Kompetensi/Pendampingan, tren nilai kelas, radar kelas, **peta MK rawan lintas semester**; presensi tetap lengkap di bagian bawah collapsible "Konteks Presensi" | `academic_data.json` + tree (`/api/periode`) |
| 2 | Rapor Wali Murid | Rapor per mahasiswa, radar 5 pilar, matriks 10 karier | `academic_data.json` |
| 3 | Portofolio & Video Progres | Deck 16:9, pratinjau + unduh video 9:16, salin caption Instagram | `output/`, `public/videos/` |
| 4 | Simulator WhatsApp | Pesan ke wali murid + tautan 3 lampiran PDF | `output/` |
| 5 | Pengaturan | Identitas institusi/dosen, terapkan ke dokumen, cetak ulang PDF | `config/identitas.json` |
| 6 | Kurikulum | Sunting topik, bobot, slot absen, jenis MK (Σ bobot wajib 100) | `data/kurikulum/` |
| 7 | Info | Halaman penjelasan ini | `public/info.md` |
| 8 | Rekap Periode | Rekap 4 level: per bulan, per MK, semua MK satu semester, semua semester — dihitung dari tree | `/api/periode` |
| 9 | Portofolio Mahasiswa | Portofolio 4 lapis + analisis potensi dari nilai (kanal bidang, dimensi khas, matriks karier) | `/api/portofolio` |
| 10 | Engine | Pindai inbox, audit integritas berkas, rapikan, lapis kirim | `data/engine/` |

Tab 5 memakai **tiga tingkat** perubahan supaya dokumen resmi tidak berubah diam-diam:
**Simpan Identitas** (label dashboard) → **Terapkan ke Dokumen** (data master + PDF
diregenerasi) → **Cetak Ulang Paket PDF**. Tingkat 3 ditolak bila identitas belum diterapkan.

---

## 5. Aturan akademik yang dipegang sistem

### 5.1 Nilai akhir terbobot

```text
Nilai Akhir = Σ (Skor Pertemuan × Bobot Pertemuan) / Σ Bobot Pertemuan
```

Satu semester = **16 pertemuan**. Bobot diatur per mata kuliah di `sesi.json` dan
jumlahnya wajib **tepat 100**; kalau tidak, dashboard menolak menyimpan (HTTP 422).
**Alpha bernilai 0 dan tetap dihitung** — tidak ada nilai gratis untuk ketidakhadiran.

### 5.2 Pertemuan yang belum diinput

Kalau slot absen satu pertemuan belum lengkap, pertemuan itu ditandai
**"Belum Diinput"** — **bukan Alpha**, **bukan nilai 0**. Pertemuan tersebut keluar
dari rata-rata (bobot dinormalisasi ulang) dan grade mahasiswa ditahan
**"Belum Lengkap"** sampai datanya lengkap.

### 5.3 Predikat grade

| Grade | Syarat |
|---|---|
| A | rata-rata ≥ 85 dan kehadiran ≥ 80% |
| A- | rata-rata ≥ 80 dan kehadiran ≥ 75% |
| B+ | rata-rata ≥ 75 dan kehadiran ≥ 75% |
| B | rata-rata ≥ 70 |
| C | rata-rata ≥ 60 |
| D / Evaluasi | rata-rata < 60 |
| Belum Lengkap | masih ada pertemuan yang presensinya belum diinput |

Ambang kehadiran hanya mengunci **predikat**, bukan kelulusan. Semua ambang hidup di
`config/aturan.json` dan dibaca oleh `scripts/aturan.py` (fail-closed bila rusak).

### 5.4 Deteksi dini At-Risk

```text
At-Risk  ⇔  (Alpha ≥ 2×)  ATAU  (Kehadiran < 75%)
```

Hanya ada **satu** definisi, di `scripts/kelas_rules.py`. Badge tabel, kartu KPI,
PDF gradebook, dan rapor wali membaca hasil yang sama.

### 5.5 Zero Competitive Ranking

Tidak ada peringkat mahasiswa di dashboard, PDF, maupun pesan wali murid. Tabel
disortir berdasarkan NPM; kolom pertama adalah nomor absen resmi.

---

## 6. Sumber kebenaran dan struktur folder

```text
KAMPUS_01/
├── config/
│   ├── identitas.json     satu sumber nama (prodi, dosen, asisten, kop)
│   ├── aturan.json        ambang At-Risk, grade, aturan kehadiran
│   ├── kurikulum.json     indeks tree (DIBUAT, jangan diedit tangan)
│   └── impor/             profil pemetaan kolom portal/modul
├── data/
│   ├── kurikulum/         ★ SUMBER KEBENARAN (ditulis manusia)
│   ├── courses/           artefak katalog per MK
│   ├── academic_data.json artefak master untuk MK aktif
│   ├── _backup/           cadangan otomatis sebelum menulis
│   └── _staging/          usulan impor/AI yang belum disetujui
├── input/
│   ├── inbox/             taruh berkas portal di sini
│   └── raw/<stempel>/     arsip asli + SHA-256 + meta.json
├── output/                paket PDF per run + manifest.json
├── public/                index.html, app.js, style.css, info.md, vendor/ (offline)
├── scripts/               mesin: tree, aturan, parse, PDF, video, impor/
├── tests/                 tes regresi (angka, dokumen, API, keamanan, impor)
└── server.py              server stdlib, port 40404
```

### Cara menjalankan

```cmd
run_server.bat                          :: server + buka http://localhost:40404
stop_server.bat                         :: matikan server dengan bersih
python scripts\parse_data.py            :: bangun ulang master + katalog dari tree
python scripts\migrasi_kurikulum.py --force
python scripts\seed_nilai_sintetis.py --force
generate_all_pdfs.bat                   :: cetak ulang paket PDF

:: jalur impor (lihat bagian 8)
python -m scripts.impor.cli pindai
python -m scripts.impor.cli impor --folder input/inbox
```

Urutan yang benar bila struktur atau nilai berubah: **migrasi → seed (opsional) →
parse_data → cetak PDF**. Kedua skrip pertama idempoten dan tidak menghapus hasil
suntingan manusia.

---

## 7. Prinsip kejujuran data

Sistem ini memilih **mengaku belum tahu** daripada mengarang angka:

| Hal | Status sekarang | Penanda |
|---|---|---|
| Nilai & presensi per pertemuan | **sintetis** (dibangkitkan deterministik per NPM + MK) | `nilai.json` → `"sintetis": true` |
| Topik pertemuan | sebagian masih placeholder | `topik_terverifikasi` di `sesi.json` |
| CPMK per pertemuan | placeholder | `cpmk_status = "placeholder"` |
| Keselarasan materi vs RPS | proksi persen kehadiran kelas, bukan mutu materi | `status_penilaian_rps = "belum_tersedia"` |
| Presensi dosen | belum pernah dicatat | ditulis apa adanya di PDF 3 |
| Nama universitas di kop | sengaja kosong | `config/identitas.json` |
| Klaim akreditasi | **tidak pernah** diklaim | dihapus dari semua dokumen |

Data asli dari portal masuk lewat **kontrak baris** yang sama: `npm`, `pertemuan`,
`slot`, `status`, `skor` (+ `alasan` opsional). Jangan menulis `nilai.json` dengan
tangan; pakai `scripts/impor` supaya tervalidasi, terbackup, dan ada jejak audit
(lihat bagian 8).

---

## 8. Status pengembangan (jujur, per 21 Oktober 2026)

> Bagian ini memisahkan **yang sudah ada kodenya** dari **yang masih rencana**.
> Fitur yang belum aktif tidak boleh dibaca sebagai klaim.

### 8.1 Sudah aktif — tombol di Tab 10 Engine + CLI tinjau/terima

**Impor nilai dari portal (Excel / CSV / HTML)** — pemindaian inbox, audit
duplikat, dan audit output kini punya tombol di **Tab 10 Engine**; peninjauan
staging masih lewat CLI:

```text
input/inbox/  →  deteksi isi  →  baca tabel  →  baris kanonik  →  validasi
              →  data/_staging/ (usulan + diff)
              →  DITINJAU MANUSIA  →  data/_backup/  →  nilai.json
```

```cmd
python -m scripts.impor.cli pindai
python -m scripts.impor.cli impor --folder input/inbox
python -m scripts.impor.cli tinjau data/_staging/<folder>
python -m scripts.impor.cli terima data/_staging/<folder>
```

Yang sudah dijamin kode + tes:

- Format dikenali dari isi (magic bytes), bukan ekstensi; `.xls`/`.doc` lama ditolak.
- Kolom dipetakan lewat `config/impor/*.json`; header asing = berhenti, bukan ditebak.
- Slot di luar `sesi.json`, Alpha berskor bukan 0, atau NPM asing → seluruh impor batal
  dan pesannya menyebut berkas + nomor baris.
- `terima` membackup `nilai.json` dulu; impor dua kali tidak menggandakan baris.
- Data yang sudah **diverifikasi manusia** (bukan sintetis, bukan hasil impor)
  ditolak tanpa `--paksa`.
- Berkas asli diarsipkan ke `input/raw/<stempel>/` + SHA-256 + `meta.json`.

**Ekstraksi & analisis modul (PDF / DOCX)**

```cmd
python -m scripts.impor.cli modul "input/inbox/RPS.pdf"
python -m scripts.impor.cli usul  "input/inbox/RPS.pdf"
python -m scripts.impor.cli terima-sesi data/_staging/<folder>
```

- PDF tanpa text layer ditandai `ocr_dibutuhkan` — isinya tidak dikarang.
- AI memakai **engine Gemini rotary milik pengguna** (bukan API berbayar baru).
  Hasilnya staging berstatus `tebakan`; hanya topik/deskripsi yang bisa masuk
  `sesi.json`, setelah lolos validasi 16 pertemuan dan aturan Σ bobot = 100.
- Belum ada tombol "ajukan/tinjau" di tab 6; sementara lewat CLI.

### 8.2 Sebagian aktif — penangkap portal (login manual)

```cmd
python -m scripts.impor.cli portal --url "https://portal.kampus/..." --halaman 2
```

- Browser terbuka; **Kaprodi login sendiri** (skrip tidak menyimpan/membaca sandi).
- Setelah halaman siap, skrip menyimpan HTML + screenshot + tabel ke
  `input/raw/<stempel>/` dan `input/inbox/`, lalu alurnya sama dengan 7.1.
- Halaman tanpa tabel **tidak dikarang**: hanya diarsipkan sebagai HTML/screenshot
  dengan catatan untuk dibaca manusia atau AI vision.

Yang **belum** ada:

- login otomatis / penanganan 2FA (memang sengaja tidak dilakukan),
- navigasi menu portal otomatis dan penjadwalan tangkapan,
- tombol unggah dan panel tinjau/terima di dashboard (masih CLI).

Prasyarat: akun resmi Kaprodi dan izin/kebijakan kampus. Kalau penangkap tidak
bisa dipakai, jalur cadangannya tetap **unduh manual → `input/inbox/`**.

### 8.3 Urutan yang tersisa

| Tahap | Pekerjaan | Status |
|---|---|---|
| R1 | Skema baris + konverter tabel + validasi | **selesai (CLI)** |
| R3 | Ekstraksi teks PDF/DOCX + arsip sumber | **selesai (CLI)** |
| R4 | Analisis AI berskema + status `tebakan` | **selesai (CLI)** |
| R2 | Penangkap portal | **sebagian**: login manual + tangkap tabel; belum otomatis penuh |
| R5 | Panel tinjau/terima di tab 6 | belum |
| R6 | OCR gambar/screenshot (vision) di alur penuh | belum (baru penanda) |

---

## 9. Batasan yang perlu diketahui

- Dashboard berjalan **offline**; seluruh aset ada di `public/vendor/`. Tidak ada
  permintaan ke internet saat halaman dibuka.
- Server hanya mendengarkan di `127.0.0.1` dan menolak dijalankan dua kali di port
  yang sama.
- Nilai yang tampil sekarang adalah **data demo sintetis**, bukan nilai resmi dosen.
  Ganti lewat `scripts/impor` (bagian 8) sebelum dipakai untuk keputusan akademik.
- Setiap perubahan aturan (ambang At-Risk, grade, bobot ujian) dilakukan di
  `config/aturan.json`, bukan dengan mengedit kode.
- Render video 9:16 membutuhkan **FFmpeg** di `PATH`; bila tidak ada, dashboard
  menampilkan pesan gagal, bukan video kosong.
- Analisis potensi dan persentase karier adalah **indikator dari data akademik**,
  bukan asesmen psikometri dan bukan alat seleksi.
- Pesan wali dan caption media sosial **disalin lalu dikirim manual**; sistem tidak
  punya akses ke akun WhatsApp/Instagram siapa pun.

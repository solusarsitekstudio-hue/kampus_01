# REQUIREMENTS & SPESIFIKASI SISTEM
## SIAK-KAPRODI: Sistem Intelijen Akademik & Rekap Portofolio Arsitektur

Dokumen ini memuat kebutuhan teknis, dependensi perangkat lunak, konfigurasi
jaringan/port, serta prasyarat lingkungan untuk menjalankan sistem.

> **Riwayat:** sampai v2.5 sistem membaca dua berkas mentah
> (`DAFTAR MAHASISWA.xlsx` dan `02 rekap qs pratikum.pdf`) memakai `openpyxl`
> dan `pypdf`. Sejak **v2.6** dua berkas itu **tidak dipakai lagi** (dianggap
> tidak ada) dan **tidak ada satu baris kode pun yang mengimpornya**. Sumber
> data sekarang **tree kurikulum** `data/kurikulum/<PRODI>/<TAHUN AJAR>/<SEMESTER>/<MK>/`.
> Acuan alur lengkap: `WORKFLOW_MAPPING.md`; acuan angka: `README.md`.

---

### 1. Spesifikasi Perangkat Lunak (Software Stack)

* **Runtime Python**: **3.10+** (wajib; diverifikasi berjalan di **Python 3.14.7**).
  `setup.bat` menolak versi di bawah 3.10.
* **Sistem Operasi**: Windows 10/11 untuk berkas `.bat` (`setup.bat`,
  `run_server.bat`, `generate_all_pdfs.bat`, dll). Skrip Python-nya sendiri
  lintas platform.
* **Web UI**: HTML5 + CSS3.
  * Tailwind CSS = **CSS statis hasil build** (`public/vendor/tailwind.css`), bukan JIT di browser.
  * ApexCharts + Lucide + font = berkas lokal di `public/vendor/`.
  * **Nol permintaan ke internet saat runtime** (`public/index.html` tidak memuat satu URL eksternal pun). Dashboard tetap utuh walau WiFi mati/diblokir kampus.
* **Web Server**: pustaka standar Python (`http.server` + `socketserver`).
  Tanpa Apache/Nginx/FastAPI/Flask, tanpa proses tambahan.
* **Rendering Dokumen**: **Playwright + Chromium** (merender 11 PDF resmi dari HTML/CSS).
* **Rendering Video (opsional)**: `numpy` + `edge-tts` (video 9:16). Kalau tidak
  dipasang, seluruh fitur lain tetap berjalan; hanya tombol video yang gagal.

| Paket (pip) | Wajib? | Dipakai di |
| --- | --- | --- |
| `playwright>=1.40.0` | **Wajib** untuk cetak PDF | `scripts/generate_pdfs.py`, `scripts/video_composer.py` |
| `numpy>=1.26.0` | Opsional (video) | `scripts/video_composer.py` |
| `edge-tts>=6.1.9` | Opsional (narasi video, butuh internet) | `scripts/video_composer.py` |

* **Node.js** hanya dibutuhkan **saat membangun ulang CSS Tailwind**
  (`scripts/build_tailwind.bat`). Tidak perlu ada saat dashboard dijalankan.
* `openpyxl` dan `pypdf` **sudah dihapus** dari `requirements.txt` karena tidak
  ada lagi impor di kode.

**Dependensi eksternal (bukan paket pip, tidak masuk `requirements.txt`)**

| Modul | Berkas | Dipakai untuk | Kalau tidak ada |
| --- | --- | --- | --- |
| `deckcraft_builder` | `E:\WORKSHOP\OPEN_CRAFT_MCP\scripts` (bisa diarahkan lewat env `OPENCRAFT_MCP_SCRIPTS`) | Merender PDF **05_deckcraft_portofolio** (deck 16:9) | Cetak massal: 8 dari 11 PDF tetap jadi + baris `[WARN]` untuk deck. Unduh per-mahasiswa (`/api/pdf/download?type=deckcraft`): gagal dengan pesan `RuntimeError` yang jelas |

`tests/test_docs_dependensi.py` mengunci aturan ini: **setiap impor pihak ketiga
di kode harus tercantum di `requirements.txt`** atau terdaftar sebagai modul
eksternal seperti di atas.

---

### 2. Konfigurasi Port & Jaringan

* **Port standar**: `40404` (khusus instance SIAK-KAPRODI)
* **Base URL**: `http://localhost:40404`
* **Bind**: hanya loopback `127.0.0.1` — tidak terekspos ke jaringan lokal.
* **Protokol**: HTTP/1.1 + JSON API. Mendukung byte-range untuk pemutaran video.

**Endpoint GET**:

| Endpoint | Isi |
| --- | --- |
| `/api/data` | Kompilasi penuh data akademik MK aktif (KPI, sesi, presensi, rekap) |
| `/api/courses` | Daftar katalog mata kuliah (`data/courses/`) |
| `/api/kurikulum` | Index tree kurikulum (`config/kurikulum.json`) |
| `/api/kurikulum/detail?prodi=&tahun_ajar=&semester=&kunci_mk=` | Isi satu MK dari tree (16 pertemuan) |
| `/api/student/<npm>` | Data mendalam satu mahasiswa (profil, radar, diagnosis, karier, pesan WA) |
| `/api/student/images?npm=...` | Berkas gambar pendukung portofolio mahasiswa |
| `/api/deckcraft_html?npm=...` | HTML deck 16:9 untuk pratinjau penuh |
| `/api/identitas` | Identitas institusi (`config/identitas.json`) |
| `/api/pdf/download?type=<TYPE>&npm=<NPM>` | Unduh satu PDF on-demand |
| `/api/runs` | Riwayat direktori hasil cetak (`output/`) |
| `/api/switch_course?course=<KUNCI_MK>` | Pindah MK aktif (memicu kompilasi ulang master) |
| `/api/video/generate?npm=...` | Render video 9:16 |
| `/api/open_folder?path=...` | Membuka folder hasil di Explorer |
| `/output/...`, `/generated_pdfs/...`, `/videos/...` | Penyajian berkas statis hasil |

**Endpoint POST** (semua memakai JSON, fail-closed):

| Endpoint | Isi |
| --- | --- |
| `/api/kurikulum/simpan` | Sunting topik/bobot/slot/jenis_mk/semester_kurikulum; **422** kalau Σ bobot ≠ 100 (tanpa menulis) |
| `/api/identitas/simpan` | Simpan identitas (backup dulu, tulis atomik) |
| `/api/identitas/terapkan` | Terapkan identitas ke data master |
| `/api/identitas/regenerasi-pdf` | Cetak ulang 11 PDF; **409** kalau identitas belum diterapkan |

---

### 3. Prasyarat Lingkungan (Prerequisites)

1. **Python 3.10+** terpasang dan ada di `PATH` (atau sediakan `.venv\Scripts\python.exe`).
2. **Internet** hanya dibutuhkan saat:
   * `setup.bat` mengunduh paket pip + Chromium,
   * `python scripts/fetch_vendor.py` (bila `public/vendor/` kosong),
   * `scripts/build_tailwind.bat` (sekali, butuh Node.js),
   * render narasi video (`edge-tts`).
3. **Ruang disk** ±500 MB (Chromium ±150 MB + aset vendor ±1 MB + PDF/video hasil).
4. **Port 40404 bebas.** `stop_server.bat` mematikan proses yang memakai port itu.

Cara menyiapkan sekali jalan:

```cmd
setup.bat
```

Skrip itu memasang dependensi, mengunduh Chromium, dan membangun
`data/academic_data.json` dari tree **kalau belum ada** (tidak menimpa).

---

### 4. Struktur Direktori Proyek

```text
E:\WORKSPACE\KAMPUS_01\
├── config/
│   ├── aturan.json             # ambang At-Risk, aturan grade, jam_per_sks, slot_belum_diisi
│   ├── identitas.json          # identitas institusi (satu-satunya tempat nama orang)
│   └── kurikulum.json          # INDEX TURUNAN tree (jangan disunting manual)
├── data/
│   ├── kurikulum/<PRODI>/<TAHUN AJAR>/<SEMESTER>/<MK>/
│   │   ├── penawaran.json      # identitas MK, jenis_mk, semester_kurikulum, jadwal
│   │   ├── sesi.json           # 16 pertemuan: tanggal, topik, bobot, slot_absen, tipe
│   │   └── nilai.json          # baris presensi+nilai per slot (sintetis, per MK)
│   ├── kurikulum/<PRODI>/mahasiswa.json      # daftar mahasiswa (canonical)
│   ├── kurikulum/<PRODI>/cetak_biru_mk.json  # cetak biru jenis_mk & semester_kurikulum
│   ├── courses/<MK>.json       # katalog hasil kompilasi (artefak)
│   ├── academic_data.json      # MASTER dataset MK aktif (artefak)
│   └── _backup/                # cadangan otomatis (gitignored)
├── input/
│   ├── raw/                    # berkas mentah per MK (bila ada)
│   ├── processed/              # snapshot olahan per MK + latest_input.json
│   └── progress_mahasiswa/
├── output/<MK>/<TIMESTAMP>/    # 11 PDF + manifest.json; latest_run.json menunjuk terbaru
├── generated_pdfs/             # salinan PDF untuk pratinjau web
├── public/
│   ├── index.html              # SPA 6 tab
│   ├── app.js                  # controller, chart, state
│   ├── style.css               # styling custom & layout cetak
│   ├── vendor/                 # Tailwind build, ApexCharts, Lucide, font (offline)
│   └── videos/                 # hasil render video 9:16
├── scripts/
│   ├── kurikulum_tree.py       # path & baca/tulis atomik, validasi sesi, index
│   ├── persona.py              # persona per NPM + RNG per NPM×MK + nilai sintetis
│   ├── kelas_rules.py          # aturan nilai, grade, At-Risk, Belum Diinput
│   ├── aturan.py               # pembaca + validator config/aturan.json
│   ├── identitas.py            # pembaca/penulis config/identitas.json
│   ├── migrasi_kurikulum.py    # bentuk STRUKTUR tree (16 pertemuan, bobot = 100)
│   ├── seed_nilai_sintetis.py  # regenerasi nilai.json per MK (dry run/--force)
│   ├── parse_data.py           # kompilasi master + katalog dari tree
│   ├── process_input.py        # olah input per MK ke input/processed/
│   ├── index_kurikulum.py      # bangun ulang/periksa index (--check)
│   ├── generate_pdfs.py        # render 11 PDF (Playwright/Chromium)
│   ├── video_composer.py       # render video 9:16 (numpy + edge-tts)
│   ├── fetch_vendor.py         # kunci aset pihak ketiga ke public/vendor/
│   ├── build_tailwind.bat      # bangun ulang CSS Tailwind (butuh Node.js)
│   └── tailwind/               # tailwind.config.js + input.css
├── tests/                      # 12 berkas regresi (lihat WORKFLOW_MAPPING.md)
├── server.py                   # server stdlib, port 40404
├── requirements.txt            # daftar paket pip
├── setup.bat                   # pasang dependensi + Chromium + data awal
├── run_server.bat / stop_server.bat
├── process_input.bat / generate_all_pdfs.bat / generate_video_shorts.bat
├── README.md                   # acuan utama
├── REQUIREMENTS.md             # dokumen ini
└── WORKFLOW_MAPPING.md         # peta alur & arsitektur
```

---

### 5. Sumber Data (Ground Truth = Tree Kurikulum, Bukan Berkas Luar)

Sistem **berdiri sendiri**. Tidak ada Excel/PDF mentah yang dibaca.

1. **Sumber kebenaran**: `data/kurikulum/<PRODI>/<TAHUN AJAR>/<SEMESTER>/<MK>/`
   (`penawaran.json`, `sesi.json`, `nilai.json`) + `mahasiswa.json` per prodi.
2. **`data/courses/` dan `data/academic_data.json` adalah ARTEFAK** hasil
   kompilasi `scripts/parse_data.py`. Kalau berbeda dengan tree, **tree yang benar**.
3. **Presensi & nilai saat ini SINTETIS** (bukan nilai resmi dosen): setiap baris
   ditandai `"sintetis": true`, dibangkitkan deterministik **per NPM dan per mata
   kuliah**. Ganti dengan data portal cukup dengan menulis ulang `nilai.json`
   (kontraknya di `README.md`), tanpa mengubah kode.
4. **Standar struktur**: 1 semester = **16 pertemuan**, Σ bobot = **100**
   (14 × 4 + UTS 20 + UAS 24), tiap pertemuan punya 1+ slot absen.
5. **Data yang belum ada tidak dihukum**: pertemuan dengan slot belum lengkap
   ditandai **"Belum Diinput"**, keluar dari rata-rata terbobot (bobot
   dinormalisasi ulang), dan grade ditahan **"Belum Lengkap"**. Perilaku lama
   (`"alpha"`) bisa dipulihkan lewat `config/aturan.json`.
6. **Penyelenggara perkuliahan** (dibaca dari `config/identitas.json`, bukan diketik di kode):
   * Program Studi: Arsitektur
   * Ketua Program Studi: Fielda Roza, S.T., M.T.
   * Dosen Pengasuh MK (Aplikasi Komputer Arsitektur & QS): Aprilia Yunita, S.T., M.T. & Duddy Fajriansyah, S.T., M.T.
   * Asisten Dosen: Adrian Ridhoa, S.T.
   * Mata kuliah yang dikelola: `APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS` (5412522233),
     `STUDIO_PERANCANGAN_ARSITEKTUR_2` (5412522404),
     `STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1` (5412522302); 35 mahasiswa, GENAP 2025/2026.

---

### 6. Perintah Penting

| Perintah | Fungsi |
| --- | --- |
| `setup.bat` | Pasang dependensi + Chromium + data awal |
| `run_server.bat` / `stop_server.bat` | Nyalakan / matikan server port 40404 |
| `python scripts\migrasi_kurikulum.py --force` | Bentuk ulang STRUKTUR tree (aman: hasil edit manusia dipertahankan) |
| `python scripts\seed_nilai_sintetis.py [--force]` | Dry run / tulis ulang nilai sintetis per MK (backup otomatis) |
| `python scripts\parse_data.py` | Kompilasi master + seluruh katalog dari tree |
| `python scripts\index_kurikulum.py --check` | Cek index vs folder (0 = sinkron) |
| `generate_all_pdfs.bat` | Cetak ulang 11 PDF arsip |
| `generate_video_shorts.bat` | Render video 9:16 |
| `python tests\<nama_tes>.py` | Regresi (lihat `WORKFLOW_MAPPING.md`) |
| `python tests\test_docs_dependensi.py` | Penjaga dokumen & dependensi: impor ↔ `requirements.txt`, nomor port, dan rute `/api` ↔ `REQUIREMENTS.md` |

---

### 7. Sifat & Batasan yang Disengaja

* **Fail-closed**: prasyarat tidak jelas, berkas rusak, bobot ≠ 100, atau upaya
  menimpa data non-sintetis → operasi **berhenti dan melapor**, tidak menebak.
* **Nol biaya API**: seluruh angka & narasi dihitung dari berkas lokal; tidak ada
  panggilan LLM berbayar di dalam sistem ini.
* **Tanpa ranking kompetitif**: urutan berdasarkan NPM, bukan peringkat kelas.
* **Belum final**: sebagian topik pertemuan masih `(belum diisi - menunggu RPS)`
  dan kolom institusi yang belum diketahui sengaja dibiarkan kosong — tidak
  dikarang. Daftar utang lengkap ada di `README.md` bagian *Sisa Utang*.

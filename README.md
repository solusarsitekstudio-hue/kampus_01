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

## 🔗 Keterhubungan dengan Framework OpenCraft MCP
Aplikasi ini dirancang modular agar terhubung langsung dengan engine otomasi di:
`E:\WORKSHOP\OPEN_CRAFT_MCP`
* `carousel-template`: Merender kartu slide Instagram resolusi tinggi (1080x1350 px).
* `filmcraft / shorts-template`: Merender video vertikal 9:16 dengan background musik dan voiceover audio.
* `designcraft`: Tata letak grafis dokumen portofolio arsitektur.
* `deckcraft`: Bahan tayang presentasi evaluasi kurikulum untuk Kaprodi.

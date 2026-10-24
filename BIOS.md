# 🛡️ SYSTEM BIOS CONSTITUTION: SYS_KAMPUS_01

> **STATUS HUKUM: IMMUTABLE (TIDAK BOLEH DIUBAH ATAU DIHAPUS OLEH AGEN AI).**  
> Pelanggaran terhadap aturan di dokumen ini membatalkan seluruh usulan kode secara otomatis.

---

## 🚫 1. PANTANGAN MUTLAK SISTEM (ABSOLUTE PROHIBITIONS)

1. **PASAL PORT KUDUS:**  
   Port resmi sistem ini adalah **`40404`**. Dilarang keras memindahkan, mengalihkan, atau mengubah port ini ke port lain tanpa instruksi eksplisit dari pemilik sistem (Adrian Ridhoa).
2. **PASAL SATU SUMBER KEBENARAN (SINGLE SOURCE OF TRUTH):**  
   Seluruh aturan kelulusan, ambang at-risk, jam teori/studio, dan bobot RPS wajib bersumber tunggal dari `config/aturan.json` dan `data/kurikulum/`. Dilarang keras melakukan *hardcode* nilai kelulusan, persentase kehadiran, atau rumus evaluasi di dalam kode script atau HTML.
3. **PASAL ANTI-FEODALISME & MULTIDISIPLIN (ANTI-IAI LOCK-IN):**  
   Sistem ini menganut prinsip **Mahasiswa adalah Center of the Universe**. Dilarang keras mengurung mahasiswa ke dalam satu organisasi feodal tunggal (seperti glorifikasi *"Standar Studio IAI"*). Sistem wajib memvalidasi potensi multidisiplin (BIM, Computational Design, PropTech, Visual Narrative, Site Supervision, dan Wirausaha Kreatif).
4. **PASAL ZERO REGRESSION ANGKA:**  
   Dilarang keras mengubah atau merusak integritas angka master di `data/academic_data.json` tanpa melalui kompilasi resmi (`scripts/parse_data.py`). Seluruh 6 suite tes regresi (`tests/test_*.py`) wajib lulus 100% sebelum dan sesudah perubahan kode.
5. **PASAL ZERO ZOMBIE PROCESS:**  
   Setiap proses server di Windows wajib memiliki mekanisme pembersihan tuntas PID melalui `STOP_SERVER.bat` (`taskkill /F /T /PID`) agar tidak meninggalkan thread zombie atau port terkunci.

---

## 🗺️ 2. PASAL MUTLAK PETA KABEL (DUAL-MAPPING LAW)

1. **MANDATORY ORIENTATION:**  
   Setiap agen AI yang bertugas memodifikasi, mendebug, atau mengembangkan sistem ini WAJIB membaca `MAPPING_UI.md` dan `MAPPING_SISTEM.md` terlebih dahulu untuk memahami skematik kabel sebelum menyentuh kode.
2. **HUKUM SINKRONISASI DUA ARAH (KODE BERUBAH = PETA BERUBAH):**  
   - Setiap kali ada penambahan, perubahan, atau penghapusan elemen UI (HTML ID, Tombol, Selector, Event JS) ➔ **WAJIB sinkronkan ke `MAPPING_UI.md`**.
   - Setiap kali ada penambahan, perubahan, atau penghapusan endpoint backend, alur data input/output, atau engine skrip ➔ **WAJIB sinkronkan ke `MAPPING_SISTEM.md`**.
   Pekerjaan dinyatakan **CACAT & TIDAK SAH** jika kodingan telah diedit namun file mapping tidak diperbarui.

---

## 📂 3. PASAL STRUKTUR FOLDER BAKU

Dilarang mengubah atau memindahkan fungsi dari organ fisik baku berikut:
- `config/` : Berkas konfigurasi JSON satu sumber.
- `data/` : Dataset master terkompilasi, direktori 35 MK, dan pohon kurikulum.
- `input/` : Folder bahan mentah progres foto mahasiswa per MK.
- `output/` : Arsip hasil run PDF, manifest, dan registri build.
- `generated_pdfs/` : Folder live sync preview PDF untuk akses cepat web UI.
- `public/` : Frontend web assets (HTML, JS, CSS, vendor, videos).
- `scripts/` : Modul engine eksekusi deterministik backend.
- `tests/` : Suite pengujian regresi otomatis penjamin mutu.
- `debug/` & `logs/` : Wadah tangkapan visual dan log murni terisolasi.

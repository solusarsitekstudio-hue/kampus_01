import os
import sys
import json
import re
import shutil
import tempfile
from datetime import datetime

# FIX TAHAP C-4: aturan kelas diimpor dari SATU modul bersama, bukan disalin
# ulang di sini. Sebelumnya konstanta yang sama muncul di 3 file - persis
# pola yang dulu melahirkan 4 aturan at-risk berbeda dalam 1 aplikasi.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kelas_rules import (  # noqa: E402
    AT_RISK_ALPHA_MIN,
    AT_RISK_KEHADIRAN_MIN,
    grade_dari_skor,
    TEKS_GRADE,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "input")
RAW_DIR = os.path.join(INPUT_DIR, "raw")
PROCESSED_DIR = os.path.join(INPUT_DIR, "processed")
DATA_DIR = os.path.join(BASE_DIR, "data")
COURSES_DIR = os.path.join(DATA_DIR, "courses")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(COURSES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def atomic_write_json(path, payload):
    """Tulis JSON lewat file .tmp lalu os.replace() (atomic di Windows & POSIX).
    FIX TAHAP A: dulu open(path,"w") langsung men-truncate file. Kalau listrik
    mati di tengah json.dump, academic_data.json jadi 0 byte dan SEMUA endpoint
    server mati total. Sekarang file lama utuh sampai file baru siap 100%."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def backup_file(path):
    """Simpan 1 salinan bertimestamp sebelum ditimpa."""
    if not os.path.exists(path):
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_dir = os.path.join(BASE_DIR, "data", "_backup")
    os.makedirs(bak_dir, exist_ok=True)
    bak_path = os.path.join(bak_dir, f"{os.path.basename(path)}.{stamp}.bak")
    try:
        shutil.copy2(path, bak_path)
        return bak_path
    except OSError:
        return None


def sanitize_folder_name(name):
    """Normalisasi nama mata kuliah menjadi nama folder yang ROUND-TRIP.

    FIX TAHAP B: versi lama hanya menghapus `\\/*?:"<>|`, jadi kurung, koma,
    dan tanda kutip TETAP ADA:
        "Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)"
        -> STUDIO_PERANCANGAN_ARSITEKTUR_2_(DESAIN_RUMAH_TINGGAL)
    Tapi kuncinya di disk adalah STUDIO_PERANCANGAN_ARSITEKTUR_2.
    Akibatnya-course 2 & 3 tidak ketemu saat dicari, dan pencarian foto
    mahasiswa jatuh ke fallback (dulu: folder D:\\Desktop milik developer).

    Sekarang: kurung/koma/kutip -> "_",underscore dirapatkan,
    nama terlarang Windows (CON, PRN, AUX, NUL, COM1..9) di-prefix.
    """
    if name is None:
        return ""
    clean = re.sub(r'[\\/:*?"<>|().,\'’“”]+', "_", str(name))
    clean = clean.replace("&", "DAN")
    clean = re.sub(r"\s+", "_", clean.strip())
    clean = re.sub(r"_+", "_", clean).strip("_").upper()
    if not clean:
        return ""
    if re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)", clean):
        clean = "MK_" + clean
    return clean[:120]


def course_folder_key(nama_mk):
    """Kunci katalog yang stabil: ambil bagian sebelum kurung buka.

    "Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)" -> STUDIO_PERANCANGAN_ARSITEKTUR_2
    Dipakai supaya DEFAULT_COURSES (kunci polos) dan nama folder di disk
    selalu cocok.
    """
    base = re.split(r"[(\[]", str(nama_mk))[0]
    return sanitize_folder_name(base)

# Course Catalog Templates for Architecture Department
DEFAULT_COURSES = {
    "APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS": {
        "kode_mk": "5412522233",
        "nama_mk": "Aplikasi Komputer Arsitektur & QS",
        "prodi": "Arsitektur",
        "fakultas": "Teknik & Desain",
        "semester": "Genap 2025/2026",
        "sks": 2,
        "kelas": "TEKZA (Lab LIKDA)",
        "jadwal": "Rabu, 10:10 - 15:50 WIB",
        "ketua_prodi": "Fielda Roza, S.T., M.T.",
        "dosen_pengasuh": ["Aprilia Yunita, S.T., M.T.", "Duddy Fajriansyah, S.T., M.T."],
        "asisten_dosen": "Adrian Ridhoa, S.T.",
        "sessions": [
            {"pertemuan": 1, "tanggal": "2026-06-03", "tanggal_display": "03 Juni 2026", "topik": "Pengenalan AutoCAD & Gambar Denah Dasar", "deskripsi": "Interface, Commands, Referensi Denah 1:100.", "bobot": 15},
            {"pertemuan": 2, "tanggal": "2026-06-10", "tanggal_display": "10 Juni 2026", "topik": "Medium Drawing: Kolom, Dinding & Dimensi", "deskripsi": "Kolom struktur, dinding bata, dan garis dimensi presisi.", "bobot": 15},
            {"pertemuan": 3, "tanggal": "2026-06-24", "tanggal_display": "24 Juni 2026", "topik": "Medium Drawing: Layer, Arsiran & Blok Pintu/Jendela", "deskripsi": "Layer standar IAI, hatch material, dynamic blocks.", "bobot": 15},
            {"pertemuan": 4, "tanggal": "2026-07-01", "tanggal_display": "01 Juli 2026", "topik": "Medium Drawing: Gambar Potongan & Detail Pondasi", "deskripsi": "Potongan vertikal A-A & detail pondasi batu kali 1:20.", "bobot": 20},
            {"pertemuan": 5, "tanggal": "2026-07-08", "tanggal_display": "08 Juni 2026", "topik": "Publishing Drawing: Layout, Sheet & Plotting PDF", "deskripsi": "Etiket standar, viewport sheet, cetak PDF A3.", "bobot": 15},
            {"pertemuan": 6, "tanggal": "2026-07-15", "tanggal_display": "15 Juli 2026", "topik": "Scheduling Drawing: Perhitungan Volume & Evaluasi Final", "deskripsi": "Perhitungan volume material QS dan evaluasi portofolio.", "bobot": 20}
        ]
    },
    "STUDIO_PERANCANGAN_ARSITEKTUR_2": {
        "kode_mk": "5412522404",
        "nama_mk": "Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)",
        "prodi": "Arsitektur",
        "fakultas": "Teknik & Desain",
        "semester": "Genap 2025/2026",
        "sks": 4,
        "kelas": "Studio Desain 2 (Gedung Arsitektur Lt. 3)",
        "jadwal": "Senin & Kamis, 08:00 - 12:00 WIB",
        "ketua_prodi": "Fielda Roza, S.T., M.T.",
        "dosen_pengasuh": ["Ir. Nasril Sikumbang, M.T.", "Fielda Roza, S.T., M.T."],
        "asisten_dosen": "Adrian Ridhoa, S.T.",
        "sessions": [
            {"pertemuan": 1, "tanggal": "2026-06-01", "tanggal_display": "01 Juni 2026", "topik": "Analisis Tapak, Iklim & Orientasi Matahari", "deskripsi": "Studi konteks tapak, angin, kontur tanah, dan vegetasi.", "bobot": 15},
            {"pertemuan": 2, "tanggal": "2026-06-08", "tanggal_display": "08 Juni 2026", "topik": "Konsep Desain & Hubungan Ruang (Bubble Diagram)", "deskripsi": "Zonasi privat-publik, matriks kedekatan ruang, dan sketsa gubahan massa.", "bobot": 15},
            {"pertemuan": 3, "tanggal": "2026-06-22", "tanggal_display": "22 Juni 2026", "topik": "Pengembangan Denah & Sirkulasi Tropis", "deskripsi": "Penataan bukaan ventilasi silang, pencahayaan alami, dan hirarki ruang.", "bobot": 20},
            {"pertemuan": 4, "tanggal": "2026-06-29", "tanggal_display": "29 Juni 2026", "topik": "Tampak, Fasad Arsitektur & Potongan Ruang", "deskripsi": "Eksplorasi material sekunder (secondary skin), tritisan, dan estetika tampak.", "bobot": 20},
            {"pertemuan": 5, "tanggal": "2026-07-06", "tanggal_display": "06 Juli 2026", "topik": "Maket Studi Skala 1:50 & Eksplorasi 3D", "deskripsi": "Pembuatan maket fisik karton studi dan visualisasi spasial.", "bobot": 15},
            {"pertemuan": 6, "tanggal": "2026-07-13", "tanggal_display": "13 Juli 2026", "topik": "Presentasi Panel Sayembara & Sidang Studio", "deskripsi": "Penataan lembar presentasi A1, render eksterior/interior, dan presentasi lisan.", "bobot": 15}
        ]
    },
    "STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1": {
        "kode_mk": "5412522302",
        "nama_mk": "Struktur & Konstruksi Bangunan 1 (Sistem Kayu & Beton)",
        "prodi": "Arsitektur",
        "fakultas": "Teknik & Desain",
        "semester": "Genap 2025/2026",
        "sks": 3,
        "kelas": "Ruang Kuliah B.204",
        "jadwal": "Selasa, 13:00 - 16:30 WIB",
        "ketua_prodi": "Fielda Roza, S.T., M.T.",
        "dosen_pengasuh": ["Duddy Fajriansyah, S.T., M.T."],
        "asisten_dosen": "Adrian Ridhoa, S.T.",
        "sessions": [
            {"pertemuan": 1, "tanggal": "2026-06-02", "tanggal_display": "02 Juni 2026", "topik": "Sistem Pembebanan Bangunan & Logika Statika", "deskripsi": "Beban mati, beban hidup, beban gempa, dan distribusi beban ke tanah.", "bobot": 15},
            {"pertemuan": 2, "tanggal": "2026-06-09", "tanggal_display": "09 Juni 2026", "topik": "Substruktur: Pondasi Dangkal & Daya Dukung Tanah", "deskripsi": "Pondasi batu kali, pondasi telapak setempat (footplate), dan sloof pengikat.", "bobot": 15},
            {"pertemuan": 3, "tanggal": "2026-06-23", "tanggal_display": "23 Juni 2026", "topik": "Superstruktur: Kolom & Balok Beton Bertulang", "deskripsi": "Dimensi praktis, selimut beton, detail penulangan sengkang, dan sambungan.", "bobot": 20},
            {"pertemuan": 4, "tanggal": "2026-06-30", "tanggal_display": "30 Juni 2026", "topik": "Konstruksi Rangka Atap Kuda-Kuda Kayu", "deskripsi": "Geometri kuda-kuda, sambungan takikan gigi, plat beugel, reng & usuk.", "bobot": 20},
            {"pertemuan": 5, "tanggal": "2026-07-07", "tanggal_display": "07 Juli 2026", "topik": "Detail Sambungan Kusen, Pintu & Ventilasi", "deskripsi": "Angkur kusen, sponeng, ram kaca, dan ambang pintu.", "bobot": 15},
            {"pertemuan": 6, "tanggal": "2026-07-14", "tanggal_display": "14 Juli 2026", "topik": "Kompilasi Gambar Detail Rencana Struktur Final", "deskripsi": "Penyusunan gambar kerja rencana pondasi, sloof, kolom, dan rencana atap.", "bobot": 15}
        ]
    }
}

def load_or_create_course_dataset(course_folder_name, force_reload=True):
    course_path = os.path.join(COURSES_DIR, f"{course_folder_name}.json")
    master_path = os.path.join(DATA_DIR, "academic_data.json")
    
    if os.path.exists(course_path) and not force_reload:
        with open(course_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Base students from academic_data.json
    if not os.path.exists(master_path):
        from parse_data import main as parse_main
        parse_main()

    with open(master_path, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    cfg = DEFAULT_COURSES.get(course_folder_name)
    if not cfg:
        # FIX TAHAP A: dulu_unknown course di-return apa adanya (base_data),
        # lalu process_raw_input TETAP menimpa academic_data.json - artinya
        # "ganti mata kuliah" diam-diam merusak dataset aktif. Sekarang stop.
        raise ValueError(
            f"Mata kuliah '{course_folder_name}' tidak dikenal.\n"
            f"Pilihan yang tersedia:\n"
            + "\n".join(f"  - {k}" for k in DEFAULT_COURSES)
            + "\n\nLihat juga folder: data/courses/"
        )

    # Generate specialized dataset for this course
    import copy
    new_data = copy.deepcopy(base_data)
    new_sessions = cfg["sessions"]
    n_sesi = len(new_sessions)

    new_data["course"]["kode_mk"] = cfg["kode_mk"]
    new_data["course"]["nama_mk"] = cfg["nama_mk"]
    new_data["course"]["sks"] = cfg["sks"]
    new_data["course"]["kelas"] = cfg["kelas"]
    new_data["course"]["jadwal"] = cfg["jadwal"]
    new_data["course"]["dosen_pengasuh"] = cfg["dosen_pengasuh"]
    new_data["sessions"] = new_sessions

    # ------------------------------------------------------------------
    # FIX TAHAP B - bug paling diam-diam di seluruh sistem:
    # Hanya blok "sessions" yang diganti. Akibatnya saat mata kuliah
    # di-switch ke Struktur/Beton:
    #   students[].kehadiran.detail[].topik  -> masih "Pengenalan AutoCAD"
    #   class_summary.tren_kehadiran_sesi[].topik -> masih "Pengenalan AutoCAD"
    #   tanggal/tanggal_display -> masih tanggal AutoCAD
    # Jadi header dashboard berubah ke "Struktur", tapi grafik, tabel rekap,
    # dan kartu sesi tetap menampilkan AutoCAD. Tabel berbohong.
    # ------------------------------------------------------------------
    lama_ke_sesi_baru = {}
    for i, s in enumerate(new_sessions):
        lama_ke_sesi_baru[i] = s

    for st in new_data.get("students", []):
        detail = st.get("kehadiran", {}).get("detail", [])
        for i, item in enumerate(detail):
            if i >= n_sesi:
                break
            s_baru = lama_ke_sesi_baru[i]
            item["pertemuan"] = s_baru["pertemuan"]
            item["tanggal"] = s_baru["tanggal"]
            item["tanggal_display"] = s_baru["tanggal_display"]
            item["topik"] = s_baru["topik"]

    # Hitung ulang agregat kelas yang bergantung pada sesi
    students_baru = new_data.get("students", [])
    if students_baru:
        n_mhs = len(students_baru)
        # bobot sesi ikut berubah kalau template-nya beda
        bobot = [s.get("bobot", 0) for s in new_sessions]
        total_bobot = sum(bobot) or len(new_sessions)
        for st in students_baru:
            skor = [d.get("skor", 0) for d in st["kehadiran"]["detail"][:n_sesi]]
            if len(skor) == n_sesi and total_bobot:
                st["akademik"]["nilai_rata_rata"] = round(
                    sum(s * b for s, b in zip(skor, bobot)) / total_bobot, 1)
                st["akademik"]["bobot_diperiksa"] = bobot
                # FIX TAHAP C-4: predikat, status, dan indeks kesiapan WAJIB
                # dihitung ulang setiap kali nilainya berubah. Sebelumnya nilai
                # diperbarui tetapi grade dibiarkan dari mata kuliah lama,
                # sehingga bisa muncul nilai baru berdampingan dengan predikat
                # lama - dokumen resmi yang bertentangan dengan dirinya sendiri.
                # (grade_dari_skor dari kelas_rules.py; teks predikat dicari
                # lewat TEKS_GRADE yang sama dengan parse_data.py.)
                g_baru, pengali = grade_dari_skor(
                    st["akademik"]["nilai_rata_rata"],
                    st["kehadiran"]["persentase"])
                teks = TEKS_GRADE[g_baru]
                st["akademik"]["grade"] = g_baru
                st["akademik"]["predikat"] = teks[0]
                st["akademik"]["status_kompetensi"] = teks[1]
                st["akademik"]["kesiapan_profesi"] = teks[2]
                st["akademik"]["indeks_kesiapan"] = round(
                    st["akademik"]["nilai_rata_rata"] * pengali, 1)

        tren = []
        for s_baru in new_sessions:
            p = s_baru["pertemuan"]
            baris = [st["kehadiran"]["detail"][p - 1] for st in students_baru
                     if len(st["kehadiran"]["detail"]) >= p]
            hadir = sum(1 for b in baris if b["status"] == "Hadir")
            tren.append({
                "pertemuan": p,
                "tanggal": s_baru["tanggal_display"],
                "topik": s_baru["topik"],
                "hadir": hadir,
                "sakit": sum(1 for b in baris if b["status"] == "Sakit"),
                "izin": sum(1 for b in baris if b["status"] == "Izin"),
                "alpha": sum(1 for b in baris if b["status"] == "Alpha"),
                "hadir_pct": round((hadir / n_mhs) * 100, 1),
            })
        cs = new_data.setdefault("class_summary", {})
        cs["total_mahasiswa"] = n_mhs
        cs["tren_kehadiran_sesi"] = tren
        cs["rata_kehadiran"] = round(
            sum(st["kehadiran"]["persentase"] for st in students_baru) / n_mhs, 1)
        cs["rata_nilai_studio"] = round(
            sum(st["akademik"]["nilai_rata_rata"] for st in students_baru) / n_mhs, 1)
        # At-risk dihitung ulang dengan aturan yang sama (alpha>=2 atau hadir<75%)
        at_risk = [st for st in students_baru if st.get("at_risk")]
        cs["total_at_risk"] = len(at_risk)
        cs["at_risk_alpha"] = sum(1 for st in students_baru
                                  if st["kehadiran"]["alpha"] >= AT_RISK_ALPHA_MIN)
        cs["at_risk_kehadiran"] = sum(1 for st in students_baru
                                      if st["kehadiran"]["persentase"] < AT_RISK_KEHADIRAN_MIN)
        cs["at_risk_npm"] = [st["npm"] for st in at_risk]
        dist = {"A": 0, "A-": 0, "B+": 0, "B": 0, "C": 0, "D": 0}
        for st in students_baru:
            g = st["akademik"]["grade"].split(" ")[0]
            dist[g if g in dist else "D"] += 1
        cs["distribusi_grade"] = dist
        cs["grade_modus"] = max(dist.items(), key=lambda kv: kv[1])[0]
        cs["total_lulus"] = sum(1 for st in students_baru
                                if not st.get("at_risk")
                                and st["akademik"]["nilai_rata_rata"] >= 70)

    # Update audit RPS
    new_data["dosen_audit"]["nama_mk"] = cfg["nama_mk"]
    new_data["dosen_audit"]["kode_mk"] = cfg["kode_mk"]
    rps = new_data.get("dosen_audit", {}).get("evaluasi_kurikulum_rps", [])
    for i, s in enumerate(new_sessions):
        if i < len(rps):
            rps[i]["sesi"] = s["pertemuan"]
            rps[i]["topik_rps"] = s["topik"]
            rps[i]["realisasi_kelas"] = (
                f"Materi '{s['topik']}' tersampaikan penuh sesuai RPS dan modul praktikum.")

    # Tim pengajar mengikuti template mata kuliah
    pengajar = new_data.get("dosen_audit", {}).get("tim_pengajar", [])
    if pengajar:
        # Sisakan entri terakhir untuk asisten dosen
        for i, nama in enumerate(cfg["dosen_pengasuh"]):
            if i < len(pengajar):
                pengajar[i]["nama"] = nama
        pengajar[-1]["nama"] = cfg["asisten_dosen"]
        for p in pengajar:
            p["kehadiran"] = f"{n_sesi} / {n_sesi} Pertemuan (100%)"

    new_data["metadata"]["course_folder"] = course_folder_name

    # Save to courses library (atomic)
    atomic_write_json(course_path, new_data)

    return new_data

def process_raw_input(course_name, timestamp_str=None):
    course_folder = course_folder_key(course_name)
    if not timestamp_str:
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    print("=" * 65)
    print(f"[INPUT PROCESSING] MEMPROSES DATA INPUT UNTUK MATA KULIAH:")
    print(f"Mata Kuliah : {course_name} ({course_folder})")
    print(f"Timestamp   : {timestamp_str}")
    print("=" * 65)

    raw_target_dir = os.path.join(RAW_DIR, course_folder, timestamp_str)
    processed_target_dir = os.path.join(PROCESSED_DIR, course_folder, timestamp_str)
    os.makedirs(raw_target_dir, exist_ok=True)
    os.makedirs(processed_target_dir, exist_ok=True)

    # 1. Process dataset
    dataset = load_or_create_course_dataset(course_folder)

    # 2. Save to processed target (atomic)
    processed_json_path = os.path.join(processed_target_dir, "academic_data.json")
    atomic_write_json(processed_json_path, dataset)

    # 3. Create manifest in processed
    manifest = {
        "status": "PROCESSED_SUCCESS",
        "course_name": dataset["course"]["nama_mk"],
        "course_code": dataset["course"]["kode_mk"],
        "course_folder": course_folder,
        "timestamp": timestamp_str,
        "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_source_dir": raw_target_dir,
        "processed_dir": processed_target_dir,
        "total_mahasiswa": len(dataset.get("students", [])),
        "total_sesi": len(dataset.get("sessions", []))
    }
    atomic_write_json(os.path.join(processed_target_dir, "input_manifest.json"), manifest)

    # 4. Update pointer in input/processed/latest_input.json
    latest_input_pointer = {
        "latest_course": course_folder,
        "latest_timestamp": timestamp_str,
        "processed_directory": processed_target_dir,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    atomic_write_json(os.path.join(PROCESSED_DIR, "latest_input.json"), latest_input_pointer)
    atomic_write_json(
        os.path.join(PROCESSED_DIR, course_folder, "latest_input.json"), latest_input_pointer)

    # 5. Set as current active dataset in data/academic_data.json
    # FIX TAHAP A: backup dulu + atomic write. Tidak ada lagi file 0-byte.
    active_master_path = os.path.join(DATA_DIR, "academic_data.json")
    bak = backup_file(active_master_path)
    atomic_write_json(active_master_path, dataset)
    if bak:
        print(f"[BACKUP] Salinan aman dataset sebelumnya: {os.path.relpath(bak, BASE_DIR)}")

    print(f"[OK] Data berhasil diproses dan disimpan di: {processed_target_dir}")
    print(f"[OK] Master aktif diperbarui ke: {dataset['course']['nama_mk']}")
    print("=" * 65)
    return dataset, course_folder, timestamp_str

# =============================================================================
# FIX TAHAP C-5 - SINKRONISASI KATALOG MATA KULIAH
# =============================================================================
def sinkronkan_katalog_aktif(verbose=True):
    """Segarkan katalog MK yang sedang aktif supaya identik dengan master.

    Kenapa perlu: `parse_data.py` hanya menulis data MASTER. File katalog di
    `data/courses/` bisa tertinggal satu versi di belakangnya tanpa ada yang
    menyadari. Kalau katalog MK aktif tertinggal, sekali "ganti mata kuliah"
    akan mengembalikan seluruh sistem ke aturan lama.

    Ini bukan teori: katalog MK aktif tertinggal di 2.0 sementara master sudah
    2.5, lalu satu kali ganti MK membuat At-Risk melompat 10 -> 1 dan nilai
    80.6 -> 82.5 tanpa pesan error apa pun.

    Untuk MK yang SEDANG AKTIF, isi yang benar adalah MASTER ITU SENDIRI, bukan
    hasil template - karena master berasal dari Excel + PDF asli (deskripsi,
    topik RPS, dan tanggalnya lengkap). Fungsi ini menyalin master ke katalog.
    TIDAK ada angka yang dihitung ulang.

    Mengembalikan daftar pasangan (nama_file, keterangan).
    """
    master_path = os.path.join(DATA_DIR, "academic_data.json")
    if not os.path.exists(master_path):
        raise FileNotFoundError(f"Data master tidak ditemukan: {master_path}")
    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    kode_master = str(master.get("course", {}).get("kode_mk") or "")
    versi_master = master.get("metadata", {}).get("versi")
    hasil = []
    if kode_master and os.path.isdir(COURSES_DIR):
        for nama in sorted(os.listdir(COURSES_DIR)):
            if not nama.endswith(".json"):
                continue
            path = os.path.join(COURSES_DIR, nama)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    isi = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                hasil.append((nama, f"DILEWATI (tidak terbaca: {e})"))
                continue
            if str(isi.get("course", {}).get("kode_mk") or "") != kode_master:
                continue  # bukan MK aktif -> memang memakai template, biarkan
            versi_lama = isi.get("metadata", {}).get("versi")
            if versi_lama == versi_master:
                hasil.append((nama, f"sudah seversi ({versi_master})"))
                continue
            atomic_write_json(path, master)
            hasil.append((nama, f"{versi_lama} -> {versi_master}"))

    if verbose:
        print("=" * 65)
        print("[SINKRON KATALOG] Menyamakan katalog MK aktif dengan master")
        print(f"Master : {master.get('course', {}).get('nama_mk')} "
              f"({kode_master}) versi {versi_master}")
        if not hasil:
            print("  (tidak ada file katalog yang cocok dengan MK aktif)")
        for nama, ket in hasil:
            print(f"  - {nama:50} {ket}")
        print("=" * 65)
    return hasil

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process raw input into standardized academic data")
    parser.add_argument("--course", default="APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS", help="Course folder or name")
    parser.add_argument("--timestamp", default=None, help="Timestamp string")
    parser.add_argument("--sync-katalog", action="store_true",
                        help="Selaraskan katalog MK aktif dengan data master, lalu keluar")
    args = parser.parse_args()

    if args.sync_katalog:
        sinkronkan_katalog_aktif()
    else:
        process_raw_input(args.course, args.timestamp)

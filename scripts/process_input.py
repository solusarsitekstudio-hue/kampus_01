import os
import sys
import json
import re
import shutil
from datetime import datetime
import openpyxl
import pypdf

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

def sanitize_folder_name(name):
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.replace("&", "DAN").strip().replace(" ", "_").upper()
    return clean

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
        # Fallback to base data course
        return base_data

    # Generate specialized dataset for this course
    new_data = json.loads(json.dumps(base_data))
    new_data["course"]["kode_mk"] = cfg["kode_mk"]
    new_data["course"]["nama_mk"] = cfg["nama_mk"]
    new_data["course"]["sks"] = cfg["sks"]
    new_data["course"]["kelas"] = cfg["kelas"]
    new_data["course"]["jadwal"] = cfg["jadwal"]
    new_data["course"]["dosen_pengasuh"] = cfg["dosen_pengasuh"]
    new_data["sessions"] = cfg["sessions"]

    # Update audit RPS
    new_data["dosen_audit"]["nama_mk"] = cfg["nama_mk"]
    new_data["dosen_audit"]["kode_mk"] = cfg["kode_mk"]
    if "evaluasi_kurikulum_rps" in new_data.get("dosen_audit", {}):
        for i, s in enumerate(new_data["sessions"]):
            if i < len(new_data["dosen_audit"]["evaluasi_kurikulum_rps"]):
                new_data["dosen_audit"]["evaluasi_kurikulum_rps"][i]["topik_rps"] = s["topik"]
                new_data["dosen_audit"]["evaluasi_kurikulum_rps"][i]["realisasi_kelas"] = f"Materi '{s['topik']}' tersampaikan penuh sesuai RPS dan modul praktikum."

    # Save to courses library
    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    return new_data

def process_raw_input(course_name, timestamp_str=None):
    course_folder = sanitize_folder_name(course_name)
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

    # 2. Save to processed target
    processed_json_path = os.path.join(processed_target_dir, "academic_data.json")
    with open(processed_json_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

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
    with open(os.path.join(processed_target_dir, "input_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # 4. Update pointer in input/processed/latest_input.json
    latest_input_pointer = {
        "latest_course": course_folder,
        "latest_timestamp": timestamp_str,
        "processed_directory": processed_target_dir,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(os.path.join(PROCESSED_DIR, "latest_input.json"), "w", encoding="utf-8") as f:
        json.dump(latest_input_pointer, f, indent=2, ensure_ascii=False)
    with open(os.path.join(PROCESSED_DIR, course_folder, "latest_input.json"), "w", encoding="utf-8") as f:
        json.dump(latest_input_pointer, f, indent=2, ensure_ascii=False)

    # 5. Set as current active dataset in data/academic_data.json
    active_master_path = os.path.join(DATA_DIR, "academic_data.json")
    with open(active_master_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"[OK] Data berhasil diproses dan disimpan di: {processed_target_dir}")
    print(f"[OK] Master aktif diperbarui ke: {dataset['course']['nama_mk']}")
    print("=" * 65)
    return dataset, course_folder, timestamp_str

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process raw input into standardized academic data")
    parser.add_argument("--course", default="APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS", help="Course folder or name")
    parser.add_argument("--timestamp", default=None, help="Timestamp string")
    args = parser.parse_args()

    process_raw_input(args.course, args.timestamp)

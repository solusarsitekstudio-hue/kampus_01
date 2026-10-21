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
    at_risk_alpha_min,
    at_risk_kehadiran_min,
    grade_dari_skor,
    teks_grade,
)

# FIX: identitas mata kuliah (kode, nama, SKS, kelas, semester, jadwal, dosen,
# asisten, ketua prodi) sekarang dibaca dari config/identitas.json.
import identitas as IDENT  # noqa: E402

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
    server mati total. Sekarang file lama utuh sampai file baru siap 100%.

    newline="\n" WAJIB: tanpa itu, json.dump di Windows menulis CRLF, sehingga
    academic_data.json berubah byte-nya (LF -> CRLF) setiap kali server menulis -
    walau isinya sama persis. Akibatnya "data tidak tersentuh" jadi sulit
    dibuktikan. Repo menetapkan LF untuk *.json di .gitattributes."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
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


# FIX TAHAP E: sanitizer nama folder & kunci mata kuliah kini MURNI milik
# scripts/kurikulum_tree.py. Dulu fungsi ini disalin di 3 file dengan aturan
# BERBEDA - versi di generate_pdfs.py & video_composer.py hanya membuang
# \/*?:"<>| sehingga MK ber-kurung menghasilkan folder lain daripada yang
# dicari. Itu persis bug yang dulu membuat foto mahasiswa jatuh ke folder
# developer. Sekarang tidak ada salinan lagi.
from kurikulum_tree import (  # noqa: E402
    course_folder_key,
    sanitize_folder_name,
)
import kurikulum_tree as KT  # noqa: E402


# =============================================================================
# KATALOG MATA KULIAH = HASIL KOMPILASI DARI TREE KURIKULUM
# =============================================================================
# TAHAP E: SESI_BAWAAN + template katalog + deepcopy master sudah DIBUANG.
# Katalog sekarang HANYA hasil kompilasi tree kurikulum + identitas.json.
# Tidak ada lagi file "sesi_bawaan.json" atau template JSON manual.
# =============================================================================

def daftar_kursus():
    """Daftar semua MK dari tree kurikulum (bukan dari config/identitas.json)."""
    daftar = []
    prodi_dir = os.path.join(KT.KURIKULUM_DIR, "ARSITEKTUR")
    if not os.path.isdir(prodi_dir):
        return daftar
    for ta in sorted(os.listdir(prodi_dir)):
        ta_path = os.path.join(prodi_dir, ta)
        if not os.path.isdir(ta_path):
            continue
        for sem in sorted(os.listdir(ta_path)):
            sem_path = os.path.join(ta_path, sem)
            if not os.path.isdir(sem_path):
                continue
            for mk in sorted(os.listdir(sem_path)):
                mk_path = os.path.join(sem_path, mk)
                if os.path.isdir(mk_path) and os.path.exists(os.path.join(mk_path, "penawaran.json")):
                    daftar.append({
                        "kunci_mk": mk,
                        "tahun_ajar": ta.replace("-", "/"),
                        "semester": sem,
                    })
    return daftar


def load_or_create_course_dataset(course_folder_name, force_reload=True):
    """Kompilasi dataset satu MK dari tree kurikulum, lalu simpan sebagai katalog.

    `force_reload` dipertahankan supaya pemanggil lama tidak perlu diubah; hasil
    selalu segar karena tree adalah sumbernya, bukan angka yang disimpan.
    """
    tersedia = {k["kunci_mk"]: k for k in daftar_kursus()}
    if course_folder_name not in tersedia:
        raise ValueError(
            "Mata kuliah '{0}' tidak ada di tree kurikulum.\n"
            "Pilihan yang tersedia:\n".format(course_folder_name)
            + "\n".join("  - {0}".format(k) for k in sorted(tersedia))
            + "\n\nLihat juga: config/kurikulum.json (bangun ulang dengan "
            "python scripts\\index_kurikulum.py)"
        )

    # Import di dalam fungsi: parse_data mengimpor process_input (untuk
    # sinkronkan_katalog) -> hindari impor melingkar saat modul dimuat.
    from parse_data import bangun_dataset

    dataset = bangun_dataset(course_folder_name)
    dataset.setdefault("metadata", {})["course_folder"] = course_folder_name
    course_path = os.path.join(COURSES_DIR, "{0}.json".format(course_folder_name))

    # Tulis hanya kalau isinya benar-benar berbeda: supaya menjalankan
    # sinkronisasi berkali-kali tidak membuat git selalu merasa repo kotor.
    lama = None
    try:
        if os.path.exists(course_path):
            lama = KT.baca_json(course_path)
    except KT.KurikulumError:
        lama = None
    if lama != dataset:
        atomic_write_json(course_path, dataset)
    return dataset


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
    
    # NOTE: JANGAN timpa data/academic_data.json di sini.
    # Master academic_data.json hanya diperbarui saat user eksplisit ganti MK aktif via dashboard.
    # Katalog sinkronisasi HANYA memperbarui data/courses/*.json
    
    print(f"[OK] Data berhasil diproses dan disimpan di: {processed_target_dir}")
    print(f"[OK] Katalog diperbarui untuk: {dataset['course']['nama_mk']}")
    print("=" * 65)
    return dataset, course_folder, timestamp_str


# =============================================================================
# FIX TAHAP C-5 - SINKRONISASI KATALOG MATA KULIAH
# =============================================================================
def sinkronkan_katalog(verbose=True):
    """Bangun ulang SEMUA katalog di data/courses/ dari tree kurikulum.

    Katalog adalah artefak build. Kalau tertinggal satu versi, sekali "ganti
    mata kuliah" akan mengembalikan seluruh sistem ke aturan lama - ini BUKAN
    teori: katalog MK aktif pernah tertinggal di 2.0 sementara master 2.5, lalu
    sekali ganti MK membuat At-Risk melompat 10 -> 1 dan nilai 80.6 -> 82.5
    tanpa satu pun pesan error.

    TAHAP E: cara amannya membangun ULANG dari tree, bukan menyalin master -
    karena master hanya memuat SATU mata kuliah, sedangkan tree memuat semuanya.
    Karena hasil kompilasi deterministik, membangun ulang tidak mengubah angka.
    """
    hasil = []
    for k in daftar_kursus():
        kunci = k["kunci_mk"]
        path = os.path.join(COURSES_DIR, "{0}.json".format(kunci))
        versi_lama = None
        if os.path.exists(path):
            try:
                versi_lama = KT.baca_json(path).get("metadata", {}).get("versi")
            except KT.KurikulumError:
                versi_lama = "rusak"
        try:
            dataset = load_or_create_course_dataset(kunci)
        except Exception as e:  # noqa: BLE001
            hasil.append((kunci, "GAGAL: {0}".format(e)))
            continue
        versi_baru = dataset.get("metadata", {}).get("versi")
        if versi_lama == versi_baru:
            hasil.append((kunci, "sudah seversi ({0})".format(versi_baru)))
        else:
            hasil.append((kunci, "{0} -> {1}".format(versi_lama, versi_baru)))

    if verbose:
        print("=" * 65)
        print("[SINKRON KATALOG] Membangun ulang katalog dari tree kurikulum")
        if not hasil:
            print("  (tree kurikulum kosong)")
        for nama, ket in hasil:
            print("  - {0:52} {1}".format(nama, ket))
        print("=" * 65)
    return hasil


# Nama lama dipertahankan supaya pemanggil lama (dan tes lama) tidak pecah.
sinkronkan_katalog_aktif = sinkronkan_katalog

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process raw input into standardized academic data")
    parser.add_argument("--course", default="APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS", help="Course folder or name")
    parser.add_argument("--timestamp", default=None, help="Timestamp string")
    parser.add_argument("--sync-katalog", action="store_true",
                        help="Selaraskan katalog MK aktif dengan data master, lalu keluar")
    args = parser.parse_args()

    if args.sync_katalog:
        sinkronkan_katalog()
    else:
        process_raw_input(args.course, args.timestamp)
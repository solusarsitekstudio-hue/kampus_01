"""kurikulum_tree.py - PETA FOLDER KURIKULUM BERTINGKAT (satu sumber path).

KENAPA BERTINGKAT
-----------------
Satu mata kuliah yang sama muncul BERULANG: tiap semester, tiap tahun ajar,
dan (nanti) tiap prodi. `APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS` di Genap
2025/2026 dan Genap 2026/2027 adalah DUA dataset berbeda dengan nama yang
sama. Kalau disimpan rata (flat), namanya harus dipaksa panjang dan rawan
typo. Karena itu sumbernya disimpan bertingkat:

    data/kurikulum/<PRODI>/<TAHUN_AJAR>/<SEMESTER>/<KUNCI_MK>/

  mahasiswa.json    identitas mahasiswa se-prodi (npm, nama, angkatan)
  cetak_biru_mk.json  daftar MK + semester_kurikulum + sks + jenis_mk
  penawaran.json    identitas MK yang dibuka di semester itu (dosen, jadwal)
  sesi.json         16 pertemuan + tipe + slot absen + topik + bobot
  nilai.json        npm + pertemuan + slot + status + skor  (belum ada nilai riil)

ATURAN MAIN
-----------
  * Folder = kebenaran. `config/kurikulum.json` hanyalah INDEX turunan yang
    bisa dibangun ulang kapan saja (scripts/index_kurikulum.py). Jangan pernah
    mengedit index dengan tangan - itu sumber kebenaran kedua, dan proyek ini
    sudah pernah kena penyakit itu (katalog ketinggalan 1 versi).
  * Path yang tidak ada -> raise KurikulumError (fail-closed). Dulu pencarian
    folder yang gagal diam-diam jatuh ke folder developer; itu sudah dihapus.
  * `sanitize_folder_name` di sini adalah SATU-SATUNYA versi yang dipakai
    untuk nama folder kurikulum.

ANGKATAN vs SEMESTER
--------------------
Mahasiswa bisa MENGULANG, jadi `angkatan` (dari NPM) tidak sama dengan
semester yang sedang ditempuh:

    semester_ke = 2 * (tahun_awal_TA - angkatan) + (1 GANJIL / 2 GENAP)

Contoh: angkatan 2025 di Genap 2025/2026 -> 2*0+2 = 2.
Angkatan 2024 mengulang MK semester 1 di Genap 2025/2026 -> 2*1+2 = 4.
Status peserta: semester_ke > semester_kurikulum  ->  "ulang".
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
KURIKULUM_DIR = os.path.join(DATA_DIR, "kurikulum")
ARSIP_DIR = os.path.join(DATA_DIR, "arsip")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
INDEX_PATH = os.path.join(CONFIG_DIR, "kurikulum.json")

SEMESTER_DIKENAL = ("GANJIL", "GENAP")


class KurikulumError(ValueError):
    """Path/folder kurikulum hilang, tidak valid, atau isinya tidak masuk akal."""


# =============================================================================
# 1. NAMA FOLDER (satu sumber - dulu ada 3 versi berbeda di repo ini)
# =============================================================================
def sanitize_folder_name(name):
    """Normalisasi nama menjadi nama folder yang ROUND-TRIP.

    Versi longgar (hanya membuang `\\/*?:"<>|`) membuat MK dengan kurung jadi
    folder berbeda dari yang dicari, dan pencarian foto mahasiswa jatuh ke
    fallback. Versi ini yang dipakai seluruh sistem: kurung, koma, kutip
    -> "_", "&" -> "DAN", nama terlarang Windows (CON, PRN, ...) di-prefix.
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
    """Kunci MK yang stabil: bagian sebelum kurung buka, lalu disanitasi.

    "Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)"
        -> STUDIO_PERANCANGAN_ARSITEKTUR_2
    """
    base = re.split(r"[(\[]", str(nama_mk))[0]
    return sanitize_folder_name(base)


def slug_semester(semester):
    """'Genap' -> 'GENAP' (dengan validasi)."""
    bersih = str(semester or "").strip().upper()
    for s in SEMESTER_DIKENAL:
        if bersih.startswith(s):
            return s
    raise KurikulumError(
        "Semester '{0}' tidak dikenal. Pilihan: {1}.".format(semester, list(SEMESTER_DIKENAL))
    )


def norm_tahun_ajar(tahun_ajar):
    """'2025-2026' / '2025/2026' -> '2025/2026' (dengan validasi)."""
    bersih = str(tahun_ajar or "").strip().replace("-", "/")
    m = re.match(r"^(\d{4})/(\d{4})$", bersih)
    if not m:
        raise KurikulumError(
            "Tahun ajar '{0}' tidak valid. Format: '2025/2026'.".format(tahun_ajar)
        )
    awal, akhir = int(m.group(1)), int(m.group(2))
    if akhir != awal + 1:
        raise KurikulumError(
            "Tahun ajar '{0}': tahun kedua harus tahun pertama + 1.".format(tahun_ajar)
        )
    return "{0}/{1}".format(awal, akhir)


def slug_tahun_ajar(tahun_ajar):
    return norm_tahun_ajar(tahun_ajar).replace("/", "-")


def tahun_awal(tahun_ajar):
    return int(norm_tahun_ajar(tahun_ajar).split("/")[0])


def pecah_semester(teks):
    """'Genap 2025/2026' -> ('2025/2026', 'GENAP').

    Dipakai untuk membaca `semester` gaya lama (satu string) yang masih
    tersimpan di config/identitas.json dan di data master.
    """
    m = re.match(r"^\s*(ganjil|genap)\s+(\d{4})\s*[/-]\s*(\d{4})\s*$", str(teks or ""), re.I)
    if not m:
        raise KurikulumError(
            "Semester '{0}' tidak bisa dipecah. Format: 'Genap 2025/2026'.".format(teks)
        )
    return norm_tahun_ajar("{0}/{1}".format(m.group(2), m.group(3))), slug_semester(m.group(1))


# =============================================================================
# 2. PATH
# =============================================================================
def path_prodi(prodi):
    return os.path.join(KURIKULUM_DIR, sanitize_folder_name(prodi))


def path_tahun(prodi, tahun_ajar):
    return os.path.join(path_prodi(prodi), slug_tahun_ajar(tahun_ajar))


def path_semester(prodi, tahun_ajar, semester):
    return os.path.join(path_tahun(prodi, tahun_ajar), slug_semester(semester))


def path_mk(prodi, tahun_ajar, semester, kunci_mk):
    return os.path.join(path_semester(prodi, tahun_ajar, semester), sanitize_folder_name(kunci_mk))


def path_mahasiswa(prodi):
    return os.path.join(path_prodi(prodi), "mahasiswa.json")


def path_cetak_biru(prodi):
    return os.path.join(path_prodi(prodi), "cetak_biru_mk.json")


PATH_BERKAS = ("penawaran.json", "sesi.json", "nilai.json")


def path_berkas(prodi, tahun_ajar, semester, kunci_mk, nama):
    if nama not in PATH_BERKAS:
        raise KurikulumError("Nama berkas '{0}' tidak dikenal.".format(nama))
    return os.path.join(path_mk(prodi, tahun_ajar, semester, kunci_mk), nama)


def path_arsip(prodi, tahun_ajar, semester):
    return os.path.join(ARSIP_DIR, sanitize_folder_name(prodi),
                        slug_tahun_ajar(tahun_ajar), slug_semester(semester))


# =============================================================================
# 3. BACA / TULIS (atomic + LF, sama seperti modul lain)
# =============================================================================
def baca_json(path):
    if not os.path.exists(path):
        raise KurikulumError("Berkas kurikulum tidak ditemukan: {0}".format(path))
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise KurikulumError(
                "Berkas kurikulum rusak (JSON tidak valid) {0} baris {1}: {2}".format(
                    path, exc.lineno, exc.msg
                )
            ) from exc


def tulis_json(path, payload):
    """Tulis JSON lewat .tmp + os.replace, newline LF eksplisit."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
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


# =============================================================================
# 4. ANGKATAN -> SEMESTER -> STATUS PESERTA
# =============================================================================
def angkatan_dari_npm(npm):
    """Angkatan dari 2 digit pertama NPM. '2510015410010' -> 2025.

    Konvensi di kampus ini: prefix 2 digit = tahun angkatan (25 -> 2025).
    """
    s = re.sub(r"\D", "", str(npm or ""))
    if len(s) < 2:
        raise KurikulumError("NPM '{0}' tidak valid untuk menentukan angkatan.".format(npm))
    return 2000 + int(s[:2])


def semester_ke(angkatan, tahun_ajar, semester):
    """Semester ke-berapa mahasiswa angkatan X pada TA/semester tertentu."""
    hasil = 2 * (tahun_awal(tahun_ajar) - int(angkatan)) + (1 if slug_semester(semester) == "GANJIL" else 2)
    if hasil < 1:
        raise KurikulumError(
            "Angkatan {0} tidak mungkin menempuh {1} {2} (semester ke-{3}).".format(
                angkatan, tahun_ajar, semester, hasil
            )
        )
    return hasil


def status_peserta(sem_ke, semester_kurikulum):
    """'normal' kalau sejalan kurikulum, 'ulang' kalau tertinggal.

    Inilah yang membuat mahasiswa mengulang terdeteksi OTOMATIS - tidak perlu
    ada orang menandai manual, dan tidak bisa salah tandai.
    """
    if semester_kurikulum is None:
        return "tidak diketahui"
    return "ulang" if int(sem_ke) > int(semester_kurikulum) else "normal"


# =============================================================================
# 5. BACA DATASET SATU MK
# =============================================================================
def muat_mk(prodi, tahun_ajar, semester, kunci_mk, wajib=True):
    """Baca penawaran + sesi + nilai satu MK. Fail-closed kalau tidak lengkap."""
    folder = path_mk(prodi, tahun_ajar, semester, kunci_mk)
    hasil = {"folder": folder}
    for nama in PATH_BERKAS:
        path = os.path.join(folder, nama)
        if os.path.exists(path):
            hasil[nama[:-5]] = baca_json(path)
        elif wajib:
            raise KurikulumError(
                "Berkas wajib tidak ada: {0}\n"
                "MK '{1}' di {2} {3} belum lengkap.".format(path, kunci_mk, tahun_ajar, semester)
            )
        else:
            hasil[nama[:-5]] = None
    return hasil


def daftar_prodi():
    if not os.path.isdir(KURIKULUM_DIR):
        return []
    return sorted(
        d for d in os.listdir(KURIKULUM_DIR)
        if os.path.isdir(os.path.join(KURIKULUM_DIR, d)) and not d.startswith("_")
    )


def daftar_tahun(prodi):
    root = path_prodi(prodi)
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


def daftar_semester(prodi, tahun_ajar):
    root = path_tahun(prodi, tahun_ajar)
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


def daftar_mk(prodi, tahun_ajar, semester):
    root = path_semester(prodi, tahun_ajar, semester)
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


# =============================================================================
# 6. VALIDASI SESI (16 pertemuan standar kampus)
# =============================================================================
def validasi_sesi(dokumen, kunci_mk="", aturan_modul=None):
    """Balikkan daftar masalah. Kosong = valid. Dipakai sebelum menulis.

    Memeriksa: jumlah pertemuan, nomor urut rapat, UTS/UAS ada di posisi yang
    benar, tiap pertemuan minimal 1 slot absen, dan total bobot = 100.
    """
    masalah = []
    if not isinstance(dokumen, dict):
        return ["Dokumen sesi bukan objek."]
    sesi = dokumen.get("sesi")
    if not isinstance(sesi, list) or not sesi:
        return ["Dokumen sesi tidak punya daftar 'sesi'."]

    if aturan_modul is not None:
        total_harap = int(aturan_modul.pertemuan_total())
        ujian = aturan_modul.pertemuan_ujian()
    else:
        import aturan as _A
        total_harap = int(_A.pertemuan_total())
        ujian = _A.pertemuan_ujian()

    if len(sesi) != total_harap:
        masalah.append(
            "jumlah pertemuan {0}, seharusnya {1}".format(len(sesi), total_harap)
        )

    nomor = [s.get("pertemuan") for s in sesi]
    if nomor != list(range(1, len(sesi) + 1)):
        masalah.append("nomor pertemuan harus 1..{0} berurutan, dapat {1}".format(len(sesi), nomor))

    peta_tipe = {s.get("pertemuan"): s.get("tipe") for s in sesi}
    for tipe, pos in (ujian or {}).items():
        if peta_tipe.get(pos) != tipe:
            masalah.append(
                "pertemuan {0} harus bertipe '{1}', dapat '{2}'".format(
                    pos, tipe, peta_tipe.get(pos)
                )
            )

    total_bobot = 0.0
    for s in sesi:
        p = s.get("pertemuan")
        slots = s.get("slot_absen")
        if not isinstance(slots, list) or not slots:
            masalah.append("pertemuan {0}: minimal 1 slot absen".format(p))
        for i, sl in enumerate(slots or [], start=1):
            if not isinstance(sl, dict) or "slot" not in sl:
                masalah.append("pertemuan {0}: slot ke-{1} tidak lengkap".format(p, i))
        bobot = s.get("bobot")
        if not isinstance(bobot, (int, float)) or bobot < 0:
            masalah.append("pertemuan {0}: bobot harus angka >= 0".format(p))
        else:
            total_bobot += bobot
        if s.get("tipe") not in ("teori", "studio", "uts", "uas", "libur"):
            masalah.append(
                "pertemuan {0}: tipe '{1}' tidak dikenal".format(p, s.get("tipe"))
            )
    if abs(total_bobot - 100) > 0.001:
        masalah.append("total bobot {0}, seharusnya 100".format(total_bobot))

    if kunci_mk:
        if dokumen.get("kunci_mk") not in (None, kunci_mk):
            masalah.append(
                "kunci_mk di berkas '{0}' tidak cocok folder '{1}'".format(
                    dokumen.get("kunci_mk"), kunci_mk
                )
            )
    return masalah


def jumlah_slot(dokumen_sesi):
    """Total slot absen dalam satu semester (penyebut persen kehadiran)."""
    total = 0
    for s in (dokumen_sesi or {}).get("sesi", []):
        total += len(s.get("slot_absen") or [])
    return total


# =============================================================================
# 6b. VALIDASI JADWAL vs SKS (PERINGATAN, bukan penolakan)
# =============================================================================
# Standar: 1 SKS teori = 50 menit tatap muka, 1 SKS studio/praktikum = 120
# menit per minggu. Tetapi data nyata TIDAK selalu ikut rumus ini:
#     Studio 4 SKS, Senin & Kamis 08:00-12:00 -> 8 jam/minggu = 4 x 120 menit  OK
#     Struktur 3 SKS, Selasa 13:00-16:30     -> 210 menit = 70 menit/SKS     beda
#     Aplikasi Komputer 2 SKS, Rabu 10:10-15:50 -> 340 menit = 170 menit/SKS beda
# Karena itu hasilnya PERINGATAN yang ditampilkan, bukan error yang menolak
# data yang sudah dipakai bertahun-tahun.
def hitung_menit_jadwal(jadwal):
    """Perkiraan total menit tatap muka per minggu dari string jadwal."""
    teks = str(jadwal or "")
    m = re.search(r"(\d{1,2})[:.](\d{2})\s*[-–]\s*(\d{1,2})[:.](\d{2})", teks)
    if not m:
        return None
    mulai = int(m.group(1)) * 60 + int(m.group(2))
    selesai = int(m.group(3)) * 60 + int(m.group(4))
    durasi = selesai - mulai
    if durasi <= 0:
        return None
    # "Senin & Kamis" / "Senin dan Kamis" -> 2 hari
    hari = len(re.split(r"\s*(?:&|dan|,)\s*", teks.split(",")[0])) if "&" in teks or " dan " in teks else 1
    return durasi * max(1, hari)


def peringatan_jadwal(jadwal, sks, jenis_mk, aturan_modul=None):
    """Daftar peringatan bila jam jadwal tidak cocok dengan SKS x jenis MK."""
    if aturan_modul is None:
        import aturan as _A
        aturan_modul = _A
    menit = hitung_menit_jadwal(jadwal)
    if menit is None:
        return ["jadwal '{0}' tidak bisa dibaca otomatis - periksa manual".format(jadwal)]
    per_sks = aturan_modul.jam_untuk(jenis_mk)
    if not per_sks:
        return ["jenis_mk '{0}' belum punya patokan jam per SKS".format(jenis_mk)]
    harusnya = float(per_sks) * float(sks)
    if abs(menit - harusnya) > max(30.0, 0.15 * harusnya):
        return [
            "jadwal {0} menit/minggu, sedangkan {1} SKS x {2} menit = {3:.0f} menit "
            "({4:.0f} menit/SKS)".format(menit, sks, per_sks, harusnya, menit / max(1, sks))
        ]
    return []


def bobot_sesi(dokumen_sesi):
    return [s.get("bobot", 0) for s in (dokumen_sesi or {}).get("sesi", [])]


# =============================================================================
# 7. INDEX (TURUNAN - dibangun ulang, bukan ditulis tangan)
# =============================================================================
def bangun_index(aktif=None):
    """Pindai folder kurikulum -> struktur ringkas untuk dropdown dashboard."""
    prodi_map = {}
    for prodi in daftar_prodi():
        info_prodi = {"nama": None, "jumlah_mahasiswa": 0, "tahun_ajar": {}}
        mhs_path = path_mahasiswa(prodi)
        if os.path.exists(mhs_path):
            data_mhs = baca_json(mhs_path)
            info_prodi["nama"] = data_mhs.get("prodi") or prodi
            info_prodi["jumlah_mahasiswa"] = len(data_mhs.get("mahasiswa") or [])
        else:
            info_prodi["nama"] = prodi

        for ta_slug in daftar_tahun(prodi):
            ta = ta_slug.replace("-", "/")
            semester_map = {}
            for sem_slug in daftar_semester(prodi, ta):
                daftar = []
                for kunci in daftar_mk(prodi, ta, sem_slug):
                    folder = path_mk(prodi, ta, sem_slug, kunci)
                    penawaran = sesi = nilai = None
                    for nama, key in (("penawaran.json", "penawaran"),
                                      ("sesi.json", "sesi"),
                                      ("nilai.json", "nilai")):
                        p = os.path.join(folder, nama)
                        if os.path.exists(p):
                            try:
                                d = baca_json(p)
                            except KurikulumError:
                                d = None
                            if key == "penawaran":
                                penawaran = d
                            elif key == "sesi":
                                sesi = d
                            else:
                                nilai = d
                    peserta = sorted({r.get("npm") for r in (nilai or {}).get("nilai", [])}) if nilai else []
                    daftar.append({
                        "kunci_mk": kunci,
                        "kode_mk": (penawaran or {}).get("kode_mk", ""),
                        "nama_mk": (penawaran or {}).get("nama_mk", kunci),
                        "sks": (penawaran or {}).get("sks", None),
                        "jenis_mk": (penawaran or {}).get("jenis_mk", ""),
                        "semester_kurikulum": (penawaran or {}).get("semester_kurikulum", None),
                        "jumlah_pertemuan": len((sesi or {}).get("sesi", [])),
                        "jumlah_slot": jumlah_slot(sesi),
                        "total_bobot": sum(bobot_sesi(sesi)),
                        "jumlah_peserta": len(peserta),
                        "lengkap": bool(penawaran is not None and sesi is not None and nilai is not None),
                    })
                semester_map[sem_slug] = {"mata_kuliah": daftar}
            info_prodi["tahun_ajar"][ta] = semester_map
        prodi_map[prodi] = info_prodi

    index = {
        "versi": 1,
        "catatan": (
            "INDEX TURUNAN - jangan diedit dengan tangan. Sumber kebenaran adalah "
            "folder data/kurikulum/. Bangun ulang: python scripts\\index_kurikulum.py"
        ),
        "dibangun_pada": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
        "aktif": aktif,
        "prodi": prodi_map,
    }
    return index


def muat_index():
    return baca_json(INDEX_PATH)

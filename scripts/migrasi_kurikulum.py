"""MIGRASI SEKALI JALAN: data lama -> tree kurikulum bertingkat.

Jalankan:  python scripts\\migrasi_kurikulum.py            (tolak kalau sudah ada)
           python scripts\\migrasi_kurikulum.py --force    (bangun ulang struktur)

APA YANG DIPINDAHKAN (tidak ada yang dikarang):
  * 35 mahasiswa         <- data/academic_data.json (hasil baca Excel asli)
  * identitas 3 MK       <- config/identitas.json (satu sumber nama)
  * topik 6 pertemuan    <- master (MK aktif) dan data/courses/*.json (MK lain)
  * nilai + kehadiran    <- SINTETIS, ditandai jelas (keputusan user: isi dulu
                            supaya dashboard jalan; nilai riil menyusul dari portal)

APA YANG DIBANGUN BARU (struktur standar kampus, bukan data akademik):
  * 16 pertemuan per MK, UTS di pertemuan 8, UAS di pertemuan 16
  * bobot mengikuti config/aturan.json: 14 x 4 + UTS 20 + UAS 24 = 100
  * setiap pertemuan punya slot absen (default 2 - silakan ubah di tab Kurikulum)

Yang MASIH PERLU DIISI MANUSIA (dicatat di berkas, tidak ditebak diam-diam):
  * jenis_mk tiap MK (teori / studio / teori_studio)
  * semester_kurikulum tiap MK (MK ini diajarkan di semester berapa)
  * topik pertemuan 7 dan 9-15 (pertemuan 1-6 memakai topik asli)

SEJAK v2.6 - `--force` TIDAK LAGI MENIMPA HASIL EDIT DASHBOARD:
  Migrasi ini membangun ULANG STRUKTUR, tetapi setiap isi yang memang milik
  manusia dipertahankan apa adanya:
    * topik & deskripsi pertemuan  (sudah lama dipertahankan)
    * bobot per pertemuan dan jumlah slot absen (suntingan tab Kurikulum)
    * jenis_mk dan semester_kurikulum yang sudah DIKONFIRMASI manusia
      (sumbernya bukan "tebakan"), baik di penawaran.json maupun cetak_biru_mk.json
    * nilai.json yang sudah ada TIDAK PERNAH ditimpa - regenerasi nilai sintetis
      adalah tugas `scripts/seed_nilai_sintetis.py` (mau `--force`), bukan efek
      samping migrasi.

  Sebelumnya `--force` menulis ulang bobot dari template, mengembalikan
  jenis_mk/semester_kurikulum ke tebakan mesin, dan menimpa nilai.json. Itu
  menghapus pekerjaan kaprodi hanya karena ingin merapikan struktur.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aturan as AT  # noqa: E402
import identitas as IDENT  # noqa: E402
import kurikulum_tree as KT  # noqa: E402
import persona as PS  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_PATH = os.path.join(BASE_DIR, "data", "academic_data.json")
COURSES_DIR = os.path.join(BASE_DIR, "data", "courses")

BULAN_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
            "Agustus", "September", "Oktober", "November", "Desember"]

# Default slot absen per pertemuan. Ubah per MK di tab Kurikulum.
# (Contoh user: kuliah 2 sesi pagi sampai sore bisa butuh 4x ambil absen.)
SLOT_ABSEN_DEFAULT = 2


def format_tanggal_id(d):
    return "{0:02d} {1} {2}".format(d.day, BULAN_ID[d.month - 1], d.year)


def tebak_jenis_mk(kunci, mk):
    """Tebakan awal jenis_mk DARI NAMA/RUANG - bukan data resmi.

    Sengaja ditandai `sumber_jenis_mk: 'tebakan-awal'` supaya tidak ada yang
    mengira ini sudah kurikulum resmi.
    """
    nama = "{0} {1}".format(kunci, mk.get("nama_mk", "")).upper()
    kelas = str(mk.get("kelas", "")).upper()
    if "STUDIO" in nama:
        return "studio"
    if "LAB" in kelas:
        return "teori_studio"
    return "teori"


def sesi_lama_untuk(kunci, master, kunci_aktif):
    """(daftar baris lama, dari_tree) untuk dipertahankan saat membangun tree.

    Urutan prioritas: tree kurikulum (paling baru, sudah berisi suntingan) ->
    master/katalog (artefak kompilasi). Tujuannya supaya migrasi boleh dijalankan
    berulang tanpa menimpa topik yang sudah benar.

    `dari_tree=True` hanya bila barisnya berasal dari tree kurikulum - yaitu
    berkas yang benar-benar disunting tab Kurikulum. Hanya di kasus itu bobot dan
    slot absen boleh dipertahankan; sumber lain (master/katalog) hanya dipakai
    untuk topik, supaya struktur mereka yang belum tentu 16 pertemuan tidak
    dipaksa masuk.
    """
    try:
        prodi, ta, sem = lokasi_mk(kunci)
        if prodi and ta and sem:
            path_tree = KT.path_berkas(prodi, ta, sem, kunci, "sesi.json")
            if os.path.exists(path_tree):
                return [dict(s) for s in KT.baca_json(path_tree).get("sesi", [])], True
    except Exception:  # noqa: BLE001 - tree belum ada = wajar saat migrasi pertama
        pass

    if kunci == kunci_aktif:
        return [dict(s) for s in master.get("sessions", [])], False
    path = os.path.join(COURSES_DIR, "{0}.json".format(kunci))
    if os.path.exists(path):
        try:
            return [dict(s) for s in KT.baca_json(path).get("sessions", [])], False
        except KT.KurikulumError:
            return [], False
    return [], False


def lokasi_mk(kunci):
    """(prodi, tahun_ajar, semester) untuk satu MK, dari config/identitas.json."""
    inst = IDENT.institusi()
    mk = IDENT.mk(kunci)
    ta, sem = KT.pecah_semester(mk.get("semester"))
    return inst.get("prodi", ""), ta, sem


# =============================================================================
# PRESERVASI HASIL EDIT MANUSIA (dipakai `--force`)
# =============================================================================
TEBAKAN_PENANDA = "tebakan"


def baca_json_aman(path):
    """Baca JSON kalau ada; kalau tidak ada / rusak -> None (bukan crash)."""
    if not path or not os.path.exists(path):
        return None
    try:
        return KT.baca_json(path)
    except (KT.KurikulumError, OSError, ValueError):
        return None


def sudah_dikonfirmasi(dok, kunci_nilai, kunci_sumber):
    """True bila sebuah nilai di dokumen lama berasal dari MANUSIA, bukan tebakan mesin.

    Penandanya adalah `sumber_*`: kalau sumbernya mengandung kata "tebakan",
    nilai itu masih tebakan awal (boleh diperbarui mesin). Selain itu - misalnya
    "dikonfirmasi-dashboard" - berarti kaprodi sudah menetapkannya dan migrasi
    TIDAK boleh mengembalikannya ke tebakan.
    """
    if not isinstance(dok, dict):
        return False
    nilai = dok.get(kunci_nilai)
    sumber = str(dok.get(kunci_sumber) or "").strip().lower()
    return nilai not in (None, "") and bool(sumber) and TEBAKAN_PENANDA not in sumber


def pilih_nilai(nilai_tebakan, sumber_tebakan, dok_lama, kunci_nilai, kunci_sumber):
    """Nilai final = yang sudah dikonfirmasi manusia kalau ada, kalau tidak tebakan."""
    if sudah_dikonfirmasi(dok_lama, kunci_nilai, kunci_sumber):
        return dok_lama.get(kunci_nilai), dok_lama.get(kunci_sumber)
    return nilai_tebakan, sumber_tebakan


def slot_absen_default(jumlah=SLOT_ABSEN_DEFAULT):
    return [{"slot": j + 1, "label": "Absen {0}".format(j + 1)} for j in range(jumlah)]


def slot_absen_lama(baris_lama):
    """Slot absen yang sudah ada di berkas, kalau bentuknya masih masuk akal."""
    slots = (baris_lama or {}).get("slot_absen")
    if isinstance(slots, list) and slots and all(isinstance(s, dict) for s in slots):
        return [dict(s) for s in slots]
    return None


def bobot_lama(baris_lama):
    """Bobot pertemuan yang sudah ada, kalau angkanya masuk akal; selain itu None."""
    try:
        b = int((baris_lama or {}).get("bobot"))
    except (TypeError, ValueError):
        return None
    return b if 0 <= b <= 100 else None


# Teks topik yang BUKAN topik asli + aturan penandanya SEKARANG hidup di
# scripts/kurikulum_tree.py (`KT.topik_terverifikasi`, `KT.TOPIK_PLACEHOLDER`).
# Dulu ada DUA salinan aturan (di sini dan di server.py) yang bisa berbeda hasil.


def bangun_sesi(kunci, penawaran, sesi_lama, ujian, pertahankan_suntingan=False):
    """16 pertemuan standar kampus, suntingan manusia dipertahankan apa adanya.

    Dari `sesi_lama` selalu dipertahankan: topik, deskripsi, tanggal.
    Kalau `pertahankan_suntingan` (baris berasal dari tree kurikulum), bobot dan
    jumlah slot absen juga dipertahankan - itulah suntingan tab Kurikulum.
    Yang selalu dihitung ulang: nomor pertemuan, tipe (dari jenis_mk), tanggal
    turunan yang belum ada, dan status terverifikasi.
    """
    total = AT.pertemuan_total()
    bobot_t = AT.standar_kampus()["bobot_template"]
    jenis = penawaran["jenis_mk"]

    # Peta per NOMOR PERTEMUAN (bukan per posisi daftar). Ini yang membuat
    # migrasi aman diulang: topik/tanggal yang sudah ada tidak ditimpa.
    lama_per_pertemuan = {}
    for s in sesi_lama:
        try:
            lama_per_pertemuan[int(s.get("pertemuan"))] = s
        except (TypeError, ValueError):
            continue

    # Tanggal dasar = tanggal TERAKHIR yang berasal dari sumber lama. Tanggal
    # turunan pertemuan 7..16 dihitung mingguan dari titik itu, jadi hasilnya
    # sama setiap kali migrasi dijalankan.
    dasar = None
    for s in sesi_lama:
        tgl = s.get("tanggal")
        if not tgl:
            continue
        try:
            d = datetime.strptime(tgl, "%Y-%m-%d")
        except ValueError:
            continue
        dasar = d if dasar is None else max(dasar, d)
    if dasar is None:
        dasar = datetime(2026, 6, 3)

    baris = []
    for i in range(1, total + 1):
        if i == ujian.get("uts"):
            tipe = "uts"
        elif i == ujian.get("uas"):
            tipe = "uas"
        elif jenis == "studio":
            tipe = "studio"
        elif jenis == "teori_studio":
            tipe = "teori" if i % 2 else "studio"
        else:
            tipe = "teori"

        lama = lama_per_pertemuan.get(i)
        topik = (lama or {}).get("topik", "")
        deskripsi = (lama or {}).get("deskripsi", "")
        tanggal = (lama or {}).get("tanggal")

        # Baris baru (belum ada di sumber lama) dibuat dari struktur standar.
        if not topik:
            if tipe == "uts":
                topik, deskripsi = "Ujian Tengah Semester", "Evaluasi tengah semester."
            elif tipe == "uas":
                topik, deskripsi = "Ujian Akhir Semester", "Evaluasi akhir semester."
            else:
                topik, deskripsi = KT.TOPIK_PLACEHOLDER, ""

        if tanggal:
            try:
                d = datetime.strptime(tanggal, "%Y-%m-%d")
            except ValueError:
                tanggal = None
        if not tanggal:
            # Pertemuan 1..6 punya tanggal asli; sisanya mingguan dari baseline.
            offset = i - max(len(lama_per_pertemuan), 6)
            d = dasar + timedelta(days=7 * offset)

        # BOBOT: pakai suntingan dashboard kalau barisnya memang dari tree;
        # kalau tidak, template. Dulu baris ini selalu menimpa bobot dengan
        # template, sehingga menjalankan ulang migrasi mengembalikan bobot yang
        # sudah diatur kaprodi.
        bobot = bobot_lama(lama) if pertahankan_suntingan else None
        if bobot is None:
            if tipe == "uts":
                bobot = bobot_t["uts"]
            elif tipe == "uas":
                bobot = bobot_t["uas"]
            else:
                bobot = bobot_t["per_pertemuan"]

        # SLOT ABSEN: idem - suntingan dashboard kalau ada, kalau tidak default.
        slots = (slot_absen_lama(lama) if pertahankan_suntingan else None) \
            or slot_absen_default()

        baris.append({
            "pertemuan": i,
            "tipe": tipe,
            "tanggal": d.strftime("%Y-%m-%d"),
            "tanggal_display": format_tanggal_id(d),
            "topik": topik,
            "deskripsi": deskripsi,
            "bobot": bobot,
            "topik_terverifikasi": KT.topik_terverifikasi(topik),
            "slot_absen": slots,
        })

    return {
        "versi": 1,
        "kunci_mk": kunci,
        "catatan": (
            "16 pertemuan standar kampus. UTS di pertemuan {0}, UAS di pertemuan {1}. "
            "bobot harus berjumlah 100. Slot absen per pertemuan boleh diubah "
            "(1, 2, atau lebih) sesuai jadwal MK.".format(ujian.get("uts"), ujian.get("uas"))
        ),
        "topik_terisi": sum(1 for b in baris if b["topik_terverifikasi"]),
        "topik_placeholder": sum(1 for b in baris if not b["topik_terverifikasi"]),
        "sesi": baris,
    }


def main():
    parser = argparse.ArgumentParser(description="Migrasi data lama ke tree kurikulum")
    parser.add_argument(
        "--force", action="store_true",
        help=("Bangun ulang STRUKTUR tree. Hasil edit manusia (topik, deskripsi, "
              "bobot, slot absen, jenis_mk/semester_kurikulum yang sudah "
              "dikonfirmasi, dan nilai.json) DIPERTAHANKAN - tidak ditimpa."),
    )
    args = parser.parse_args()

    if not os.path.exists(MASTER_PATH):
        print("[GAGAL] data master tidak ada: {0}".format(MASTER_PATH))
        return 1
    master = KT.baca_json(MASTER_PATH)
    institusi = IDENT.institusi()
    prodi = institusi.get("prodi", "")
    kunci_aktif = IDENT.mk_aktif()
    ujian = AT.pertemuan_ujian()

    # Jangan timpa tanpa izin: migrasi ini sekali jalan.
    cek = KT.path_mahasiswa(prodi)
    if os.path.exists(cek) and not args.force:
        print("[BERHENTI] Tree kurikulum sudah ada ({0}).".format(cek))
        print("           Jalankan dengan --force kalau memang mau membangun ulang.")
        return 1

    ditulis = []

    # 1. Identitas mahasiswa se-prodi (canonical: nama hanya ada di sini)
    mahasiswa = []
    for s in master.get("students", []):
        npm = str(s.get("npm"))
        mahasiswa.append({
            "npm": npm,
            "nama": s.get("nama", ""),
            "angkatan": KT.angkatan_dari_npm(npm),
        })
    KT.tulis_json(KT.path_mahasiswa(prodi), {
        "versi": 1,
        "prodi": prodi,
        "fakultas": institusi.get("fakultas", ""),
        "catatan": (
            "IDENTITAS CANONICAL. Nama mahasiswa hanya boleh ada di sini; "
            "berkas nilai per MK menyimpan NPM saja, supaya koreksi satu nama "
            "tidak perlu diburu ke puluhan berkas. `angkatan` dihitung dari 2 "
            "digit awal NPM."
        ),
        "mahasiswa": mahasiswa,
    })
    ditulis.append(KT.path_mahasiswa(prodi))

    # 2. Cetak biru MK (semester_kurikulum masih perlu konfirmasi kaprodi)
    ta_aktif, sem_aktif = KT.pecah_semester(IDENT.mk(kunci_aktif).get("semester"))
    sem_ke_kelas = KT.semester_ke(KT.angkatan_dari_npm(mahasiswa[0]["npm"]), ta_aktif, sem_aktif)
    # Cetak biru lama dibaca dulu: nilai yang sudah dikonfirmasi kaprodi jangan
    # dikembalikan menjadi tebakan mesin hanya karena migrasi dijalankan ulang.
    cb_lama_per_kunci = {}
    dok_cb_lama = baca_json_aman(KT.path_cetak_biru(prodi))
    for c in ((dok_cb_lama or {}).get("mata_kuliah") or []):
        if isinstance(c, dict) and c.get("kunci_mk"):
            cb_lama_per_kunci[str(c["kunci_mk"])] = c
    sumber_sem_tebakan = (
        "dari angkatan kelas saat ini (semua angkatan {0} di semester {1})".format(
            mahasiswa[0]["angkatan"] if mahasiswa else "-", sem_ke_kelas
        )
    )
    cetak_biru = []
    peta_jenis = {}
    for kunci, mk in IDENT.daftar_mk().items():
        c_lama = cb_lama_per_kunci.get(kunci) or {}
        # penawaran.json = berkas yang benar-benar ditulis tab Kurikulum, jadi
        # konfirmasinya MENANG atas cetak biru. Urutan: tebakan -> cetak biru lama
        # -> penawaran lama.
        ta_mk, sem_mk_dir = KT.pecah_semester(mk.get("semester"))
        pw_lama_mk = baca_json_aman(
            KT.path_berkas(prodi, ta_mk, sem_mk_dir, kunci, "penawaran.json")) or {}
        jenis_mk, sumber_jenis = pilih_nilai(
            tebak_jenis_mk(kunci, mk), "tebakan-awal-dari-nama-dan-ruang",
            c_lama, "jenis_mk", "sumber_jenis_mk",
        )
        jenis_mk, sumber_jenis = pilih_nilai(
            jenis_mk, sumber_jenis, pw_lama_mk, "jenis_mk", "sumber_jenis_mk",
        )
        sem_final, sumber_sem = pilih_nilai(
            sem_ke_kelas, sumber_sem_tebakan,
            c_lama, "semester_kurikulum", "sumber_semester_kurikulum",
        )
        sem_final, sumber_sem = pilih_nilai(
            sem_final, sumber_sem, pw_lama_mk,
            "semester_kurikulum", "sumber_semester_kurikulum",
        )
        peta_jenis[kunci] = jenis_mk
        cetak_biru.append({
            "kunci_mk": kunci,
            "kode_mk": mk.get("kode_mk", ""),
            "nama_mk": mk.get("nama_mk", ""),
            "sks": mk.get("sks"),
            "jenis_mk": jenis_mk,
            "semester_kurikulum": sem_final,
            "sumber_jenis_mk": sumber_jenis,
            "sumber_semester_kurikulum": sumber_sem,
        })
    # Catatan harus jujur: kalau semua baris sudah dikonfirmasi, jangan bilang
    # "masih tebakan" - dan sebaliknya.
    jumlah_tebakan = sum(
        1 for c in cetak_biru if TEBAKAN_PENANDA in str(c["sumber_jenis_mk"]).lower()
    )
    if jumlah_tebakan == 0:
        catatan_cb = (
            "CETAK BIRU KURIKULUM. `jenis_mk` (teori/studio/teori_studio) dan "
            "`semester_kurikulum` di sini SUDAH DIKONFIRMASI manusia (lihat "
            "`sumber_*` tiap baris). `semester_kurikulum` dipakai untuk mendeteksi "
            "mahasiswa mengulang secara otomatis."
        )
    elif jumlah_tebakan == len(cetak_biru):
        catatan_cb = (
            "CETAK BIRU KURIKULUM. `jenis_mk` (teori/studio/teori_studio) dan "
            "`semester_kurikulum` di sini masih TEBakan awal - mohon dikonfirmasi "
            "kaprodi. `semester_kurikulum` dipakai untuk mendeteksi mahasiswa "
            "mengulang secara otomatis."
        )
    else:
        catatan_cb = (
            "CETAK BIRU KURIKULUM. Sebagian baris sudah dikonfirmasi, sebagian "
            "masih tebakan - lihat `sumber_jenis_mk`/`sumber_semester_kurikulum` "
            "tiap baris (yang TIDAK memuat kata 'tebakan' berarti sudah "
            "dikonfirmasi manusia). `semester_kurikulum` dipakai untuk mendeteksi "
            "mahasiswa mengulang secara otomatis."
        )
    KT.tulis_json(KT.path_cetak_biru(prodi), {
        "versi": 1,
        "prodi": prodi,
        "catatan": catatan_cb,
        "mata_kuliah": cetak_biru,
    })
    ditulis.append(KT.path_cetak_biru(prodi))

    # 3. Per MK: penawaran + sesi + nilai
    ringkasan = []
    for kunci, mk in IDENT.daftar_mk().items():
        ta, sem = KT.pecah_semester(mk.get("semester"))
        sesi_lama = sesi_lama_untuk(kunci, master, kunci_aktif)
        baris_lama, dari_tree = sesi_lama
        path_penawaran = KT.path_berkas(prodi, ta, sem, kunci, "penawaran.json")
        path_sesi = KT.path_berkas(prodi, ta, sem, kunci, "sesi.json")
        path_nilai = KT.path_berkas(prodi, ta, sem, kunci, "nilai.json")

        # penawaran.json lama adalah sumber UTAMA konfirmasi kaprodi (itulah yang
        # ditulis tab Kurikulum). Cetak biru dipakai sebagai cadangan.
        pw_lama = baca_json_aman(path_penawaran) or {}
        cb = next((c for c in cetak_biru if c["kunci_mk"] == kunci), {})
        jenis_mk, sumber_jenis = pilih_nilai(
            cb.get("jenis_mk", peta_jenis.get(kunci, "teori")),
            cb.get("sumber_jenis_mk", "tebakan-awal-dari-nama-dan-ruang"),
            pw_lama, "jenis_mk", "sumber_jenis_mk",
        )
        sem_mk, sumber_sem = pilih_nilai(
            cb.get("semester_kurikulum", sem_ke_kelas),
            cb.get("sumber_semester_kurikulum", sumber_sem_tebakan),
            pw_lama, "semester_kurikulum", "sumber_semester_kurikulum",
        )

        penawaran = {
            "versi": 1,
            "prodi": prodi,
            "fakultas": institusi.get("fakultas", ""),
            "tahun_ajar": ta,
            "semester": sem,
            "kunci_mk": kunci,
            "kode_mk": mk.get("kode_mk", ""),
            "nama_mk": mk.get("nama_mk", ""),
            "sks": mk.get("sks"),
            "jenis_mk": jenis_mk,
            "sumber_jenis_mk": sumber_jenis,
            "semester_kurikulum": sem_mk,
            "sumber_semester_kurikulum": sumber_sem,
            "kelas": mk.get("kelas", ""),
            "jadwal": mk.get("jadwal", ""),
            "dosen_pengasuh": list(mk.get("dosen_pengasuh") or []),
            "asisten_dosen": mk.get("asisten_dosen", ""),
        }
        # Kalau nilainya masih tebakan, simpan jejak tebakannya supaya jelas.
        if TEBAKAN_PENANDA in str(sumber_jenis).lower():
            penawaran["tebakan_jenis_mk"] = tebak_jenis_mk(kunci, mk)
        penawaran["peringatan_jadwal"] = KT.peringatan_jadwal(
            penawaran["jadwal"], penawaran["sks"] or 0, penawaran["jenis_mk"]
        )

        sesi_doc = bangun_sesi(kunci, penawaran, baris_lama, ujian,
                               pertahankan_suntingan=dari_tree)
        masalah = KT.validasi_sesi(sesi_doc, kunci)
        if masalah:
            print("[GAGAL] sesi {0} tidak valid: {1}".format(kunci, masalah))
            return 1

        # nilai.json: kalau sudah ada, JANGAN ditimpa. Mengganti data nilai bukan
        # tugas migrasi struktur. Regenerasi nilai sintetis punya script sendiri.
        nilai_lama = baca_json_aman(path_nilai)
        if nilai_lama is not None:
            nilai_doc = nilai_lama
        else:
            # Bentuk dokumen + bumbu RNG per MK dipusatkan di persona.py supaya
            # script seed (scripts/seed_nilai_sintetis.py) tidak bisa berbeda.
            nilai_doc = PS.dokumen_nilai_sintetis(
                kunci, ta, sem,
                PS.bangun_nilai_satu_mk(mahasiswa, sesi_doc, konteks=str(kunci)),
            )

        KT.tulis_json(path_penawaran, penawaran)
        KT.tulis_json(path_sesi, sesi_doc)
        ditulis += [path_penawaran, path_sesi]
        if nilai_lama is None:
            KT.tulis_json(path_nilai, nilai_doc)
            ditulis.append(path_nilai)

        ringkasan.append({
            "kunci": kunci, "ta": ta, "sem": sem, "jenis": penawaran["jenis_mk"],
            "pertemuan": len(sesi_doc["sesi"]), "slot": KT.jumlah_slot(sesi_doc),
            "topik_asli": sesi_doc["topik_terisi"],
            "nilai_baris": len(nilai_doc.get("nilai") or []),
            "nilai_dipertahankan": nilai_lama is not None,
            "peringatan": penawaran["peringatan_jadwal"],
        })

    # 4. Index turunan
    index = KT.bangun_index({
        "prodi": KT.sanitize_folder_name(prodi),
        "tahun_ajar": ta_aktif,
        "semester": sem_aktif,
        "kunci_mk": kunci_aktif,
    })
    KT.tulis_json(KT.INDEX_PATH, index)
    ditulis.append(KT.INDEX_PATH)

    print("=" * 72)
    print("MIGRASI KURIKULUM SELESAI")
    print("=" * 72)
    print("Prodi       : {0}   (angkatan {1}, semester ke-{2})".format(
        prodi, mahasiswa[0]["angkatan"] if mahasiswa else "-", sem_ke_kelas))
    print("Mahasiswa   : {0}".format(len(mahasiswa)))
    print("Berkas      : {0} file".format(len(ditulis)))
    print("-" * 72)
    for r in ringkasan:
        print("  {0}".format(r["kunci"]))
        print("    {0} {1} | {2} | {3} pertemuan | {4} slot absen".format(
            r["ta"], r["sem"], r["jenis"], r["pertemuan"], r["slot"]))
        nilai_info = "{0} baris nilai".format(r["nilai_baris"])
        if r["nilai_dipertahankan"]:
            nilai_info += " (DIPERTAHANKAN - tidak ditimpa)"
        print("    topik asli {0}, placeholder {1} | {2}".format(
            r["topik_asli"], r["pertemuan"] - r["topik_asli"], nilai_info))
        for w in r["peringatan"]:
            print("    [PERINGATAN] {0}".format(w))
    print("=" * 72)
    print("Catatan: hasil edit dashboard (bobot, slot absen, jenis_mk, "
          "semester_kurikulum yang dikonfirmasi) dan nilai.json DIPERTAHANKAN.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())

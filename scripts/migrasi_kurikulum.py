"""MIGRASI SEKALI JALAN: data lama -> tree kurikulum bertingkat.

Jalankan:  python scripts\\migrasi_kurikulum.py            (tolak kalau sudah ada)
           python scripts\\migrasi_kurikulum.py --force    (timpa)

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
    """Topik yang sudah pernah ada, untuk DIPERTAHANKAN saat membangun tree.

    Urutan prioritas: tree kurikulum (paling baru, sudah berisi suntingan) ->
    master/katalog (artefak kompilasi). Tujuannya supaya migrasi boleh dijalankan
    berulang tanpa menimpa topik yang sudah benar.
    """
    try:
        prodi, ta, sem = lokasi_mk(kunci)
        if prodi and ta and sem:
            path_tree = KT.path_berkas(prodi, ta, sem, kunci, "sesi.json")
            if os.path.exists(path_tree):
                return [dict(s) for s in KT.baca_json(path_tree).get("sesi", [])]
    except Exception:  # noqa: BLE001 - tree belum ada = wajar saat migrasi pertama
        pass

    if kunci == kunci_aktif:
        return [dict(s) for s in master.get("sessions", [])]
    path = os.path.join(COURSES_DIR, "{0}.json".format(kunci))
    if os.path.exists(path):
        try:
            return [dict(s) for s in KT.baca_json(path).get("sessions", [])]
        except KT.KurikulumError:
            return []
    return []


def lokasi_mk(kunci):
    """(prodi, tahun_ajar, semester) untuk satu MK, dari config/identitas.json."""
    inst = IDENT.institusi()
    mk = IDENT.mk(kunci)
    ta, sem = KT.pecah_semester(mk.get("semester"))
    return inst.get("prodi", ""), ta, sem


# Teks topik yang BUKAN topik asli (hasil generate/pending RPS). Dipakai untuk
# menilai apakah sebuah baris pertemuan benar-benar berasal dari sumber lama -
# supaya migrasi yang diulang tidak pelan-pelan menaikkan status placeholder
# menjadi "terverifikasi".
PLACEHOLDER_TOPIK = {
    "",
    "(belum diisi - menunggu RPS)",
    "(belum diisi)",
    "Ujian Tengah Semester",
    "Ujian Akhir Semester",
}


def bangun_sesi(kunci, penawaran, sesi_lama, ujian):
    """16 pertemuan standar kampus, topik lama dipertahankan apa adanya."""
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
                topik, deskripsi = "(belum diisi - menunggu RPS)", ""

        if tanggal:
            try:
                d = datetime.strptime(tanggal, "%Y-%m-%d")
            except ValueError:
                tanggal = None
        if not tanggal:
            # Pertemuan 1..6 punya tanggal asli; sisanya mingguan dari baseline.
            offset = i - max(len(lama_per_pertemuan), 6)
            d = dasar + timedelta(days=7 * offset)

        if tipe == "uts":
            bobot = bobot_t["uts"]
        elif tipe == "uas":
            bobot = bobot_t["uas"]
        else:
            bobot = bobot_t["per_pertemuan"]

        baris.append({
            "pertemuan": i,
            "tipe": tipe,
            "tanggal": d.strftime("%Y-%m-%d"),
            "tanggal_display": format_tanggal_id(d),
            "topik": topik,
            "deskripsi": deskripsi,
            "bobot": bobot,
            "tanggal_terverifikasi": topik.strip() not in PLACEHOLDER_TOPIK,
            "slot_absen": [
                {"slot": j + 1, "label": "Absen {0}".format(j + 1)}
                for j in range(SLOT_ABSEN_DEFAULT)
            ],
        })

    return {
        "versi": 1,
        "kunci_mk": kunci,
        "catatan": (
            "16 pertemuan standar kampus. UTS di pertemuan {0}, UAS di pertemuan {1}. "
            "bobot harus berjumlah 100. Slot absen per pertemuan boleh diubah "
            "(1, 2, atau lebih) sesuai jadwal MK.".format(ujian.get("uts"), ujian.get("uas"))
        ),
        "topik_terisi": sum(1 for b in baris if b["tanggal_terverifikasi"]),
        "topik_placeholder": sum(1 for b in baris if not b["tanggal_terverifikasi"]),
        "sesi": baris,
    }


def main():
    parser = argparse.ArgumentParser(description="Migrasi data lama ke tree kurikulum")
    parser.add_argument("--force", action="store_true", help="Timpa berkas yang sudah ada")
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
    cetak_biru = []
    for kunci, mk in IDENT.daftar_mk().items():
        cetak_biru.append({
            "kunci_mk": kunci,
            "kode_mk": mk.get("kode_mk", ""),
            "nama_mk": mk.get("nama_mk", ""),
            "sks": mk.get("sks"),
            "jenis_mk": tebak_jenis_mk(kunci, mk),
            "semester_kurikulum": sem_ke_kelas,
            "sumber_jenis_mk": "tebakan-awal-dari-nama-dan-ruang",
            "sumber_semester_kurikulum": (
                "dari angkatan kelas saat ini (semua angkatan {0} di semester {1})".format(
                    mahasiswa[0]["angkatan"] if mahasiswa else "-", sem_ke_kelas
                )
            ),
        })
    KT.tulis_json(KT.path_cetak_biru(prodi), {
        "versi": 1,
        "prodi": prodi,
        "catatan": (
            "CETAK BIRU KURIKULUM. `jenis_mk` (teori/studio/teori_studio) dan "
            "`semester_kurikulum` di sini masih TEBakan awal - mohon dikonfirmasi "
            "kaprodi. `semester_kurikulum` dipakai untuk mendeteksi mahasiswa "
            "mengulang secara otomatis."
        ),
        "mata_kuliah": cetak_biru,
    })
    ditulis.append(KT.path_cetak_biru(prodi))

    # 3. Per MK: penawaran + sesi + nilai
    peta_jenis = {c["kunci_mk"]: c["jenis_mk"] for c in cetak_biru}
    ringkasan = []
    for kunci, mk in IDENT.daftar_mk().items():
        ta, sem = KT.pecah_semester(mk.get("semester"))
        sesi_lama = sesi_lama_untuk(kunci, master, kunci_aktif)
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
            "jenis_mk": peta_jenis[kunci],
            "sumber_jenis_mk": "tebakan-awal-dari-nama-dan-ruang",
            "semester_kurikulum": sem_ke_kelas,
            "sumber_semester_kurikulum": (
                "tebakan awal: semua angkatan {0} sekarang di semester {1} - "
                "mohon dikonfirmasi kaprodi".format(
                    mahasiswa[0]["angkatan"] if mahasiswa else "-", sem_ke_kelas
                )
            ),
            "kelas": mk.get("kelas", ""),
            "jadwal": mk.get("jadwal", ""),
            "dosen_pengasuh": list(mk.get("dosen_pengasuh") or []),
            "asisten_dosen": mk.get("asisten_dosen", ""),
        }
        penawaran["peringatan_jadwal"] = KT.peringatan_jadwal(
            penawaran["jadwal"], penawaran["sks"] or 0, penawaran["jenis_mk"]
        )

        sesi_doc = bangun_sesi(kunci, penawaran, sesi_lama, ujian)
        masalah = KT.validasi_sesi(sesi_doc, kunci)
        if masalah:
            print("[GAGAL] sesi {0} tidak valid: {1}".format(kunci, masalah))
            return 1

        nilai_rows = []
        for idx, m in enumerate(mahasiswa):
            nilai_rows.extend(PS.bangun_nilai_sintetis(m["npm"], idx, sesi_doc))
        nilai_doc = {
            "versi": 1,
            "kunci_mk": kunci,
            "tahun_ajar": ta,
            "semester": sem,
            "catatan": (
                "NILAI SINTETIS (bukan nilai resmi dosen). Dibangkitkan sekali "
                "supaya dashboard punya isi, dengan RNG per NPM sehingga menambah "
                "mahasiswa lain tidak menggeser angka siapa pun. Ganti dengan data "
                "portal begitu tersedia."
            ),
            "sintetis": True,
            "nilai": nilai_rows,
        }

        KT.tulis_json(KT.path_berkas(prodi, ta, sem, kunci, "penawaran.json"), penawaran)
        KT.tulis_json(KT.path_berkas(prodi, ta, sem, kunci, "sesi.json"), sesi_doc)
        KT.tulis_json(KT.path_berkas(prodi, ta, sem, kunci, "nilai.json"), nilai_doc)
        ditulis += [
            KT.path_berkas(prodi, ta, sem, kunci, "penawaran.json"),
            KT.path_berkas(prodi, ta, sem, kunci, "sesi.json"),
            KT.path_berkas(prodi, ta, sem, kunci, "nilai.json"),
        ]
        ringkasan.append({
            "kunci": kunci, "ta": ta, "sem": sem, "jenis": penawaran["jenis_mk"],
            "pertemuan": len(sesi_doc["sesi"]), "slot": KT.jumlah_slot(sesi_doc),
            "topik_asli": sesi_doc["topik_terisi"], "nilai_baris": len(nilai_rows),
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
        print("    topik asli {0}, placeholder {1} | {2} baris nilai".format(
            r["topik_asli"], r["pertemuan"] - r["topik_asli"], r["nilai_baris"]))
        for w in r["peringatan"]:
            print("    [PERINGATAN] {0}".format(w))
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())

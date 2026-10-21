"""seed_nilai_sintetis.py - bangkitkan ULANG nilai.json sintetis per mata kuliah.

KENAPA ADA
----------
Nilai + kehadiran di tree kurikulum adalah DATA SINTETIS (pengganti sementara
data portal). Benih RNG-nya dulu hanya `42 + npm`, jadi ketiga mata kuliah
berisi catatan yang PERSIS SAMA (byte per byte) - masalah yang sama seperti
"kelas yang sama, angka yang sama di semua MK".

Selain itu tidak ada jalan resmi untuk membangkitkan ulang: orang harus
menghapus `nilai.json` dulu supaya migrasi mau menulis lagi - cara yang
gampang dipakai untuk menghapus data tak sengaja.

Script ini jadi SATU pintu regenerasi yang aman:

  * benih RNG dapat bumbu kunci mata kuliah (lihat `scripts/persona.py`),
    sehingga tiap MK berbeda tapi tetap deterministic (panggil dua kali =
    berkas yang sama),
  * tanpa `--force`  -> DRY RUN: hanya melaporkan rencana + SHA yang AKAN
    ditulis, TIDAK menyentuh berkas apa pun,
  * dengan `--force` -> menulis, SETELAH menyalin `nilai.json` lama ke
    `data/_backup/seed_nilai_<timestamp>/...`.

FAIL-CLOSED
-----------
Berkas yang TIDAK bertanda `"sintetis": true` (artinya mungkin data portal
asli) TIDAK PERNAH ditimpa. Script berhenti dan minta manusia memutuskan.

CONTOH
------
    python scripts\\seed_nilai_sintetis.py            # lihat dulu
    python scripts\\seed_nilai_sintetis.py --force    # baru tulis
    python scripts\\seed_nilai_sintetis.py --force --kunci STUDIO_PERANCANGAN_ARSITEKTUR_2
"""

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aturan as AT          # noqa: E402
import kurikulum_tree as KT  # noqa: E402
import persona as PS         # noqa: E402


def _sha_berkas(path):
    """SHA256 (12 digit pertama) isi berkas apa adanya. None kalau tak ada."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12].upper()


def _sha_payload(payload):
    """SHA256 (12 digit pertama) dari byte yang AKAN ditulis `KT.tulis_json`."""
    teks = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return hashlib.sha256(teks.encode("utf-8")).hexdigest()[:12].upper()


def _daftar_target(prodi_filter, ta_filter, sem_filter, kunci_filter):
    """[(prodi, tahun_ajar, semester, kunci)] dari tree, urut dan tanpa duplikat."""
    target = []
    for prodi in KT.daftar_prodi():
        if prodi_filter and prodi != prodi_filter:
            continue
        for ta in KT.daftar_tahun(prodi):
            if ta_filter and ta.replace("/", "-") != ta_filter.replace("/", "-"):
                continue
            for sem in KT.daftar_semester(prodi, ta):
                if sem_filter and sem.upper() != sem_filter.upper():
                    continue
                for kunci in KT.daftar_mk(prodi, ta, sem):
                    if kunci_filter and kunci != kunci_filter:
                        continue
                    target.append((prodi, ta, sem, kunci))
    return target


def _baris_untuk_mk(prodi, ta, sem, kunci):
    """(dokumen_baru, jumlah_baris) untuk satu MK. Gagal = KT.KurikulumError."""
    path_mhs = KT.path_mahasiswa(prodi)
    if not os.path.exists(path_mhs):
        raise KT.KurikulumError(
            "Daftar mahasiswa prodi belum ada: {0}. Jalankan migrasi dulu.".format(path_mhs)
        )
    mahasiswa = (KT.baca_json(path_mhs).get("mahasiswa") or [])
    if not mahasiswa:
        raise KT.KurikulumError("Daftar mahasiswa {0} kosong.".format(path_mhs))

    path_sesi = KT.path_berkas(prodi, ta, sem, kunci, "sesi.json")
    sesi_doc = KT.baca_json(path_sesi)
    masalah = KT.validasi_sesi(sesi_doc, kunci)
    if masalah:
        raise KT.KurikulumError(
            "sesi.json {0} tidak valid: {1}".format(kunci, "; ".join(masalah))
        )

    baris = PS.bangun_nilai_satu_mk(mahasiswa, sesi_doc, konteks=str(kunci))
    # Kepala dokumen HARUS sama bentuknya dengan penawaran.json/sesi.json
    # ("2025/2026" + "GENAP"), bukan nama folder ("2025-2026"). Tanpa ini nilai
    # yang ditulis script ini dan yang ditulis migrasi akan berbeda kepala.
    return PS.dokumen_nilai_sintetis(
        kunci, KT.norm_tahun_ajar(ta), KT.slug_semester(sem), baris
    ), len(baris)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Bangkitkan ulang nilai.json sintetis (per mata kuliah).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Benar-benar menulis. Tanpa ini script hanya melaporkan rencana (dry run).",
    )
    parser.add_argument("--prodi", default="", help="Batasi ke satu prodi (mis. ARSITEKTUR).")
    parser.add_argument("--tahun-ajar", default="", help="Batasi ke satu tahun ajar (mis. 2025-2026).")
    parser.add_argument("--semester", default="", help="Batasi ke satu semester (GANJIL/GENAP).")
    parser.add_argument("--kunci", default="", help="Batasi ke satu kunci mata kuliah.")
    parser.add_argument(
        "--adopsi-sintetis", action="store_true",
        help="(SEKALI PAKAI) Anggap nilai.json tanpa penanda sintetis:true sebagai "
             "nilai sintetis lama dan timpa dengan hasil baru. Hanya untuk data demo "
             "yang sudah diketahui sintetis; data portal asli JANGAN dipakai dengan "
             "flag ini.",
    )
    args = parser.parse_args(argv)

    target = _daftar_target(args.prodi, args.tahun_ajar, args.semester, args.kunci)
    if not target:
        print("[GAGAL] Tidak ada mata kuliah yang cocok dengan filter.")
        return 1

    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak_dir = os.path.join(AT.BACKUP_DIR, "seed_nilai_{0}".format(stempel))

    print("Regenerasi nilai.json sintetis")
    print("  mode   : {0}".format("TULIS (--force)" if args.force else "DRY RUN (belum menulis)"))
    print("  mata kuliah: {0}".format(len(target)))
    print("")
    print("{0:<40} {1:>6} {2:>13} {3:>13}  {4}".format("MATA KULIAH", "BARIS", "SHA LAMA", "SHA BARU", "STATUS"))

    gagal = []
    siap = []
    for prodi, ta, sem, kunci in target:
        path_nilai = KT.path_berkas(prodi, ta, sem, kunci, "nilai.json")

        # FAIL-CLOSED: berkas non-sintetis = kemungkinan data portal asli.
        lama_mentah = None
        if os.path.exists(path_nilai):
            try:
                lama_mentah = KT.baca_json(path_nilai)
            except KT.KurikulumError as exc:
                gagal.append((kunci, "nilai.json rusak: {0}".format(exc)))
                print("{0:<40} {1:>6} {2:>13} {3:>13}  RUSAK".format(kunci[:40], "-", "-", "-"))
                continue
            if lama_mentah.get("sintetis") is not True and not args.adopsi_sintetis:
                gagal.append((kunci, "TIDAK bertanda sintetis:true (mungkin data portal asli) - tidak disentuh"))
                print("{0:<40} {1:>6} {2:>13} {3:>13}  DILEWATI".format(
                    kunci[:40], "-", _sha_berkas(path_nilai), "-"))
                continue

        try:
            dokumen, n_baris = _baris_untuk_mk(prodi, ta, sem, kunci)
        except KT.KurikulumError as exc:
            gagal.append((kunci, str(exc)))
            print("{0:<40} {1:>6} {2:>13} {3:>13}  GAGAL".format(kunci[:40], "-", "-", "-"))
            continue

        sha_lama = _sha_berkas(path_nilai)
        sha_baru = _sha_payload(dokumen)
        if sha_lama == sha_baru:
            status = "sama (tidak perlu ditulis)"
        elif sha_lama is None:
            status = "baru"
        else:
            status = "berubah"
        print("{0:<40} {1:>6} {2:>13} {3:>13}  {4}".format(
            kunci[:40], n_baris, sha_lama or "-", sha_baru, status))
        siap.append((prodi, ta, sem, kunci, path_nilai, dokumen))

    print("")
    if not args.force:
        print("DRY RUN selesai. Tidak ada berkas yang ditulis.")
        print("Jalankan ulang dengan --force untuk menulis (otomatis backup ke data/_backup/).")
        if gagal:
            for kunci, pesan in gagal:
                print("  [PERHATIAN] {0}: {1}".format(kunci, pesan))
            return 1
        return 0

    ditulis = 0
    for prodi, ta, sem, kunci, path_nilai, dokumen in siap:
        if os.path.exists(path_nilai):
            tujuan_bak = os.path.join(bak_dir, prodi, ta, sem, kunci, "nilai.json")
            os.makedirs(os.path.dirname(tujuan_bak), exist_ok=True)
            shutil.copy2(path_nilai, tujuan_bak)
        KT.tulis_json(path_nilai, dokumen)
        ditulis += 1

    print("Selesai. {0} nilai.json ditulis.".format(ditulis))
    if ditulis:
        print("Backup nilai lama: {0}".format(bak_dir))
        print("")
        print("LANJUTKAN dengan:")
        print("  python scripts\\parse_data.py        # segarkan data/academic_data.json")
        print("  lalu cetak ulang PDF dari dashboard (tab Identitas & Kelas).")
    if gagal:
        print("")
        print("Yang TIDAK disentuh:")
        for kunci, pesan in gagal:
            print("  [PERHATIAN] {0}: {1}".format(kunci, pesan))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

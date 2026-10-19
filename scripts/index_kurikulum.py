"""Bangun ulang `config/kurikulum.json` dari folder `data/kurikulum/`.

INDEX INI TURUNAN - JANGAN DIEDIT DENGAN TANGAN.
------------------------------------------------
Sumber kebenaran adalah folder `data/kurikulum/<PRODI>/<TAHUN_AJAR>/<SEMESTER>/<MK>/`.
Index hanya ringkasan supaya dashboard tidak perlu memindai seluruh folder
setiap kali dibuka.

Kalau index berbeda dari isi folder, FOLDER yang benar. Buktinya: kalau index
dihapus, perintah di bawah membangunnya kembali tanpa kehilangan apa pun.

Pemakaian:
    python scripts\\index_kurikulum.py            tulis ulang index
    python scripts\\index_kurikulum.py --check     bandingkan saja (0 = sinkron)
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import identitas as IDENT  # noqa: E402
import kurikulum_tree as KT  # noqa: E402


def pointer_aktif():
    """(prodi, TA, semester, kunci MK) yang sedang dipakai data master.

    Diambil dari config/identitas.json. Kalau gagal, index tetap dibangun -
    hanya kolom 'aktif' yang dikosongkan (jangan sampai index gagal total
    hanya karena satu pointer).
    """
    try:
        inst = IDENT.institusi()
        kunci = IDENT.mk_aktif()
        mk = IDENT.mk(kunci)
        ta, sem = KT.pecah_semester(mk.get("semester"))
        return {
            "prodi": KT.sanitize_folder_name(inst.get("prodi", "")),
            "tahun_ajar": ta,
            "semester": sem,
            "kunci_mk": kunci,
        }
    except Exception as exc:  # noqa: BLE001
        print("[PERINGATAN] pointer aktif tidak bisa ditentukan: {0}".format(exc))
        return None


def _tanpa_stempel(index):
    """Salinan index tanpa stempel waktu (untuk perbandingan --check)."""
    salin = json.loads(json.dumps(index))
    salin.pop("dibangun_pada", None)
    return salin


def main():
    parser = argparse.ArgumentParser(description="Bangun ulang index kurikulum")
    parser.add_argument("--check", action="store_true",
                        help="Bandingkan saja; keluar 1 kalau index berbeda dari isi folder")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    index = KT.bangun_index(pointer_aktif())

    if args.check:
        if not os.path.exists(KT.INDEX_PATH):
            print("[BEDA] config/kurikulum.json belum ada. Jalankan tanpa --check.")
            return 1
        lama = KT.baca_json(KT.INDEX_PATH)
        if _tanpa_stempel(lama) == _tanpa_stempel(index):
            print("[SINKRON] config/kurikulum.json cocok dengan isi folder.")
            return 0
        print("[BEDA] config/kurikulum.json TIDAK cocok dengan isi folder.")
        print("       Jalankan: python scripts\\index_kurikulum.py")
        return 1

    KT.tulis_json(KT.INDEX_PATH, index)
    if not args.quiet:
        jumlah_mk = 0
        for info in index["prodi"].values():
            for sem_map in info["tahun_ajar"].values():
                for isi in sem_map.values():
                    jumlah_mk += len(isi["mata_kuliah"])
        print("=" * 65)
        print("[INDEX KURIKULUM] {0}".format(KT.INDEX_PATH))
        print("  prodi       : {0}".format(", ".join(index["prodi"]) or "-"))
        print("  mata kuliah : {0}".format(jumlah_mk))
        print("  aktif       : {0}".format(index.get("aktif")))
        print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())

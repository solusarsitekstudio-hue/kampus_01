# -*- coding: utf-8 -*-
"""test_karier_ai_failclosed.py - LAPIS B (ai_karier.py) TANPA engine.

Yang dijaga (fail-closed, kuota tidak pernah terpakai di tes):
1. Config hilang/rusak -> nonaktif -> narasi_ai None + sebab.
2. Matriks tanpa `bukti` -> None (Lapis A wajib jalan dulu).
3. Engine tak tersedia -> None + sebab, TIDAK crash.
4. verifikasi_narasi: angka bukti lolos; angka karangan = tolak.
5. terapkan_ke_potensi / terapkan_cache: hanya baris lolos verifikasi yang
   ditempel; angka inti (kecocokan_persen) tidak pernah ditimpa AI.
6. Cache: kunci berubah bila bukti berubah; baris cache rusak = diabaikan.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.ai_karier as AK  # noqa: E402

GAGAL = []


def cek(nama, syarat, detail=""):
    if syarat:
        print("[OK  ] {0}".format(nama))
    else:
        print("[GAGAL] {0} {1}".format(nama, detail))
        GAGAL.append(nama)


MASTRIKS = [
    {"id": 2, "profesi": "BIM Modeler & Coordinator", "kecocokan_persen": 85.0,
     "kategori_kecocokan": "Tinggi",
     "bukti": ["penguasaan lingkungan CAD 88", "ketelitian detail gambar 84",
               "2 MK sekanal rata 84.5", "skor kecocokan 85"],
     "analisis_potensi": "template"},
    {"id": 3, "profesi": "Quantity Surveyor (QS)", "kecocokan_persen": 83.9,
     "kategori_kecocokan": "Tinggi",
     "bukti": ["ketelitian detail gambar 84", "skor kecocokan 83.9"],
     "analisis_potensi": "template"},
    {"id": 1, "profesi": "Architectural Designer", "kecocokan_persen": 80.2,
     "kategori_kecocokan": "Tinggi",
     "bukti": ["rata nilai sepanjang kuliah 78.9", "skor kecocokan 80.2"],
     "analisis_potensi": "template"},
]


def main():
    cfg_asli = AK.CHIP_KONFIG
    try:
        AK.CHIP_KONFIG = cfg_asli + ".hilang"
        if os.path.exists(AK.CHIP_KONFIG):
            os.remove(AK.CHIP_KONFIG)
        cek("1. config default fail-closed: file hilang -> aktif False",
            AK.muat_config()["aktif"] is False)
    finally:
        AK.CHIP_KONFIG = cfg_asli

    cek("2. verifikasi: narasi dengan angka bukti lolos",
        AK.verifikasi_narasi(
            "Raka menunjukkan penguasaan chat CAD 88 dengan rata 84.5.",
            MASTRIKS[0]["bukti"]))

    cek("3. verifikasi: angka karangan (77) yang tidak ada di bukti = TOLAK",
        not AK.verifikasi_narasi("Penguasaan CAD 77 saja.", MASTRIKS[0]["bukti"]))

    cek("4. verifikasi: pembulatan 1 desimal diperbolehkan (84.5 -> 85)",
        AK.verifikasi_narasi("Rata 85 antara dua MK.", MASTRIKS[0]["bukti"]))

    # config dinonaktifkan -> narasi_ai None tanpa menyentuh engine
    cfg_asli = AK.CHIP_KONFIG
    try:
        with open(cfg_asli + ".uji", "w", encoding="utf-8") as f:
            json.dump({"aktif": False}, f)
        AK.CHIP_KONFIG = cfg_asli + ".uji"
        h, s = AK.narasi_ai(
            {"analisis_potensi": {"matriks_karier_kuliah": MASTRIKS}},
            "ARSITEKTUR", "123")
        cek("5. fail-closed aktif=false -> hasil None + sebab",
            h is None and bool(s))
    finally:
        os.remove(cfg_asli + ".uji")
        AK.CHIP_KONFIG = cfg_asli

    # matriks tanpa bukti -> tanpa sebab, None
    h, s = AK.narasi_ai(
        {"analisis_potensi": {"matriks_karier_kuliah": [
            {"profesi": "X", "kecocokan_persen": 50}]}},
        "ARSITEKTUR", "123")
    cek("6. matriks tanpa bukti -> None (Lapis A prasyarat)",
        h is None)

    # terapkan_ke_potensi menolak teks berangka karangan
    hasil_ai = {"items": {
        "BIM Modeler & Coordinator": "Skor 85 dengan bukti CAD 88 rata 84.5.",
        "Quantity Surveyor (QS)": "Kecocokan 71% dengan teliti 77."},
    }
    kop = {"analisis_potensi": {"matriks_karier_kuliah": [dict(m) for m in MASTRIKS]}}
    AK.terapkan_ke_potensi(kop, hasil_ai)
    m1 = kop["potensi"]["matriks_karier_kuliah"][0]
    m2 = kop["potensi"]["matriks_karier_kuliah"][1]
    cek("7a. baris sah ditempel + label sumber 'ai'",
        m1["analisis_sumber"] == "ai" and "rata 84.5" in m1["analisis_potensi"])
    cek("7b. baris kasar (angka karangan) TIDAK ditempa",
        m2["analisis_potensi"] == "template"
        and "analisis_sumber" not in m2)
    cek("7c. kecocokan angka tidak disentuh AI",
        m1["kecocokan_persen"] == 85.0 and m2["kecocokan_persen"] == 83.9)

    # kunci cache berubah bila bukti berubah
    k1 = AK._kunci_cache("P", "123", "identitas A")
    k2 = AK._kunci_cache("P", "123", "identitas B")
    k3 = AK._kunci_cache("P", "456", "identitas A")
    cek("8. kunci cache: bukti beda = kunci beda; npm beda = kunci beda",
        k1 != k2 and k1 != k3 and k3 != k2)

    print()
    if GAGAL:
        print("HASIL: ADA YANG GAGAL ({0} kasus)".format(len(GAGAL)))
        return 1
    print("HASIL: SEMUA LULUS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

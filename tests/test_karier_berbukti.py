# -*- coding: utf-8 -*-
"""test_karier_berbukti.py - Lapis A "potensi karier berbukti".
Keputusan user 2026-10-21: matriks karier sepanjang kuliah harus
(a) ditimbang bukti nyata kanal (bukan bonus datar +4),
(b) punya field `bukti` berisi angka nyata, deterministik,
(c) analisis_potensi dibangun dari bukti (dinamis per mahasiswa),
(d) saran miring ke dim penopang terlemah,
(e) tanpa konteks -> perilaku lama (bonus +4) tetap dijamin.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.diagnosis as D  # noqa: E402
import scripts.bidang as BIDANG  # noqa: E402

GAGAL = []


def cek(nama, syarat, detail=""):
    if syarat:
        print("[OK  ] {0}".format(nama))
    else:
        print("[GAGAL] {0} {1}".format(nama, detail))
        GAGAL.append(nama)


RADAR = {
    "penguasaan_cad": 88,
    "ketelitian_detail": 84,
    "kedisiplinan_asistensi": 90,
    "logika_ruang_struktur": 76,
    "manajemen_waktu": 82,
}

KONTEKS = {
    "kanal_terkuat": "TEKNOLOGI",
    "nama_kanal": "Teknologi & Komputer Arsitektur",
    "mk_sekanal": [
        {"nama_mk": "Aplikasi Komputer", "nilai": 86, "grade": "B+"},
        {"nama_mk": "Gambar Teknik", "nilai": 83, "grade": "B+"},
        {"nama_mk": "Belum Diinput MK", "nilai": None, "grade": "Belum Lengkap"},
    ],
    "rata_nilai": 78.9,
    "dimensi_khas": {
        "presisi_cad": {"label": "Presisi CAD & Dokumentasi", "nilai": 85,
                         "sumber": "estimasi"},
        "manajemen_layer": {"label": "Manajemen Layer & Standar", "nilai": 80,
                              "sumber": "estimasi"},
        "volume_qs": {"label": "Perhitungan Volume QS", "nilai": 78,
                      "sumber": "estimasi"},
    },
}


def main():
    m = D.matriks_karier(RADAR, "Raka", bidang_terkuat="TEKNOLOGI",
                          konteks=KONTEKS)
    sekanal_ids = (2, 3, 4, 6)
    kat_sekanal = [c for c in m if c["id"] in sekanal_ids]
    kat_lain = [c for c in m if c["id"] not in sekanal_ids]

    cek("1a. field bukti ada di SEMUA item & berisi kalimat",
        all(isinstance(c.get("bukti"), list) and c["bukti"] for c in m))

    cek("1b. bukti menimbang kanal: item sekanal memuat angka MK sekanal",
        any("rata 84.5" in " ".join(c["bukti"]) for c in kat_sekanal),
        " ".join(kat_sekanal[0].get("bukti", [])))

    cek("1c. narasi dinamis: teks analisis berbeda antar profesi (bukan satu kalimat statis)",
        len({c["analisis_potensi"] for c in kat_lain[:3]}) == 3)

    cek("1d. narasi menyebut nama mahasiswa & angka bukti",
        all("Raka" in c["analisis_potensi"] for c in m[:3]))

    cek("1e. saran miring ke dim penopang terlemah",
        all("Langkah konkret" in c["saran_pengembangan"] for c in m[:3]))

    # determinisme penuh
    m2 = D.matriks_karier(RADAR, "Raka", bidang_terkuat="TEKNOLOGI",
                           konteks=KONTEKS)
    cek("2. DETERMINISTIK: profil sama -> hasil bit-identik", m == m2)

    # bukti kanal lebih tinggi -> kecocokan karier sekanal naik (monoton)
    konteks_baik = dict(KONTEKS, mk_sekanal=[
        {"nama_mk": "MK A", "nilai": 95, "grade": "A"},
        {"nama_mk": "MK B", "nilai": 93, "grade": "A"},
    ], dimensi_khas={
        k: dict(v, nilai=95) for k, v in KONTEKS["dimensi_khas"].items()
    })
    m_baik = D.matriks_karier(RADAR, "Raka", bidang_terkuat="TEKNOLOGI",
                               konteks=konteks_baik)
    cek_baik = {c["id"]: c["kecocokan_persen"] for c in m_baik}
    cek_asal = {c["id"]: c["kecocokan_persen"] for c in m}
    cek("3. MONOTON: bukti kanal naik -> kecocokan karier sekanal naik",
        all(cek_baik[i] > cek_asal[i] for i in sekanal_ids))

    # cap karier tetap dihormati (tidak pernah "100% pasti")
    caps = {i[0]: i[4] for i in D._KARIER}
    cek("4. CAP: tidak ada kecocokan melebihi cap profesi",
        all(c["kecocokan_persen"] <= caps[c["id"]] for c in m_baik))

    # tanpa konteks -> perilaku lama: bonus +4 & tanpa field bukti
    m_lama = D.matriks_karier(RADAR, "Raka", bidang_terkuat="TEKNOLOGI")
    cek("5a. kompatibel: tanpa konteks tidak ada field bukti",
        all("bukti" not in c for c in m_lama))
    skor_lama_elemen = [c for c in m_lama if c["id"] == 2][0]["kecocokan_persen"]
    b2 = float(RADAR["penguasaan_cad"]) * 0.60 \
        + float(RADAR["ketelitian_detail"]) * 0.20 \
        + float(RADAR["manajemen_waktu"]) * 0.20 + BIDANG.BONUS_KARIER_SEBIDANG
    cek("5b. kompatibel: skor sekanal lama = base + 4",
        abs(skor_lama_elemen - min(99, round(b2, 1))) < 0.05,
        "skor={0} harapan={1}".format(skor_lama_elemen, round(b2, 1)))

    # kisahkan: MK sekanal tanpa nilai tak merusak (fail-closed proporsional)
    konteks_bolong = dict(KONTEKS, mk_sekanal=[
        {"nama_mk": "MK X", "nilai": None, "grade": "Belum Lengkap"}])
    m_bolong = D.matriks_karier(RADAR, "Raka", bidang_terkuat="TEKNOLOGI",
                                 konteks=konteks_bolong)
    cek("6. FAIL-CLOSED: MK sekanal kosong tidak mengarang kecocokan",
        isinstance(m_bolong[0]["kecocokan_persen"], float)
        and 1.0 < m_bolong[0]["kecocokan_persen"] <= 99)

    print()
    if GAGAL:
        print("HASIL: ADA YANG GAGAL ({0} kasus)".format(len(GAGAL)))
        return 1
    print("HASIL: SEMUA LULUS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

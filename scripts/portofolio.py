"""portofolio.py - PEMBUNGKUS TIPIS fitur_mahasiswa (Zona 2, 2026-10-21).

Seluruh transformasi lapis 1-4 + analisis potensi DIPINDAH UTUH ke
scripts/fitur_mahasiswa.py: satu buka katalog per MK sepanjang umur proses
(ber-stempel mtime+ukuran, hanya MK basi yang dibangun ulang), bukan
membuka ulang 30 katalog SETIAP NPM seperti versi lama (terukur 280 ms per
mahasiswa -> kini ~ms untuk mahasiswa berikutnya).

Konsumen lama TIDAK terusik:
  - server.py      : portofolio.kumpulan_portofolio(npm)
  - generate_pdfs  : PORTO.kumpulan_portofolio(student["npm"]) (PDF 06)
  - test_portofolio: P.kumpulan_portofolio(...) + P._label_potensi(...)
Satu sumber yang tidak berubah: diagnosis.py (dipanggil saat kompilasi) dan
bidang.py (mesin kanal murni) - keduanya diimpor oleh fitur_mahasiswa.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from fitur_mahasiswa import (  # noqa: E402,F401
    kumpulan as _kumpulan_fitur,
    _label_potensi,  # SATU SUMBER ambang potensi (dipinjam test_portofolio)
    _isis_detail_bulanan,  # aturan chip bulanan (dipinjam test_portofolio)
)


def kumpulan_portofolio(npm):
    """Data portofolio lengkap 4 lapis untuk SATU mahasiswa (API lama).

    Kembalian None jika NPM tidak ada di katalog mana pun; ValueError kalau
    parameter kosong atau tree kosong. Dekomposisi ada di fitur_mahasiswa.
    """
    return _kumpulan_fitur(npm)

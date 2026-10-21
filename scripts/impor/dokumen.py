"""Ekstraksi teks dari dokumen modul: PDF, DOCX, dan penanda untuk gambar.

Yang penting di sini adalah KEJUJURAN: kalau PDF hasil scan tidak punya text
layer, fungsi ini tidak mencoba mengarang isi. Berkasnya ditandai
`ocr_dibutuhkan: true` dan pemanggil yang memutuskan (lewat AI vision atau
manusia).
"""
from __future__ import annotations

import os

from . import deteksi as deteksi_modul

CHUNK_BAWAAN = 8000


def baca_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dijaga tes dependensi
        raise RuntimeError(
            "pypdf belum terpasang. Jalankan: python -m pip install -r requirements.txt"
        ) from exc

    reader = PdfReader(path)
    halaman = []
    kosong = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            teks = page.extract_text() or ""
        except Exception as exc:  # PDF rusak sebagian - laporkan, jangan tebak
            teks = ""
            kosong.append({"nomor": i, "sebab": "gagal ekstrak: {0}".format(exc)})
        teks = teks.strip()
        if not teks and not any(k["nomor"] == i for k in kosong):
            kosong.append({"nomor": i, "sebab": "tidak ada text layer"})
        halaman.append({"nomor": i, "teks": teks})

    total_teks = sum(len(h["teks"]) for h in halaman)
    return {
        "berkas": os.path.basename(path),
        "jenis": "pdf",
        "halaman": halaman,
        "teks_lengkap": "\n\n".join(h["teks"] for h in halaman if h["teks"]),
        "ocr_dibutuhkan": total_teks == 0,
        "meta": {
            "jumlah_halaman": len(halaman),
            "halaman_tanpa_teks": [k["nomor"] for k in kosong],
            "jumlah_karakter": total_teks,
        },
    }


def baca_docx(path):
    try:
        import docx
    except ImportError as exc:  # pragma: no cover - dijaga tes dependensi
        raise RuntimeError(
            "python-docx belum terpasang. Jalankan: python -m pip install -r requirements.txt"
        ) from exc

    dokumen = docx.Document(path)
    bagian = []
    judul = "Awal dokumen"
    buf = []

    def tutup():
        teks = "\n".join(buf).strip()
        if teks:
            bagian.append({"nomor": len(bagian) + 1, "judul": judul, "teks": teks})

    for paragraf in dokumen.paragraphs:
        teks = (paragraf.text or "").strip()
        gaya = (paragraf.style.name or "").lower() if paragraf.style is not None else ""
        if teks and gaya.startswith("heading"):
            tutup()
            buf = []
            judul = teks
            continue
        if teks:
            buf.append(teks)

    # Tabel ikut dibaca - RPS biasanya berisi tabel pertemuan.
    for idx, tabel in enumerate(dokumen.tables, start=1):
        baris = []
        for row in tabel.rows:
            sel = [" ".join((c.text or "").split()) for c in row.cells]
            if any(sel):
                baris.append(" | ".join(sel))
        if baris:
            buf.append("[Tabel {0}]\n{1}".format(idx, "\n".join(baris)))

    tutup()

    return {
        "berkas": os.path.basename(path),
        "jenis": "docx",
        "halaman": bagian,
        "teks_lengkap": "\n\n".join(b["teks"] for b in bagian),
        "ocr_dibutuhkan": False,
        "meta": {
            "jumlah_bagian": len(bagian),
            "jumlah_karakter": sum(len(b["teks"]) for b in bagian),
            "catatan": "DOCX tidak menyimpan nomor halaman; bagian = heading/tabel.",
        },
    }


def baca_gambar(path):
    return {
        "berkas": os.path.basename(path),
        "jenis": "gambar",
        "halaman": [],
        "teks_lengkap": "",
        "ocr_dibutuhkan": True,
        "meta": {"catatan": "Gambar perlu AI vision atau input manual."},
    }


def baca(path, jenis=None):
    """Pintu masuk: pilih pembaca sesuai jenis hasil deteksi."""
    if jenis is None:
        jenis = deteksi_modul.deteksi(path)["jenis"]
    if jenis == "pdf":
        return baca_pdf(path)
    if jenis == "docx":
        return baca_docx(path)
    if jenis == "gambar":
        return baca_gambar(path)
    raise ValueError("jenis {0!r} bukan dokumen yang bisa diekstrak".format(jenis))


def potongan(halaman, maks_karakter=CHUNK_BAWAAN):
    """Gabungkan halaman menjadi potongan <= maks_karakter, simpan rentangnya.

    Dipakai analisis AI supaya setiap topik tetap bisa dilacak ke halamannya.
    """
    hasil = []
    buf = []
    ukuran = 0
    awal = None
    akhir = None
    for h in halaman:
        nomor = h.get("nomor")
        teks = h.get("teks") or ""
        if not teks:
            continue
        if buf and ukuran + len(teks) > maks_karakter:
            hasil.append({"halaman_awal": awal, "halaman_akhir": akhir,
                          "teks": "\n\n".join(buf)})
            buf, ukuran, awal, akhir = [], 0, None, None
        if awal is None:
            awal = nomor
        buf.append("[halaman {0}]\n{1}".format(nomor, teks))
        ukuran += len(teks)
        akhir = nomor
    if buf:
        hasil.append({"halaman_awal": awal, "halaman_akhir": akhir,
                      "teks": "\n\n".join(buf)})
    return hasil

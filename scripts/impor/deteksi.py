"""Deteksi jenis berkas masuk tanpa bergantung pada ekstensi saja.

Ekstensi bisa salah (portal sering mengunduh `data.xls` yang isinya HTML).
Karena itu urutannya: magic bytes -> isi -> ekstensi terakhir.
"""
from __future__ import annotations

import os
import zipfile

EKSTENSI = {
    ".xlsx": "xlsx",
    ".xlsm": "xlsx",
    ".xls": "xls_lama",
    ".csv": "csv",
    ".tsv": "csv",
    ".txt": "csv",
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc_lama",
    ".png": "gambar",
    ".jpg": "gambar",
    ".jpeg": "gambar",
    ".webp": "gambar",
    ".bmp": "gambar",
    ".html": "html",
    ".htm": "html",
}

JENIS_BISA_DIBACA = ("xlsx", "csv", "pdf", "docx", "html", "gambar")


def _isi_zip(path):
    try:
        with zipfile.ZipFile(path) as z:
            return set(z.namelist())
    except (zipfile.BadZipFile, OSError):
        return set()


def deteksi(path) -> dict:
    """Kembalikan {"jenis", "alasan", "bisa_dibaca"} untuk satu berkas."""
    nama = os.path.basename(str(path))
    ext = os.path.splitext(nama)[1].lower()
    tebakan_ext = EKSTENSI.get(ext)

    if not os.path.isfile(path):
        return {"jenis": "tidak_ada", "alasan": "berkas tidak ditemukan",
                "bisa_dibaca": False}

    with open(path, "rb") as f:
        kepala = f.read(8)

    if kepala.startswith(b"%PDF"):
        return {"jenis": "pdf", "alasan": "magic bytes %PDF", "bisa_dibaca": True}

    if kepala.startswith(b"\x89PNG\r\n\x1a\n") or kepala.startswith(b"\xff\xd8\xff"):
        return {"jenis": "gambar", "alasan": "magic bytes gambar", "bisa_dibaca": True}
    if kepala.startswith(b"RIFF") and ext in (".webp",):
        return {"jenis": "gambar", "alasan": "magic bytes RIFF/webp", "bisa_dibaca": True}

    if kepala.startswith(b"PK\x03\x04"):
        isi = _isi_zip(path)
        if "xl/workbook.xml" in isi:
            return {"jenis": "xlsx", "alasan": "zip berisi xl/workbook.xml",
                    "bisa_dibaca": True}
        if "word/document.xml" in isi:
            return {"jenis": "docx", "alasan": "zip berisi word/document.xml",
                    "bisa_dibaca": True}
        return {"jenis": "zip_lain", "alasan": "zip tanpa workbook/document",
                "bisa_dibaca": False}

    # .xls lama (BIFF) - tidak didukung, jangan menebak isinya
    if kepala.startswith(b"\xd0\xcf\x11\xe0"):
        return {"jenis": "xls_lama", "alasan": "format OLE/BIFF (.xls lama)",
                "bisa_dibaca": False}

    # Teks: cek apakah HTML atau CSV
    try:
        with open(path, "r", encoding="utf-8-sig", errors="strict") as f:
            contoh = f.read(4096)
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1", errors="replace") as f:
            contoh = f.read(4096)

    rendah = contoh.lower()
    if "<table" in rendah or "<html" in rendah:
        return {"jenis": "html", "alasan": "isi mengandung <table>/<html>",
                "bisa_dibaca": True}
    if tebakan_ext == "csv" or ("," in contoh or ";" in contoh or "\t" in contoh):
        return {"jenis": "csv", "alasan": "teks dengan pemisah kolom",
                "bisa_dibaca": True}

    if tebakan_ext in JENIS_BISA_DIBACA:
        return {"jenis": tebakan_ext, "alasan": "ekstensi " + ext,
                "bisa_dibaca": True}

    return {"jenis": "tidak_dikenal", "alasan": "tidak ada penanda yang cocok",
            "bisa_dibaca": False}


def pindai(folder) -> list:
    """Pindai folder (tidak rekursif) dan kembalikan daftar hasil deteksi."""
    hasil = []
    if not os.path.isdir(folder):
        return hasil
    for nama in sorted(os.listdir(folder)):
        if nama.startswith("."):
            continue  # .gitkeep dan berkas tersembunyi bukan bahan impor
        path = os.path.join(folder, nama)
        if not os.path.isfile(path):
            continue
        info = deteksi(path)
        info["berkas"] = nama
        info["path"] = path
        info["ukuran"] = os.path.getsize(path)
        hasil.append(info)
    return hasil

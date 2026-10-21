"""Pembaca tabel: xlsx, csv/tsv, dan tabel HTML.

Keluaran seragam:

    {"sumber": "nilai.xlsx / Sheet1", "header": ["NPM", "Nama", ...],
     "baris": [["2510015410010", "M YAZID", ...], ...],
     "meta": {"format": "xlsx", "jumlah_baris": 12}}

Tidak ada pemetaan kolom di sini - itu tugas profil.py.
"""
from __future__ import annotations

import csv
import datetime
import io
import os
from html.parser import HTMLParser


def _sel_teks(nilai) -> str:
    if nilai is None:
        return ""
    if isinstance(nilai, datetime.datetime):
        if nilai.time() == datetime.time(0, 0):
            return nilai.date().isoformat()
        return nilai.isoformat(sep=" ")
    if isinstance(nilai, datetime.date):
        return nilai.isoformat()
    if isinstance(nilai, float) and nilai == int(nilai):
        return str(int(nilai))
    return str(nilai).strip()


def _buang_baris_kosong(baris):
    return [b for b in baris if any(_sel_teks(c).strip() for c in b)]


def _tabel_dari_matriks(matriks, sumber, format_):
    """Matriks -> tabel dengan header baris pertama yang punya >= 2 sel."""
    matriks = _buang_baris_kosong(matriks)
    if not matriks:
        return None

    idx_header = 0
    for i, baris in enumerate(matriks):
        terisi = [c for c in baris if _sel_teks(c).strip()]
        if len(terisi) >= 2:
            idx_header = i
            break

    header = [_sel_teks(c) for c in matriks[idx_header]]
    # Buang kolom ekor yang seluruh header-nya kosong.
    while header and not header[-1].strip():
        header.pop()

    baris_data = []
    for baris in matriks[idx_header + 1:]:
        nilai = [_sel_teks(c) for c in baris][:len(header)]
        if len(nilai) < len(header):
            nilai += [""] * (len(header) - len(nilai))
        baris_data.append(nilai)

    if not header:
        return None
    return {
        "sumber": sumber,
        "header": header,
        "baris": baris_data,
        "meta": {"format": format_, "jumlah_baris": len(baris_data)},
    }


def baca_xlsx(path):
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - dijaga tes dependensi
        raise RuntimeError(
            "openpyxl belum terpasang. Jalankan: python -m pip install -r requirements.txt"
        ) from exc

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    hasil = []
    try:
        for ws in wb.worksheets:
            matriks = [list(r) for r in ws.iter_rows(values_only=True)]
            tabel = _tabel_dari_matriks(matriks, "{0} / {1}".format(os.path.basename(path), ws.title), "xlsx")
            if tabel:
                tabel["meta"]["sheet"] = ws.title
                hasil.append(tabel)
    finally:
        wb.close()
    return hasil


def baca_csv(path):
    with open(path, "rb") as f:
        mentah = f.read()
    teks = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            teks = mentah.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if teks is None:  # pragma: no cover - latin-1 selalu berhasil
        raise RuntimeError("CSV tidak bisa dibaca sebagai teks")

    contoh = teks[:8192]
    try:
        dialect = csv.Sniffer().sniff(contoh, delimiters=",;\t|")
        pemisah = dialect.delimiter
    except csv.Error:
        kandidat = {p: contoh.count(p) for p in ",;\t|"}
        pemisah = max(kandidat, key=kandidat.get) if max(kandidat.values()) else ","

    baris = list(csv.reader(io.StringIO(teks), delimiter=pemisah))
    tabel = _tabel_dari_matriks(baris, os.path.basename(path), "csv")
    if tabel:
        tabel["meta"]["pemisah"] = pemisah
        return [tabel]
    return []


class _ParserTabel(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tabel = []
        self._sedang_tabel = False
        self._sedang_baris = False
        self._sel = None
        self._baris = []
        self._tabel_aktif = []
        self._span = 1

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._sedang_tabel = True
            self._tabel_aktif = []
        elif self._sedang_tabel and tag == "tr":
            self._sedang_baris = True
            self._baris = []
        elif self._sedang_baris and tag in ("td", "th"):
            self._sel = []
            self._span = 1
            for k, v in attrs:
                if k == "colspan":
                    try:
                        self._span = max(1, int(v))
                    except (TypeError, ValueError):
                        self._span = 1

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._sel is not None:
            teks = " ".join("".join(self._sel).split())
            self._baris.append(teks)
            for _ in range(self._span - 1):
                self._baris.append("")
            self._sel = None
            self._span = 1
        elif tag == "tr" and self._sedang_baris:
            self._tabel_aktif.append(self._baris)
            self._sedang_baris = False
        elif tag == "table" and self._sedang_tabel:
            if self._tabel_aktif:
                self.tabel.append(self._tabel_aktif)
            self._sedang_tabel = False

    def handle_data(self, data):
        if self._sel is not None:
            self._sel.append(data)


def baca_html(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        isi = f.read()
    parser = _ParserTabel()
    parser.feed(isi)
    hasil = []
    for i, matriks in enumerate(parser.tabel, start=1):
        tabel = _tabel_dari_matriks(matriks, "{0} / tabel-{1}".format(os.path.basename(path), i), "html")
        if tabel:
            hasil.append(tabel)
    return hasil


def baca_tabel(path, jenis=None):
    """Pintu masuk utama. Kembalikan daftar tabel (bisa lebih dari satu)."""
    if jenis is None:
        from . import deteksi as _deteksi
        jenis = _deteksi.deteksi(path)["jenis"]
    if jenis == "xlsx":
        return baca_xlsx(path)
    if jenis == "csv":
        return baca_csv(path)
    if jenis == "html":
        return baca_html(path)
    raise ValueError("jenis {0!r} bukan tabel yang bisa dibaca".format(jenis))

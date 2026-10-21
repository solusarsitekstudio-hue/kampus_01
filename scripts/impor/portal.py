"""Penangkapan data portal kampus: login MANUAL, ambil tabel, simpan ke inbox.

Prinsip modul ini (mengikuti aturan sistem):

* **Tidak menyimpan kredensial.** Login dikerjakan pengguna sendiri di jendela
  browser yang terbuka; skrip hanya menunggu sampai halaman siap.
* **Tidak menembak endpoint tersembunyi.** Yang diambil adalah halaman yang
  benar-benar sedang dilihat (HTML + tabel + screenshot), lalu HTML-nya
  diperlakukan sebagai berkas mentah biasa lewat `scripts/impor`.
* **Tanpa tabel = tidak diam-diam sukses.** Kalau halaman tidak memuat tabel,
  yang disimpan hanya HTML + screenshot, dan statusnya dilaporkan
  "perlu tinjauan manusia" (OCR/manual) - bukan dikarang.

Bagian pengambilan (Playwright) hanya jalan saat dipanggil; fungsi penyimpanan
di bawah bisa diuji tanpa browser.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime

from . import sumber_tabel

PROFIL_BAWAAN = os.path.join("input", ".session", "chromium")


def simpan_tabel(tabel, folder, label, format_="csv"):
    """Tulis satu tabel hasil bacaan ke CSV atau XLSX. Kembalikan path."""
    os.makedirs(folder, exist_ok=True)
    if format_ == "csv":
        path = os.path.join(folder, label + ".csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            penulis = csv.writer(f)
            penulis.writerow(tabel["header"])
            penulis.writerows(tabel["baris"])
        return path
    if format_ == "xlsx":
        try:
            import openpyxl
        except ImportError as exc:  # pragma: no cover - dijaga tes dependensi
            raise RuntimeError(
                "openpyxl belum terpasang. Jalankan: python -m pip install -r requirements.txt"
            ) from exc
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Nilai"
        ws.append(list(tabel["header"]))
        for baris in tabel["baris"]:
            ws.append(list(baris))
        path = os.path.join(folder, label + ".xlsx")
        wb.save(path)
        wb.close()
        return path
    raise ValueError("format harus 'csv' atau 'xlsx', dapat {0!r}".format(format_))


def simpan_hasil_tangkapan(html, folder_arsip, folder_inbox, label,
                           format_="csv", screenshot=None):
    """Simpan HTML (+screenshot) lalu ekstrak tabelnya ke folder inbox.

    Kembalikan dict: path html, path tabel (bisa kosong), jumlah tabel.
    """
    os.makedirs(folder_arsip, exist_ok=True)
    os.makedirs(folder_inbox, exist_ok=True)

    html_path = os.path.join(folder_arsip, label + ".html")
    with open(html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    hasil = {
        "label": label,
        "html": html_path,
        "screenshot": None,
        "tabel": [],
        "catatan": "",
    }
    if screenshot and os.path.isfile(screenshot):
        tujuan = os.path.join(folder_arsip, label + ".png")
        if os.path.abspath(screenshot) != os.path.abspath(tujuan):
            with open(screenshot, "rb") as src, open(tujuan, "wb") as dst:
                dst.write(src.read())
        hasil["screenshot"] = tujuan

    try:
        tabel_list = sumber_tabel.baca_html(html_path)
    except Exception as exc:  # HTML aneh: laporkan, jangan tebak
        hasil["catatan"] = "gagal membaca tabel: {0}".format(exc)
        return hasil

    for i, tabel in enumerate(tabel_list, start=1):
        nama = "{0}-tabel{1:02d}".format(label, i)
        path = simpan_tabel(tabel, folder_inbox, nama, format_)
        hasil["tabel"].append({"path": path, "sumber": tabel["sumber"],
                               "baris": len(tabel["baris"]),
                               "format": format_})

    if not tabel_list:
        hasil["catatan"] = (
            "tidak ada tabel HTML di halaman ini; sisa tersimpan sebagai "
            "screenshot/HTML untuk dibaca manusia atau AI vision"
        )
    return hasil


def tangkap(url, folder_arsip, folder_inbox, jumlah_halaman=1,
            profil_dir=PROFIL_BAWAAN, format_="csv", jeda_prompt=input):
    """Buka browser (headed), tunggu login manual, ambil halaman per halaman.

    `jeda_prompt` bisa diganti di luar CLI (mis. untuk otomasi/tes).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - dijaga tes dependensi
        raise RuntimeError(
            "playwright belum terpasang. Jalankan: python -m pip install -r requirements.txt"
        ) from exc

    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    arsip = os.path.join(folder_arsip, stempel)
    os.makedirs(arsip, exist_ok=True)
    os.makedirs(profil_dir, exist_ok=True)

    hasil_semua = []
    with sync_playwright() as p:
        konteks = p.chromium.launch_persistent_context(profil_dir, headless=False)
        try:
            halaman = konteks.pages[0] if konteks.pages else konteks.new_page()
            halaman.goto(url, wait_until="domcontentloaded")
            jeda_prompt(
                "Jendela browser sudah terbuka.\n"
                "  1. Login manual dengan akun resmi (skrip tidak menyimpan sandi).\n"
                "  2. Buka halaman data/nilai yang ingin diambil.\n"
                "  3. Rapikan tampilan (muat semua baris) lalu tekan Enter di sini.\n"
            )
            for i in range(1, int(jumlah_halaman) + 1):
                label = "portal-{0}-hal{1:02d}".format(stempel, i)
                png = os.path.join(arsip, label + ".png")
                try:
                    halaman.screenshot(path=png, full_page=True)
                except Exception:
                    png = None
                hasil_semua.append(simpan_hasil_tangkapan(
                    halaman.content(), arsip, folder_inbox, label,
                    format_=format_, screenshot=png,
                ))
                if i < int(jumlah_halaman):
                    jeda_prompt(
                        "Halaman {0} tersimpan. Pindah ke halaman berikutnya "
                        "di browser, lalu tekan Enter.\n".format(i))
        finally:
            konteks.close()
    return {"stempel": stempel, "arsip": arsip, "halaman": hasil_semua}
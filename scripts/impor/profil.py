"""Profil pemetaan kolom: satu-satunya tempat yang perlu diubah saat format
portal/berkas asli ketemu.

Profil tinggal di `config/impor/*.json`:

    {
      "nama": "portal_v1",
      "kolom": {"NPM": "npm", "Nama Mahasiswa": "nama",
                "Pertemuan": "pertemuan", "Status": "status", "Nilai": "skor"},
      "status": {"H": "Hadir", "A": "Alpha"},
      "konteks": {"prodi": "Arsitektur", "tahun_ajar": "2025-2026",
                  "semester": "GENAP", "kunci_mk": "..."}
    }

Kalau tidak ada profil yang cocok, dipakai alias bawaan (kolom Indonesia yang
umum). Kalau header tetap tidak dikenali, proses BERHENTI - tidak menebak.
"""
from __future__ import annotations

import glob
import json
import os

from .kanonik import KOLOM_WAJIB, kunci_kolom

FIELD = ("npm", "nama", "pertemuan", "slot", "status", "skor", "alasan")

# Alias bawaan. Urutan penting: yang lebih spesifik lebih dulu.
ALIAS_BAWAAN = {
    "npm": (
        "npm", "nim", "nomor pokok mahasiswa", "nomor induk mahasiswa",
        "no induk mahasiswa", "nim mahasiswa", "npm mahasiswa",
    ),
    "nama": ("nama mahasiswa", "nama lengkap", "nama"),
    "pertemuan": (
        "pertemuan ke", "pertemuan", "sesi ke", "sesi", "tatap muka",
        "meeting", "p",
    ),
    "slot": ("slot absen", "slot ke", "slot", "jam ke", "jam"),
    "status": (
        "status kehadiran", "status presensi", "status", "kehadiran",
        "presensi", "keterangan",
    ),
    "skor": (
        "nilai pertemuan", "nilai akhir", "nilai", "skor", "score", "angka",
    ),
    "alasan": ("alasan", "catatan", "keterangan tambahan", "note"),
}

_PETA_ALIAS = {}
for _field, _daftar in ALIAS_BAWAAN.items():
    for _alias in _daftar:
        _PETA_ALIAS.setdefault(kunci_kolom(_alias), _field)


def muat_profil(folder) -> list:
    """Baca semua profil JSON di folder. Profil rusak = error, bukan diabaikan."""
    hasil = []
    if not folder or not os.path.isdir(folder):
        return hasil
    for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
        with open(path, "r", encoding="utf-8-sig") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as exc:
                raise ValueError("Profil {0} bukan JSON valid: {1}".format(path, exc)) from exc
        if not isinstance(data, dict) or not data.get("nama"):
            raise ValueError("Profil {0} tidak punya field 'nama'".format(path))
        data["_path"] = path
        hasil.append(data)
    return hasil


def _peta_kolom(header, profil) -> dict:
    """header index -> nama field kanonik."""
    peta_profil = {}
    for k, v in (profil or {}).get("kolom", {}).items():
        peta_profil[kunci_kolom(k)] = v
    hasil = {}
    dipakai = {}
    for i, nama in enumerate(header):
        kunci = kunci_kolom(nama)
        if not kunci:
            continue
        field = peta_profil.get(kunci) or _PETA_ALIAS.get(kunci)
        if not field:
            continue
        if field not in FIELD:
            raise ValueError(
                "Profil {0}: kolom '{1}' dipetakan ke field tak dikenal '{2}'".format(
                    (profil or {}).get("nama", "bawaan"), nama, field)
            )
        if field in dipakai:
            raise ValueError(
                "Profil {0}: field '{1}' dipetakan dua kali (kolom '{2}' dan '{3}')".format(
                    (profil or {}).get("nama", "bawaan"), field,
                    header[dipakai[field]], nama)
            )
        hasil[i] = field
        dipakai[field] = i
    return hasil


def peta_tabel(tabel, profil=None) -> dict:
    """Kembalikan {"peta": {index: field}, "hilang": [...], "profil": nama}."""
    peta = _peta_kolom(tabel["header"], profil)
    terpetakan = set(peta.values())
    wajib = list(KOLOM_WAJIB)
    for k in (profil or {}).get("deteksi", {}).get("kolom_wajib", []):
        if k not in wajib:
            wajib.append(k)
    hilang = [k for k in wajib if k not in terpetakan]
    return {
        "peta": peta,
        "hilang": hilang,
        "profil": (profil or {}).get("nama", "bawaan"),
        "terpetakan": sorted(terpetakan),
    }


def pilih_profil(tabel, profil_list) -> dict:
    """Pilih profil yang paling banyak mencocokkan header dan tidak kehilangan
    kolom wajib. Bila tidak ada yang cocok, kembalikan None (nanti dipakai
    alias bawaan). Profil eksplisit yang tidak lengkap = error, bukan diam."""
    terbaik = None
    skor_terbaik = -1
    for profil in profil_list or []:
        hasil = peta_tabel(tabel, profil)
        skor = len(hasil["peta"])
        if hasil["hilang"]:
            continue
        if skor > skor_terbaik:
            terbaik, skor_terbaik = profil, skor
    return terbaik


def petakan_baris(tabel, profil=None) -> list:
    """Ubah tabel mentah menjadi daftar dict mentah siap masuk kanonik.

    Menyertakan `_asal` (nomor baris di sumber) supaya pesan error bisa
    menunjuk baris yang salah.
    """
    hasil_peta = peta_tabel(tabel, profil)
    if hasil_peta["hilang"]:
        raise ValueError(
            "Kolom wajib tidak ditemukan: {0}. Header terbaca: {1}".format(
                ", ".join(hasil_peta["hilang"]), tabel["header"])
        )
    peta = hasil_peta["peta"]
    keluaran = []
    for nomor, baris in enumerate(tabel["baris"], start=2):
        data = {}
        for idx, field in peta.items():
            data[field] = baris[idx] if idx < len(baris) else ""
        if not any(str(v).strip() for v in data.values()):
            continue
        data["_asal"] = {"sumber": tabel["sumber"], "baris": nomor}
        keluaran.append(data)
    return keluaran


def konteks(profil=None, override=None) -> dict:
    """Gabungkan konteks dari profil dengan override CLI."""
    hasil = {}
    for sumber in ((profil or {}).get("konteks", {}) or {}, override or {}):
        for k, v in sumber.items():
            if v not in (None, ""):
                hasil[k] = v
    return hasil

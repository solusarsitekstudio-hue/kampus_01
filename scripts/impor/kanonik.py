"""Skema baris kanonik untuk subsistem impor.

SEMUA pintu masuk (Excel/CSV/HTML/portal/screenshot) WAJIB berakhir di bentuk
yang sama sebelum menyentuh tree kurikulum:

    {"npm": "2510015410010", "pertemuan": 3, "slot": 1,
     "status": "Hadir", "skor": 95, "alasan": "-"}

Berkas ini TIDAK menulis apa pun. Tugasnya cuma menormalkan dan memeriksa.
Prinsipnya fail-closed: nilai yang tidak bisa dipastikan DITOLAK dengan pesan
yang menyebut kolom/barisnya, bukan ditebak.
"""
from __future__ import annotations

import re

# Kosakata status resmi. Ini yang dibaca scripts/parse_data.py (6 keranjang:
# Hadir, Hadir Sebagian, Sakit, Izin, Alpha, Belum Diinput - yang terakhir
# adalah turunan, bukan isi berkas).
STATUS_RESMI = ("Hadir", "Hadir Sebagian", "Sakit", "Izin", "Alpha")

# Alias yang lazim muncul di portal/kertas. Kunci sudah dinormalkan oleh
# `kunci_kolom()` supaya "Hadir Sebagian", "HADIR_SEBAGIAN", "hadir sebagian"
# semuanya jatuh ke kunci yang sama.
ALIAS_STATUS = {
    "hadir": "Hadir",
    "h": "Hadir",
    "masuk": "Hadir",
    "present": "Hadir",
    "p": "Hadir",
    "hadirsebagian": "Hadir Sebagian",
    "sebagian": "Hadir Sebagian",
    "hs": "Hadir Sebagian",
    "hadir sebagian": "Hadir Sebagian",
    "sakit": "Sakit",
    "s": "Sakit",
    "skt": "Sakit",
    "izin": "Izin",
    "i": "Izin",
    "ijin": "Izin",
    "alpha": "Alpha",
    "alpa": "Alpha",
    "a": "Alpha",
    "absen": "Alpha",
    "tidak hadir": "Alpha",
    "tanpa keterangan": "Alpha",
    "th": "Alpha",
}

KOLOM_WAJIB = ("npm", "pertemuan", "status")

_ANGKA_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")
_ALIAS_TERCACHE = None


def _alias_norm():
    """Alias dengan kunci yang sudah dinormalkan (dibangun sekali)."""
    global _ALIAS_TERCACHE
    if _ALIAS_TERCACHE is None:
        _ALIAS_TERCACHE = {kunci_kolom(k): v for k, v in ALIAS_STATUS.items()}
    return _ALIAS_TERCACHE



def kunci_kolom(teks) -> str:
    """Normalkan nama kolom: 'Nilai Akhir' -> 'nilaiakhir'."""
    if teks is None:
        return ""
    t = str(teks).strip().lower()
    t = t.replace("_", " ").replace("-", " ")
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", "", t)


def bersihkan_teks(teks) -> str:
    """Rapikan spasi/newline. None -> string kosong."""
    if teks is None:
        return ""
    return re.sub(r"\s+", " ", str(teks).replace("\xa0", " ")).strip()


def normalisasi_npm(nilai) -> str:
    """NPM selalu string digit. Float dari Excel (2510015410010.0) diterima."""
    if nilai is None:
        return ""
    if isinstance(nilai, bool):
        raise ValueError("NPM tidak boleh boolean")
    if isinstance(nilai, float):
        if nilai != int(nilai):
            raise ValueError("NPM pecahan: {0!r}".format(nilai))
        return str(int(nilai))
    teks = str(nilai).strip()
    if re.fullmatch(r"\d+\.0+", teks):
        teks = teks.split(".")[0]
    teks = re.sub(r"\s+", "", teks)
    if not teks.isdigit():
        raise ValueError("NPM bukan angka: {0!r}".format(nilai))
    return teks


def ke_int(nilai, nama="nilai") -> int:
    """Konversi longgar tapi tegas: '4', '4.0', 4.0 -> 4. Selain itu error."""
    if nilai is None or (isinstance(nilai, str) and not nilai.strip()):
        raise ValueError("{0} kosong".format(nama))
    if isinstance(nilai, bool):
        raise ValueError("{0} tidak boleh boolean".format(nama))
    if isinstance(nilai, int):
        return nilai
    if isinstance(nilai, float):
        if nilai != int(nilai):
            raise ValueError("{0} pecahan: {1!r}".format(nama, nilai))
        return int(nilai)
    teks = str(nilai).strip().replace(",", ".")
    if _ANGKA_RE.match(teks):
        angka = float(teks)
        if angka != int(angka):
            raise ValueError("{0} pecahan: {1!r}".format(nama, nilai))
        return int(angka)
    raise ValueError("{0} bukan angka: {1!r}".format(nama, nilai))


def normalisasi_status(nilai, peta_tambahan=None) -> str:
    """Kembalikan salah satu STATUS_RESMI, atau raise kalau tidak dikenal."""
    teks = bersihkan_teks(nilai)
    if not teks:
        raise ValueError("status kosong")
    # Sudah bentuk resmi?
    for resmi in STATUS_RESMI:
        if teks.lower() == resmi.lower():
            return resmi
    kunci = kunci_kolom(teks)
    if peta_tambahan:
        for k, v in peta_tambahan.items():
            if kunci_kolom(k) == kunci:
                teks = v
                break
    for resmi in STATUS_RESMI:
        if kunci_kolom(teks) == kunci_kolom(resmi):
            return resmi
    alias = _alias_norm()
    if kunci in alias:
        return alias[kunci]
    raise ValueError("status tidak dikenal: {0!r}".format(nilai))


def normalisasi_skor(nilai, status=None) -> int:
    """Skor 0..100. Alpha WAJIB 0 (aturan sistem: alpha tidak dapat nilai)."""
    skor = ke_int(nilai, "skor")
    if skor < 0 or skor > 100:
        raise ValueError("skor di luar 0..100: {0}".format(skor))
    if status == "Alpha" and skor != 0:
        raise ValueError("status Alpha wajib skor 0, dapat {0}".format(skor))
    return skor


def baris_kanonik(data, peta_status=None) -> dict:
    """Bangun satu baris kanonik dari dict mentah (kunci sudah dipetakan).

    Melempar ValueError dengan pesan spesifik supaya pemanggil bisa menolak
    seluruh berkas dan menyebut baris mana yang salah.
    """
    npm = normalisasi_npm(data.get("npm"))
    if not npm:
        raise ValueError("npm kosong")
    pertemuan = ke_int(data.get("pertemuan"), "pertemuan")
    slot = ke_int(data.get("slot", 1), "slot")
    status = normalisasi_status(data.get("status"), peta_status)
    skor = normalisasi_skor(data.get("skor"), status)
    return {
        "npm": npm,
        "pertemuan": pertemuan,
        "slot": slot,
        "status": status,
        "alasan": bersihkan_teks(data.get("alasan")) or "-",
        "skor": skor,
    }


def validasi_baris(baris, *, mahasiswa=None, slot_map=None,
                   total_pertemuan=16) -> list:
    """Periksa satu baris kanonik. Kembalikan daftar masalah (kosong = valid)."""
    masalah = []
    npm = baris.get("npm")
    if not isinstance(npm, str) or not npm.isdigit():
        masalah.append("npm tidak valid: {0!r}".format(npm))
    elif mahasiswa is not None and npm not in mahasiswa:
        masalah.append("npm {0} tidak ada di mahasiswa.json".format(npm))

    p = baris.get("pertemuan")
    if not isinstance(p, int) or not (1 <= p <= total_pertemuan):
        masalah.append("pertemuan {0!r} di luar 1..{1}".format(p, total_pertemuan))
        return masalah

    slot = baris.get("slot")
    if not isinstance(slot, int) or slot < 1:
        masalah.append("slot {0!r} tidak valid".format(slot))
    elif slot_map is not None:
        maks = slot_map.get(p)
        if maks is None:
            masalah.append("pertemuan {0} tidak ada di sesi.json".format(p))
        elif slot > maks:
            masalah.append(
                "pertemuan {0} hanya punya {1} slot, dapat slot {2}".format(p, maks, slot)
            )

    if baris.get("status") not in STATUS_RESMI:
        masalah.append("status tidak resmi: {0!r}".format(baris.get("status")))

    skor = baris.get("skor")
    if not isinstance(skor, int) or not (0 <= skor <= 100):
        masalah.append("skor {0!r} di luar 0..100".format(skor))
    elif baris.get("status") == "Alpha" and skor != 0:
        masalah.append("status Alpha wajib skor 0, dapat {0}".format(skor))

    return masalah

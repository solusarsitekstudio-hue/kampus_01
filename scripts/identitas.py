"""Sumber tunggal identitas akademik: mata kuliah, dosen, asisten, ketua prodi, institusi.

KENAPA FILE INI ADA
-------------------
Dulu nama mata kuliah / dosen pengasuh / asisten / ketua prodi disalin manual di
5 tempat terpisah (parse_data.py, process_input.py, generate_pdfs.py,
video_composer.py, dan index.html) - dan nilainya ikut TERTANAM ke dalam data
turunan (35 wa_text per mahasiswa, seluruh PDF, dan video). Akibatnya mengganti
satu nama berarti memburu 5+ lokasi, dan risiko dokumen resmi bertanda tangan
dengan nama yang salah.

Sekarang hanya ada SATU tempat: config/identitas.json.

ATURAN
------
- Nilai TIDAK boleh di-hardcode lagi di skrip mana pun.
- Config rusak / tidak lengkap => fail-closed: raise, jangan menebak.
- simpan() selalu membackup ke data/_backup/ dulu, lalu tulis atomik.
"""

import json
import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "identitas.json")
BACKUP_DIR = os.path.join(BASE_DIR, "data", "_backup")

FIELD_INSTITUSI_WAJIB = ("fakultas", "prodi", "ketua_prodi", "kota")
FIELD_MK_WAJIB = (
    "kode_mk",
    "nama_mk",
    "sks",
    "kelas",
    "semester",
    "jadwal",
    "dosen_pengasuh",
    "asisten_dosen",
)

_cache = {"mtime": None, "data": None}


class IdentitasError(ValueError):
    """Config identitas hilang / rusak / tidak lolos validasi."""


def _baca_mentah():
    if not os.path.exists(CONFIG_PATH):
        raise IdentitasError(
            "File identitas tidak ditemukan: {0}\n"
            "Pulihkan dengan: git checkout config/identitas.json".format(CONFIG_PATH)
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise IdentitasError(
                "config/identitas.json rusak (JSON tidak valid) baris {0}: {1}".format(
                    exc.lineno, exc.msg
                )
            ) from exc


def muat(force=False):
    """Baca config (di-cache sampai file berubah)."""
    mtime = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else None
    if force or _cache["data"] is None or _cache["mtime"] != mtime:
        data = _baca_mentah()
        _cache["data"] = data
        _cache["mtime"] = mtime
    return _cache["data"]


def validasi(cfg):
    """Balikkan daftar pesan kesalahan. Daftar kosong = valid. (fail-closed)"""
    masalah = []
    if not isinstance(cfg, dict):
        return ["Isi config harus berupa objek JSON."]

    inst = cfg.get("institusi")
    if not isinstance(inst, dict):
        masalah.append("Bagian 'institusi' tidak ada / bukan objek.")
    else:
        for k in FIELD_INSTITUSI_WAJIB:
            if not str(inst.get(k, "")).strip():
                masalah.append("institusi.{0} tidak boleh kosong.".format(k))
        # universitas & nip_ketua_prodi OPSIONAL: dirender hanya kalau diisi.
        for k in ("universitas", "nip_ketua_prodi"):
            if not isinstance(inst.get(k, ""), str):
                masalah.append("institusi.{0} harus berupa teks.".format(k))

    dash = cfg.get("dashboard")
    if not isinstance(dash, dict):
        masalah.append("Bagian 'dashboard' tidak ada / bukan objek.")
    else:
        for k in ("judul", "subjudul", "deskripsi"):
            if not str(dash.get(k, "")).strip():
                masalah.append("dashboard.{0} tidak boleh kosong.".format(k))

    mk = cfg.get("mata_kuliah")
    if not isinstance(mk, dict) or not mk:
        masalah.append("Bagian 'mata_kuliah' kosong / bukan objek.")
        mk = {}
    for kunci, item in mk.items():
        if not isinstance(item, dict):
            masalah.append("mata_kuliah.{0} bukan objek.".format(kunci))
            continue
        for k in FIELD_MK_WAJIB:
            nilai = item.get(k)
            if k == "dosen_pengasuh":
                if not isinstance(nilai, list) or not [d for d in nilai if str(d).strip()]:
                    masalah.append(
                        "mata_kuliah.{0}.dosen_pengasuh minimal 1 nama.".format(kunci)
                    )
            elif k == "sks":
                if not isinstance(nilai, int) or nilai <= 0:
                    masalah.append(
                        "mata_kuliah.{0}.sks harus angka bulat > 0.".format(kunci)
                    )
            elif not str(nilai if nilai is not None else "").strip():
                masalah.append("mata_kuliah.{0}.{1} tidak boleh kosong.".format(kunci, k))

    aktif = cfg.get("mata_kuliah_aktif")
    if aktif not in mk:
        masalah.append(
            "mata_kuliah_aktif '{0}' tidak ada di daftar mata_kuliah.".format(aktif)
        )
    return masalah


def institusi():
    return muat().get("institusi", {})


def daftar_mk():
    """Balikkan {kunci: identitas_mk} apa adanya dari file."""
    return muat().get("mata_kuliah", {})


def mk_aktif():
    return muat().get("mata_kuliah_aktif")


def mk(kunci=None):
    """Identitas satu mata kuliah. Default: yang sedang aktif."""
    cfg = muat()
    k = kunci or cfg.get("mata_kuliah_aktif")
    item = cfg.get("mata_kuliah", {}).get(k)
    if not item:
        raise IdentitasError(
            "Mata kuliah '{0}' tidak ada di config/identitas.json".format(k)
        )
    return item


def lengkapi(kunci=None):
    """Identitas MK digabung dengan institusi -> satu dict datar siap pakai."""
    cfg = muat()
    inst = cfg.get("institusi", {})
    item = dict(mk(kunci))
    item["kunci_mk"] = kunci or cfg.get("mata_kuliah_aktif")
    item["prodi"] = inst.get("prodi", "")
    item["fakultas"] = inst.get("fakultas", "")
    item["ketua_prodi"] = inst.get("ketua_prodi", "")
    item["nip_ketua_prodi"] = inst.get("nip_ketua_prodi", "")
    item["universitas"] = inst.get("universitas", "")
    item["kota"] = inst.get("kota", "")
    item["dosen_pengasuh"] = list(item.get("dosen_pengasuh") or [])
    return item


def teks_header():
    """judul/subjudul/deskripsi dashboard, placeholder {prodi} dll sudah terisi."""
    cfg = muat()
    inst = cfg.get("institusi", {})
    peta = {
        "prodi": inst.get("prodi", ""),
        "fakultas": inst.get("fakultas", ""),
        "kaprodi": inst.get("ketua_prodi", ""),
        "universitas": inst.get("universitas", ""),
    }
    hasil = {}
    for k, v in (cfg.get("dashboard") or {}).items():
        s = str(v)
        for nama, nilai in peta.items():
            s = s.replace("{" + nama + "}", nilai)
        hasil[k] = s
    return hasil


def kop_instansi():
    """Baris kop surat: PRODI + FAKULTAS (huruf besar), plus universitas bila diisi."""
    inst = institusi()
    fakultas = str(inst.get("fakultas", "")).upper()
    prodi = str(inst.get("prodi", "")).upper()
    universitas = str(inst.get("universitas", "")).strip().upper()
    return {
        "prodi": prodi,
        "fakultas": fakultas,
        "universitas": universitas,
        "baris_prodi_fakultas": "PROGRAM STUDI {0} — FAKULTAS {1}".format(prodi, fakultas),
    }


def tanggal_tanda_tangan():
    return str(muat().get("dokumen", {}).get("tanggal_tanda_tangan", ""))


def selisih_dengan(data_course):
    """Field identitas yang sudah diubah di config tapi BELUM masuk dokumen.

    Dipakai dashboard untuk menampilkan peringatan "Tingkat 2 belum dijalankan".
    Balikkan daftar dict {field, config, dokumen}. Kosong = dokumen sudah sinkron.
    """
    if not isinstance(data_course, dict):
        return []
    kini = lengkapi()
    dipantau = (
        "nama_mk",
        "kode_mk",
        "kelas",
        "semester",
        "sks",
        "jadwal",
        "ketua_prodi",
        "dosen_pengasuh",
        "asisten_dosen",
    )
    beda = []
    for k in dipantau:
        if data_course.get(k) != kini.get(k):
            beda.append({"field": k, "config": kini.get(k), "dokumen": data_course.get(k)})
    return beda


def simpan(cfg):
    """Validasi -> backup -> tulis atomik. Raise IdentitasError kalau tidak valid."""
    masalah = validasi(cfg)
    if masalah:
        raise IdentitasError(
            "Config identitas tidak valid, tidak disimpan:\n- " + "\n- ".join(masalah)
        )
    if os.path.exists(CONFIG_PATH):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(CONFIG_PATH, os.path.join(BACKUP_DIR, "identitas.{0}.json".format(stamp)))
    else:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, CONFIG_PATH)

    _cache["data"] = None
    _cache["mtime"] = None
    return cfg

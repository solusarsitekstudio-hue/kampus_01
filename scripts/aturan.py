"""aturan.py - SATU SUMBER ATURAN AKADEMIK YANG BISA DIATUR.

KENAPA FILE INI ADA
-------------------
Dulu ambang at-risk (Alpha >= 2x ATAU kehadiran < 75%), ambang grade, dan
aturan kehadiran DIPAKU di dalam kode `scripts/kelas_rules.py`. Padahal:

  * Kepala Prodi belum menetapkan angka resminya (masih menunggu data portal),
  * tiap prodi/kampus bisa punya kebijakan berbeda,
  * mengubah satu ambang berarti ikut mengubah 3 file sekaligus.

Sekarang angkanya hidup di `config/aturan.json`. `kelas_rules.py` membacanya
dari sini, jadi mengubah kebijakan TIDAK perlu menyentuh kode sama sekali.

ATURAN MAIN
-----------
  * Config HILANG / RUSAK / tidak lengkap  -> raise AturanError (fail-closed).
  * Nilai asing (mis. tipe aturan yang tidak dikenal) -> raise.
  * ANGKA DEFAULT = angka lama. Memindahkan aturan dari kode ke config tidak
    mengubah hasil apa pun sampai angkanya benar-benar diubah.
"""

import json
import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "aturan.json")
BACKUP_DIR = os.path.join(BASE_DIR, "data", "_backup")

TIPE_AT_RISK_DIKENAL = ("alpha_min", "kehadiran_min")
BASIS_PERSEN_DIKENAL = ("slot", "pertemuan")
SATUAN_TAMPILAN_DIKENAL = ("pertemuan", "slot")

_cache = {"mtime": None, "data": None}


class AturanError(ValueError):
    """config/aturan.json hilang / rusak / tidak lolos validasi."""


def _baca_mentah():
    if not os.path.exists(CONFIG_PATH):
        raise AturanError(
            "File aturan tidak ditemukan: {0}\n"
            "Pulihkan dengan: git checkout config/aturan.json".format(CONFIG_PATH)
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise AturanError(
                "config/aturan.json rusak (JSON tidak valid) baris {0}: {1}".format(
                    exc.lineno, exc.msg
                )
            ) from exc


def muat(force=False):
    """Baca config aturan (di-cache sampai file berubah)."""
    mtime = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else None
    if force or _cache["data"] is None or _cache["mtime"] != mtime:
        data = _baca_mentah()
        masalah = validasi(data)
        if masalah:
            raise AturanError(
                "config/aturan.json tidak valid:\n- " + "\n- ".join(masalah)
            )
        _cache["data"] = data
        _cache["mtime"] = mtime
    return _cache["data"]


def validasi(cfg):
    """Balikkan daftar pesan kesalahan. Daftar kosong = valid. (fail-closed)"""
    masalah = []
    if not isinstance(cfg, dict):
        return ["Isi config harus berupa objek JSON."]

    keh = cfg.get("kehadiran")
    if not isinstance(keh, dict):
        masalah.append("Bagian 'kehadiran' tidak ada / bukan objek.")
    else:
        if keh.get("basis_persen") not in BASIS_PERSEN_DIKENAL:
            masalah.append(
                "kehadiran.basis_persen harus salah satu dari {0}.".format(
                    list(BASIS_PERSEN_DIKENAL)
                )
            )
        if keh.get("satuan_tampilan") not in SATUAN_TAMPILAN_DIKENAL:
            masalah.append(
                "kehadiran.satuan_tampilan harus salah satu dari {0}.".format(
                    list(SATUAN_TAMPILAN_DIKENAL)
                )
            )
        rasio = keh.get("min_slot_ratio_hadir")
        if not isinstance(rasio, (int, float)) or not (0 <= float(rasio) <= 1):
            masalah.append("kehadiran.min_slot_ratio_hadir harus angka 0..1.")

    ar = cfg.get("at_risk")
    if not isinstance(ar, dict):
        masalah.append("Bagian 'at_risk' tidak ada / bukan objek.")
    else:
        if not isinstance(ar.get("aktif"), bool):
            masalah.append("at_risk.aktif harus true/false.")
        daftar = ar.get("aturan")
        if not isinstance(daftar, list) or not daftar:
            masalah.append("at_risk.aturan harus daftar minimal 1 aturan.")
        else:
            for a in daftar:
                if not isinstance(a, dict):
                    masalah.append("at_risk.aturan berisi item bukan objek.")
                    continue
                if a.get("tipe") not in TIPE_AT_RISK_DIKENAL:
                    masalah.append(
                        "at_risk.aturan.tipe '{0}' tidak dikenal (pilihan: {1}).".format(
                            a.get("tipe"), list(TIPE_AT_RISK_DIKENAL)
                        )
                    )
                if not isinstance(a.get("nilai"), (int, float)):
                    masalah.append(
                        "at_risk.aturan[{0}].nilai harus angka.".format(a.get("tipe"))
                    )

    grade = cfg.get("grade")
    if not isinstance(grade, list) or not grade:
        masalah.append("Bagian 'grade' harus daftar minimal 1 ambang.")
    else:
        for i, g in enumerate(grade):
            if not isinstance(g, dict):
                masalah.append("grade[{0}] bukan objek.".format(i))
                continue
            if not str(g.get("grade", "")).strip():
                masalah.append("grade[{0}].grade tidak boleh kosong.".format(i))
            if not isinstance(g.get("min_nilai"), (int, float)):
                masalah.append("grade[{0}].min_nilai harus angka.".format(i))
            mh = g.get("min_kehadiran", None)
            if mh is not None and not isinstance(mh, (int, float)):
                masalah.append("grade[{0}].min_kehadiran harus angka atau null.".format(i))
            if not isinstance(g.get("pengali_kesiapan"), (int, float)):
                masalah.append("grade[{0}].pengali_kesiapan harus angka.".format(i))

    jam = cfg.get("jam_per_sks")
    if not isinstance(jam, dict) or not jam:
        masalah.append("Bagian 'jam_per_sks' harus objek minimal 1 jenis.")
    else:
        for jenis, menit in jam.items():
            if not isinstance(menit, (int, float)) or float(menit) <= 0:
                masalah.append("jam_per_sks.{0} harus angka > 0.".format(jenis))

    sk = cfg.get("standar_kampus")
    if not isinstance(sk, dict):
        masalah.append("Bagian 'standar_kampus' tidak ada / bukan objek.")
    else:
        pt = sk.get("pertemuan_total")
        if not isinstance(pt, int) or pt <= 0:
            masalah.append("standar_kampus.pertemuan_total harus angka bulat > 0.")
        ujian = sk.get("pertemuan_ujian")
        if not isinstance(ujian, dict) or not ujian:
            masalah.append("standar_kampus.pertemuan_ujian harus objek.")
        bobot = sk.get("bobot_template")
        if not isinstance(bobot, dict):
            masalah.append("standar_kampus.bobot_template harus objek.")
        else:
            for k in ("per_pertemuan", "uts", "uas"):
                if not isinstance(bobot.get(k), (int, float)):
                    masalah.append(
                        "standar_kampus.bobot_template.{0} harus angka.".format(k)
                    )

    return masalah


# --------------------------------------------------------------------------- #
# Akses
# --------------------------------------------------------------------------- #
def kehadiran():
    return muat().get("kehadiran", {})


def basis_persen_kehadiran():
    return kehadiran().get("basis_persen", "slot")


def min_slot_ratio_hadir():
    return float(kehadiran().get("min_slot_ratio_hadir", 0.5))


def at_risk():
    return muat().get("at_risk", {})


def at_risk_aktif():
    return bool(at_risk().get("aktif", True))


def at_risk_rules():
    return list(at_risk().get("aturan", []))


def nilai_aturan(tipe):
    """Nilai satu tipe aturan (mis. 'alpha_min' -> 2). None kalau tidak dipakai."""
    for a in at_risk_rules():
        if a.get("tipe") == tipe:
            return a.get("nilai")
    return None


def grade_bounds():
    """Daftar ambang grade, urut dari tertinggi ke terendah."""
    return sorted(
        muat().get("grade", []),
        key=lambda g: float(g.get("min_nilai", 0)),
        reverse=True,
    )


def jam_per_sks():
    return muat().get("jam_per_sks", {})


def jam_untuk(jenis_mk):
    """Menit tatap muka per SKS untuk satu jenis MK (teori/studio)."""
    return jam_per_sks().get(str(jenis_mk or "").lower())


def standar_kampus():
    return muat().get("standar_kampus", {})


def pertemuan_total():
    return int(standar_kampus().get("pertemuan_total", 16))


def pertemuan_ujian():
    return dict(standar_kampus().get("pertemuan_ujian", {}) or {})


# --------------------------------------------------------------------------- #
# Teks siap tampil (dipakai dashboard, PDF, dan metadata master)
# --------------------------------------------------------------------------- #
def teks_at_risk():
    """'Alpha >= 2x ATAU Kehadiran < 75%' - dibangun dari SATU sumber."""
    if not at_risk_aktif():
        return "Deteksi at-risk dimatikan di config/aturan.json"
    bagian = []
    a = nilai_aturan("alpha_min")
    if a is not None:
        bagian.append("Alpha >= {0:g}x".format(float(a)))
    k = nilai_aturan("kehadiran_min")
    if k is not None:
        bagian.append("Kehadiran < {0:g}%".format(float(k)))
    return " ATAU ".join(bagian) if bagian else "(tidak ada aturan at-risk)"


def ringkasan():
    """Ringkasan aturan berbentuk list baris, untuk dashboard/README."""
    baris = ["Aturan at-risk: " + teks_at_risk()]
    baris.append(
        "Kehadiran: tampilan per {0}, persen berbasis {1}, minimal {2:.0%} slot "
        "agar 1 pertemuan dihitung hadir".format(
            kehadiran().get("satuan_tampilan", "pertemuan"),
            basis_persen_kehadiran(),
            min_slot_ratio_hadir(),
        )
    )
    baris.append(
        "Jam per SKS: "
        + ", ".join("{0} {1:g} menit".format(k, float(v)) for k, v in jam_per_sks().items())
    )
    baris.append(
        "Standar kampus: {0} pertemuan, UTS ke-{1}, UAS ke-{2}".format(
            pertemuan_total(),
            pertemuan_ujian().get("uts", "-"),
            pertemuan_ujian().get("uas", "-"),
        )
    )
    return baris


def simpan(cfg):
    """Validasi -> backup -> tulis atomik. Raise AturanError kalau tidak valid."""
    masalah = validasi(cfg)
    if masalah:
        raise AturanError(
            "Config aturan tidak valid, tidak disimpan:\n- " + "\n- ".join(masalah)
        )
    if os.path.exists(CONFIG_PATH):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(CONFIG_PATH, os.path.join(BACKUP_DIR, "aturan.{0}.json".format(stamp)))
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

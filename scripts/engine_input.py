"""engine_input.py - ENGINE PEMERIKSA INPUT (data masuk tidak diproses dua kali).

KEPUTUSAN USER (2026-10-21):
* Engine cek input & output DIPISAH - modul ini sisi input; sisi output ada di
  scripts/engine_output.py.
* Kalau ada data masuk ke `input/inbox/` yang TELAH PERNAH diproses / sudah
  pernah masuk (dicocokkan lewat SHA-256, bukan nama berkas), engine menandai
  status **"duplikat"** dan menyebut kembarannya yang lama - supaya manusia
  tidak menimpa pekerjaan yang sudah dikonfirmasi.

REGISTRY: data/engine/input_registry.json -> {"versi": 1, "berkas": {
    "<sha256>": {"ukuran": int, "lokasi": [paths rel], "jenis": str,
    "pertama_dilihat": iso, "diproses_at": iso|null, "keterangan": str}}}

Semua tulis atomik (tmp + os.replace) & LF. Fail-closed: registry rusak ->
di-reset + pesan, bukan crash.
"""

import hashlib
import json
import os
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_HERE)
REG_DIR = os.path.join(BASE_DIR, "data", "engine")
REG_PATH = os.path.join(REG_DIR, "input_registry.json")
INBOX_DIR = os.path.join(BASE_DIR, "input", "inbox")
RAW_DIR = os.path.join(BASE_DIR, "input", "raw")

# Server concurrent (ThreadingMixIn) - tanpa lock, pindai() tulis registry di
# GET dan bisa saling menimpa dengan tandai_diproses() (lost update). RLock
# agar pindai -> tandai bersarang aman bila kelak dijadikan satu alur.
_LOCK = threading.RLock()


def _sha256(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _rel(path):
    return os.path.relpath(path, BASE_DIR).replace("\\", "/")


def _muat_registry():
    if not os.path.exists(REG_PATH):
        return {"versi": 1, "berkas": {}}, None
    try:
        with open(REG_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        if not isinstance(reg.get("berkas"), dict):
            raise ValueError("kunci 'berkas' bukan dict")
        return reg, None
    except Exception as e:
        return {"versi": 1, "berkas": {}}, f"registry rusak, di-reset: {e}"


def _tulis_registry(reg):
    os.makedirs(os.path.dirname(REG_PATH), exist_ok=True)
    tmp = REG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, REG_PATH)


def _get_entry(reg, sha):
    return reg.setdefault("berkas", {}).setdefault(sha, {
        "ukuran": None, "lokasi": [], "jenis": "inbox",
        "pertama_dilihat": _now(), "diproses_at": None, "keterangan": ""})


def _seed_arsip_raw(reg):
    """Bukti 'pernah masuk' dari arsip input/raw/<MK>/<stamp>/<berkas>."""
    if not os.path.isdir(RAW_DIR):
        return
    for dirpath, _dirs, files in os.walk(RAW_DIR):
        for fn in files:
            p = os.path.join(dirpath, fn)
            sha = _sha256(p)
            if not sha:
                continue
            e = reg.get("berkas", {}).get(sha) or _get_entry(reg, sha)
            e["ukuran"] = os.path.getsize(p)
            loc = _rel(p)
            if loc not in e["lokasi"]:
                e["lokasi"].append(loc)
            if e.get("jenis") == "inbox":
                e["jenis"] = "arsip_raw"


def pindai():
    """Pindai inbox + arsip: status tiap berkas = baru/duplikat/terdaftar.

    * baru      -> SHA belum pernah terlihat (kidang masuk pertama kali).
    * duplikat  -> SHA sama dengan berkas LAIN yang sudah pernah masuk/
                   diproses; detail kembarannya ikut dilaporkan.
    * terdaftar -> berkas yang sama masih ada di tempat yang sama (belum
                   dipindah/diproses).
    """
    with _LOCK:
        return _pindai_locked()


def _pindai_locked():
    reg, err = _muat_registry()
    _seed_arsip_raw(reg)

    daftar = []
    ringkasan = {"total": 0, "baru": 0, "duplikat": 0, "terdaftar": 0}
    if os.path.isdir(INBOX_DIR):
        for dirpath, _dirs, files in os.walk(INBOX_DIR):
            for fn in sorted(files):
                if fn.startswith("."):
                    continue  # dotfile (mis. .gitkeep) bukan data masuk
                p = os.path.join(dirpath, fn)
                sha = _sha256(p)
                if not sha:
                    continue
                loc = _rel(p)
                reg_lama = reg.get("berkas", {}).get(sha)
                lokasi_lain = []
                if reg_lama:
                    lokasi_lain = [l for l in reg_lama.get("lokasi", [])
                                   if l != loc]
                if reg_lama and lokasi_lain:
                    status = "duplikat"
                elif reg_lama:
                    status = "terdaftar"
                else:
                    status = "baru"
                ringkasan[status] += 1
                ringkasan["total"] += 1
                daftar.append({
                    "nama": fn,
                    "path": loc,
                    "ukuran": os.path.getsize(p),
                    "sha256": (sha[:16] + "..."),
                    "status": status,
                    "diproses_at": (reg_lama or {}).get("diproses_at"),
                    "kembar_dengan": lokasi_lain[:5],
                })
                # tandai inbox sebagai lokasi dikenal (tulis registry sekali)
                e = reg.get("berkas", {}).get(sha)
                if e is None:
                    e = _get_entry(reg, sha)
                    e["ukuran"] = os.path.getsize(p)
                    reg.setdefault("berkas", {})[sha] = e
                if loc not in e["lokasi"]:
                    e["lokasi"].append(loc)

    _tulis_registry(reg)
    return {"registry": _rel(REG_PATH), "registry_error": err,
            "ringkasan": ringkasan, "berkas": daftar, "pindai_at": _now()}


def tandai_diproses(sha, keterangan="", lokasi=None):
    """Tandai satu masukan 'sudah diproses' (dipanggil setelah impor diterima).

    sha diberikan dalam bentuk penuh (64 hex) atau awalan 16 hex yang luaran
    sama dengan tampilan pindai() - fail-closed kalau tidak dikenal.
    """
    if not sha:
        return None, "sha wajib diisi"
    with _LOCK:
        return _tandai_locked(sha, keterangan, lokasi)


def _tandai_locked(sha, keterangan, lokasi):
    reg, err = _muat_registry()
    brkas = reg.get("berkas", {})
    cocok = [k for k in brkas if k == sha or k.startswith(sha)]
    if len(cocok) != 1:
        detail = "tidak dikenal" if not cocok else \
            f"awalan ambang: {len(cocok)} kandidat"
        return None, f"sha {detail} di registry (pindai dulu)"
    e = brkas[cocok[0]]
    e["diproses_at"] = _now()
    if keterangan:
        e["keterangan"] = str(keterangan)
    if lokasi and lokasi not in e["lokasi"]:
        e["lokasi"].append(lokasi)
    _tulis_registry(reg)
    return {"sha": cocok[0], "diproses_at": e["diproses_at"],
            "keterangan": e["keterangan"]}, None


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(pindai(), indent=2, ensure_ascii=False))

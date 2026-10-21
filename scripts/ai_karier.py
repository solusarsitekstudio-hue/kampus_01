# -*- coding: utf-8 -*-
"""ai_karier.py - LAPIS B "potensi karier berbukti" (keputusan user 2026-10-21).

Engine Gemini rotary milik pengguna (7 akun, via scripts/impor/ai_engine.py)
merapikan GAYA narasi karier — bukan mengarang isi.

JAMINAN (fail-closed, urutan penting):
1. Nonaktif default: config/ai_karier.json hilang/rusak/"aktif": false ->
   fungsi mengembalikan None, UI tetap menampilkan narasi template Lapis A.
2. Hanya TOP-N karier (default 3) per mahasiswa yang dikirim — hemat kuota.
3. Prompt dikunci: model diberi BUKTI (field `bukti` Lapis A) + larangan
   menambah angka/klaim baru.
4. VERIFIKASI ANGKA: setiap angka di narasi hasil AI WAJIB muncul di bukti
   (atau adalah bilangan pembulatan 1 desimal dari skor kecocokan). Gagal =
   buang hasil AI, kembali ke template. Tidak pernah ada angka karangan.
5. Cache fail-closed: data/ai_karier_cache.json per kunci
   sha256(prodi|npm|sha bukti). Bukti berubah -> kunci baru (kompil ulang otomatis).
6. Teks AI tetap dilabel sumber "ai" di field terpisah supaya tampilan
   bisa jujur "dirapikan AI, disunting berdasarkan bukti".

Modul ini TIDAK diimport saat server start (import lazily dari server.py)
dan tidak memakai lib di luar stdlib.
"""

import hashlib
import json
import math
import os
import re
import threading
from datetime import datetime

INK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHIP_KONFIG = os.path.join(INK_ROOT, "config", "ai_karier.json")
CHIP_CACHE = os.path.join(INK_ROOT, "data", "ai_karier_cache.json")

_LOCK = threading.RLock()

_KONFIG_DEFAULT = {
    "aktif": False,          # fail-closed: file hilang = AI mati
    "max_karier": 3,         # hanya narasi karier teratas yang dirapikan AI
    "suhu": 0.2,
}

SYSTEM = (
    "Kamu penyunting gaya narasi karier mahasiswa arsitektur untuk dokumen "
    "resmi prodi. ATURAN MUTLAK: jangan menambah atau mengubah SATU PUN angka "
    "dan jangan menambah klaim kemampuan yang tidak ada di bukti yang diberikan. "
    "Tugasmu hanya: merapikan ejaan, menyambung kalimat agar enak dibaca, dan "
    "menjaga nada formal-hangat khas rapor guru. Satuan tetap persen. "
    "Jawab HANYA objek JSON sesuai skema yang diminta."
)


def muat_config():
    """Baca config/ai_karier.json. File hilang/rusak = default fail-closed."""
    cfg = dict(_KONFIG_DEFAULT)
    if not os.path.isfile(CHIP_KONFIG):
        return cfg
    try:
        with open(CHIP_KONFIG, "r", encoding="utf-8") as f:
            isi = json.load(f)
        if isinstance(isi, dict):
            cfg.update(isi)
    except (OSError, json.JSONDecodeError):
        pass
    cfg["aktif"] = bool(cfg.get("aktif"))
    try:
        cfg["max_karier"] = max(1, min(10, int(cfg.get("max_karier", 3))))
    except (TypeError, ValueError):
        cfg["max_karier"] = 3
    return cfg


def _angka_teks(teks):
    """Semua angka (int/float, termasuk %) yang muncul di teks."""
    if not isinstance(teks, str):
        return []
    return [m.group(0) for m in
            re.finditer(r"\d+(?:[\.,]\d+)?", teks)]


def _norm_angka(a):
    """85.0 / 85,0 / 85 -> '85'; 84.3 tetap '84.3'."""
    try:
        f = float(str(a).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return "{0:g}".format(f)


def verifikasi_narasi(narasi, bukti):
    """True bila SETIAP angka di narasi ada di bukti (normalisasi koma/titik,
    pembulatan 1 desimal diperbolehkan). Satu saja yang cilat = tolak."""
    izin = set()
    for b in bukti or []:
        if isinstance(b, str):
            for a in _angka_teks(b):
                n = _norm_angka(a)
                if n is not None:
                    izin.add(n)
                    # izinkan pembulatan 1 desimal (84.5 -> 85)
                    f = float(n)
                    izin.add("{0:g}".format(math.floor(f)))
                    izin.add("{0:g}".format(math.ceil(f)))
    if not izin:
        return False
    for a in _angka_teks(narasi or ""):
        if _norm_angka(a) not in izin:
            return False
    return True


def _kunci_cache(prodi, npm, identitas):
    mentah = json.dumps(
        {"prodi": prodi, "npm": npm, "identitas": identitas},
        ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(mentah).hexdigest()[:24]


def _baca_cache():
    if not os.path.isfile(CHIP_CACHE):
        return {}
    try:
        with open(CHIP_CACHE, "r", encoding="utf-8") as f:
            isi = json.load(f)
        return isi if isinstance(isi, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _tulis_cache(isi):
    tmp = CHIP_CACHE + ".tmp"
    os.makedirs(os.path.dirname(CHIP_CACHE), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(isi, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, CHIP_CACHE)


def _prompt_bukti(item):
    baris = [
        "Profil: {0}".format(item.get("profesi", "")),
        "Kecocokan: {0}%".format(item.get("kecocokan_persen")),
        "Kategori: {0}".format(item.get("kategori_kecocokan", "")),
        "Bukti wajib dipakai, tidak boleh ditambah angka: {0}".format(
            "; ".join(item.get("bukti", []))),
    ]
    return "\n".join(baris)


def rakit_identitas(matriks, max_karier):
    """Pangkas matriks jadi contoh prompt + identitas cache (top-N saja)."""
    atas = (matriks or [])[: max(1, max_karier)]
    contoh = [{
        "profesi": c.get("profesi"),
        "bukti": c.get("bukti"),
        "kecocokan_persen": c.get("kecocokan_persen"),
        "kategori_kecocokan": c.get("kategori_kecocokan"),
        "teks_sekarang": c.get("analisis_potensi"),
    } for c in atas]
    return atas, contoh


def narasi_ai(kumpulan, prodi, npm, paksa=False):
    """Return (hasil, sebab): hasil = {"items": {profesi: teks_ai}, "model":
    ..., "stempel": ..., "cache": bool} atau None + sebab (pemanggil
    tetap pakai template Lapis A).

    `kumpulan` = hasil kumpulan_portofolio(npm) -> potensi.matriks_karier_kuliah
    dengan field `bukti` dari Lapis A. Tanpa `bukti` -> None (fail-closed).
    """
    cfg = muat_config()
    if not cfg["aktif"]:
        return None, "AI nonaktif (config/ai_karier.json)"
    pot = (kumpulan or {}).get("analisis_potensi") or {}
    matriks = pot.get("matriks_karier_kuliah")
    if not matriks or not all(c.get("bukti") for c in matriks[:1]):
        return None, "matriks tanpa bukti (Lapis A belum jalan)"

    try:
        sys_mod = __import__("sys")
        if "" not in sys_mod.path and INK_ROOT not in sys_mod.path:
            sys_mod.path.insert(0, INK_ROOT)
        from scripts.impor import ai_engine
    except Exception as exc:  # noqa: BLE001
        return None, "engine Gemini tak terjangkau: {0}".format(exc)

    atas, contoh = rakit_identitas(matriks, cfg["max_karier"])
    identitas = hashlib.sha256(json.dumps(
        contoh, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    kunci = _kunci_cache(prodi, npm, identitas)

    with _LOCK:
        cache = _baca_cache()
        entri = cache.get(kunci)
        if entri and not paksa:
            rusak = any(
                not verifikasi_narasi(t, c.get("bukti"))
                for c, t in _pasang(atas, entri))
            if not rusak:
                entri["cache"] = True
                return entri, None

    prompt = (
        "Rapikan narasi karier berikut untuk mahasiswa NPM {0}. "
        "Tetap pakai nama panggilan sama, tetap formal hangat, dan SEMUA "
        "angka HARUS persis seperti di bukti - tidak boleh ada angka baru.\n\n"
        "Kembalikan JSON: {{\"narasi\": [{{\"profesi\": \"...\", \"teks\": \"...\"}}]}}\n\n"
        "DATA:\n{1}"
        .format(npm, json.dumps(contoh, ensure_ascii=False, indent=1))
    )
    try:
        hasil = ai_engine.tanya_json(prompt, system_instruction=SYSTEM,
                                     temperature=float(cfg.get("suhu", 0.2)))
    except Exception as exc:  # noqa: BLE001
        return None, "panggilan engine gagal: {0}".format(exc)

    daftar = []
    data = (hasil or {}).get("data") or {}
    if isinstance(data.get("narasi"), list):
        daftar = data["narasi"]
    dipasang = {(c.get("profesi") or ""): c for c in atas}
    items = {}
    for ent in daftar:
        prof = (ent or {}).get("profesi")
        teks = (ent or {}).get("teks")
        c = dipasang.get(prof)
        if not c or not isinstance(teks, str) or len(teks) < 20:
            continue  # item tidak dikenal/sampah -> abaikan (bukan gagal total)
        if not verifikasi_narasi(teks, c.get("bukti")):
            continue  # angka cilat -> buang item ini saja
        items[prof] = teks.strip()
    if not items:
        return None, "bankar: semua narasi AI gagal verifikasi angka"

    keluar = {
        "items": items,
        "model": hasil.get("model"),
        "stempel": datetime.now().isoformat(timespec="seconds"),
        "cache": False,
    }
    with _LOCK:
        # simpan di bawah kunci baru; salinan usang otomatis basi karena
        # identitasnya sha bukti (bukti berubah -> kunci baru).
        cache[kunci] = dict(keluar, cache=True)
        try:
            _tulis_cache(cache)
        except OSError as exc:  # cache gagal tulis bukan fatal
            keluar["cache_tulis"] = str(exc)
    return keluar, None


def _pasang(atas, entri):
    items = (entri or {}).get("items") or {}
    return [(c, items.get(c.get("profesi"))) for c in atas
            if items.get(c.get("profesi"))]


def terapkan_cache(kumpulan, prodi, npm):
    """Baca cache saja (TANPA memanggil engine, tanpa kuota) lalu tempel
    ke matriks potensi. Dipanggil server di /api/portofolio supaya UI Tab 9,
    PDF 06, dan WA otomatis sinkron dengan narasi AI yang pernah disetujui.
    Return (kumpulan, jumlah_baris_ai)."""
    cfg = muat_config()
    if not cfg["aktif"]:
        return kumpulan, 0
    pot = (kumpulan or {}).get("analisis_potensi") or {}
    matriks = pot.get("matriks_karier_kuliah")
    if not matriks or not any(c.get("bukti") for c in matriks[:1]):
        return kumpulan, 0
    atas, contoh = rakit_identitas(matriks, cfg["max_karier"])
    identitas = hashlib.sha256(json.dumps(
        contoh, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    kunci = _kunci_cache(prodi, npm, identitas)
    with _LOCK:
        entri = _baca_cache().get(kunci)
    if not entri:
        return kumpulan, 0
    # fail-closed: cache yang tidak lolos verifikasi angka diperlakukan basi
    if any(not verifikasi_narasi(t, c.get("bukti")) for c, t in _pasang(atas, entri)):
        return kumpulan, 0
    terapkan_ke_potensi(kumpulan, entri)
    return kumpulan, len(_pasang(atas, entri))


def terapkan_ke_potensi(kumpulan, hasil_ai):
    """Tempel teks AI ke matriks potensi TANPA menimpa angka. Field baru
    `analisis_sumber` menjelaskan asal teks ('ai' atau 'template')."""
    if not (hasil_ai or {}).get("items"):
        return kumpulan
    pot = kumpulan.get("analisis_potensi")
    if not pot:
        return kumpulan
    matriks = pot.get("matriks_karier_kuliah") or []
    for c in matriks:
        teks = hasil_ai["items"].get(c.get("profesi"))
        if not teks:
            continue
        if not verifikasi_narasi(teks, c.get("bukti")):
            continue  # baris tidak lolos verifikasi -> biarkan template
        c["analisis_potensi"] = teks
        c["analisis_sumber"] = "ai"
    pot["ai_narasi"] = {
        "model": hasil_ai.get("model"), "stempel": hasil_ai.get("stempel"),
        "jumlah": sum(1 for c in matriks if c.get("analisis_sumber") == "ai"),
    }
    kumpulan["potensi"] = pot
    return kumpulan

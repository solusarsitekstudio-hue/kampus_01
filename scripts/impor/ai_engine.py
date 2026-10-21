"""Jembatan ke engine Gemini rotary milik pengguna (7 akun, auto-rotary).

Engine-nya BUKAN bagian repo ini: letaknya di `E:\\WORKSHOP\\CORE_SYSTEM_ENGINE`
(atau sesuai env `EOS_GEMINI_ENGINE`). Kita memanggil fungsinya langsung karena
CLI engine tidak menerima `json_mode` maupun gambar - dua hal yang dibutuhkan
untuk analisis modul dan screenshot.

Tidak ada API key yang disimpan di sini. Key dibaca oleh engine dari lokasi
yang sudah kamu atur sendiri.
"""
from __future__ import annotations

import json
import os
import re
import sys

KANDIDAT_ENGINE = (
    os.environ.get("EOS_GEMINI_ENGINE"),
    r"E:\WORKSHOP\CORE_SYSTEM_ENGINE",
    r"E:\WORKSHOP\VIDEO_GEN_HUMAN",
)

_cache = None


def path_engine():
    for kandidat in KANDIDAT_ENGINE:
        if not kandidat:
            continue
        path = kandidat
        if os.path.isdir(path):
            path = os.path.join(path, "gemini_rotary_engine.py")
        if os.path.isfile(path):
            return path
    raise RuntimeError(
        "Engine Gemini tidak ditemukan. Set env EOS_GEMINI_ENGINE ke folder/file "
        "gemini_rotary_engine.py (kandidat: {0})".format(
            ", ".join(k for k in KANDIDAT_ENGINE if k))
    )


def muat_engine():
    global _cache
    if _cache is not None:
        return _cache
    path = path_engine()
    folder = os.path.dirname(path)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import gemini_rotary_engine as engine  # modul eksternal (lihat EXTERNAL_OK)
    _cache = engine
    return engine


def status():
    """Cek kesiapan tanpa mencetak/membocorkan key."""
    try:
        engine = muat_engine()
    except Exception as exc:
        return {"siap": False, "sebab": str(exc), "path": None, "jumlah_kunci": 0}
    try:
        kunci = engine.load_gemini_keys()
    except Exception as exc:
        return {"siap": False, "sebab": str(exc), "path": path_engine(), "jumlah_kunci": 0}
    return {
        "siap": bool(kunci),
        "sebab": "" if kunci else "tidak ada Gemini API key yang terbaca",
        "path": path_engine(),
        "jumlah_kunci": len(kunci),
    }


def _ambil_json(teks):
    """Ambil objek JSON dari balasan model (boleh dibungkus ```json)."""
    t = (teks or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    awal = t.find("{")
    akhir = t.rfind("}")
    if awal >= 0 and akhir > awal:
        return json.loads(t[awal:akhir + 1])
    raise ValueError("balasan tidak mengandung objek JSON")


def tanya_json(prompt, system_instruction=None, image_path=None,
               maks_perbaikan=2, temperature=0.2):
    """Panggil engine dan kembalikan {"data", "mentah", "model", "key_index"}.

    Kalau JSON tidak valid, dicoba perbaikan berulang dengan umpan balik.
    Kalau tetap gagal: raise ValueError yang menyertakan potongan balasan -
    pemanggil yang memutuskan mau menyimpan mentahnya atau tidak.
    """
    engine = muat_engine()
    prompt_aktif = prompt
    pesan_terakhir = ""
    for percobaan in range(maks_perbaikan + 1):
        hasil = engine.generate_text_rotary(
            prompt_aktif,
            system_instruction=system_instruction,
            json_mode=True,
            image_path=image_path,
            temperature=temperature,
        )
        teks = (hasil or {}).get("text", "")
        try:
            data = _ambil_json(teks)
        except Exception as exc:
            pesan_terakhir = str(exc)
            if percobaan >= maks_perbaikan:
                raise ValueError(
                    "JSON tidak valid setelah {0} percobaan: {1}. Potongan balasan: {2}".format(
                        percobaan + 1, pesan_terakhir, teks[:300])
                )
            prompt_aktif = (
                "Balasan sebelumnya BUKAN JSON valid ({0}). Ulangi dan balas HANYA "
                "objek JSON sesuai skema, tanpa penjelasan dan tanpa ```.\n\n"
                "Balasan sebelumnya:\n{1}\n\nPermintaan awal:\n{2}".format(
                    pesan_terakhir, teks[:1500], prompt)
            )
            continue
        return {
            "data": data,
            "mentah": teks,
            "model": (hasil or {}).get("model"),
            "key_index": (hasil or {}).get("key_index"),
            "percobaan": percobaan + 1,
        }
    raise ValueError("tidak terduga: loop selesai tanpa hasil")

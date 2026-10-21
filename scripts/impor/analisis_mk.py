"""Analisis modul/RPS dengan AI -> usulan isi sesi.json (status: tebakan).

Batas keras yang dipegang modul ini:

* AI hanya MENGUSULKAN. Tidak ada satu baris pun yang masuk tree tanpa
  persetujuan manusia lewat `terapkan()`.
* Keluaran wajib berskema. JSON rusak -> perbaikan berulang -> kalau tetap
  gagal, berhenti dan simpan mentahnya (bukan memaksakan isi).
* Setiap topik menunjuk halaman sumber. Halaman di luar jumlah halaman dokumen
  = ditolak.
* Bobot usulan (kalau ada) wajib berjumlah 100 sebelum boleh dipakai.

Bagian ini TIDAK memanggil jaringan saat diimpor; panggilan AI baru terjadi di
`analisis()`, jadi tes tetap offline.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime

from . import ai_engine

_KT = None


def _kt():
    """Impor kurikulum_tree (satu-satunya pemilik aturan penanda topik)."""
    global _KT
    if _KT is None:
        import os as _os
        import sys as _sys
        scripts = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if scripts not in _sys.path:
            _sys.path.insert(0, scripts)
        import kurikulum_tree as KT
        _KT = KT
    return _KT


SKEMA = {
    "identitas": {"nama_mk": "string|null", "kode_mk": "string|null",
                  "sks": "integer|null", "semester": "string|null"},
    "cpmk": [{"kode": "string", "rumusan": "string", "halaman": ["integer"]}],
    "pertemuan": [{"p": "integer 1..16", "topik": "string", "deskripsi": "string|null",
                   "bobot_usulan": "number|null", "halaman": ["integer"]}],
    "referensi": ["string"],
    "catatan": "string",
}

SYSTEM = """Kamu asisten kurikulum program studi arsitektur. Tugasmu MEMBACA dokumen
modul/RPS dan mengeluarkan data terstruktur. Kamu BUKAN pengarang: jangan menambah
materi yang tidak ada di dokumen.

Balas HANYA objek JSON dengan skema:
{
  "identitas": {"nama_mk": string|null, "kode_mk": string|null, "sks": int|null, "semester": string|null},
  "cpmk": [{"kode": string, "rumusan": string, "halaman": [int]}],
  "pertemuan": [{"p": int, "topik": string, "deskripsi": string|null, "bobot_usulan": number|null, "halaman": [int]}],
  "referensi": [string],
  "catatan": string
}

ATURAN WAJIB:
1. Nomor pertemuan 1..16. Kalau dokumen tidak memuat suatu pertemuan, JANGAN
   dikarang - lewati saja dan sebutkan di "catatan".
2. "halaman" HARUS nomor halaman yang benar-benar ada di dokumen (ditandai
   "[halaman N]" pada teks masukan). Kalau tidak yakin, kirim [].
3. "bobot_usulan" hanya diisi bila dokumen menyebut angka bobot/penilaian.
4. Jangan menyalin teks placeholder seperti "(belum diisi)".
5. "catatan" diisi kejujuran: bagian mana yang tidak terbaca/tidak ada.
"""


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for potongan in iter(lambda: f.read(1024 * 1024), b""):
            h.update(potongan)
    return h.hexdigest()


def _prompt_potongan(potongan, konteks, petunjuk):
    return (
        "Konteks: prodi {prodi}, tahun ajar {ta}, semester {sem}. "
        "Dokumen ini adalah modul/RPS mata kuliah.\n"
        "Ambil hanya pertemuan yang benar-benar tertulis di potongan halaman "
        "{awal}-{akhir} berikut.\n\n"
        "{petunjuk}\n\n"
        "--- ISI DOKUMEN ---\n{teks}\n--- SELESAI ---\n\n"
        "Balas JSON sesuai skema."
    ).format(
        prodi=konteks.get("prodi", "-"), ta=konteks.get("tahun_ajar", "-"),
        sem=konteks.get("semester", "-"),
        awal=potongan.get("halaman_awal"), akhir=potongan.get("halaman_akhir"),
        petunjuk=petunjuk, teks=potongan.get("teks", ""),
    )


def petunjuk_dari_profil(profil_modul):
    if not profil_modul:
        return ""
    penanda = profil_modul.get("penanda") or {}
    if not penanda:
        return ""
    baris = ["Penanda yang biasa dipakai dokumen ini:"]
    for nama, daftar in penanda.items():
        baris.append("- {0}: {1}".format(nama, ", ".join(daftar)))
    return "\n".join(baris)


def _gabung(hasil_list):
    identitas = {}
    cpmk = {}
    pertemuan = {}
    referensi = []
    catatan = []

    for data in hasil_list:
        for k, v in (data.get("identitas") or {}).items():
            if v not in (None, "", 0) and identitas.get(k) in (None, "", 0):
                identitas[k] = v
        for c in data.get("cpmk") or []:
            if not isinstance(c, dict):
                continue
            kunci = (c.get("kode") or c.get("rumusan") or "").strip()[:100]
            if kunci and kunci not in cpmk:
                cpmk[kunci] = c
        for p in data.get("pertemuan") or []:
            if not isinstance(p, dict):
                continue
            nomor = p.get("p")
            if not isinstance(nomor, int) or not (1 <= nomor <= 16):
                continue
            lama = pertemuan.get(nomor)
            if lama is None or (not str(lama.get("topik") or "").strip()
                                and str(p.get("topik") or "").strip()):
                pertemuan[nomor] = p
        for r in data.get("referensi") or []:
            if isinstance(r, str) and r.strip() and r not in referensi:
                referensi.append(r.strip())
        if data.get("catatan"):
            catatan.append(str(data["catatan"]).strip())

    return {
        "identitas": identitas,
        "cpmk": list(cpmk.values()),
        "pertemuan": [pertemuan[k] for k in sorted(pertemuan)],
        "referensi": referensi,
        "catatan": " | ".join(c for c in catatan if c)[:2000],
    }


def validasi_usulan(usulan, jumlah_halaman=0, total_pertemuan=16):
    """Periksa usulan sebelum ditampilkan/diterapkan. Kosong = valid."""
    masalah = []
    pertemuan = usulan.get("pertemuan")
    if not isinstance(pertemuan, list) or not pertemuan:
        return ["tidak ada pertemuan yang berhasil diekstrak"]

    nomor = []
    bobot_ada = []
    terverifikasi = _kt().topik_terverifikasi
    for p in pertemuan:
        n = p.get("p")
        if not isinstance(n, int) or not (1 <= n <= total_pertemuan):
            masalah.append("nomor pertemuan tidak valid: {0!r}".format(n))
            continue
        nomor.append(n)
        topik = str(p.get("topik") or "").strip()
        if not topik:
            masalah.append("pertemuan {0}: topik kosong".format(n))
        elif not terverifikasi(topik):
            masalah.append("pertemuan {0}: topik masih placeholder".format(n))
        bobot = p.get("bobot_usulan")
        if bobot is not None:
            if not isinstance(bobot, (int, float)) or bobot < 0:
                masalah.append("pertemuan {0}: bobot tidak valid".format(n))
            else:
                bobot_ada.append((n, float(bobot)))
        for h in p.get("halaman") or []:
            if not isinstance(h, int) or (jumlah_halaman and not (1 <= h <= jumlah_halaman)):
                masalah.append("pertemuan {0}: halaman {1!r} di luar dokumen".format(n, h))

    if len(nomor) != len(set(nomor)):
        masalah.append("nomor pertemuan ganda")
    if len(set(nomor)) != total_pertemuan:
        masalah.append("pertemuan terkumpul {0}, seharusnya {1}".format(
            len(set(nomor)), total_pertemuan))
    if bobot_ada:
        total = round(sum(b for _, b in bobot_ada), 2)
        if abs(total - 100) > 0.01:
            masalah.append("total bobot usulan {0}, seharusnya 100 (atau kosongkan)".format(total))

    for c in usulan.get("cpmk") or []:
        if not str(c.get("rumusan") or "").strip():
            masalah.append("CPMK tanpa rumusan")

    return masalah


def analisis(hasil_dokumen, konteks=None, profil_modul=None, gambar=None,
             maks_potongan=None):
    """Dokumen -> usulan terstruktur (belum ditulis ke tree).

    `gambar` = path screenshot/foto halaman (dipakai bila OCR/vision).
    """
    konteks = konteks or {}
    petunjuk = petunjuk_dari_profil(profil_modul)
    hasil_ai = []

    if gambar:
        prompt = (
            "Gambar ini adalah screenshot/foto halaman portal atau modul. "
            "Bacalah tabel/teks yang terlihat, lalu ubah menjadi JSON sesuai skema. "
            "Kalau ada bagian yang tidak terbaca, tulis di 'catatan' dan JANGAN menebak.\n\n"
            "{0}\n\nBalas JSON sesuai skema."
        ).format(petunjuk)
        keluaran = ai_engine.tanya_json(prompt, system_instruction=SYSTEM, image_path=gambar)
        hasil_ai.append(keluaran)
    else:
        potongan = _potongan_dari(hasil_dokumen, maks_potongan)
        if not potongan:
            raise ValueError("dokumen tidak punya teks yang bisa dianalisis")
        for bagian in potongan:
            prompt = _prompt_potongan(bagian, konteks, petunjuk)
            hasil_ai.append(ai_engine.tanya_json(prompt, system_instruction=SYSTEM))

    gabungan = _gabung([h["data"] for h in hasil_ai])
    jumlah_halaman = int((hasil_dokumen or {}).get("meta", {}).get("jumlah_halaman") or 0)
    masalah = validasi_usulan(gabungan, jumlah_halaman=jumlah_halaman)

    return {
        "versi": 1,
        "jenis": "usulan_sesi",
        "dibuat": datetime.now().isoformat(timespec="seconds"),
        "konteks": konteks,
        "sumber": {
            "berkas": (hasil_dokumen or {}).get("berkas"),
            "jenis": (hasil_dokumen or {}).get("jenis"),
            "jumlah_halaman": jumlah_halaman,
            "sha256": (hasil_dokumen or {}).get("sha256"),
            "ocr": bool((hasil_dokumen or {}).get("ocr_dibutuhkan")),
            "potongan": len(hasil_ai),
            "model": [h.get("model") for h in hasil_ai],
            "key_index": [h.get("key_index") for h in hasil_ai],
        },
        "status": "tebakan",
        "identitas": gabungan["identitas"],
        "cpmk": gabungan["cpmk"],
        "pertemuan": gabungan["pertemuan"],
        "referensi": gabungan["referensi"],
        "catatan_ai": gabungan["catatan"],
        "masalah": masalah,
    }


def _potongan_dari(hasil_dokumen, maks_potongan=None):
    from . import dokumen as dokumen_modul
    halaman = (hasil_dokumen or {}).get("halaman") or []
    if not halaman:
        return []
    potongan = dokumen_modul.potongan(halaman)
    if maks_potongan:
        potongan = potongan[:maks_potongan]
    return potongan


def tulis_staging(usulan, staging_root):
    from .nilai_impor import tulis_json_atomik
    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    kunci = str((usulan.get("konteks") or {}).get("kunci_mk") or "MODUL").replace("/", "_")
    label = re.sub(r"[^A-Za-z0-9_-]+", "_", str((usulan.get("sumber") or {}).get("berkas") or "modul"))[:40]
    folder = os.path.join(staging_root, "{0}_usul_sesi_{1}_{2}".format(stempel, kunci, label))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "usulan_sesi.json")
    tulis_json_atomik(path, usulan)
    return path


def muat_usulan(path):
    if os.path.isdir(path):
        path = os.path.join(path, "usulan_sesi.json")
    if not os.path.isfile(path):
        raise FileNotFoundError("Usulan sesi tidak ditemukan: {0}".format(path))
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f), path


def terapkan(usulan, folder_mk, backup_root, ikut_bobot=False):
    """Tulis topik/deskripsi (dan opsional bobot) ke sesi.json.

    Menolak kalau usulan bermasalah, kalau folder bukan MK yang sama, atau
    kalau bobot hasil perubahan tidak berjumlah 100.
    """
    if usulan.get("masalah"):
        raise ValueError(
            "Usulan masih punya {0} masalah; perbaiki dulu.".format(len(usulan["masalah"])))

    path_sesi = os.path.join(folder_mk, "sesi.json")
    if not os.path.isfile(path_sesi):
        raise FileNotFoundError("sesi.json tidak ditemukan: {0}".format(path_sesi))
    with open(path_sesi, "r", encoding="utf-8-sig") as f:
        dokumen = json.load(f)

    kunci = dokumen.get("kunci_mk")
    kunci_usulan = (usulan.get("konteks") or {}).get("kunci_mk")
    if kunci and kunci_usulan and kunci != kunci_usulan:
        raise ValueError(
            "Usulan untuk MK '{0}', folder ini MK '{1}'".format(kunci_usulan, kunci))

    peta = {p["p"]: p for p in usulan.get("pertemuan") or []}
    berubah = 0
    KT = _kt()
    for sesi in dokumen.get("sesi") or []:
        p = sesi.get("pertemuan")
        usul = peta.get(p)
        if not usul:
            continue
        topik = str(usul.get("topik") or "").strip()
        if topik and topik != sesi.get("topik"):
            sesi["topik"] = topik
            sesi["topik_terverifikasi"] = bool(KT.topik_terverifikasi(topik))
            berubah += 1
        deskripsi = usul.get("deskripsi")
        if isinstance(deskripsi, str) and deskripsi.strip() and deskripsi.strip() != sesi.get("deskripsi"):
            sesi["deskripsi"] = deskripsi.strip()
        if ikut_bobot and usul.get("bobot_usulan") is not None:
            sesi["bobot"] = usul["bobot_usulan"]

    if ikut_bobot:
        total = round(sum(float(s.get("bobot") or 0) for s in dokumen.get("sesi") or []), 2)
        if abs(total - 100) > 0.01:
            raise ValueError(
                "Bobot usulan membuat total {0} (harus 100). Pakai tanpa --bobot, "
                "atau perbaiki usulan.".format(total))

    # Hitung ulang ringkasan header supaya tidak drift.
    sesi_list = dokumen.get("sesi") or []
    dokumen["topik_terisi"] = sum(1 for s in sesi_list if s.get("topik_terverifikasi"))
    dokumen["topik_placeholder"] = len(sesi_list) - dokumen["topik_terisi"]

    masalah = KT.validasi_sesi(dokumen, kunci or "")
    if masalah:
        raise ValueError("Sesi hasil suntingan tidak valid: " + "; ".join(masalah))

    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder_backup = os.path.join(backup_root, "impor_sesi_{0}".format(stempel))
    os.makedirs(folder_backup, exist_ok=True)
    with open(path_sesi, "rb") as f:
        isi = f.read()
    with open(os.path.join(folder_backup, "sesi.json"), "wb") as f:
        f.write(isi)
    with open(os.path.join(folder_backup, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({
            "waktu": datetime.now().isoformat(timespec="seconds"),
            "sumber": usulan.get("sumber", {}),
            "ikut_bobot": bool(ikut_bobot),
            "pertemuan_diubah": berubah,
            "sha256_lama": hashlib.sha256(isi).hexdigest(),
        }, f, indent=2, ensure_ascii=False)
        f.write("\n")

    from .nilai_impor import tulis_json_atomik
    tulis_json_atomik(path_sesi, dokumen)
    return {"path": path_sesi, "pertemuan_diubah": berubah, "backup": folder_backup}

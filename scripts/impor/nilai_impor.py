"""Nilai impor: baris kanonik -> staging -> (setelah disetujui) tree.

Alurnya sengaja dua langkah:

    bangun_usulan()  -> menulis data/_staging/... (TIDAK menyentuh tree)
    terapkan()       -> backup dulu, baru menulis nilai.json

`terapkan()` hanya boleh dipanggil setelah manusia melihat hasil `bandingkan()`.
Tidak ada jalur yang menulis langsung dari berkas mentah ke tree.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime

from . import kanonik, profil as profil_modul, sumber_tabel

VERSI = 1
CATATAN_IMPOR = (
    "NILAI HASIL IMPOR (bukan sintetis). Sumber asli diarsipkan di input/raw/ "
    "dan usulan/diff-nya di data/_staging/. Berkas ini ditulis oleh "
    "scripts/impor/nilai_impor.py setelah disetujui manusia."
)


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for potongan in iter(lambda: f.read(1024 * 1024), b""):
            h.update(potongan)
    return h.hexdigest()


def baca_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def tulis_json_atomik(path, payload):
    """Tulis JSON dengan LF eksplisit + os.replace (pola yang sama dengan tree)."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def baca_sesi(folder_mk):
    path = os.path.join(folder_mk, "sesi.json")
    if not os.path.isfile(path):
        raise FileNotFoundError("sesi.json tidak ditemukan di {0}".format(folder_mk))
    dokumen = baca_json(path)
    sesi = dokumen.get("sesi")
    if not isinstance(sesi, list) or not sesi:
        raise ValueError("sesi.json tidak punya daftar 'sesi': {0}".format(path))
    slot_map = {}
    for s in sesi:
        p = s.get("pertemuan")
        slots = s.get("slot_absen") or []
        if isinstance(p, int):
            slot_map[p] = len(slots)
    return dokumen, slot_map, len(sesi)


def baca_mahasiswa(path):
    if not os.path.isfile(path):
        raise FileNotFoundError("mahasiswa.json tidak ditemukan: {0}".format(path))
    dokumen = baca_json(path)
    daftar = dokumen.get("mahasiswa") or []
    nama = {}
    for m in daftar:
        npm = str(m.get("npm", "")).strip()
        if npm:
            nama[npm] = m.get("nama", "")
    if not nama:
        raise ValueError("mahasiswa.json tidak berisi satu pun NPM: {0}".format(path))
    return set(nama), nama


def _kunci_baris(baris):
    return (baris["npm"], int(baris["pertemuan"]), int(baris["slot"]))


def proses_tabel(tabel, profil=None, *, mahasiswa, slot_map,
                 total_pertemuan=16, peta_status=None):
    """Satu tabel -> (baris_kanonik, masalah). Tidak melempar untuk baris jelek;
    masalah dikumpulkan supaya bisa dilaporkan sekaligus."""
    baris_kanonik = []
    masalah = []
    pasangan = profil_modul.petakan_baris(tabel, profil)
    for mentah in pasangan:
        asal = mentah.get("_asal", {})
        try:
            baris = kanonik.baris_kanonik(mentah, peta_status)
        except ValueError as exc:
            masalah.append("{0} baris {1}: {2}".format(
                asal.get("sumber", "?"), asal.get("baris", "?"), exc))
            continue
        for m in kanonik.validasi_baris(
            baris, mahasiswa=mahasiswa, slot_map=slot_map,
            total_pertemuan=total_pertemuan,
        ):
            masalah.append("{0} baris {1}: {2}".format(
                asal.get("sumber", "?"), asal.get("baris", "?"), m))
        baris["_asal"] = asal
        baris_kanonik.append(baris)
    return baris_kanonik, masalah


def _ringkas(baris):
    hitung = {s: 0 for s in kanonik.STATUS_RESMI}
    for b in baris:
        hitung[b["status"]] = hitung.get(b["status"], 0) + 1
    return {
        "baris": len(baris),
        "npm_unik": len({b["npm"] for b in baris}),
        "pertemuan": sorted({b["pertemuan"] for b in baris}),
        "status": hitung,
        "skor_min": min((b["skor"] for b in baris), default=None),
        "skor_maks": max((b["skor"] for b in baris), default=None),
    }


def _cek_ganda(baris):
    """Kunci (npm, pertemuan, slot) ganda = sumber tidak konsisten -> error."""
    terlihat = {}
    for b in baris:
        k = _kunci_baris(b)
        if k in terlihat:
            nilai_lama = terlihat[k]
            if (nilai_lama["status"], nilai_lama["skor"]) != (b["status"], b["skor"]):
                raise ValueError(
                    "Baris ganda bertentangan untuk npm {0} pertemuan {1} slot {2}: "
                    "{3}/{4} vs {5}/{6}".format(
                        k[0], k[1], k[2],
                        nilai_lama["status"], nilai_lama["skor"], b["status"], b["skor"])
                )
            continue
        terlihat[k] = b
    return list(terlihat.values())


def bandingkan(baris_baru, dokumen_lama):
    """Ringkas beda terhadap nilai.json yang ada (tanpa menulis apa pun)."""
    lama = {}
    for b in (dokumen_lama or {}).get("nilai", []):
        try:
            lama[_kunci_baris(b)] = b
        except (KeyError, TypeError, ValueError):
            continue

    baru = {_kunci_baris(b): b for b in baris_baru}
    sama = berubah = 0
    contoh = []
    for k, b in baru.items():
        if k not in lama:
            continue
        o = lama[k]
        if (o.get("status"), o.get("skor")) == (b["status"], b["skor"]):
            sama += 1
        else:
            berubah += 1
            if len(contoh) < 10:
                contoh.append({
                    "npm": k[0], "pertemuan": k[1], "slot": k[2],
                    "lama": {"status": o.get("status"), "skor": o.get("skor")},
                    "baru": {"status": b["status"], "skor": b["skor"]},
                })
    hanya_di_lama = sorted(set(lama) - set(baru))
    return {
        "baru": len(set(baru) - set(lama)),
        "berubah": berubah,
        "sama": sama,
        "hanya_di_data_lama": len(hanya_di_lama),
        "contoh_perubahan": contoh,
        "contoh_hanya_lama": [
            {"npm": k[0], "pertemuan": k[1], "slot": k[2]} for k in hanya_di_lama[:10]
        ],
    }


def bangun_usulan(berkas_tabel, *, folder_mk, folder_mahasiswa, profil_list=None,
                  peta_status=None, sumber_meta=None):
    """Proses satu/lebih berkas tabel menjadi dokumen usulan (belum menulis)."""
    dok_sesi, slot_map, total = baca_sesi(folder_mk)
    mahasiswa, nama = baca_mahasiswa(folder_mahasiswa)

    semua_baris = []
    semua_masalah = []
    sumber = []
    profil_dipakai = set()
    for path, jenis in berkas_tabel:
        for tabel in sumber_tabel.baca_tabel(path, jenis):
            profil = profil_modul.pilih_profil(tabel, profil_list)
            if profil is None:
                # Coba alias bawaan sebelum menyerah.
                uji = profil_modul.peta_tabel(tabel, None)
                if uji["hilang"]:
                    semua_masalah.append(
                        "{0}: tidak ada profil yang cocok dan kolom wajib tidak "
                        "lengkap (hilang: {1})".format(tabel["sumber"], ", ".join(uji["hilang"])))
                    continue
                profil_dipakai.add("bawaan")
            else:
                profil_dipakai.add(profil.get("nama"))
            baris, masalah = proses_tabel(
                tabel, profil, mahasiswa=mahasiswa, slot_map=slot_map,
                total_pertemuan=total,
                peta_status=peta_status or (profil or {}).get("status"),
            )
            semua_baris.extend(baris)
            semua_masalah.extend(masalah)
            sumber.append({
                "berkas": os.path.basename(path),
                "jenis": jenis,
                "tabel": tabel["sumber"],
                "baris": len(baris),
            })

    if not semua_baris:
        semua_masalah.append("tidak ada satu pun baris nilai yang bisa dibaca")

    unik = []
    if semua_baris:
        try:
            unik = _cek_ganda(semua_baris)
        except ValueError as exc:
            semua_masalah.append(str(exc))

    for b in unik:
        b.pop("_asal", None)

    usulan = {
        "versi": VERSI,
        "jenis": "usulan_nilai",
        "dibuat": datetime.now().isoformat(timespec="seconds"),
        "folder_mk": os.path.abspath(folder_mk),
        "kunci_mk": dok_sesi.get("kunci_mk"),
        "tahun_ajar": dok_sesi.get("tahun_ajar"),
        "semester": dok_sesi.get("semester"),
        "profil": sorted(profil_dipakai),
        "sumber": sumber + list(sumber_meta or []),
        "ringkasan": _ringkas(unik),
        "masalah": semua_masalah,
        "baris": sorted(unik, key=_kunci_baris),
    }
    usulan["beda"] = bandingkan(usulan["baris"], baca_nilai_aman(folder_mk))
    return usulan


def baca_nilai_aman(folder_mk):
    path = os.path.join(folder_mk, "nilai.json")
    if not os.path.isfile(path):
        return {"nilai": []}
    try:
        return baca_json(path)
    except (json.JSONDecodeError, OSError):
        return {"nilai": []}


def tulis_staging(usulan, staging_root, label="impor_nilai"):
    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    kunci = (usulan.get("kunci_mk") or "MK").replace("/", "_")
    folder = os.path.join(staging_root, "{0}_{1}_{2}".format(stempel, label, kunci))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "usulan_nilai.json")
    tulis_json_atomik(path, usulan)
    return path


def muat_usulan(path):
    if os.path.isdir(path):
        path = os.path.join(path, "usulan_nilai.json")
    if not os.path.isfile(path):
        raise FileNotFoundError("Usulan tidak ditemukan: {0}".format(path))
    return baca_json(path), path


def terapkan(usulan, folder_mk, backup_root, mode="gabung", paksa=False):
    """Tulis usulan ke tree. `mode`:
    - "gabung" (bawaan): baris lama dipertahankan, hanya kunci yang diimpor diubah
    - "ganti"          : isi nilai.json diganti seluruhnya oleh baris impor

    `paksa=False` menolak menimpa nilai.json yang BUKAN sintetis dan BUKAN hasil
    impor sebelumnya (mis. sudah diverifikasi manusia). Impor ulang berkas yang
    sama tetap boleh karena berkas tulisannya ditandai `dari_impor: true`.
    """
    if mode not in ("gabung", "ganti"):
        raise ValueError("mode harus 'gabung' atau 'ganti', dapat {0!r}".format(mode))
    if usulan.get("masalah"):
        raise ValueError(
            "Usulan masih punya {0} masalah; perbaiki dulu (lihat 'masalah').".format(
                len(usulan["masalah"])))
    if not usulan.get("baris"):
        raise ValueError("Usulan tidak berisi baris nilai")

    path_nilai = os.path.join(folder_mk, "nilai.json")
    lama = baca_nilai_aman(folder_mk)
    if lama.get("nilai"):
        if lama.get("sintetis") is not True and lama.get("dari_impor") is not True and not paksa:
            raise ValueError(
                "nilai.json ini bukan data sintetis dan bukan hasil impor "
                "(sintetis={0!r}). Kalau memang ingin menimpanya, ulangi dengan "
                "--paksa setelah membackup manual.".format(lama.get("sintetis")))

    if mode == "ganti":
        gabungan = sorted(usulan["baris"], key=_kunci_baris)
    else:
        peta_baru = {_kunci_baris(b): b for b in usulan["baris"]}
        gabungan = []
        terpakai = set()
        for b in lama.get("nilai", []):
            k = _kunci_baris(b)
            if k in peta_baru:
                baru = peta_baru[k]
                gabungan.append({
                    "npm": k[0], "pertemuan": k[1], "slot": k[2],
                    "status": baru["status"], "alasan": baru.get("alasan", "-"),
                    "skor": baru["skor"],
                })
                terpakai.add(k)
            else:
                gabungan.append(b)
        sisa = [b for k, b in peta_baru.items() if k not in terpakai]
        for b in sorted(sisa, key=_kunci_baris):
            gabungan.append({
                "npm": b["npm"], "pertemuan": b["pertemuan"], "slot": b["slot"],
                "status": b["status"], "alasan": b.get("alasan", "-"), "skor": b["skor"],
            })

    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    if os.path.isfile(path_nilai):
        folder_backup = os.path.join(backup_root, "impor_nilai_{0}".format(stempel))
        os.makedirs(folder_backup, exist_ok=True)
        with open(path_nilai, "rb") as f:
            isi = f.read()
        with open(os.path.join(folder_backup, "nilai.json"), "wb") as f:
            f.write(isi)
        with open(os.path.join(folder_backup, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({
                "waktu": datetime.now().isoformat(timespec="seconds"),
                "mode": mode,
                "sumber": usulan.get("sumber", []),
                "sha256_lama": hashlib.sha256(isi).hexdigest(),
                "jumlah_baris_lama": len(lama.get("nilai", [])),
                "jumlah_baris_baru": len(gabungan),
            }, f, indent=2, ensure_ascii=False)
            f.write("\n")

    dokumen = {
        "versi": lama.get("versi", VERSI),
        "kunci_mk": lama.get("kunci_mk") or usulan.get("kunci_mk"),
        "tahun_ajar": lama.get("tahun_ajar") or usulan.get("tahun_ajar"),
        "semester": lama.get("semester") or usulan.get("semester"),
        "catatan": CATATAN_IMPOR,
        "sintetis": False,
        "dari_impor": True,
        "nilai": gabungan,
    }
    tulis_json_atomik(path_nilai, dokumen)
    return {
        "path": path_nilai,
        "mode": mode,
        "jumlah_baris": len(gabungan),
        "sha256_baru": sha256(path_nilai),
    }

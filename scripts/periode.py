"""periode.py - agregasi laporan per-periode dari tree kurikulum.

Latar belakang: dulu dashboard hanya punya master flat 1 MK
(data/academic_data.json), jadi tidak ada data untuk laporan "per semester
semua MK" atau "semua semester semua MK". Semua agregasi di sini membaca
TREE langsung (data/kurikulum/<prodi>/<TA>/<SEM>/<MK>/) supaya tidak bisa
tertinggal di belakang master.

Aturan yang diikuti (Batch B - BELUM-DIINPUT-KEHADIRAN):
  * Pertemuan yang datanya belum lengkap TIDAK ikut menekan persen
    kehadiran (keluar dari penyebut) dan tidak mengangkat ambang.
  * Kehadiran yang belum bisa dihitung sama sekali = None (netral),
    bukan 0% yang salah menuduh mahasiswa.
  * At-risk dihitung PER MK (keputusan user 2026-10-21), aturannya dari
    SATU sumber config/aturan.json lewat kelas_rules.

Keputusan user 2026-10-21 (poin 2): hasil dihitung dari TREE, cepat via
cache per MK, dan tanda mtime membuat cache usang sendiri setiap berkas
disimpan - tidak ada tombol "ilangkan cache".
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aturan as AT  # noqa: E402
import kelas_rules as KR  # noqa: E402
import kurikulum_tree as KT  # noqa: E402

# "Tanpa Tanggal": pertemuan tanpa tanggal (placeholder) tampil sebagai grup
# terpisah, bukan ikut bersama bulan yang salah (keputusan user poin 1).
GRUP_TANPA_TANGGAL = "-"

# Cache per MK: {(prodi, ta, sem, kunci): (tanda_mtime, rekap)}. Tanda mengikuti
# mtime terbesar penawaran/sesi/nilai MK itu; berkas berganti -> rekap diulang.
_REKAP_CACHE = {}


def kosongkan_cache():
    """Belt-and-braces; pemanggilan normal tidak butuh karena tanda mtime."""
    _REKAP_CACHE.clear()


def _bulan_dari_tanggal(tanggal):
    """'2025-08-15' -> '2025-08'. None/bentuk aneh -> None (jangan ditebak)."""
    if not tanggal or not isinstance(tanggal, str):
        return None
    parts = tanggal.strip().split("-")
    if len(parts) >= 2 and len(parts[0]) == 4 and len(parts[1]) >= 2:
        return "{0}-{1}".format(parts[0], parts[1][:2])
    return None


def _tanda_mk(prodi, ta, sem, kunci):
    """Tanda cache: mtime terbesar dari 3 berkas MK itu. -1 kalau kosong."""
    folder = KT.path_mk(prodi, ta, sem, kunci)
    tanda = -1.0
    for nama in KT.PATH_BERKAS:
        path = os.path.join(folder, nama)
        if os.path.exists(path):
            tanda = max(tanda, os.path.getmtime(path))
    return tanda


# ----------------------------------------------------------------------------- #
# Basis per pertemuan: matriks (npm, pertemuan) dari nilai.json satu MK.
# ----------------------------------------------------------------------------- #
def _matriks_nilai(baris_nilai):
    """{npm: {pertemuan: [baris slot]}} - sumber semua agregat."""
    per_npm = defaultdict(lambda: defaultdict(list))
    for r in (baris_nilai or []):
        npm = str(r.get("npm") or "")
        if not npm:
            continue
        per_npm[npm][int(r.get("pertemuan") or 0)].append(r)
    return per_npm


def _rekap_mk_dalam(prodi, ta, sem, kunci, data):
    """Hitung rekap 1 MK dari hasil KT.muat_mk. Aturan identik dengan
    parse_data.generate_student_profiles, satu sumber di kelas_rules."""
    penawaran = data.get("penawaran") or {}
    sesi_dok = data.get("sesi") or {}
    sesi_rows = sesi_dok.get("sesi") or []
    sesi_map = {int(r["pertemuan"]): r for r in sesi_rows}
    bobot_pertemuan = {
        p: (float(d.get("bobot"))
            if isinstance(d.get("bobot"), (int, float)) else 0.0)
        for p, d in sesi_map.items()
    }
    per_npm = _matriks_nilai((data.get("nilai") or {}).get("nilai"))

    jumlah_peserta = len(per_npm)
    jumlah_kehadiran = 0.0
    jumlah_percen = 0          # mahasiswa yang kehadirannya bisa dihitung
    jumlah_nilai = 0.0
    dihitung_nilai = 0
    at_risk_npm = []

    for npm in sorted(per_npm):
        pertemuan_npm = per_npm[npm]
        slot_hadir_mhs = 0
        slot_total_mhs = 0
        alpha_total = 0
        pasangan = []          # (skor_pertemuan, bobot); None = belum diinput

        for p in sorted(sesi_map):
            slot_total = len((sesi_map.get(p) or {}).get("slot_absen") or [])
            if not slot_total:
                continue
            baris = pertemuan_npm.get(p) or []
            if len(baris) < slot_total:
                # BELUM DIINPUT -> netral (Batch B): tidak menekan persen,
                # tidak jadi Alpha, nilai pertemuan itu ditahan (None).
                pasangan.append((None, bobot_pertemuan.get(p, 0)))
                continue
            # "Hadir Sebagian" pada slot tetap dihitung hadir (satu sumber
            # aturan di kelas_rules.slot_dianggap_hadir).
            hadir_p = sum(1 for b in baris if KR.slot_dianggap_hadir(b.get("status")))
            slot_hadir_mhs += hadir_p
            slot_total_mhs += slot_total
            # Alpha dihitung per pertemuan seperti parse_data:
            # Hadir Sebagian BUKAN Alpha; pertemuan Sakit/Izin juga BUKAN Alpha.
            if hadir_p == 0:
                status_isi = {b.get("status") for b in baris}
                if "Sakit" not in status_isi and "Izin" not in status_isi:
                    alpha_total += 1
            skor = round(sum((b.get("skor") if b.get("skor") is not None else 0)
                             for b in baris) / slot_total, 1)
            pasangan.append((skor, bobot_pertemuan.get(p, 0)))

        if slot_total_mhs:
            jumlah_kehadiran += KR.persentase_kehadiran(
                slot_hadir_mhs, slot_total_mhs)
            jumlah_percen += 1
        pct = (KR.persentase_kehadiran(slot_hadir_mhs, slot_total_mhs)
               if slot_total_mhs else None)
        if KR.is_at_risk(alpha_total, pct):
            at_risk_npm.append(npm)
        if slot_total_mhs:
            jumlah_nilai += KR.hitung_nilai_terbobot(
                [s for s, _b in pasangan], [b for _s, b in pasangan])
            dihitung_nilai += 1

    # Keterlaksanaan RPS + cakupan bulan dari tanggal sesi.json (keputusan poin 1)
    topik_terisi = 0
    bulan = defaultdict(int)
    for r in sesi_rows:
        if r.get("topik_terverifikasi"):
            topik_terisi += 1
        b = _bulan_dari_tanggal(r.get("tanggal"))
        bulan[b or GRUP_TANPA_TANGGAL] += 1

    return {
        "kunci_mk": kunci,
        "nama_mk": penawaran.get("nama_mk", kunci),
        "kode_mk": penawaran.get("kode_mk", ""),
        "sks": penawaran.get("sks"),
        "kelas": penawaran.get("kelas", ""),
        "jenis_mk": penawaran.get("jenis_mk", ""),
        "prodi": prodi, "tahun_ajar": ta, "semester": sem,
        "peserta": jumlah_peserta,
        "pertemuan": len(sesi_rows),
        "pertemuan_standar": AT.pertemuan_total(),
        "topik_terisi": topik_terisi,
        "topik_placeholder": len(sesi_rows) - topik_terisi,
        "bobot_total": sum(int(r.get("bobot") or 0) for r in sesi_rows),
        "kehadiran_rata": (round(jumlah_kehadiran / jumlah_percen, 1)
                           if jumlah_percen else None),
        "nilai_rata": (round(jumlah_nilai / dihitung_nilai, 1)
                       if dihitung_nilai else None),
        "jumlah_at_risk": len(at_risk_npm),
        "at_risk_npm": at_risk_npm,
        "bulan": dict(sorted(bulan.items(),
                             key=lambda kv: (kv[0] == GRUP_TANPA_TANGGAL,
                                             kv[0]))),
    }


def agregat_mk(prodi, ta, sem, kunci):
    """Baris rekap 1 MK - basis per semester dan rollup semua semester.

    MK yang berkasnya tidak lengkap TIDAK membuat laporan mati: barisnya
    ditandai ``rusak`` dengan pesannya, sisa MK tetap tampil.
    """
    try:
        data = KT.muat_mk(prodi, ta, sem, kunci)
    except KT.KurikulumError as e:
        return {
            "prodi": prodi, "tahun_ajar": ta, "semester": sem,
            "kunci_mk": kunci, "nama_mk": kunci, "kode_mk": "", "sks": None,
            "peserta": None, "pertemuan": 0, "pertemuan_standar": AT.pertemuan_total(),
            "topik_terisi": 0, "topik_placeholder": AT.pertemuan_total(),
            "bobot_total": 0, "kehadiran_rata": None, "nilai_rata": None,
            "jumlah_at_risk": 0, "at_risk_npm": [], "bulan": {},
            "rusak": str(e),
        }
    tanda = _tanda_mk(prodi, ta, sem, kunci)
    kotak = _REKAP_CACHE.get((prodi, ta, sem, kunci))
    if kotak and kotak[0] == tanda:
        rekap = kotak[1]
    else:
        rekap = _rekap_mk_dalam(prodi, ta, sem, kunci, data)
        _REKAP_CACHE[(prodi, ta, sem, kunci)] = (tanda, rekap)
    hasil = dict(rekap)
    hasil["rusak"] = None
    return hasil


# ----------------------------------------------------------------------------- #
# Ringkasan tingkat di atas MK.
# ----------------------------------------------------------------------------- #
def _rata_mks(baris, field):
    """Rata-rata antar-MK satu field; MK yang tidak bisa dihitung (None)
    keluar dari penyebut, bukan difilter 0 - ikut aturan netral."""
    angka = [float(b[field]) for b in baris
             if not b.get("rusak") and b.get(field) is not None]
    return round(sum(angka) / len(angka), 1) if angka else None


def _ringkas_baris(baris, prodi, tahun_ajar=None, semester=None):
    """KPI rollup atas baris-baris MK.

    At-Risk dihitung PER MK (aturan tiap MK boleh berbeda hasilnya), lalu
    digabung sebagai MAHASISWA UNIK untuk KPI. Dulu KPI menjumlahkan angka
    per MK, sehingga 3 MK berisi 20 mahasiswa yang sama tampil sebagai "60
    at-risk" - lebih banyak daripada jumlah mahasiswa (35). Jumlah kejadian
    per MK tetap disediakan sebagai `jumlah_kejadian_at_risk` supaya laporan
    tidak kehilangan informasi.
    """
    mk_lengkap = sum(
        1 for b in baris
        if not b.get("rusak")
        and b.get("pertemuan", 0) > 0
        and (b.get("peserta") or 0) > 0)
    at_risk_unik = set()
    for b in baris:
        if b.get("rusak"):
            continue
        at_risk_unik.update(str(n) for n in (b.get("at_risk_npm") or []))
    ringkas = {
        "jumlah_mk": len(baris),
        "jumlah_at_risk": len(at_risk_unik),
        "at_risk_npm": sorted(at_risk_unik),
        "jumlah_kejadian_at_risk": sum(
            int(b.get("jumlah_at_risk") or 0) for b in baris
            if not b.get("rusak")),
        "mk_lengkap": mk_lengkap,
        "mk_rusak": sum(1 for b in baris if b.get("rusak")),
        "jumlah_topik_placeholder": sum(
            int(b.get("topik_placeholder") or 0) for b in baris
            if not b.get("rusak")),
        "kehadiran_rata": _rata_mks(baris, "kehadiran_rata"),
        "nilai_rata": _rata_mks(baris, "nilai_rata"),
    }
    if prodi is not None:
        ringkas["prodi"] = prodi
    if tahun_ajar is not None:
        ringkas["tahun_ajar"] = tahun_ajar
    if semester is not None:
        ringkas["semester"] = semester
    return ringkas


def agregat_semester(prodi, tahun_ajar, semester):
    """LEVEL 3: rekap SEMUA MK dalam satu (prodi, tahun ajar, semester)."""
    baris = [agregat_mk(prodi, tahun_ajar, semester, kunci)
             for kunci in KT.daftar_mk(prodi, tahun_ajar, semester)]
    return {
        "ringkas": _ringkas_baris(
            baris, prodi, tahun_ajar=tahun_ajar, semester=semester),
        "baris": baris,
    }


def agregat_semua_semester(prodi):
    """LEVEL 4: rollup SEMUA semester dan SEMUA MK untuk satu prodi.

    Bentuk:
      {'prodi': ..., 'ringkas': {...pohon penuh...},
       'tahun_ajar': {ta: {sem: {'ringkas': {...}, 'baris': [...]}}}}
    """
    hasil_tahun = {}
    for ta in KT.daftar_tahun(prodi):
        hasil_sem = {}
        for sem in KT.daftar_semester(prodi, ta):
            hasil_sem[sem] = agregat_semester(prodi, ta, sem)
        hasil_tahun[ta] = hasil_sem
    baris_pohon = [
        b for dok in hasil_tahun.values()
        for bagian in dok.values()
        for b in (bagian.get("baris") or [])
    ]
    return {
        "prodi": prodi,
        "ringkas": _ringkas_baris(baris_pohon, prodi),
        "tahun_ajar": hasil_tahun,
    }


# ----------------------------------------------------------------------------- #
# Potensi LEVEL 3: perkembangan mahasiswa SEPANJANG KULIAH (lintas MK/semester).
# Keputusan user 2026-10-21: potensi harus 3 lapis - per bulan (dalam 1 MK),
# per MK/semester (kartu potensi), dan perkembangan sepanjang kuliah per
# mahasiswa. Dua lapis pertama sudah ada di dashboard; lapis ketiga dihitung
# di sini dari katalog build data/courses/<kunci>.json setiap MK di tree.
# ----------------------------------------------------------------------------- #

# Cache tren: {prodi: (tanda_mtime_seluruh_katalog, hasil)} - katalog di-build
# ulang -> mtime berubah -> cache usang sendiri (pola yang sama dengan rekap).
_TREND_CACHE = {}


def _path_katalog(kunci):
    """Path katalog build satu MK: data/courses/<kunci>.json."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "courses", "{0}.json".format(kunci))


def perkembangan_mahasiswa(prodi):
    """Perjalanan tiap mahasiswa LINTAS MK - sepanjang kuliah.

    Sumber: katalog build per MK (data/courses/<kunci>.json) untuk SEMUA MK
    di tree prodi. Katalog belum dibangun TIDAK mematikan laporan: MK itu
    dicatat di ``mk_tanpa_katalog`` dan sisanya tetap dihitung (aturan yang
    sama dengan agregat_mk yang menandai rusak, bukan membatalkan).

    Bentuk keluaran:
      {'prodi': ..., 'jumlah_mk_tree': N, 'mk_tanpa_katalog': [...],
       'mahasiswa': {npm: {
           'nama', 'jumlah_mk',
           'riwayat': [{tahun_ajar, semester, kunci_mk, nama_mk, nilai,
                        grade, kehadiran, alpha, at_risk}, ...],
           'semester': [{tahun_ajar, semester, jumlah_mk, rata_nilai,
                         rata_kehadiran}, ...],
           'delta_nilai_terakhir': +x.x/-x.x/None,
           'arah_nilai': 'naik' | 'turun' | 'stabil' | None}}}
    """
    prodi = str(prodi or "").strip()
    if not prodi:
        raise KT.KurikulumError("Parameter prodi kosong.")
    if not prodi in KT.daftar_prodi():
        raise KT.KurikulumError("Prodi '{0}' tidak ada di tree kurikulum.".format(prodi))

    daftar = []
    for ta in KT.daftar_tahun(prodi):
        for sem in KT.daftar_semester(prodi, ta):
            for kunci in KT.daftar_mk(prodi, ta, sem):
                daftar.append((ta, sem, kunci))

    tanda = 0.0
    for _ta, _sem, kunci in daftar:
        path = _path_katalog(kunci)
        if os.path.exists(path):
            tanda = max(tanda, os.path.getmtime(path))
    cache = _TREND_CACHE.get(prodi)
    if cache and cache[0] == tanda and tanda:
        return cache[1]

    per_npm = {}
    tanpa_katalog = []
    for ta, sem, kunci in daftar:
        path = _path_katalog(kunci)
        if not os.path.exists(path):
            tanpa_katalog.append(kunci)
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                kat = json.load(f)
        except (OSError, json.JSONDecodeError):
            tanpa_katalog.append(kunci)
            continue
        nama_mk = (kat.get("course") or {}).get("nama_mk") or kunci
        for s in kat.get("students") or []:
            npm = str(s.get("npm") or "")
            if not npm:
                continue
            ak = s.get("akademik") or {}
            kh = s.get("kehadiran") or {}
            rec = per_npm.setdefault(npm, {"nama": s.get("nama") or npm,
                                           "riwayat": []})
            rec["nama"] = s.get("nama") or rec["nama"]
            rec["riwayat"].append({
                "tahun_ajar": ta, "semester": sem,
                "kunci_mk": kunci, "nama_mk": nama_mk,
                "nilai": ak.get("nilai_rata_rata"),
                "grade": ak.get("grade"),
                "kehadiran": kh.get("persentase"),
                "alpha": kh.get("alpha"),
                "at_risk": bool(s.get("at_risk")),
            })

    mahasiswa = {}
    for npm, rec in per_npm.items():
        riw = sorted(rec["riwayat"],
                     key=lambda r: (r["tahun_ajar"], r["semester"]))
        per_sem = defaultdict(list)
        for r in riw:
            per_sem[(r["tahun_ajar"], r["semester"])].append(r)
        semester = []
        for (ta, sem), isi in sorted(per_sem.items()):
            nilai = [r["nilai"] for r in isi if r["nilai"] is not None]
            keh = [r["kehadiran"] for r in isi if r["kehadiran"] is not None]
            semester.append({
                "tahun_ajar": ta, "semester": sem, "jumlah_mk": len(isi),
                "rata_nilai": (round(sum(nilai) / len(nilai), 1) if nilai else None),
                "rata_kehadiran": (round(sum(keh) / len(keh), 1) if keh else None),
            })
        delta = None
        arah = None
        if len(semester) >= 2:
            a = semester[-2]["rata_nilai"]
            b = semester[-1]["rata_nilai"]
            if a is not None and b is not None:
                delta = round(b - a, 1)
                if delta >= 5:
                    arah = "naik"
                elif delta <= -5:
                    arah = "turun"
                else:
                    arah = "stabil"
        mahasiswa[npm] = {
            "nama": rec["nama"],
            "jumlah_mk": len(riw),
            "riwayat": riw,
            "semester": semester,
            "delta_nilai_terakhir": delta,
            "arah_nilai": arah,
        }

    hasil = {
        "prodi": prodi,
        "jumlah_mk_tree": len(daftar),
        "mk_tanpa_katalog": tanpa_katalog,
        "mahasiswa": mahasiswa,
    }
    _TREND_CACHE[prodi] = (tanda, hasil)
    return hasil

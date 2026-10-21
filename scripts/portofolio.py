"""portofolio.py - Kumpulan data PORTOFOLIO MAHASISWA 4 LAPIS (keputusan user 2026-10-21).

Lapisan:
  1. PER BULAN     - rekap kehadiran & skor per bulan dalam tiap MK
                     (dari kehadiran.detail katalog; pertemuan tanpa tanggal
                     dikeluarkan, "Belum Diinput" NETRAL - aturan sama UI).
  2. PER MK        - ringkasan tiap MK: nilai terbobot, grade, kehadiran,
                     alpha, at-risk, archetype diagnosis v3.
  3. PER SEMESTER  - rollup jumlah MK + rata nilai + rata kehadiran.
  4. SEANJUTNYA    - sepanjang kuliah: agregat semua MK, arah tren ±5,
                     jumlah MK at-risk.

SUMBER & KETAATAN
-----------------
* Nilai/diagnosis TIDAK dihitung ulang di sini - semua dibaca dari katalog
  build data/courses/<kunci>.json yang SAMA dengan dashboard & PDF, jadi
  tidak ada dua sumber kebenaran.
* Aturan bulanan mengikuti app.js _chipBulananDetail:
  "Belum Diinput" / slot 0 = NETRAL (tidak menekan persen), tanpa tanggal
  dikeluarkan dari grup (GRUP_TANPA_TANGGAL).
* Fail-closed: NPM kosong -> ValueError; NPM tidak dikenal di satu katalog
  pun -> None (endpoint jadi 404). MK rusak tidak membatalkan laporan:
  masuk mk_gagal dengan alasan (aturan sama dengan periode.py).
* Cache: {npm: (tanda_mtime_seluruh_katalog, hasil)} - katalog di-build
  ulang -> mtime berubah -> cache usang sendiri (pola sama periode.py).
"""

import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kurikulum_tree as KT  # noqa: E402
import diagnosis as DIAG  # noqa: E402  (AMBANG label potensi - SATU SUMBER)
import bidang as BIDANG  # noqa: E402  (kanal bidang + dimensi khas + karier)

_LABEL_DIM = getattr(DIAG, "_LABEL_DIM", {})
_CACHE = {}


def _path_katalog(kunci):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "courses", "{0}.json".format(kunci))


def _isis_detail_bulanan(detail):
    """Lapis 1: rekap per bulan dari kehadiran.detail satu MK.

    Mengikuti aturan _chipBulananDetail app.js supaya UI dan dokumen
    menampilkan angka yang SAMA.
    """
    grup = defaultdict(lambda: {"total": 0, "hadir": 0, "skor": 0.0, "n": 0,
                                "pertemuan": 0})
    for d in (detail or []):
        d = d or {}
        tgl = str(d.get("tanggal") or "").strip()
        try:
            bulan = tgl[:7]
        except Exception:
            bulan = ""
        if d.get("status") == "Belum Diinput" or not d.get("slot_terisi"):
            continue  # netral - tidak menekan persen
        if not (len(bulan) == 7 and bulan[4] == "-"):
            continue  # GRUP_TANPA_TANGGAL: pertemuan tanpa tanggal
        g = grup[bulan]
        g["pertemuan"] += 1
        g["total"] += int(d.get("slot_total") or 0)
        g["hadir"] += int(d.get("slot_hadir") or 0)
        skor = d.get("skor")
        if isinstance(skor, (int, float)):
            g["skor"] += float(skor)
            g["n"] += 1
    hasil = []
    for bulan in sorted(grup):
        g = grup[bulan]
        pct = round(g["hadir"] / g["total"] * 100, 1) if g["total"] else None
        rata = round(g["skor"] / g["n"], 1) if g["n"] else None
        hasil.append({
            "bulan": bulan,
            "pertemuan": g["pertemuan"],
            "hadir_persen": pct,
            "rata_skor": rata,
        })
    return hasil


def _tanda_mtime(prodi):
    """Kunci cache: mtime terbaru seluruh katalog prodi."""
    tanda = 0.0
    for ta in KT.daftar_tahun(prodi):
        for sem in KT.daftar_semester(prodi, ta):
            for kunci in KT.daftar_mk(prodi, ta, sem):
                path = _path_katalog(kunci)
                if os.path.exists(path):
                    tanda = max(tanda, os.path.getmtime(path))
    return tanda


def kumpulan_portofolio(npm):
    """Data portofolio lengkap 4 lapis untuk SATU mahasiswa.

    Kembalian None jika NPM tidak ada di katalog mana pun; ValueError kalau
    parameter kosong atau tree kosong.
    """
    npm = str(npm or "").strip()
    if not npm:
        raise ValueError("Parameter npm kosong.")
    prodi_list = KT.daftar_prodi()
    if not prodi_list:
        raise KT.KurikulumError("Tree kurikulum kosong.")
    prodi = prodi_list[0]

    daftar = []
    for ta in KT.daftar_tahun(prodi):
        for sem in KT.daftar_semester(prodi, ta):
            for kunci in KT.daftar_mk(prodi, ta, sem):
                daftar.append((ta, sem, kunci))

    tanda = _tanda_mtime(prodi)
    cache = _CACHE.get(npm)
    if cache and cache[0] == tanda and tanda:
        return cache[1]

    mk_semua = []
    mk_gagal = []
    nama = None
    for ta, sem, kunci in daftar:
        path = _path_katalog(kunci)
        if not os.path.exists(path):
            mk_gagal.append({"kunci_mk": kunci, "sebab": "katalog belum dibangun"})
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                kat = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            mk_gagal.append({"kunci_mk": kunci, "sebab": "katalog tak terbaca: " + str(e)})
            continue

        student = next(
            (s for s in (kat.get("students") or []) if str(s.get("npm")) == npm),
            None)
        if not student:
            continue  # mahasiswa ini tidak mengambil MK itu - wajar, lanjut
        nama = student.get("nama") or nama
        ak = student.get("akademik") or {}
        kh = student.get("kehadiran") or {}
        ai = student.get("ai_diagnosis") or {}
        course = kat.get("course") or {}
        mk_semua.append({
            "tahun_ajar": ta,
            "semester": sem,
            "kunci_mk": kunci,
            "nama_mk": course.get("nama_mk") or kunci,
            "sks": course.get("sks"),
            "dosen_pengasuh": course.get("dosen_pengasuh"),
            "nilai": ak.get("nilai_rata_rata"),
            "grade": ak.get("grade"),
            "kehadiran": kh.get("persentase"),
            "alpha": kh.get("alpha"),
            "at_risk": bool(student.get("at_risk")),
            "alasan_at_risk": student.get("alasan_at_risk") or "",
            "archetype": (ai.get("mesin") or {}).get("archetype", ""),
            "status_alert": ai.get("status_alert") or "",
            "jumlah_pertemuan": len(kh.get("detail") or []),
            # LAPIS 1: rekap bulanan (pembanding chip yang sama di dashboard).
            "bulanan": _isis_detail_bulanan(kh.get("detail")),
            # ANALISIS NILAI/POTENSI: radar kompetensi per MK dari mesin v3 -
            # dirata-rata lintas MK untuk radar sepanjang kuliah.
            "kompetensi": ak.get("kompetensi") or {},
            "radar_sumber": ai.get("radar_sumber") or {},
        })

    if not mk_semua:
        return None  # NPM tidak dikenal di katalog mana pun - fail-closed

    mk_semua.sort(key=lambda m: (m["tahun_ajar"], m["semester"], m["kunci_mk"]))

    # LAPIS 3: rollup per semester.
    per_sem = defaultdict(list)
    for m in mk_semua:
        per_sem[(m["tahun_ajar"], m["semester"])].append(m)
    semester = []
    for (ta, sem), isi in sorted(per_sem.items()):
        nilai = [m["nilai"] for m in isi if m["nilai"] is not None]
        keh = [m["kehadiran"] for m in isi if m["kehadiran"] is not None]
        semester.append({
            "tahun_ajar": ta,
            "semester": sem,
            "jumlah_mk": len(isi),
            "rata_nilai": round(sum(nilai) / len(nilai), 1) if nilai else None,
            "rata_kehadiran": round(sum(keh) / len(keh), 1) if keh else None,
            "jumlah_at_risk": sum(1 for m in isi if m["at_risk"]),
            "mk": isi,  # lapis 1+2 dirujuk di dalam semester (expand UI/PDF)
        })

    # LAPIS 4: agregat sepanjang kuliah + arah tren ±5 (rumus sama periode.py).
    nilai_all = [m["nilai"] for m in mk_semua if m["nilai"] is not None]
    keh_all = [m["kehadiran"] for m in mk_semua if m["kehadiran"] is not None]
    delta = None
    arah = None
    bersih = [s["rata_nilai"] for s in semester if s["rata_nilai"] is not None]
    if len(bersih) >= 2:
        delta = round(bersih[-1] - bersih[-2], 1)
        arah = "naik" if delta >= 5 else ("turun" if delta <= -5 else "stabil")

    hasil = {
        "npm": npm,
        "nama": nama or npm,
        "prodi": prodi,
        "jumlah_mk": len(mk_semua),
        "jumlah_mk_at_risk": sum(1 for m in mk_semua if m["at_risk"]),
        "rata_nilai": round(sum(nilai_all) / len(nilai_all), 1) if nilai_all else None,
        "rata_kehadiran": round(sum(keh_all) / len(keh_all), 1) if keh_all else None,
        "total_alpha": sum(int(m["alpha"] or 0) for m in mk_semua),
        "delta_nilai_terakhir": delta,
        "arah_nilai": arah,
        "semester": semester,
        "mk": mk_semua,
        "mk_gagal": mk_gagal,
        # ANALISIS NILAI -> POTENSI (bukan lagi sekadar absen).
        "analisis_potensi": _analisis_potensi(mk_semua, arah, nama or npm),
    }
    _CACHE[npm] = (tanda, hasil)
    return hasil


# --------------------------------------------------------------------------- #
# ANALISIS NILAI -> POTENSI (dari SINYAL NYATA lintas MK - bukan absen saja)   #
# --------------------------------------------------------------------------- #
# RANCANGAN (keputusan user 2026-10-21, semua opsi rekomendasi terkunci):
#   1. CLUSTER BIDANG: MK dikelompokkan ke kanal (bidang.py), MK duplikat
#      antar-tahun di-dedup berdasar nama supaya tidak menimbang ganda.
#      Kanal terkuat = rata nilai tertinggi -> dasar narasi & dimensi khas.
#   2. MK TERATAS di kanal itu jadi "kasus utama" analisis.
#   3. DIMENSI KHAS BIDANG via TRAFO ESTIMASI JUJUR:
#      nilai_dim = 0.70 * rata nilai MK sekanal
#                + 0.30 * radar generik (diagnosis v3) yang merefleksi dim.
#      SELALU label "estimasi" - tidak pernah tampil sebagai fakta terukur.
#   4. MATRIKS KARIER SEPANJANG KULIAH: karier sekanal dapat bonus +4
#      (clamp cap karier), karier kanal lain tetap tampil.
# --------------------------------------------------------------------------- #

def _agregat_kanal(mk_semua):
    """Cluster nilai per kanal bidang (dedup MK duplikat via nama normal)."""
    per = {}
    nama_sudah = set()
    for m in mk_semua:
        if m.get("nilai") is None:
            continue
        nama_norm = str(m.get("nama_mk") or "").split("(")[0].strip().lower()
        if nama_norm in nama_sudah:
            continue  # MK kembar antar-tahun - cukup satu timbangan
        nama_sudah.add(nama_norm)
        kanal = BIDANG.kanal_dari_mk(m.get("kunci_mk"), m.get("nama_mk"))
        g = per.setdefault(kanal, {"mk": []})
        g["mk"].append(m)
    hasil = []
    for kanal in sorted(per):
        isi = sorted(per[kanal]["mk"],
                     key=lambda m: -(m["nilai"] if m["nilai"] is not None else -1))
        nilai = [m["nilai"] for m in isi]
        teratas = isi[0]
        hasil.append({
            "kanal": kanal,
            "nama": BIDANG.nama_kanal(kanal),
            "jumlah_mk": len(isi),
            "rata_nilai": round(sum(nilai) / len(nilai), 1),
            "mk_teratas": {"nama_mk": teratas.get("nama_mk"),
                           "nilai": teratas.get("nilai"),
                           "grade": teratas.get("grade")},
        })
    hasil.sort(key=lambda k: (-k["rata_nilai"], -k["jumlah_mk"]))
    return hasil


def _dim_khas(kanal, mk_sekanal, radar):
    """Dim khas bidang via trafo estimasi jujur (70% nilai kanal + 30% radar).

    Kembalian {id_dim: {label, nilai, sumber:"estimasi"}} atau {} bila data
    belum cukup (mengapa overstated menghormati prinsip fail-closed).
    """
    nilai_sekanal = [m.get("nilai") for m in mk_sekanal
                     if m.get("nilai") is not None]
    if not nilai_sekanal or not radar:
        return {}
    rata = sum(float(v) for v in nilai_sekanal) / len(nilai_sekanal)
    keluar = {}
    for dim_id, label, refleksi in BIDANG.dimensi_kanal(kanal):
        ref = float(radar.get(refleksi, rata))
        val = 0.70 * rata + 0.30 * ref
        keluar[dim_id] = {
            "label": label,
            "nilai": int(round(max(0.0, min(100.0, val)))),
            "sumber": "estimasi",
        }
    return keluar


def _label_potensi(rata_nilai, rata_kehadiran, arah):
    """Label potensi dari ambang yang SAMA dengan mesin diagnosis v3
    (diagnosis.AMBANG - satu sumber: star 85/90, high 80/85, normal 70/75).
    Kehadiran None (belum diinput) tidak mengangkat label ke star/high."""
    A = DIAG.AMBANG
    keh = rata_kehadiran if rata_kehadiran is not None else 0.0
    if rata_nilai is None:
        return "DATA BELUM LENGKAP"
    if rata_nilai >= A["star"]["nilai"] and keh >= A["star"]["kehadiran"]:
        label = "POTENSI TINGGI"
    elif rata_nilai >= A["high"]["nilai"] and keh >= A["high"]["kehadiran"]:
        label = "POTENSI BAIK"
    elif rata_nilai >= A["normal"]["nilai"]:
        label = "POTENSI MEMADAI"
    else:
        label = "BUTUH PENGUATAN"
    if arah == "naik":
        label += " · MENANJAK"
    elif arah == "turun":
        label += " · MENURUN"
    return label


def _analisis_potensi(mk_semua, arah, nama=""):
    """Agregat lintas MK dari NILAI KINERJA yang benar-benar tercatat.

    Kembalian (semua angka dari katalog, tanpa mengarang):
      label              - potensi keseluruhan (ambang diagnosis.py).
      alasan             - bukti angka yang menopang label.
      rekomendasi        - langkah konkret dari dim/MK terlemah.
      radar/radar_sumber - rata-rata kompetensi lintas MK (5 dim v3);
                           sumber jujur: "terukur" hanya kalau SEMUA MK
                           yang memasok dim itu terukur.
      mk_terkuat/terlemah- 3 MK dengan nilai tertinggi/terendah.
      sebaran            - tinggi, rendah, deviasi antar-MK (konsistensi).
      distribusi         - jumlah MK per archetype diagnosis.
      kanal/kanal_terkuat- cluster bidang (bidang.py); terkuat = rata nilai
                           tertinggi (MK duplikat antar-tahun di-dedup).
      dimensi_khas       - 3 dim khas bidang terkuat via trafo estimasi jujur
                           (70% nilai kanal + 30% radar generik), label
                           "estimasi" selalu.
      matriks_karier_kuliah - 10 karier sepanjang kuliah; karier sekanal
                           dapat bonus +4 (clamp cap), lainnya tetap.
    """
    nilai_sah = [m for m in mk_semua if m.get("nilai") is not None]

    # --- sebaran & konsistensi nilai ------------------------------------------
    angka = [float(m["nilai"]) for m in nilai_sah]
    sebaran = {}
    if angka:
        rata = sum(angka) / len(angka)
        sebaran = {
            "tertinggi": max(angka),
            "terendah": min(angka),
            "deviasi": (round(math.sqrt(
                sum((v - rata) ** 2 for v in angka) / len(angka)), 1)
                if len(angka) >= 3 else None),
        }

    # --- MK terkuat / terlemah (nilai, bukan absen) -----------------------------
    urut = sorted(mk_semua, key=lambda m: (-(m["nilai"] if m["nilai"] is not None else -1),
                                           m["kunci_mk"]))
    kuat = [{"nama_mk": m["nama_mk"], "nilai": m["nilai"], "grade": m["grade"]}
            for m in urut[:3] if m["nilai"] is not None]
    lemah = [{"nama_mk": m["nama_mk"], "nilai": m["nilai"], "grade": m["grade"]}
             for m in reversed(urut[-3:]) if m["nilai"] is not None]

    # --- radar kompetensi rata-rata lintas MK (sumber jujur) -------------------
    per_dim = defaultdict(lambda: {"vals": [], "semua_terukur": True})
    for m in mk_semua:
        comp = m.get("kompetensi") or {}
        sumber = m.get("radar_sumber") or {}
        for dim, val in comp.items():
            if isinstance(val, (int, float)):
                if sumber.get(dim) != "terukur":
                    per_dim[dim]["semua_terukur"] = False
                per_dim[dim]["vals"].append(float(val))
    radar = {}
    radar_sumber = {}
    for dim, isi in per_dim.items():
        if isi["vals"]:
            radar[dim] = int(round(sum(isi["vals"]) / len(isi["vals"])))
            radar_sumber[dim] = ("terukur" if isi["semua_terukur"]
                                 else "estimasi")

    # --- distribusi archetype ---
    distribusi = defaultdict(int)
    for m in mk_semua:
        if m.get("archetype"):
            distribusi[m["archetype"]] += 1

    # --- bukti angka + label + rekomendasi --------------------------------------
    rata_nilai = (round(sum(angka) / len(angka), 1) if angka else None)
    n_at_risk = sum(1 for m in mk_semua if m["at_risk"])
    total_alpha = sum(int(m["alpha"] or 0) for m in mk_semua)
    keh_semua = [m["kehadiran"] for m in mk_semua if m["kehadiran"] is not None]
    rata_keh = (round(sum(keh_semua) / len(keh_semua), 1)
                if keh_semua else None)
    label = _label_potensi(rata_nilai, rata_keh, arah)

    # --- bukti angka (potongan alasan) ------------------------------------------
    potongan = []
    if rata_nilai is not None:
        potongan.append(f"Rata nilai {rata_nilai} dari {len(mk_semua)} MK")
    if rata_keh is not None:
        potongan.append(f"hadir rata-rata {rata_keh}%")
    if total_alpha:
        potongan.append(f"{total_alpha} hari alpha")
    if n_at_risk:
        potongan.append(f"{n_at_risk} MK berstatus at-risk")
    arah_txt = {"naik": "tren nilai menanjak", "turun": "tren nilai menurun",
                "stabil": "tren nilai stabil"}.get(arah)
    if arah_txt:
        potongan.append(arah_txt)

    # --- CLUSTER BIDANG (MK terkuat -> dimensi menyesuaikan) -------------------
    kanal_list = _agregat_kanal(mk_semua)
    kanal_top = kanal_list[0] if kanal_list else None
    dim_khas = {}
    matriks_kuliah = []
    if kanal_top:
        mk_sekanal = [m for m in mk_semua
                      if BIDANG.kanal_dari_mk(m.get("kunci_mk"), m.get("nama_mk"))
                      == kanal_top["kanal"]]
        dim_khas = _dim_khas(kanal_top["kanal"], mk_sekanal, radar)
        # contoh MK lemah IKUT dari kanal yang sama (konteks konsisten)
        lem_sekanal = sorted((m for m in mk_sekanal if m.get("nilai") is not None),
                             key=lambda m: m["nilai"])[:2]
        if radar:
            matriks_kuliah = DIAG.matriks_karier(
                radar, nama or "", bidang_terkuat=kanal_top["kanal"])
        if rata_nilai is not None:
            t = kanal_top["mk_teratas"]
            potongan.insert(0, (
                f"Kanal terkuat {kanal_top['nama']} — rata {kanal_top['rata_nilai']} "
                f"({kanal_top['jumlah_mk']} MK • tertinggi {t['nama_mk']} {t['nilai']})"))

    alasan = " • ".join(potongan) if potongan else "Data nilai belum lengkap."

    # --- rekomendasi: dim khas terlemah + arah karier sekanal -------------------
    rekomendasi = ""
    if dim_khas:
        dim_lemah = min(dim_khas.items(), key=lambda kv: kv[1]["nilai"])
        mk_lemah = " dan ".join(x["nama_mk"] for x in lem_sekanal) or ""
        rekomendasi = (
            f"Prioritas: asah {dim_lemah[1]['label']} "
            f"(estimasi skor {dim_lemah[1]['nilai']}), mulai dari MK {mk_lemah}."
            if mk_lemah else
            f"Prioritas: asah {dim_lemah[1]['label']} "
            f"(estimasi skor {dim_lemah[1]['nilai']}).")
        if matriks_kuliah:
            t0 = matriks_kuliah[0]
            rekomendasi += (
                f" Arah karier terdekat: {t0['profesi']} "
                f"({t0['kecocokan_persen']}%).")
    elif radar and len(radar) >= 2:
        dim_lemah = min(radar.items(), key=lambda kv: kv[1])  # skor terendah
        nama_dim = _LABEL_DIM.get(dim_lemah[0], dim_lemah[0])
        mk_lemah = " dan ".join(x["nama_mk"] for x in lemah[:2]) or ""
        rekomendasi = (
            f"Prioritas peningkatan: {nama_dim} (skor rata-rata {dim_lemah[1]}). "
            f"Mulai dari MK {mk_lemah}"
            if mk_lemah else
            f"Prioritas peningkatan: {nama_dim} (skor rata-rata {dim_lemah[1]}).")
        if dim_lemah[0] == "kedisiplinan_asistensi" or n_at_risk:
            rekomendasi += ". Kehadiran adalah fondasi: kunci ritme asistensi terjadwal."
        else:
            rekomendasi += ". Latihan bertahap dengan umpan balik asistensi meja."

    return {
        "label": label,
        "alasan": alasan,
        "rekomendasi": rekomendasi,
        "radar": radar,
        "radar_sumber": radar_sumber,
        "kanal": kanal_list,
        "kanal_terkuat": (kanal_top or {}).get("kanal"),
        "dimensi_khas": dim_khas,
        "mk_terkuat": kuat,
        "mk_terlemah": lemah,
        "sebaran": sebaran,
        "distribusi": dict(distribusi),
        "matriks_karier_kuliah": matriks_kuliah,
    }

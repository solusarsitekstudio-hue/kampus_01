"""parse_data: bangun data/academic_data.json DARI tree kurikulum.

TAHAP E - SUMBER DATA PINDAH
----------------------------
Dulu file ini membaca `D:\\Desktop\\- HAL LAIN\\DAFTAR MAHASISWA.xlsx` dan
`...\\02 rekap qs pratikum.pdf` (folder pribadi), dan mengarang 6 sesi di dalam
kode. Akibatnya sistem tidak mandiri dan jumlah pertemuan tidak bisa dipercaya.

Sekarang sumbernya tree kurikulum:

    data/kurikulum/<PRODI>/<TAHUN_AJAR>/<SEMESTER>/<KUNCI_MK>/

File ini menjadi "compiler": membaca identitas + 16 pertemuan + catatan nilai,
lalu menghitung. Tidak ada lagi `random.seed(42)` global - RNG dibuat PER
MAHASISWA (`persona.rng_untuk(npm)`), sehingga menambah satu baris tidak
menggeser nilai seluruh kelas (utang #1 dibayar).
"""
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_JSON = os.path.join(DATA_DIR, "academic_data.json")

# =============================================================================
# ATURAN KELAS -> SATU MODUL BERSAMA (FIX TAHAP C-4)
# =============================================================================
# Aturan nilai, at-risk, dan badge karier TIDAK didefinisikan di file ini.
# Semua modul mengimpor dari scripts/kelas_rules.py supaya tidak ada salinan
# yang bisa berbeda - akar yang dulu melahirkan 4 aturan at-risk berbeda.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kelas_rules import (  # noqa: E402
    at_risk_alpha_min,
    at_risk_kehadiran_min,
    at_risk_reasons,
    is_at_risk,
    hitung_nilai_terbobot,
    cakupan_bobot,
    GRADE_BELUM_LENGKAP,
    kategori_kecocokan_dari_skor,
    grade_dari_skor,
    persentase_kehadiran,
    pertemuan_belum_diinput,
    pertemuan_memenuhi_ambang,
    slot_dianggap_hadir,
    status_pertemuan_dari_status,
    validasi_bobot,
    teks_grade,
)
# FIX TAHAP E: ambang at-risk & teksnya kini dari satu sumber config/aturan.json.
import aturan as ATURAN  # noqa: E402

# FIX: identitas (mata kuliah, dosen, asisten, ketua prodi, institusi) dibaca
# dari SATU sumber -- config/identitas.json lewat scripts/identitas.py.
import identitas as IDENT  # noqa: E402
# Tree kurikulum bertingkat + persona/RNG per NPM.
import kurikulum_tree as KT  # noqa: E402
import persona as PS  # noqa: E402
# Mesin diagnosis v3: sinyal nyata -> klasi radar/karier/narasi (tanpa RNG).
import diagnosis as DIAG  # noqa: E402

import hashlib  # noqa: E402
import shutil  # noqa: E402
import time  # noqa: E402

# ======================== STEMPEL KOMPILASI PER-MK (Tangga B) ================
# Keputusan diskusi user 2026-10-21 (zona optimasi 1 - kompilasi master):
#
# Master itu PER-MK AKTIF (`bangun_dataset()` membaca satu MK), jadi "skip
# stempel" naif tidak pernah menyala saat ganti MK - memang harus di-hitung
# MK yang baru. Solusinya SNAPSHOT per-MK yang deterministik:
#   * setiap kompilasi selain menulis master juga menyimpan salinan utuh ke
#     `data/master_mk/<KUNCI>.json`;
#   * stempel(kunci) = sha1 atas (mtime + ukuran + mtime_ns) seluruh berkas
#     sumber yang MENENTUKAN isi master MK itu: folder tree MK (sesi.json,
#     nilai.json, penawaran.json, ...), mahasiswa.json prodi, plus global
#     config/aturan.json, config/kurikulum.json, dan config/identitas.json
#     TANPA penunjuk `mata_kuliah_aktif` (penunjuk aktif memilih SIAPA yang
#     ditampilkan, bukan isi data - kunci yang jujur untuk perbandingan).
#   * kalau stempel TERBARU == stempel tersimpan DAN snapshot ada -> master
#     = SALINAN BIT-IDENTIK snapshot (build benar-benar deterministik, kunci
#     RNG per NPM). Tidak ada kompilasi 12 detik; pindah MK kembali ke MK
#     yang pernah dikompilasi jadi < 0.5 s. `python scripts/parse_data.py
#     --compile-ulang` memaksa kompilasi penuh (kalau benar-benar diminta).
# Tanda "masih segar" kesalahan paling berbahaya dinetral: karena snapshot
# SELALU disalin ke master di jalur segar, master tidak mungkin jauh dari
# snapshot yang sama stampnya. Tree-tulisan manual masih keluar lewat stempel
# maju -> kompilasi ulang normal.
# -----------------------------------------------------------------------------
STAMPEL_PATH = os.path.join(DATA_DIR, "master_stamps.json")
SNAPSHOT_DIR = os.path.join(DATA_DIR, "master_mk")


def stempel_kompilasi(kunci=None):
    """Stempel sumber master untuk SATU MK (fail-closed dari muat_kurikulum).

    Menghasilkan (kunci, stamp_hex). stamp diam-diam menangkap perubahan
    berkas tree MK, mahasiswa.json prodi, dan global aturan/kurikulum/
    identitas (minus penunjuk aktif).
    """
    prodi, ta, sem, kunci = mk_aktif_dari_tree(kunci)
    paths = []
    folder_mk = KT.path_mk(prodi, ta, sem, kunci)
    for root, _dirs, files in os.walk(folder_mk):
        for fn in files:
            if not fn.startswith("."):
                paths.append(os.path.join(root, fn))
    paths.append(KT.path_mahasiswa(prodi))
    for rel in ("config/aturan.json", "config/kurikulum.json"):
        paths.append(os.path.join(BASE_DIR, rel))
    paths.sort()
    bagian = []
    for p in paths:
        label = os.path.relpath(p, BASE_DIR).replace("\\", "/")
        if os.path.isfile(p):
            st = os.stat(p)
            bagian.append("{0}:{1}:{2}".format(
                label, int(st.st_mtime), st.st_size))
        else:
            bagian.append("{0}:-".format(label))
    # identitas minus penunjuk MK aktif - isi lain (dosen MK, institusi,
    # identitas MK lain) benar-benar mempengaruhi dataset saat compile.
    cfg = {k: v for k, v in (IDENT.muat(force=True) or {}).items()
           if k != "mata_kuliah_aktif"}
    bagian.append("identitas:{0}".format(
        json.dumps(cfg, sort_keys=True, ensure_ascii=False)))
    stamp = hashlib.sha1("\n".join(bagian).encode("utf-8")).hexdigest()
    return kunci, stamp


def muat_reg_stempel():
    """Registry stempel; rusak/hilang -> {} (fail-closed, akan kompilasi)."""
    try:
        with open(STAMPEL_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        return reg if isinstance(reg, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def tulis_reg_stempel(reg):
    os.makedirs(os.path.dirname(STAMPEL_PATH), exist_ok=True)
    tmp = STAMPEL_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STAMPEL_PATH)


def _salin_atomik(src, dest):
    """Salin berkas ATOMIK (tmp + os.replace) - pembaca tidak melihat setengah."""
    tmp = dest + ".tmp"
    shutil.copyfile(src, tmp)
    os.replace(tmp, dest)


def _waktu_seribuan():
    return time.strftime("%Y-%m-%d %H:%M:%S")



# =============================================================================
# SUMBER DATA: TREE KURIKULUM (bukan Excel/PDF lagi)
# =============================================================================
def mk_aktif_dari_tree(kunci=None):
    """(prodi, tahun_ajar, semester, kunci_mk) untuk satu MK.

    `kunci=None` berarti MK yang sedang aktif di config/identitas.json. Kunci
    yang diminta HARUS ada di config/identitas.json (fail-closed), karena
    identitas MK tetap satu sumber di sana.
    """
    inst = IDENT.institusi()
    kunci = kunci or IDENT.mk_aktif()
    mk = IDENT.mk(kunci)
    ta, sem = KT.pecah_semester(mk.get("semester"))
    return inst.get("prodi", ""), ta, sem, kunci


def muat_kurikulum(kunci=None):
    """Baca identitas mahasiswa + penawaran + 16 sesi + nilai dari tree.

    Fail-closed: berkas tidak lengkap atau bobot tidak berjumlah 100 = raise.
    Dulu sumber yang gagal diam-diam jatuh ke template lain, dan dashboard
    menampilkan topik mata kuliah yang salah tanpa satu pun pesan error.
    """
    prodi, ta, sem, kunci = mk_aktif_dari_tree(kunci)
    path_mhs = KT.path_mahasiswa(prodi)
    if not os.path.exists(path_mhs):
        raise ValueError(
            "Identitas mahasiswa belum ada: {0}\n"
            "Bangun dulu: python scripts\\migrasi_kurikulum.py".format(path_mhs)
        )
    mahasiswa = KT.baca_json(path_mhs).get("mahasiswa") or []
    if not mahasiswa:
        raise ValueError("Tidak ada mahasiswa di {0}".format(path_mhs))

    data = KT.muat_mk(prodi, ta, sem, kunci)
    penawaran, sesi_doc, nilai_doc = data["penawaran"], data["sesi"], data["nilai"]

    masalah = KT.validasi_sesi(sesi_doc, kunci)
    if masalah:
        raise ValueError("sesi.json '{0}' tidak valid:\n- {1}".format(
            kunci, "\n- ".join(masalah)))
    masalah_bobot = validasi_bobot(KT.bobot_sesi(sesi_doc), kunci)
    if masalah_bobot:
        raise ValueError("Bobot sesi '{0}' tidak valid:\n- {1}".format(
            kunci, "\n- ".join(masalah_bobot)))

    return {
        "prodi": prodi,
        "tahun_ajar": ta,
        "semester": sem,
        "kunci_mk": kunci,
        "mahasiswa": mahasiswa,
        "penawaran": penawaran,
        "sesi_dokumen": sesi_doc,
        "sessions": list(sesi_doc.get("sesi") or []),
        "nilai_dokumen": nilai_doc,
    }


def kelompokkan_nilai(nilai_dokumen):
    """{npm: [baris slot]} dari berkas nilai."""
    hasil = {}
    for r in (nilai_dokumen or {}).get("nilai", []):
        hasil.setdefault(str(r.get("npm")), []).append(r)
    return hasil


def ringkas_kehadiran(baris_slot, sessions):
    """Rincian kehadiran PER PERTEMUAN, jujur sampai tingkat slot.

    Keputusan user (Tahap E): yang ditampilkan pertemuan, tetapi persen
    dihitung dari slot - jadi mahasiswa yang hadir 1 dari 4 slot tampil
    "Hadir Sebagian", tidak dibulatkan menjadi hadir atau alpha.

    FIX: pertemuan yang baris slotnya BELUM LENGKAP (mis. baru 1 dari 2 slot,
    atau kosong sama sekali) TIDAK lagi dianggap Alpha dan TIDAK diberi nilai 0.
    Pertemuan itu ditandai "Belum Diinput", dikeluarkan dari hitung nilai.
    Perilaku lama (slot kosong = Alpha) hanya dipakai bila
    `kehadiran.slot_belum_diisi` di config diset "alpha".
    """
    per_pertemuan = {}
    for r in baris_slot:
        per_pertemuan.setdefault(int(r.get("pertemuan") or 0), []).append(r)

    # Perilaku lama (slot kosong = Alpha) hanya kalau diminta eksplisit di config.
    pakai_belum_diinput = not ATURAN.hitung_slot_kosong_sebagai_alpha()

    detail = []
    hitung = {"Hadir": 0, "Hadir Sebagian": 0, "Sakit": 0, "Izin": 0,
              "Alpha": 0, "Belum Diinput": 0}
    slot_hadir_total = 0
    slot_total_semua = 0
    pertemuan_ambang = 0

    for s in sessions:
        p = int(s["pertemuan"])
        slot_total = len(s.get("slot_absen") or [])
        baris = per_pertemuan.get(p, [])
        slot_terisi = len(baris)
        # "Hadir Sebagian" pada slot tetap dihitung hadir (lihat kelas_rules).
        slot_hadir = sum(1 for b in baris if slot_dianggap_hadir(b.get("status")))
        belum = pakai_belum_diinput and pertemuan_belum_diinput(slot_terisi, slot_total)

        if belum:
            # Data belum masuk: jangan mengarang nilai dan jangan menghitung Alpha.
            bucket = "Belum Diinput"
            skor = None
        else:
            skor = (
                round(sum((b.get("skor") if b.get("skor") is not None else 0) for b in baris) / slot_total, 1)
                if slot_total else 0.0
            )
            bucket = status_pertemuan_dari_status(
                [b.get("status") for b in baris], slot_total
            )

        hitung[bucket] += 1
        if belum:
            # FIX BELUM-DIINPUT-KEHADIRAN (Batch B): pertemuan yang datanya
            # belum masuk TIDAK boleh menekan persen kehadiran - dulu
            # slot_totalnya tetap masuk penyebut, jadi mahasiswa bisa tercatat
            # "Kehadiran < 75%" hanya karena dosen belum menginput presensi.
            # Konsisten dengan nilai/grade yang ditahan: pertemuan ini netral
            # (keluar dari penyebut, keluar dari hitungan pertemuan_ambang).
            pass
        else:
            if pertemuan_memenuhi_ambang(slot_hadir, slot_total):
                pertemuan_ambang += 1
            slot_hadir_total += slot_hadir
            slot_total_semua += slot_total

        alasan = "-"
        if bucket in ("Sakit", "Izin"):
            alasan = next((b.get("alasan") for b in baris
                           if b.get("alasan") not in (None, "-")), "-")
        elif bucket == "Alpha":
            alasan = "Tanpa keterangan / tidak hadir di presensi portal"
        elif bucket == "Belum Diinput":
            alasan = ("Presensi pertemuan ini belum diinput "
                      "({0}/{1} slot tercatat) - bukan Alpha, nilai tidak dihitung"
                      ).format(slot_terisi, slot_total)

        detail.append({
            "pertemuan": p,
            "tanggal": s.get("tanggal"),
            "tanggal_display": s.get("tanggal_display"),
            "topik": s.get("topik"),
            "tipe": s.get("tipe"),
            "slot_total": slot_total,
            "slot_terisi": slot_terisi,
            "slot_hadir": slot_hadir,
            "status": bucket,
            "alasan": alasan,
            "skor": skor,
        })

    return detail, hitung, pertemuan_ambang, slot_hadir_total, slot_total_semua

# CATATAN: `kategori_kecocokan_dari_skor()` sekarang diimpor dari kelas_rules.py
# (FIX TAHAP C-4) supaya hanya ada satu definisi di seluruh sistem.


# =============================================================================
# PERSONA / MATRIKS KARIER - DIPINDAH KE scripts/diagnosis.py (MESIN V3)
# =============================================================================
# Dulu di sini ada generate_10_career_matrix() berbasis RNG per NPM dan alias
# persona NPM (PS.tentukan_archetype). Keputusan user 2026-10-21: diagnosis
# 100% dari SINYAL NYATA, jadi mesin klasi/radar/matriks/narasi tinggal SATU:
# scripts/diagnosis.py - dipanggil di generate_student_profiles. persona.py
# tetap ada khusus untuk generator nilai sintetis + tests/test_seed_per_mk.py.


# =============================================================================
# CPMK PLACEHOLDER
# =============================================================================
# Dipakai laporan audit dosen -> kaprodi. BELUM dari RPS resmi dan BUKAN klaim
# capaian pembelajaran; hanya pengingat agar kolomnya tidak kosong dan tidak
# terkesan sudah final. Ganti dengan CPMK resmi dari RPS saat tersedia.
CPMK_PLACEHOLDER = [
    "CPMK-1: Menguasai konsep dasar dan instrumen kerja mata kuliah",
    "CPMK-2: Mampu menerapkan prosedur kerja standar pada studi kasus",
    "CPMK-3: Mampu menyusun keluaran kerja sesuai standar profesinya",
    "CPMK-4: Mampu mempublikasikan dan mengomunikasikan hasil kerja",
]


def generate_student_profiles(students, sessions, nilai_per_npm, ctx=None):
    # FIX: identitas mata kuliah TIDAK lagi disalin di sini. Dibaca dari satu
    # sumber (config/identitas.json). Kunci yang ditulis SENGAJA dikunci ke 11
    # kunci yang sama seperti sebelumnya, supaya academic_data.json tidak berubah.
    ctx = ctx or {}
    _ident = IDENT.lengkapi(ctx.get("kunci_mk"))
    course_info = {
        k: _ident[k]
        for k in (
            "kode_mk",
            "nama_mk",
            "prodi",
            "fakultas",
            "semester",
            "sks",
            "kelas",
            "jadwal",
            "ketua_prodi",
            "dosen_pengasuh",
            "asisten_dosen",
        )
    }
    _institusi = IDENT.institusi()
    _prodi = str(_institusi.get("prodi", ""))
    _fakultas = str(_institusi.get("fakultas", ""))
    _kaprodi = str(_institusi.get("ketua_prodi", ""))
    _nama_mk = str(course_info["nama_mk"])
    _asisten = str(course_info["asisten_dosen"])
    _total_sesi = len(sessions)

    student_records = []

    for idx, s in enumerate(students):
        npm = str(s["npm"])
        nama = s["nama"]

        # MESIN DIAGNOSIS V3 (keputusan user 2026-10-21): klasifikasi, radar,
        # matriks karier, dan narasi 100% dari SINYAL NYATA mahasiswa ini
        # (nilai terbobot, kehadiran slot, alpha, konsistensi skor). Persona
        # NPM (persona.py) SENGGAJA TIDAK dipakai di jalur diagnosis - dia
        # tetap dipakai generator nilai sintetis saja. Deterministik & tanpa RNG.
        baris_slot = nilai_per_npm.get(npm, [])
        (attendance_list, hitung_status, pertemuan_ambang,
         slot_hadir_total, slot_total_semua) = ringkas_kehadiran(baris_slot, sessions)

        total_hadir = hitung_status["Hadir"]
        total_sebagian = hitung_status["Hadir Sebagian"]
        total_sakit = hitung_status["Sakit"]
        total_izin = hitung_status["Izin"]
        total_alpha = hitung_status["Alpha"]
        total_belum_diinput = hitung_status["Belum Diinput"]
        session_scores = [d["skor"] for d in attendance_list]

        # Persen kehadiran berbasis SLOT (bukan jumlah pertemuan): 2 dari 4 slot
        # = 50%. Ini yang membuat kehadiran sebagian terbaca jujur, bukan
        # dibulatkan diam-diam menjadi hadir atau alpha.
        attendance_pct = persentase_kehadiran(slot_hadir_total, slot_total_semua)

        # FIX TAHAP B: Alpha (nilai 0) ikut dihitung dan bobot sesi dipakai.
        # FIX TAHAP E: bobot kini dari sesi.json (16 pertemuan, total 100).
        # FIX BELUM-DIINPUT: sesi yang belum diinput keluar dari hitung nilai dan
        # bobotnya dinormalisasi ulang; grade ditahan sampai data lengkap.
        bobot_sesi = [sess.get("bobot", 0) for sess in sessions]
        avg_score = hitung_nilai_terbobot(session_scores, bobot_sesi)
        cakupan = cakupan_bobot(session_scores, bobot_sesi)
        data_lengkap = total_belum_diinput == 0

        # Grade Assignment & Competency Status (No Ranking, focusing on growth)
        # FIX TAHAP C-4: ambang batas grade diambil dari kelas_rules.py, bukan
        # ditulis ulang sebagai rantai if/elif. Teks predikat pun diambil dari
        # satu tabel, sehingga tidak mungkin ada grade tanpa teksnya.
        if data_lengkap:
            grade, pengali_kesiapan = grade_dari_skor(avg_score, attendance_pct)
        else:
            grade, pengali_kesiapan = GRADE_BELUM_LENGKAP, 1.0
        # FIX BELUM-DIINPUT-KEHADIRAN: kehadiran yang belum ada datanya sama
        # sekali (slot_total_semua == 0) -> kirim None ke at-risk supaya tidak
        # tercatat "Kehadiran 0%" (menuduh) padahal datanya memang belum masuk.
        pct_untuk_at_risk = attendance_pct if slot_total_semua else None
        at_risk_reasons_list = at_risk_reasons(total_alpha, pct_untuk_at_risk)
        student_is_at_risk = bool(at_risk_reasons_list)
        predikat, status_kompetensi, kesiapan_profesi = teks_grade(grade)
        indeks_kesiapan = round(avg_score * pengali_kesiapan, 1)

        # MESIN DIAGNOSIS V3 (keputusan user 2026-10-21): klasi, radar, narasi,
        # dan matriks karier 100% dari SINYAL NYATA - nilai terbobot, kehadiran
        # slot, alpha, konsistensi skor sekian pertemuan. Persona NPM TIDAK
        # dipakai lagi di jalur ini (tetap dipakai generator nilai sintetis di
        # persona.py). At-risk TETAP satu aturan kelas_rules di atas -> tidak
        # ada lagi label yang kontradiksi dengan badge AT-RISK. Deterministik:
        # tanpa RNG; sinyal sama -> hasil sama (tanda_sinyal di meta).
        (archetype, competency, ai_diagnosis, diag_meta) = DIAG.hasil(
            nama=nama,
            nilai=avg_score,
            kehadiran=(attendance_pct if slot_total_semua else None),
            alpha=total_alpha,
            skor_sesi=session_scores,
            data_lengkap=data_lengkap,
            cakupan_bobot=cakupan,
            nama_mk=_nama_mk,
        )
        career_matrix = ai_diagnosis["matriks_karier_10"]

        # Video Storyboard for Student Showcase (Focus on pride, progress, and motivating parents)
        video_storyboard = {
            "durasi_detik": 32,
            "format": "9:16 Vertikal (Reels / Shorts / WhatsApp Story)",
            "bgm_mood": "Inspiratif, Modern Upbeat Acoustic Architecture",
            "voiceover_script": (
                f"Alhamdulillah! Satu semester penuh dedikasi dan kerja keras di Lab Komputer Arsitektur! "
                f"Inilah ananda {nama.title()}, yang telah berhasil menuntaskan seluruh modul gambar kerja digital "
                f"mulai dari perancangan denah presisi hingga detail potongan struktural dengan capaian predikat {grade}. "
                f"Bapak dan Ibu patut sangat bangga, ananda siap melangkah menjadi arsitek masa depan kebanggaan keluarga dan bangsa!"
            ),
            "scenes": [
                {
                    "detik": "00:00 - 00:06",
                    "visual": "Foto Mahasiswa & Gelar Sertifikasi Kompetensi Studio 2026",
                    "teks": f"Kebanggaan Ananda {nama.split()[0]}"
                },
                {
                    "detik": "00:06 - 00:16",
                    "visual": "Zoom-in aktivitas gambar di layar AutoCAD Lab LIKDA",
                    "teks": "Fokus Menggambar Denah & Detail Struktur"
                },
                {
                    "detik": "00:16 - 00:25",
                    "visual": "Karya layout lembar kerja etiket cetak PDF standar A3",
                    "teks": "Karya Nyata Siap Portofolio Profesional"
                },
                {
                    "detik": "00:25 - 00:32",
                    "visual": "Logo Resmi Prodi Arsitektur & Pesan Apresiasi Orang Tua",
                    "teks": "Terima Kasih Atas Doa & Dukungan Orang Tua"
                }
            ]
        }

        # WhatsApp Message (Polite, formal, NO competitive rank, highlighting pride & 10 career possibilities)
        wa_message = (
            f"Assalamuâ€™alaikum Warahmatullahi Wabarakatuh.\n\n"
            f"Kepada Yth. Bapak/Ibu Wali Murid dari *{nama.upper()}*,\n\n"
            f"Salam hangat dan salam takzim dari Program Studi {_prodi}, Fakultas {_fakultas}.\n\n"
            f"Melalui pesan resmi ini, kami menyampaikan Laporan Perkembangan Akademik, Portofolio Gambar Kerja, dan Analisis Pemetaan Potensi Karier ananda pada mata kuliah *{_nama_mk}*:\n\n"
            f"ðŸ“Š *Ringkasan Capaian Kompetensi:*\n"
            f"â€¢ Kehadiran Studio: *{attendance_pct}%* ({total_hadir}/{_total_sesi} Sesi Terlaksana)\n"
            f"â€¢ Nilai Akhir Studio: *{avg_score}* (Predikat: *{grade}* - {predikat})\n"
            f"â€¢ Status Kompetensi: *{status_kompetensi}*\n"
            f"â€¢ Kesiapan Industri: *{kesiapan_profesi}* (Indeks: *{indeks_kesiapan}/100*)\n\n"
            f"ðŸ’¡ *Catatan Dosen Pengasuh:*\n"
            f"\"{ai_diagnosis['analisis_karakter_spasial'][:140]}...\"\n\n"
            f"ðŸ“ *Lampiran Berkas Resmi Terlampir:*\n"
            f"1. ðŸ“Ž Rekap Kehadiran Mahasiswa Bulanan (Presensi & Log Sesi)\n"
            f"2. ðŸ“Ž Rapor Hasil Evaluasi Akhir & Pemetaan 10 Karier Masa Depan\n"
            f"3. ðŸ“Ž Portofolio Presentasi Slide Deck 16:9 Widescreen (DeckCraft)\n\n"
            f"Bapak/Ibu dapat meninjau berkas dokumen terlampir. Terima kasih tak terhingga atas doa, bimbingan, dan cinta kasih Bapak/Ibu yang senantiasa mendampingi ananda di rumah.\n\n"
            f"Hormat kami,\n"
            f"*Ketua Program Studi {_prodi}*\n"
            f"*{_kaprodi}*\n"
            f"Asisten Dosen: *{_asisten}*"
        )

        student_records.append({
            "no": s.get("no", idx + 1),
            "npm": npm,
            "nama": nama,
            "archetype": archetype,
            "at_risk": student_is_at_risk,
            "alasan_at_risk": at_risk_reasons_list,
            "kehadiran": {
                # DUA ukuran "hadir" - jangan disatukan, keduanya ditampilkan:
                #   pertemuan_penuh            = SEMUA slot pertemuan itu hadir
                #   pertemuan_ambang_terpenuhi = >= min_slot_ratio_hadir (longgar)
                "pertemuan_penuh": total_hadir,
                "hadir_sebagian": total_sebagian,
                "sakit": total_sakit,
                "izin": total_izin,
                "alpha": total_alpha,
                "belum_diinput": total_belum_diinput,
                "pertemuan_ambang_terpenuhi": pertemuan_ambang,
                "total_pertemuan": len(sessions),
                "slot_hadir": slot_hadir_total,
                "slot_total": slot_total_semua,
                "persentase": attendance_pct,
                "basis_persen": ATURAN.basis_persen_kehadiran(),
                "min_slot_ratio_hadir": ATURAN.min_slot_ratio_hadir(),
                "data_lengkap": data_lengkap,
                "cakupan_bobot": cakupan,
                "slot_belum_diisi": ATURAN.slot_belum_diisi(),
                "detail": attendance_list
            },
            "akademik": {
                "nilai_rata_rata": avg_score,
                "nilai_rata_sederhana": round(
                    sum(x for x in session_scores if x is not None)
                    / max(1, len([x for x in session_scores if x is not None])), 1),
                "data_lengkap": data_lengkap,
                "cakupan_bobot": cakupan,
                "bobot_diperiksa": bobot_sesi,
                "grade": grade,
                "predikat": predikat,
                "status_kompetensi": status_kompetensi,
                "kesiapan_profesi": kesiapan_profesi,
                "indeks_kesiapan": indeks_kesiapan,
                "kompetensi": competency,
                "skor_sesi": session_scores
            },
            # MESIN DIAGNOSIS V3: satu paket dari sinyal nyata (radar terukur
            # + narasi dinamis + matriks karier deterministik). Skema kunci
            # lama tetap utuh; tambahan (radar_sumber, mesin) tidak merusak
            # konsumen lama karena konsumen hanya membaca kunci yang ia tahu.
            "ai_diagnosis": ai_diagnosis,
            "marketing": {
                "video": video_storyboard,
                "wa_text": wa_message
            }
        })

    # Class-level aggregates for Kaprodi Executive Suite
    total_mhs = len(student_records)
    if total_mhs == 0:
        raise ValueError("Tidak ada mahasiswa yang bisa dibaca dari tree kurikulum.")
    class_hadir_pct = round(sum(s["kehadiran"]["persentase"] for s in student_records) / total_mhs, 1)
    class_avg_score = round(sum(s["akademik"]["nilai_rata_rata"] for s in student_records) / total_mhs, 1)
    # FIX TAHAP B: pakai fungsi aturan yang sama (alpha>=2 ATAU hadir<75%).
    # Dulu di sini pakai "alpha>=2 atau nilai<70" sehingga KPI menulis 1 orang
    # padahal 9 mahasiswa lain juga berisiko.
    at_risk_list = [s for s in student_records if s["at_risk"]]
    # FIX BUG KPI: dulu "(nilai() or 0)" membuat ambang yang TIDAK dipakai
    # (nilai None) berubah jadi 0 -> kondisi "alpha >= 0" SELALU true; umpan
    # baliknya asimetris: "persentase < 0" tidak pernah true. Dua KPI ini jadi
    # salah arah begitu salah satu tipe aturan dihapus dari config/aturan.json.
    # Sekarang: peraturan mati -> KPI-nya juga mati (sama dengan at_risk_reasons).
    _aktif = ATURAN.at_risk_aktif()
    _ambang_alpha = at_risk_alpha_min()
    _ambang_hadir = at_risk_kehadiran_min()
    at_risk_alpha = [
        s for s in student_records
        if _aktif and _ambang_alpha is not None
        and s["kehadiran"]["alpha"] >= _ambang_alpha
    ]
    at_risk_kehadiran = [
        s for s in student_records
        if _aktif and _ambang_hadir is not None
        and s["kehadiran"]["persentase"] < _ambang_hadir
    ]
    
    # Grade distribution
    # FIX BELUM-DIINPUT: "Belum Lengkap" punya keranjang sendiri dan TIDAK
    # dilebur ke D - kalau dilebur, distribusi grade jadi bohong.
    grades_count = {"A": 0, "A-": 0, "B+": 0, "B": 0, "C": 0, "D": 0,
                    GRADE_BELUM_LENGKAP: 0}
    for s in student_records:
        g = s["akademik"]["grade"]
        if g in grades_count:
            grades_count[g] += 1
        else:
            g = g.split(" ")[0]
            if g in grades_count:
                grades_count[g] += 1
            else:
                grades_count["D"] += 1

    # Session-by-session attendance trends.
    # TAHAP E: satu pertemuan bisa punya beberapa slot absen, jadi "hadir"
    # perlu dibedakan dari "hadir sebagian". Ambang 50% slot (aturan.json)
    # menentukan siapa yang DIHITUNG hadir - angka ini yang dipakai persen.
    session_attendance_trend = []
    for sess in sessions:
        p_num = sess["pertemuan"]
        detail_p = [s["kehadiran"]["detail"][p_num - 1] for s in student_records]
        hadir_count = sum(1 for d in detail_p if d["status"] == "Hadir")
        sebagian_count = sum(1 for d in detail_p if d["status"] == "Hadir Sebagian")
        sakit_count = sum(1 for d in detail_p if d["status"] == "Sakit")
        izin_count = sum(1 for d in detail_p if d["status"] == "Izin")
        alpha_count = sum(1 for d in detail_p if d["status"] == "Alpha")
        belum_diinput_count = sum(1 for d in detail_p if d["status"] == "Belum Diinput")
        slot_total = detail_p[0]["slot_total"] if detail_p else 0
        slot_hadir = sum(d["slot_hadir"] for d in detail_p)
        memenuhi_ambang = sum(
            1 for d in detail_p if pertemuan_memenuhi_ambang(d["slot_hadir"], d["slot_total"])
        )
        session_attendance_trend.append({
            "pertemuan": p_num,
            "tanggal": sess["tanggal_display"],
            "topik": sess["topik"],
            "tipe": sess.get("tipe"),
            # Nama field mengikuti kosakata yang sama dengan catatan per mahasiswa
            # (lihat ringkas_kehadiran): hadir_penuh = SEMUA slot hadir,
            # memenuhi_ambang = >= min_slot_ratio_hadir. Dua angka ini berbeda dan
            # sengaja tidak disatukan.
            "hadir_penuh": hadir_count,
            "hadir_sebagian": sebagian_count,
            "sakit": sakit_count,
            "izin": izin_count,
            "alpha": alpha_count,
            "belum_diinput": belum_diinput_count,
            "slot_total": slot_total * total_mhs,
            "slot_hadir": slot_hadir,
            "memenuhi_ambang": memenuhi_ambang,
            "memenuhi_ambang_pct": (
                round((memenuhi_ambang / total_mhs) * 100, 1) if total_mhs else 0.0
            ),
        })

    # Lecturer and Curriculum Audit Data (for Kaprodi -> Dosen QA Report)
    total_sesi = len(sessions)
    # HONESTY: baris ini DULU menulis "16 / 16 Pertemuan (100%)" untuk SEMUA dosen.
    # Angka itu tidak berarti apa pun tentang dosen - ia cuma "jumlah pertemuan yang
    # terdefinisi di sesi.json". Tidak ada satu pun tempat di sistem ini yang
    # mencatat presensi dosen, jadi laporan QA tidak boleh mengklaim 100%.
    kehadiran_dosen = "Belum ada rekap presensi dosen (diisi manual oleh prodi)"
    tim_pengajar = []
    # FIX: tim pengajar TIDAK lagi disalin manual di sini. Diambil dari
    # course_info (yang bersumber dari config/identitas.json): dosen pengasuh
    # ke-1 = pengasuh utama, berikutnya = pendamping, lalu asisten dosen.
    for _i, _nama_dosen in enumerate(course_info["dosen_pengasuh"]):
        tim_pengajar.append({
            "nama": _nama_dosen,
            "peran": "Dosen Pengasuh Utama" if _i == 0 else "Dosen Pengasuh Pendamping",
            "kehadiran": kehadiran_dosen,
            "status": "Belum dinilai (instrumen penilaian dosen belum ada)"
        })
    tim_pengajar.append({
        "nama": course_info["asisten_dosen"],
        "peran": "Asisten Dosen & Instruktur Studio Lab LIKDA",
        "kehadiran": kehadiran_dosen,
        "status": "Belum dinilai (instrumen penilaian dosen belum ada)"
    })

    # TAHAP E: baris evaluasi RPS DIBANGUN dari sesi.json (16 pertemuan), bukan
    # 6 baris yang disalin manual. Topik asli dari RPS/portal, realisasi dihitung
    # dari kehadiran nyata.
    #
    # KOSAKATA JUJUR (dulu menyesatkan): field `skor_keselarasan` diganti
    # `keterlaksanaan_persen`. Isinya = persen kehadiran pertemuan tersebut,
    # BUKAN penilaian keselarasan materi vs RPS. Nama lama membuat pembaca mengira
    # ada audit mutu yang sebenarnya tidak pernah dilakukan.
    evaluasi_rps = []
    for d in session_attendance_trend:
        p = d["pertemuan"]
        if d["tipe"] in ("uts", "uas"):
            realisasi = "Evaluasi {0} semester diikuti {1} dari {2} mahasiswa.".format(
                "tengah" if d["tipe"] == "uts" else "akhir", d["memenuhi_ambang"], total_mhs
            )
        else:
            realisasi = (
                "Materi tersampaikan; {0} dari {1} mahasiswa memenuhi ambang kehadiran "
                "(hadir penuh {2}, hadir sebagian {3}, sisanya sakit/izin/alpha).".format(
                    d["memenuhi_ambang"], total_mhs, d["hadir_penuh"], d["hadir_sebagian"]
                )
            )
            if d.get("belum_diinput"):
                realisasi += " {0} mahasiswa presensinya BELUM DIINPUT.".format(
                    d["belum_diinput"]
                )
        evaluasi_rps.append({
            "sesi": p,
            "topik_rps": d["topik"],
            "realisasi_kelas": realisasi,
            "keterlaksanaan_persen": d["memenuhi_ambang_pct"],
            "cpmk": CPMK_PLACEHOLDER[(p - 1) % len(CPMK_PLACEHOLDER)],
            # Ditandai di DATA (bukan hanya di teks PDF) supaya tidak ada yang
            # mengira CPMK ini hasil penetapan prodi.
            "cpmk_status": "placeholder",
        })

    # FIX TAHAP B: hitung dari data, jangan diketik manual.
    # Dulu ditulis 96.0 dan kebetulan cocok, tapi diam-diam bohong begitu
    # satu skor berubah.
    dosen_audit = {
        "tim_pengajar": tim_pengajar,
        "evaluasi_kurikulum_rps": evaluasi_rps,
        "keterlaksanaan_rata_rata": (
            round(sum(e["keterlaksanaan_persen"] for e in evaluasi_rps) / len(evaluasi_rps), 1)
            if evaluasi_rps else 0.0
        ),
        # HONESTY: dulu di sini tertulis "Terakreditasi Sangat Baik / Memenuhi
        # Standar CPMK & CPL LAM Teknik". Itu klaim STATUS AKREDITASI yang tidak
        # pernah diverifikasi siapa pun dan tidak boleh dikarang oleh perangkat
        # lunak. Diganti pernyataan status yang benar-benar diketahui.
        "status_penilaian_rps": "belum_tersedia",
        "keterangan_status_rps": (
            "Penilaian keselarasan materi vs RPS/CPMK BELUM dilakukan - menunggu RPS "
            "resmi dan rubrik penilaian dari dosen. Angka 'keterlaksanaan' di atas "
            "adalah proksi persen kehadiran pertemuan, bukan penilaian mutu materi. "
            "Sistem ini tidak menyatakan status akreditasi program studi apa pun."
        ),
        "catatan_kaprodi": "Perkuliahan berjalan sangat disiplin dan interaktif. Metode asistensi studio di Lab LIKDA terbukti efektif mengangkat pemahaman mahasiswa. Disarankan untuk semester depan modul dapat ditambah pengenalan BIM Arsitektur (Revit) tingkat dasar."
    }

    dataset = {
        "metadata": {
            "sistem": "SIAK-KAPRODI ARSITEKTUR INTELLIGENCE",
            "versi": "2.6-KURIKULUM-BERTINGKAT",
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
            "build_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "target_port": 40404,
            "metodologi_nilai": (
                "Rata-rata TERBEBOT per pertemuan. Alpha bernilai 0 dan ikut dihitung. "
                "Nilai satu pertemuan = rata-rata nilai seluruh slot absennya. "
                "Pertemuan yang presensinya BELUM DIINPUT tidak dihitung 0 (dikeluarkan "
                "dari rata-rata dan bobotnya dinormalisasi ulang); grade ditahan "
                "'Belum Lengkap' sampai seluruh pertemuan terisi."
            ),
            "aturan_at_risk": ATURAN.teks_at_risk(),
            "aturan_slot_belum_diisi": ATURAN.slot_belum_diisi(),
            # --- TAHAP E: asal-usul data, supaya tidak ada yang menebak ---
            "sumber_data": "data/kurikulum/<PRODI>/<TAHUN_AJAR>/<SEMESTER>/<KUNCI_MK>/",
            "prodi": ctx.get("prodi"),
            "tahun_ajar": ctx.get("tahun_ajar"),
            "semester": ctx.get("semester"),
            "kunci_mk": ctx.get("kunci_mk"),
            "pertemuan_total": len(sessions),
            "slot_absen_total": KT.jumlah_slot(ctx.get("sesi_dokumen") or {}),
            "basis_persen_kehadiran": ATURAN.basis_persen_kehadiran(),
            "min_slot_ratio_hadir": ATURAN.min_slot_ratio_hadir(),
            "catatan_kehadiran": (
                "Persen kehadiran dihitung dari SLOT absen (slot_hadir/slot_total), bukan "
                "jumlah pertemuan. Ada DUA ukuran 'hadir' yang sengaja dipisah supaya tidak "
                "ada angka yang bisa dibaca dua cara: (1) `pertemuan_penuh` = pertemuan yang "
                "SEMUA slotnya hadir (ini yang dipakai rapor/PDF); (2) "
                "`pertemuan_ambang_terpenuhi` = pertemuan dengan slot hadir minimal {0:.0%} "
                "(ambang di config/aturan.json). Sisa statusnya (hadir sebagian, sakit, izin, "
                "alpha, belum diinput) ditampilkan apa adanya.".format(
                    ATURAN.min_slot_ratio_hadir()
                )
            ),
            "catatan_belum_diinput": (
                "Pertemuan yang baris slot absennya belum lengkap ditandai 'Belum "
                "Diinput' - bukan Alpha, tidak dinilai 0, dan grade mahasiswa "
                "ditahan 'Belum Lengkap' sampai data lengkap."
                if ATURAN.slot_belum_diisi() == "belum_diinput"
                else "Slot absen tanpa catatan dihitung sebagai Alpha (perilaku lama)."
            ),
            "catatan_nilai": (
                "NILAI PER PERTEMUAN MASIH SINTETIS (bukan input dosen). Ganti dengan "
                "data portal begitu tersedia; berkas sumber ditandai `sintetis: true`."
                if (ctx.get("nilai_dokumen") or {}).get("sintetis")
                else "Nilai berasal dari berkas nilai MK (bukan sintetis)."
            ),
            "metodologi_keterlaksanaan": (
                "keterlaksanaan_persen per pertemuan = persen kehadiran pertemuan tersebut "
                "(proksi keterlaksanaan), BUKAN penilaian keselarasan RPS. Field ini dulu "
                "bernama skor_keselarasan - nama itu menyesatkan dan sudah diganti."
            ),
            "catatan_cpmk": (
                "CPMK di laporan audit masih PLACEHOLDER (4 butir generik yang berulang) "
                "sampai RPS resmi disediakan. Setiap baris ditandai cpmk_status = "
                "'placeholder' supaya tidak dikira capaian resmi prodi."
            ),
            "catatan_status_rps": (
                "Sistem ini TIDAK menyatakan status akreditasi program studi. Klaim "
                "'Terakreditasi ... / Memenuhi Standar CPMK & CPL' yang dulu ada di data "
                "sudah dibuang karena tidak pernah diverifikasi."
            ),
        },
        "course": course_info,
        "sessions": sessions,
        "class_summary": {
            "total_mahasiswa": total_mhs,
            "rata_kehadiran": class_hadir_pct,
            "rata_nilai_studio": class_avg_score,
            "total_at_risk": len(at_risk_list),
            "at_risk_alpha": len(at_risk_alpha),
            "at_risk_kehadiran": len(at_risk_kehadiran),
            "at_risk_npm": [s["npm"] for s in at_risk_list],
            "grade_modus": max(grades_count.items(), key=lambda kv: kv[1])[0],
            "total_lulus": sum(1 for s in student_records if not s["at_risk"]
                               and s["akademik"]["grade"] != GRADE_BELUM_LENGKAP
                               and s["akademik"]["nilai_rata_rata"] >= 70),
            "total_belum_lengkap": sum(
                1 for s in student_records if not s["kehadiran"]["data_lengkap"]),
            "total_pertemuan_belum_diinput": sum(
                s["kehadiran"]["belum_diinput"] for s in student_records),
            "data_kelas_lengkap": all(
                s["kehadiran"]["data_lengkap"] for s in student_records),
            "distribusi_grade": grades_count,
            "tren_kehadiran_sesi": session_attendance_trend
        },
        "dosen_audit": dosen_audit,
        "students": student_records
    }

    return dataset

def bangun_dataset(kunci=None):
    """Bangun dataset akademik lengkap untuk satu MK dari tree kurikulum.

    `kunci=None` = MK aktif. Dipakai oleh main() (untuk MASTER) dan oleh
    process_input (untuk membangun katalog MK lain). Karena RNG-nya per NPM dan
    sumbernya berkas, hasilnya DETERMINISTIK: membangun dua kali menghasilkan
    angka yang sama persis (dibuktikan tests/test_rules_unchanged.py).
    """
    ctx = muat_kurikulum(kunci)
    nilai_per_npm = kelompokkan_nilai(ctx["nilai_dokumen"])
    return generate_student_profiles(
        ctx["mahasiswa"], ctx["sessions"], nilai_per_npm, ctx
    )


def _cetak_ringkas_dataset(path_data):
    """Ringkasan satu baris dari file dataset (di jalur kompilasi ATAU salinan)."""
    try:
        with open(path_data, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        print("Ringkasan Kelas:")
        print(" - Total Mahasiswa: {0}".format(
            dataset["class_summary"]["total_mahasiswa"]))
        print(" - Rata-rata Kehadiran: {0}%".format(
            dataset["class_summary"]["rata_kehadiran"]))
        print(" - Rata-rata Nilai Studio: {0}%".format(
            dataset["class_summary"]["rata_nilai_studio"]))
        print(" - Mahasiswa At-Risk: {0}".format(
            dataset["class_summary"]["total_at_risk"]))
    except (OSError, KeyError) as e:
        print(f"[PERINGATAN] ringkasan tidak terbaca: {e}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    paksa = "--compile-ulang" in sys.argv

    # --- JALUR SEGAR (Tangga B): stempel sama + snapshot ada = salin saja ---
    kunci, stamp_baru = stempel_kompilasi()
    snapshot = os.path.join(SNAPSHOT_DIR, "{0}.json".format(kunci))
    reg = muat_reg_stempel()
    if (not paksa
            and reg.get(kunci, {}).get("stamp") == stamp_baru
            and os.path.isfile(snapshot)
            and os.path.isfile(OUTPUT_JSON)):
        try:
            _salin_atomik(snapshot, OUTPUT_JSON)
            reg[kunci]["terakhir_dipakai"] = _waktu_seribuan()
            tulis_reg_stempel(reg)
            print("[STAMPEL] master '{0}' masih SEGAR (stempel {1})".format(
                kunci, stamp_baru[:10]))
            print("[STAMPEL] master = salinan bit-identik snapshot"
                  " '{0}' - tidak ada kompilasi".format(
                      os.path.relpath(snapshot, BASE_DIR)))
            print("Dataset berhasil disimpan ke: {0}".format(OUTPUT_JSON))
            _cetak_ringkas_dataset(OUTPUT_JSON)
            return
        except OSError as e:
            print("[PERINGATAN] salinan snapshot gagal ({0}) - kompilasi "
                  "ulang penuh".format(e))

    if paksa:
        print("[STAMPEL] --compile-ulang: kompilasi penuh dipaksa.")

    print("Membaca kurikulum dari tree (data/kurikulum/...):")
    ctx = muat_kurikulum()
    print("  - prodi       : {0}".format(ctx["prodi"]))
    print("  - mata kuliah : {0} ({1})".format(
        ctx["penawaran"].get("nama_mk"), ctx["kunci_mk"]))
    print("  - periode     : {0} {1}".format(ctx["semester"], ctx["tahun_ajar"]))
    print("  - pertemuan   : {0} | slot absen {1}".format(
        len(ctx["sessions"]), KT.jumlah_slot(ctx["sesi_dokumen"])))
    print("  - mahasiswa   : {0}".format(len(ctx["mahasiswa"])))

    print("Mengompilasi dataset akademik (10 matriks karier per mahasiswa)...")
    dataset = bangun_dataset()

    # DEBUG: Check at_risk values before dump
    students = dataset.get("students", [])
    if students:
        print(f"DEBUG: Before dump, first student at_risk = {repr(students[0].get('at_risk'))}")

    # newline="\n" WAJIB: json.dump di Windows default-nya menulis CRLF, sehingga
    # academic_data.json berubah byte-nya setiap regenerate walau isinya sama.
    # FIX BUG RACE: dulu open(path,"w") truncate dulu baru dump - endpoint baca
    # bersamaan bisa menangkap file terpotong (JSONDecodeError -> 500 sesaat).
    # Sekarang tulis .tmp lalu os.replace() atomik, pola sama dengan TAHAP A.
    try:
        from process_input import atomic_write_json
        atomic_write_json(OUTPUT_JSON, dataset)
    except ImportError:
        # Fallback jarang dipakai: proses_input tidak ada di sys.path.
        with open(OUTPUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

    # --- Simpan SNAPSHOT + STEMPEL (Tangga B) --------------------------------
    # Tulisan master di atas atomik; snapshot identik dari dataset yang sama.
    # Pindah-MK kembali ke sini = salinan, bukan kompilasi 12 detik.
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    _salin_atomik(OUTPUT_JSON, snapshot)
    reg[kunci] = {
        "stamp": stamp_baru,
        "snapshot": os.path.relpath(snapshot, BASE_DIR).replace("\\", "/"),
        "dibuat": _waktu_seribuan(),
    }
    tulis_reg_stempel(reg)
    print("[STAMPEL] '{0}' dikompilasi & snapshot disimpan (stempel {1})".format(
        kunci, stamp_baru[:10]))

    print("Dataset berhasil disimpan ke: {0}".format(OUTPUT_JSON))
    _cetak_ringkas_dataset(OUTPUT_JSON)

    # FIX TAHAP C-5: file ini hanya menulis data MASTER. Tanpa langkah berikut,
    # katalog di data/courses/ bisa tertinggal satu versi di belakang master -
    # dan sekali "ganti mata kuliah" master ikut mundur tanpa pesan error.
    # TAHAP E: katalog untuk SEMUA MK dibangun ulang dari tree (bukan hanya yang
    # aktif), supaya tidak ada lagi katalog yang memakai aturan lama.
    try:
        from process_input import sinkronkan_katalog
        sinkronkan_katalog()
    except Exception as e:  # noqa: BLE001
        print(f"[PERINGATAN] Katalog mata kuliah tidak disinkronkan: {e}")
        print("            Jalankan: python scripts\\process_input.py --sync-katalog")

if __name__ == "__main__":
    main()

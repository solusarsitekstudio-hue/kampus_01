"""CLI subsistem impor.

Contoh:

    python -m scripts.impor.cli pindai
    python -m scripts.impor.cli impor --folder input/inbox
    python -m scripts.impor.cli impor --berkas "D:/unduhan/nilai.xlsx" --terapkan
    python -m scripts.impor.cli tinjau data/_staging/20261020-101500_impor_nilai_...
    python -m scripts.impor.cli terima data/_staging/... --mode gabung
    python -m scripts.impor.cli modul "input/inbox/RPS.pdf"

Semua perintah menolak menulis ke tree kecuali `impor --terapkan` dan
`terima`, dan keduanya selalu membackup dulu.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

# --- bootstrap path: scripts/ harus ada di sys.path untuk kurikulum_tree ---
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCRIPTS = os.path.join(_ROOT, "scripts")
for _p in (_ROOT, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kurikulum_tree as KT  # noqa: E402

from scripts.impor import deteksi as deteksi_modul  # noqa: E402
from scripts.impor import dokumen as dokumen_modul  # noqa: E402
from scripts.impor import nilai_impor  # noqa: E402
from scripts.impor import profil as profil_modul  # noqa: E402
from scripts.impor import ai_engine  # noqa: E402
from scripts.impor import analisis_mk  # noqa: E402
from scripts.impor import portal as portal_modul  # noqa: E402

BASE = _ROOT
CONFIG_IMPOR = os.path.join(BASE, "config", "impor")
INBOX = os.path.join(BASE, "input", "inbox")
RAW = os.path.join(BASE, "input", "raw")
STAGING = os.path.join(BASE, "data", "_staging")
BACKUP = os.path.join(BASE, "data", "_backup")
IDENTITAS = os.path.join(BASE, "config", "identitas.json")


# --------------------------------------------------------------------- util
def _cetak(teks=""):
    print(teks)


def _gagal(pesan, kode=2):
    _cetak("[GAGAL] " + pesan)
    return kode


def _baca_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def konteks_default():
    """Tebak konteks dari config/identitas.json (bukan dari menebak folder)."""
    try:
        identitas = _baca_json(IDENTITAS)
    except (OSError, json.JSONDecodeError):
        return {}
    institusi = identitas.get("institusi") or {}
    kunci = identitas.get("mata_kuliah_aktif")
    mk = (identitas.get("mata_kuliah") or {}).get(kunci) or {}
    hasil = {
        "prodi": institusi.get("prodi") or "",
        "kunci_mk": kunci or "",
    }
    semester_teks = str(mk.get("semester") or "")
    if semester_teks:
        cocok = re.search(r"(\d{4})\s*/\s*(\d{4})", semester_teks)
        if cocok:
            hasil["tahun_ajar"] = "{0}/{1}".format(cocok.group(1), cocok.group(2))
        if "genap" in semester_teks.lower():
            hasil["semester"] = "GENAP"
        elif "ganjil" in semester_teks.lower():
            hasil["semester"] = "GANJIL"
    return {k: v for k, v in hasil.items() if v}


def resolve_konteks(args):
    """Konteks akhir: CLI > identitas.json. Gagal kalau masih tidak lengkap."""
    dasar = konteks_default()
    hasil = dict(dasar)
    for nama in ("prodi", "tahun_ajar", "semester", "kunci_mk"):
        nilai = getattr(args, nama, None)
        if nilai:
            hasil[nama] = nilai
    if hasil.get("tahun_ajar"):
        hasil["tahun_ajar"] = KT.norm_tahun_ajar(hasil["tahun_ajar"])
    if hasil.get("semester"):
        hasil["semester"] = KT.slug_semester(hasil["semester"])

    if getattr(args, "folder_mk", None):
        folder_mk = os.path.abspath(args.folder_mk)
        folder_mhs = os.path.abspath(args.mahasiswa) if getattr(args, "mahasiswa", None) \
            else os.path.join(os.path.dirname(os.path.dirname(folder_mk)), "mahasiswa.json")
        return hasil, folder_mk, folder_mhs

    hilang = [k for k in ("prodi", "tahun_ajar", "semester", "kunci_mk") if not hasil.get(k)]
    if hilang:
        raise SystemExit(_gagal(
            "konteks belum lengkap: {0}. Isi lewat --prodi/--tahun-ajar/--semester/"
            "--kunci-mk (atau --folder-mk).".format(", ".join(hilang))))

    folder_mk = KT.path_mk(hasil["prodi"], hasil["tahun_ajar"], hasil["semester"], hasil["kunci_mk"])
    folder_mhs = KT.path_mahasiswa(hasil["prodi"])
    if not os.path.isdir(folder_mk):
        raise SystemExit(_gagal("folder MK tidak ditemukan: {0}".format(folder_mk)))
    if not os.path.isfile(folder_mhs):
        raise SystemExit(_gagal("mahasiswa.json tidak ditemukan: {0}".format(folder_mhs)))
    return hasil, folder_mk, folder_mhs


def muat_profil_tabel():
    """Hanya profil yang punya bagian 'kolom' (profil modul dilewati)."""
    semua = profil_modul.muat_profil(CONFIG_IMPOR)
    return [p for p in semua if isinstance(p.get("kolom"), dict) and p["kolom"]]


def arsipkan_sumber(paths, konteks, catatan=""):
    """Salin berkas asli ke input/raw/<stamp>/ + meta.json (jejak audit)."""
    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = os.path.join(RAW, stempel)
    os.makedirs(folder, exist_ok=True)
    meta = {
        "waktu": datetime.now().isoformat(timespec="seconds"),
        "konteks": konteks,
        "catatan": catatan,
        "berkas": [],
    }
    for path in paths:
        tujuan = os.path.join(folder, os.path.basename(path))
        if os.path.abspath(path) != os.path.abspath(tujuan):
            shutil.copy2(path, tujuan)
        meta["berkas"].append({
            "nama": os.path.basename(path),
            "ukuran": os.path.getsize(path),
            "sha256": nilai_impor.sha256(path),
            "jenis": deteksi_modul.deteksi(path)["jenis"],
        })
    with open(os.path.join(folder, "meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return folder


def _format_ringkasan(usulan):
    r = usulan.get("ringkasan") or {}
    b = usulan.get("beda") or {}
    k = usulan.get("konteks") or {}
    _cetak("  Konteks      : {0} / {1} / {2} / {3}".format(
        k.get("prodi") or "-", k.get("tahun_ajar") or "-",
        k.get("semester") or "-", usulan.get("kunci_mk") or "-"))
    _cetak("  Profil       : {0}".format(", ".join(usulan.get("profil") or ["-"])))
    _cetak("  Baris valid  : {0} (NPM unik: {1})".format(r.get("baris", 0), r.get("npm_unik", 0)))
    _cetak("  Pertemuan    : {0}".format(r.get("pertemuan") or "-"))
    _cetak("  Status       : {0}".format(r.get("status") or "-"))
    _cetak("  Skor         : {0} .. {1}".format(r.get("skor_min"), r.get("skor_maks")))
    _cetak("  Beda vs tree : +{0} baru, {1} berubah, {2} sama, {3} hanya di data lama".format(
        b.get("baru", 0), b.get("berubah", 0), b.get("sama", 0), b.get("hanya_di_data_lama", 0)))


def _cetak_masalah(usulan, maks=25):
    masalah = usulan.get("masalah") or []
    if not masalah:
        _cetak("  Masalah      : tidak ada")
        return
    _cetak("  Masalah      : {0}".format(len(masalah)))
    for m in masalah[:maks]:
        _cetak("    - " + m)
    if len(masalah) > maks:
        _cetak("    ... dan {0} lainnya".format(len(masalah) - maks))


# ----------------------------------------------------------------- perintah
def cmd_pindai(args):
    folder = os.path.abspath(args.folder or INBOX)
    if not os.path.isdir(folder):
        return _gagal("folder tidak ditemukan: {0}".format(folder))
    hasil = deteksi_modul.pindai(folder)
    if not hasil:
        _cetak("Tidak ada berkas di {0}".format(folder))
        return 0
    _cetak("{0:<40} {1:<12} {2:<10} {3}".format("BERKAS", "JENIS", "UKURAN", "STATUS"))
    _cetak("-" * 90)
    for h in hasil:
        status = "siap" if h["bisa_dibaca"] else "TIDAK DIDUKUNG: " + h["alasan"]
        _cetak("{0:<40} {1:<12} {2:<10} {3}".format(
            h["berkas"][:40], h["jenis"], h["ukuran"], status))
    _cetak("")
    _cetak("Catatan: berkas .xls lama dan .doc lama tidak dibaca (jangan ditebak). "
           "Simpan ulang sebagai .xlsx/.docx.")
    return 0


def _kumpulkan_berkas(args):
    if args.berkas:
        paths = [os.path.abspath(p) for p in args.berkas]
    else:
        folder = os.path.abspath(args.folder or INBOX)
        paths = [os.path.join(folder, n) for n in sorted(os.listdir(folder))
                 if os.path.isfile(os.path.join(folder, n))] if os.path.isdir(folder) else []
    if not paths:
        raise SystemExit(_gagal("tidak ada berkas untuk diimpor (folder: {0})".format(
            args.folder or INBOX)))

    terpilih = []
    ditolak = []
    for p in paths:
        info = deteksi_modul.deteksi(p)
        if info["jenis"] in ("xlsx", "csv", "html"):
            terpilih.append((p, info["jenis"]))
        else:
            ditolak.append("{0} ({1})".format(os.path.basename(p), info["alasan"]))
    for d in ditolak:
        _cetak("[LEWAT] " + d)
    if not terpilih:
        raise SystemExit(_gagal("tidak ada berkas tabel yang bisa dibaca"))
    return terpilih


def cmd_impor(args):
    konteks, folder_mk, folder_mhs = resolve_konteks(args)
    berkas = _kumpulkan_berkas(args)
    profil_list = muat_profil_tabel()

    if args.profil:
        profil_list = [p for p in profil_list if p.get("nama") == args.profil]
        if not profil_list:
            return _gagal("profil {0!r} tidak ditemukan di {1}".format(args.profil, CONFIG_IMPOR))

    _cetak("Membaca {0} berkas tabel...".format(len(berkas)))
    usulan = nilai_impor.bangun_usulan(
        berkas, folder_mk=folder_mk, folder_mahasiswa=folder_mhs,
        profil_list=profil_list,
        sumber_meta=[{"berkas": os.path.basename(b), "jenis": j, "asal": "cli"} for b, j in berkas],
    )

    usulan["konteks"] = konteks
    path = nilai_impor.tulis_staging(usulan, STAGING)
    arsip = arsipkan_sumber([b for b, _ in berkas], konteks, catatan="impor nilai")

    _cetak("")
    _format_ringkasan(usulan)
    _cetak("  Arsip sumber : {0}".format(arsip))
    _cetak("  Staging      : {0}".format(path))
    _cetak("")
    _cetak_masalah(usulan)

    if usulan["masalah"]:
        _cetak("")
        _cetak("TIDAK ditulis ke tree. Perbaiki sumber/profil, lalu ulangi.")
        return 1

    if not args.terapkan:
        _cetak("")
        _cetak("Dry-run selesai. Untuk menulis ke tree:")
        _cetak("  python -m scripts.impor.cli terima \"{0}\"".format(path))
        return 0

    hasil = nilai_impor.terapkan(usulan, folder_mk, BACKUP, mode=args.mode,
                                 paksa=getattr(args, "paksa", False))
    _cetak("")
    _cetak("[OK] nilai.json ditulis: {0}".format(hasil["path"]))
    _cetak("     mode={0}, baris={1}, sha256={2}".format(
        hasil["mode"], hasil["jumlah_baris"], hasil["sha256_baru"][:16] + "..."))
    _cetak("Langkah berikutnya:  python scripts\\parse_data.py")
    return 0


def cmd_tinjau(args):
    usulan, path = nilai_impor.muat_usulan(args.staging)
    _cetak("Usulan : {0}".format(path))
    _cetak("Dibuat : {0}".format(usulan.get("dibuat")))
    _format_ringkasan(usulan)
    _cetak_masalah(usulan)

    beda = usulan.get("beda") or {}
    contoh = beda.get("contoh_perubahan") or []
    if contoh:
        _cetak("")
        _cetak("Contoh perubahan:")
        for c in contoh:
            _cetak("  npm {0} P{1}.{2}: {3}/{4} -> {5}/{6}".format(
                c["npm"], c["pertemuan"], c["slot"],
                c["lama"]["status"], c["lama"]["skor"],
                c["baru"]["status"], c["baru"]["skor"]))
    hanya_lama = beda.get("contoh_hanya_lama") or []
    if hanya_lama:
        _cetak("")
        _cetak("Ada di data lama tapi tidak diimpor (mode 'gabung' mempertahankannya):")
        for c in hanya_lama:
            _cetak("  npm {0} P{1}.{2}".format(c["npm"], c["pertemuan"], c["slot"]))
    _cetak("")
    _cetak("Terima dengan:  python -m scripts.impor.cli terima \"{0}\"".format(path))
    return 0 if not usulan.get("masalah") else 1


def cmd_terima(args):
    usulan, path = nilai_impor.muat_usulan(args.staging)
    folder_mk = args.folder_mk or usulan.get("folder_mk")
    if not folder_mk or not os.path.isdir(folder_mk):
        return _gagal("folder MK tidak diketahui. Isi --folder-mk.")
    try:
        hasil = nilai_impor.terapkan(usulan, folder_mk, BACKUP, mode=args.mode,
                                     paksa=getattr(args, "paksa", False))
    except ValueError as exc:
        return _gagal(str(exc))
    _cetak("[OK] nilai.json ditulis: {0}".format(hasil["path"]))
    _cetak("     mode={0}, baris={1}".format(hasil["mode"], hasil["jumlah_baris"]))
    _cetak("     backup : {0}".format(os.path.join(BACKUP, "impor_nilai_*")))
    _cetak("Langkah berikutnya:  python scripts\\parse_data.py")
    return 0


def cmd_modul(args):
    path = os.path.abspath(args.berkas)
    info = deteksi_modul.deteksi(path)
    if not info["bisa_dibaca"]:
        return _gagal("berkas tidak bisa dibaca: {0}".format(info["alasan"]))
    if info["jenis"] not in ("pdf", "docx", "gambar"):
        return _gagal("bukan dokumen modul: {0}".format(info["jenis"]))

    _cetak("Membaca {0} ({1})...".format(os.path.basename(path), info["jenis"]))
    hasil = dokumen_modul.baca(path, info["jenis"])
    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = os.path.splitext(os.path.basename(path))[0][:40]
    folder = os.path.join(STAGING, "{0}_modul_{1}".format(stempel, label))
    os.makedirs(folder, exist_ok=True)
    path_hasil = os.path.join(folder, "ekstraksi.json")
    nilai_impor.tulis_json_atomik(path_hasil, hasil)

    _cetak("  Halaman/bagian : {0}".format(len(hasil["halaman"])))
    _cetak("  Karakter       : {0}".format(hasil["meta"].get("jumlah_karakter", 0)))
    _cetak("  Perlu OCR      : {0}".format("YA" if hasil["ocr_dibutuhkan"] else "tidak"))
    _cetak("  Hasil          : {0}".format(path_hasil))
    if hasil["ocr_dibutuhkan"]:
        _cetak("")
        _cetak("PDF/gambar ini tidak punya text layer. Jangan diisi manual dengan tebakan;")
        _cetak("gunakan: python -m scripts.impor.cli usul \"{0}\" --gambar".format(path))
    return 0


# -------------------------------------------------------------------- main
def cmd_portal(args):
    _cetak("Membuka browser. Login MANUAL - sandi tidak disimpan skrip ini.")
    _cetak("Sesi browser disimpan di: {0}".format(
        os.path.abspath(args.profil or portal_modul.PROFIL_BAWAAN)))
    try:
        hasil = portal_modul.tangkap(
            args.url, RAW, INBOX,
            jumlah_halaman=args.halaman,
            profil_dir=os.path.abspath(args.profil or portal_modul.PROFIL_BAWAAN),
            format_=args.format,
        )
    except Exception as exc:
        return _gagal("{0}: {1}".format(type(exc).__name__, exc))

    _cetak("")
    _cetak("Arsip HTML/screenshot : {0}".format(hasil["arsip"]))
    _cetak("Berkas masuk inbox    : {0}".format(INBOX))
    ada_tabel = 0
    for h in hasil["halaman"]:
        _cetak("  {0}: {1} tabel".format(h["label"], len(h["tabel"])))
        for t in h["tabel"]:
            ada_tabel += 1
            _cetak("    - {0} ({1} baris)".format(os.path.basename(t["path"]), t["baris"]))
        if h["catatan"]:
            _cetak("    catatan: {0}".format(h["catatan"]))
    _cetak("")
    if not ada_tabel:
        _cetak("Tidak ada tabel yang bisa diekstrak. Halaman disimpan sebagai HTML +")
        _cetak("screenshot; jangan diisi manual dengan tebakan. Kalau tabelnya berupa")
        _cetak("gambar, gunakan: python -m scripts.impor.cli usul <png> --gambar")
        return 1
    _cetak("Langkah berikutnya (dry-run):")
    _cetak("  python -m scripts.impor.cli impor --folder input/inbox")
    return 0


def cmd_status_ai(args):
    info = ai_engine.status()
    _cetak("Engine   : {0}".format(info.get("path") or "(tidak ditemukan)"))
    _cetak("Siap     : {0}".format("YA" if info["siap"] else "TIDAK"))
    _cetak("Kunci    : {0}".format(info.get("jumlah_kunci", 0)))
    if info.get("sebab"):
        _cetak("Sebab    : {0}".format(info["sebab"]))
    return 0 if info["siap"] else 1


def cmd_usul(args):
    path = os.path.abspath(args.berkas)
    info = deteksi_modul.deteksi(path)
    if not info["bisa_dibaca"]:
        return _gagal("berkas tidak bisa dibaca: {0}".format(info["alasan"]))

    konteks, folder_mk, _folder_mhs = resolve_konteks(args)

    if args.gambar or info["jenis"] == "gambar":
        hasil = dokumen_modul.baca_gambar(path)
    else:
        hasil = dokumen_modul.baca(path, info["jenis"])

    if hasil["ocr_dibutuhkan"] and not (args.gambar or info["jenis"] == "gambar"):
        return _gagal(
            "dokumen tanpa text layer. Jalankan ulang dengan --gambar agar AI "
            "membacanya sebagai gambar (hasilnya ditandai OCR).")

    hasil["sha256"] = nilai_impor.sha256(path)
    profil_modul_cfg = next(
        (p for p in profil_modul.muat_profil(CONFIG_IMPOR) if p.get("penanda")), None)

    _cetak("Menganalisis {0} dengan engine Gemini...".format(os.path.basename(path)))
    usulan = analisis_mk.analisis(
        hasil, konteks=konteks, profil_modul=profil_modul_cfg,
        gambar=path if (args.gambar or info["jenis"] == "gambar") else None,
    )
    usulan["konteks"]["kunci_mk"] = konteks.get("kunci_mk")
    path_usulan = analisis_mk.tulis_staging(usulan, STAGING)
    arsip = arsipkan_sumber([path], konteks, catatan="analisis modul")

    _cetak("")
    _cetak("  Sumber       : {0}".format(usulan["sumber"].get("berkas")))
    _cetak("  Halaman      : {0}".format(usulan["sumber"].get("jumlah_halaman")))
    _cetak("  OCR          : {0}".format("ya" if usulan["sumber"].get("ocr") else "tidak"))
    _cetak("  Model        : {0}".format(usulan["sumber"].get("model")))
    _cetak("  Pertemuan    : {0} dari 16".format(len(usulan["pertemuan"])))
    _cetak("  CPMK         : {0}".format(len(usulan["cpmk"])))
    _cetak("  Topik contoh : {0}".format(
        (usulan["pertemuan"][0].get("topik") if usulan["pertemuan"] else "-")))
    _cetak("  Arsip sumber : {0}".format(arsip))
    _cetak("  Staging      : {0}".format(path_usulan))
    _cetak("")
    _cetak_masalah(usulan)

    if usulan["masalah"]:
        _cetak("")
        _cetak("TIDAK bisa diterapkan sebelum masalah di atas selesai.")
        _cetak("Periksa manual: buka berkas staging, sunting jika perlu (status tetap 'tebakan').")
        return 1
    _cetak("")
    _cetak("Tinjau lalu terima dengan:")
    _cetak("  python -m scripts.impor.cli terima-sesi \"{0}\"".format(path_usulan))
    return 0


def cmd_terima_sesi(args):
    usulan, path = analisis_mk.muat_usulan(args.staging)
    folder_mk = args.folder_mk
    if not folder_mk:
        konteks = usulan.get("konteks") or {}
        try:
            _k, folder_mk, _m = resolve_konteks(argparse.Namespace(
                prodi=konteks.get("prodi"), tahun_ajar=konteks.get("tahun_ajar"),
                semester=konteks.get("semester"), kunci_mk=konteks.get("kunci_mk"),
                folder_mk=None, mahasiswa=None,
            ))
        except SystemExit:
            return _gagal("folder MK tidak bisa ditentukan. Isi --folder-mk.")
    try:
        hasil = analisis_mk.terapkan(usulan, folder_mk, BACKUP, ikut_bobot=args.bobot)
    except (ValueError, FileNotFoundError) as exc:
        return _gagal(str(exc))
    _cetak("[OK] sesi.json diperbarui: {0}".format(hasil["path"]))
    _cetak("     pertemuan diubah: {0}".format(hasil["pertemuan_diubah"]))
    _cetak("     backup          : {0}".format(hasil["backup"]))
    _cetak("Langkah berikutnya:  python scripts\\parse_data.py")
    return 0


def bangun_parser():
    p = argparse.ArgumentParser(
        prog="python -m scripts.impor.cli",
        description="Impor berkas mentah (portal/Excel/CSV/HTML) dan modul PDF/DOCX.",
    )
    sub = p.add_subparsers(dest="perintah", required=True)

    def tambah_konteks(sp):
        sp.add_argument("--prodi", help="contoh: ARSITEKTUR")
        sp.add_argument("--tahun-ajar", dest="tahun_ajar", help="contoh: 2025/2026")
        sp.add_argument("--semester", help="GANJIL atau GENAP")
        sp.add_argument("--kunci-mk", dest="kunci_mk", help="nama folder MK")
        sp.add_argument("--folder-mk", dest="folder_mk", help="jalur folder MK langsung")
        sp.add_argument("--mahasiswa", help="jalur mahasiswa.json (opsional)")

    sp = sub.add_parser("pindai", help="lihat isi folder inbox")
    sp.add_argument("--folder", help="default: input/inbox")
    sp.set_defaults(func=cmd_pindai)

    sp = sub.add_parser("impor", help="impor tabel nilai (dry-run kecuali --terapkan)")
    tambah_konteks(sp)
    sp.add_argument("--berkas", nargs="+", help="satu atau lebih berkas")
    sp.add_argument("--folder", help="default: input/inbox")
    sp.add_argument("--profil", help="nama profil di config/impor")
    sp.add_argument("--terapkan", action="store_true", help="langsung tulis ke tree")
    sp.add_argument("--mode", choices=["gabung", "ganti"], default="gabung")
    sp.add_argument("--paksa", action="store_true",
                    help="izinkan menimpa nilai.json yang sudah diverifikasi manusia")
    sp.set_defaults(func=cmd_impor)

    sp = sub.add_parser("tinjau", help="lihat isi staging usulan")
    sp.add_argument("staging")
    sp.set_defaults(func=cmd_tinjau)

    sp = sub.add_parser("terima", help="tulis usulan yang sudah ditinjau ke tree")
    sp.add_argument("staging")
    sp.add_argument("--folder-mk", dest="folder_mk")
    sp.add_argument("--mode", choices=["gabung", "ganti"], default="gabung")
    sp.add_argument("--paksa", action="store_true",
                    help="izinkan menimpa nilai.json yang sudah diverifikasi manusia")
    sp.set_defaults(func=cmd_terima)

    sp = sub.add_parser("modul", help="ekstrak teks modul PDF/DOCX")
    sp.add_argument("berkas")
    sp.set_defaults(func=cmd_modul)

    sp = sub.add_parser("status-ai", help="cek kesiapan engine Gemini rotary")
    sp.set_defaults(func=cmd_status_ai)

    sp = sub.add_parser("portal", help="tangkap tabel portal (login manual di browser)")
    sp.add_argument("--url", required=True, help="halaman awal portal")
    sp.add_argument("--halaman", type=int, default=1, help="jumlah halaman yang ditangkap")
    sp.add_argument("--format", choices=["csv", "xlsx"], default="csv")
    sp.add_argument("--profil", help="folder profil browser (default: input/.session/chromium)")
    sp.set_defaults(func=cmd_portal)

    sp = sub.add_parser("usul", help="analisis modul/RPS dengan AI -> staging (belum menulis)")
    tambah_konteks(sp)
    sp.add_argument("berkas")
    sp.add_argument("--gambar", action="store_true",
                    help="paksa baca sebagai gambar (screenshot/foto) via AI vision")
    sp.set_defaults(func=cmd_usul)

    sp = sub.add_parser("terima-sesi", help="tulis usulan topik hasil AI ke sesi.json")
    sp.add_argument("staging")
    sp.add_argument("--folder-mk", dest="folder_mk")
    sp.add_argument("--bobot", action="store_true", help="ikut menulis bobot usulan")
    sp.set_defaults(func=cmd_terima_sesi)

    return p


def main(argv=None):
    args = bangun_parser().parse_args(argv)
    try:
        return args.func(args)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    except Exception as exc:  # fail-closed: tampilkan sebab, jangan traceback
        return _gagal("{0}: {1}".format(type(exc).__name__, exc))


if __name__ == "__main__":
    sys.exit(main())

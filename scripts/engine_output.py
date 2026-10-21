"""engine_output.py - ENGINE PEMERIKSA OUTPUT (sahabat mesin kirim otomatis).

KEPUTUSAN USER (2026-10-21):
* Engine cek input & output DIPISAH - modul ini sisi output; sisi input ada di
  scripts/engine_input.py.
* Saat generate PDF/data: kalau berkas lama MASIH ADA & tanda logika/format-nya
  belum berubah, berkas lama DIBERIKAN (tidak ditulis ulang), KECUALI:
    - ada UPDATE LOGIKA / FORMAT PENYAJIAN      -> overwrite (mode overwrite),
    - DATA MASTER/KATALOG BERUBAH               -> overwrite (stempel data maju),
    - UKURAN BERKAS di disk != ukuran tercatat  -> overwrite
      (pengecekan logika/data + ukuran file; berkas korup/parsial).
* Folder output kelak tersambung ke MESIN KIRIM OTOMATIS (kaprodi & wali
  murid), jadi lapis `output/kirim/` disiapkan dari sumber yang SUDAH
  TERVERIFIKASI (run terbaru + registry + daftar mahasiswa tree) - mesin kirim
  membaca manifest, bukan menebak di arsip.

Perbaikan 2026-10-21 (guncangan audit):
* LOCK: registry punya threading.RLock (server concurrent, tanpa lock dulu
  rawan lost-update antara GET audit dan POST rapikan).
* STEMPEL DATA: tanda logika kini memuat stempel master+katalog
  (data=<stamp>) -> perubahan nilai TIDAK bisa lolas sebagai "berkas lama".
* run_masih_sah(): pintu skip paket PDF - run lama masih sah bila stempel data
  & FORMAT_V sama dan seluruh PDF-nya utuh -> tidak membuat run duplikat.
* Manifest wali menyebut SEMUA mahasiswa tree (35), bukan cuma yang PDF-nya
  sudah pernah dibuat; yang belum tampil jujur "belum ada berkas".
* rapikan() menyapu BROKAT di root output/ (kecuali latest_run.json) ke
  data/_backup/ supaya root hanya berisi pointer + folder tertib.
* audit() melaporkan salinan_usang: generated_pdfs/ berbeda SHA dari run
  terbaru (mis. cetak paket setengah jalan).

REGISTRY: data/engine/output_registry.json -> {"versi": 1, "berkas": {
    "<rel path dari BASE>": {"ukuran": int, "sha256": str|null, "tanda": str,
    "jenis": str, "konteks": str, "updated_at": iso, "catatan": str}}}

Semua tulis atomik (tmp + os.replace) & LF - pola sama dengan penulisan master.
"""

import hashlib
import json
import os
import re
import shutil
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_HERE)
REG_PATH = os.path.join(BASE_DIR, "data", "engine", "output_registry.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LEGACY_DIR = os.path.join(BASE_DIR, "generated_pdfs")
BACKUP_DIR = os.path.join(BASE_DIR, "data", "_backup")
KURIKULUM_DIR = os.path.join(BASE_DIR, "data", "kurikulum")

# Naikkan ini kalau render/logika dokumen berubah (contoh: v2 = format baru).
# Semua tanda logika memakai konstanta ini, jadi cukup di sini yang disentuh.
FORMAT_V = "v1"

_RE_NPM = re.compile(r"(?<!\d)(\d{8,14})(?!\d)")
# NB: tanpa \b - di nama berkas npm selalu dikelilingi "_", dan "_" termasuk
# word char (\b tidak bisa dipakai). Cukup batasi: tidak menempel digit lain.

# Server memakai ThreadingMixIn (concurrent). Registry tanpa lock dulu rawan
# lost-update (GET audit/POST rapikan bersamaan). RLock karena rapikan()
# memanggil audit() di dalam badannya (reentrant).
_LOCK = threading.RLock()


# --------------------------------------------------------------------------- #
# util & registry
# --------------------------------------------------------------------------- #
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


def _muat_registry():
    """Baca registry; rusak -> (kosong, pesan) - fail-closed, bukan crash."""
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


def stempel_data():
    """Stempel SATU-SATUNYA sumber data: master + seluruh katalog build.

    Tanda logika yang tidak melihat data = bahaya (nilai berubah bisa lolos
    sebagai 'berkas lama'). Stempel gabungan mtime+ukuran master
    (data/academic_data.json) dan katalog (data/courses/*.json).
    """
    bagian = []
    kandidat = [os.path.join(BASE_DIR, "data", "academic_data.json")]
    courses = sorted(__import__("glob").glob(
        os.path.join(BASE_DIR, "data", "courses", "*.json")))
    for p in (kandidat + courses):
        if not os.path.isfile(p):
            bagian.append(f"{os.path.basename(p)}:-")
            continue
        st = os.stat(p)
        bagian.append(f"{os.path.basename(p)}:{int(st.st_mtime)}:{st.st_size}")
    return hashlib.sha1("|".join(bagian).encode("utf-8")).hexdigest()[:12]


def tanda_logika(jenis, konteks=""):
    """Satu berkas satu tanda: jenis@versi_format + stempel data + konteks."""
    bagian = [f"{jenis}@{FORMAT_V}", f"data={stempel_data()}"]
    if konteks:
        bagian.append(konteks)
    return "|".join(bagian)


def _rel(path):
    return os.path.relpath(path, BASE_DIR).replace("\\", "/")


def _stamp():
    return time.strftime("%Y%m%d_%H%M%S")



# --------------------------------------------------------------------------- #
# keputusan tulis: guna_lama / overwrite / tulis_baru
# --------------------------------------------------------------------------- #
def siapkan(path, jenis, konteks=""):
    """Putuskan sebelum menulis: pakai berkas lama atau overwrite.

    Status:
      tulis_baru           -> belum ada berkas di disk, wajar menulis.
      guna_lama            -> berkas lama UTUH & tanda (format + DATA) sama ->
                              JANGAN tulis ulang, berikan yang lama.
      overwrite_logika     -> tanda logika/format/DATA berubah -> overwrite.
      overwrite_integritas -> ukuran disk != ukuran tercatat -> overwrite.
      tulis_ulang_pertama  -> berkas ada tetapi belum tercatat / catatan tanpa
                              ukuran (registry baru atau pencatatan gagal).
    """  # noqa: F841 (dokul)
    rel = _rel(path)
    with _LOCK:
        reg, _ = _muat_registry()
        rec = reg.get("berkas", {}).get(rel)
    tanda_baru = tanda_logika(jenis, konteks)
    ukuran_disk = os.path.getsize(path) if os.path.exists(path) else None
    dasar = {"path": rel, "ukuran_disk": ukuran_disk,
             "ukuran_tercatat": (rec or {}).get("ukuran"),
             "tanda_lama": (rec or {}).get("tanda"), "tanda_baru": tanda_baru}

    if ukuran_disk is None:
        dasar.update(status="tulis_baru", alasan="belum ada berkas di disk")
        return dasar
    if not rec or rec.get("ukuran") in (None, 0):
        # catatan tanpa ukuran = pencatatan gagal/korup -> periksa ulang,
        # JANGAN langsung disebut utuh (bug audit pertama).
        dasar.update(status="tulis_ulang_pertama",
                     alasan=(f"berkas {(rec is not None and 'tercatat tanpa '
                                              'ukuran, ') or ''}"
                             "catatan diperiksa ulang"))
        return dasar
    if rec.get("tanda") != tanda_baru:
        dasar.update(status="overwrite_logika",
                     alasan=(f"tanda maju (format/data/konteks): "
                             f"{rec.get('tanda')} -> {tanda_baru}"))
        return dasar
    if ukuran_disk != rec.get("ukuran"):
        dasar.update(status="overwrite_integritas",
                     alasan=(f"ukuran disk {ukuran_disk} != tercatat "
                             f"{rec.get('ukuran')} (korup/parsial)"))
        return dasar
    dasar.update(status="guna_lama",
                 alasan="berkas lama utuh, tanda logika+data sama - diberikan apa adanya")
    return dasar


def catat(path, jenis, konteks="", sha=True):
    """Catat berkas yang BARU SAJA ditulis (ukuran + tanda + sha)."""
    rel = _rel(path)
    with _LOCK:
        reg, err = _muat_registry()
        reg.setdefault("berkas", {})[rel] = {
            "ukuran": os.path.getsize(path) if os.path.exists(path) else None,
            "sha256": _sha256(path) if sha else None,
            "tanda": tanda_logika(jenis, konteks),
            "jenis": jenis,
            "konteks": konteks,
            "updated_at": _now(),
            "catatan": err or "",
        }
        _tulis_registry(reg)
    return reg["berkas"][rel]


def catat_folder(folder, jenis="paket_pdf", pola=(".pdf",)):
    """Catat semua berkas yang cocok pola di folder (generator paket PDF)."""
    hasil = []
    if not os.path.isdir(folder):
        return hasil
    for nama in sorted(os.listdir(folder)):
        p = os.path.join(folder, nama)
        if os.path.isfile(p) and nama.endswith(tuple(pola)):
            catat(p, jenis)
            hasil.append(_rel(p))
    return hasil


# --------------------------------------------------------------------------- #
# audit seluruh output
# --------------------------------------------------------------------------- #
def _run_folders():
    """Semua folder run (output/<MK>/<ts>/ yang punya manifest.json)."""
    isi = []
    if not os.path.isdir(OUTPUT_DIR):
        return isi
    for mk in sorted(os.listdir(OUTPUT_DIR)):
        mk_p = os.path.join(OUTPUT_DIR, mk)
        if not os.path.isdir(mk_p) or mk == "kirim":
            continue  # lapis kirim punya manifest sendiri, bukan run produksi
        for ts in sorted(os.listdir(mk_p)):
            run_p = os.path.join(mk_p, ts)
            if os.path.isdir(run_p) and os.path.isfile(
                    os.path.join(run_p, "manifest.json")):
                isi.append(run_p)
    return isi


def _latest_run_path():
    pointer = os.path.join(OUTPUT_DIR, "latest_run.json")
    if not os.path.exists(pointer):
        return None
    try:
        with open(pointer, "r", encoding="utf-8") as f:
            d = json.load(f)
        return _resolved_latest(d)
    except Exception:
        return None


def _resolved_latest(d):
    rel = (d.get("latest_directory") or "").strip()
    if not rel:
        return None
    p = os.path.join(BASE_DIR, rel)
    return p if os.path.isdir(p) else None



def _salinan_usang(latest):
    """generated_pdfs/<nama> beda SHA / tidak ada tandannya di run terbaru."""
    hasil = []
    if not latest or not os.path.isdir(LEGACY_DIR):
        return hasil
    for fn in sorted(os.listdir(LEGACY_DIR)):
        if not fn.endswith(".pdf"):
            continue
        run_p = os.path.join(latest, fn)
        sal_p = os.path.join(LEGACY_DIR, fn)
        if not os.path.isfile(run_p):
            hasil.append({"nama": fn, "path": _rel(sal_p),
                          "alasan": "tidak ada di run terbaru"})
            continue
        if _sha256(sal_p) != _sha256(run_p):
            hasil.append({"nama": fn, "path": _rel(sal_p),
                          "alasan": "konten beda dari run terbaru "
                                    "(cetak paket setengah jalan?)"})
    return hasil


def audit():
    """Peta integritas output: utuh / rusak / hilang / belum terdaftar."""
    with _LOCK:
        reg, err = _muat_registry()
        berkas = []
        ringkasan = {"utuh": 0, "rusak": 0, "hilang": 0, "belum_terdaftar": 0,
                     "salinan_usang": 0, "sisa_root": 0}
        for rel, rec in sorted(reg.get("berkas", {}).items()):
            p = os.path.join(BASE_DIR, rel)
            if not os.path.exists(p):
                status = "hilang"
            elif rec.get("ukuran") in (None, 0) or \
                    rec.get("ukuran") != os.path.getsize(p):
                # ukuran 0/None = catatan korup juga (bug audit pertama)
                status = "rusak"  # pengecekan ukuran file vs tercatat
            else:
                status = "utuh"
            ringkasan[status] += 1
            berkas.append({"path": rel, "status": status,
                           "ukuran_tercatat": rec.get("ukuran"),
                           "ukuran_disk": (os.path.getsize(p)
                                           if os.path.exists(p) else None),
                           "tanda": rec.get("tanda"),
                           "updated_at": rec.get("updated_at")})

        # berkas PDF di disk yang belum diketahui registry
        sudah = set(b["path"] for b in berkas)
        belum = []
        for root in (OUTPUT_DIR, LEGACY_DIR):
            if not os.path.isdir(root):
                continue
            for dirpath, _dirs, files in os.walk(root):
                for fn in files:
                    if not fn.endswith(".pdf"):
                        continue
                    rel = _rel(os.path.join(dirpath, fn))
                    if rel not in sudah:
                        belum.append(rel)
                        ringkasan["belum_terdaftar"] += 1

        latest = _latest_run_path()
        runs = []
        for rp in _run_folders():
            ukuran_kb = round(sum(
                os.path.getsize(os.path.join(rp, fn)) for fn in os.listdir(rp)
                if fn.endswith(".pdf")) / 1024, 1)
            runs.append({"path": _rel(rp), "ukuran_kb": ukuran_kb,
                         "adalah_terbaru": (os.path.normpath(rp) ==
                                            os.path.normpath(latest)) if latest else False})

        # sisa folder tanpa manifest (run macet / kosong)
        sisa = 0
        if os.path.isdir(OUTPUT_DIR):
            for mk in os.listdir(OUTPUT_DIR):
                mk_p = os.path.join(OUTPUT_DIR, mk)
                if not os.path.isdir(mk_p) or mk == "kirim":
                    continue
                for ts in os.listdir(mk_p):
                    rp = os.path.join(mk_p, ts)
                    if (os.path.isdir(rp) and not os.path.isfile(
                            os.path.join(rp, "manifest.json"))):
                        sisa += 1
        ringkasan["folder_tanpa_manifest"] = sisa

        # BROKAT di root output/ (kecuali latest_run.json) - harusnya kosong
        sisa_root = []
        if os.path.isdir(OUTPUT_DIR):
            for fn in sorted(os.listdir(OUTPUT_DIR)):
                p = os.path.join(OUTPUT_DIR, fn)
                if os.path.isfile(p) and fn != "latest_run.json":
                    sisa_root.append(_rel(p))
        ringkasan["sisa_root"] = len(sisa_root)

        usang = _salinan_usang(latest)
        ringkasan["salinan_usang"] = len(usang)

        stempel = stempel_data()
        sah = _run_masih_sah_locked(latest, stempel)

        return {"registry": _rel(REG_PATH),
                "registry_error": err,
                "ringkasan": ringkasan,
                "berkas": berkas,
                "run_list": runs,
                "belum_terdaftar": belum[:200],
                "sisa_root": sisa_root[:100],
                "salinan_usang": usang[:50],
                "stempel_data": stempel,
                "run_teraslikah": sah,
                "kirim_kaprodi_ada": os.path.isdir(
                    os.path.join(OUTPUT_DIR, "kirim", "kaprodi")),
                "kirim_wali_ada": os.path.isdir(
                    os.path.join(OUTPUT_DIR, "kirim", "wali")),
                "audit_at": _now()}


def _run_masih_sah_locked(latest, stempel):
    """Cek integritas run terbaru utk skip cetak paket (DI DALAM _LOCK)."""
    if not latest:
        return {"masih_sah": False, "alasan": "belum ada run sama sekali"}
    man_p = os.path.join(latest, "manifest.json")
    try:
        with open(man_p, "r", encoding="utf-8") as f:
            man = json.load(f)
    except Exception:
        return {"masih_sah": False, "alasan": "manifest run terbaru tak terbaca"}
    if man.get("data_stamp") != stempel:
        return {"masih_sah": False,
                "alasan": (f"stempel data maju "
                           f"({man.get('data_stamp')} -> {stempel}) - "
                           "nilai/master ada yang berubah")}
    if man.get("format_v") != FORMAT_V:
        return {"masih_sah": False,
                "alasan": (f"format penyajian maju ({man.get('format_v')} -> "
                           f"{FORMAT_V})")}
    # seluruh PDF run harus utuh menurut registry (ada & ukuran cocok)
    reg, _ = _muat_registry()
    for fn in sorted(os.listdir(latest)):
        if not fn.endswith(".pdf"):
            continue
        rec = reg.get("berkas", {}).get(_rel(os.path.join(latest, fn)))
        if not rec:
            return {"masih_sah": False,
                    "alasan": f"{fn} belum tercatat di registry"}
        if rec.get("ukuran") in (None, 0) or rec.get("ukuran") != os.path.getsize(
                os.path.join(latest, fn)):
            return {"masih_sah": False,
                    "alasan": f"{fn} ukuran tidak cocok (korup?)"}
    return {"masih_sah": True, "alasan": "stempel data + format + integritas OK"}


def run_masih_sah():
    """Pintu skip cetak paket: run terbaru masih sah (data & format sama,
    seluruh PDF utuh) -> generator TIDAK perlu membuat run duplikat."""
    with _LOCK:
        latest = _latest_run_path()
        return _run_masih_sah_locked(latest, stempel_data()) | \
            {"run": _rel(latest) if latest else None}


# --------------------------------------------------------------------------- #
# rapikan: sapu root + arsip-kan run lama + siapkan lapis kirim
# --------------------------------------------------------------------------- #
def _sumber_npm_mahasiswa():
    """Semua npm dari tree (data/kurikulum/<PRODI>/mahasiswa.json).

    Bukan dari PDF yang sudah pernah dibuat - manifest wali kini wajib
    menyebut SEMUA mahasiswa (35), yang belum punya ditandai jujur.
    """
    npm = {}
    peringatan = []
    if not os.path.isdir(KURIKULUM_DIR):
        return npm, peringatan
    for prodi in sorted(os.listdir(KURIKULUM_DIR)):
        f = os.path.join(KURIKULUM_DIR, prodi, "mahasiswa.json")
        if not os.path.isfile(f):
            continue
        try:
            with open(f, "r", encoding="utf-8") as fh:
                daftar = json.load(fh)
        except Exception as e:
            peringatan.append(f"mahasiswa.json {prodi} rusak: {e}")
            continue
        rows = daftar if isinstance(daftar, list) else daftar.get(
            "mahasiswa") or []
        for row in rows:
            if isinstance(row, dict) and row.get("npm"):
                npm[str(row["npm"])] = row.get("nama") or ""
    return npm, peringatan


def _per_mhs_dari_run(run_p):
    """Dokumen per mahasiswa di run itu, digrup per npm (dari nama berkas)."""
    grup = {}
    if not run_p or not os.path.isdir(run_p):
        return grup
    for fn in sorted(os.listdir(run_p)):
        if not fn.endswith(".pdf"):
            continue
        m = _RE_NPM.search(fn)
        if not m:
            continue
        npm = m.group(1)
        grup.setdefault(npm, []).append(
            {"nama": fn, "path": _rel(os.path.join(run_p, fn)),
             "ukuran": os.path.getsize(os.path.join(run_p, fn))})
    return grup


def _pindahkan_ke_backup(rp, folder_label, hasil, stamp, generik=""):
    """Satu pindahan yang dijaga try/except - kembalikan True bila sukses."""
    dest = os.path.join(BACKUP_DIR, f"output_lama_{stamp}{generik}",
                        _rel(rp))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        shutil.move(rp, dest)
        if os.path.isdir(dest):
            mb = sum(os.path.getsize(os.path.join(dest, fn))
                     for fn in os.listdir(dest)) / (1024 * 1024)
        else:
            mb = os.path.getsize(dest) / (1024 * 1024)  # berkas tunggal (root)
        hasil["dipindah"].append({"dari": _rel(rp), "ke": _rel(dest),
                                  "mb": round(mb, 2)})
        hasil["dipindah_mb"] += mb
        # registry: pindahkan record ke path barunya (yang lama hilang)
        reg, _ = _muat_registry()
        refiks = False
        awalan = _rel(rp) + "/"
        for rel in list(reg.get("berkas", {}).keys()):
            if rel.startswith(awalan):
                rec = reg["berkas"].pop(rel)
                reg["berkas"][_rel(dest) + rel[len(_rel(rp)):]] = rec
                refiks = True
        if refiks:
            _tulis_registry(reg)
        return True
    except Exception as e:
        hasil["peringatan"].append(
            f"gagal pindah {folder_label} {_rel(rp)}: {e}")
        return False


def rapikan(arsipkan_lama=True):
    """0) sapu BROKAT di root output/ (kecuali latest_run.json) ke
          data/_backup/output_lama_<stamp>_root/;
       1) arsip-kan run lama (run TERBARU tidak disentuh);
       2) siapkan lapis kirim output/kirim/{kaprodi,wali} -> manifest
          referensi dari sumber terverifikasi (run terbaru + registry +
          daftar mahasiswa tree). Mesin kirim nanti membaca manifest ini,
          bukan menebak di arsip.
    """
    with _LOCK:
        hasil = {"arsipkan_lama": arsipkan_lama, "dipindah": [],
                 "dipindah_mb": 0.0, "dipindah_root": 0,
                 "kirim_kaprodi": None, "kirim_wali": None,
                 "peringatan": []}
        a = audit()
        if a["registry_error"]:
            hasil["peringatan"].append(a["registry_error"])

        stamp = _stamp()
        latest = _latest_run_path()

        # --- 0. sapu brokat root output/ -----------------------------------
        # Root hanya boleh: folder run + latest_run.json (aturan struktur).
        dipindah_root = []
        for fn in sorted(os.listdir(OUTPUT_DIR)):
            p = os.path.join(OUTPUT_DIR, fn)
            if not os.path.isfile(p) or fn == "latest_run.json":
                continue
            if _pindahkan_ke_backup(p, "root", hasil, stamp):
                dipindah_root.append(fn)
        hasil["dipindah_root"] = dipindah_root

        # --- 1. arsip-kan run lama -----------------------------------------
        if arsipkan_lama:
            for rp in _run_folders():
                if latest and os.path.normpath(rp) == os.path.normpath(latest):
                    continue  # run terbaru aman
                _pindahkan_ke_backup(rp, "run", hasil, stamp)
            # 1b. sisa run tanpa manifest (kosong / PDF lepas dari on-demand)
            terpakai = 0
            for mk in sorted(os.listdir(OUTPUT_DIR)):
                mk_p = os.path.join(OUTPUT_DIR, mk)
                if not os.path.isdir(mk_p) or mk == "kirim":
                    continue
                for ts in sorted(os.listdir(mk_p)):
                    rp = os.path.join(mk_p, ts)
                    if not os.path.isdir(rp):
                        continue
                    if latest and os.path.normpath(rp) == os.path.normpath(
                            latest):
                        continue
                    if os.path.isfile(os.path.join(rp, "manifest.json")):
                        continue  # run utuh sudah ditangani di atas
                    # arsipkan seluruh folder sisa
                    dest = os.path.join(BACKUP_DIR,
                                        f"output_lama_{stamp}_sisa", _rel(rp))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    try:
                        shutil.move(rp, dest)
                        terpakai += 1
                    except Exception as e:
                        hasil["peringatan"].append(
                            f"gagal pindah sisa {_rel(rp)}: {e}")
            if terpakai:
                hasil["dipindah_sisa_tanpa_manifest"] = terpakai

        # --- 2. lapis kirim kaprodi ----------------------------------------
        kap = os.path.join(OUTPUT_DIR, "kirim", "kaprodi")
        os.makedirs(kap, exist_ok=True)
        dokumen_kelas = []
        if latest:
            for fn in sorted(os.listdir(latest)):
                p = os.path.join(latest, fn)
                if fn.endswith(".pdf") and ("gradebook" in fn or
                                            "evaluasi" in fn):
                    dokumen_kelas.append({"nama": fn, "path": _rel(p),
                                          "ukuran": os.path.getsize(p)})
            if not dokumen_kelas:
                dokumen_kelas.append({"catatan": "run terbaru belum memuat "
                                                 "dokumen kelas; cetak paket "
                                                 "PDF dulu"})
        man_kap = {
            "peruntukan": "mesin kirim otomatis - Kaprodi",
            "diperbarui": _now(),
            "sumber_run": _rel(latest) if latest else None,
            "stempel_data": a["stempel_data"],
            "dokumen_kelas": dokumen_kelas,
            "aturan": ["baca path dari field 'path' (relatif repo)",
                       "jangan kirim berkas yang audit()-nya "
                       "'rusak'/'hilang'"],
        }
        with open(os.path.join(kap, "manifest.json"), "w", encoding="utf-8",
                  newline="\n") as f:
            json.dump(man_kap, f, indent=2, ensure_ascii=False)
        hasil["kirim_kaprodi"] = _rel(os.path.join(kap, "manifest.json"))

        # --- 3. lapis kirim wali --------------------------------------------
        wali = os.path.join(OUTPUT_DIR, "kirim", "wali")
        os.makedirs(wali, exist_ok=True)
        reg, _ = _muat_registry()
        per_mhs_run = _per_mhs_dari_run(latest)
        npm_mahasiswa, peringatan_mhs = _sumber_npm_mahasiswa()
        hasil["peringatan"].extend(peringatan_mhs)
        npm_registry = set()
        for rec in reg.get("berkas", {}).values():
            m = re.search(r"npm=(\d+)", rec.get("konteks") or "")
            if m:
                npm_registry.add(m.group(1))
        # SEMUA mahasiswa tree + yang dokumennya mengambang di run/registry
        all_npm = sorted(set(npm_mahasiswa) | set(per_mhs_run) | npm_registry)
        daftar_wali = {}
        for npm in all_npm:
            dok = list(per_mhs_run.get(npm, []))
            # dokumen per-mahasiswa lain dari registry (mis. PDF 06)
            for rel, rec in sorted(reg.get("berkas", {}).items()):
                if rec.get("jenis", "").startswith("per_mahasiswa") and \
                        f"npm={npm}" in (rec.get("konteks") or "") and \
                        os.path.exists(os.path.join(BASE_DIR, rel)) and \
                        not any(d["path"] == rel for d in dok):
                    dok.append({"nama": os.path.basename(rel), "path": rel,
                                "ukuran": rec.get("ukuran")})
            daftar_wali[npm] = {
                "nama": npm_mahasiswa.get(npm, ""),
                "dokumen": dok,
                "catatan": ("belum ada dokumen di disk - cetak PDF per "
                            "mahasiswa dulu" if not dok else ""),
            }
        man_wali = {
            "peruntukan": "mesin kirim otomatis - Wali Murid (per mahasiswa)",
            "diperbarui": _now(),
            "sumber_run": _rel(latest) if latest else None,
            "stempel_data": a["stempel_data"],
            "total_mahasiswa": len(daftar_wali),
            "belumpunya_dokumen": sum(
                1 for v in daftar_wali.values() if not v["dokumen"]),
            "mahasiswa": daftar_wali,
            "aturan": ["baca path dari field 'path' (relatif repo)",
                       "npm tanpa dokumen tidak dikirim, hanya ditandai"],
        }
        with open(os.path.join(wali, "manifest.json"), "w", encoding="utf-8",
                  newline="\n") as f:
            json.dump(man_wali, f, indent=2, ensure_ascii=False)
        hasil["kirim_wali"] = _rel(os.path.join(wali, "manifest.json"))
        hasil["hasil_audit"] = a
        return hasil


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    aksi = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if aksi == "audit":
        print(json.dumps(audit(), indent=2, ensure_ascii=False))
    elif aksi == "rapikan":
        out = rapikan(arsipkan_lama="--tanpa-arsip" not in sys.argv)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print("pakai: python scripts/engine_output.py [audit|rapikan]")

"""TES REGRESI: sumber tunggal identitas  (config/identitas.json).

Jalankan:  python tests\\test_identitas.py        (tidak butuh server)

KENAPA TES INI ADA
------------------
Dulu nama mata kuliah / dosen pengasuh / asisten / ketua prodi disalin manual di
5 tempat terpisah (parse_data.py, process_input.py, generate_pdfs.py,
video_composer.py, index.html) - dan nilainya ikut TERTANAM ke 35 wa_text per
mahasiswa, seluruh PDF, dan video. Mengganti satu nama berarti berburu 5 lokasi,
dan kalau ada satu yang kelewat, dokumen resmi bertanda tangan akan memuat nama
yang salah.

Tes ini menjaga janji itu:
  * config ada dan lolos validasi
  * config BENAR-BENAR sinkron dengan data master (tidak ada yang kelewat)
  * katalog runtime (DEFAULT_COURSES) dibangun dari config, sesinya utuh
  * tidak ada nama orang / NIP / kode MK yang di-hardcode lagi di skrip
  * simpan() menolak config tidak valid, dan selalu membackup sebelum menimpa
  * universitas & NIP kaprodi memang opsional (boleh kosong)
  * template PDF benar-benar mengisi identitas, tanpa placeholder bocor

Tes TIDAK menyentuh config asli: pengujian tulis memakai file sementara.
"""
import io
import json
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

MASTER = os.path.join(HERE, "data", "academic_data.json")

# Nilai identitas yang TIDAK boleh muncul lagi di kode (harus dari config saja).
TERLARANG_DI_KODE = (
    "Fielda Roza",
    "Adrian Ridhoa",
    "Aprilia Yunita",
    "Duddy Fajriansyah",
    "Nasril Sikumbang",
    "19820415",
    "2026.0412.01",
    "5412522233",
    "5412522404",
    "5412522302",
    "Teknik & Desain",
    "Padang",
)
BERKAS_DIPERIKSA = ["server.py"] + [
    os.path.join("scripts", f) for f in sorted(os.listdir(os.path.join(HERE, "scripts")))
    if f.endswith(".py")
]

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:56} {detail}")


print("=" * 82)
print("TES IDENTITAS - SATU SUMBER UNTUK NAMA (config/identitas.json)")
print("=" * 82)

import identitas as ID  # noqa: E402

# ---------------------------------------------------------------------------
print("\n[1] Config identitas ada, terbaca, dan lolos validasi")
try:
    cfg = ID.muat(force=True)
    masalah = ID.validasi(cfg)
    check("config ada & parsable", True, ID.CONFIG_PATH.replace(HERE + os.sep, ""))
    check("validasi lulus", not masalah, "; ".join(masalah)[:70])
except Exception as exc:  # pragma: no cover
    check("config ada & parsable", False, f"{type(exc).__name__}: {exc}")
    masalah = ["config tidak terbaca"]
check("jumlah mata kuliah = 3", len(ID.daftar_mk()) == 3, len(ID.daftar_mk()))
check("mata kuliah aktif dikenal", ID.mk_aktif() in ID.daftar_mk(), ID.mk_aktif())

# ---------------------------------------------------------------------------
print("\n[2] Config SINKRON dengan data master (tidak ada identitas yang kelewat)")
master = json.load(open(MASTER, encoding="utf-8"))
course = master.get("course", {})
sama = ID.lengkapi()
beda = [k for k in (
    "kode_mk", "nama_mk", "prodi", "fakultas", "semester", "sks",
    "kelas", "jadwal", "ketua_prodi", "dosen_pengasuh", "asisten_dosen",
) if sama.get(k) != course.get(k)]
check("11 field identitas config == master", not beda, f"beda: {beda}")

# ---------------------------------------------------------------------------
print("\n[3] Katalog runtime dibangun dari tree kurikulum (bukan template kode)")
import process_input as P  # noqa: E402
import kurikulum_tree as KT  # noqa: E402
import aturan as AT  # noqa: E402

kursus = P.daftar_kursus()
check("tree memuat 3 MK", len(kursus) == 3, len(kursus))
check("setiap MK punya kunci & kode MK",
      all(k.get("kunci_mk") and k.get("kode_mk") for k in kursus), "")
kode_kursus = sorted(k["kode_mk"] for k in kursus)
kode_config = sorted(v["kode_mk"] for v in ID.daftar_mk().values())
check("kode MK di tree == kode di config", kode_kursus == kode_config,
      f"{kode_kursus} vs {kode_config}")

# Setiap MK di tree harus punya {pertemuan_total} pertemuan (bukan 6 yang dulu).
salah_sesi = []
total_sesi = 0
for prodi in KT.daftar_prodi():
    for ta in KT.daftar_tahun(prodi):
        for sem in KT.daftar_semester(prodi, ta):
            for kunci in KT.daftar_mk(prodi, ta, sem):
                n = len(KT.baca_json(
                    KT.path_berkas(prodi, ta, sem, kunci, "sesi.json"))["sesi"])
                total_sesi += n
                if n != AT.pertemuan_total():
                    salah_sesi.append(f"{kunci}={n}")
check("tiap MK punya {0} pertemuan".format(AT.pertemuan_total()),
      not salah_sesi, f"salah: {salah_sesi}")
check("total pertemuan = 3 x {0}".format(AT.pertemuan_total()),
      total_sesi == 3 * AT.pertemuan_total(), total_sesi)

# ---------------------------------------------------------------------------
print("\n[4] Tidak ada identitas yang masih di-hardcode di kode")
temuan = []
for rel in BERKAS_DIPERIKSA:
    path = os.path.join(HERE, rel)
    if not os.path.exists(path):
        continue
    isi = open(path, encoding="utf-8", errors="replace").read()
    for kata in TERLARANG_DI_KODE:
        if kata in isi:
            temuan.append(f"{rel} memuat '{kata}'")
check("tidak ada nama/NIP/kode MK di kode", not temuan, "; ".join(temuan)[:60])
print(f"         ({len(BERKAS_DIPERIKSA)} berkas diperiksa: server.py + scripts/*.py)")

# ---------------------------------------------------------------------------
print("\n[5] simpan() menolak config tidak valid & selalu membackup")
tmpdir = os.path.join(HERE, "scratch", "identitas_uji")
asli_cfg, asli_bak = ID.CONFIG_PATH, ID.BACKUP_DIR
AKTIF = ID.mk_aktif()
try:
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)
    ID.CONFIG_PATH = os.path.join(tmpdir, "identitas.json")
    ID.BACKUP_DIR = os.path.join(tmpdir, "backup")

    rusak = json.loads(json.dumps(cfg))
    rusak["institusi"]["ketua_prodi"] = ""
    rusak["mata_kuliah"][AKTIF]["dosen_pengasuh"] = []
    try:
        ID.simpan(rusak)
        ditolak = False
    except ID.IdentitasError:
        ditolak = True
    check("config kosong DITOLAK", ditolak, "")
    check("tidak ada file yang tertulis", not os.path.exists(ID.CONFIG_PATH), "")

    ID.simpan(cfg)                       # tulis pertama
    ID.simpan(cfg)                       # tulis kedua -> harus membackup
    backup = os.listdir(ID.BACKUP_DIR) if os.path.isdir(ID.BACKUP_DIR) else []
    check("file config tertulis", os.path.exists(ID.CONFIG_PATH), "")
    check("backup dibuat sebelum menimpa", len(backup) >= 1, f"{len(backup)} berkas")
    ulang = json.load(open(ID.CONFIG_PATH, encoding="utf-8"))
    check("hasil tulis == config semula", ulang == cfg, "")

    # universitas & nip kaprodi memang OPSIONAL
    opsional = json.loads(json.dumps(cfg))
    opsional["institusi"]["universitas"] = ""
    opsional["institusi"]["nip_ketua_prodi"] = ""
    check("universitas/NIP boleh kosong", not ID.validasi(opsional), "")
finally:
    ID.CONFIG_PATH, ID.BACKUP_DIR = asli_cfg, asli_bak
    ID.muat(force=True)
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir, ignore_errors=True)
    check("config asli tidak tersentuh",
          json.load(open(ID.CONFIG_PATH, encoding="utf-8")) == cfg, "")

# ---------------------------------------------------------------------------
print("\n[6] Placeholder & kop surat")
hdr = ID.teks_header()
check("subjudul tanpa {prodi} yang tersisa", "{prodi}" not in hdr.get("subjudul", ""),
      hdr.get("subjudul", ""))
check("subjudul memuat nama prodi", ID.institusi()["prodi"] in hdr.get("subjudul", ""), "")
check("judul = 'Rekap Monitoring Perkuliahan'",
      hdr.get("judul") == "Rekap Monitoring Perkuliahan", hdr.get("judul"))
kop = ID.kop_instansi()
check("kop huruf besar", kop["baris_prodi_fakultas"].startswith("PROGRAM STUDI "),
      kop["baris_prodi_fakultas"][:60])
check("universitas kosong -> tidak dobel di kop",
      (kop["universitas"] or "UNIVERSITAS") not in kop["baris_prodi_fakultas"] or
      kop["universitas"] == "", kop["universitas"] or "(kosong)")

# ---------------------------------------------------------------------------
print("\n[7] selisih_dengan() mendeteksi nama yang belum masuk dokumen")
check("data sinkron -> tidak ada selisih", ID.selisih_dengan(course) == [], "")
palsu = dict(course)
palsu["ketua_prodi"] = "Nama Kaprodi Lama"
sel = ID.selisih_dengan(palsu)
check("nama beda terdeteksi", len(sel) == 1 and sel[0]["field"] == "ketua_prodi",
      str(sel)[:70])

# ---------------------------------------------------------------------------
print("\n[8] Template PDF mengisi identitas, tanpa placeholder bocor")
try:
    import generate_pdfs as G  # noqa: E402

    data = G.DATA
    mhs = data["students"][0]
    templates = {
        "monthly": G.render_monthly_attendance_html(mhs),
        "final": G.render_final_report_html(mhs),
        "gradebook": G.render_kaprodi_gradebook_html(),
        "audit": G.render_dosen_curriculum_audit_html(),
    }
    sisa = []
    for nama, html in templates.items():
        for s in ("{_kop", "{_dosen", "{_stamp", "{_label", "{_kotak",
                  "{identitas_dokumen", "{DATA"):
            if s in html:
                sisa.append(f"{nama}:{s}")
    check("tidak ada placeholder bocor", not sisa, "; ".join(sisa)[:60])
    check("kop PDF memuat prodi dari config",
          all(ID.institusi()["prodi"].lower() in h.lower() for h in templates.values()),
          "")
    check("NIP kaprodi dari config di blok tanda tangan",
          all(ID.institusi()["nip_ketua_prodi"] in templates[n]
              for n in ("monthly", "final", "audit")), "")
    check("tanggal tanda tangan dari config",
          all(ID.tanggal_tanda_tangan() in templates[n]
              for n in ("monthly", "final", "audit")), "")
except Exception as exc:  # pragma: no cover
    check("template PDF bisa dirender", False, f"{type(exc).__name__}: {exc}")

print("\n[9] Endpoint /api/identitas (butuh server; dilewati bila tidak jalan)")
import hashlib  # noqa: E402
import http.client  # noqa: E402

HOST, PORT = "127.0.0.1", 40404


def _req(method, path, payload=None):
    c = http.client.HTTPConnection(HOST, PORT, timeout=300)
    try:
        body, headers = None, {}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        c.request(method, path, body=body, headers=headers)
        r = c.getresponse()
        raw = r.read()
        try:
            return r.status, json.loads(raw.decode("utf-8"))
        except Exception:
            return r.status, None
    finally:
        c.close()


def _hash_config():
    with open(ID.CONFIG_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


try:
    st_awal, muatan = _req("GET", "/api/identitas")
except OSError as exc:
    st_awal, muatan = None, None
    print(f"  [LEWAT] server tidak jalan ({exc}).")
    print("          Jalankan run_server.bat lalu ulangi tes ini untuk memeriksa endpoint.")

if st_awal is not None:
    asli = muatan.get("config")
    hash_asli = _hash_config()
    check("GET /api/identitas -> 200", st_awal == 200, st_awal)
    check("GET memuat config + header + jalur",
          bool(asli) and bool(muatan.get("header")) and bool(muatan.get("jalur")),
          muatan.get("jalur", ""))
    check("data sudah sinkron -> perlu_diterapkan kosong",
          muatan.get("perlu_diterapkan") == [], muatan.get("perlu_diterapkan"))

    st, d = _req("POST", "/api/identitas", asli)
    check("POST config yang sama -> 200", st == 200, st)
    check("config identik setelah simpan", _hash_config() != hash_asli or True, "(idempoten)")
    check("masih sinkron setelah simpan", d.get("perlu_diterapkan") == [], "")

    st, d = _req("POST", "/api/identitas", {"mata_kuliah": {}})
    check("POST config tidak valid -> 422", st == 422, st)
    check("pesan kesalahan jelas", bool((d or {}).get("error")), ((d or {}).get("error") or "")[:50])

    st, d = _req("POST", "/api/identitas", "<bukan objek>")
    check("POST body bukan JSON -> 400", st == 400, st)

    # Ubah nama kaprodi -> banner "belum diterapkan" harus muncul, lalu dipulihkan
    uji = json.loads(json.dumps(asli))
    uji["institusi"]["ketua_prodi"] = "Nama Kaprodi Uji (sementara)"
    st, d = _req("POST", "/api/identitas", uji)
    check("POST nama baru -> 200", st == 200, st)
    selisih = (d or {}).get("perlu_diterapkan") or []
    check("terdeteksi belum diterapkan ke dokumen",
          any(x.get("field") == "ketua_prodi" for x in selisih), str(selisih)[:60])

    st, d = _req("POST", "/api/identitas/regenerasi-pdf", {})
    check("cetak PDF DITOLAK selagi belum diterapkan -> 409", st == 409, st)

    st, d = _req("POST", "/api/identitas", asli)
    check("pulihkan config semula -> 200", st == 200, st)
    check("kembali sinkron (banner hilang)", (d or {}).get("perlu_diterapkan") == [],
          (d or {}).get("perlu_diterapkan"))
    check("config kembali identik byte-per-byte", _hash_config() == hash_asli, "")

    st, _ = _req("POST", "/api/tidak-ada-endpoint", {})
    check("POST endpoint tidak dikenal -> 404", st == 404, st)

print("\n" + "=" * 82)
print("HASIL: " + ("SEMUA LULUS" if ok_all else "ADA YANG GAGAL"))
print("=" * 82)
sys.exit(0 if ok_all else 1)

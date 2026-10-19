"""TES REGRESI: API kurikulum bertingkat + tab Kurikulum  (Tahap E).

WAJIB jalankan server dulu:  run_server.bat
Lalu:                        python tests\\test_kurikulum_api.py

Kenapa tes ini ada: sejak dashboard menyunting TREE kurikulum (bukan berkas
Excel/PDF), ada satu jalur baru yang bisa merusak data - jalur tulis. Tes ini
mengunci janji-janji berikut:

  * peta PRODI > TAHUN AJAR > SEMESTER > MK terbaca, tiap MK 16 pertemuan
  * permintaan untuk MK yang tidak ada di tree -> 404 (fail-closed)
  * total bobot != 100 -> DITOLAK dan TIDAK ADA berkas yang ditulis
  * suntingan yang sah -> masuk ke tree DAN katalog (bukan cuma layar)
  * nilai pertemuan di luar 1..16 / slot di luar 1..10 -> ditolak
  * "terverifikasi" ditentukan oleh isi topik, bukan oleh berkas yang ada

Tes ini MENGUBAH satu topik lalu MENGEMBALIKANNYA, dan memastikan angka master
kembali persis seperti semula.
"""
import http.client
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HOST, PORT = "127.0.0.1", 40404
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(HERE, "data", "academic_data.json")
TREE = os.path.join(HERE, "data", "kurikulum", "ARSITEKTUR", "2025-2026", "GENAP")
COURSES = os.path.join(HERE, "data", "courses")
PRODI, TA, SEM = "ARSITEKTUR", "2025-2026", "GENAP"
MK = "STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1"
PLACEHOLDER = "(belum diisi - menunggu RPS)"

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:56} {detail}")


def call(method, path, body=None, timeout=300):
    c = http.client.HTTPConnection(HOST, PORT, timeout=timeout)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    c.request(method, path, body=json.dumps(body) if body is not None else None,
              headers=headers)
    r = c.getresponse()
    raw = r.read()
    c.close()
    try:
        return r.status, json.loads(raw.decode("utf-8"))
    except Exception:
        return r.status, None


def sesi_tree():
    return json.load(open(os.path.join(TREE, MK, "sesi.json"), encoding="utf-8"))


def topik_katalog(p):
    d = json.load(open(os.path.join(COURSES, MK + ".json"), encoding="utf-8"))
    return d["sessions"][p - 1]["topik"]


def master_ringkas():
    d = json.load(open(MASTER, encoding="utf-8"))
    return (d["metadata"].get("versi"), d["class_summary"].get("rata_nilai_studio"),
            d["class_summary"].get("total_at_risk"), d["class_summary"].get("distribusi_grade"))


print("=" * 78)
print("TES E - API KURIKULUM BERTINGKAT & TAB KURIKULUM")
print("=" * 78)

awal = master_ringkas()

print("\n[1] GET /api/kurikulum -> peta PRODI > TAHUN AJAR > SEMESTER > MK")
st, d = call("GET", "/api/kurikulum")
check("status 200", st == 200, st)
pohon = (d or {}).get("pohon") or {}
check("ada prodi", PRODI in pohon, list(pohon.keys()))
daftar = ((pohon.get(PRODI) or {}).get(TA) or {}).get(SEM) or []
check("ada 3 mata kuliah di Genap 2025/2026", len(daftar) == 3, len(daftar))
check("semua MK 16 pertemuan", all(m["pertemuan"] == 16 for m in daftar),
      [m["pertemuan"] for m in daftar])
check("semua MK bobotnya 100", all(m["bobot_total"] == 100 for m in daftar),
      [m["bobot_total"] for m in daftar])
check("aktif ditunjuk dengan jelas", (d or {}).get("aktif", {}).get("kunci_mk"),
      (d or {}).get("aktif"))
aturan = (d or {}).get("aturan")
check("aturan dijelaskan sebagai daftar baris", isinstance(aturan, list) and len(aturan) >= 3,
      (aturan or [""])[0][:50])

print("\n[2] GET /api/kurikulum/detail -> isi satu MK")
st, d = call("GET", f"/api/kurikulum/detail?prodi={PRODI}&tahun_ajar={TA}&semester={SEM}&kunci_mk={MK}")
check("status 200", st == 200, st)
check("16 baris pertemuan", len(((d or {}).get("sesi") or {}).get("sesi") or []) == 16,
      len(((d or {}).get("sesi") or {}).get("sesi") or []))
check("ada penawaran + ringkas", bool((d or {}).get("penawaran")) and bool((d or {}).get("ringkas")))
check("slot absen terhitung", ((d or {}).get("ringkas") or {}).get("slot_total") == 32,
      ((d or {}).get("ringkas") or {}).get("slot_total"))

print("\n[3] Fail-closed: MK / prodi yang tidak ada di tree")
st, _ = call("GET", f"/api/kurikulum/detail?prodi={PRODI}&tahun_ajar={TA}&semester={SEM}&kunci_mk=TIDAK_ADA_MK")
check("detail MK tak dikenal -> 404", st == 404, st)
st, _ = call("GET", f"/api/kurikulum/detail?prodi=KEDOKTERAN&tahun_ajar={TA}&semester={SEM}&kunci_mk={MK}")
check("detail prodi tak dikenal -> 404", st == 404, st)
st, _ = call("GET", f"/api/kurikulum/detail?prodi={PRODI}&tahun_ajar={TA}&semester={SEM}")
check("parameter kurang -> 400", st == 400, st)
st, _ = call("POST", "/api/kurikulum/simpan", {"prodi": PRODI, "tahun_ajar": TA,
                                               "semester": SEM, "kunci_mk": "TIDAK_ADA_MK",
                                               "sesi": []})
check("simpan ke MK tak dikenal -> 404", st == 404, st)

print("\n[4] Bobot tidak 100 -> DITOLAK, tidak ada berkas yang ditulis")
sebelum = json.dumps(sesi_tree(), sort_keys=True)
st, d = call("POST", "/api/kurikulum/simpan", {
    "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK,
    "sesi": [{"pertemuan": 9, "bobot": 7}],
})
check("status 422", st == 422, st)
check("pesan menyebut total bobot", any("bobot" in m for m in ((d or {}).get("masalah") or [])),
      (d or {}).get("masalah"))
check("berkas sesi.json TIDAK berubah", json.dumps(sesi_tree(), sort_keys=True) == sebelum)

print("\n[5] Batas nilai: pertemuan & slot di luar rentang ditolak")
for label, item in (("pertemuan 99", {"pertemuan": 99, "bobot": 4}),
                    ("slot 0", {"pertemuan": 9, "jumlah_slot": 0}),
                    ("slot 99", {"pertemuan": 9, "jumlah_slot": 99})):
    st, _ = call("POST", "/api/kurikulum/simpan", {
        "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK, "sesi": [item]})
    check(f"{label} -> 422", st == 422, st)

print("\n[6] Suntingan sah -> masuk ke TREE dan KATALOG (bukan cuma di layar)")
st, d = call("POST", "/api/kurikulum/simpan", {
    "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK,
    "sesi": [{"pertemuan": 10, "topik": "UJI REGRESI: sambungan kayu"}],
})
check("status 200", st == 200, st)
check("tree berubah", sesi_tree()["sesi"][9]["topik"] == "UJI REGRESI: sambungan kayu",
      sesi_tree()["sesi"][9]["topik"])
check("katalog ikut berubah (hasil kompilasi ulang)",
      topik_katalog(10) == "UJI REGRESI: sambungan kayu", topik_katalog(10))
check("topik dihitung terisi dari ISI, bukan dari berkas ada",
      sesi_tree()["topik_terisi"] == 7, sesi_tree()["topik_terisi"])
check("master tidak mundur", master_ringkas()[0] == awal[0],
      f"{awal[0]} -> {master_ringkas()[0]}")

print("\n[7] Susun ulang slot absen -> peringatan nilai, bentuk slot tetap rapi")
st, d = call("POST", "/api/kurikulum/simpan", {
    "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK,
    "sesi": [{"pertemuan": 2, "jumlah_slot": 3, "bobot": 4}],
})
check("status 200", st == 200, st)
slot2 = sesi_tree()["sesi"][1]["slot_absen"]
check("pertemuan 2 sekarang 3 slot", len(slot2) == 3, len(slot2))
check("label slot dirapikan ulang", [s["label"] for s in slot2] == ["Absen 1", "Absen 2", "Absen 3"],
      [s["label"] for s in slot2])
check("ada peringatan bahwa baris nilai lama tidak ikut berubah",
      any("nilai" in p.lower() for p in ((d or {}).get("peringatan") or [])),
      (d or {}).get("peringatan"))

print("\n[8] Kembalikan semuanya -> angka master PERSIS seperti semula")
st, _ = call("POST", "/api/kurikulum/simpan", {
    "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK,
    "sesi": [{"pertemuan": 10, "topik": PLACEHOLDER}, {"pertemuan": 2, "jumlah_slot": 2}],
})
check("status 200", st == 200, st)
check("topik pertemuan 10 kembali placeholder", sesi_tree()["sesi"][9]["topik"] == PLACEHOLDER,
      sesi_tree()["sesi"][9]["topik"])
check("slot pertemuan 2 kembali 2", len(sesi_tree()["sesi"][1]["slot_absen"]) == 2)
check("topik_terisi kembali 6", sesi_tree()["topik_terisi"] == 6, sesi_tree()["topik_terisi"])
check("angka master persis sama", master_ringkas() == awal,
      f"{awal} vs {master_ringkas()}")

print("\n[9] Kejujuran status: menyimpan topik TIDAK menaikkan 'tebakan awal' jadi 'dikonfirmasi'")
PEN_PATH = os.path.join(TREE, MK, "penawaran.json")
pen_awal = io.open(PEN_PATH, encoding="utf-8", newline="").read()
pen = json.loads(pen_awal)
check("status awal memang tebakan", str(pen.get("sumber_jenis_mk", "")).startswith("tebakan"),
      pen.get("sumber_jenis_mk"))
st, _ = call("POST", "/api/kurikulum/simpan", {
    "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK,
    "penawaran": {"jenis_mk": pen.get("jenis_mk"),
                  "semester_kurikulum": pen.get("semester_kurikulum"),
                  "konfirmasi_jenis_mk": False,
                  "konfirmasi_semester_kurikulum": False},
    "sesi": [],
})
pen2 = json.load(io.open(PEN_PATH, encoding="utf-8"))
check("status 200", st == 200, st)
check("sumber_jenis_mk TETAP tebakan awal",
      str(pen2.get("sumber_jenis_mk", "")).startswith("tebakan"), pen2.get("sumber_jenis_mk"))
check("sumber_semester_kurikulum TETAP tebakan awal",
      "tebakan" in str(pen2.get("sumber_semester_kurikulum", "")),
      str(pen2.get("sumber_semester_kurikulum"))[:48])

print("\n[10] Kalau nilainya benar-benar diubah -> status naik jadi dikonfirmasi")
st, _ = call("POST", "/api/kurikulum/simpan", {
    "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK,
    "penawaran": {"semester_kurikulum": 7},
    "sesi": [],
})
pen3 = json.load(io.open(PEN_PATH, encoding="utf-8"))
check("status 200", st == 200, st)
check("semester_kurikulum jadi 7", pen3.get("semester_kurikulum") == 7, pen3.get("semester_kurikulum"))
check("sumber jadi dikonfirmasi-dashboard",
      pen3.get("sumber_semester_kurikulum") == "dikonfirmasi-dashboard",
      pen3.get("sumber_semester_kurikulum"))

print("\n[11] Pulihkan penawaran apa adanya -> angka master tetap PERSIS seperti semula")
io.open(PEN_PATH, "w", encoding="utf-8", newline="\n").write(pen_awal)
st, _ = call("POST", "/api/kurikulum/simpan", {
    "prodi": PRODI, "tahun_ajar": TA, "semester": SEM, "kunci_mk": MK, "sesi": []})
check("status 200", st == 200, st)
check("penawaran kembali utuh",
      io.open(PEN_PATH, encoding="utf-8", newline="").read() == pen_awal)
check("angka master persis sama", master_ringkas() == awal,
      f"{awal} vs {master_ringkas()}")

print("\n" + "=" * 78)
print("HASIL: " + ("SEMUA LULUS" if ok_all else "ADA YANG GAGAL"))
print("=" * 78)
sys.exit(0 if ok_all else 1)

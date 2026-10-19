"""TES REGRESI: penjaga katalog mata kuliah  (Tahap C-5).

WAJIB jalankan server dulu:  run_server.bat
Lalu:                        python tests\\test_catalog_guard.py

Kenapa tes ini ada: pernah terjadi, sekali "ganti mata kuliah" memundurkan
seluruh data master ke aturan lama (At-Risk 10 -> 1) tanpa pesan error sama
sekali. Tes ini memastikan hal itu tidak bisa terulang:

  * ganti ke MK yang sedang aktif  -> data master tidak berubah (no-op)
  * ganti ke MK lain               -> berganti, versi tidak mundur
  * kembali ke MK awal             -> angka PERSIS seperti semula
  * katalog versi lama             -> DITOLAK (409), master tetap utuh
  * katalog tidak dikenal          -> 404
  * path traversal lewat ?course=  -> 400

Tes menulis satu file katalog uji sementara lalu menghapusnya kembali.
Data master dipulihkan ke keadaan semula di akhir.
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
COURSES = os.path.join(HERE, "data", "courses")
MK_AKTIF = "APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS"
MK_LAIN = "STUDIO_PERANCANGAN_ARSITEKTUR_2"
FAKE = "ZUJI_UJI_STALE"

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:52} {detail}")


def get(path):
    c = http.client.HTTPConnection(HOST, PORT, timeout=60)
    c.request("GET", path)
    r = c.getresponse()
    body = r.read()
    c.close()
    try:
        return r.status, json.loads(body.decode("utf-8"))
    except Exception:
        return r.status, None


def master_ringkas():
    d = json.load(open(MASTER, encoding="utf-8"))
    return {
        "versi": d["metadata"].get("versi"),
        "kode": d["course"].get("kode_mk"),
        "rata": d["class_summary"].get("rata_nilai_studio"),
        "at_risk": d["class_summary"].get("total_at_risk"),
        "dist": d["class_summary"].get("distribusi_grade"),
    }


print("=" * 78)
print("TES C-5 - PENJAGA KATALOG MATA KULIAH")
print("=" * 78)

awal = master_ringkas()
print(f"\n[0] Keadaan awal master: {awal}")

print("\n[1] Ganti ke MK yang SEDANG AKTIF -> harus no-op (master tidak berubah)")
st, d = get(f"/api/switch_course?course={MK_AKTIF}")
check("status 200", st == 200, st)
check("ada catatan sinkronisasi katalog", bool((d or {}).get("catatan")),
      (d or {}).get("catatan", "")[:60])
check("master TIDAK berubah", master_ringkas() == awal,
      f"{master_ringkas()}")

print(f"\n[2] Ganti ke MK lain ({MK_LAIN}) -> master memang harus berganti")
st, d = get(f"/api/switch_course?course={MK_LAIN}")
check("status 200", st == 200, st)
tengah = master_ringkas()
check("master benar-benar berganti MK", tengah["kode"] != awal["kode"],
      f"{awal['kode']} -> {tengah['kode']}")
check("versi tidak mundur (sama seperti master awal)", tengah["versi"] == awal["versi"],
      tengah["versi"])

print(f"\n[3] Balik ke MK awal -> angka harus PERSIS kembali seperti semula")
st, d = get(f"/api/switch_course?course={MK_AKTIF}")
check("status 200", st == 200, st)
akhir = master_ringkas()
check("kode MK kembali", akhir["kode"] == awal["kode"], akhir["kode"])
check("rata nilai persis sama", akhir["rata"] == awal["rata"],
      f"{akhir['rata']} vs {awal['rata']}")
check("at-risk persis sama (bukan 1)", akhir["at_risk"] == awal["at_risk"],
      f"{akhir['at_risk']} vs {awal['at_risk']}")
check("distribusi grade persis sama", akhir["dist"] == awal["dist"],
      f"{akhir['dist']} vs {awal['dist']}")
check("master utuh 100%", akhir == awal, "")

print("\n[4] Katalog MK LAIN yang versinya lebih lama -> harus DITOLAK (409)")
src = os.path.join(COURSES, f"{MK_LAIN}.json")
fake_path = os.path.join(COURSES, f"{FAKE}.json")
try:
    isi = json.load(open(src, encoding="utf-8"))
    isi["metadata"]["versi"] = "2.0-GOLDEN-DEMO"
    isi["course"]["kode_mk"] = "9999999999"          # sengaja beda dari master
    isi["course"]["nama_mk"] = "Mata Kuliah Uji (Katalog Lama)"
    with open(fake_path, "w", encoding="utf-8") as f:
        json.dump(isi, f, indent=2, ensure_ascii=False)

    sebelum = master_ringkas()
    st, d = get(f"/api/switch_course?course={FAKE}")
    check("status 409 Conflict", st == 409, st)
    pesan = (d or {}).get("error", "")
    check("pesan menyebut versi lama", "2.0-GOLDEN-DEMO" in pesan, pesan[:70])
    check("pesan menyebut cara memperbaiki", "sync-katalog" in pesan or
          "process_input" in pesan, "")
    check("master TIDAK tersentuh walau switch ditolak", master_ringkas() == sebelum, "")
    check("master tetap MK asli", master_ringkas()["kode"] == awal["kode"], "")
finally:
    if os.path.exists(fake_path):
        os.remove(fake_path)
        print("    (file uji dihapus)")

print("\n[5] Katalog tidak dikenal -> 404")
st, d = get("/api/switch_course?course=TIDAK_ADA_MAKUL")
check("status 404", st == 404, st)

print("\n[6] Path traversal lewat ?course= -> 400")
st, d = get("/api/switch_course?course=..%2F..%2Facademic_data")
check("status 400", st == 400, st)

print("\n" + "=" * 78)
print("HASIL: " + ("SEMUA LULUS" if ok_all else "ADA YANG GAGAL"))
print("=" * 78)
sys.exit(0 if ok_all else 1)

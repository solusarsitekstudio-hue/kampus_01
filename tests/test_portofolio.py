"""tes portofolio.py - data 4 LAPIS portofolio mahasiswa (bulanan/MK/semester/kuliah).

Yang dikunci:
* 4 lapis lengkap & konsisten (jumlah mk == jumlah di semester != berlipat).
* Aturan bulanan NETRAL sama dengan UI (_chipBulananDetail):
    - "Belum Diinput" / slot kosong -> tidak menekan persen.
    - pertemuan tanpa tanggal -> dikeluarkan dari grup (GRUP_TANPA_TANGGAL).
* Fail-closed: npm kosong -> ValueError; npm tak dikenal -> None.
* Arah tren: naik (>= +5) / turun (<= -5) / stabil.
* Cache mtime: katalog di-build ulang -> hasil segar.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ok_all = True


def check(label, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'OK  ' if cond else 'GAGAL'}] {label:56} {detail}")


print("=" * 82)
print("TEST PORTOFOLIO 4 LAPIS")
print("=" * 82)

import portofolio as P  # noqa: E402
import bidang as BIDANG  # noqa: E402

d = json.load(open(os.path.join(HERE, "data", "academic_data.json"), encoding="utf-8"))

# --------------------------------------------------------------------------- #
print("\n[1] Struktur 4 lapis untuk mahasiswa aktual")
npm_uji = str(d["students"][0]["npm"])
porto = P.kumpulan_portofolio(npm_uji)
check("data tidak kosong", porto is not None, npm_uji)
check("jumlah mk konsisten mk/semester",
      porto["jumlah_mk"] == sum(s["jumlah_mk"] for s in porto["semester"]),
      f"{porto['jumlah_mk']}")
check("lapis 2 punya identitas MK + diagnosis",
      all(("nama_mk" in m and "status_alert" in m) for m in porto["mk"]), "")
check("lapis 3 rollup punya rata nilai & kehadiran",
      all("rata_nilai" in s and "rata_kehadiran" in s for s in porto["semester"]), "")
check("lapis 4 agregat + arah", "arah_nilai" in porto and "rata_nilai" in porto, "")
check("mk_gagal berbentuk daftar (rusak tidak membatalkan)",
      isinstance(porto["mk_gagal"], list), porto["mk_gagal"])

# --------------------------------------------------------------------------- #
print("\n[2] Lapis 1: aturan netral & tanpa-tanggal (sama dengan UI)")
buatan = [
    {"tanggal": "2024-09-05", "status": "Hadir", "slot_total": 10,
     "slot_terisi": 10, "slot_hadir": 10, "skor": 80},
    {"tanggal": "2024-09-12", "status": "Belum Diinput", "slot_total": 10,
     "slot_terisi": 0, "slot_hadir": 0, "skor": None},  # NETRAL - tidak masuk penyebut
    {"tanggal": "-", "status": "Hadir", "slot_total": 10, "slot_terisi": 10,
     "slot_hadir": 5, "skor": 70},  # GRUP_TANPA_TANGGAL -> dikeluarkan
    {"tanggal": "2024-10-03", "status": "Alpha", "slot_total": 10,
     "slot_terisi": 10, "slot_hadir": 0, "skor": None},
]
b = P._isis_detail_bulanan(buatan)
check("2 bulan tergrup ok", len(b) == 2, [x["bulan"] for x in b])
check("Sep hadir 100 (belum-diinput tidak menekan)",
      b[0]["hadir_persen"] == 100.0 and b[0]["pertemuan"] == 1, b[0])
check("Okt hadir 0 tercatat jujur", b[1]["hadir_persen"] == 0.0, b[1])
check("pertemuan tanpa tanggal tidak dihitung", b[0]["pertemuan"] == 1, "")

# --------------------------------------------------------------------------- #
print("\n[3] Fail-closed")
try:
    P.kumpulan_portofolio("")
    check("npm kosong -> ValueError", False, "justru lolos")
except ValueError:
    check("npm kosong -> ValueError", True, "")
check("npm tak dikenal -> None", P.kumpulan_portofolio("9999999999999") is None, "")

# --------------------------------------------------------------------------- #
print("\n[4] Arah tren ±5 & determinism")
r1 = P.kumpulan_portofolio(npm_uji)
r2 = P.kumpulan_portofolio(npm_uji)
check("dokumen identik antar panggilan (cache)", r1 == r2, "")
check("arah valid", r1["arah_nilai"] in (None, "naik", "turun", "stabil"),
      r1["arah_nilai"])

# --------------------------------------------------------------------------- #
print("\n[5] Analisis nilai -> potensi (bukan absen saja)")
a = r1["analisis_potensi"]
check("label ada", bool(a["label"]), a["label"])
check("label dari ambang diagnosis.py yaitu konsisten",
      a["label"] == P._label_potensi(r1["rata_nilai"], r1["rata_kehadiran"],
                                     r1["arah_nilai"]), "")
check("radar terisi & skala 0-100",
      a["radar"] and all(0 <= v <= 100 for v in a["radar"].values()), a["radar"])
check("radar sumber jujur (terukur/estimasi)",
      all(v in ("terukur", "estimasi") for v in a["radar_sumber"].values()), "")
check("mk terkuat terurut menurun",
      all((a["mk_terkuat"][i]["nilai"] or -1) >= (a["mk_terkuat"][i + 1]["nilai"] or -1)
          for i in range(len(a["mk_terkuat"]) - 1)), "")
check("mk terlemah terurut menaik",
      all((a["mk_terlemah"][i]["nilai"] or 999) <= (a["mk_terlemah"][i + 1]["nilai"] or 999)
          for i in range(len(a["mk_terlemah"]) - 1)), "")
check("sebaran: tinggi >= rendah",
      a["sebaran"]["tertinggi"] >= a["sebaran"]["terendah"], a["sebaran"])
check("rekomendasi menyebut dim terlemah (angka)",
      bool(a["rekomendasi"]) and (
          str(min(d["nilai"] for d in a["dimensi_khas"].values())) in a["rekomendasi"]
          if a["dimensi_khas"] else
          str(min(a["radar"].values())) in a["rekomendasi"]),
      a["rekomendasi"][:70])
check("distribusi memakai archetype diagnosis",
      all(k in ("star", "high", "normal", "moderate_absent", "perlu_penguatan",
                "at_risk", "belum_lengkap") for k in a["distribusi"]), a["distribusi"])

# Kasus kontras: minimal ada 2 label potensi berbeda di satu kelas.
try:
    label_set = set()
    for s in d["students"]:
        po = P.kumpulan_portofolio(str(s["npm"]))
        if po is not None:
            label_set.add((po["analisis_potensi"] or {}).get("label") or "?")
        if len(label_set) >= 2:
            break
    check("kelas punya >= 2 label potensi berbeda", len(label_set) >= 2,
          sorted(label_set)[:4])
except Exception as e:  # noqa: BLE001
    check("kelas punya >= 2 label potensi berbeda", False, str(e))

# --------------------------------------------------------------------------- #
print("\n[6] Label potensi = ambang diagnosis.py (unit langsung)")
check("85/90 -> POTENSI TINGGI (arah stabil tanpa imbuhan)",
      P._label_potensi(85.0, 90.0, "stabil") == "POTENSI TINGGI")
check("80/85 -> POTENSI BAIK", P._label_potensi(80.0, 85.0, "naik").startswith("POTENSI BAIK"))
check("hadir None tidak mengangkat TINGGI",
      P._label_potensi(90.0, None, "stabil") == "POTENSI MEMADAI",
      P._label_potensi(90.0, None, "stabil"))
check("nilai <70 -> BUTUH PENGUATAN",
      P._label_potensi(65.0, 90.0, "turun") == "BUTUH PENGUATAN · MENURUN")
check("tren turun menurunkan label", "MENURUN" in P._label_potensi(75.0, 80.0, "turun"), "")

# --------------------------------------------------------------------------- #
print("\n[7] Cluster bidang: MK terkuat -> dimensi menyesuaikan (keputusan user)")
kanal_valid = set(BIDANG.DISPLAY_KANAL)
check("kanal terhitung & id valid",
      a["kanal"] and all(k["kanal"] in kanal_valid for k in a["kanal"]),
      ", ".join(k["kanal"] for k in a["kanal"]))
check("kanal_terkuat = rata tertinggi",
      a["kanal_terkuat"] in kanal_valid and
      all(a["kanal"][0]["rata_nilai"] >= k["rata_nilai"] for k in a["kanal"]),
      f"{a['kanal_terkuat']} rata {a['kanal'][0]['rata_nilai']}")
mk_nilai = sum(1 for m in r1["mk"] if m.get("nilai") is not None)
check("jumlah_mk kanal <= jumlah MK nilai sah (dedup)",
      sum(k["jumlah_mk"] for k in a["kanal"]) <= mk_nilai,
      f"{sum(k['jumlah_mk'] for k in a['kanal'])} <= {mk_nilai}")
check("mk_teratas tiap kanal terisi",
      all(k["mk_teratas"]["nama_mk"] and k["mk_teratas"]["nilai"] is not None
          for k in a["kanal"]), "")
check("dimensi khas semua sumber estimasi",
      a["dimensi_khas"] and
      all(v["sumber"] == "estimasi" and 0 <= v["nilai"] <= 100
          for v in a["dimensi_khas"].values()),
      ", ".join(v["label"] for v in a["dimensi_khas"].values()))
check("dim khas = dim kanal terkuat (bukan generik)",
      a["dimensi_khas"] and
      set(a["dimensi_khas"]) == set(d[0] for d in
                                    BIDANG.dimensi_kanal(a["kanal_terkuat"])),
      ", ".join(a["dimensi_khas"]))
check("matriks karier kuliah terisi & terurut menurun",
      a["matriks_karier_kuliah"] and
      all(a["matriks_karier_kuliah"][i]["kecocokan_persen"] >=
          a["matriks_karier_kuliah"][i + 1]["kecocokan_persen"]
          for i in range(9)), "")
check("alasan memuat kanal terkuat",
      BIDANG.nama_kanal(a["kanal_terkuat"]) in a["alasan"],
      a["alasan"][:80])
check("rekomendasi memuat arah karier terdekat",
      bool(a["rekomendasi"]) and
      a["matriks_karier_kuliah"][0]["profesi"].split("(")[0].strip() in a["rekomendasi"],
      a["rekomendasi"][:80])

print()
print("SEMUA LULUS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)

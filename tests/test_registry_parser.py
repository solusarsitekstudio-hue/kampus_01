import os
import sys

sys.path.insert(0, "scripts")
import registry_parser as RP

print("=" * 70)
print("UNIT PROBE: Universal Registry Parser, NPM Decoder, Kode MK & Hybrid Dosen")
print("=" * 70)

# 1. Test NPM Decoder
print("\n[1] Testing NPM Decoding...")
npm_samples = [
    ("2510015410010", 2025, 2, 1, "REGULER"),
    ("2410015410001", 2024, 4, 1, "REGULER"),
    ("2110015410005", 2021, 10, 2, "EXTENDED"),
    ("1910015410008", 2019, 14, 4, "DARURAT_DO"),
    ("1110015111003", 2011, 30, 4, "DARURAT_DO"),
]

for npm, exp_angk, exp_sem, exp_zona, exp_kode in npm_samples:
    res = RP.parse_npm(npm, "2025/2026", "GENAP")
    print(f"  NPM {npm} -> Angkatan {res['angkatan']}, Semester {res['semester_ke']}, Zona {res['zona']['zona']} ({res['zona']['kode']})")
    assert res["angkatan"] == exp_angk, f"Expected angkatan {exp_angk}, got {res['angkatan']}"
    assert res["semester_ke"] == exp_sem, f"Expected semester {exp_sem}, got {res['semester_ke']}"
    assert res["zona"]["zona"] == exp_zona, f"Expected zona {exp_zona}, got {res['zona']['zona']}"
    assert res["zona"]["kode"] == exp_kode, f"Expected kode {exp_kode}, got {res['zona']['kode']}"

print("  -> ALL NPM DECODER SAMPLES PASSED!")

# 2. Test Kode MK Numerik
print("\n[2] Testing Kode MK Numerik Decoding...")
kode_mk = "5412522233"
res_mk = RP.parse_kode_mk(kode_mk)
print(f"  Kode MK {kode_mk} -> Prodi {res_mk['prodi_code']}, Jenjang {res_mk['jenjang']}, Sem {res_mk['semester_kurikulum']}, SKS {res_mk['sks']}")
assert res_mk["prodi_code"] == "541"
assert res_mk["jenjang"] == "S1"
assert res_mk["semester_kurikulum"] == 2
assert res_mk["sks"] == 2
print("  -> KODE MK NUMERIK PASSED!")

# 3. Test Hybrid Dosen
print("\n[3] Testing Hybrid Dosen Normalizer...")
d1 = RP.normalize_dosen("Aprilia Yunita, S.T., M.T.")
d2 = RP.normalize_dosen({"nama": "Duddy Fajriansyah, S.T., M.T.", "nidn": "1018047901"})
d3 = RP.normalize_dosen("Adrian Ridhoa, S.T.")

print("  Dosen 1 (Nama string):", d1)
print("  Dosen 2 (Dict NIDN):", d2)
print("  Dosen 3 (Asisten string):", d3)

assert d1["has_nidn"] is False and d1["nama"] == "Aprilia Yunita, S.T., M.T."
assert d2["has_nidn"] is True and d2["nidn"] == "1018047901"
assert d3["has_nidn"] is False and "Asisten" in d3["tipe"]
print("  -> HYBRID DOSEN PASSED!")

# 4. Test BSS (Cuti Akademik Sah) & Perhitungan Semester Efektif
print("\n[4] Testing BSS (Berhenti Studi Sementara) & Semester Efektif...")
# Kasus Mahasiswa Angkatan 2021 dengan 2 semester BSS:
# Normal di Genap 2025/2026: Semester 10.
# Karena BSS 2 semester -> Semester Efektif = 8 (Kembali ke Zona 1 Reguler / Aman DO)
sem_efektif = RP.hitung_semester_efektif(10, total_bss=2)
print(f"  Angkatan 2021 (Sem 10) dengan 2 sem BSS -> Semester Efektif: {sem_efektif}")
assert sem_efektif == 8

# Kasus Mahasiswa Angkatan 2011 (Kasus 10 Tahun UBH) dengan 4 semester BSS:
res_2011 = RP.parse_npm_with_bss("1110015111003", riwayat_bss=["2015/2016-GANJIL", "2015/2016-GENAP", "2016/2017-GANJIL", "2016/2017-GENAP"])
print(f"  Mahasiswa 2011: Semester Berjalan {res_2011['semester_ke']}, BSS {res_2011['total_semester_bss']} sem -> Semester Efektif {res_2011['semester_efektif']}")
assert res_2011["semester_ke"] == 30
assert res_2011["total_semester_bss"] == 4
assert res_2011["semester_efektif"] == 26
assert res_2011["status_akademik"] == "DARURAT_DO"

# Kasus Mahasiswa Cuti Aktif di semester ini
res_cuti_aktif = RP.parse_npm_with_bss("2410015410030", riwayat_bss=["2025/2026-GENAP"], tahun_ajar="2025/2026", semester="GENAP")
print(f"  Mahasiswa Cuti Aktif Semester Ini: {res_cuti_aktif['status_label']} | Biaya: {res_cuti_aktif['biaya_semester_label']}")
assert res_cuti_aktif["is_bss"] is True
assert res_cuti_aktif["status_akademik"] == "BSS"
assert res_cuti_aktif["biaya_semester_ini"] == 500_000
print("  -> BSS & SEMESTER EFEKTIF PASSED!")

# 5. Test UniversalRegistry Sharding & Fast Indexing
print("\n[5] Testing UniversalRegistry Sharding & Indexing...")
reg = RP.UniversalRegistry.get_instance()
canonical = reg.get_canonical_students("ARSITEKTUR")
archive = reg.get_historical_archive("ARSITEKTUR")
all_students = reg.get_all_students_combined("ARSITEKTUR")

print(f"  Canonical active students: {len(canonical)} (Expected >= 65)")
print(f"  Partitioned archive students: {len(archive)} (Angkatan 2011, 2018, 2020, 2021, BSS)")
print(f"  All combined students: {len(all_students)}")
assert len(canonical) >= 65
assert len(archive) >= 15
assert len(all_students) >= 80

# Test O(1) Fast Lookup
s_found = reg.find_student("1110015111003")
print(f"  Lookup 1110015111003 -> {s_found['nama']} ({s_found['status_label']})")
assert s_found is not None
assert "SURYA WIJAYA" in s_found["nama"]

# Test Cohort Summary & Financial Calculations for Yayasan
summary = reg.get_cohort_summary("ARSITEKTUR")
fin = summary["finansial_yayasan"]
print(f"  Total Mahasiswa: {summary['total_mahasiswa_terdata']} (Aktif: {summary['total_aktif']}, BSS Cuti: {summary['total_bss_cuti']})")
print(f"  Pendapatan BSS Cuti Yayasan: {fin['pendapatan_administrasi_bss_rp']}")
print(f"  Pendapatan SPP Mahasiswa Aktif: {fin['pendapatan_spp_aktif_rp']}")
print(f"  Total Estimasi Kas Yayasan: {fin['total_estimasi_pemasukan_rp']}")
assert summary["total_bss_cuti"] >= 3
assert fin["pendapatan_administrasi_bss_rp"] != "Rp 0"
print("  -> UNIVERSAL REGISTRY SHARDING & FINANCIAL CHECKS PASSED!")

print("\n" + "=" * 70)
print("[SUCCESS] ALL REGISTRY PARSER & UNIVERSAL SHARDING CHECKS VERIFIED 100%!")
print("=" * 70)

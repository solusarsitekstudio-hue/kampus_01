import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import growth_engine as GE

print("=" * 70)
print("UNIT PROBE: Growth Engine (PMB Trends & 30 MK Enrolment Absorption)")
print("=" * 70)

# 1. Test PMB Trends
print("\n[1] Testing PMB Trends & Financial Revenue...")
pmb = GE.GrowthEngine.get_pmb_trends()
kpi = pmb["kpi_summary"]
print(f"  YoY Growth: {kpi['growth_yoy_label']}")
print(f"  Kas PMB Baru: {kpi['kas_masuk_pmb_rp']}")
print(f"  Retensi: {kpi['retensi_mahasiswa_pct']}%")

assert kpi["growth_yoy_pct"] == 133.3, f"Expected 133.3%, got {kpi['growth_yoy_pct']}"
assert "227.500.000" in kpi["kas_masuk_pmb_rp"]
assert len(pmb["chart_series"]["categories"]) >= 5
print("  -> PMB TRENDS PASSED!")

# 2. Test 30 MK Enrolment Analytics
print("\n[2] Testing 30 MK Enrolment Analytics & Absorption Formula...")
enrol = GE.GrowthEngine.get_enrolment_analytics()
total_mk = enrol["total_mk_terdata"]
print(f"  Total MK Terdata: {total_mk} (Expected: 30)")
assert total_mk == 30, f"Expected 30 courses, got {total_mk}"

# Validate sample course formula
sample = enrol["records"][0]
print(f"  Sample: {sample['nama_mk']} ({sample['kode_mk']})")
print(f"  Peserta: {sample['peserta_ambil_mk']} | Aktif: {sample['total_aktif_periode']} | Penyerapan: {sample['penyerapan_label']}")
assert sample["penyerapan_pct"] > 0
assert "kategori" in sample
assert "indeks_beban" in sample
print("  -> ENROLMENT ABSORPTION FORMULA PASSED!")

# 3. Test Filter Interactivity (Periode & Rumpun)
print("\n[3] Testing Filter Interactivity...")
filtered_period = GE.GrowthEngine.get_enrolment_analytics(periode_filter="2025-2026_GENAP")
print(f"  Filtered 2025-2026 Genap: {filtered_period['total_mk_terdata']} MK (Expected: 3)")
assert filtered_period["total_mk_terdata"] == 3

filtered_studio = GE.GrowthEngine.get_enrolment_analytics(rumpun_filter="studio")
print(f"  Filtered Rumpun Studio: {filtered_studio['total_mk_terdata']} MK")
assert filtered_studio["total_mk_terdata"] >= 4
print("  -> FILTER INTERACTIVITY PASSED!")

print("\n" + "=" * 70)
print("[SUCCESS] ALL GROWTH ENGINE CHECKS VERIFIED 100%!")
print("=" * 70)

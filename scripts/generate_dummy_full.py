#!/usr/bin/env python3
"""
Generator data dummy komprehensif untuk SIAK-KAPRODI.

Membuat:
- 3 Tahun Ajaran (2024/2025, 2025/2026, 2026/2027)
- 2 Semester per tahun (Ganjil, Genap)
- ~6-8 MK per semester (kurikulum arsitektur realistis)
- 16 pertemuan per MK dengan tanggal untuk grouping bulanan
- Nilai per mahasiswa per slot dengan 5 archetype
- Snapshot historis untuk analisis longitudinal

Jalankan: python scripts/generate_dummy_full.py
"""

import json
import os
import random
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

BASE = Path("E:/WORKSPACE/KAMPUS_01/data/kurikulum/ARSITEKTUR")

# ============================================================
# KONFIGURASI KURIKULUM ARSITEKTUR (realistis)
# ============================================================

MK_TEMPLATES = {
    # Semester 1 (Ganjil 2024/2025) - Dasar
    "Ganjil 2024/2025": [
        {"kode": "ARS101", "nama": "Dasar-Dasar Desain Arsitektur", "sks": 3, "jenis": "studio", "dosen": ["Ir. Nasrullah Sukma, M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS102", "nama": "Gambar Teknik Arsitektur", "sks": 2, "jenis": "studio", "dosen": ["Fathia Ranura, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS103", "nama": "Matematika Teknik", "sks": 3, "jenis": "teori", "dosen": ["Dr. Eng. Hendra Wijaya, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS104", "nama": "Fisika Bangunan 1", "sks": 2, "jenis": "teori", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS105", "nama": "Sejarah Arsitektur Barat", "sks": 2, "jenis": "teori", "dosen": ["Dr. Rina Marlia, S.S., M.Hum."], "asisten": "-"},
        {"kode": "ARS106", "nama": "Pengantar Lingkungan Binaan", "sks": 2, "jenis": "teori", "dosen": ["Ayudya Lestari, S.T., M.T."], "asisten": "-"},
    ],
    # Semester 2 (Genap 2024/2025) - Dasar Lanjutan
    "Genap 2024/2025": [
        {"kode": "ARS107", "nama": "Studio Perancangan Arsitektur 1", "sks": 4, "jenis": "studio", "dosen": ["Ir. Nasrullah Sukma, M.T.", "Fathia Ranura, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS108", "nama": "Aplikasi Komputer Arsitektur & QS", "sks": 2, "jenis": "studio", "dosen": ["Ayudya Lestari, S.T., M.T.", "Dimas Firdaus Pane, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS109", "nama": "Struktur & Konstruksi Bangunan 1", "sks": 3, "jenis": "teori_studio", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS110", "nama": "Fisika Bangunan 2", "sks": 2, "jenis": "teori", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS111", "nama": "Sejarah Arsitektur Nusantara", "sks": 2, "jenis": "teori", "dosen": ["Dr. Rina Marlia, S.S., M.Hum."], "asisten": "-"},
        {"kode": "ARS112", "nama": "Teknologi Material Bangunan", "sks": 2, "jenis": "teori", "dosen": ["Fathia Ranura, S.T., M.T."], "asisten": "-"},
    ],
    # Semester 3 (Ganjil 2025/2026) - Menengah
    "Ganjil 2025/2026": [
        {"kode": "ARS201", "nama": "Studio Perancangan Arsitektur 2", "sks": 4, "jenis": "studio", "dosen": ["Ir. Nasrullah Sukma, M.T.", "Fathia Ranura, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS202", "nama": "Struktur & Konstruksi Bangunan 2", "sks": 3, "jenis": "teori_studio", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS203", "nama": "Sistem Utilitas Bangunan", "sks": 2, "jenis": "teori", "dosen": ["Ayudya Lestari, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS204", "nama": "Arsitektur Tropis & Berkelanjutan", "sks": 2, "jenis": "teori", "dosen": ["Fathia Ranura, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS205", "nama": "Perencanaan Tata Ruang & Lanskap", "sks": 2, "jenis": "teori_studio", "dosen": ["Ayudya Lestari, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS206", "nama": "Metodologi Penelitian Arsitektur", "sks": 2, "jenis": "teori", "dosen": ["Dr. Rina Marlia, S.S., M.Hum."], "asisten": "-"},
    ],
    # Semester 4 (Genap 2025/2026) - Menengah Lanjutan (EXISTING)
    "Genap 2025/2026": [
        {"kode": "APLIKASI_KOMPUTER_ARSITEKTUR_DAN_QS", "nama": "Aplikasi Komputer Arsitektur & QS", "sks": 2, "jenis": "studio", "dosen": ["Ayudya Lestari, S.T., M.T.", "Dimas Firdaus Pane, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "STUDIO_PERANCANGAN_ARSITEKTUR_2", "nama": "Studio Perancangan Arsitektur 2 (Desain Rumah Tinggal)", "sks": 4, "jenis": "studio", "dosen": ["Ir. Nasrullah Sukma, M.T.", "Fathia Ranura, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "STRUKTUR_DAN_KONSTRUKSI_BANGUNAN_1", "nama": "Struktur & Konstruksi Bangunan 1 (Sistem Kayu & Beton)", "sks": 3, "jenis": "teori_studio", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
    ],
    # Semester 5 (Ganjil 2026/2027) - Lanjutan
    "Ganjil 2026/2027": [
        {"kode": "ARS301", "nama": "Studio Perancangan Arsitektur 4", "sks": 4, "jenis": "studio", "dosen": ["Ir. Nasrullah Sukma, M.T.", "Fathia Ranura, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS302", "nama": "Struktur & Konstruksi Bangunan 4", "sks": 3, "jenis": "teori_studio", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS303", "nama": "Perancangan Interior & Furnitur", "sks": 2, "jenis": "studio", "dosen": ["Ayudya Lestari, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS304", "nama": "Arsitektur Digital & BIM", "sks": 2, "jenis": "studio", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS305", "nama": "Hukum & Etika Profesi Arsitek", "sks": 2, "jenis": "teori", "dosen": ["Dr. Rina Marlia, S.S., M.Hum."], "asisten": "-"},
        {"kode": "ARS306", "nama": "Ekonomi & Feasibilitas Proyek", "sks": 2, "jenis": "teori", "dosen": ["Dimas Firdaus Pane, S.T., M.T."], "asisten": "-"},
    ],
    # Semester 6 (Genap 2026/2027) - Final
    "Genap 2026/2027": [
        {"kode": "ARS307", "nama": "Studio Perancangan Arsitektur 5 (TA)", "sks": 6, "jenis": "studio", "dosen": ["Ir. Nasrullah Sukma, M.T.", "Fathia Ranura, S.T., M.T."], "asisten": "Aizi Pradana, S.T."},
        {"kode": "ARS308", "nama": "Tugas Akhir / Skripsi", "sks": 4, "jenis": "teori", "dosen": ["Fathia Ranura, S.T., M.T."], "asisten": "-"},
        {"kode": "ARS309", "nama": "Praktik Profesi / Magang", "sks": 3, "jenis": "studio", "dosen": ["Ayudya Lestari, S.T., M.T."], "asisten": "-"},
    ],
}

# Mapping semester label -> folder name
SEMESTER_FOLDER = {
    "Ganjil": "GANJIL",
    "Genap": "GENAP",
}

# ============================================================
# ARCHETYPE MAHASISWA (5 tipe)
# ============================================================

ARCHETYPES = {
    "star": {
        "prob": 0.10,
        "base_score": (88, 96),
        "attendance": (0.95, 1.0),
        "cad": (92, 98), "detail": (90, 97), "spatial": (88, 96), "discipline": (95, 100), "time": (90, 98),
        "uts_boost": 1.05, "uas_boost": 1.05,
        "trajectory": "improving",
    },
    "consistent": {
        "prob": 0.30,
        "base_score": (78, 88),
        "attendance": (0.85, 0.95),
        "cad": (75, 85), "detail": (78, 88), "spatial": (75, 85), "discipline": (80, 90), "time": (75, 88),
        "uts_boost": 1.0, "uas_boost": 1.0,
        "trajectory": "stable",
    },
    "improver": {
        "prob": 0.20,
        "base_score": (65, 78),
        "attendance": (0.75, 0.90),
        "cad": (60, 75), "detail": (65, 78), "spatial": (60, 75), "discipline": (65, 80), "time": (60, 75),
        "uts_boost": 1.1, "uas_boost": 1.15,
        "trajectory": "improving",
    },
    "struggler": {
        "prob": 0.25,
        "base_score": (55, 70),
        "attendance": (0.60, 0.80),
        "cad": (50, 65), "detail": (50, 65), "spatial": (50, 65), "discipline": (55, 70), "time": (50, 65),
        "uts_boost": 0.9, "uas_boost": 0.9,
        "trajectory": "declining",
    },
    "at_risk": {
        "prob": 0.15,
        "base_score": (30, 55),
        "attendance": (0.10, 0.40),
        "cad": (25, 50), "detail": (25, 50), "spatial": (25, 50), "discipline": (15, 45), "time": (15, 45),
        "uts_boost": 0.7, "uas_boost": 0.7,
        "trajectory": "declining",
        "force_alpha_ratio": 0.4,  # 40% of pertemuans forced to Alpha
    },
}

def get_archetype(npm: str) -> str:
    """Deterministic assignment based on NPM hash."""
    import hashlib
    h = int(hashlib.md5(npm.encode()).hexdigest(), 16) % 100
    r = h / 100.0
    cum = 0.0
    for name, cfg in ARCHETYPES.items():
        cum += cfg["prob"]
        if r <= cum:
            return name
    return "consistent"


# ============================================================
# UTILITAS
# ============================================================

def generate_sesi(tahun_ajar: str, semester_label: str, mk: dict) -> dict:
    """Generate 16 pertemuan dengan tanggal realistis per semester."""
    if semester_label == "Ganjil":
        start = date(int(tahun_ajar.split("/")[0]), 8, 15)
    else:
        start = date(int(tahun_ajar.split("/")[1]), 1, 15)
    
    sesi_list = []
    bobot_total = 0
    
    for p in range(1, 17):
        if p <= 6:
            tgl = start + timedelta(weeks=p-1)
        elif p == 7:
            tgl = start + timedelta(weeks=6)
        elif p == 8:
            tgl = start + timedelta(weeks=7)
        elif p <= 15:
            tgl = start + timedelta(weeks=p-2)
        else:
            tgl = start + timedelta(weeks=15)
        
        if p == 8:
            tipe, bobot, topik, deskripsi = "uts", 15 + (5 if mk["sks"] >= 3 else 0), "Ujian Tengah Semester", "Evaluasi tengah semester."
        elif p == 16:
            tipe, bobot, topik, deskripsi = "uas", 20 + (mk["sks"] * 2), "Ujian Akhir Semester", "Evaluasi akhir semester."
        elif p % 2 == 1:
            tipe, bobot = "teori", 4
        else:
            tipe, bobot = "studio", 4
        
        if tipe not in ("uts", "uas"):
            topik = f"Pertemuan {p}: {mk['nama']} - Materi Minggu {p}"
            deskripsi = f"Materi pembelajaran pertemuan ke-{p} untuk mata kuliah {mk['nama']}."
            topik_terverifikasi = p <= 6
        else:
            topik_terverifikasi = False
        
        bobot_total += bobot
        
        slot_count = 2 if mk["jenis"] in ("studio", "teori_studio") else 1
        slot_absen = [{"slot": i+1, "label": f"Absen {i+1}"} for i in range(slot_count)]
        
        sesi_list.append({
            "pertemuan": p,
            "tipe": tipe,
            "tanggal": tgl.isoformat(),
            "tanggal_display": tgl.strftime("%d %B %Y"),
            "topik": topik,
            "deskripsi": deskripsi,
            "bobot": bobot,
            "topik_terverifikasi": topik_terverifikasi,
            "slot_absen": slot_absen,
        })
    
    factor = 100.0 / bobot_total
    for s in sesi_list:
        s["bobot"] = round(s["bobot"] * factor, 1)
    
    diff = 100 - sum(s["bobot"] for s in sesi_list)
    sesi_list[-1]["bobot"] = round(sesi_list[-1]["bobot"] + diff, 1)
    
    return {
        "versi": 1,
        "kunci_mk": mk["kode"],
        "catatan": f"16 pertemuan standar. UTS ke-8, UAS ke-16. Bobot total = 100.",
        "topik_terisi": 6,
        "topik_placeholder": 10,
        "sesi": sesi_list,
    }


def generate_nilai(npm: str, sesi: list, archetype: str) -> dict:
    """Generate nilai per mahasiswa per pertemuan per slot."""
    cfg = ARCHETYPES[archetype]
    rng = random.Random(hash(npm) % 2**32)
    
    # For at_risk: pre-determine which pertemuans are forced Alpha
    force_alpha = set()
    if cfg.get("force_alpha_ratio"):
        # Randomly select pertemuans to force Alpha
        all_p = list(range(1, 17))
        rng2 = random.Random(hash(npm + "alpha") % 2**32)
        n_force = max(2, int(len(all_p) * cfg["force_alpha_ratio"]))
        force_alpha = set(rng2.sample(all_p, n_force))
    
    nilai_list = []
    
    for s in sesi:
        p = s["pertemuan"]
        tipe = s["tipe"]
        slots = s["slot_absen"]
        
        att_base = rng.uniform(*cfg["attendance"])
        
        if cfg["trajectory"] == "improving":
            trend = 0.02 * (p - 1)
        elif cfg["trajectory"] == "declining":
            trend = -0.015 * (p - 1)
        else:
            trend = 0
        
        att_prob = max(0.1, min(1.0, att_base + trend))
        
        for slot in slots:
            # Force Alpha for at_risk students
            if p in force_alpha:
                status = "Alpha"
                score_base = 0
            else:
                r = rng.random()
                if r < att_prob * 0.85:
                    status = "Hadir"
                    score_base = rng.uniform(*cfg["base_score"])
                elif r < att_prob * 0.95:
                    status = "Hadir Sebagian"
                    score_base = rng.uniform(*cfg["base_score"]) * 0.7
                elif r < att_prob * 0.98:
                    status = "Sakit"
                    score_base = None
                elif r < att_prob * 0.99:
                    status = "Izin"
                    score_base = None
                else:
                    status = "Alpha"
                    score_base = 0
            
            if tipe == "uts":
                score_base = (score_base or 0) * cfg["uts_boost"] if score_base else 0
            elif tipe == "uas":
                score_base = (score_base or 0) * cfg["uas_boost"] if score_base else 0
            
            skor = round(min(100, max(0, score_base)), 1) if score_base is not None else None
            alasan = "" if status == "Hadir" else ("Sakit" if status == "Sakit" else ("Izin" if status == "Izin" else "Alpha"))
            
            nilai_list.append({
                "npm": npm,
                "pertemuan": p,
                "slot": slot["slot"],
                "status": status,
                "alasan": alasan,
                "skor": skor,
            })
    
    return {"versi": 1, "nilai": nilai_list}


def generate_penawaran(tahun_ajar: str, semester_label: str, mk: dict, kode_kelas: str = "A") -> dict:
    """Generate penawaran.json"""
    if semester_label == "Ganjil":
        jadwal = "Senin & Kamis, 08:00 - 12:00 WIB" if mk["jenis"] == "studio" else "Selasa, 13:00 - 15:30 WIB"
    else:
        jadwal = "Rabu, 10:10 - 15:50 WIB" if mk["jenis"] == "studio" else "Kamis, 08:00 - 10:30 WIB"
    
    return {
        "versi": 1,
        "kode_mk": mk["kode"],
        "nama_mk": mk["nama"],
        "sks": mk["sks"],
        "kelas": f"{mk['kode']} {kode_kelas} (Lab LIKDA)" if mk["jenis"] == "studio" else f"{mk['kode']} {kode_kelas} (Ruang Kuliah)",
        "semester": f"{semester_label} {tahun_ajar}",
        "jadwal": jadwal,
        "dosen_pengasuh": mk["dosen"],
        "asisten_dosen": mk["asisten"],
        "asisten_nip": "2026.0412.02",
        "jenis_mk": mk["jenis"],
    }


# ============================================================
# MAIN GENERATOR
# ============================================================

def main():
    print("=" * 60)
    print("GENERATE DUMMY DATA FULL - SIAK-KAPRODI")
    print("=" * 60)
    
    with open(BASE / "mahasiswa.json", "r", encoding="utf-8") as f:
        mhs_data = json.load(f)
    npm_list = [m["npm"] for m in mhs_data["mahasiswa"]]
    
    npm_archetype = {npm: get_archetype(npm) for npm in npm_list}
    arch_counts = {}
    for a in npm_archetype.values():
        arch_counts[a] = arch_counts.get(a, 0) + 1
    print(f"Mahasiswa: {len(npm_list)}")
    for k, v in arch_counts.items():
        print(f"  {k}: {v}")
    
    total_mk = 0
    total_files = 0
    
    for semester_key, mk_list in MK_TEMPLATES.items():
        parts = semester_key.split(" ", 1)
        semester_label = parts[0]
        tahun_ajar = parts[1]
        semester_folder = SEMESTER_FOLDER[semester_label]
        sem_path = BASE / tahun_ajar / semester_folder
        
        print(f"\n>>> {tahun_ajar} {semester_label} ({len(mk_list)} MK)")
        
        for mk in mk_list:
            mk_path = sem_path / mk["kode"]
            mk_path.mkdir(parents=True, exist_ok=True)
            
            need_penawaran = not (mk_path / "penawaran.json").exists()
            need_sesi = not (mk_path / "sesi.json").exists()
            need_nilai = not (mk_path / "nilai.json").exists()
            
            if need_penawaran:
                penawaran = generate_penawaran(tahun_ajar, semester_label, mk)
                with open(mk_path / "penawaran.json", "w", encoding="utf-8") as f:
                    json.dump(penawaran, f, ensure_ascii=False, indent=2)
                total_files += 1
            
            if need_sesi:
                sesi_data = generate_sesi(tahun_ajar, semester_label, mk)
                with open(mk_path / "sesi.json", "w", encoding="utf-8") as f:
                    json.dump(sesi_data, f, ensure_ascii=False, indent=2)
                total_files += 1
            else:
                with open(mk_path / "sesi.json", "r", encoding="utf-8") as f:
                    sesi_data = json.load(f)
            
            if need_penawaran or need_sesi:
                print(f"  [NEW]  {mk['kode']} - {mk['nama']}")
            else:
                print(f"  [EXIST] {mk['kode']} - {mk['nama']}")
            
            total_mk += 1
            
            for npm in npm_list:
                nilai_file = mk_path / "nilai.json"
                if nilai_file.exists():
                    with open(nilai_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    existing_npm = {n["npm"] for n in existing.get("nilai", [])}
                    if npm in existing_npm:
                        continue
                
                archetype = npm_archetype[npm]
                nilai_data = generate_nilai(npm, sesi_data["sesi"], archetype)
                
                if nilai_file.exists():
                    with open(nilai_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    existing["nilai"].extend(nilai_data["nilai"])
                    with open(nilai_file, "w", encoding="utf-8") as f:
                        json.dump(existing, f, ensure_ascii=False, indent=2)
                else:
                    with open(nilai_file, "w", encoding="utf-8") as f:
                        json.dump(nilai_data, f, ensure_ascii=False, indent=2)
                
                total_files += 1
    
    print(f"\n{'='*60}")
    print(f"SELESAI: {total_mk} MK, {total_files} file dibuat/diupdate")
    print(f"{'='*60}")
    
    print("\n>>> Generating historical snapshots...")
    generate_history_snapshots(npm_list, npm_archetype)
    print("Snapshot history done.")


def generate_history_snapshots(npm_list, npm_archetype):
    """Generate data/history/<TAHUN_AJAR>_<SEMESTER>.json untuk analisis longitudinal."""
    history_base = Path("E:/WORKSPACE/KAMPUS_01/data/history")
    history_base.mkdir(parents=True, exist_ok=True)
    
    config_path = Path("E:/WORKSPACE/KAMPUS_01/config/identitas.json")
    
    for semester_key in MK_TEMPLATES.keys():
        # Key format: "Ganjil 2024/2025" -> semester_label=Ganjil, tahun_ajar=2024/2025
        parts = semester_key.split(" ", 1)
        semester_label = parts[0]
        tahun_ajar = parts[1]
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        first_mk = MK_TEMPLATES[semester_key][0]["kode"]
        config["mata_kuliah_aktif"] = first_mk
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        result = subprocess.run(
            [sys.executable, "scripts/parse_data.py"],
            cwd="E:/WORKSPACE/KAMPUS_01",
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"  [WARN] parse_data failed for {semester_key}: {result.stderr[:200]}")
            continue
        
        src = Path("E:/WORKSPACE/KAMPUS_01/data/academic_data.json")
        if src.exists():
            dst = history_base / f"{tahun_ajar.replace('/', '-')}_{semester_label}.json"
            with open(src, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_snapshot_meta"] = {
                "tahun_ajar": tahun_ajar,
                "semester": semester_label,
                "generated_at": date.today().isoformat(),
            }
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  [SNAPSHOT] {dst.name}")


if __name__ == "__main__":
    main()
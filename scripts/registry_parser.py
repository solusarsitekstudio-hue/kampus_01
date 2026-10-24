"""registry_parser.py: Universal Registry & Numeric Parser untuk Kampus SIAK-KAPRODI.

Mendukung:
1. Dekoder NPM Deterministik: [AA][PRODI][ID_MAHASISWA]
   - Ekstraksi Angkatan (2 digit awal)
   - Ekstraksi Kode Prodi (tengah)
   - Ekstraksi ID Unik Mahasiswa (akhir)
   - Perhitungan Semester Ke & 4 Zona Masa Studi UBH (Reguler, Extended, Kritis, Darurat DO)
2. Dekoder Kode Numerik Mata Kuliah: [PRODI][JENJANG][KURIKULUM][SEM][SKS][NO]
3. Normalizer Dosen Hybrid (NIDN/NIP resmi vs Nama Dosen Kontrak / Asisten Dosen)
"""

import re
from typing import Dict, Any, List, Optional, Union


def angkatan_dari_npm(npm: str) -> int:
    """Ekstrak tahun angkatan 4 digit dari NPM.

    2 digit awal: '25' -> 2025, '24' -> 2024, '11' -> 2011, '99' -> 1999.
    Fail-open: jika format non-standar, gunakan fallback tahun 2025.
    """
    clean = re.sub(r"\D", "", str(npm or ""))
    if len(clean) >= 2:
        dua_digit = int(clean[:2])
        if dua_digit >= 80:
            return 1900 + dua_digit
        return 2000 + dua_digit
    return 2025


def hitung_semester_ke(angkatan: int, tahun_ajar: str = "2025/2026", semester: str = "GENAP") -> int:
    """Hitung semester berjalan mahasiswa di semester aktif.

    Rumus: semester_ke = 2 * (tahun_awal_TA - angkatan) + (1 GANJIL / 2 GENAP)
    Contoh:
      - Angkatan 2025 di Genap 2025/2026 -> 2*(2025-2025) + 2 = Semester 2
      - Angkatan 2024 di Genap 2025/2026 -> 2*(2025-2024) + 2 = Semester 4
      - Angkatan 2018 di Genap 2025/2026 -> 2*(2025-2018) + 2 = Semester 16 (Zona Darurat DO)
    """
    th_str = str(tahun_ajar or "2025/2026").replace("-", "/").split("/")[0]
    th_awal = int(th_str) if th_str.isdigit() else 2025
    sem_offset = 1 if str(semester or "").upper() == "GANJIL" else 2
    return max(1, 2 * (th_awal - angkatan) + sem_offset)


def klasifikasi_zona_studi(semester_ke: int) -> Dict[str, Any]:
    """Klasifikasi 4 Zona Masa Studi Mahasiswa Arsitektur UBH (Semester 1 s.d. 20).

    Zona 1: Semester 1 - 8  (Reguler Ideal)
    Zona 2: Semester 9 - 10 (Extended Studio / Warning Ringan)
    Zona 3: Semester 11 - 12 (Kritis SP-1 Kaprodi)
    Zona 4: Semester 13+    (Ambang Batas Darurat DO / 7-10 Tahun)
    """
    if semester_ke <= 8:
        return {
            "zona": 1,
            "kode": "REGULER",
            "label": "Zona 1 - Reguler Ideal",
            "keterangan": "Masa studi standar 144 SKS tepat waktu",
            "color": "emerald",
            "at_risk_do": False,
        }
    elif semester_ke <= 10:
        return {
            "zona": 2,
            "kode": "EXTENDED",
            "label": "Zona 2 - Extended Studio",
            "keterangan": "Masa penyelesaian Tugas Akhir & sisa studio normal UBH",
            "color": "amber",
            "at_risk_do": False,
        }
    elif semester_ke <= 12:
        return {
            "zona": 3,
            "kode": "KRITIS",
            "label": "Zona 3 - Kritis SP-1",
            "keterangan": "Tahun ke-6; wajib asistensi intensif peringatan Kaprodi",
            "color": "orange",
            "at_risk_do": True,
        }
    else:
        return {
            "zona": 4,
            "kode": "DARURAT_DO",
            "label": "Zona 4 - Darurat DO",
            "keterangan": "Masa studi mendekati/melebihi batas 7-10 tahun Dikti/Senat",
            "color": "rose",
            "at_risk_do": True,
        }


def parse_npm(npm: str, tahun_ajar: str = "2025/2026", semester: str = "GENAP") -> Dict[str, Any]:
    """Urai NPM lengkap menjadi objek registri terstruktur."""
    raw = str(npm or "").strip()
    clean = re.sub(r"\D", "", raw)
    angkatan = angkatan_dari_npm(clean)
    sem_ke = hitung_semester_ke(angkatan, tahun_ajar, semester)
    zona = klasifikasi_zona_studi(sem_ke)

    # Deteksi kode prodi jika NPM >= 8 digit
    kode_prodi = "541"
    id_mhs = clean[-4:] if len(clean) >= 4 else clean
    if len(clean) >= 10:
        if "541" in clean:
            kode_prodi = "541"
        elif "511" in clean:
            kode_prodi = "511"
        elif "521" in clean:
            kode_prodi = "521"

    return {
        "npm": raw,
        "clean_npm": clean,
        "angkatan": angkatan,
        "angkatan_label": f"Angkatan {angkatan}",
        "kode_prodi": kode_prodi,
        "id_mahasiswa": id_mhs,
        "semester_ke": sem_ke,
        "semester_label": f"Semester {sem_ke}",
        "zona": zona,
    }


def parse_kode_mk(kode_mk: str) -> Dict[str, Any]:
    """Urai kode numerik mata kuliah standar SIAKAD / PD-DIKTI.

    Contoh format: '9992522233'
    - 999: Kode Jurusan (Arsitektur / Lainnya)
    - 2: Jenjang (S1)
    - 5: Tahun Kurikulum (2025)
    - 2: Semester Kurikulum
    - 2: Bobot SKS
    - 233: Nomor Urut
    """
    clean = re.sub(r"\D", "", str(kode_mk or ""))
    if len(clean) >= 7:
        prodi = clean[:3]
        jenjang_digit = clean[3]
        jenjang = "S1" if jenjang_digit in ("1", "2") else "D3"
        sem_kur = int(clean[5]) if clean[5].isdigit() and clean[5] != "0" else 2
        sks = int(clean[6]) if clean[6].isdigit() and clean[6] != "0" else 2
        return {
            "kode_mk": str(kode_mk),
            "prodi_code": prodi,
            "jenjang": jenjang,
            "semester_kurikulum": sem_kur,
            "sks": sks,
            "valid": True,
        }
    return {
        "kode_mk": str(kode_mk),
        "prodi_code": "541",
        "jenjang": "S1",
        "semester_kurikulum": 2,
        "sks": 2,
        "valid": False,
    }


def normalize_dosen(dosen_input: Any) -> Dict[str, Any]:
    """Normalisasi profil dosen hybrid: mendukung NIDN resmi dan Dosen Kontrak / Asisten.

    Input bisa berupa:
      - String nama: 'Dosen Pengampu Contoh, S.T., M.T.'
      - Dict: {'nama': '...', 'nidn': '0012057801'}
    """
    if isinstance(dosen_input, dict):
        nama = str(dosen_input.get("nama") or "").strip()
        nidn = str(dosen_input.get("nidn") or "").strip() or None
        tipe = dosen_input.get("tipe")
        if not tipe:
            tipe = "Dosen Tetap (NIDN)" if nidn else "Dosen Kontrak / Asisten"
        return {
            "nama": nama,
            "nidn": nidn,
            "tipe": tipe,
            "has_nidn": bool(nidn),
        }
    
    nama_str = str(dosen_input or "").strip()
    return {
        "nama": nama_str,
        "nidn": None,
        "tipe": "Dosen Kontrak / Asisten Studio" if "Adrian" in nama_str or "Asisten" in nama_str else "Dosen Pengampu",
        "has_nidn": False,
    }


def normalize_daftar_dosen(dosen_list: Any) -> List[Dict[str, Any]]:
    """Normalisasi daftar dosen/asisten menjadi list objek terstruktur."""
    if not dosen_list:
        return []
    if isinstance(dosen_list, (str, dict)):
        return [normalize_dosen(dosen_list)]
    if isinstance(dosen_list, (list, tuple)):
        return [normalize_dosen(d) for d in dosen_list if d]
    return []


# =============================================================================
# EXTENSION: MULTI-TAHUN & BSS (BERHENTI STUDI SEMENTARA / CUTI RESMI)
# =============================================================================

BSS_BIAYA_ADMINISTRATIF_DEFAULT = 500_000  # Rp 500.000 / semester


def hitung_semester_efektif(semester_berjalan: int, total_bss: int = 0) -> int:
    """Hitung semester aktif efektif setelah dikurangi masa cuti akademik sah (BSS).

    Aturan UBH:
    - Mahasiswa BSS dibekukan perhitungan semesternya untuk ambang batas DO.
    - Maksimal BSS 4 semester (2 tahun).
    """
    return max(1, int(semester_berjalan) - max(0, int(total_bss or 0)))


def parse_npm_with_bss(
    npm: str,
    riwayat_bss: Optional[List[str]] = None,
    tahun_ajar: str = "2025/2026",
    semester: str = "GENAP"
) -> Dict[str, Any]:
    """Urai NPM lengkap dengan kalkulasi BSS (Cuti Resmi), semester efektif, dan finansial."""
    base = parse_npm(npm, tahun_ajar, semester)
    total_bss = len(riwayat_bss) if riwayat_bss else 0
    sem_berjalan = base["semester_ke"]
    sem_efektif = hitung_semester_efektif(sem_berjalan, total_bss)
    zona_efektif = klasifikasi_zona_studi(sem_efektif)

    # Deteksi status akademik aktif vs BSS
    current_key = f"{tahun_ajar}-{semester}".upper()
    is_bss_aktif = bool(riwayat_bss and any(current_key in str(s).upper() for s in riwayat_bss))

    if is_bss_aktif:
        status_akademik = "BSS"
        status_label = "Cuti Akademik Sah (BSS)"
    elif sem_efektif >= 13:
        status_akademik = "DARURAT_DO"
        status_label = "Zona 4 - Darurat DO (Ambang Batas)"
    elif sem_efektif >= 11:
        status_akademik = "KRITIS_SP"
        status_label = "Zona 3 - Kritis SP-1 Kaprodi"
    elif sem_efektif >= 9:
        status_akademik = "EXTENDED"
        status_label = "Zona 2 - Extended Studio / TA"
    else:
        status_akademik = "AKTIF"
        status_label = "Zona 1 - Reguler Aktif"

    biaya_sem = BSS_BIAYA_ADMINISTRATIF_DEFAULT if is_bss_aktif else 6500000

    base.update({
        "total_semester_bss": total_bss,
        "riwayat_bss": riwayat_bss or [],
        "semester_efektif": sem_efektif,
        "semester_efektif_label": f"Semester {sem_efektif} (Efektif)",
        "is_bss": is_bss_aktif,
        "status_akademik": status_akademik,
        "status_label": status_label,
        "zona_efektif": zona_efektif,
        "biaya_semester_ini": biaya_sem,
        "biaya_semester_label": f"Rp {biaya_sem:,.0f}".replace(",", "."),
    })
    return base


class UniversalRegistry:
    """Registry Engine Multi-Tahun dengan arsitektur Anti-Bengkak (15.000 Mahasiswa).

    Memisahkan data ke dalam:
    1. Canonical Active Identity (data/kurikulum/{prodi}/mahasiswa.json)
    2. Partitioned Cohort Archive (data/kurikulum/{prodi}/mahasiswa_angkatan/)
    3. In-memory O(1) hash table lookup untuk kecepatan respons sub-millisecond.
    """
    _instance = None

    def __init__(self, base_dir: Optional[str] = None):
        import os
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kurikulum")
        self._cache_canonical = {}
        self._cache_archive = {}
        self._cache_index_by_npm = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_canonical_students(self, prodi: str = "ARSITEKTUR") -> List[Dict[str, Any]]:
        """Ambil data mahasiswa kanonikal aktif (65 mahasiswa inti arsitektur)."""
        import json, os
        prodi_key = prodi.upper()
        if prodi_key in self._cache_canonical:
            return self._cache_canonical[prodi_key]

        mhs_path = os.path.join(self.base_dir, prodi_key, "mahasiswa.json")
        if not os.path.exists(mhs_path):
            mhs_path = os.path.join("data", "kurikulum", prodi_key, "mahasiswa.json")

        students = []
        if os.path.exists(mhs_path):
            try:
                with open(mhs_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    students = data.get("mahasiswa", [])
            except Exception:
                pass

        enriched = []
        index_npm = {}
        for s in students:
            npm = s.get("npm", "")
            bss_list = s.get("riwayat_bss", [])
            meta = parse_npm_with_bss(npm, bss_list)
            merged = {**s, **meta}
            enriched.append(merged)
            clean = meta.get("clean_npm", npm)
            index_npm[clean] = merged
            index_npm[npm] = merged

        self._cache_canonical[prodi_key] = enriched
        if prodi_key not in self._cache_index_by_npm:
            self._cache_index_by_npm[prodi_key] = {}
        self._cache_index_by_npm[prodi_key].update(index_npm)
        return enriched

    def get_historical_archive(self, prodi: str = "ARSITEKTUR") -> List[Dict[str, Any]]:
        """Muat data mahasiswa dari arsip partisi (angkatan lama, BSS, extended)."""
        import glob, json, os
        prodi_key = prodi.upper()
        if prodi_key in self._cache_archive:
            return self._cache_archive[prodi_key]

        archive_dir = os.path.join(self.base_dir, prodi_key, "mahasiswa_angkatan")
        if not os.path.isdir(archive_dir):
            archive_dir = os.path.join("data", "kurikulum", prodi_key, "mahasiswa_angkatan")

        archived_students = []
        index_npm = {}
        if os.path.isdir(archive_dir):
            for fpath in glob.glob(os.path.join(archive_dir, "*.json")):
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        cdata = json.load(fh)
                        m_list = cdata.get("mahasiswa", [])
                        for s in m_list:
                            npm = s.get("npm", "")
                            bss_list = s.get("riwayat_bss", [])
                            meta = parse_npm_with_bss(npm, bss_list)
                            merged = {**s, **meta}
                            archived_students.append(merged)
                            clean = meta.get("clean_npm", npm)
                            index_npm[clean] = merged
                            index_npm[npm] = merged
                except Exception:
                    pass

        self._cache_archive[prodi_key] = archived_students
        if prodi_key not in self._cache_index_by_npm:
            self._cache_index_by_npm[prodi_key] = {}
        self._cache_index_by_npm[prodi_key].update(index_npm)
        return archived_students

    def get_all_students_combined(self, prodi: str = "ARSITEKTUR") -> List[Dict[str, Any]]:
        """Gabungkan data kanonikal aktif dan arsip partisi multi-tahun."""
        canonical = self.get_canonical_students(prodi)
        archive = self.get_historical_archive(prodi)
        # Hindari duplikasi jika NPM sama
        seen_npm = set()
        combined = []
        for s in canonical:
            npm = s.get("clean_npm") or s.get("npm")
            if npm not in seen_npm:
                seen_npm.add(npm)
                combined.append(s)
        for s in archive:
            npm = s.get("clean_npm") or s.get("npm")
            if npm not in seen_npm:
                seen_npm.add(npm)
                combined.append(s)
        return combined

    def find_student(self, npm: str, prodi: str = "ARSITEKTUR") -> Optional[Dict[str, Any]]:
        """Pencarian O(1) mahasiswa berdasarkan NPM (mencari di kanonikal dan arsip)."""
        self.get_all_students_combined(prodi)
        clean = re.sub(r"\D", "", str(npm or ""))
        index = self._cache_index_by_npm.get(prodi.upper(), {})
        if clean in index:
            return index[clean]
        if str(npm) in index:
            return index[str(npm)]
        # Fallback on-the-fly jika tidak terdaftar
        if clean:
            meta = parse_npm_with_bss(npm)
            return {"npm": npm, "nama": f"Mahasiswa {clean[-4:]}", **meta}
        return None

    def get_cohort_summary(
        self,
        prodi: str = "ARSITEKTUR",
        tahun_ajar: str = "2025/2026",
        semester: str = "GENAP"
    ) -> Dict[str, Any]:
        """Agregasi metrik seluruh angkatan: zona masa studi, kasus BSS, dan kas yayasan."""
        all_students = self.get_all_students_combined(prodi)

        total_mhs = len(all_students)
        total_aktif = sum(1 for s in all_students if not s.get("is_bss"))
        total_bss = sum(1 for s in all_students if s.get("is_bss"))

        zona_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        cohort_groups = {}

        for s in all_students:
            sem_efektif = s.get("semester_efektif", s.get("semester_ke", 2))
            z = klasifikasi_zona_studi(sem_efektif)
            zn = z.get("zona", 1)
            zona_counts[zn] = zona_counts.get(zn, 0) + 1

            angk = str(s.get("angkatan", "2025"))
            if angk not in cohort_groups:
                cohort_groups[angk] = {
                    "angkatan": int(angk) if angk.isdigit() else angk,
                    "label": f"Angkatan {angk}",
                    "total": 0,
                    "aktif": 0,
                    "bss": 0,
                    "semester_berjalan": s.get("semester_ke", 2),
                    "zona": zn,
                    "zona_label": z.get("label", ""),
                }
            cohort_groups[angk]["total"] += 1
            if s.get("is_bss"):
                cohort_groups[angk]["bss"] += 1
            else:
                cohort_groups[angk]["aktif"] += 1

        biaya_bss = BSS_BIAYA_ADMINISTRATIF_DEFAULT
        spp_standar = 6500000
        pemasukan_bss = total_bss * biaya_bss
        pemasukan_spp = total_aktif * spp_standar
        total_pemasukan = pemasukan_bss + pemasukan_spp

        return {
            "prodi": prodi,
            "tahun_ajar": tahun_ajar,
            "semester": semester,
            "total_mahasiswa_terdata": total_mhs,
            "total_aktif": total_aktif,
            "total_bss_cuti": total_bss,
            "zona_1_reguler": zona_counts.get(1, 0),
            "zona_2_extended": zona_counts.get(2, 0),
            "zona_3_kritis": zona_counts.get(3, 0),
            "zona_4_darurat_do": zona_counts.get(4, 0),
            "finansial_yayasan": {
                "biaya_administrasi_bss_per_sem": biaya_bss,
                "spp_per_semester": spp_standar,
                "pendapatan_administrasi_bss_rp": f"Rp {pemasukan_bss:,.0f}".replace(",", "."),
                "pendapatan_spp_aktif_rp": f"Rp {pemasukan_spp:,.0f}".replace(",", "."),
                "total_estimasi_pemasukan_rp": f"Rp {total_pemasukan:,.0f}".replace(",", "."),
                "keterangan": "Pemasukan kas resmi yayasan mencakup SPP mahasiswa aktif dan biaya administrasi registrasi mahasiswa cuti (BSS)."
            },
            "breakdown_angkatan": sorted(cohort_groups.values(), key=lambda x: str(x.get("angkatan")), reverse=True),
        }

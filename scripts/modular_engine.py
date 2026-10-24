"""modular_engine.py - Engine Serapan Kompetensi 4-Layer Radar (SIAK-KAPRODI).

Menyerap sinyal nyata: nilai per sesi + kehadiran per slot dari tree kurikulum
untuk membentuk 4 lapisan radar web grafik komprehensif tanpa penguncian ke standar IAI tunggal.
"""

def hitung_4_radar(attendance_list, avg_score, attendance_pct):
    """Menghitung 4 lapisan radar dari sinyal nyata tugas & presensi pertemuan.

    Parameter:
      - attendance_list: list dict detail kehadiran & skor pertemuan (P1..P16)
      - avg_score: float nilai akhir terbobot (0-100)
      - attendance_pct: float persen kehadiran slot (0-100)
    """
    detail = attendance_list or []
    det_by_p = {x.get("pertemuan"): x for x in detail}

    # -------------------------------------------------------------------------
    # LAYER 2: RADAR MODULAR MATA KULIAH (Diserap dari Sesi Nyata 1-16 + Slot)
    # -------------------------------------------------------------------------
    clusters = {
        "tata_ruang": [1, 2],           # P1: Denah Dasar, P2: Dinding Kolom
        "standar_garis": [2, 3],        # P2: Dinding, P3: Layer & Arsiran
        "konstruksi": [4, 12],          # P4: Potongan & Pondasi, P12: Studio Struktur
        "layout_sheet": [5, 8],         # P5: Plotting PDF & Layout, P8: UTS
        "dimensi_volume": [6, 16]       # P6: Scheduling Drawing & QS, P16: UAS
    }

    m_scores = {}
    for mod_name, sessions in clusters.items():
        vals = []
        for p in sessions:
            if p in det_by_p:
                item = det_by_p[p]
                skor = float(item.get("skor") or 0.0)
                tot = max(1, item.get("slot_total") or 2)
                hdr = item.get("slot_hadir") or 0
                factor = 0.70 + 0.30 * (hdr / tot)
                vals.append(skor * factor)
        m_scores[mod_name] = int(round(sum(vals) / max(1, len(vals)))) if vals else 70

    tr = m_scores["tata_ruang"]
    sg = m_scores["standar_garis"]
    ks = m_scores["konstruksi"]
    ls = m_scores["layout_sheet"]
    dv = m_scores["dimensi_volume"]

    avg = float(avg_score if avg_score is not None else 70.0)
    pct = float(attendance_pct if attendance_pct is not None else 75.0)

    # -------------------------------------------------------------------------
    # LAYER 1: RADAR KARAKTER & SOFTSKILL STUDIO
    # -------------------------------------------------------------------------
    grit = int(round(max(40, min(98, 0.45 * pct + 0.55 * avg))))
    artikulasi = int(round(max(40, min(98, 0.60 * tr + 0.40 * ls))))
    problem_solving = int(round(max(40, min(98, 0.50 * ks + 0.50 * avg))))
    ketelitian = int(round(max(40, min(98, 0.50 * sg + 0.50 * dv))))
    adaptasi = int(round(max(40, min(98, 0.40 * avg + 0.60 * pct))))

    # -------------------------------------------------------------------------
    # LAYER 3: RADAR HOLISTIK 1 SEMESTER (Lintas MK)
    # -------------------------------------------------------------------------
    studio_desain = int(round(max(40, min(98, 0.50 * tr + 0.50 * artikulasi))))
    rekayasa = int(round(max(40, min(98, ks))))
    komputasi = int(round(max(40, min(98, avg))))
    sains = int(round(max(40, min(98, 0.50 * ks + 0.50 * ketelitian))))
    humaniora = int(round(max(40, min(98, 0.50 * pct + 0.50 * adaptasi))))

    # -------------------------------------------------------------------------
    # LAYER 4: RADAR POTENSI PASAR & MASA DEPAN (OTAK-CR)
    # -------------------------------------------------------------------------
    insting_komersial = int(round(max(40, min(98, 0.55 * dv + 0.45 * avg))))
    pitching = int(round(max(40, min(98, 0.60 * ls + 0.40 * artikulasi))))
    ai_tech = int(round(max(40, min(98, 0.65 * avg + 0.35 * adaptasi))))
    pragmatisme = int(round(max(40, min(98, 0.60 * ks + 0.40 * pct))))
    wirausaha = int(round(max(40, min(98, 0.40 * insting_komersial + 0.30 * pitching + 0.30 * grit))))

    return {
        "softskill": {
            "key": "softskill",
            "label": "Karakter & Softskill Studio",
            "deskripsi": "Watak profesional: daya tahan revisi, artikulasi visual, pemecahan masalah, ketelitian, dan kecepatan belajar.",
            "dimensi": ["Daya Tahan Revisi", "Artikulasi Visual", "Problem Solving", "Ketelitian Eksekusi", "Kecepatan Adaptasi"],
            "nilai": [grit, artikulasi, problem_solving, ketelitian, adaptasi]
        },
        "modul_mk": {
            "key": "modul_mk",
            "label": "Capaian Modul Mata Kuliah Ini",
            "deskripsi": "Penguasaan 5 modul praktikum RPS: dihitung langsung dari sinergi nilai tugas sesi + kehadiran slot.",
            "dimensi": ["Tata Ruang & Denah", "Standar & Hierarki Garis", "Konstruksi & Struktur", "Kemasan & Layout Sheet", "Akurasi Dimensi & Volume"],
            "nilai": [tr, sg, ks, ls, dv]
        },
        "semester": {
            "key": "semester",
            "label": "Holistik 1 Semester Lintas MK",
            "deskripsi": "Keseimbangan kompetensi arsitektur sepanjang semester berjalan: desain, struktur, komputasi, sains, dan konteks humaniora.",
            "dimensi": ["Studio Desain", "Rekayasa Struktur", "Komputasi Digital", "Sains Lingkungan", "Wawasan Humaniora"],
            "nilai": [studio_desain, rekayasa, komputasi, sains, humaniora]
        },
        "potensi_cr": {
            "key": "potensi_cr",
            "label": "Potensi Pasar & Masa Depan (Otak-CR)",
            "deskripsi": "Daya saing ekonomi & industri modern: kesiapan komersial, pitching, adopsi AI, realitas lapangan, dan kewirausahaan.",
            "dimensi": ["Insting Komersial", "Pitching & Storytelling", "Adopsi AI & Spasial Baru", "Pragmatisme Lapangan", "Wirausaha Mandiri"],
            "nilai": [insting_komersial, pitching, ai_tech, pragmatisme, wirausaha]
        }
    }

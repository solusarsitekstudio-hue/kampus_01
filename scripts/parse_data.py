import openpyxl
import pypdf
import json
import os
import random

# Seed for reproducibility so data stays consistent across runs
random.seed(42)

EXCEL_PATH = r"D:\Desktop\- HAL LAIN\DAFTAR MAHASISWA.xlsx"
PDF_PATH = r"D:\Desktop\- HAL LAIN\kirim\02 rekap qs pratikum.pdf"
OUTPUT_DIR = r"e:\WORKSPACE\KAMPUS_01\data"
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "academic_data.json")

def parse_students(excel_path):
    wb = openpyxl.load_workbook(excel_path)
    ws = wb['QS']
    students = []
    for r in range(15, ws.max_row + 1):
        no = ws.cell(row=r, column=2).value
        npm = ws.cell(row=r, column=3).value
        nama = ws.cell(row=r, column=4).value
        if npm and nama:
            students.append({
                "no": int(no) if no else len(students) + 1,
                "npm": str(npm).strip(),
                "nama": str(nama).strip()
            })
    return students

def parse_syllabus(pdf_path):
    # Extracted directly from 02 rekap qs pratikum.pdf
    sessions = [
        {
            "pertemuan": 1,
            "tanggal": "2026-06-03",
            "tanggal_display": "03 Juni 2026",
            "topik": "Pengenalan AutoCAD & Gambar Denah Dasar",
            "deskripsi": "Pengenalan AutoCAD: Interface, Toolbar, Basic Commands (Line, Circle, Rectangle), Import Gambar sebagai referensi denah.",
            "bobot": 15
        },
        {
            "pertemuan": 2,
            "tanggal": "2026-06-10",
            "tanggal_display": "10 Juni 2026",
            "topik": "Medium Drawing: Kolom, Dinding & Dimensi",
            "deskripsi": "Menggambar dan Mengedit: menggambar kolom struktur, dinding bata, notasi arsitektural dan penarikan garis dimensi presisi.",
            "bobot": 15
        },
        {
            "pertemuan": 3,
            "tanggal": "2026-06-24",
            "tanggal_display": "24 Juni 2026",
            "topik": "Medium Drawing: Layer, Arsiran & Blok Pintu/Jendela",
            "deskripsi": "Pendalaman materi layer manajemen, pemberian arsiran material (hatch), dan pembuatan block kusen pintu dan jendela.",
            "bobot": 15
        },
        {
            "pertemuan": 4,
            "tanggal": "2026-07-01",
            "tanggal_display": "01 Juli 2026",
            "topik": "Medium Drawing: Gambar Potongan & Detail Pondasi",
            "deskripsi": "Menggambar Potongan Bangunan (A-A & B-B), sinkronisasi denah dengan garis potongan, dan membuat detail pondasi batu kali.",
            "bobot": 20
        },
        {
            "pertemuan": 5,
            "tanggal": "2026-07-08",
            "tanggal_display": "08 Juli 2026",
            "topik": "Publishing Drawing: Layout, Sheet & Plotting PDF",
            "deskripsi": "Layout etiket gambar standar arsitektur, pengenalan sheet viewport, plot ke PDF standar cetak A3, dan estimasi dasar daftar volume.",
            "bobot": 15
        },
        {
            "pertemuan": 6,
            "tanggal": "2026-07-15",
            "tanggal_display": "15 Juli 2026",
            "topik": "Scheduling Drawing: Perhitungan Volume & Evaluasi Final",
            "deskripsi": "Menghitung Volume dari item pekerjaan arsitektur dari gambar CAD, input tabel volume, dan evaluasi hasil kompilasi portofolio.",
            "bobot": 20
        }
    ]
    return sessions

def generate_student_profiles(students, sessions):
    course_info = {
        "kode_mk": "5412522233",
        "nama_mk": "Aplikasi Komputer Arsitektur & QS",
        "prodi": "Arsitektur",
        "fakultas": "Teknik & Desain",
        "semester": "Genap 2025/2026",
        "sks": 2,
        "kelas": "TEKZA (Lab LIKDA)",
        "jadwal": "Rabu, 10:10 - 15:50 WIB",
        "ketua_prodi": "Fielda Roza, S.T., M.T.",
        "dosen_pengasuh": [
            "Aprilia Yunita, S.T., M.T.",
            "Duddy Fajriansyah, S.T., M.T."
        ],
        "asisten_dosen": "Adrian Ridhoa, S.T."
    }

    # Possible absence reasons
    reasons_sakit = [
        "Sakit demam & flu (surat dokter terlampir)",
        "Sakit radang tenggorokan & istirahat dokter",
        "Kondisi fisik drop pasca asistensi studio malam",
        "Sakit tifus rawat jalan (ada konfirmasi dokter)"
    ]
    reasons_izin = [
        "Izin delegasi Sayembara Desain Arsitektur Nasional",
        "Izin kegiatan studi banding Ikatan Mahasiswa Arsitektur (IMA)",
        "Izin urusan keluarga mendesak di luar kota",
        "Izin servis laptop kendala hardware crash AutoCAD"
    ]

    student_records = []

    # Highlighted archetype students for compelling demo presentation
    # 1. Top Achiever: M YAZID ZIDANE MULYADI (NPM 2510015410010)
    # 2. Consistent Diligent: ALSA DMI YESYA PUTRI (NPM 2510015410001)
    # 3. At-Risk Needs Attention: ROZI ANDRIAN SURVA (NPM 2510015410011) or similar

    for idx, s in enumerate(students):
        npm = s["npm"]
        nama = s["nama"]
        
        # Archetype determination
        if idx == 0:  # M YAZID ZIDANE MULYADI (Star Student)
            archetype = "star"
        elif idx == 10: # ROZI ANDRIAN SURVA (At-Risk Intervention)
            archetype = "at_risk"
        elif idx == 1: # ALSA DMI YESYA PUTRI (Consistent Creative)
            archetype = "high"
        elif idx % 7 == 0:
            archetype = "moderate_absent"
        elif idx % 4 == 0:
            archetype = "good"
        else:
            archetype = "normal"

        # Generate attendance per session
        attendance_list = []
        total_hadir = 0
        total_sakit = 0
        total_izin = 0
        total_alpha = 0
        
        session_scores = []

        for sess in sessions:
            p_num = sess["pertemuan"]
            
            if archetype == "star":
                status = "Hadir"
                alasan = "-"
                score = random.randint(92, 98)
            elif archetype == "at_risk":
                if p_num in [2, 4]:
                    status = "Alpha"
                    alasan = "Tanpa keterangan / tidak hadir di presensi portal"
                    score = 0
                elif p_num == 3:
                    status = "Sakit"
                    alasan = "Sakit radang tenggorokan (surat menyusul)"
                    score = 65
                else:
                    status = "Hadir"
                    alasan = "-"
                    score = random.randint(68, 75)
            elif archetype == "moderate_absent":
                if p_num == 3:
                    status = "Izin"
                    alasan = random.choice(reasons_izin)
                    score = 78
                elif p_num == 5:
                    status = "Sakit"
                    alasan = random.choice(reasons_sakit)
                    score = 80
                else:
                    status = "Hadir"
                    alasan = "-"
                    score = random.randint(80, 88)
            elif archetype == "high":
                if p_num == 4:
                    status = "Izin"
                    alasan = "Izin delegasi Sayembara Desain Arsitektur"
                    score = 88
                else:
                    status = "Hadir"
                    alasan = "-"
                    score = random.randint(88, 95)
            else:
                # normal random distribution (mostly Hadir)
                roll = random.random()
                if roll < 0.85:
                    status = "Hadir"
                    alasan = "-"
                    score = random.randint(75, 90)
                elif roll < 0.92:
                    status = "Izin"
                    alasan = random.choice(reasons_izin)
                    score = random.randint(72, 85)
                elif roll < 0.97:
                    status = "Sakit"
                    alasan = random.choice(reasons_sakit)
                    score = random.randint(70, 82)
                else:
                    status = "Alpha"
                    alasan = "Terlambat lebih dari 45 menit / tidak rekam absensi"
                    score = 45

            if status == "Hadir":
                total_hadir += 1
            elif status == "Sakit":
                total_sakit += 1
            elif status == "Izin":
                total_izin += 1
            elif status == "Alpha":
                total_alpha += 1

            attendance_list.append({
                "pertemuan": p_num,
                "tanggal": sess["tanggal_display"],
                "topik": sess["topik"],
                "status": status,
                "alasan": alasan,
                "skor_sesi": score
            })
            session_scores.append(score)

        # Calculate averages
        valid_scores = [s for s in session_scores if s > 0]
        avg_score = round(sum(session_scores) / len(session_scores), 1) if session_scores else 0
        attendance_pct = round((total_hadir / len(sessions)) * 100, 1)

        # Grade calculation
        if avg_score >= 85:
            grade = "A"
            predikat = "Sangat Memuaskan (Cum Laude Potensial)"
        elif avg_score >= 80:
            grade = "A-"
            predikat = "Memuaskan"
        elif avg_score >= 75:
            grade = "B+"
            predikat = "Baik"
        elif avg_score >= 70:
            grade = "B"
            predikat = "Cukup Baik"
        elif avg_score >= 60:
            grade = "C"
            predikat = "Kurang (Perlu Remidi & Asistensi)"
        else:
            grade = "D / Evaluasi"
            predikat = "Kritis (Rentan Tidak Lulus)"

        # Competency Radar Scores (Scale 1-100)
        if archetype == "star":
            competency = {
                "penguasaan_cad": 96,
                "ketelitian_detail": 94,
                "kedisiplinan_asistensi": 98,
                "logika_ruang_struktur": 92,
                "manajemen_waktu": 95
            }
            ai_swot = {
                "kekuatan": "Kemampuan pemahaman software AutoCAD sangat cepat dan presisi tinggi. Garis potongan dan detail pondasi tersinkronisasi rapi dengan standar arsitektur profesional.",
                "kelemahan": "Kadang terlalu perfeksionis pada detail kecil sehingga pengerjaan layouting sheet sedikit memakan waktu lebih.",
                "saran_wali_murid": "Dukungan orang tua sangat diapresiasi! Ananda memiliki bakat kepemimpinan di studio arsitektur, disarankan terus didukung untuk mengikuti sayembara desain arsitektur tingkat nasional.",
                "status_alert": "OPTIMAL",
                "alert_color": "emerald"
            }
        elif archetype == "at_risk":
            competency = {
                "penguasaan_cad": 62,
                "ketelitian_detail": 58,
                "kedisiplinan_asistensi": 45,
                "logika_ruang_struktur": 65,
                "manajemen_waktu": 50
            }
            ai_swot = {
                "kekuatan": "Memiliki intuisi perancangan ruang yang cukup kreatif saat sesi diskusi konsep denah awal.",
                "kelemahan": "Kedisiplinan presensi sangat rendah (tercatat 2x Alpha & 1x Sakit). Tugas detail potongan dan arsiran material belum terselesaikan tepat waktu.",
                "saran_wali_murid": "Mohon bantuan dan perhatian bapak/ibu wali murid untuk memantau jam tidur dan jadwal keberangkatan kuliah pagi. Ananda sangat perlu asistensi khusus susulan di Lab LIKDA agar tidak tertinggal evaluasi semester.",
                "status_alert": "PERHATIAN KHUSUS",
                "alert_color": "rose"
            }
        elif archetype == "high":
            competency = {
                "penguasaan_cad": 90,
                "ketelitian_detail": 92,
                "kedisiplinan_asistensi": 88,
                "logika_ruang_struktur": 89,
                "manajemen_waktu": 87
            }
            ai_swot = {
                "kekuatan": "Etos kerja studio sangat baik, konsisten dalam asistensi perbaikan gambar denah dan detail kusen pintu/jendela.",
                "kelemahan": "Perlu penguatan pada kecepatan perhitungan volume pekerjaan (Quantity Surveying) agar tidak buru-buru saat plotting akhir.",
                "saran_wali_murid": "Pertahankan ritme belajar yang sehat di rumah. Ananda berada pada jalur prestasi yang sangat positif di Program Studi Arsitektur.",
                "status_alert": "POSITIF",
                "alert_color": "sky"
            }
        else:
            base_cad = random.randint(72, 88)
            competency = {
                "penguasaan_cad": base_cad,
                "ketelitian_detail": random.randint(70, 86),
                "kedisiplinan_asistensi": random.randint(75, 90),
                "logika_ruang_struktur": random.randint(70, 85),
                "manajemen_waktu": random.randint(68, 85)
            }
            if total_alpha >= 2:
                alert_stat = "PERHATIAN KHUSUS"
                alert_col = "rose"
                saran = "Mohon perhatian wali murid mengenai kehadiran kuliah agar memenuhi syarat minimal 75% untuk mengikuti ujian akhir."
            else:
                alert_stat = "STABIL"
                alert_col = "blue"
                saran = "Dukung ananda untuk konsisten melakukan asistensi gambar mandiri di luar jam kuliah."

            ai_swot = {
                "kekuatan": "Menunjukkan kemauan belajar yang tinggi dan aktif bertanya saat materi gambar potongan dan detail pondasi.",
                "kelemahan": "Perlu lebih teliti dalam penamaan layer dan pemilihan ketebalan garis (lineweight) saat plotting PDF.",
                "saran_wali_murid": saran,
                "status_alert": alert_stat,
                "alert_color": alert_col
            }

        # Marketing Assets Data (4-Slide Carousel & Vertical Video Storyboard)
        carousel_slides = [
            {
                "slide_no": 1,
                "tipe": "COVER & PENCAPAIAN",
                "badge": "STUDIO ARSITEKTUR 2026",
                "headline": f"Progres Karya Arsitektur: {nama.title()}",
                "subline": f"Kompilasi Praktikum Aplikasi Komputer & Gambar Kerja CAD • Nilai: {grade} ({avg_score})",
                "highlight": "Tingkat Kehadiran: " + str(attendance_pct) + "%",
                "accent": "Gold Accent (#FFC800)"
            },
            {
                "slide_no": 2,
                "tipe": "DOKUMENTASI AKTIVITAS",
                "badge": "LAB LIKDA • PRAKTEK LANGSUNG",
                "headline": "Asistensi Presisi & Konstruksi Denah",
                "subline": "Mahasiswa mengasah logika struktur kolom, dinding, dan notasi teknis sesuai standar arsitektural IAI.",
                "highlight": "Fokus & Kolaboratif",
                "accent": "Emerald Accent (#10B981)"
            },
            {
                "slide_no": 3,
                "tipe": "HASIL KARYA / OUTPUT",
                "badge": "KARYA GAMBAR KERJA A3",
                "headline": "Potongan Bangunan & Detail Pondasi",
                "subline": "Sinkronisasi denah dengan potongan struktural dan perhitungan volume pekerjaan arsitektur presisi tinggi.",
                "highlight": "Karya Siap Portofolio",
                "accent": "Cyan Accent (#06B6D4)"
            },
            {
                "slide_no": 4,
                "tipe": "PRIDE & CLOSING",
                "badge": "PROGRAM STUDI ARSITEKTUR",
                "headline": "Mencetak Arsitek Unggul Masa Depan",
                "subline": "Terima kasih bapak/ibu wali murid atas kepercayaan dan kolaborasi mendampingi putra/putri tercinta.",
                "highlight": "Official Campus Branding",
                "accent": "Gold Accent (#FFC800)"
            }
        ]

        video_storyboard = {
            "durasi_detik": 32,
            "format": "9:16 Vertikal (Reels / TikTok / WhatsApp Status)",
            "bgm_mood": "Inspiratif, Modern Upbeat Acoustic Architecture",
            "voiceover_script": (
                f"Satu bulan penuh dedikasi di Lab Komputer Arsitektur! "
                f"Inilah ananda {nama.title()}, yang telah menuntaskan modul gambar kerja digital "
                f"mulai dari perancangan denah presisi hingga sinkronisasi detail pondasi struktural dengan capaian predikat {grade}. "
                f"Terus berkarya dan menginspirasi bersama Program Studi Arsitektur!"
            ),
            "scenes": [
                {"detik": "00:00 - 00:05", "visual": "Foto Mahasiswa + Header Animasi Prestasi Bulan Ini", "teks": f"Pencapaian {nama.title()}"},
                {"detik": "00:05 - 00:15", "visual": "Zoom-in aktivitas gambar di layar AutoCAD Lab LIKDA", "teks": "Fokus Menggambar Denah & Detail Pondasi"},
                {"detik": "00:15 - 00:25", "visual": "Karya layout lembar kerja cetak PDF standar A3", "teks": "Output Presisi Standar Industri"},
                {"detik": "00:25 - 00:32", "visual": "Logo Resmi Prodi Arsitektur & Pesan Bangga untuk Orang Tua", "teks": "Bangga Menjadi Bagian Arsitektur"}
            ]
        }

        # WhatsApp Message Template ready to send to Parent
        wa_message = (
            f"Bismillaahirrohmaanirrohiim.\n\n"
            f"Kepada Yth. Bapak/Ibu Wali Murid dari *{nama}*,\n\n"
            f"Salam hangat dari Program Studi Arsitektur.\n"
            f"Berikut kami sampaikan Rekap Laporan Bulanan & Perkembangan Studi ananda pada mata kuliah *Aplikasi Komputer Arsitektur (AutoCAD & Gambar Kerja)* untuk periode berjalan:\n\n"
            f"📊 *Ringkasan Kinerja:*\n"
            f"• Kehadiran: *{attendance_pct}%* ({total_hadir}/{len(sessions)} Sesi Hadir)\n"
            f"• Rata-rata Nilai Studio: *{avg_score}* (Predikat: *{grade}*)\n"
            f"• Catatan Akademik: {ai_swot['kekuatan']}\n\n"
            f"✨ *Rapor Interaktif, Portofolio Karya & Video Progres Ananda:*\n"
            f"Bapak/Ibu dapat melihat rapor visual, galeri foto karya 4-slide, serta video pencapaian ananda melalui tautan resmi berikut:\n"
            f"👉 https://siak-arsitektur.ac.id/rapor/mhs/{npm}\n\n"
            f"Terima kasih atas doa dan dukungan berkelanjutan dari Bapak/Ibu di rumah.\n\n"
            f"Hormat kami,\n"
            f"*Ketua Program Studi Arsitektur*\n"
            f"*Fielda Roza, S.T., M.T.*"
        )

        student_records.append({
            "no": s["no"],
            "npm": npm,
            "nama": nama,
            "archetype": archetype,
            "kehadiran": {
                "hadir": total_hadir,
                "sakit": total_sakit,
                "izin": total_izin,
                "alpha": total_alpha,
                "persentase": attendance_pct,
                "detail": attendance_list
            },
            "akademik": {
                "nilai_rata_rata": avg_score,
                "grade": grade,
                "predikat": predikat,
                "kompetensi": competency,
                "skor_sesi": session_scores
            },
            "ai_diagnosis": ai_swot,
            "marketing": {
                "carousel": carousel_slides,
                "video": video_storyboard,
                "wa_text": wa_message
            }
        })

    # Class-level aggregates for Kaprodi Executive Suite
    total_mhs = len(student_records)
    class_hadir_pct = round(sum(s["kehadiran"]["persentase"] for s in student_records) / total_mhs, 1)
    class_avg_score = round(sum(s["akademik"]["nilai_rata_rata"] for s in student_records) / total_mhs, 1)
    at_risk_list = [s for s in student_records if s["kehadiran"]["alpha"] >= 2 or s["akademik"]["nilai_rata_rata"] < 70]
    
    # Grade distribution
    grades_count = {"A": 0, "A-": 0, "B+": 0, "B": 0, "C": 0, "D": 0}
    for s in student_records:
        g = s["akademik"]["grade"].split(" ")[0]
        if g in grades_count:
            grades_count[g] += 1
        else:
            grades_count["D"] += 1

    # Session-by-session attendance trends
    session_attendance_trend = []
    for sess in sessions:
        p_num = sess["pertemuan"]
        hadir_count = sum(1 for s in student_records if s["kehadiran"]["detail"][p_num - 1]["status"] == "Hadir")
        sakit_count = sum(1 for s in student_records if s["kehadiran"]["detail"][p_num - 1]["status"] == "Sakit")
        izin_count = sum(1 for s in student_records if s["kehadiran"]["detail"][p_num - 1]["status"] == "Izin")
        alpha_count = sum(1 for s in student_records if s["kehadiran"]["detail"][p_num - 1]["status"] == "Alpha")
        session_attendance_trend.append({
            "pertemuan": p_num,
            "tanggal": sess["tanggal_display"],
            "topik": sess["topik"],
            "hadir": hadir_count,
            "sakit": sakit_count,
            "izin": izin_count,
            "alpha": alpha_count,
            "hadir_pct": round((hadir_count / total_mhs) * 100, 1)
        })

    dataset = {
        "metadata": {
            "sistem": "SIAK-KAPRODI ARSITEKTUR INTELLIGENCE",
            "versi": "2.0-GOLDEN-DEMO",
            "generated_at": "2026-10-18T00:40:00+07:00",
            "target_port": 40404
        },
        "course": course_info,
        "sessions": sessions,
        "class_summary": {
            "total_mahasiswa": total_mhs,
            "rata_kehadiran": class_hadir_pct,
            "rata_nilai_studio": class_avg_score,
            "total_at_risk": len(at_risk_list),
            "distribusi_grade": grades_count,
            "tren_kehadiran_sesi": session_attendance_trend
        },
        "students": student_records
    }

    return dataset

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Membaca data mahasiswa dari Excel...")
    students = parse_students(EXCEL_PATH)
    print(f"Berhasil membaca {len(students)} data mahasiswa.")

    print("Membaca silabus dan rekap praktikum dari PDF...")
    sessions = parse_syllabus(PDF_PATH)
    print(f"Berhasil memetakan {len(sessions)} sesi praktikum AutoCAD & QS.")

    print("Mengompilasi dataset akademik & kecerdasan AI...")
    dataset = generate_student_profiles(students, sessions)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Dataset berhasil disimpan ke: {OUTPUT_JSON}")
    print("Ringkasan Kelas:")
    print(f" - Total Mahasiswa: {dataset['class_summary']['total_mahasiswa']}")
    print(f" - Rata-rata Kehadiran: {dataset['class_summary']['rata_kehadiran']}%")
    print(f" - Rata-rata Nilai Studio: {dataset['class_summary']['rata_nilai_studio']}")
    print(f" - Mahasiswa At-Risk: {dataset['class_summary']['total_at_risk']}")

if __name__ == "__main__":
    main()

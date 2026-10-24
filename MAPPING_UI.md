# 🗺️ MAPPING UI: SYS_KAMPUS_01 (PETA KABEL ANTARMUKA)

> **HUKUM SINKRONISASI DUA ARAH (KODE BERUBAH = PETA BERUBAH):**  
> Setiap kali ada elemen HTML ID, tombol, atau fungsi JavaScript yang ditambah, diubah, atau dihapus pada antarmuka web, tabel ini **WAJIB** diperbarui seketika.

---

## 🌐 1. NAVIGASI HEADER, LEFT SIDEBAR & GLOBAL CONTEXT

| ID Kabel | Elemen UI (HTML ID / Class) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-HDR-00` | `#app-campus-logo` | Render | Brand Logo | Static SVG | Special Edition Cyber-CAD Konoha Coret (Amber Gold Obsidian) dengan nukenin slash & anime aesthetic Kaprodi |
| `UI-HDR-01` | `#sel-prodi` | `change` | `onKonteksBerubah('prodi')` | `/api/kurikulum` | Mengubah prodi aktif di dropdown konteks |
| `UI-HDR-02` | `#sel-tahun` | `change` | `onKonteksBerubah('tahun')` | `/api/kurikulum` | Mengubah tahun ajar di dropdown konteks |
| `UI-HDR-03` | `#sel-semester` | `change` | `onKonteksBerubah('semester')` | `/api/kurikulum` | Mengubah semester di dropdown konteks |
| `UI-HDR-04` | `#course-selector` | `change` | `onKonteksBerubah('mk')` | `/api/switch_course?course=<KUNCI>` | Beralih mata kuliah aktif, reload dataset & rekap |
| `UI-HDR-05` | `#sel-angkatan` / `.pill-angkatan` | `change / click` | `onKonteksBerubah('angkatan')` | Local filter / `/api/data` | **Global Context Filter:** Filter data seluruh tab ke Angkatan terpilih (Semua / 2024 / 2025 / 2026 / 🚨 Senior Kritis Sem 9+) |
| `UI-HDR-06` | `#btn-mobile-filter-toggle` | `click` | `toggleMobileFilterBar()` | Local UI State | Tombol filter collapsible di header mobile untuk memunculkan/menyembunyikan panel konteks |
| `UI-NAV-01` | `.tab-btn` (Sidebar Tabs 1-14) | `click` | `switchTab(tabId)` | Local UI State | Menampilkan `#section-<tabId>` & menyembunyikan tab lain |
| `UI-NAV-02` | `#btn-mobile-menu-toggle` | `click` | `toggleMobileSidebar()` | Local UI State | Tombol hamburger mobile (lg:hidden) untuk membuka/menutup drawer navigasi |
| `UI-NAV-03` | `#sidebar-backdrop` | `click` | `closeMobileSidebar()` | Local UI State | Backdrop overlay gelap blur yang menutup drawer mobile saat disentuh |
| `UI-NAV-04` | `#btn-mobile-close-sidebar` | `click` | `closeMobileSidebar()` | Local UI State | Tombol silang di dalam header drawer mobile untuk menutup menu |
| `UI-HK-01` | `#btn-quick-at-risk` | `click` | `bukaModalAtRisk()` | Local dataset | Hotkey sidebar: membuka modal drilldown 3 mhs at-risk |
| `UI-HK-02` | `#btn-quick-audit-dosen` | `click` | `switchTab('dosen')` | Local UI State | Hotkey sidebar: lompat ke Tab 4 Audit Kinerja Dosen |
| `UI-HK-03` | `#btn-quick-observatorium` | `click` | `switchTab('analytics')` | Local UI State | Hotkey sidebar: lompat ke Tab 8 Observatorium Grafik |
| `UI-HK-04` | `#btn-quick-gradebook` | `click` | `downloadKaprodiGradebook()` | `/api/pdf/download` | Hotkey sidebar: unduh langsung PDF Gradebook Master |
| `UI-SYS-01` | `#btn-retry-load` | `click` | `retryLoad()` | `/api/data` | Memuat ulang master data jika server sempat terputus |
| `UI-AUTH-01` | `#gatekeeper-modal` | Auto on load / Keypad | `initGatekeeper()` / `verifikasiPinGatekeeper()` | `POST /api/auth/verify_pin` (Live/Mock) | Fullscreen PIN Lock Gatekeeper Modal saat akses pertama (mewajibkan PIN 6-digit) |
| `UI-AUTH-02` | `#btn-lock-session` | `click` | `kunciSesiDashboard()` | Local `sessionStorage` | Tombol gembok pada header navbar untuk mengunci kembali sesi dashboard kapan saja |
| `UI-AUTH-03` | `#btn-gatekeeper-submit` / `#btn-gatekeeper-hint` | `click / Enter` | `verifikasiPinGatekeeper()` | `POST /api/auth/verify_pin` | Tombol submit verifikasi PIN & shortcut hint pengunjung demo (PIN: `404040`) |
| `UI-AUTH-04` | `.gatekeeper-card` (`< 480px`) | Render / Resize | CSS Media Query | Local Responsive | Layout keypad elastis & auto-fit layar ultra-kecil (0 clipping di HP) |

---

## 🏛️ 2. TAB 1: MONITORING KAPRODI (`#section-kaprodi`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB1-01` | `#filter-bulan` | `change` | `onBulanBerubah()` | Local filter | Memfilter sesi berdasarkan bulan pelaksanaan |
| `UI-TAB1-02` | `#filter-session` | `change` | `filterTable()` | Local filter | Memfilter data sesi (P1-P16) pada tabel dan KPI |
| `UI-TAB1-03` | `#filter-status` | `change` | `filterTable()` | Local filter | Memfilter baris berdasarkan status kelulusan / at-risk |
| `UI-TAB1-04` | `#table-search` | `input` | `filterTable()` | Local filter | Pencarian instan teks nama dan NPM mahasiswa |
| `UI-TAB1-05` | `#btn-unduh-gradebook` | `click` | `downloadKaprodiGradebook()` | `/api/pdf/download?type=gradebook` | Mengunduh PDF 03 (Laporan Penilaian Kaprodi Landscape) |
| `UI-TAB1-06` | `#btn-unduh-audit-dosen`| `click` | `downloadDosenAuditPDF()` | `/api/pdf/download?type=evaluasi_dosen` | Mengunduh PDF 04 (Audit Efektivitas Dosen & RPS) |
| `UI-TAB1-07` | `#btn-kpi-at-risk-shortcut` | `click` | `bukaModalAtRisk()` | Local dataset | Shortcut Tab 1: buka modal 3 mahasiswa at-risk |
| `UI-TAB1-08` | Baris Mhs (`tr[data-npm]`)| `click` | `selectStudent(npm)` | Local state | Memilih mahasiswa aktif dan sinkron ke seluruh tab |
| `UI-TAB1-09` | `#chart-nilai-trend` | Render | `renderNilaiTrendChart()` | Local aggregate | Tren rata-rata nilai kelas per pertemuan (P1-P16) |
| `UI-TAB1-10` | `#chart-radar-kelas` | Render | `renderRadarKelasChart()` | Local aggregate | Radar 5 dimensi rata-rata kelas aktif |
| `UI-TAB1-11` | `#chart-grade-dist` | Render | `renderGradeDistChart(dist)` | Local aggregate | Bar Chart distribusi sebaran grade studio |
| `UI-TAB1-12` | `#mk-rawan-list` | Render | `muatMkRawan()` | `/api/periode?semua_semester=1` | Render 5 MK nilai terendah lintas kurikulum |
| `UI-TAB1-13` | `#modal-at-risk` (Close) | `click` | `tutupModalAtRisk()` | Local modal DOM | Menutup modal pop-up drilldown at-risk |

---

## 🌟 3. TAB 2: RAPOR WALI MURID & DETAIL MAHASISWA (`#section-wali`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB2-01` | `#student-dropdown` | `change` | `onStudentSelect(this)` | Local state | Memilih mahasiswa aktif (NPM) untuk seluruh tab |
| `UI-TAB2-02` | `.btn-sample-mhs` (Yazid/Rozi/Alsa) | `click` | `selectStudent(npm)` | Local state | Tombol cepat pilih sampel mahasiswa teladan / remedi |
| `UI-TAB2-03` | `#btn-radar-softskill` | `click` | `switchRadarLayer('softskill')` | Local `student.radars` | Render Radar Layer 1: Karakter & Softskill Studio |
| `UI-TAB2-04` | `#btn-radar-modul_mk` | `click` | `switchRadarLayer('modul_mk')` | Local `student.radars` | Render Radar Layer 2: Capaian Modul MK Ini (16 Sesi) |
| `UI-TAB2-05` | `#btn-radar-semester` | `click` | `switchRadarLayer('semester')` | Local `student.radars` | Render Radar Layer 3: Holistik 1 Semester Lintas MK |
| `UI-TAB2-06` | `#btn-radar-potensi_cr`| `click` | `switchRadarLayer('potensi_cr')` | Local `student.radars` | Render Radar Layer 4: Potensi Pasar & Masa Depan (Otak-CR) |
| `UI-TAB2-07` | `#radar-breakdown-grid` | Dynamic | `renderActiveRadarLayer()` | Local `student.radars` | 5 kartu dimensi dengan progress bar & nilai terukur |
| `UI-TAB2-08` | Tombol Salin Flex Card | `click` | `salinStudentFlexCard()` | Clipboard API | Salin ringkasan prestasi spotlight ke clipboard |
| `UI-TAB2-09` | Tombol Showcase | `click` | `bukaModalShowcase()` | Local modal DOM | Buka modal showcase mahakarya & DNA karir |
| `UI-TAB2-10` | `#modal-showcase` (Close) | `click` | `tutupModalShowcase()` | Local modal DOM | Menutup modal showcase |
| `UI-TAB2-11` | `#mhs-badge-container` | Dynamic | `renderStudentUniverse()` | Local Gamification | Render 4 Dopamine Badges (✨ Unlocked / 🔒 Locked) |
| `UI-TAB2-12` | `#btn-unduh-monthly` | `click` | `downloadCurrentStudentMonthlyPDF()` | `/api/pdf/download?type=monthly&npm=` | Unduh PDF 01 Rekap Kehadiran Bulanan |
| `UI-TAB2-13` | `#btn-unduh-rapor` | `click` | `downloadCurrentStudentFinalPDF()` | `/api/pdf/download?type=rapor&npm=` | Unduh PDF 02 Rapor Akhir Semester |
| `UI-TAB2-14` | Unduh PDF DeckCraft | `click` | `downloadCurrentStudentDeckcraftPDF()` | `/api/pdf/download?type=deckcraft&npm=`| Unduh PDF 05 DeckCraft Portofolio 16:9 (5 Slide Widescreen - Termasuk Quad-Radar Array) |
| `UI-TAB2-15` | Unduh Paket 3-in-1 | `click` | `downloadAll3StudentPDFs()` | 3x `/api/pdf/download` | Mengunduh seluruh dokumen mahasiswa secara batch |

---

## 📚 4. TAB 3: KURIKULUM & RPS MULTI-MK (`#section-kurikulum`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB3-01` | `#form-kurikulum` | `submit`| `simpanKurikulum()` | `POST /api/kurikulum/simpan` | Menyimpan ke tree JSON & memicu kompilasi ulang dataset |
| `UI-TAB3-02` | `#btn-simpan-kurikulum` | `click` | `simpanKurikulum()` | `POST /api/kurikulum/simpan` | Tombol submit perubahan struktur 16 pertemuan RPS |
| `UI-TAB3-03` | Dropdown Tipe Sesi | `change` | `renderTabelSesi()` | Local form state | Mengatur mode sesi (Teori, Studio, Teori+Studio, UTS, UAS) |
| `UI-TAB3-04` | Tombol Isi Topik Kosong | `click` | `isiTopikSisa()` | Local form generator | Mengisi otomatis topik RPS pertemuan yang masih kosong |
| `UI-TAB3-05` | Tombol Muat Ulang Kurikulum | `click` | `muatDetailKurikulum()` | `/api/kurikulum/detail` | Memuat ulang konfigurasi 16 sesi MK terpilih dari tree |

---

## 👨‍🏫 5. TAB 4: AUDIT PRESENSI & RPS DOSEN (`#section-dosen`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB4-01` | `#tab-btn-dosen` | `click` | `switchTab('dosen')` | Local UI state | Buka tab audit presensi dosen & modul RPS |
| `UI-TAB4-02` | `#btn-dosen-unduh-audit`| `click` | `downloadDosenAuditPDF()` | `/api/pdf/download?type=evaluasi_dosen` | Mengunduh PDF 04 (Audit Dosen & Modul RPS) |
| `UI-TAB4-03` | `#btn-dosen-refresh` | `click` | `renderDosenSection()` | Local state | Memuat ulang tampilan data audit dosen |
| `UI-TAB4-04` | `#dosen-tim-pengajar` | Render | `renderDosenSection()` | Local `dosen_audit` | Kartu profil Dosen Pengampu & Asisten Studio (Hybrid Badge: NIDN vs Dosen Kontrak / Asisten Studio) |
| `UI-TAB4-05` | `#tabel-dosen-body` | Render | `renderDosenSection()` | Local `dosen_audit` | Log 16 pertemuan tatap muka, CPMK, dan BAP |
| `UI-TAB4-06` | `#dosen-kaprodi-note` | Render | `renderDosenSection()` | Local `dosen_audit` | Catatan evaluasi mutu perkuliahan dari Kaprodi |

---

## 📊 6. TAB 5: REKAP PERIODE & TREE KURIKULUM (`#section-rekap`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB5-02` | `#rekap-scope-mk` | `click` | `aktifkanScopeRekap('mk')` | Local UI state | Beralih ke rekapitulasi satu semester untuk 1 MK |
| `UI-TAB5-03` | `#rekap-scope-semester` | `click` | `aktifkanScopeRekap('semester')` | Local UI state | Beralih ke rollup satu semester lintas seluruh MK |
| `UI-TAB5-04` | `#rekap-scope-semua` | `click` | `aktifkanScopeRekap('semua')` | Local UI state | Beralih ke rollup seluruh semester sepanjang perkuliahan |
| `UI-TAB5-06` | `#btn-muat-rekap` | `click` | `muatRekap()` | `/api/periode` | Menghitung rollup aggregasi lintas MK dari tree kurikulum |
| `UI-TAB5-07` | `#rekap-potensi-sel` | `change` | `muatPotensiMk()` | `/api/course_data?course=` | Memilih katalog MK untuk analisis potensi mahasiswa kelas riil (37 Mhs di Sem 2) |
| `UI-TAB5-08` | `#btn-jadikan-mk-aktif` | `click` | `jadikanKonteksAktifDashboard()` | `/api/switch_course?course=` | Mengalihkan konteks utama seluruh dashboard ke MK terpilih |
| `UI-TAB5-09` | Tombol Drill-Down MK | `click` | `rekapLihatMk(...)` | Local state | Membuka detail MK terpilih di tab Kurikulum |

---

## 📁 7. TAB 6: PORTOFOLIO & DECKCRAFT (`#section-portofolio`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB6-01` | `#porto-sel` | `change` | `muatPortofolio()` | `/api/portofolio?npm=` | Menghubungkan pilihan mahasiswa ke generator portofolio |
| `UI-TAB6-02` | Tombol Unduh PDF Lengkap | `click` | `unduhPortofolioPdf('portofolio_lengkap')` | `/api/pdf/download?type=portofolio_lengkap` | Mengunduh PDF 4-lapis lengkap mahasiswa |
| `UI-TAB6-03` | Tombol Unduh PDF Bulanan | `click` | `unduhPortofolioPdf('monthly')` | `/api/pdf/download?type=monthly` | Mengunduh PDF 01 bulanan MK aktif |
| `UI-TAB6-04` | Tombol Unduh PDF Rapor | `click` | `unduhPortofolioPdf('rapor')` | `/api/pdf/download?type=rapor` | Mengunduh PDF 02 rapor akhir semester |
| `UI-TAB6-05` | Tombol Unduh PDF DeckCraft| `click` | `unduhPortofolioPdf('deckcraft')` | `/api/pdf/download?type=deckcraft` | Mengunduh PDF 05 DeckCraft 16:9 |
| `UI-TAB6-06` | `#porto-bss-audit` | Dynamic | `_renderPortoBssAudit(d)` | `/api/registry/student?npm=` | Banner audit status BSS & riwayat asistensi studio senior |

---

## 🏛️ 8. TAB 7: COCKPIT YAYASAN & INVESTOR (`#section-yayasan`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB7-01` | `#tab-btn-yayasan` | `click` | `switchTab('yayasan')` | Local UI state | Membuka tab boardroom eksekutif & investor |
| `UI-TAB7-02` | `#btn-yayasan-unduh-paket` | `click` | `unduhPaketLengkapAkreditasiProdi()` | `/api/pdf/download` | Mengunduh paket 3 PDF akreditasi (Dokumen 03, 04, 06) berurutan |
| `UI-TAB7-03` | `#btn-yayasan-unduh-pdf` | `click` | `unduhExecutivePitchPdf()` | `/api/pdf/download?type=boardroom_pitch` | Mengunduh Dokumen 06: Boardroom Pitch Deck PDF 2-halaman |
| `UI-TAB7-04` | `#btn-yayasan-copy-pitch` | `click` | `salinExecutivePitchText()` | Clipboard API | Menyalin naskah pidato promosi kepemimpinan Ka Prodi |
| `UI-TAB7-05` | `#btn-yayasan-refresh` | `click` | `renderExecutiveCockpit()` | `/api/executive_cockpit` | Menghitung ulang 5 kartu truf agregasi eksekutif & SPP dinamis |
| `UI-TAB7-06` | `#yayasan-kartu-container` | Render | `renderExecutiveCockpit()` | `/api/executive_cockpit` | 5 Kartu Truf: Arus Kas Masuk SPP & Pertumbuhan PMB (+133%), Akreditasi, PMB, IKU, Skala |
| `UI-TAB7-07` | `#yayasan-pitch-box` | Render | `renderExecutiveCockpit()` | `/api/executive_cockpit` | Naskah narasi proposal transformasi satu universitas |
| `UI-TAB7-08` | `#yayasan-search-mk` | `input` | `filterYayasanMatriks()` | Local filter | Filter real-time 30 MK berdasarkan nama/kode |
| `UI-TAB7-09` | `#btn-filter-mk-semua` | `click` | `setYayasanMatriksFilter('all')` | Local UI state | Menampilkan seluruh 30 MK kurikulum prodi |
| `UI-TAB7-10` | `#btn-filter-mk-kritis` | `click` | `setYayasanMatriksFilter('kritis')` | Local UI state | Menampilkan 9 MK kategori kritis / butuh asistensi |
| `UI-TAB7-11` | `#btn-filter-mk-aman` | `click` | `setYayasanMatriksFilter('aman')` | Local UI state | Menampilkan 21 MK kategori terkendali |
| `UI-TAB7-12` | `#yayasan-matriks-table` | Render | `renderYayasanMatriksTable()` | `/api/bridge/retakes` | Tabel interaktif diagnostik 30 MK Arsitektur (30 baris) |
| `UI-TAB7-13` | `#yayasan-matriks-tbody` | Render | `renderYayasanMatriksTable()` | `/api/bridge/retakes` | Baris-baris daftar MK, SKS, remedial, dan status |
| `UI-TAB7-14` | `#modal-asistensi-mk` | Render | `bukaModalAsistensiMk()` | `/api/bridge/course_detail` | Modal pop-up drilldown rincian mahasiswa remedial per MK |
| `UI-TAB7-15` | `#btn-close-modal-asistensi` | `click` | `tutupModalAsistensiMk()` | Local UI state | Menutup modal pop-up rincian asistensi MK |
| `UI-TAB7-16` | `#reg-total-bss` | Dynamic | `renderExecutiveCockpit()` | `/api/registry/cohorts` | Metrik total mahasiswa BSS (3 Mhs, Rp 1.500.000) |
| `UI-TAB7-17` | `#reg-total-senior` | Dynamic | `renderExecutiveCockpit()` | `/api/registry/cohorts` | Metrik total mahasiswa senior semester 9-20 (15 Mahasiswa) |

---

## 📈 9. TAB 8: ANALISIS PERTUMBUHAN PMB & PENYERAPAN 30 MK KURIKULUM (`#section-pertumbuhan`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB8-01` | `#tab-btn-pertumbuhan` | `click` | `switchTab('pertumbuhan')` | Local UI state | Membuka tab analisis pertumbuhan PMB & penyerapan 30 MK |
| `UI-TAB8-02` | `#btn-export-cohort-pdf` | `click` | Direct Link | `/api/pdf/download?type=cohort_report` | Mengunduh PDF Dokumen 07 (Laporan Komprehensif Kohort & BSS Yayasan) |
| `UI-TAB8-03` | Tombol Sinkronisasi | `click` | `renderGrowthTab()` | `/api/analytics/growth` | Memuat ulang seluruh KPI, chart Apex, dan tabel serapan 30 MK |
| `UI-TAB8-04` | `#stat-growth-yoy` | Render | `renderGrowthTab()` | `/api/analytics/growth` | KPI Pertumbuhan YoY PMB (+133.3% YoY, 35 Mahasiswa Baru) |
| `UI-TAB8-05` | `#stat-growth-retensi` | Render | `renderGrowthTab()` | `/api/analytics/growth` | KPI Tingkat Retensi Mahasiswa (94.6% Anti-DO Aktif) |
| `UI-TAB8-06` | `#stat-growth-kas` | Render | `renderGrowthTab()` | `/api/analytics/growth` | KPI Penerimaan Kas PMB Baru (Rp 227.5 Jt) |
| `UI-TAB8-07` | `#stat-growth-studio` | Render | `renderGrowthTab()` | `/api/analytics/growth` | KPI Utilisasi Studio Desain (87.5% Kapasitas 35 Kursi) |
| `UI-TAB8-08` | `#chart-pmb-growth` | Render | `renderGrowthTab()` | `/api/analytics/growth` | Grafik Area/Bar tren PMB multi-tahun (2021-2026) & arus kas |
| `UI-TAB8-09` | `#sel-growth-periode` | `change` | `filterGrowthData()` | Local Filter | Filter periode tahun ajar/semester (6 semester 30 MK) |
| `UI-TAB8-10` | `#sel-growth-rumpun` | `change` | `filterGrowthData()` | Local Filter | Filter rumpun keilmuan (Studio, Struktur, Komputasi/BIM, Teori) |
| `UI-TAB8-11` | `#search-growth-mk` | `input` | `onGrowthSearchInput()` | Local Filter | Filter pencarian teks instan nama dan kode MK |
| `UI-TAB8-12` | `#growth-mk-count-badge` | Dynamic | `filterGrowthData()` | Local Filter | Badge indikator jumlah MK hasil filter (misal: 30 MK) |
| `UI-TAB8-13` | `#chart-enrolment-absorption` | Render | `renderGrowthTab()` | `/api/analytics/growth` | Grafik Bar/Line penyerapan pasar S_MK & volume peserta n |
| `UI-TAB8-14` | `#growth-enrolment-tbody` | Render | `renderGrowthEnrolmentTable()` | `/api/analytics/growth` | Tabel matriks enrolment 30 MK, SKS, peserta, rasio serapan, beban dosen |

---

## 🔭 10. TAB 9: OBSERVATORIUM MUTU & GRAFIK (`#section-analytics`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB9-01` | `#tab-btn-analytics` | `click` | `switchTab('analytics')` | Local UI state | Membuka tab observatorium analitik visual |
| `UI-TAB9-02` | `#chart-radar-analytics` | Render | `renderAnalyticsCharts()` | `/api/bridge/summary` | Radar capaian 5 kompetensi makro prodi |
| `UI-TAB9-03` | `#chart-retake-trend` | Render | `renderAnalyticsCharts()` | `/api/bridge/retakes` | Diagram tren mahasiswa retake & remedi per MK |
| `UI-TAB9-04` | `#chart-attendance-curve`| Render | `renderAnalyticsCharts()` | `/api/bridge/summary` | Kurva penurunan presensi mingguan P1-P16 |
| `UI-TAB9-05` | `#chart-analytics-cohort`| Render | `renderAnalyticsCharts()` | `/api/analytics/overview` | Komparasi multi-angkatan (Kohort 2024 vs 2025 vs 2026) |

---

## 🎬 11. TAB 10: SHOWCASE MARKETING & VIDEO (`#section-marketing`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB10-01` | Tombol Fullscreen DeckCraft| `click`| `openLiveDeckcraft()` | `/api/deckcraft_html?npm=` | Membuka presentasi 16:9 interaktif di tab baru |
| `UI-TAB10-02` | Tombol Unduh PDF DeckCraft | `click`| `downloadCurrentStudentDeckcraftPDF()` | `/api/pdf/download?type=deckcraft&npm=`| Mengunduh file PDF 05 DeckCraft 16:9 |
| `UI-TAB10-03` | Tombol Buka Folder Aset | `click` | `openStudentProgressFolder()` | `/api/open_folder?npm=` | Membuka folder gambar input di File Explorer desktop |
| `UI-TAB10-04` | `#btn-generate-video` | `click` | `generateCurrentStudentVideo()` | `/api/video/generate?npm=` | Eksekusi engine FFmpeg & kompilasi video 9:16 |
| `UI-TAB10-05` | `#btn-download-video-mp4` | `click` | `downloadStudentVideoMP4()` | Static `/videos/*.mp4` | Mengunduh video portofolio MP4 1080x1920 |
| `UI-TAB10-06` | `#btn-copy-caption` | `click` | `copyInstagramCaption()` | Clipboard API | Menyalin draft caption Instagram/TikTok |
| `UI-TAB10-07` | `#student-real-video` | Event | `renderVideoStory()` | `/videos/*.mp4` (Range 206) | Memutar video MP4 vertikal (jika `video_exists`) |

---

## 💬 12. TAB 11: WHATSAPP BROADCAST SIMULATOR (`#section-whatsapp`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB11-01` | `#btn-copy-wa-message` | `click` | `copyWhatsAppMessage()` | Clipboard API | Menyalin draft chat personal (Vanguard/Steady/Turnaround) |
| `UI-TAB11-02` | `#btn-open-wa-direct` | `click` | `openWhatsAppDirect()` | `https://web.whatsapp.com`| Membuka WhatsApp Web dengan teks terisi otomatis |
| `UI-TAB11-03` | `#wa-opening-text` | Render | `renderWhatsAppSimulation()` | Local student template | Preview bubble chat WhatsApp resmi prodi |

---

## ⚙️ 13. TAB 12: PENGATURAN IDENTITAS (`#section-pengaturan`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB12-01` | `#form-pengaturan` | `submit`| `simpanIdentitas()` | `POST /api/identitas` | Menyimpan perubahan konfigurasi nama, prodi, dosen, dan SPP |
| `UI-TAB12-02` | `#btn-simpan-identitas` | `click` | `simpanIdentitas()` | `POST /api/identitas` | Tombol submit simpan metadata identitas |
| `UI-TAB12-03` | Tombol Terapkan ke Dokumen | `click` | `terapkanKeDokumen()` | `POST /api/identitas/terapkan` | Kompilasi ulang dataset dengan konfigurasi identitas baru |
| `UI-TAB12-04` | Tombol Cetak Ulang Paket PDF | `click`| `regenerasiPaketPdf()` | `POST /api/identitas/regenerasi-pdf` | Render ulang seluruh paket arsip PDF di latar belakang |
| `UI-TAB12-05` | Tombol Muat Ulang Identitas | `click` | `muatIdentitas()` | `/api/identitas` | Membaca ulang konfigurasi JSON identitas dari server |
| `UI-TAB12-06` | `#cfg-spp` | `input` | `kumpulkanFormKeConfig()` | Local Form State | Input dinamis nominal SPP/UKT per semester (Rp) |
| `UI-TAB12-07` | `#cfg-sisa-semester` | `input` | `kumpulkanFormKeConfig()` | Local Form State | Input dinamis sisa semester studi standar (S1 = 8 semester) |

---

## 📖 14. TAB 13: PANDUAN & SOP KAPRODI (`#section-info`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB13-01` | `#tab-btn-info` | `click` | `switchTab('info')` | Local UI state | Membuka dokumen panduan operasional & SOP Kaprodi |
| `UI-TAB13-02` | `#info-sop-container` | Render | Static Markdown | N/A | SOP Penyelamatan Mahasiswa At-Risk, Audit Dosen, & Akreditasi |

---

## 🛠️ 15. TAB 14: ENGINE DIAGNOSTICS (`#section-engine`)

| ID Kabel | Elemen UI (HTML ID) | Event | Target Handler (JS) | Endpoint Backend | Output Tampilan / Efek |
|---|---|---|---|---|---|
| `UI-TAB14-01` | `#btn-engine-input` | `click` | `engineInputPindai()` | `/api/engine/input` | Memindai berkas inbox & deteksi duplikat SHA-256 |
| `UI-TAB14-02` | `#btn-engine-output` | `click` | `engineOutputAudit()` | `/api/engine/output` | Audit kelengkapan paket kirim kaprodi & wali murid |
| `UI-TAB14-03` | `#btn-engine-rapikan` | `click` | `engineOutputRapikan()` | `POST /api/engine/output` | Merapikan run lama ke backup & registri manifes |

---

## 🛡️ 16. CLIENT-SIDE SECURITY SHIELD & INTEGRITAS PERANGKAT

| ID Kabel UI | Mekanisme Proteksi Client | Saluran / Elemen | Target Backend Guard | Efek Pengamanan Terverifikasi |
|---|---|---|---|---|
| `UI-SEC-01` | **Same-Origin Fetch Enforcement** | `fetch()` API panggilan UI | `SYS-SEC-01` (`server.py::_is_origin_allowed`) | Request browser menyertakan header `Origin: http://127.0.0.1:40404`. Menggagalkan data theft dari tab browser eksternal. |
| `UI-SEC-02` | **Frame Sandboxing (Anti-Clickjacking)** | Global Header | `SYS-SEC-03` (`X-Frame-Options: SAMEORIGIN`) | Mencegah dashboard disisipkan ke dalam iframe situs jahat (Zero Clickjacking). |
| `UI-SEC-03` | **Strict Content-Type Sniffing Shield** | Global Header | `SYS-SEC-03` (`X-Content-Type-Options: nosniff`) | Browser dipaksa mematuhi MIME type murni (mencegah eksekusi script pada upload media). |
| `UI-SEC-04` | **Client-Side NPM Sanity Guard** | Input NPM di modal & filter | `SYS-SEC-05` (`server.py::NPM_RE`) | Melindungi form masukan dari karakter traversal (`../`) dan injection string. |
| `UI-SEC-05` | **GitHub Pages Mock Fetch Interceptor** | `public/gh_pages_mock.js` | `SYS-ENG-20` (`scripts/export_static_showcase.py`) | Mencegat `window.fetch('/api/*')` dan mengarahkannya ke `./static_api/*.json`, serta memblokir mutasi POST di hosting statis publik. |
| `UI-SEC-06` | **Showcase Static Banner** | `#showcase-gh-pages-banner` | Client DOM Injection | Menampilkan indikator visual status showcase 24/7 di bagian atas layar GitHub Pages. |



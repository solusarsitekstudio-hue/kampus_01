/* =============================================================================
 * MODUL: public/js/03_tab_presensi_nilai.js
 * DESKRIPSI: Tab Monitoring Presensi & Evaluasi Nilai Studio
 * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)
 * ============================================================================= */

// =============================================================================

// TAB 1: EXECUTIVE KAPRODI DASHBOARD RENDERING

// =============================================================================

function renderKaprodiDashboard() {

  if (!masterData) return;

  const summary = masterData.class_summary || {};

  _updateTab1ActiveCourseHero();

  _updateTab1ActiveCourseHero();

  _updateTab1ActiveCourseHero();

  _updateTab1ActiveCourseHero();

  // REPOSISI Tab 1 (keputusan user 2026-10-21): nilai & kompetensi jadi muka.

  renderKpiKelas(summary);

  setText("kpi-nilai", summary.rata_nilai_studio ?? "-");

  setText("kpi-kehadiran", `${summary.rata_kehadiran ?? "-"}%`);

  setText("kpi-at-risk", `${summary.total_at_risk ?? 0} Mahasiswa`);

  // Executive Cockpit Yayasan & Kaprodi: LTV Churn Risk & Retention

  const totalMhs = summary.total_mahasiswa || 35;

  const atRiskCount = summary.total_at_risk || 0;

  const safeCount = Math.max(0, totalMhs - atRiskCount);

  const retensiPct = totalMhs > 0 ? ((safeCount / totalMhs) * 100).toFixed(1) : "100.0";

  const sppPerSem = 6500000;

  const sisaSem = 6;

  const safeLtv = safeCount * sppPerSem * sisaSem;

  const riskLtv = atRiskCount * sppPerSem * sisaSem;

  const existingBadge = document.getElementById("yayasan-retensi-badge");

  if (existingBadge && !existingBadge.textContent.includes("PMB")) {

    setText("yayasan-retensi-badge", `Retensi: ${retensiPct}% (${safeCount}/${totalMhs} Aman)`);

  }

  setText("yayasan-ltv-safe", `Rp ${safeLtv.toLocaleString("id-ID")}`);

  setText("yayasan-ltv-risk", `Rp ${riskLtv.toLocaleString("id-ID")}`);

  const dosenAudit = masterData.dosen_audit || {};

  const keterlaksanaan = dosenAudit.keterlaksanaan_rata_rata ?? 88.9;

  setText("yayasan-dosen-rate", `${keterlaksanaan}% Keterlaksanaan`);

  const dosenNama = (masterData.course && masterData.course.dosen_pengasuh) || "Fielda Roza, S.T., M.T.";

  setText("yayasan-dosen-nama", dosenNama);

  // Badge periode Level 2 + ringkasan bulan Level 1

  updatePeriodeBadge();

  const ringkasB = ringkasBulanAktif();

  const bulanSel = document.getElementById("filter-bulan");

  if (bulanSel && ringkasB && bulanAktif() !== "all") {

    bulanSel.title =

      `Kehadiran ${ringkasB.label}: ${ringkasB.kehadiran}` +

      ` atas ${ringkasB.pertemuan} pertemuan` +

      (ringkasB.belum ? `, ${ringkasB.belum} entri belum diinput (netral)` : "");

  }

  // Predikat kelas dihitung dari distribusi, bukan teks hardcoded

  if (summary.distribusi_grade) {

    const modal = Object.entries(summary.distribusi_grade)

      .sort((a, b) => b[1] - a[1])[0];

    setText("kpi-predikat-desc", modal ? `${modal[0]} (${modal[1]} mahasiswa)` : "-");

  }

  // Ringkasan at-risk kelas dihitung dari data, bukan teks hardcoded

  setText("kpi-at-risk-desc",

    (masterData.metadata && masterData.metadata.aturan_at_risk)

      ? masterData.metadata.aturan_at_risk

      : "Alpha >= 2x atau kehadiran < 75%");

  const note = document.getElementById("kaprodi-note");

  if (note && masterData.class_summary) {

    const s = masterData.class_summary;

    const dist = s.distribusi_grade || {};

    const modus = s.grade_modus || (Object.entries(dist).sort((a, b) => b[1] - a[1])[0] || ["-"])[0];

    note.innerText =

      `Predikat dominan kelas ${modus}. Rata-rata nilai studio ${s.rata_nilai_studio} ` +

      `dengan rata-rata kehadiran ${s.rata_kehadiran}%. ` +

      `${s.total_at_risk} mahasiswa teridentifikasi perlu pendampingan ` +

      `(${s.at_risk_alpha ?? "-"} berdasarkan alpha, ${s.at_risk_kehadiran ?? "-"} berdasarkan kehadiran).` +

      ((s.total_belum_lengkap || 0) > 0

        ? ` PERHATIAN: ${s.total_belum_lengkap} mahasiswa masih punya ` +

          `${s.total_pertemuan_belum_diinput} pertemuan yang presensinya belum diinput ` +

          `- grade mereka ditahan sampai data lengkap.`

        : " Seluruh presensi pertemuan sudah terinput.");

  }

  // Chart analisis (bintang baru) + presensi (konteks, di details bawah)

  renderNilaiTrendChart();

  renderRadarKelasChart();

  renderGradeDistChart(summary.distribusi_grade || {});

  renderAttendanceTrendChart(summary.tren_kehadiran_sesi || []);

  renderAttendanceTable();

  muatMkRawan();

}

// =============================================================================

// TAB 1 REPOSISI: agregat kompetensi kelas dari master (tanpa angka baru dari

// luar - semua dari akademik.kompetensi & indeks_kesiapan mahasiswa).

// =============================================================================

const _DIMS_KELAS = ["penguasaan_cad", "ketelitian_detail", "kedisiplinan_asistensi",

  "logika_ruang_struktur", "manajemen_waktu"];

function kelasKompetensi() {

  const per = {};

  const kesiapan = [];

  (masterData.students || []).forEach(s => {

    const sip = Number((s.akademik || {}).indeks_kesiapan);

    if (Number.isFinite(sip)) kesiapan.push(sip);

    const comp = (s.akademik || {}).kompetensi || {};

    const sumber = (s.ai_diagnosis || {}).radar_sumber || {};

    _DIMS_KELAS.forEach(d => {

      const v = comp[d];

      if (typeof v !== "number") return;

      const isi = (per[d] = per[d] || { sum: 0, n: 0, terukur: 0 });

      isi.sum += v;

      isi.n += 1;

      if (sumber[d] === "terukur") isi.terukur += 1;

    });

  });

  const rata = {};

  _DIMS_KELAS.forEach(d => {

    rata[d] = (per[d] && per[d].n)

      ? Math.round((per[d].sum / per[d].n) * 10) / 10 : null;

  });

  const rataKesiapan = kesiapan.length

    ? Math.round((kesiapan.reduce((a, b) => a + b, 0) / kesiapan.length) * 10) / 10

    : null;

  return { rata, per, kesiapanSemua: kesiapan, rataKesiapan };

}

function renderKpiKelas(summary) {

  const k = kelasKompetensi();

  const kelas = (masterData.course && masterData.course.kelas) || "-";

  const nMhs = k.kesiapanSemua.length;

  setText("kpi-kesiapan", k.rataKesiapan != null ? k.rataKesiapan : "-");

  setText("kpi-kesiapan-desc",

    `Kelas ${kelas} • rata indeks ${nMhs} mahasiswa aktif`);

  const nilaiDim = _DIMS_KELAS.map(d => k.rata[d]).filter(v => v != null);

  const rataKomp = nilaiDim.length

    ? Math.round((nilaiDim.reduce((a, b) => a + b, 0) / nilaiDim.length) * 10) / 10

    : null;

  const dimTerukur = _DIMS_KELAS.filter(d =>

    k.per[d] && k.per[d].n && k.per[d].terukur > 0).length;

  setText("kpi-komp", rataKomp != null ? rataKomp : "-");

  setText("kpi-komp-desc",

    `Rata 5 dim • ${dimTerukur}/5 dim punya komponen terukur, sisanya estimasi`);

}

/** Chart TREN NILAI KELAS: rata skor praktikum per pertemuan lintas mahasiswa.

 *  Sumber: kehadiran.detail[].skor master (yang benar-benar terisi) - netral

 *  terhadap "Belum Diinput" & slot kosong, ikut filter bulan (Level 1). */

function renderNilaiTrendChart() {

  if (!masterData) return;

  const setP = pertemuanDalamBulan();

  const agg = {};

  (masterData.students || []).forEach(s => {

    ((s.kehadiran || {}).detail || []).forEach(d => {

      d = d || {};

      if (setP && !setP.has(String(d.pertemuan))) return;

      if (d.status === "Belum Diinput" || !d.slot_terisi) return; // netral

      if (typeof d.skor !== "number") return;

      const a = (agg[d.pertemuan] = agg[d.pertemuan] ||

        { sum: 0, n: 0, tanggal: d.tanggal_display || d.tanggal || "" });

      a.sum += d.skor;

      a.n += 1;

    });

  });

  const urut = Object.keys(agg).map(Number).sort((a, b) => a - b);

  const counter = document.getElementById("chart-nilai-count");

  if (counter) counter.textContent = urut.length ? `${urut.length} Pertemuan` : "— Pertemuan";

  if (!urut.length) {

    nilaiTrendChart = null;

    const c = document.querySelector("#chart-nilai-trend");

    if (c) c.innerHTML = `<p class="text-xs text-slate-500 italic py-8 text-center">Belum ada skor yang terisi - tren nilai menunggu input.</p>`;

    return;

  }

  const data = urut.map(p => Math.round((agg[p].sum / agg[p].n) * 10) / 10);

  const options = {

    series: [{ name: "Rata Nilai Kelas (0-100)", data }],

    chart: { type: "area", height: 260, toolbar: { show: false }, background: "transparent", zoom: { enabled: false } },

    theme: { mode: "dark" },

    colors: ["#f59e0b"],

    fill: { type: "gradient", gradient: { shadeIntensity: 0.4, opacityFrom: 0.45, opacityTo: 0.05 } },

    stroke: { width: 2.5, curve: "smooth" },

    markers: { size: 3, colors: ["#ffc800"] },

    dataLabels: { enabled: true, style: { fontSize: "9px", colors: ["#cbd5e1"] },

      formatter: (v) => (v == null ? "" : String(v)) },

    xaxis: {

      categories: urut.map(p => `P${p}`),

      labels: { style: { colors: "#94a3b8", fontSize: "11px" } },

      axisBorder: { color: "#334155" },

      tooltip: { enabled: false },

    },

    yaxis: { min: 0, max: 100, labels: { style: { colors: "#94a3b8", fontSize: "11px" } } },

    grid: { borderColor: "#1e293b" },

    tooltip: {

      y: { formatter: (v, o) => {

        const p = urut[o.dataPointIndex];

        return `P${p}${agg[p].tanggal ? " • " + agg[p].tanggal : ""}: rata ${v} (${agg[p].n} skor terisi)`;

      } },

    },

  };

  nilaiTrendChart = mountChart(nilaiTrendChart, "#chart-nilai-trend", options);

}

function getDimensiKompetensiMk(course) {

  const nama = ((course && course.nama_mk) || "").toLowerCase();

  // 1. Rumpun Struktur & Rekayasa Konstruksi

  if (nama.includes("struktur") || nama.includes("konstruksi") || nama.includes("mekanika") || nama.includes("statika") || nama.includes("beton") || nama.includes("baja")) {

    return {

      rumpun: "Struktur & Rekayasa Konstruksi",

      labels: ["Logika Statika/Struktur", "Detail Konstruksi", "Kehadiran Studio", "Pemilihan Material", "Manajemen Waktu"],

      dims: ["logika_ruang_struktur", "ketelitian_detail", "kedisiplinan_asistensi", "penguasaan_cad", "manajemen_waktu"]

    };

  }

  // 2. Rumpun Teori, Sejarah & Humaniora

  if (nama.includes("sejarah") || nama.includes("teori") || nama.includes("tipologi") || nama.includes("arsitektur kota") || nama.includes("etika") || nama.includes("metodologi") || nama.includes("permukiman") || nama.includes("pengantar")) {

    return {

      rumpun: "Teori & Sejarah Arsitektur",

      labels: ["Penguasaan Teori/Konsep", "Analisis Tipologi/Kritik", "Kehadiran & Diskusi", "Sintesis Gagasan Desain", "Manajemen Waktu"],

      dims: ["penguasaan_cad", "ketelitian_detail", "kedisiplinan_asistensi", "logika_ruang_struktur", "manajemen_waktu"]

    };

  }

  // 3. Rumpun Sains, Fisika & Rekayasa Lingkungan

  if (nama.includes("fisika") || nama.includes("matematika") || nama.includes("utilitas") || nama.includes("lingkungan") || nama.includes("klimatologi") || nama.includes("akustik")) {

    return {

      rumpun: "Sains & Fisika Bangunan",

      labels: ["Rekayasa Sains Bangunan", "Analisis Kenyamanan/Sains", "Kedisiplinan Praktikum", "Kalkulasi Problem Solving", "Manajemen Waktu"],

      dims: ["penguasaan_cad", "ketelitian_detail", "kedisiplinan_asistensi", "logika_ruang_struktur", "manajemen_waktu"]

    };

  }

  // 4. Default: Rumpun Studio & CAD/BIM

  return {

    rumpun: "Studio Perancangan & CAD",

    labels: ["Penguasaan Software/CAD", "Detail & Presisi Gambar", "Kedisiplinan Studio", "Konsep Spasial/Bentuk", "Manajemen Waktu"],

    dims: ["penguasaan_cad", "ketelitian_detail", "kedisiplinan_asistensi", "logika_ruang_struktur", "manajemen_waktu"]

  };

}

/** Chart RADAR KELAS: rata 5 dim kompetensi lintas mahasiswa MK aktif (Dinamis Rumpun MK). */

function renderRadarKelasChart() {

  if (!masterData) return;

  const k = kelasKompetensi();

  const countEl = document.getElementById("radar-kelas-count");

  if (countEl) countEl.textContent = `${k.kesiapanSemua.length} Mhs`;

  const legend = document.getElementById("radar-kelas-legend");

  const spec = getDimensiKompetensiMk(masterData.course || {});

  const nilai = spec.dims.map(d => k.rata[d]);

  const labels = spec.labels;

  if (legend) {

    const dimTerukur = spec.dims.filter(d =>

      k.per[d] && k.per[d].n && k.per[d].terukur > 0).length;

    legend.textContent = `Rumpun: ${spec.rumpun} • ${dimTerukur}/5 dim terukur dari bukti data.`;

  }

  if (!nilai.some(v => v != null)) {

    radarKelasChart = null;

    const c = document.querySelector("#chart-radar-kelas");

    if (c) c.innerHTML = `<p class="text-xs text-slate-500 italic py-6 text-center">Kompetensi belum terhitung.</p>`;

    return;

  }

  const options = {

    series: [{ name: "Rata Kompetensi Kelas", data: nilai.map(v => v ?? 0) }],

    chart: { type: "radar", height: 250, toolbar: { show: false }, background: "transparent" },

    labels,

    colors: ["#a78bfa"],

    markers: { size: 3, colors: ["#c4b5fd"] },

    fill: { opacity: 0.3, colors: ["#a78bfa"] },

    yaxis: { max: 100, show: false },

    xaxis: { labels: { style: { colors: Array(5).fill("#cbd5e1"), fontSize: "10px", fontWeight: 600 } } },

    theme: { mode: "dark" },

  };

  radarKelasChart = mountChart(radarKelasChart, "#chart-radar-kelas", options);

}

// =============================================================================

// TAB 1 REPOSISI: PETA MK RAWAN - 5 MK rata nilai terendah lintas semester

// dari /api/periode?semua_semester=1 (sumber tree, bukan master 1 MK).

// =============================================================================

async function muatMkRawan() {

  const host = document.getElementById("mk-rawan-list");

  const statusEl = document.getElementById("mk-rawan-status");

  if (!host || !masterData) return;

  const prodi = ((pohonKurikulum && pohonKurikulum.aktif && pohonKurikulum.aktif.prodi) ||

    ((pohonKurikulum && pohonKurikulum.prodi) || [])[0] || "");

  if (!prodi) {

    if (statusEl) statusEl.textContent = "Tree kurikulum belum terbaca — menunggu konteks prodi.";

    return;

  }

  if (!mkRawanState.dimuat || mkRawanState.prodi !== prodi) {

    if (statusEl) statusEl.textContent = "Menghitung dari tree kurikulum…";

    host.innerHTML = "";

    try {

      const res = await fetch(`/api/periode?prodi=${encodeURIComponent(prodi)}&semua_semester=1`,

        { cache: "no-store" });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

      // Baris dari dokumen semua TA: flatten per TA->semester.

      let baris = [];

      (data.tahun_ajar ? Object.values(data.tahun_ajar) : []).forEach(semMap => {

        Object.values(semMap || {}).forEach(dok => {

          baris = baris.concat(dok.baris || []);

        });

      });

      mkRawanState = { prodi, dimuat: true, baris };

    } catch (err) {

      if (statusEl) statusEl.textContent = `Gagal memuat: ${err.message}`;

      return;

    }

  }

  const kandidat = mkRawanState.baris

    .filter(b => b && !b.rusak && b.nilai_rata != null)

    .sort((a, b) => a.nilai_rata - b.nilai_rata)

    .slice(0, 5);

  if (statusEl) {

    statusEl.textContent = kandidat.length

      ? `${kandidat.length} MK prioritas (dari ${mkRawanState.baris.length} MK di tree)`

      : "Belum ada MK dengan nilai tercatat.";

  }

  if (!kandidat.length) {

    host.innerHTML = `<p class="text-xs text-slate-500 italic col-span-full">Belum ada katalog MK dengan nilai di tree.</p>`;

    return;

  }

  host.innerHTML = kandidat.map(b => `

    <div class="flex items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/50 px-3 py-2.5">

      <div class="min-w-0">

        <div class="text-xs font-bold text-slate-100 truncate" title="${escapeHtml(b.nama_mk)}">${escapeHtml(b.nama_mk)}</div>

        <div class="text-[10px] text-slate-400 font-mono">${escapeHtml(_tampilTahun(b.tahun_ajar))} ${escapeHtml(b.semester)}${b.kode_mk ? ` • ${escapeHtml(b.kode_mk)}` : ""}</div>

      </div>

      <div class="flex items-center gap-3 flex-shrink-0 text-[11px] font-mono">

        <span class="text-emerald-300">${b.kehadiran_rata != null ? b.kehadiran_rata + "%" : "-"}</span>

        <span class="${b.jumlah_at_risk ? "text-rose-300 font-bold" : "text-slate-500"}">${b.jumlah_at_risk ?? 0} risiko</span>

        <strong class="text-amber-300 font-black">${b.nilai_rata}</strong>

        <button data-mkrawan class="touch-target px-2 py-1 rounded-lg bg-slate-800 hover:bg-cyan-500/20 text-cyan-300 border border-slate-700 hover:border-cyan-500/40 transition"

          data-prodi="${escapeHtml(b.prodi || "")}" data-ta="${escapeHtml(b.tahun_ajar || "")}"

          data-sem="${escapeHtml(b.semester || "")}" data-kunci="${escapeHtml(b.kunci_mk || "")}">

          Detail

        </button>

      </div>

    </div>`).join("");

  host.querySelectorAll("[data-mkrawan]").forEach(btn => {

    btn.addEventListener("click", () =>

      bukaModalEvaluasiMkRawan(btn.dataset.kunci || btn.dataset.kode || ""));

  });

}

/** Buka/tutup bagian Konteks Presensi: chart kehadiran digambar ulang setelah

 *  terlihat (Apex di dalam kontainer hidden punya lebar 0 -> perlu render ulang). */

function onPresensiToggle(ev) {

  if (ev.target.open && attendanceTrendChart) {

    setTimeout(() => { try { attendanceTrendChart.render(); } catch (e) { /* noop */ } }, 120);

  }

  if (window.lucide) lucide.createIcons();

}

function renderAttendanceTrendChart(trends) {

  // FILTER BULAN (Level 1): pertemuan di luar bulan pilihan tidak digambar.

  const setP = pertemuanDalamBulan();

  let tapis = Array.isArray(trends) ? trends : [];

  if (setP) tapis = tapis.filter(t => setP.has(String(t.pertemuan)));

  setText("chart-trend-count", tapis.length ? `${tapis.length} Pertemuan` : "— Pertemuan");

  if (!tapis.length) {

    attendanceTrendChart = null;

    const c = document.querySelector("#chart-attendance-trend");

    if (c) c.innerHTML = `<p class="text-xs text-slate-500 italic py-8 text-center">Data tren kehadiran belum tersedia.</p>`;

    return;

  }

  const options = {

    series: [

      { name: "Hadir Penuh", data: tapis.map(t => t.hadir_penuh ?? t.hadir ?? 0), color: "#10b981" },

      // TAHAP E: satu pertemuan bisa punya beberapa slot absen, jadi ada murid

      // yang hanya masuk sebagian. Kalau seri ini tidak digambar, tumpukan bar

      // tidak akan berjumlah seisi kelas dan grafiknya jadi bohong.

      { name: "Hadir Sebagian", data: tapis.map(t => t.hadir_sebagian || 0), color: "#2dd4bf" },

      // BELUM DIINPUT: pertemuan yang presensinya belum masuk TIDAK dihitung

      // Alpha (lihat config/aturan.json). Kalau seri ini tidak digambar, bar

      // tumpuk tidak berjumlah seisi kelas dan grafiknya jadi bohong.

      { name: "Belum Diinput", data: tapis.map(t => t.belum_diinput || 0), color: "#64748b" },

      { name: "Izin / Sakit / Alpha", data: tapis.map(t => (t.sakit || 0) + (t.izin || 0) + (t.alpha || 0)), color: "#f43f5e" }

    ],

    chart: { type: "bar", height: 260, stacked: true, toolbar: { show: false }, background: "transparent" },

    theme: { mode: "dark" },

    plotOptions: { bar: { borderRadius: 6, columnWidth: "40%" } },

    xaxis: {

      categories: tapis.map(t => `P${t.pertemuan}`),

      labels: { style: { colors: "#94a3b8", fontSize: "11px" } },

      axisBorder: { color: "#334155" }

    },

    yaxis: {

      max: (masterData.class_summary && masterData.class_summary.total_mahasiswa) || undefined,

      labels: { style: { colors: "#94a3b8", fontSize: "11px" } }

    },

    legend: { position: "top", horizontalAlign: "right", labels: { colors: "#cbd5e1" } },

    grid: { borderColor: "#1e293b" }

  };

  attendanceTrendChart = mountChart(attendanceTrendChart, "#chart-attendance-trend", options);

}

function renderGradeDistChart(dist) {

  // BELUM DIINPUT: keranjang "Belum Lengkap" selalu ada di data (nilai 0 saat

  // semua terisi). Buang yang nol supaya legenda tidak menampilkan slice hantu.

  const entries = Object.entries(dist || {}).filter(([, v]) => v > 0);

  const labels = entries.map(([k]) => k);

  if (!labels.length) {

    gradeDistChart = null;

    const c = document.querySelector("#chart-grade-dist");

    if (c) c.innerHTML = `<p class="text-xs text-slate-500 italic py-8 text-center">Data distribusi grade belum tersedia.</p>`;

    return;

  }

  const options = {

    series: entries.map(([, v]) => v),

    chart: { type: "donut", height: 230, background: "transparent" },

    labels: labels,

    colors: ["#10b981", "#22c55e", "#06b6d4", "#3b82f6", "#f59e0b", "#ef4444", "#64748b"],

    theme: { mode: "dark" },

    legend: { position: "bottom", labels: { colors: "#cbd5e1", fontSize: "10px" } },

    stroke: { width: 2, colors: ["#0f172a"] },

    dataLabels: { enabled: true, style: { fontSize: "10px" } }

  };

  gradeDistChart = mountChart(gradeDistChart, "#chart-grade-dist", options);

}

function renderAttendanceTable() {

  const tbody = document.getElementById("attendance-table-body");

  if (!tbody || !masterData) return;

  tbody.innerHTML = "";

  const searchEl = document.getElementById("table-search");

  const sessionEl = document.getElementById("filter-session");

  const statusEl = document.getElementById("filter-status");

  const searchVal = (searchEl.value || "").trim().toLowerCase();

  const sessionVal = sessionEl.value;

  const statusVal = statusEl.value;

  const setP = pertemuanDalamBulan();

  let rowCount = 0;

  masterData.students.forEach((s) => {

    const nama = (s.nama || "").toLowerCase();

    const npm = String(s.npm || "");

    if (searchVal && !(nama.includes(searchVal) || npm.includes(searchVal))) return;

    if (!matchesActiveAngkatan(s)) return;

    (s.kehadiran.detail || []).forEach((sess) => {

      if (setP && !setP.has(String(sess.pertemuan))) return; // FILTER BULAN (Level 1)

      if (sessionVal !== "all" && String(sess.pertemuan) !== sessionVal) return;

      if (statusVal !== "all" && sess.status !== statusVal) return;

      rowCount++;

      let statusBadge;

      if (sess.status === "Hadir") {

        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Hadir</span>`;

      } else if (sess.status === "Hadir Sebagian") {

        // TAHAP E: satu pertemuan bisa punya beberapa slot absen. Mahasiswa yang

        // hanya masuk sebagian slot TIDAK dibulatkan jadi Hadir atau Alpha -

        // ditampilkan apa adanya, lengkap dengan berapa slot yang terisi.

        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30">Hadir Sebagian ${esc(sess.slot_hadir)}/${esc(sess.slot_total)}</span>`;

      } else if (sess.status === "Sakit") {

        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">Sakit</span>`;

      } else if (sess.status === "Izin") {

        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">Izin</span>`;

      } else if (sess.status === "Belum Diinput") {

        // BELUM DIINPUT: presensi pertemuan ini belum masuk - bukan Alpha.

        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-500/20 text-slate-300 border border-slate-500/40">Belum Diinput ${esc(sess.slot_terisi)}/${esc(sess.slot_total)}</span>`;

      } else {

        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">Alpha</span>`;

      }

      // FIX: badge TIDAK lagi ditebak dari alpha saja. Gunakan flag at_risk

      // dari server supaya sama persis dengan KPI & PDF.

      let alphaBadge = `<span class="font-mono text-slate-400">${s.kehadiran.alpha}x</span>`;

      if (s.at_risk) {

        alphaBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 font-mono">${s.kehadiran.alpha}x (At-Risk)</span>`;

      }

      const tr = document.createElement("tr");

      tr.className = "hover:bg-slate-800/60 transition cursor-pointer group";
      tr.setAttribute("data-npm", esc(s.npm));
      tr.title = `Buka Rapor & Analisis: ${esc(s.nama)} (${esc(s.npm)})`;
      tr.onclick = () => selectQuickStudent(s.npm);

      tr.innerHTML = `

        <td class="px-4 py-3 text-slate-400">${esc(s.no)}</td>

        <td class="px-4 py-3 font-mono text-amber-400 font-semibold">${esc(s.npm)}</td>

        <td class="px-4 py-3 text-white font-medium">${esc(s.nama)}</td>

        <td class="px-4 py-3 text-slate-300 font-mono">P${esc(sess.pertemuan)} • ${esc(sess.tanggal_display || sess.tanggal)}</td>

        <td class="px-4 py-3 text-slate-300 max-w-xs truncate" title="${esc(sess.topik)}">${esc(sess.topik)}</td>

        <td class="px-4 py-3">${statusBadge}</td>

        <td class="px-4 py-3 text-slate-400 italic">${esc(sess.alasan)}</td>

        <td class="px-4 py-3 text-center">${alphaBadge}</td>

        <td class="px-4 py-3 text-right">

          <button onclick="event.stopPropagation(); selectQuickStudent('${esc(s.npm)}')" class="px-2.5 py-1 bg-slate-800 hover:bg-amber-500 hover:text-slate-950 text-slate-300 rounded-lg text-[11px] font-medium transition flex items-center gap-1 ml-auto">

            <span>Rapor</span> <i data-lucide="chevron-right" class="w-3 h-3"></i>

          </button>

        </td>

      `;

      tbody.appendChild(tr);

    });

  });

  if (rowCount === 0) {

    tbody.innerHTML = `<tr><td colspan="9" class="py-8 text-center text-slate-500 italic">

      Tidak ada baris yang cocok dengan filter saat ini.</td></tr>`;

  }

  if (window.lucide) lucide.createIcons();

}

window.activeAngkatan = "all";

function matchesActiveAngkatan(s) {

  if (!s) return false;

  if (!window.activeAngkatan || window.activeAngkatan === "all") return true;

  const angkYear = s.angkatan ? parseInt(s.angkatan, 10) : parseInt("20" + String(s.npm || "").slice(0, 2), 10);

  if (window.activeAngkatan === "senior") {

    return angkYear <= 2021 || (s.semester_ke || 0) >= 9;

  }
  if (window.activeAngkatan === "bss") {
    return Boolean(s.is_bss || s.status === "BSS" || (s.riwayat_bss && s.riwayat_bss.length > 0));
  }

  const angkStr = String(angkYear);

  return angkStr === window.activeAngkatan;

}

function onAngkatanBerubah(val) {

  window.activeAngkatan = val || "all";

  const sel = document.getElementById("sel-angkatan");

  if (sel && sel.value !== window.activeAngkatan) sel.value = window.activeAngkatan;

  renderAttendanceTable();

  _updateFilteredOverviewKPIs();

  populateStudentDropdown();

  if (typeof renderExecutiveCockpit === "function") {

    renderExecutiveCockpit();

  }

  const label = val === "all" ? "Semua Angkatan (Sem 1-20)" : (val === "senior" ? "🚨 Zona Senior Kritis (Sem 9+)" : (val === "bss" ? "⏸️ Mahasiswa Cuti Sah (BSS)" : `Angkatan ${val}`));

  if (typeof toast === "function") {

    toast(`Global Context: Filter beralih ke ${label}`, "info", 2000);

  }

}

function _updateFilteredOverviewKPIs() {

  if (!masterData || !masterData.students) return;

  let filtered = masterData.students;

  if (window.activeAngkatan && window.activeAngkatan !== "all") {

    filtered = masterData.students.filter(s => matchesActiveAngkatan(s));

  }

  const totalMhs = filtered.length;

  const atRiskCount = filtered.filter(s => s.at_risk).length;

  setText("kpi-at-risk", `${atRiskCount} Mahasiswa`);

}

function filterTable() {

  renderAttendanceTable();

}

// =============================================================================

// TAB 2: PORTAL RAPOR WALI MURID RENDERING

// =============================================================================

function populateStudentDropdown() {

  const dropdown = document.getElementById("student-dropdown");

  if (!dropdown || !masterData) return;

  dropdown.innerHTML = "";

  const filteredStudents = (masterData.students || []).filter(s => matchesActiveAngkatan(s));

  filteredStudents.forEach(s => {

    const opt = document.createElement("option");

    opt.value = s.npm;

    opt.textContent = `${s.nama} (${s.npm}) - Grade: ${s.akademik.grade}`;

    dropdown.appendChild(opt);

  });

  const curNpm = (typeof currentStudent !== "undefined" && currentStudent) ? currentStudent.npm : null;

  if (filteredStudents.length > 0 && (!curNpm || !filteredStudents.find(s => s.npm === curNpm))) {

    selectStudent(filteredStudents[0].npm);

  }

}

function filterWaliStudent(query) {

  const dropdown = document.getElementById("student-dropdown");

  if (!dropdown || !masterData || !Array.isArray(masterData.students)) return;

  const q = (query || "").trim().toLowerCase();

  dropdown.innerHTML = "";

  const filtered = masterData.students.filter(s => {

    if (!q) return true;

    return (s.nama || "").toLowerCase().includes(q) || String(s.npm || "").toLowerCase().includes(q);

  });

  if (filtered.length === 0) {

    const opt = document.createElement("option");

    opt.value = "";

    opt.textContent = "-- Mahasiswa tidak ditemukan --";

    dropdown.appendChild(opt);

    return;

  }

  filtered.forEach(s => {

    const opt = document.createElement("option");

    opt.value = s.npm;

    opt.textContent = `${s.nama} (${s.npm}) - Grade: ${s.akademik?.grade || "-"}`;

    dropdown.appendChild(opt);

  });

  dropdown.value = filtered[0].npm;

  selectStudent(filtered[0].npm);

}

function onStudentSelect(npm) {

  selectStudent(npm);

}

function selectQuickStudent(npm) {

  selectStudent(npm);

  switchTab("wali");

}

function selectStudent(npm) {

  if (!masterData) return;

  const student = masterData.students.find(s => s.npm === npm);

  if (!student) {

    toast(`Mahasiswa NPM ${npm} tidak ada di dataset aktif.`, "error");

    return;

  }

  currentStudent = student;

  const secPorto = document.getElementById("section-portofolio");

  if (secPorto && !secPorto.classList.contains("hidden")) {

    muatPortofolio(npm);

  }

  const dropdown = document.getElementById("student-dropdown");

  if (dropdown) dropdown.value = npm;

  const ak = student.akademik;

  const kh = student.kehadiran;

  const ai = student.ai_diagnosis;

  // Profile Hero

  const initials = (student.nama || "").split(" ").filter(Boolean).map(w => w[0]).slice(0, 2).join("");

  setText("mhs-avatar", initials || "?");

  setText("mhs-nama", student.nama);

  setText("mhs-npm", student.npm);

  // Alert badge

  // FIX TAHAP B: sumber kebenaran = flag at_risk dari server (dihitung dengan

  // aturan yang sama dengan PDF). Dulu badge hanyaBirth dari warnanya, dan

  // tabel memakai "alpha>=2 saja" - tiga aturan berbeda dalam satu layar.

  const alertBadge = document.getElementById("mhs-alert-badge");

  if (alertBadge) {

    const palette = {

      rose:   "px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30",

      sky:    "px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30",

      amber:  "px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30",

      emerald:"px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"

    };

    alertBadge.innerText = ai.status_alert || "-";

    alertBadge.className = palette[ai.alert_color] || palette.emerald;

  }

  // FASE 5: badge sumber mesin (templat v3 dari sinyal nyata; akan berubah

  // "AI-Gemini" ketika jalur narasi Gemini diaktifkan di Fase 4).

  const sumberBadge = document.getElementById("mhs-sumber-badge");

  if (sumberBadge) {

    const m = ai.mesin || {};

    sumberBadge.textContent = `mesin: ${m.sumber || "templat_v3"} • ${m.tanda_sinyal || "-"}`;

  }

  // Info at-risk memakai flag yang sama (bukan ditebak ulang di frontend)

  const riskNote = document.getElementById("mhs-risk-note");

  if (riskNote) {

    const reasons = student.alasan_at_risk || [];

    riskNote.textContent = student.at_risk

      ? `At-Risk: ${reasons.join(" + ") || "sesuai aturan deteksi dini"}`

      : "Tidak terdeteksi sebagai mahasiswa berisiko";

    riskNote.className = "text-[10px] " + (student.at_risk ? "text-rose-300" : "text-emerald-400");

  }

  // Indeks Kesiapan (pengganti ranking kelas)

  const statusKompetensi = ak.status_kompetensi || "Kompeten Unggul";

  const indeksKesiapan = ak.indeks_kesiapan ?? 95;

  const rankPill = document.getElementById("mhs-ranking-pill");

  if (rankPill) {

    rankPill.innerText = `🎯 INDEKS KESIAPAN: ${indeksKesiapan}% (${statusKompetensi.toUpperCase()})`;

    rankPill.className = indeksKesiapan >= 90

      ? "px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono"

      : indeksKesiapan >= 80

        ? "px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-mono"

        : "px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono";

  }

  setText("mhs-stat-kompetensi", statusKompetensi);

  setText("mhs-stat-kesiapan", `Kesiapan: ${indeksKesiapan}%`);

  setText("mhs-stat-kehadiran", `${kh.persentase}%`);

  // TAHAP E: satuan tampilan = PERTEMUAN, persen berbasis SLOT. DUA ukuran

  // "hadir" ditampilkan terpisah supaya tidak ada angka yang bisa dibaca dua

  // cara: pertemuan PENUH (semua slot hadir) vs pertemuan yang MEMENUHI AMBANG

  // (>= min_slot_ratio_hadir). Dulu baris ini menulis "11 / 16 Pertemuan"

  // memakai ukuran longgar, di sebelah tulisan "hadir sebagian" - satu baris

  // membantah dirinya sendiri.

  const totalPertemuan = kh.total_pertemuan ?? (kh.detail || []).length;

  const penuh = kh.pertemuan_penuh ?? kh.hadir ?? 0;

  const ambang = kh.pertemuan_ambang_terpenuhi ?? penuh;

  const sebagian = kh.hadir_sebagian || 0;

  const belum = kh.belum_diinput || 0;

  setText("mhs-stat-absen-desc",

    `${penuh} / ${totalPertemuan} pertemuan penuh (semua slot)` +

    (sebagian ? ` • ${sebagian} hadir sebagian` : "") +

    (ambang !== penuh ? ` • ${ambang} memenuhi ambang ${Math.round((kh.min_slot_ratio_hadir ?? 0.5) * 100)}%` : "") +

    (belum ? ` • ${belum} belum diinput` : "") +

    (kh.slot_total ? ` • ${kh.slot_hadir}/${kh.slot_total} slot` : ""));

  setText("mhs-stat-nilai", ak.nilai_rata_rata);

  setText("mhs-stat-grade", `Grade: ${ak.grade}`);

  setText("mhs-stat-alpha", `${kh.alpha}x`);

  renderRadarCompetencyChart(student, ai.radar_sumber || null);

  // FASE 5: tren perkembangan sepanjang kuliah (lintas MK dari tree).

  muatTrenMahasiswa(student);

  // 4 Kuadran Narasi AI

  setText("ai-karakter-spasial", ai.analisis_karakter_spasial || ai.kekuatan || "-");

  setText("ai-potensi-kedepan", ai.potensi_kedepan || "-");

  setText("ai-catatan-mahasiswa", ai.catatan_khusus_mahasiswa || "-");

  setText("ai-panduan-wali", ai.panduan_wali_murid || "-");

  renderCareerMatrix(ai.matriks_karier_10 || []);

  renderStudentSessionCards(kh.detail || []);

  renderVideoStory(student);

  renderWhatsAppSimulation(student);

  renderStudentUniverse(student);

  if (window.lucide) lucide.createIcons();

}

// =============================================================================

// MODULAR COMPETENCY RADAR ENGINE (4-LAYER INTERACTIVE SWITCHER)

// =============================================================================

let currentRadarLayer = 'softskill';

const _RADAR_THEMES = {

  softskill: {

    theme: "amber",

    hex: "#f59e0b",

    marker: "#fbbf24",

    btnActive: "bg-amber-500/20 text-amber-300 border-amber-500/40 font-semibold shadow-sm",

    btnInactive: "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-transparent font-medium",

    badgeDot: "bg-amber-400",

    textClass: "text-amber-400",

    barClass: "bg-amber-500",

    engineText: "Engine: Karakter & Softskill Studio"

  },

  modul_mk: {

    theme: "emerald",

    hex: "#10b981",

    marker: "#34d399",

    btnActive: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 font-semibold shadow-sm",

    btnInactive: "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-transparent font-medium",

    badgeDot: "bg-emerald-400",

    textClass: "text-emerald-400",

    barClass: "bg-emerald-500",

    engineText: "Engine: 16 Sesi RPS + Slot Hadir"

  },

  semester: {

    theme: "cyan",

    hex: "#06b6d4",

    marker: "#22d3ee",

    btnActive: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40 font-semibold shadow-sm",

    btnInactive: "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-transparent font-medium",

    badgeDot: "bg-cyan-400",

    textClass: "text-cyan-400",

    barClass: "bg-cyan-500",

    engineText: "Engine: Tree Kurikulum Semester"

  },

  potensi_cr: {

    theme: "violet",

    hex: "#8b5cf6",

    marker: "#a78bfa",

    btnActive: "bg-purple-500/20 text-purple-300 border-purple-500/40 font-semibold shadow-sm",

    btnInactive: "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border-transparent font-medium",

    badgeDot: "bg-purple-400",

    textClass: "text-purple-400",

    barClass: "bg-purple-500",

    engineText: "Engine: Otak-CR Edge & Future Career"

  }

};

function switchRadarLayer(layerKey) {

  if (!_RADAR_THEMES[layerKey]) layerKey = 'softskill';

  currentRadarLayer = layerKey;

  // Update switcher buttons UI

  ['softskill', 'modul_mk', 'semester', 'potensi_cr'].forEach(k => {

    const btn = document.getElementById(`btn-radar-${k}`);

    if (btn) {

      if (k === currentRadarLayer) {

        btn.className = `px-2 py-1.5 text-[11px] rounded-lg transition-all text-center flex items-center justify-center gap-1 border ${_RADAR_THEMES[k].btnActive}`;

      } else {

        btn.className = `px-2 py-1.5 text-[11px] rounded-lg transition-all text-center flex items-center justify-center gap-1 border ${_RADAR_THEMES[k].btnInactive}`;

      }

    }

  });

  if (currentStudent) {

    renderActiveRadarLayer(currentStudent);

  }

}

window.switchRadarLayer = switchRadarLayer;

function renderActiveRadarLayer(student) {

  if (!student) return;

  const cfg = _RADAR_THEMES[currentRadarLayer] || _RADAR_THEMES.softskill;

  const radars = student.radars || {};

  const activeRadar = radars[currentRadarLayer];

  if (!activeRadar) {

    renderLegacyRadar(student);

    return;

  }

  // Update title, description, badge, engine

  const titleEl = document.getElementById("radar-layer-title");

  if (titleEl) {

    titleEl.innerHTML = `<span class="w-2 h-2 rounded-full ${cfg.badgeDot}"></span> ${escapeHtml(activeRadar.label)}`;

  }

  const descEl = document.getElementById("radar-layer-desc");

  if (descEl) {

    descEl.textContent = activeRadar.deskripsi || "";

  }

  const tagEl = document.getElementById("radar-engine-tag");

  if (tagEl) {

    tagEl.textContent = cfg.engineText;

  }

  const legendEl = document.getElementById("radar-legend");

  if (legendEl) {

    legendEl.textContent = "Skala 0 - 100";

  }

  // Update 5 Dimension Breakdown Grid

  const gridEl = document.getElementById("radar-breakdown-grid");

  if (gridEl) {

    const dimensi = activeRadar.dimensi || [];

    const nilai = activeRadar.nilai || [];

    gridEl.innerHTML = dimensi.map((d, i) => {

      const val = nilai[i] ?? 0;

      return `

        <div class="bg-slate-900/90 p-2.5 rounded-xl border border-slate-800/80 flex flex-col justify-between">

          <div class="flex items-center justify-between text-slate-300 text-[11px] mb-1.5">

            <span class="truncate pr-1" title="${escapeHtml(d)}">${escapeHtml(d)}</span>

            <strong class="font-bold ${cfg.textClass} font-mono text-xs">${val}</strong>

          </div>

          <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">

            <div class="${cfg.barClass} h-1.5 rounded-full transition-all duration-300" style="width: ${Math.min(100, Math.max(0, val))}%"></div>

          </div>

        </div>

      `;

    }).join("");

  }

  // Render ApexCharts Radar

  const options = {

    series: [{ name: activeRadar.label, data: activeRadar.nilai || [] }],

    chart: { type: "radar", height: 280, toolbar: { show: false }, background: "transparent" },

    labels: activeRadar.dimensi || [],

    colors: [cfg.hex],

    markers: { size: 4, colors: [cfg.marker] },

    fill: { opacity: 0.35, colors: [cfg.hex] },

    yaxis: { max: 100, min: 0, show: false },

    xaxis: { labels: { style: { colors: Array(5).fill("#cbd5e1"), fontSize: "10px", fontWeight: 600 } } },

    theme: { mode: "dark" }

  };

  radarCompetencyChart = mountChart(radarCompetencyChart, "#chart-radar-competency", options);

}

function renderLegacyRadar(student) {

  const comp = (student && student.akademik && student.akademik.kompetensi) || student || {};

  const values = [

    comp.penguasaan_cad ?? 0,

    comp.ketelitian_detail ?? 0,

    comp.kedisiplinan_asistensi ?? 0,

    comp.logika_ruang_struktur ?? 0,

    comp.manajemen_waktu ?? 0

  ];

  const options = {

    series: [{ name: "Skor Mahasiswa", data: values }],

    chart: { type: "radar", height: 280, toolbar: { show: false }, background: "transparent" },

    labels: ["Penguasaan CAD", "Detail & Presisi", "Kedisiplinan Studio", "Logika Ruang/Struktur", "Manajemen Waktu"],

    colors: ["#f59e0b"],

    markers: { size: 4, colors: ["#ffc800"] },

    fill: { opacity: 0.35, colors: ["#f59e0b"] },

    yaxis: { max: 100, min: 0, show: false },

    xaxis: { labels: { style: { colors: Array(5).fill("#cbd5e1"), fontSize: "10px", fontWeight: 600 } } },

    theme: { mode: "dark" }

  };

  radarCompetencyChart = mountChart(radarCompetencyChart, "#chart-radar-competency", options);

}

function renderRadarCompetencyChart(arg1, sumber) {

  if (arg1 && arg1.radars) {

    renderActiveRadarLayer(arg1);

    return;

  }

  if (currentStudent && currentStudent.radars) {

    renderActiveRadarLayer(currentStudent);

    return;

  }

  renderLegacyRadar(arg1);

}

/** FASE 5: kartu tren sepanjang kuliah di tab wali - rollup per semester +

 * arah tren dari /api/perkembangan (sama dengan chip tab 8, versi lebar). */

async function muatTrenMahasiswa(student) {

  const isi = document.getElementById("tren-isi");

  const hitung = document.getElementById("tren-mk-count");

  if (!isi) return;

  const perk = await dataPerkembangan();

  const p = perk ? (perk.mahasiswa || {})[String(student.npm)] : null;

  if (!hitung) return;

  if (!p || !p.jumlah_mk) {

    hitung.textContent = "-";

    isi.innerHTML = `<p class="text-slate-500 italic">Riwayat lintas MK belum tersedia untuk NPM ini.</p>`;

    return;

  }

  hitung.textContent = `${p.jumlah_mk} MK`;

  const ikon = p.arah_nilai === "naik" ? "↑ naik"

    : p.arah_nilai === "turun" ? "↓ turun" : "→ stabil";

  const kelas = p.arah_nilai === "naik"

    ? "text-emerald-300 border-emerald-500/30"

    : p.arah_nilai === "turun" ? "text-rose-300 border-rose-500/30"

    : "text-slate-300 border-slate-600/60";

  const barisSemester = (p.semester || []).map(sem => {

    const nilai = sem.rata_nilai != null ? `${sem.rata_nilai}` : "-";

    const keh = sem.rata_kehadiran != null ? `${sem.rata_kehadiran}%` : "-";

    return `<div class="flex items-center justify-between gap-2 bg-slate-900 rounded-lg px-3 py-2 border border-slate-800">

      <span class="font-semibold text-slate-200">${escapeHtml(_tampilTahun(sem.tahun_ajar))} ${escapeHtml(sem.semester)}</span>

      <span class="text-slate-400">${sem.jumlah_mk} MK • rata nilai <span class="text-amber-300 font-bold">${escapeHtml(nilai)}</span> • hadir <span class="text-cyan-300 font-bold">${escapeHtml(keh)}</span></span>

    </div>`;

  }).join("");

  isi.innerHTML =

    `<div class="flex items-center gap-2 mb-2">

      <span class="px-2 py-0.5 rounded border text-[10px] font-bold ${kelas}">${ikon}${p.delta_nilai_terakhir != null ? ` (${p.delta_nilai_terakhir > 0 ? "+" : ""}${p.delta_nilai_terakhir})` : ""}</span>

      <span class="text-[10px] text-slate-500">arah terakhir = rata-rata nilai semester terakhir vs sebelumnya (ambang ±5)</span>

    </div>` +

    (barisSemester ||

      `<p class="text-slate-500 italic">Belum ada rollup semester.</p>`);

}

function renderStudentSessionCards(detailList) {

  const container = document.getElementById("student-session-cards");

  if (!container) return;

  container.innerHTML = "";

  if (!detailList.length) {

    container.innerHTML = `<p class="text-xs text-slate-500 italic py-4 text-center">Rincian sesi belum tersedia.</p>`;

    return;

  }

  detailList.forEach(item => {

    const card = document.createElement("div");

    card.className = "p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-3 text-xs";

    let statPill;

    if (item.status === "Hadir") {

      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">Hadir</span>`;

    } else if (item.status === "Hadir Sebagian") {

      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-500/20 text-teal-300">Hadir Sebagian ${esc(item.slot_hadir)}/${esc(item.slot_total)}</span>`;

    } else if (item.status === "Sakit") {

      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400">Sakit</span>`;

    } else if (item.status === "Izin") {

      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400">Izin</span>`;

    } else if (item.status === "Belum Diinput") {

      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-500/20 text-slate-300">Belum Diinput ${esc(item.slot_terisi)}/${esc(item.slot_total)}</span>`;

    } else {

      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400">Alpha</span>`;

    }

    const skor = item.skor !== undefined && item.skor !== null ? item.skor : "-";

    card.innerHTML = `

      <div class="flex items-center gap-3">

        <div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center font-mono font-bold text-amber-400 text-xs">

          P${esc(item.pertemuan)}

        </div>

        <div>

          <div class="font-bold text-white">${esc(item.topik)}</div>

          <div class="text-[11px] text-slate-400 font-mono">${esc(item.tanggal_display || item.tanggal)} • ${esc(item.alasan)}</div>

        </div>

      </div>

      <div class="flex items-center gap-3 flex-shrink-0">

        ${statPill}

        <div class="text-right">

          <div class="text-xs font-mono font-bold text-amber-400">${esc(skor)}</div>

          <div class="text-[10px] text-slate-500">Nilai Praktikum</div>

        </div>

      </div>

    `;

    container.appendChild(card);

  });

}

function renderCareerMatrix(careers) {

  const tbody = document.getElementById("career-matrix-rows");

  if (!tbody) return;

  tbody.innerHTML = "";

  if (!careers || careers.length === 0) {

    tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500 italic">Data matriks karier belum dikompilasi.</td></tr>`;

    return;

  }

  careers.forEach((item, idx) => {

    const tr = document.createElement("tr");

    tr.className = "hover:bg-slate-850/60 transition border-b border-slate-850/80";

    const score = Number(item.kecocokan_persen ?? 0);

    // FIX: badge SEBELUMNYA ikut memakai item.kategori_kecocokan yang di-hardcode

    // di sisi server ("Sangat Tinggi" padahal skornya 67%). Sekarang badge,

    // warna bar, dan lebar bar semuanya diturunkan dari SATU angka: score.

    let badgeClass, scoreColor, barGradient, kategori;

    if (score >= 95) {

      kategori = "Sangat Tinggi";

      badgeClass = "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";

      scoreColor = "text-emerald-400";

      barGradient = "from-emerald-500 to-teal-400";

    } else if (score >= 85) {

      kategori = "Tinggi";

      badgeClass = "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40";

      scoreColor = "text-cyan-400";

      barGradient = "from-cyan-500 to-blue-400";

    } else if (score >= 70) {

      kategori = "Sedang";

      badgeClass = "bg-amber-500/20 text-amber-300 border border-amber-500/40";

      scoreColor = "text-amber-400";

      barGradient = "from-amber-500 to-orange-400";

    } else {

      kategori = "Rendah";

      badgeClass = "bg-rose-500/20 text-rose-300 border border-rose-500/40";

      scoreColor = "text-rose-400";

      barGradient = "from-rose-500 to-red-400";

    }

    const skills = item.keterampilan_kunci

      ? String(item.keterampilan_kunci).split(",").map(sk => sk.trim()).filter(Boolean)

      : [];

    const skillsHtml = skills

      .map(sk => `<span class="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700/80 text-[10px] text-slate-300 font-mono">${esc(sk)}</span>`)

      .join("");

    tr.innerHTML = `

      <td class="py-3 px-3 text-center font-mono font-bold text-slate-400">${esc(item.id || idx + 1)}</td>

      <td class="py-3 px-4">

        <div class="font-bold text-white text-xs">${esc(item.profesi)}</div>

        <div class="text-[11px] text-slate-400 font-mono mt-0.5">${esc(item.bidang_industri)}</div>

      </td>

      <td class="py-3 px-4 w-44">

        <div class="flex justify-between items-center mb-1 gap-2">

          <span class="text-xs font-mono font-bold ${scoreColor}">${score}%</span>

          <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold ${badgeClass}">${kategori}</span>

        </div>

        <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">

          <div class="h-1.5 rounded-full bg-gradient-to-r ${barGradient}" style="width: ${Math.max(0, Math.min(100, score))}%"></div>

        </div>

      </td>

      <td class="py-3 px-4">

        <div class="flex flex-wrap gap-1 max-w-xs">${skillsHtml}</div>

      </td>

      <td class="py-3 px-4 text-xs leading-relaxed">

        <p class="text-slate-200 mb-1.5 text-justify">${esc(item.analisis_potensi)}</p>

        <div class="p-1.5 rounded bg-slate-900/90 border border-amber-500/30 text-amber-300 text-[11px] flex items-start gap-1.5">

          <i data-lucide="sparkles" class="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5"></i>

          <span><strong>Langkah Pengembangan:</strong> ${esc(item.saran_pengembangan)}</span>

        </div>

      </td>

    `;

    tbody.appendChild(tr);

  });

}

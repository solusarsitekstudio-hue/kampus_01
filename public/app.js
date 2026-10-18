// ============================================================================
// App Controller for SIAK-KAPRODI (Arsitektur Intelligence)
//
// FIX TAHAP A (UI):
//   * Carousel 4-slide DIHAPUS. Data marketing.carousel tidak pernah ada di
//     academic_data.json, jadi tombol prev/next/thumb mati total (klik tidak
//     terjadi apa-apa). Sekarang panel DeckCraft hanya menampilkan tombol yang
//     benar-benar bekerja: Fullscreen Interaktif + Unduh PDF 16:9.
//   * Chart DIREDUCK / DESTROY lebih dulu -> tidak ada object ApexCharts numpuk
//   * Semua data dari JSON di-escape sebelum masuk innerHTML (XSS / HTML rusak)
//   * Ditambah: loading skeleton + banner error + toast (ganti alert())
//   * Header, dropdown MK, dan filter sesi disinkronkan ke course AKTIF
//   * Video tidak di-load ulang tiap pilih mahasiswa
// ============================================================================

let masterData = null;
let currentStudent = null;
let videoLoadedNpm = null;   // NPM yang videonya sudah dimuat (hindari reload)
let videoGenerating = false;

// Chart instances
let attendanceTrendChart = null;
let gradeDistChart = null;
let radarCompetencyChart = null;

// =============================================================================
// UTILITAS
// =============================================================================

/** Escape HTML - dipakai untuk SEMUA data dari JSON sebelum masuk innerHTML. */
function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.innerText = value;
}

/** Buat chart, hancurkan yang lama supaya tidak menumpuk di memory. */
function mountChart(current, containerSelector, options) {
  const container = document.querySelector(containerSelector);
  if (!container) return null;
  if (current && typeof current.destroy === "function") {
    try { current.destroy(); } catch (e) { /* abaikan */ }
  }
  container.innerHTML = "";
  const chart = new ApexCharts(container, options);
  chart.render();
  return chart;
}

// ---------------------------------------------------------------- TOAST
const TOAST_STYLES = {
  success: { bg: "bg-emerald-600", icon: "check-circle-2" },
  error:   { bg: "bg-rose-600",    icon: "alert-triangle" },
  info:    { bg: "bg-sky-600",     icon: "info" },
  warn:    { bg: "bg-amber-600",   icon: "alert-circle" }
};

function toast(message, type = "info", ms = 4000) {
  const host = document.getElementById("toast-host");
  if (!host) { console.log(`[${type}] ${message}`); return; }
  const style = TOAST_STYLES[type] || TOAST_STYLES.info;
  const el = document.createElement("div");
  el.className = `${style.bg} text-white text-xs font-semibold rounded-xl px-4 py-3 shadow-2xl border border-white/20 flex items-start gap-2.5 max-w-sm pointer-events-auto animate-toast-in`;
  el.innerHTML = `<i data-lucide="${style.icon}" class="w-4 h-4 flex-shrink-0 mt-px"></i><span>${esc(message)}</span>`;
  host.appendChild(el);
  if (window.lucide) lucide.createIcons();
  setTimeout(() => {
    el.classList.add("animate-toast-out");
    setTimeout(() => el.remove(), 300);
  }, ms);
}

// ------------------------------------------------------- LOADING / ERROR UI
function setAppState(state, message) {
  const loading = document.getElementById("app-loading");
  const errorBox = document.getElementById("app-error");
  const main = document.getElementById("app-main");
  const footer = document.getElementById("app-footer");
  const tabs = document.getElementById("nav-tabs");

  if (loading) loading.classList.toggle("hidden", state !== "loading");
  if (errorBox) errorBox.classList.toggle("hidden", state !== "error");

  // Sembunyikan konten utama saat masih loading / gagal, supaya user tidak
  // salah mengira angka placeholder (mis. "35", "82.4%") sebagai data asli.
  const isLoading = state === "loading";
  const isError = state === "error";
  if (main) main.classList.toggle("hidden", isLoading || isError);
  if (footer) footer.classList.toggle("hidden", isLoading || isError);
  if (tabs) tabs.classList.toggle("opacity-40", isLoading || isError);

  const msgEl = document.getElementById("app-error-message");
  if (msgEl && message) msgEl.innerText = message;
}

// On Page Load
document.addEventListener("DOMContentLoaded", async () => {
  setAppState("loading");
  await loadAcademicData();
  // Teks header (judul / sub judul / deskripsi) diambil dari config/identitas.json
  // supaya mengganti nama prodi tidak perlu lagi mengedit index.html.
  await muatIdentitas({ diam: true });
  if (window.lucide) lucide.createIcons();
});

async function retryLoad() {
  setAppState("loading");
  await loadAcademicData();
  if (window.lucide) lucide.createIcons();
}

// Fetch Data from Server API
async function loadAcademicData() {
  try {
    const res = await fetch("/api/data", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status} - ${res.statusText}`);
    masterData = await res.json();

    if (!masterData || !Array.isArray(masterData.students)) {
      throw new Error("Format data tidak dikenali (field 'students' tidak ada).");
    }

    setAppState("ready");
    syncActiveCourseToUi(masterData.course);
    renderKaprodiDashboard();
    populateStudentDropdown();
    populateSessionFilter();

    // Jumlah mahasiswa pada label tombol dihitung dari data, bukan diketik "35".
    setText("hero-jml-mhs", masterData.students.length);

    const preferred = currentStudent
      ? masterData.students.find(s => s.npm === currentStudent.npm)
      : null;
    if (preferred) {
      selectStudent(preferred.npm);
    } else if (masterData.students.length > 0) {
      selectStudent(masterData.students[0].npm);
    } else {
      toast("Dataset aktif tidak memuat satu pun mahasiswa.", "warn");
    }

    fetch("/api/runs")
      .then(r => r.json())
      .then(runsData => {
        if (runsData && runsData.latest && runsData.latest.latest_timestamp) {
          setText("output-folder-display",
            `output/${runsData.latest.latest_course}/${runsData.latest.latest_timestamp}/`);
          setText("output-timestamp-text", `Sesi Terakhir: ${runsData.latest.latest_timestamp}`);
        }
      })
      .catch(() => { /* info output bukan kritis */ });

  } catch (err) {
    console.error("Failed to load academic data:", err);
    setAppState("error",
      "Gagal memuat data akademik dari server. Pastikan run_server.bat masih berjalan. " +
      `(${err.message})`);
  }
}

/** Sinkronkan header + dropdown MK ke mata kuliah yang SEDANG AKTIF di server. */
function syncActiveCourseToUi(course) {
  if (!course || !course.nama_mk) return;
  setText("current-course-title", course.nama_mk);

  const selector = document.getElementById("course-selector");
  if (selector) {
    let matched = false;
    Array.from(selector.options).forEach(opt => {
      if (opt.value === course.nama_mk || opt.textContent.trim() === course.nama_mk) {
        selector.value = opt.value;
        matched = true;
      }
    });
    if (!matched) {
      // Mata kuliah aktif tidak ada di daftar dropdown -> tambahkan supaya tidak menyesatkan
      const opt = document.createElement("option");
      opt.value = course.nama_mk;
      opt.textContent = course.nama_mk;
      opt.selected = true;
      selector.appendChild(opt);
    }
  }

  setText("kpi-kelas-desc", course.kelas || "");
  setText("kpi-jadwal-desc", course.jadwal || "");
}

/** Filter sesi dibangun dari data, bukan dari topik AutoCAD yang diketik manual. */
function populateSessionFilter() {
  const sel = document.getElementById("filter-session");
  if (!sel || !masterData) return;
  const current = sel.value;
  sel.innerHTML = `<option value="all">Semua Sesi (${masterData.sessions.length})</option>`;
  masterData.sessions.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.pertemuan;
    const topic = (s.topik || "").length > 34 ? s.topik.slice(0, 34) + "..." : (s.topik || "");
    opt.textContent = `Sesi ${s.pertemuan}: ${topic}`;
    sel.appendChild(opt);
  });
  sel.value = current || "all";
}

// Switch Active Navigation Tabs
function switchTab(tabName) {
  document.querySelectorAll(".tab-section").forEach(sec => sec.classList.add("hidden"));
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.remove("active-tab");
    btn.classList.add("text-slate-400");
  });

  const activeSection = document.getElementById(`section-${tabName}`);
  const activeBtn = document.getElementById(`tab-btn-${tabName}`);

  if (activeSection) activeSection.classList.remove("hidden");
  if (activeBtn) {
    activeBtn.classList.add("active-tab");
    activeBtn.classList.remove("text-slate-400");
  }

  // Radar digambar saat section masih hidden -> lebarnya 0. Redraw setelah tampil.
  if (tabName === "wali" && radarCompetencyChart) {
    setTimeout(() => { try { radarCompetencyChart.render(); } catch (e) { /* noop */ } }, 120);
  }
  // Tab Pengaturan: muat identitas terbaru dari server tiap kali dibuka, supaya
  // yang tampil selalu keadaan sebenarnya (termasuk kalau config diubah manual).
  if (tabName === "pengaturan") muatIdentitas();
  if (window.lucide) lucide.createIcons();
}

// =============================================================================
// TAB 1: EXECUTIVE KAPRODI DASHBOARD RENDERING
// =============================================================================
function renderKaprodiDashboard() {
  if (!masterData) return;

  const summary = masterData.class_summary || {};
  setText("kpi-total-mhs", summary.total_mahasiswa ?? "-");
  setText("kpi-kehadiran", `${summary.rata_kehadiran ?? "-"}%`);
  setText("kpi-nilai", summary.rata_nilai_studio ?? "-");
  setText("kpi-at-risk", `${summary.total_at_risk ?? 0} Mahasiswa`);

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
      `(${s.at_risk_alpha ?? "-"} berdasarkan alpha, ${s.at_risk_kehadiran ?? "-"} berdasarkan kehadiran).`;
  }

  renderAttendanceTrendChart(summary.tren_kehadiran_sesi || []);
  renderGradeDistChart(summary.distribusi_grade || {});
  renderAttendanceTable();
}

function renderAttendanceTrendChart(trends) {
  if (!trends.length) {
    attendanceTrendChart = null;
    const c = document.querySelector("#chart-attendance-trend");
    if (c) c.innerHTML = `<p class="text-xs text-slate-500 italic py-8 text-center">Data tren kehadiran belum tersedia.</p>`;
    return;
  }

  const options = {
    series: [
      { name: "Hadir di Lab", data: trends.map(t => t.hadir), color: "#10b981" },
      { name: "Izin / Sakit / Alpha", data: trends.map(t => (t.sakit || 0) + (t.izin || 0) + (t.alpha || 0)), color: "#f43f5e" }
    ],
    chart: { type: "bar", height: 260, stacked: true, toolbar: { show: false }, background: "transparent" },
    theme: { mode: "dark" },
    plotOptions: { bar: { borderRadius: 6, columnWidth: "40%" } },
    xaxis: {
      categories: trends.map(t => `Sesi ${t.pertemuan}`),
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
  const labels = Object.keys(dist);
  if (!labels.length) {
    gradeDistChart = null;
    const c = document.querySelector("#chart-grade-dist");
    if (c) c.innerHTML = `<p class="text-xs text-slate-500 italic py-8 text-center">Data distribusi grade belum tersedia.</p>`;
    return;
  }
  const options = {
    series: Object.values(dist),
    chart: { type: "donut", height: 230, background: "transparent" },
    labels: labels,
    colors: ["#10b981", "#22c55e", "#06b6d4", "#3b82f6", "#f59e0b", "#ef4444"],
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

  let rowCount = 0;

  masterData.students.forEach((s) => {
    const nama = (s.nama || "").toLowerCase();
    const npm = String(s.npm || "");
    if (searchVal && !(nama.includes(searchVal) || npm.includes(searchVal))) return;

    (s.kehadiran.detail || []).forEach((sess) => {
      if (sessionVal !== "all" && String(sess.pertemuan) !== sessionVal) return;
      if (statusVal !== "all" && sess.status !== statusVal) return;
      rowCount++;

      let statusBadge;
      if (sess.status === "Hadir") {
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Hadir</span>`;
      } else if (sess.status === "Sakit") {
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">Sakit</span>`;
      } else if (sess.status === "Izin") {
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">Izin</span>`;
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
      tr.className = "hover:bg-slate-800/40 transition";
      tr.innerHTML = `
        <td class="px-4 py-3 text-slate-400">${esc(s.no)}</td>
        <td class="px-4 py-3 font-mono text-amber-400 font-semibold">${esc(s.npm)}</td>
        <td class="px-4 py-3 text-white font-medium">${esc(s.nama)}</td>
        <td class="px-4 py-3 text-slate-300 font-mono">Sesi ${esc(sess.pertemuan)} • ${esc(sess.tanggal_display || sess.tanggal)}</td>
        <td class="px-4 py-3 text-slate-300 max-w-xs truncate" title="${esc(sess.topik)}">${esc(sess.topik)}</td>
        <td class="px-4 py-3">${statusBadge}</td>
        <td class="px-4 py-3 text-slate-400 italic">${esc(sess.alasan)}</td>
        <td class="px-4 py-3 text-center">${alphaBadge}</td>
        <td class="px-4 py-3 text-right">
          <button onclick="selectQuickStudent('${esc(s.npm)}')" class="px-2.5 py-1 bg-slate-800 hover:bg-amber-500 hover:text-slate-950 text-slate-300 rounded-lg text-[11px] font-medium transition flex items-center gap-1 ml-auto">
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
  masterData.students.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.npm;
    opt.textContent = `${s.nama} (${s.npm}) - Grade: ${s.akademik.grade}`;
    dropdown.appendChild(opt);
  });
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
  const totalSesi = (kh.detail || []).length;
  setText("mhs-stat-absen-desc", `${kh.hadir} / ${totalSesi} Sesi Hadir`);
  setText("mhs-stat-nilai", ak.nilai_rata_rata);
  setText("mhs-stat-grade", `Grade: ${ak.grade}`);
  setText("mhs-stat-alpha", `${kh.alpha}x`);

  renderRadarCompetencyChart(ak.kompetensi || {});

  // 4 Kuadran Narasi AI
  setText("ai-karakter-spasial", ai.analisis_karakter_spasial || ai.kekuatan || "-");
  setText("ai-potensi-kedepan", ai.potensi_kedepan || "-");
  setText("ai-catatan-mahasiswa", ai.catatan_khusus_mahasiswa || "-");
  setText("ai-panduan-wali", ai.panduan_wali_murid || "-");

  renderCareerMatrix(ai.matriks_karier_10 || []);
  renderStudentSessionCards(kh.detail || []);

  renderVideoStory(student);
  renderWhatsAppSimulation(student);

  if (window.lucide) lucide.createIcons();
}

function renderRadarCompetencyChart(comp) {
  setText("radar-val-cad", comp.penguasaan_cad ?? "-");
  setText("radar-val-detail", comp.ketelitian_detail ?? "-");
  setText("radar-val-disiplin", comp.kedisiplinan_asistensi ?? "-");
  setText("radar-val-ruang", comp.logika_ruang_struktur ?? "-");
  // FIX: sumbu ke-5 (Manajemen Waktu) sebelumnya tidak pernah punya nilai di UI
  setText("radar-val-waktu", comp.manajemen_waktu ?? "-");

  const values = [
    comp.penguasaan_cad ?? 0,
    comp.ketelitian_detail ?? 0,
    comp.kedisiplinan_asistensi ?? 0,
    comp.logika_ruang_struktur ?? 0,
    comp.manajemen_waktu ?? 0
  ];

  const options = {
    series: [{ name: "Skor Mahasiswa", data: values }],
    chart: { type: "radar", height: 290, toolbar: { show: false }, background: "transparent" },
    labels: ["Penguasaan CAD", "Detail & Presisi", "Kedisiplinan Studio", "Logika Ruang/Struktur", "Manajemen Waktu"],
    colors: ["#f59e0b"],
    markers: { size: 4, colors: ["#ffc800"] },
    fill: { opacity: 0.35, colors: ["#f59e0b"] },
    yaxis: { max: 100, show: false },
    xaxis: { labels: { style: { colors: Array(5).fill("#cbd5e1"), fontSize: "11px", fontWeight: 600 } } },
    theme: { mode: "dark" }
  };

  radarCompetencyChart = mountChart(radarCompetencyChart, "#chart-radar-competency", options);
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
    } else if (item.status === "Sakit") {
      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400">Sakit</span>`;
    } else if (item.status === "Izin") {
      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400">Izin</span>`;
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

// =============================================================================
// TAB 3: VIDEO 9:16
// =============================================================================
async function renderVideoStory(student) {
  const vid = (student.marketing && student.marketing.video) || {};
  setText("video-full-script", `"${vid.voiceover_script || "Naskah voiceover belum tersedia."}"`);

  await detectStudentProgressPhotos(student.npm);

  // FIX: dulu videoEl.load() dipanggil tiap pilih mahasiswa -> video ter-buffer
  // ulang dari 0 dan muter-muter. Sekarang hanya kalau NPM-nya memang beda.
  if (videoLoadedNpm === student.npm) return;

  const videoEl = document.getElementById("student-real-video");
  const videoSrc = document.getElementById("student-video-src");
  if (videoEl && videoSrc) {
    const videoUrl = `/videos/video_portofolio_${student.npm}.mp4?t=${Date.now()}`;
    videoSrc.src = videoUrl;
    videoEl.load();
    videoLoadedNpm = student.npm;

    videoEl.addEventListener("error", () => {
      toast(`Video untuk ${student.nama} belum ada. Tekan "Render Video MP4" dulu.`, "warn");
    }, { once: true });
  }
}

async function detectStudentProgressPhotos(npm) {
  const countEl = document.getElementById("detected-photo-count");
  const folderEl = document.getElementById("detected-photo-folder");
  const chipsEl = document.getElementById("detected-photo-chips");
  if (countEl) countEl.innerText = "Memuat...";

  try {
    const res = await fetch(`/api/student/images?npm=${encodeURIComponent(npm)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    if (countEl) countEl.innerText = `${data.count} Foto Terdeteksi`;
    if (folderEl) folderEl.innerText = data.folder || `input/progress_mahasiswa/.../${npm}`;

    if (chipsEl) {
      chipsEl.innerHTML = "";
      if (data.filenames && data.filenames.length > 0) {
        data.filenames.forEach(fn => {
          const chip = document.createElement("span");
          chip.className = "px-2 py-0.5 rounded bg-slate-800 text-[10px] text-amber-300 font-mono border border-slate-700/80 truncate max-w-[140px]";
          chip.innerText = fn;
          chip.title = fn;
          chipsEl.appendChild(chip);
        });
      } else {
        chipsEl.innerHTML = `<span class="text-[10px] text-slate-500 italic">Folder kosong. Taruh foto (.jpg/.png) di folder di atas, lalu Render Video.</span>`;
      }
    }
  } catch (err) {
    console.error("Error detecting photos:", err);
    if (countEl) countEl.innerText = "Gagal deteksi";
    if (chipsEl) chipsEl.innerHTML = `<span class="text-[10px] text-rose-400 italic">${esc(err.message)}</span>`;
  }
}

async function openStudentProgressFolder() {
  if (!currentStudent) return;
  try {
    const res = await fetch(`/api/open_folder?npm=${encodeURIComponent(currentStudent.npm)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    if (data.success) {
      toast(`Folder dibuka: ${data.folder}`, "success");
    }
  } catch (err) {
    toast(`Gagal membuka folder: ${err.message}`, "error", 6000);
  }
}

async function generateCurrentStudentVideo() {
  if (!currentStudent || videoGenerating) return;
  const btn = document.getElementById("btn-generate-video");
  const origHtml = btn ? btn.innerHTML : "";
  videoGenerating = true;

  if (btn) {
    btn.disabled = true;
    btn.classList.add("opacity-70", "cursor-not-allowed");
    btn.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> Rendering...`;
    if (window.lucide) lucide.createIcons();
  }

  try {
    const res = await fetch(`/api/video/generate?npm=${encodeURIComponent(currentStudent.npm)}`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    if (!data.success) throw new Error(data.error || "Render video gagal tanpa pesan.");

    toast(`Video 9:16 untuk ${currentStudent.nama} selesai (${data.duration}s).`, "success", 6000);

    const videoEl = document.getElementById("student-real-video");
    const videoSrc = document.getElementById("student-video-src");
    if (videoEl && videoSrc) {
      videoSrc.src = data.video_url;
      videoEl.load();
      videoEl.play().catch(() => { /* autoplay bisa diblokir browser */ });
    }
    await detectStudentProgressPhotos(currentStudent.npm);
  } catch (err) {
    toast(`Gagal render video: ${err.message}`, "error", 9000);
  } finally {
    videoGenerating = false;
    if (btn) {
      btn.disabled = false;
      btn.classList.remove("opacity-70", "cursor-not-allowed");
      btn.innerHTML = origHtml;
      if (window.lucide) lucide.createIcons();
    }
  }
}

function downloadStudentVideoMP4() {
  if (!currentStudent) return;
  const videoUrl = `/videos/video_portofolio_${currentStudent.npm}.mp4`;
  const a = document.createElement("a");
  a.href = videoUrl;
  a.download = `05_video_portofolio_${currentStudent.npm}_${currentStudent.nama.replace(/\s+/g, "_")}.mp4`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// Copy Instagram Caption
function copyInstagramCaption() {
  if (!currentStudent) return;
  const caption = `Alhamdulillah! Progres pembelajaran ananda ${currentStudent.nama} di Program Studi Arsitektur bulan ini menunjukkan dedikasi luar biasa.\n\n` +
    `Mulai dari perancangan denah presisi hingga kalkulasi detail potongan dan estimasi volume, karya nyata siap portofolio telah tuntas dengan predikat ${currentStudent.akademik.grade}.\n\n` +
    `Bangga bersama Program Studi Arsitektur!\n` +
    `#Arsitektur #MahasiswaArsitektur #KaryaArsitektur #AutoCAD #DesainBangunan #GenerasiUnggul`;
  copyToClipboard(caption, "Caption Instagram & hashtag berhasil disalin!");
}

// =============================================================================
// TAB 4: WHATSAPP SIMULATOR
// =============================================================================
function renderWhatsAppSimulation(student) {
  setText("wa-recipient-name", `Wali Murid ${student.nama}`);

  const courseName = (masterData && masterData.course && masterData.course.nama_mk)
    ? masterData.course.nama_mk : "Aplikasi Komputer Arsitektur & QS";
  const openingText = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\nKepada Yth. Bapak/Ibu Wali Murid dari *${student.nama}*,\n\nSalam hangat dan salam sejahtera dari Program Studi Arsitektur, Fakultas Teknik & Desain.\n\nBerikut kami sampaikan Surat Resmi Perkembangan Akademik, Portofolio Pembelajaran, dan Pemetaan 10 Karier Masa Depan ananda pada mata kuliah *${courseName}* untuk periode semester berjalan:`;
  setText("wa-opening-text", openingText);

  setText("wa-card-file-1", `01_rekap_kehadiran_${student.npm}.pdf`);
  setText("wa-card-file-2", `02_rapor_akhir_kompetensi_${student.npm}.pdf`);
  setText("wa-card-file-3", `05_deckcraft_portofolio_${student.npm}.pdf`);
}

function copyWhatsAppMessage() {
  if (!currentStudent) return;
  const courseName = (masterData && masterData.course && masterData.course.nama_mk)
    ? masterData.course.nama_mk : "Aplikasi Komputer Arsitektur & QS";
  const fullMsg = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\n` +
    `Kepada Yth. Bapak/Ibu Wali Murid dari *${currentStudent.nama}*,\n\n` +
    `Salam hangat dari Program Studi Arsitektur, Fakultas Teknik & Desain.\n` +
    `Melalui pesan ini, kami menyampaikan Surat Resmi Perkembangan Akademik, Portofolio Pembelajaran, dan Pemetaan 10 Karier Masa Depan ananda pada mata kuliah *${courseName}* periode semester berjalan.\n\n` +
    `Bersama pesan ini, kami lampirkan 3 Dokumen Resmi Terverifikasi:\n` +
    `1. 📎 Rekap Kehadiran Mahasiswa Bulanan (Presensi & Log Sesi Praktikum)\n` +
    `2. 📎 Rapor Hasil Evaluasi Akhir & Pemetaan 10 Karier Masa Depan (Capaian Kompetensi & Kesiapan Profesi)\n` +
    `3. 📎 Portofolio Karya & Dokumentasi Studio Arsitektur (Slide Deck Presentasi 16:9 Widescreen)\n\n` +
    `Bapak/Ibu dapat mengunduh dan meninjau berkas PDF terlampir. Terima kasih atas doa, bimbingan, dan cinta kasih yang senantiasa Bapak/Ibu berikan kepada ananda tercinta di rumah.\n\n` +
    `Hormat kami,\n` +
    `*Ketua Program Studi Arsitektur*\n` +
    `*Fielda Roza, S.T., M.T.*\n` +
    `Asisten Dosen: *Adrian Ridhoa, S.T.*`;

  copyToClipboard(fullMsg, "Pesan pembuka resmi & daftar lampiran berhasil disalin!");
}

/** Clipboard + fallback untuk browser yang menolak navigator.clipboard (non-secure context). */
function copyToClipboard(text, successMessage) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text)
      .then(() => toast(successMessage, "success"))
      .catch(() => legacyCopy(text, successMessage));
  } else {
    legacyCopy(text, successMessage);
  }
}

function legacyCopy(text, successMessage) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  try {
    const ok = document.execCommand("copy");
    toast(ok ? successMessage : "Gagal menyalin otomatis. Tekan Ctrl+C manual.",
          ok ? "success" : "error", 6000);
  } catch (e) {
    toast("Gagal menyalin otomatis. Tekan Ctrl+C manual.", "error", 6000);
  }
  ta.remove();
}

function openWhatsAppDirect() {
  if (!currentStudent) return;
  const fullMsg = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\n` +
    `Kepada Yth. Bapak/Ibu Wali Murid dari *${currentStudent.nama}*,\n\n` +
    `Berikut kami sampaikan berkas Laporan Hasil Belajar & Portofolio Arsitektur ananda dalam 3 lampiran dokumen PDF resmi terverifikasi. Terima kasih atas bimbingan dan dukungan Bapak/Ibu di rumah.\n\n` +
    `Hormat kami,\nProgram Studi Arsitektur`;
  window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(fullMsg)}`, "_blank", "noopener");
}

function exportDataJSON() {
  if (!masterData) return;
  const str = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(masterData, null, 2));
  const a = document.createElement("a");
  a.setAttribute("href", str);
  a.setAttribute("download", `SIAK_ARSITEKTUR_DATA_${new Date().toISOString().slice(0, 10)}.json`);
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// =============================================================================
// PDF DOWNLOAD CONTROLLERS
// =============================================================================
/** Buka PDF on-demand. Dulu pakai window.open -> kalau gagal, user cuma lihat
 *  tab kosong tanpa tahu apa yang salah. Sekarang errornya ditampilkan. */
async function openPdf(url, label) {
  const win = window.open("", "_blank");
  if (!win) {
    toast("Popup diblokir browser. Izinkan popup untuk situs ini lalu coba lagi.", "warn", 7000);
  }
  try {
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    const blob = await res.blob();
    const objUrl = URL.createObjectURL(blob);
    if (win) {
      win.location.href = objUrl;
    } else {
      window.open(objUrl, "_blank");
    }
    setTimeout(() => URL.revokeObjectURL(objUrl), 60000);
    toast(`${label} siap.`, "success");
  } catch (err) {
    if (win) win.close();
    toast(`Gagal membuat ${label}: ${err.message}`, "error", 9000);
  }
}

function downloadKaprodiGradebook() {
  openPdf("/api/pdf/download?type=gradebook", "PDF Gradebook Kaprodi");
}

function downloadDosenAuditPDF() {
  openPdf("/api/pdf/download?type=audit", "PDF Audit Dosen");
}

function downloadCurrentStudentMonthlyPDF() {
  if (!currentStudent) return;
  openPdf(`/api/pdf/download?type=monthly&npm=${encodeURIComponent(currentStudent.npm)}`,
           "PDF Rekap Kehadiran");
}

function downloadCurrentStudentFinalPDF() {
  if (!currentStudent) return;
  openPdf(`/api/pdf/download?type=rapor&npm=${encodeURIComponent(currentStudent.npm)}`,
           "PDF Rapor Capaian & Karier");
}

function downloadCurrentStudentDeckcraftPDF() {
  if (!currentStudent) return;
  openPdf(`/api/pdf/download?type=deckcraft&npm=${encodeURIComponent(currentStudent.npm)}`,
           "PDF DeckCraft 16:9");
}

function downloadAll3StudentPDFs() {
  if (!currentStudent) return;
  const npm = encodeURIComponent(currentStudent.npm);
  openPdf(`/api/pdf/download?type=monthly&npm=${npm}`, "PDF 1: Rekap Kehadiran");
  setTimeout(() => openPdf(`/api/pdf/download?type=rapor&npm=${npm}`, "PDF 2: Rapor"), 900);
  setTimeout(() => openPdf(`/api/pdf/download?type=deckcraft&npm=${npm}`, "PDF 3: DeckCraft"), 1800);
}

function openLiveDeckcraft() {
  if (!currentStudent) return;
  window.open(`/api/deckcraft_html?npm=${encodeURIComponent(currentStudent.npm)}`, "_blank", "noopener");
}

// Dynamic Course Switcher
async function switchActiveCourse(courseId) {
  if (!courseId) return;
  const selector = document.getElementById("course-selector");
  try {
    selector.disabled = true;
    const res = await fetch(`/api/switch_course?course=${encodeURIComponent(courseId)}`);
    const resData = await res.json();
    if (!res.ok) throw new Error(resData.error || `HTTP ${res.status}`);
    if (!resData.success) throw new Error(resData.error || "Gagal berganti mata kuliah.");

    toast(`Mata kuliah aktif: ${resData.active_course.nama_mk}`, "success");
    // FIX TAHAP C-5: beri tahu kalau kode katalog tidak ikut berubah.
    // - "sudah aktif"  -> memang tidak ada yang perlu berubah
    // - "diselaraskan" -> katalog MK ini tertinggal versi, sudah diperbaiki
    if (resData.catatan) toast(resData.catatan, "info", 9000);
    // Muat ulang seluruh dataset; loadAcademicData() akan menyinkronkan header
    // dan dropdown ke course yang baru (bukan lagi ke pilihan pertama).
    await loadAcademicData();
    if (selector) selector.value = courseId;
  } catch (err) {
    toast(`Gagal berganti mata kuliah: ${err.message}`, "error", 8000);
  } finally {
    if (selector) selector.disabled = false;
  }
}

// =============================================================================
// TAB 5: PENGATURAN IDENTITAS  (config/identitas.json)
// =============================================================================
// Sengaja dibagi 3 tingkat supaya tidak ada satu klik yang diam-diam mengubah
// dokumen resmi:
//   1. Simpan Identitas   -> hanya label dashboard. Instan. Tidak menyentuh data.
//   2. Terapkan ke Dokumen-> regen data master, nama ikut ke pesan wali murid + PDF.
//   3. Cetak Ulang PDF    -> cetak ulang paket arsip. Berat. Hanya boleh setelah (2).
// Selama (2) belum dijalankan, banner peringatan wajib terlihat - "sudah
// disimpan" TIDAK sama dengan "sudah diterapkan".
let identitasData = null;      // payload terakhir dari GET /api/identitas
let mkSedangDiatur = null;     // kunci mata kuliah yang sedang tampil di form

function _bisa(el) { return el !== null && el !== undefined; }

async function muatIdentitas(opts = {}) {
  const diam = opts && opts.diam === true;
  const status = document.getElementById("pengaturan-status");
  if (status) status.textContent = "Memuat…";
  try {
    const res = await fetch("/api/identitas", { cache: "no-store" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    identitasData = data;
    terapkanIdentitasKeForm(data);
    terapkanHeaderIdentitas(data);
    renderBannerPenerapan(data);
    if (status) status.textContent = "";
  } catch (err) {
    if (status) status.textContent = "";
    if (!diam) toast(`Gagal memuat identitas: ${err.message}`, "error", 8000);
  }
}

/**
 * Judul / sub judul / deskripsi dashboard dari config (placeholder {prodi} dll
 * sudah diisi oleh server). Kalau kosong, teks di HTML dibiarkan apa adanya.
 */
function terapkanHeaderIdentitas(data) {
  const h = (data && data.header) || {};
  if (h.judul) setText("hero-judul", h.judul);
  if (h.subjudul) setText("hero-subjudul", h.subjudul);
  if (h.deskripsi) setText("hero-deskripsi", h.deskripsi);
}

function terapkanIdentitasKeForm(data) {
  const cfg = (data && data.config) || {};
  const inst = cfg.institusi || {};
  const dash = cfg.dashboard || {};
  const dok = cfg.dokumen || {};
  const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v ?? ""; };

  setVal("cfg-universitas", inst.universitas);
  setVal("cfg-fakultas", inst.fakultas);
  setVal("cfg-prodi", inst.prodi);
  setVal("cfg-kota", inst.kota);
  setVal("cfg-kaprodi", inst.ketua_prodi);
  setVal("cfg-nip-kaprodi", inst.nip_ketua_prodi);
  setVal("cfg-judul", dash.judul);
  setVal("cfg-subjudul", dash.subjudul);
  setVal("cfg-deskripsi", dash.deskripsi);
  setVal("cfg-tanggal", dok.tanggal_tanda_tangan);

  const jalur = document.getElementById("pengaturan-jalur");
  if (jalur && data && data.jalur) jalur.textContent = data.jalur;

  const pilih = document.getElementById("cfg-mk-pilih");
  if (!pilih) return;
  pilih.innerHTML = "";
  Object.entries(cfg.mata_kuliah || {}).forEach(([kunci, mk]) => {
    const opt = document.createElement("option");
    opt.value = kunci;
    opt.textContent = mk.nama_mk + (kunci === cfg.mata_kuliah_aktif ? " • aktif" : "");
    pilih.appendChild(opt);
  });
  const daftar = cfg.mata_kuliah || {};
  const target = (mkSedangDiatur && daftar[mkSedangDiatur]) ? mkSedangDiatur : cfg.mata_kuliah_aktif;
  if (target) pilih.value = target;
  pilihMkUntukDiatur(target);
}

function pilihMkUntukDiatur(kunci) {
  if (!kunci || !identitasData || !identitasData.config) return;
  const cfg = identitasData.config;
  const mk = (cfg.mata_kuliah || {})[kunci];
  if (!mk) return;
  mkSedangDiatur = kunci;
  const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v ?? ""; };

  setVal("cfg-mk-nama", mk.nama_mk);
  setVal("cfg-mk-kode", mk.kode_mk);
  setVal("cfg-mk-sks", mk.sks);
  setVal("cfg-mk-kelas", mk.kelas);
  setVal("cfg-mk-semester", mk.semester);
  setVal("cfg-mk-jadwal", mk.jadwal);
  setVal("cfg-mk-dosen", (mk.dosen_pengasuh || []).join("\n"));
  setVal("cfg-mk-asisten", mk.asisten_dosen);
  setVal("cfg-mk-asisten-nip", mk.asisten_nip);
  const aktif = document.getElementById("cfg-mk-aktif");
  if (aktif) aktif.checked = (kunci === cfg.mata_kuliah_aktif);
}

function kumpulkanFormKeConfig() {
  const cfg = JSON.parse(JSON.stringify(identitasData.config));
  const val = (id) => { const el = document.getElementById(id); return el ? el.value.trim() : ""; };

  cfg.institusi = cfg.institusi || {};
  cfg.institusi.universitas = val("cfg-universitas");
  cfg.institusi.fakultas = val("cfg-fakultas");
  cfg.institusi.prodi = val("cfg-prodi");
  cfg.institusi.kota = val("cfg-kota");
  cfg.institusi.ketua_prodi = val("cfg-kaprodi");
  cfg.institusi.nip_ketua_prodi = val("cfg-nip-kaprodi");

  cfg.dashboard = cfg.dashboard || {};
  cfg.dashboard.judul = val("cfg-judul");
  cfg.dashboard.subjudul = val("cfg-subjudul");
  cfg.dashboard.deskripsi = val("cfg-deskripsi");

  cfg.dokumen = cfg.dokumen || {};
  cfg.dokumen.tanggal_tanda_tangan = val("cfg-tanggal");

  const kunci = mkSedangDiatur || cfg.mata_kuliah_aktif;
  cfg.mata_kuliah = cfg.mata_kuliah || {};
  const sks = parseInt(val("cfg-mk-sks"), 10);
  cfg.mata_kuliah[kunci] = {
    kode_mk: val("cfg-mk-kode"),
    nama_mk: val("cfg-mk-nama"),
    sks: Number.isFinite(sks) && sks > 0 ? sks : 1,
    kelas: val("cfg-mk-kelas"),
    semester: val("cfg-mk-semester"),
    jadwal: val("cfg-mk-jadwal"),
    dosen_pengasuh: val("cfg-mk-dosen").split("\n").map(s => s.trim()).filter(Boolean),
    asisten_dosen: val("cfg-mk-asisten"),
    asisten_nip: val("cfg-mk-asisten-nip")
  };

  const aktif = document.getElementById("cfg-mk-aktif");
  if (aktif && aktif.checked) cfg.mata_kuliah_aktif = kunci;

  return cfg;
}

function tampilkanLogIdentitas(teks) {
  const el = document.getElementById("pengaturan-log");
  if (!el) return;
  if (!teks) {
    el.classList.add("hidden");
    el.textContent = "";
    return;
  }
  el.classList.remove("hidden");
  el.textContent = teks;
}

function renderBannerPenerapan(data) {
  const el = document.getElementById("pengaturan-banner");
  if (!el) return;
  const selisih = (data && data.perlu_diterapkan) || [];
  if (!selisih.length) {
    el.classList.add("hidden");
    return;
  }
  el.classList.remove("hidden");
  el.className = "rounded-2xl p-5 border shadow-xl border-amber-500/40 bg-amber-500/10 text-amber-200";
  setText("pengaturan-banner-judul", "Nama sudah disimpan, dokumen belum diperbarui");
  const rinci = selisih
    .map(s => `${s.field} → dokumen masih “${s.dokumen ?? "-"}”`)
    .join(" · ");
  setText("pengaturan-banner-isi",
    `${selisih.length} identitas belum masuk dokumen resmi (${rinci}). ` +
    "Pesan wali murid dan PDF masih memakai nama lama sampai “Terapkan ke Dokumen” dijalankan.");
}

async function kirimIdentitas(jalur, body, label) {
  const status = document.getElementById("pengaturan-status");
  if (status) status.textContent = label || "Memproses…";
  try {
    const opsi = { method: "POST" };
    if (_bisa(body)) {
      opsi.headers = { "Content-Type": "application/json" };
      opsi.body = JSON.stringify(body);
    }
    const res = await fetch(jalur, opsi);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      tampilkanLogIdentitas(data.log || data.error || `HTTP ${res.status}`);
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    if (data.config) {
      identitasData = data;
      terapkanIdentitasKeForm(data);
    }
    renderBannerPenerapan(data);
    tampilkanLogIdentitas(Array.isArray(data.log) ? data.log.join("\n") : (data.log || ""));
    toast(data.pesan || "Selesai.", "success", 7000);
    return data;
  } catch (err) {
    toast(`Gagal: ${err.message}`, "error", 9000);
    return null;
  } finally {
    if (status) status.textContent = "";
  }
}

async function simpanIdentitas() {
  if (!identitasData || !identitasData.config) {
    toast("Identitas belum termuat. Klik 'Muat Ulang' dulu.", "warn");
    return null;
  }
  const cfg = kumpulkanFormKeConfig();
  return kirimIdentitas("/api/identitas", cfg, "Menyimpan identitas…");
}

async function terapkanKeDokumen() {
  const lanjut = confirm(
    "Terapkan identitas ke DATA & DOKUMEN?\n\n" +
    "Data master akan diregenerasi dari config. Angka nilai TIDAK berubah " +
    "(dijaga tes regresi), tetapi isi pesan wali murid dan seluruh dokumen akan " +
    "memakai nama yang baru.\n\n" +
    "Data lama tetap dibackup otomatis."
  );
  if (!lanjut) return;
  const hasil = await kirimIdentitas("/api/identitas/terapkan", undefined, "Menerapkan ke dokumen…");
  if (hasil) await loadAcademicData();
}

async function regenerasiPaketPdf() {
  const lanjut = confirm(
    "Cetak ulang paket PDF arsip?\n\n" +
    "Proses ini membuka Chromium dan mencetak ulang seluruh dokumen resmi " +
    "(bisa 1-2 menit). Hanya boleh dijalankan setelah 'Terapkan ke Dokumen'.\n\n" +
    "Lanjutkan?"
  );
  if (!lanjut) return;
  await kirimIdentitas("/api/identitas/regenerasi-pdf", undefined, "Mencetak ulang paket PDF…");
}
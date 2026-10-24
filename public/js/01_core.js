/* =============================================================================
 * MODUL: public/js/01_core.js
 * DESKRIPSI: Core State, Gatekeeper PIN, Utils & Navigation Controller
 * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)
 * ============================================================================= */

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

// REPOSISI Tab 1 (2026-10-21): chart analisis baru + cache peta MK rawan

let nilaiTrendChart = null;

let radarKelasChart = null;

let mkRawanState = { prodi: null, dimuat: false, baris: [] };

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

// ------------------------------------------------------- PINTAS EKSEKUTIF KAPRODI (OPSI A)

function pintasKe(target) {

  if (target === "mk-rawan") {

    switchTab("kaprodi");

    setTimeout(() => {

      const el = document.getElementById("mk-rawan-list");

      if (el) {

        el.scrollIntoView({ behavior: "smooth", block: "center" });

        el.classList.add("ring-2", "ring-rose-500", "transition-all");

        setTimeout(() => el.classList.remove("ring-2", "ring-rose-500"), 1800);

      }

    }, 150);

  } else if (target === "kurikulum") {

    switchTab("kurikulum");

    window.scrollTo({ top: 0, behavior: "smooth" });

  } else if (target === "engine") {

    switchTab("engine");

    window.scrollTo({ top: 0, behavior: "smooth" });

  }

}

// =============================================================================
// 🛡️ GATEKEEPER AUTH & PIN PROTECTED ACCESS (UI-AUTH-01, 02, 03 & SYS-SEC-10)
// =============================================================================
let _gatekeeperPinBuffer = "";
const PIN_AUTH_KEY = "siak_kaprodi_auth";
const PIN_VAL_KEY = "siak_kaprodi_pin";

function updateGatekeeperDisplay() {
  const dots = document.querySelectorAll("#gatekeeper-dots .pin-box");
  dots.forEach((box, i) => {
    if (i < _gatekeeperPinBuffer.length) {
      box.textContent = "•";
      box.classList.add("active");
    } else {
      box.textContent = "•";
      box.classList.remove("active");
    }
  });

  const statusEl = document.getElementById("gatekeeper-status");
  if (statusEl) {
    statusEl.style.opacity = "0";
  }
}

async function verifikasiPinGatekeeper(pinOverride = null) {
  const pin = (pinOverride !== null ? pinOverride : _gatekeeperPinBuffer).trim();
  const statusEl = document.getElementById("gatekeeper-status");
  const statusText = document.getElementById("gatekeeper-status-text");
  const dotsContainer = document.getElementById("gatekeeper-dots");
  const modal = document.getElementById("gatekeeper-modal");

  if (pin.length < 6) {
    if (statusEl && statusText) {
      statusText.textContent = "Masukkan 6-digit PIN lengkap.";
      statusEl.classList.remove("text-emerald-400", "text-amber-400");
      statusEl.classList.add("text-rose-400");
      statusEl.style.opacity = "1";
    }
    return;
  }

  if (statusEl && statusText) {
    statusText.textContent = "Memverifikasi PIN Akses...";
    statusEl.classList.remove("text-rose-400", "text-emerald-400");
    statusEl.classList.add("text-amber-400");
    statusEl.style.opacity = "1";
  }

  let authenticated = false;
  try {
    const res = await fetch("/api/auth/verify_pin", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Kaprodi-PIN": pin
      },
      body: JSON.stringify({ pin: pin })
    });
    if (res.ok) {
      const data = await res.json();
      if (data && (data.authenticated === true || data.status === "ok")) {
        authenticated = true;
      }
    }
  } catch (err) {
    console.warn("[GATEKEEPER] Error probe backend, falling back to local verification:", err);
  }

  // Fallback check jika offline / static demo
  if (!authenticated && pin === "404040") {
    authenticated = true;
  }

  if (authenticated) {
    sessionStorage.setItem(PIN_AUTH_KEY, "unlocked");
    sessionStorage.setItem(PIN_VAL_KEY, pin);
    window.KAPRODI_PIN = pin;

    if (statusEl && statusText) {
      statusText.textContent = "✓ PIN Terverifikasi! Membuka sistem AL-ANALISIS...";
      statusEl.classList.remove("text-rose-400", "text-amber-400");
      statusEl.classList.add("text-emerald-400");
      statusEl.style.opacity = "1";
    }

    if (modal) {
      modal.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      modal.style.opacity = "0";
      modal.style.transform = "scale(1.02)";
      setTimeout(() => {
        modal.classList.add("hidden");
        modal.style.opacity = "";
        modal.style.transform = "";
      }, 400);
    }
    if (window.lucide) lucide.createIcons();
  } else {
    if (statusEl && statusText) {
      statusText.textContent = "PIN salah. Silakan coba kembali.";
      statusEl.classList.remove("text-emerald-400", "text-amber-400");
      statusEl.classList.add("text-rose-400");
      statusEl.style.opacity = "1";
    }

    if (dotsContainer) {
      dotsContainer.style.transform = "translateX(-8px)";
      setTimeout(() => dotsContainer.style.transform = "translateX(8px)", 80);
      setTimeout(() => dotsContainer.style.transform = "translateX(-5px)", 160);
      setTimeout(() => dotsContainer.style.transform = "translateX(5px)", 240);
      setTimeout(() => dotsContainer.style.transform = "", 320);
    }

    _gatekeeperPinBuffer = "";
    setTimeout(updateGatekeeperDisplay, 400);
  }
}

function kunciSesiDashboard() {
  sessionStorage.removeItem(PIN_AUTH_KEY);
  sessionStorage.removeItem(PIN_VAL_KEY);
  window.KAPRODI_PIN = null;
  _gatekeeperPinBuffer = "";

  const modal = document.getElementById("gatekeeper-modal");
  if (modal) {
    modal.classList.remove("hidden");
    modal.style.opacity = "1";
    modal.style.transform = "none";
  }
  updateGatekeeperDisplay();
  const input = document.getElementById("gatekeeper-pin-input");
  if (input) input.focus();
  if (window.lucide) lucide.createIcons();
}

function initGatekeeper() {
  const modal = document.getElementById("gatekeeper-modal");
  if (!modal) return;

  const isUnlocked = sessionStorage.getItem(PIN_AUTH_KEY) === "unlocked";
  if (isUnlocked) {
    modal.classList.add("hidden");
    window.KAPRODI_PIN = sessionStorage.getItem(PIN_VAL_KEY) || "404040";
  } else {
    modal.classList.remove("hidden");
    updateGatekeeperDisplay();
  }

  // Keypad numeric click handlers
  document.querySelectorAll(".keypad-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const val = btn.getAttribute("data-val");
      if (_gatekeeperPinBuffer.length < 6) {
        _gatekeeperPinBuffer += val;
        updateGatekeeperDisplay();
        if (_gatekeeperPinBuffer.length === 6) {
          verifikasiPinGatekeeper();
        }
      }
    });
  });

  // Backspace handler
  const btnBack = document.getElementById("btn-gatekeeper-backspace");
  if (btnBack) {
    btnBack.addEventListener("click", () => {
      if (_gatekeeperPinBuffer.length > 0) {
        _gatekeeperPinBuffer = _gatekeeperPinBuffer.slice(0, -1);
        updateGatekeeperDisplay();
      }
    });
  }

  // Clear handler
  const btnClear = document.getElementById("btn-gatekeeper-clear");
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      _gatekeeperPinBuffer = "";
      updateGatekeeperDisplay();
    });
  }

  // Submit button
  const btnSubmit = document.getElementById("btn-gatekeeper-submit");
  if (btnSubmit) {
    btnSubmit.addEventListener("click", () => {
      verifikasiPinGatekeeper();
    });
  }

  // Hint button for visitors / reviewers
  const btnHint = document.getElementById("btn-gatekeeper-hint");
  if (btnHint) {
    btnHint.addEventListener("click", () => {
      _gatekeeperPinBuffer = "404040";
      updateGatekeeperDisplay();
      verifikasiPinGatekeeper("404040");
    });
  }

  // Physical keyboard support
  window.addEventListener("keydown", (e) => {
    if (modal.classList.contains("hidden")) return;
    if (e.key >= "0" && e.key <= "9") {
      if (_gatekeeperPinBuffer.length < 6) {
        _gatekeeperPinBuffer += e.key;
        updateGatekeeperDisplay();
        if (_gatekeeperPinBuffer.length === 6) {
          verifikasiPinGatekeeper();
        }
      }
    } else if (e.key === "Backspace") {
      if (_gatekeeperPinBuffer.length > 0) {
        _gatekeeperPinBuffer = _gatekeeperPinBuffer.slice(0, -1);
        updateGatekeeperDisplay();
      }
    } else if (e.key === "Escape") {
      _gatekeeperPinBuffer = "";
      updateGatekeeperDisplay();
    } else if (e.key === "Enter") {
      verifikasiPinGatekeeper();
    }
  });

  // Lock session button in top header navbar
  const btnLock = document.getElementById("btn-lock-session");
  if (btnLock) {
    btnLock.addEventListener("click", () => {
      kunciSesiDashboard();
    });
  }
}

// Auto-attach X-Kaprodi-PIN on POST requests
const _nativeFetchWithPin = window.fetch;
window.fetch = function (input, init = {}) {
  const pin = window.KAPRODI_PIN || sessionStorage.getItem("siak_kaprodi_pin");
  if (pin && init && init.method && init.method.toUpperCase() === "POST") {
    init.headers = init.headers || {};
    if (init.headers instanceof Headers) {
      if (!init.headers.has("X-Kaprodi-PIN")) init.headers.set("X-Kaprodi-PIN", pin);
    } else {
      if (!init.headers["X-Kaprodi-PIN"]) init.headers["X-Kaprodi-PIN"] = pin;
    }
  }
  return _nativeFetchWithPin.call(this, input, init);
};

// On Page Load

document.addEventListener("DOMContentLoaded", async () => {

  initGatekeeper();

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

    await syncActiveCourseToUi(masterData.course);

    renderKaprodiDashboard();

    renderDosenSection();

    populateStudentDropdown();

    _sinkronWaliContextSelectors();

    populateSessionFilter();

    populateBulanFilter();

    const secRekap = document.getElementById("section-rekap");

    if (secRekap && !secRekap.classList.contains("hidden")) {

      const kunciAktif = (masterData.metadata && masterData.metadata.kunci_mk) || _nilai("course-selector");

      sinkronkanTabRekapKeKonteks(kunciAktif);

    }

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

/** Sinkronkan header + konteks (PRODI > TAHUN > SEMESTER > MK) ke MK yang AKTIF.

 *

 * TAHAP E: daftar mata kuliah tidak lagi ditulis di dalam index.html. Pilihan

 * diambil dari tree kurikulum lewat /api/kurikulum, jadi menambah MK di tree

 * cukup - tidak perlu mengedit HTML.

 */

async function syncActiveCourseToUi(course) {

  if (!course || !course.nama_mk) return;

  setText("current-course-title", course.nama_mk);

  try {

    await muatKurikulum();

    muatMkRawan();

  } catch (_) { /* header tetap jalan walau tree gagal dibaca */ }

  setText("kpi-jadwal-desc", course.jadwal || "");

  // Asisten mengikuti MK aktif - tiap MK boleh punya asisten berbeda

  // (diatur per-MK di menu Pengaturan).

  const asisten = course.asisten_dosen || "-";

  setText("header-asisten", asisten);

  setText("wali-asisten", asisten);

  setText("wa-asisten-nama", asisten);

}

/** Filter sesi dibangun dari data, bukan dari topik AutoCAD yang diketik manual. */

function populateSessionFilter() {

  const sel = document.getElementById("filter-session");

  if (!sel || !masterData) return;

  const current = sel.value;

  sel.innerHTML = `<option value="all">Semua Pertemuan (${masterData.sessions.length})</option>`;

  masterData.sessions.forEach(s => {

    const opt = document.createElement("option");

    opt.value = s.pertemuan;

    const topic = (s.topik || "").length > 34 ? s.topik.slice(0, 34) + "..." : (s.topik || "");

    opt.textContent = `P${s.pertemuan}: ${topic}`;

    sel.appendChild(opt);

  });

  sel.value = current || "all";

}

// =============================================================================

// LEVEL 1: FILTER PER BULAN (Kaprodi) — dari tanggal ISO sesi.json

// =============================================================================

// Keputusan user (2026-10-21): pertemuan tanpa tanggal (placeholder) dikelompokkan

// sendiri di "Tanpa Tanggal", BUKAN ikut bulan yang salah.

const GRUP_TANPA_TANGGAL = "-";

function bulanDariTanggal(t) {

  t = String(t || "").trim();

  return /^\d{4}-\d{2}/.test(t) ? t.slice(0, 7) : GRUP_TANPA_TANGGAL;

}

function labelBulan(b) {

  if (b === GRUP_TANPA_TANGGAL) return "Tanpa Tanggal";

  const [y, m] = b.split("-");

  const nama = ["Januari","Februari","Maret","April","Mei","Juni","Juli",

    "Agustus","September","Oktober","November","Desember"][Number(m) - 1] || m;

  return `${nama} ${y}`;

}

function populateBulanFilter() {

  const sel = document.getElementById("filter-bulan");

  if (!sel || !masterData) return;

  const current = sel.value || "all";

  const hitung = {};

  masterData.sessions.forEach(s => {

    const b = bulanDariTanggal(s.tanggal);

    hitung[b] = (hitung[b] || 0) + 1;

  });

  const urut = Object.keys(hitung)

    .sort((a, b2) => (a === GRUP_TANPA_TANGGAL) - (b2 === GRUP_TANPA_TANGGAL) || a.localeCompare(b2));

  sel.innerHTML = `<option value="all">Semua Bulan (${masterData.sessions.length} pertemuan)</option>`;

  urut.forEach(b => {

    const opt = document.createElement("option");

    opt.value = b;

    opt.textContent = `${labelBulan(b)} (${hitung[b]})`;

    sel.appendChild(opt);

  });

  sel.value = urut.includes(current) ? current : "all";

}

function bulanAktif() {

  const sel = document.getElementById("filter-bulan");

  return sel ? sel.value : "all";

}

function pertemuanDalamBulan() {

  const b = bulanAktif();

  if (b === "all") return null; // null = tidak memfilter

  return new Set(masterData.sessions

    .filter(s => bulanDariTanggal(s.tanggal) === b)

    .map(s => String(s.pertemuan)));

}

/** KPI ringkas satu bulan: rata kehadiran slot atas pertemuan yang datanya

 *  lengkap (belum diinput NETRAL - aturan yang sama dengan Batch B). */

function ringkasBulanAktif() {

  const setP = pertemuanDalamBulan();

  if (!masterData || !setP) return null;

  let hadir = 0, total = 0, belum = 0;

  masterData.students.forEach(s => {

    (s.kehadiran && s.kehadiran.detail || []).forEach(d => {

      if (!setP.has(String(d.pertemuan))) return;

      if (d.status === "Belum Diinput") { belum++; return; } // netral

      hadir += (d.slot_hadir || 0);

      total += (d.slot_total || 0);

    });

  });

  const b = bulanAktif();

  return {

    label: labelBulan(b),

    kehadiran: total

      ? `${Math.round((hadir / total) * 1000) / 10}%`

      : "belum bisa dihitung",

    pertemuan: setP.size,

    belum: belum,

  };

}

function onBulanBerubah() {

  renderKaprodiDashboard();

}

/** Badge Level 2: konteks periode eksplisit dari MASTER (bukan ditebak). */

function updatePeriodeBadge() {

  const el = document.getElementById("kaprodi-periode-badge");

  if (!el || !masterData) return;

  const md = masterData.metadata || {};

  const parts = [

    md.tahun_ajar || "-",

    (md.semester || "").toUpperCase(),

    (masterData.course && masterData.course.nama_mk) || md.kunci_mk || "-",

  ].filter(Boolean);

  const semuaLengkap = md.tahun_ajar && md.semester && md.kunci_mk;

  el.innerHTML =

    `<i data-lucide="calendar-clock" class="w-3.5 h-3.5 text-sky-400"></i> ` +

    `Periode data: <strong class="text-slate-200">${parts

      .map(p => escapeHtml(p)).join(" · ")}</strong>` +

    (semuaLengkap ? "" : " <span class='text-amber-400'>(metadata master tidak lengkap)</span>");

  if (window.lucide) lucide.createIcons();

}

// Switch Active Navigation Tabs

function switchTab(tabName, opsi) {
  closeMobileSidebar();

  // Membuka tab Kurikulum lewat menu = kembali ke MK aktif. Drill-down dari

  // tab Rekap memakai {pertahankanOverride:true} supaya MK yang dipilih tetap

  // ditampilkan tanpa memicu switch_course.

  if (tabName === "kurikulum" && !(opsi && opsi.pertahankanOverride)) {

    detailOverrideKonteks = null;

  }

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

  // Tab Wali: sinkronkan context bar Tahun -> Semester -> MK

  if (tabName === "wali") {

    _sinkronWaliContextSelectors();

    if (radarCompetencyChart) {

      setTimeout(() => { try { radarCompetencyChart.render(); } catch (e) { /* noop */ } }, 120);

    }

  }

  // Tab Pengaturan: muat identitas terbaru dari server tiap kali dibuka, supaya

  // yang tampil selalu keadaan sebenarnya (termasuk kalau config diubah manual).

  if (tabName === "pengaturan") muatIdentitas();

  // Tab Kurikulum: ambil ulang pohon + isi MK yang sedang dipilih, supaya yang

  // tampil adalah isi tree saat ini (bisa saja baru diubah dari luar dashboard).

  if (tabName === "kurikulum") {

    muatKurikulum()

      .then(() => muatDetailKurikulum())

      .catch(err => toast(`Tree kurikulum tidak bisa dibaca: ${err.message}`, "error", 8000));

  }

  // Tab Rekap Periode: ambil ulang agregasi + panel potensi tiap kali dibuka,

  // supaya yang tampil adalah isi tree saat ini (cache di server usang sendiri

  // via mtime).

  if (tabName === "rekap") {

    const aktif = _nilai("course-selector");

    _isiPilihMkPotensi(aktif);

    muatRekap();

    muatPotensiMk(aktif);

  }

  // Tab 9 Portofolio: isi dropdown sekali, lalu muat data mahasiswa terpilih.

  if (tabName === "portofolio") muatPortofolio();

  // Tab 10 Engine: auto-load HANYA pertama kali tab dibuka per sesi. Pindai

  // & audit menulis/queries bisa memicu tulis registry; muat berulang tiap

  // buka tab = kerja ulang + spam tulis (bug #5). Buka ulang tab pakai

  // tombol Pindai/Audit manual.

  if (tabName === "engine" && !window.__engineSudahMuat) {

    engineInputPindai(); engineOutputAudit();

    window.__engineSudahMuat = true;

  }

  // Tab Dosen: audit presensi tatap muka & modul pembelajaran RPS

  if (tabName === "dosen") renderDosenSection();

  // Tab 11 Yayasan: cockpit eksekutif & investor

  if (tabName === "yayasan") renderExecutiveCockpit();

  if (tabName === "pertumbuhan") renderGrowthTab();

  // Tab 13 Visual Analytics Studio & Observatorium Grafik

  if (tabName === "analytics") muatVisualAnalytics();

  // Tab Info: dokumentasi dibaca dari public/info.md (di-cache setelah sukses).

  if (tabName === "info") muatInfoSistem();

  if (window.lucide) lucide.createIcons();

}

// =============================================================================

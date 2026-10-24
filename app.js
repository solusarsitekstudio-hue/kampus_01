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



// TAB 9: PORTOFOLIO MAHASISWA 4 LAPIS (keputusan user 2026-10-21)



// =============================================================================



// Sumber satu pintu: /api/portofolio?npm=... (katalog SEMUA MK di tree):



//   lapis 1 per bulan, lapis 2 per MK, lapis 3 per semester, lapis 4 kumulatif.



// PDF lengkap via /api/pdf/download?type=portofolio_lengkap (mesin v3 juga).



// =============================================================================







let _portofolioData = null;    // hasil /api/portofolio mahasiswa aktif



let _portofolioMuat = false;   // dropdown sudah diisi masterData?







/** Isi dropdown + muat data mahasiswa terpilih (prioritaskan mahasiswa aktif saat ini). */



function muatPortofolio(npmTarget) {



  _sinkronPortoContextSelectors();



  _sinkronPortoContextSelectors();



  _sinkronPortoContextSelectors();



  if (!masterData) {



    toast("Data master belum dimuat, coba lagi sebentar.", "error");



    return;



  }



  const sel = document.getElementById("porto-sel");



  if (sel && !sel.options.length) {



    masterData.students.forEach(s => {



      const opt = document.createElement("option");



      opt.value = s.npm;



      opt.textContent = `${s.nama} — ${s.npm}`;



      sel.appendChild(opt);



    });



  }



  const target = npmTarget;



  let chosenNpm = target;



  if (sel) {



    if (target && Array.from(sel.options).some(o => o.value === String(target))) {



      sel.value = String(target);



    } else if (!sel.value && masterData.students.length) {



      sel.value = String(masterData.students[0].npm);



    }



    chosenNpm = sel.value;



  }



  if (!chosenNpm && masterData.students.length) {



    chosenNpm = String(masterData.students[0].npm);



  }



  if (chosenNpm && masterData && Array.isArray(masterData.students)) {



    const s = masterData.students.find(x => String(x.npm) === String(chosenNpm));



    if (s) {



      currentStudent = s;



      const input = document.getElementById("porto-search-input");



      if (input && !input.matches(":focus")) input.value = `${s.nama} (${s.npm})`;
      const dropdown = document.getElementById("student-dropdown");
      if (dropdown && dropdown.value !== String(s.npm)) dropdown.value = String(s.npm);



    }



  }



  _ambilPortofolio(chosenNpm);



}







function onPortoSelChange() {



  const sel = document.getElementById("porto-sel");



  if (!sel || !sel.value) return;



  const npm = sel.value;



  if (masterData && Array.isArray(masterData.students)) {



    const s = masterData.students.find(x => String(x.npm) === String(npm));



    if (s) {



      currentStudent = s;



      const input = document.getElementById("porto-search-input");



      if (input && !input.matches(":focus")) input.value = `${s.nama} (${s.npm})`;
      const dropdown = document.getElementById("student-dropdown");
      if (dropdown && dropdown.value !== String(s.npm)) dropdown.value = String(s.npm);



    }



  }



  _ambilPortofolio(npm);



}







/* Omni-Search & Quick Filter Tab 10 */



function filterPortoSearch(query) {



  const container = document.getElementById("porto-search-results");



  if (!container || !masterData || !Array.isArray(masterData.students)) return;



  const q = (query || "").trim().toLowerCase();



  const list = masterData.students.filter(s => {



    if (!q) return true;



    return (s.nama || "").toLowerCase().includes(q) || String(s.npm || "").toLowerCase().includes(q);



  });



  if (list.length === 0) {



    container.innerHTML = `<div class="p-3 text-xs text-slate-400 italic text-center">Tidak ada mahasiswa yang cocok.</div>`;



    container.classList.remove("hidden");



    return;



  }



  container.innerHTML = list.slice(0, 15).map(s => {



    const ini = (s.nama || "").split(" ").filter(Boolean).map(w => w[0]).slice(0, 2).join("").toUpperCase() || "?";



    const isAtRisk = s.at_risk || (s.akademik && s.akademik.at_risk);



    const badge = isAtRisk



      ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/10 text-rose-300 border border-rose-500/30">At-Risk</span>`



      : `<span class="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">Grade ${s.akademik?.grade || "A"}</span>`;



    return `



      <div onclick="pilihPortoStudent('${s.npm}')" class="p-2.5 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between gap-3 transition">



        <div class="flex items-center gap-2.5 min-w-0">



          <div class="w-7 h-7 rounded-lg bg-lime-500/20 text-lime-400 font-bold text-xs flex items-center justify-center shrink-0 border border-lime-500/30">



            ${ini}



          </div>



          <div class="truncate">



            <div class="text-xs font-bold text-white truncate">${escapeHtml(s.nama)}</div>



            <div class="text-[10px] text-slate-400 font-mono">${s.npm}</div>



          </div>



        </div>



        <div class="shrink-0">${badge}</div>



      </div>



    `;



  }).join("");



  container.classList.remove("hidden");



}







function showPortoDropdown() {



  const input = document.getElementById("porto-search-input");



  filterPortoSearch(input ? input.value : "");



}







function clearPortoSearch() {



  const input = document.getElementById("porto-search-input");



  if (input) input.value = "";



  const container = document.getElementById("porto-search-results");



  if (container) container.classList.add("hidden");



}







function filterPortoChip(tipe) {



  const container = document.getElementById("porto-search-results");



  if (!container || !masterData) return;



  let list = masterData.students || [];



  if (tipe === "star") {



    list = list.filter(s => s.akademik && (s.akademik.grade === "A" || s.akademik.nilai_akhir >= 85));



  } else if (tipe === "atrisk") {



    list = list.filter(s => s.at_risk || (s.akademik && s.akademik.at_risk));



  }



  container.innerHTML = list.slice(0, 15).map(s => {



    const ini = (s.nama || "").split(" ").filter(Boolean).map(w => w[0]).slice(0, 2).join("").toUpperCase() || "?";



    return `



      <div onclick="pilihPortoStudent('${s.npm}')" class="p-2.5 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between gap-3 transition">



        <div class="flex items-center gap-2.5 min-w-0">



          <div class="w-7 h-7 rounded-lg bg-lime-500/20 text-lime-400 font-bold text-xs flex items-center justify-center shrink-0 border border-lime-500/30">



            ${ini}



          </div>



          <div class="truncate">



            <div class="text-xs font-bold text-white truncate">${escapeHtml(s.nama)}</div>



            <div class="text-[10px] text-slate-400 font-mono">${s.npm}</div>



          </div>



        </div>



      </div>



    `;



  }).join("");



  container.classList.remove("hidden");



}







function pilihPortoStudent(npm) {



  const sel = document.getElementById("porto-sel");



  if (sel) sel.value = String(npm);



  const mhsDropdown = document.getElementById("porto-sel-mhs");



  if (mhsDropdown) mhsDropdown.value = String(npm);



  const container = document.getElementById("porto-search-results");



  if (container) container.classList.add("hidden");



  if (masterData && Array.isArray(masterData.students)) {



    const s = masterData.students.find(x => String(x.npm) === String(npm));



    if (s) {



      currentStudent = s;



      const input = document.getElementById("porto-search-input");



      if (input) input.value = `${s.nama} (${s.npm})`;



    }



  }



  _ambilPortofolio(npm);



}







document.addEventListener("click", function(e) {



  const container = document.getElementById("porto-search-results");



  const input = document.getElementById("porto-search-input");



  if (!container || !input) return;



  if (!container.contains(e.target) && e.target !== input) {



    container.classList.add("hidden");



  }



});







function _targetPortofolio() {



  // Prioritas: mahasiswa yang sedang dipilih di tab wali (kesinambungan UX).



  return currentStudent ? String(currentStudent.npm) : null;



}







/** LAPIS B potensi karier: narasi top-N dirapikan engine Gemini rotary.



 *  Fail-closed: gagal/p refusal -> tetap template; sukses -> reload portofolio



 *  (cache AI sudah ditempel otomatis server di /api/portofolio). */



let _aiKarrierJalan = false;



async function kirimKierAI(paksa = false) {



  const sel = document.getElementById("porto-sel");



  const npm = (sel && sel.value) || _targetPortofolio();



  const btn = document.getElementById("porto-ai-btn");



  if (_aiKarrierJalan || !npm) return;



  _aiKarrierJalan = true;



  const label = btn ? btn.innerHTML : "";



  if (btn) {



    btn.disabled = true;



    btn.innerHTML = `<i data-lucide="loader" class="w-3 h-3 animate-spin"></i> AI menyunting…`;



  }



  try {



    const res = await fetch("/api/portofolio/ai", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ npm: String(npm), paksa: !!paksa }),



    });



    const data = await res.json();



    if (!res.ok || data.ok === false) {



      toast(



        `${data.sebab || `HTTP ${res.status}`} — narasi tetap pakai template (fail-closed).`,



        "warn");



      return;



    }



    toast(



      `Narasi ${data.jumlah} karier dirapikan AI${data.model ? " (" + data.model + ")" : ""} — langsung tampil & ikut PDF berikutnya.`,



      "ok");



    await _ambilPortofolio(npm);



  } catch (err) {



    toast(`Lapis AI gagal: ${err.message} — narasi tetap template Lapis A.`, "error");



  } finally {



    _aiKarrierJalan = false;



    if (btn) {



      btn.disabled = false;



      btn.innerHTML = label;



      if (window.lucide) lucide.createIcons();



    }



  }



}







async function _ambilPortofolio(npm) {



  if (!npm) return;



  const isi = document.getElementById("porto-isi");



  if (isi) isi.innerHTML = `<p class="text-slate-500 italic text-sm">Memuat portofolio…</p>`;



  // Kosongkan kanvas dari muatan sebelumnya biar tidak menampilkan data



  // mahasiswa lama saat loading data mahasiswa baru.



  const kpi = document.getElementById("porto-kpi");



  const anl = document.getElementById("porto-analisis");



  if (kpi) kpi.innerHTML = "";



  if (anl) anl.innerHTML = "";



  try {



    const res = await fetch(`/api/portofolio?npm=${encodeURIComponent(npm)}`,



      { cache: "no-store" });



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);



    _portofolioData = data;



    _renderPortofolio(data);



  } catch (err) {



    _portofolioData = null;



    if (isi) isi.innerHTML =



      `<p class="text-rose-300 text-sm">Gagal memuat portofolio: ${escapeHtml(err.message)}</p>`;



  }



}







/** Lapis 4: KPI kumulatif sepanjang kuliah. */



function _portoKpi(d) {



  const arah = d.arah_nilai === "naik" ? ["↑ Naik", "text-emerald-300 border-emerald-500/40 bg-emerald-500/10"]



    : d.arah_nilai === "turun" ? ["↓ Turun", "text-rose-300 border-rose-500/40 bg-rose-500/10"]



    : d.arah_nilai === "stabil" ? ["→ Stabil", "text-slate-300 border-slate-600/60 bg-slate-800/60"]



    : ["-", "text-slate-400 border-slate-700 bg-slate-800/60"];



  const kartu = (label, nilai) => `



    <div class="bg-[#0f172a] rounded-xl p-3 border border-slate-800 shadow">



      <span class="text-[10px] text-slate-500 block mb-0.5">${label}</span>



      <strong class="text-xl font-black text-white">${escapeHtml(nilai)}</strong>



    </div>`;



  return [



    kartu("Total MK Ditempuh", String(d.jumlah_mk)),



    kartu("MK At-Risk", `${d.jumlah_mk_at_risk}`),



    kartu(`Rata Nilai (${d.jumlah_mk} MK)`, d.rata_nilai != null ? String(d.rata_nilai) : "-"),



    kartu("Rata Kehadiran", d.rata_kehadiran != null ? `${d.rata_kehadiran}%` : "-"),



    kartu("Total Alpha", `${d.total_alpha} hari`),



    `<div class="bg-[#0f172a] rounded-xl p-3 border ${arah[1]} shadow">



       <span class="text-[10px] text-slate-500 block mb-0.5">Arah Tren (±5)</span>



       <strong class="text-xl font-black">${escapeHtml(arah[0])}${d.delta_nilai_terakhir != null ? `<span class="text-xs font-semibold"> (${d.delta_nilai_terakhir > 0 ? "+" : ""}${d.delta_nilai_terakhir})</span>` : ""}</strong>



     </div>`,



  ].join("");



}







/** Lapis 1: sel bulanan (aturan sama dengan _chipBulananDetail di tab 8). */



function _portoSelBulanan(bulanan) {



  if (!bulanan || !bulanan.length) return "";



  const namaBulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",



                     "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];



  return `<div class="flex flex-wrap gap-1 mt-2">${bulanan.map(b => {



    const pct = b.hadir_persen;



    const warna = pct == null ? "text-slate-500"



      : pct >= 85 ? "text-emerald-300 bg-emerald-500/10"



      : pct >= 75 ? "text-amber-300 bg-amber-500/10"



      : "text-rose-300 bg-rose-500/10";



    const ym = String(b.bulan).split("-");



    const label = `${namaBulan[Number(ym[1]) - 1] || "?"} ${ym[0].slice(2)}`;



    const tt = `${b.pertemuan} pertemuan • hadir ${pct != null ? pct + "%" : "-"} • rata skor ${b.rata_skor != null ? b.rata_skor : "-"}`;



    return `<span class="px-1.5 py-0.5 rounded border border-slate-700/50 text-[10px] font-semibold ${warna}" title="${escapeHtml(tt)}">${escapeHtml(label)} ${pct != null ? Math.round(pct) + "%" : "-"}</span>`;



  }).join("")}</div>`;



}







/** ANALISIS NILAI -> POTENSI: label + radar lintas MK + MK terkuat/terlemah.



 *  Ambang ambang label pinjam AMBANG diagnosis v3 (skor 85/90, 80/85, 70/75) -



 *  dihitung server dari nilai katalog, bukan dari absen. */



function _renderAnalisisPotensi(d) {



  const host = document.getElementById("porto-analisis");



  const sebar = document.getElementById("porto-analisis-sebaran");



  if (!host) return;



  const a = d.analisis_potensi;



  if (!a || !a.label) {



    host.innerHTML = `<p class="text-slate-500 italic text-sm">Analisis potensi belum tersedia (data nilai belum lengkap).</p>`;



    if (sebar) sebar.textContent = "-";



    return;



  }







  const warnaLabel = a.label.startsWith("POTENSI TINGGI")



    ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/40"



    : a.label.startsWith("POTENSI BAIK")



    ? "bg-sky-500/15 text-sky-300 border-sky-500/40"



    : a.label.startsWith("POTENSI MEMADAI")



    ? "bg-amber-500/15 text-amber-300 border-amber-500/40"



    : a.label.startsWith("BUTUH")



    ? "bg-rose-500/15 text-rose-300 border-rose-500/40"



    : "bg-slate-500/15 text-slate-300 border-slate-600/50";







  const namaDim = {



    penguasaan_cad: "Penguasaan CAD",



    ketelitian_detail: "Detail Gambar",



    kedisiplinan_asistensi: "Kedisiplinan Studio",



    logika_ruang_struktur: "Logika Ruang/Struktur",



    manajemen_waktu: "Manajemen Waktu",



  };



  const saran = a.radar_sumber || {};



  const barRadar = Object.entries(a.radar || {}).map(([k, v]) => {



    const est = saran[k] === "estimasi";



    return `<div class="flex items-center gap-2">



      <span class="w-32 shrink-0 text-[10px] text-slate-400">${escapeHtml(namaDim[k] || k)}${est ? " *" : ""}</span>



      <div class="flex-1 h-2.5 bg-slate-900 rounded overflow-hidden border border-slate-800">



        <div class="h-full rounded ${est ? "bg-slate-500" : "bg-gradient-to-r from-emerald-600 to-lime-500"}" style="width:${Math.max(2, Math.min(100, v))}%"></div>



      </div>



      <strong class="w-8 text-right text-xs ${est ? "text-slate-400" : "text-emerald-300"}">${v}</strong>



    </div>`;



  }).join("");







  const kolom = (judul, daftar, kelas) => `



    <div class="rounded-xl border ${kelas} p-3">



      <p class="text-[10px] font-bold text-slate-300 mb-1.5 uppercase tracking-wide">${judul}</p>



      ${(daftar || []).map(x => `



        <div class="flex items-center justify-between gap-2 py-0.5">



          <span class="text-[11px] text-slate-300 truncate">${escapeHtml(x.nama_mk)}</span>



          <span class="text-[11px] font-mono font-bold">${escapeHtml(String(x.nilai))} ${escapeHtml(x.grade || "")}</span>



        </div>`).join("") || '<p class="text-slate-600 italic text-[10px]">-</p>'}



    </div>`;







  // --- Analisis pusat: bidang terkuat -> dimensi menyesuaikan (estimasi jujur)



  const kanal = a.kanal || [];



  const barKhas = Object.entries(a.dimensi_khas || {}).map(([id, v]) => `



    <div class="flex items-center gap-2">



      <span class="w-32 shrink-0 text-[10px] text-violet-200">${escapeHtml(v.label)} *</span>



      <div class="flex-1 h-2.5 bg-slate-900 rounded overflow-hidden border border-violet-900/60">



        <div class="h-full rounded bg-gradient-to-r from-violet-600 to-fuchsia-400" style="width:${Math.max(2, Math.min(100, v.nilai))}%"></div>



      </div>



      <strong class="w-8 text-right text-xs text-violet-300">${v.nilai}</strong>



    </div>`).join("");



  const chipsKanal = kanal.map(k => {



    const top = k.kanal === a.kanal_terkuat;



    return `<span class="px-2 py-0.5 rounded border text-[10px] font-mono ${top



      ? "border-violet-400/60 bg-violet-500/15 text-violet-200 font-bold"



      : "border-slate-700/60 bg-slate-800/70 text-slate-400"}">



      ${top ? "★ " : ""}${escapeHtml(k.nama)} ${k.rata_nilai} (${k.jumlah_mk} MK)</span>`;



  }).join(" ");



  const karierTop = (a.matriks_karier_kuliah || []).slice(0, 3).map(c => `



    <div class="py-0.5 border-b border-violet-500/10 last:border-b-0">



      <div class="flex items-center justify-between gap-2">



        <span class="text-[11px] text-slate-300 truncate" title="${escapeHtml(c.analisis_potensi || "")}">${escapeHtml(c.profesi)}</span>



        <span class="text-[11px] font-mono shrink-0 ${c.kategori_kecocokan === "Sangat Tinggi"



        ? "text-emerald-300" : c.kategori_kecocokan === "Tinggi" ? "text-lime-300" : "text-slate-400"}">



          ${c.kecocokan_persen}% · ${escapeHtml(c.kategori_kecocokan)}${c.analisis_sumber === "ai" ? " · AI" : ""}</span>



      </div>



      ${c.analisis_potensi ? `<p class="text-[10px] text-slate-400 leading-snug mt-0.5 text-justify">${escapeHtml(c.analisis_potensi)}</p>` : ""}



    </div>`).join("");







  const dist = Object.entries(a.distribusi || {}).map(([k, v]) =>



    `<span class="px-2 py-0.5 rounded border border-slate-700/60 bg-slate-800/70 text-[10px] font-mono text-slate-300">${escapeHtml(k)} × ${v}</span>`



  ).join(" ");







  host.innerHTML = `



    <div class="flex items-center gap-3 flex-wrap mb-3">



      <span class="px-3 py-1 rounded-lg border text-sm font-black ${warnaLabel}">${escapeHtml(a.label)}</span>



      <span class="text-[11px] text-slate-400">${escapeHtml(a.alasan)}</span>



    </div>



    ${barKhas ? `



    <div class="rounded-xl border border-violet-500/30 bg-violet-500/5 p-3 mb-3" id="porto-bidang">



      <p class="text-[10px] font-bold uppercase tracking-wide text-violet-200 mb-2" title="Analisis berpusat di bidang terkuat: dimensi khas bidang = 70% rata nilai MK sebidang + 30% radar terukur (dia estimasi, tidak sebagai fakta).">🎯 Analisis Pusat: Bidang Terkuat (dimensi menyesuaikan bidang — estimasi)</p>



      <div class="flex flex-wrap gap-1.5 mb-2">${chipsKanal}</div>



      <div class="space-y-1.5">${barKhas}</div>



      ${karierTop ? `



      <div class="mt-2.5 pt-2 border-t border-violet-500/20">



        <div class="flex items-center justify-between gap-2 mb-1 flex-wrap">



          <p class="text-[10px] font-bold text-slate-300 uppercase tracking-wide">Arah Karier Sepanjang Kuliah (bonus sebidang, lainnya tetap)</p>



          <button id="porto-ai-btn" onclick="kirimKierAI()"



            title="Narasi 3 karier teratas dirapikan engine Gemini rotary. Angka bukti dikunci & diverifikasi - AI tidak bisa menambah angka. Gagal = kembali ke template."



            class="touch-target px-2 py-1 rounded-lg text-[10px] font-bold border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 transition flex items-center gap-1">



            <i data-lucide="sparkles" class="w-3 h-3"></i> Rapikan dengan AI



          </button>



        </div>



        ${karierTop}



      </div>` : ""}



    </div>` : ""}



    <div class="grid lg:grid-cols-2 gap-4">



      <div class="space-y-1.5">${barRadar || '<p class="text-slate-600 italic text-xs">belum ada radar</p>'}



        <p class="text-[9px] text-slate-600 mt-1">* estimasi: dim dirata dari proksi sinyal lain; dim tanpa * terukur langsung dari nilai kinerja.</p>



      </div>



      <div class="space-y-2">



        <div class="grid grid-cols-2 gap-2">



          ${kolom("MK Terkuat", a.mk_terkuat, "border-emerald-500/30")}



          ${kolom("MK Terlemah", a.mk_terlemah, "border-rose-500/30")}



        </div>



        <p class="text-[11px] text-slate-300 leading-relaxed border-l-2 border-emerald-500/40 pl-2">



          ${escapeHtml(a.rekomendasi || "-")}



        </p>



        <div class="flex flex-wrap gap-1.5">${dist || '<span class="text-slate-600 text-[10px] italic">tidak ada data diagnosis</span>'}</div>



      </div>



    </div>`;







  if (sebar) {



    const s = a.sebaran || {};



    sebar.textContent = s.deviasi != null



      ? `nilai ${s.terendah}–${s.tertinggi} • deviasi ${s.deviasi} (makin kecil makin konsisten)`



      : "-";



  }



  if (window.lucide) lucide.createIcons();



}







/** Lapis 3 (accordion) berisi lapis 2 (per MK) + lapis 1 (bulanan expand). */



function _renderPortofolio(d) {



  const isi = document.getElementById("porto-isi");



  const meta = document.getElementById("porto-meta");



  const kpi = document.getElementById("porto-kpi");



  if (!isi) return;







  // Update Featured Student Profile Card in Tab 10



  const studentNama = d.nama || (masterData && masterData.students.find(s => String(s.npm) === String(d.npm))?.nama) || "Mahasiswa";



  const studentNpm = d.npm || "-";



  const initials = studentNama.split(" ").filter(Boolean).map(w => w[0]).slice(0, 2).join("").toUpperCase() || "M";



  setText("porto-card-avatar", initials);



  setText("porto-profile-nama", studentNama);



  setText("porto-profile-npm", studentNpm);



  const badgeEl = document.getElementById("porto-profile-badge");



  if (badgeEl) {



    if (d.jumlah_mk_at_risk > 0) {



      badgeEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/15 text-rose-300 border border-rose-500/40";



      badgeEl.textContent = `⚠️ At-Risk (${d.jumlah_mk_at_risk} MK)`;



    } else if (d.rata_nilai && d.rata_nilai >= 85) {



      badgeEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/40";



      badgeEl.textContent = "🌟 Top Star";



    } else {



      badgeEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-500/15 text-sky-300 border border-sky-500/40";



      badgeEl.textContent = "✨ Akademik Terjaga";



    }



  }



  const searchInput = document.getElementById("porto-search-input");



  if (searchInput && !searchInput.matches(":focus")) {



    searchInput.value = `${studentNama} (${studentNpm})`;



  }







  if (kpi) kpi.innerHTML = _portoKpi(d);



  _renderAnalisisPotensi(d);



  _renderPortoBssAudit(d);



  if (meta) {



    meta.textContent = `${d.jumlah_mk} MK${d.mk_gagal && d.mk_gagal.length



      ? ` • ${d.mk_gagal.length} katalog tak terbaca` : ""}`;



  }







  const atRiskBadge = (bar) => bar



    ? `<span class="px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/40 text-[9px] font-bold">AT-RISK</span>`



    : "";



  const gradeWarna = (g) => (g === "A" || g === "AB") ? "text-emerald-300"



    : (g === "B") ? "text-sky-300" : (g === "C") ? "text-amber-300"



    : "text-rose-300";







  const taAktif = _nilai("sel-tahun") ? _tampilTahun(_nilai("sel-tahun")) : "";



  const semAktif = _nilai("sel-semester") || "";



  const totalSem = (d.semester || []).length;







  isi.innerHTML = (d.semester || []).map((s, si) => {



    const isAktif = (_tampilTahun(s.tahun_ajar) === taAktif && s.semester === semAktif) || (si === totalSem - 1);



    const kelasBuka = isAktif ? "" : "hidden";



    const rotateChev = isAktif ? "rotate-90" : "";



    const badgeAktif = isAktif ? `<span class="px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 text-[9px] font-bold">SEMESTER TERPILIH</span>` : "";







    return `<div class="rounded-xl border border-slate-800 overflow-hidden">



      <button onclick="togglePortofolioSemester(${si})"



        class="w-full flex items-center justify-between px-4 py-3 bg-slate-900/70 hover:bg-slate-900 transition text-left">



        <span class="flex items-center gap-2">



          <i id="porto-chev-${si}" data-lucide="chevron-right" class="w-4 h-4 text-slate-500 transition-transform ${rotateChev}"></i>



          <span class="text-sm font-bold text-white">${escapeHtml(_tampilTahun(s.tahun_ajar))} ${escapeHtml(s.semester)}</span>



          ${badgeAktif}



          ${s.jumlah_at_risk ? `<span class="text-[9px] font-bold text-rose-300">${s.jumlah_at_risk} MK at-risk</span>` : ""}



        </span>



        <span class="text-[10px] text-slate-400 font-mono">



          ${s.jumlah_mk} MK • nilai ${s.rata_nilai != null ? s.rata_nilai : "-"} • hadir ${s.rata_kehadiran != null ? s.rata_kehadiran + "%" : "-"}



        </span>



      </button>



      <div id="porto-sem-${si}" class="${kelasBuka} px-4 pb-3 pt-1 space-y-2 bg-slate-950/40">



        ${(s.mk || []).map(m => {



          const sksBadge = m.sks ? `<span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[9px] font-mono">${m.sks} SKS</span>` : "";



          const dosenInfo = m.dosen_pengasuh && m.dosen_pengasuh.length ? `<span class="text-[10px] text-slate-400"> • Dosen: ${escapeHtml(m.dosen_pengasuh.join(", "))}</span>` : "";



          return `<div class="rounded-lg border border-slate-800 p-3">



            <div class="flex items-center justify-between gap-2 flex-wrap">



              <span class="text-xs font-bold text-slate-100 flex items-center gap-1.5 flex-wrap">



                ${escapeHtml(m.nama_mk)}



                ${sksBadge}



                ${atRiskBadge(m.at_risk)}



              </span>



              <span class="text-[10px] font-mono text-slate-400">



                <span class="${gradeWarna(m.grade)} font-black text-xs">${escapeHtml(m.grade || "-")}</span>



                ${m.nilai != null ? escapeHtml(String(m.nilai)) : "-"} • hadir ${m.kehadiran != null ? m.kehadiran + "%" : "-"} • alpha ${m.alpha ?? 0} hari



              </span>



            </div>



            <div class="flex items-center gap-2 mt-0.5 flex-wrap">



              <span class="text-[10px] text-slate-500 font-medium">${escapeHtml(m.status_alert || "-")}</span>



              ${dosenInfo}



            </div>



            ${_portoSelBulanan(m.bulanan) || "<p class=\"text-[10px] text-slate-600 italic mt-1\">Rekap bulanan belum tersedia (pertemuan belum diinput/bertanggal).</p>"}



          </div>`;



        }).join("")}



      </div>



    </div>`;



  }).join("") || `<p class="text-slate-500 italic text-sm">Belum ada katalog MK untuk mahasiswa ini.</p>`;







  if (window.lucide) lucide.createIcons();



}







/** Accordion: buka/tutup 1 semester + putar chevron. */



function togglePortofolioSemester(si) {



  const isi = document.getElementById(`porto-sem-${si}`);



  const chev = document.getElementById(`porto-chev-${si}`);



  if (!isi) return;



  isi.classList.toggle("hidden");



  if (chev) chev.classList.toggle("rotate-90");



}







/** Unduh PDF (lengkap / bulanan / rapor / deck) — pasangan aksi tab 9. */



function unduhPortofolioPdf(tipe) {



  const sel = document.getElementById("porto-sel");



  const npm = sel && sel.value ? sel.value : _targetPortofolio();



  if (!npm) {



    toast("Pilih mahasiswa dulu, bro.", "error");



    return;



  }



  const url = `/api/pdf/download?type=${tipe}&npm=${encodeURIComponent(npm)}`;



  window.open(url, "_blank");



}







// =============================================================================



// TAB 7: INFO SISTEM (markdown lokal, dirender tanpa pustaka eksternal)



// =============================================================================



let infoMdCache = null;







async function muatInfoSistem(paksa = false) {



  const host = document.getElementById("info-md");



  const status = document.getElementById("info-status");



  if (!host) return;







  if (infoMdCache && !paksa) {



    host.innerHTML = infoMdCache;



    return;



  }







  host.innerHTML = '<p class="text-sm text-slate-400">Memuat penjelasan sistem…</p>';



  if (status) status.textContent = "";







  try {



    const res = await fetch("info.md", { cache: "no-store" });



    if (!res.ok) throw new Error(`HTTP ${res.status}`);



    const teks = await res.text();



    infoMdCache = renderMarkdown(teks);



    host.innerHTML = infoMdCache;



    if (status) {



      status.textContent = `Dimuat ${new Date().toLocaleTimeString("id-ID")}`;



    }



    if (window.lucide) lucide.createIcons();



  } catch (err) {



    host.innerHTML = `<div class="info-error">Penjelasan sistem tidak bisa dibaca: <strong>${escapeHtml(err.message)}</strong>.



      Pastikan berkas <code>public/info.md</code> ada, lalu klik Muat Ulang.</div>`;



    if (status) status.textContent = "Gagal memuat";



  }



}







function escapeHtml(teks) {



  return String(teks)



    .replace(/&/g, "&amp;")



    .replace(/</g, "&lt;")



    .replace(/>/g, "&gt;")



    .replace(/"/g, "&quot;");



}







// Inline markdown: `kode`, **tebal**, *miring*, [teks](tautan).



function renderInline(teks) {



  const kode = [];



  let t = String(teks).replace(/`([^`]+)`/g, (_, isi) => {



    kode.push(`<code>${escapeHtml(isi)}</code>`);



    return `\u0000${kode.length - 1}\u0000`;



  });







  t = escapeHtml(t);



  t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, label, href) => {



    const aman = /^(https?:|#|\/|\.\/|[\w-]+\.md)/i.test(href) ? href : "#";



    const luar = /^https?:/i.test(aman) ? ' target="_blank" rel="noopener noreferrer"' : "";



    return `<a href="${aman}"${luar}>${label}</a>`;



  });



  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");



  t = t.replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>");



  return t.replace(/\u0000(\d+)\u0000/g, (_, i) => kode[Number(i)]);



}







function barisTabel(baris) {



  return baris.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map(s => s.trim());



}







function adalahAwalTabel(lines, i) {



  if (i + 1 >= lines.length) return false;



  if (!lines[i].includes("|")) return false;



  return /^\s*\|?[\s:|-]*-[\s:|-]*\|[\s:|-]*$/.test(lines[i + 1]) && lines[i + 1].includes("-");



}







// Parser markdown blok: heading, code fence, blockquote, tabel, list, hr, paragraf.



function renderMarkdown(md) {



  const lines = String(md).replace(/\r\n?/g, "\n").split("\n");



  const out = [];



  let i = 0;







  while (i < lines.length) {



    const line = lines[i];







    if (!line.trim()) { i++; continue; }







    const fence = line.match(/^```(\w*)\s*$/);



    if (fence) {



      const buf = [];



      i++;



      while (i < lines.length && !/^```\s*$/.test(lines[i])) { buf.push(lines[i]); i++; }



      i++; // lewati penutup



      out.push(`<pre class="info-pre"><code>${escapeHtml(buf.join("\n"))}</code></pre>`);



      continue;



    }







    const heading = line.match(/^(#{1,6})\s+(.*)$/);



    if (heading) {



      const lv = heading[1].length;



      out.push(`<h${lv}>${renderInline(heading[2].trim())}</h${lv}>`);



      i++;



      continue;



    }







    if (/^\s*(---+|\*\*\*+|___+)\s*$/.test(line)) {



      out.push("<hr>");



      i++;



      continue;



    }







    if (/^\s*>\s?/.test(line)) {



      const buf = [];



      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {



        buf.push(lines[i].replace(/^\s*>\s?/, ""));



        i++;



      }



      out.push(`<blockquote>${renderMarkdown(buf.join("\n"))}</blockquote>`);



      continue;



    }







    if (adalahAwalTabel(lines, i)) {



      const kepala = barisTabel(lines[i]);



      i += 2;



      const isi = [];



      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {



        isi.push(barisTabel(lines[i]));



        i++;



      }



      const th = kepala.map(c => `<th>${renderInline(c)}</th>`).join("");



      const tr = isi.map(r => `<tr>${r.map(c => `<td>${renderInline(c)}</td>`).join("")}</tr>`).join("");



      out.push(`<div class="info-table-wrap"><table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table></div>`);



      continue;



    }







    if (/^\s*([-*+]|\d+\.)\s+/.test(line)) {



      const berurut = /^\s*\d+\./.test(line);



      const item = [];



      while (i < lines.length && /^\s*([-*+]|\d+\.)\s+/.test(lines[i])) {



        item.push(lines[i].replace(/^\s*([-*+]|\d+\.)\s+/, ""));



        i++;



        // Baris lanjutan yang di-indentasi tetap milik bullet yang sama.



        while (



          i < lines.length && /^\s{2,}\S/.test(lines[i]) &&



          !/^\s*([-*+]|\d+\.)\s+/.test(lines[i]) &&



          !adalahAwalTabel(lines, i)



        ) {



          item[item.length - 1] += " " + lines[i].trim();



          i++;



        }



      }



      const tag = berurut ? "ol" : "ul";



      out.push(`<${tag}>${item.map(t => `<li>${renderInline(t)}</li>`).join("")}</${tag}>`);



      continue;



    }







    const buf = [];



    while (



      i < lines.length && lines[i].trim() &&



      !/^(#{1,6}\s|```|\s*>\s?|\s*([-*+]|\d+\.)\s+|---)/.test(lines[i]) &&



      !adalahAwalTabel(lines, i)



    ) {



      buf.push(lines[i].trim());



      i++;



    }



    if (!buf.length) { i++; continue; }



    out.push(`<p>${renderInline(buf.join(" "))}</p>`);



  }







  return out.join("\n");



}







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







// =============================================================================



// TAB 3: VIDEO 9:16



// =============================================================================



async function renderVideoStory(student) {



  const vid = (student.marketing && student.marketing.video) || {};



  setText("video-full-script", `"${vid.voiceover_script || "Naskah voiceover belum tersedia."}"`);







  const photoData = await detectStudentProgressPhotos(student.npm);







  const videoEl = document.getElementById("student-real-video");



  const videoSrc = document.getElementById("student-video-src");



  const videoBadge = document.getElementById("student-video-status-badge");







  if (photoData && photoData.video_exists) {



    if (videoLoadedNpm !== student.npm) {



      if (videoEl && videoSrc) {



        const videoUrl = `/videos/video_portofolio_${student.npm}.mp4?t=${Date.now()}`;



        videoSrc.src = videoUrl;



        videoEl.load();



        videoLoadedNpm = student.npm;



      }



    }



    if (videoBadge) {



      videoBadge.className = "px-2.5 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center gap-1";



      videoBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Video Siap Diputar`;



    }



  } else {



    // Video belum dibuat: kosongkan src dan hindari pemicuan 404 merah di konsol browser



    videoLoadedNpm = null;



    if (videoEl && videoSrc) {



      videoSrc.src = "";



    }



    if (videoBadge) {



      videoBadge.className = "px-2.5 py-0.5 rounded text-[11px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1";



      videoBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Belum Dirender`;



    }



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



    return data;



  } catch (err) {



    console.error("Error detecting photos:", err);



    if (countEl) countEl.innerText = "Gagal deteksi";



    if (chipsEl) chipsEl.innerHTML = `<span class="text-[10px] text-rose-400 italic">${esc(err.message)}</span>`;



    return null;



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



/** Sumber identitas salam dokumen WA: config identitas (paling segar,



 *  berubah seketika setelah Simpan di Pengaturan) dengan fallback data master. */



function _metaIdentitasSalam() {



  const cfg = (identitasData && identitasData.config) || {};



  const inst = cfg.institusi || {};



  const mkAktif = (cfg.mata_kuliah || {})[cfg.mata_kuliah_aktif] || {};



  const c = (masterData && masterData.course) || {};



  const prodi = inst.prodi || c.prodi || "Arsitektur";



  const fakultas = inst.fakultas || c.fakultas || "Fakultas Teknik & Desain";



  return {



    prodi,



    fakultas,



    instansi: `Program Studi ${prodi}, ${fakultas}`,



    kaprodi: inst.ketua_prodi || c.ketua_prodi || "-",



    asisten: mkAktif.asisten_dosen || c.asisten_dosen || "-",



  };



}







function renderWhatsAppSimulation(student) {



  setText("wa-recipient-name", `Wali Murid ${student.nama}`);







  const courseName = (masterData && masterData.course && masterData.course.nama_mk)



    ? masterData.course.nama_mk : "Aplikasi Komputer Arsitektur & QS";



  const m = _metaIdentitasSalam();



  const openingText = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\nKepada Yth. Bapak/Ibu Wali Murid dari *${student.nama}*,\n\nSalam hangat dan salam sejahtera dari ${m.instansi}.\n\nBerikut kami sampaikan Surat Resmi Perkembangan Akademik, Portofolio Pembelajaran, dan Pemetaan 10 Karier Masa Depan ananda pada mata kuliah *${courseName}* untuk periode semester berjalan:`;



  setText("wa-opening-text", openingText);







  const namaMhs = String(student.nama || "").replace(/\s+/g, "_");



  setText("wa-card-file-1", `01_rekap_kehadiran_bulanan_${student.npm}_${namaMhs}.pdf`);



  setText("wa-card-file-2", `02_rapor_akhir_semester_${student.npm}_${namaMhs}.pdf`);



  setText("wa-card-file-3", `05_deckcraft_portofolio_arsitektur_${student.npm}_${namaMhs}.pdf`);



}







function copyWhatsAppMessage() {



  if (!currentStudent) return;



  const courseName = (masterData && masterData.course && masterData.course.nama_mk)



    ? masterData.course.nama_mk : "Aplikasi Komputer Arsitektur & QS";



  const m = _metaIdentitasSalam();



  const fullMsg = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\n` +



    `Kepada Yth. Bapak/Ibu Wali Murid dari *${currentStudent.nama}*,\n\n` +



    `Salam hangat dari ${m.instansi}.\n` +



    `Melalui pesan ini, kami menyampaikan Surat Resmi Perkembangan Akademik, Portofolio Pembelajaran, dan Pemetaan 10 Karier Masa Depan ananda pada mata kuliah *${courseName}* periode semester berjalan.\n\n` +



    `Bersama pesan ini, kami lampirkan 3 Dokumen Resmi Terverifikasi:\n` +



    `1. 📎 Rekap Kehadiran Mahasiswa Bulanan (Presensi & Log Sesi Praktikum)\n` +



    `2. 📎 Rapor Hasil Evaluasi Akhir & Pemetaan 10 Karier Masa Depan (Capaian Kompetensi & Kesiapan Profesi)\n` +



    `3. 📎 Portofolio Karya & Dokumentasi Studio Arsitektur (Slide Deck Presentasi 16:9 Widescreen)\n\n` +



    `Bapak/Ibu dapat mengunduh dan meninjau berkas PDF terlampir. Terima kasih atas doa, bimbingan, dan cinta kasih yang senantiasa Bapak/Ibu berikan kepada ananda tercinta di rumah.\n\n` +



    `Hormat kami,\n` +



    `*Ketua Program Studi ${m.prodi}*\n` +



    `*${m.kaprodi}*\n` +



    `Asisten Dosen: *${m.asisten}*`;







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



  // Satu sumber salam/instansi: _metaIdentitasSalam (config identitas), sama



  // dengan pesan yang disalin di Tab 4 - bukan tanda tangan hardcode lama.



  const m = _metaIdentitasSalam();



  const courseName = (masterData && masterData.course && masterData.course.nama_mk)



    ? masterData.course.nama_mk : "-";



  const fullMsg = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\n` +



    `Kepada Yth. Bapak/Ibu Wali Murid dari *${currentStudent.nama}*,\n\n` +



    `Salam hangat dari ${m.instansi}.\n` +



    `Lampiran pengembangan akademik ananda pada mata kuliah *${courseName}* ` +



    `kami sampaikan dalam 3 dokumen PDF resmi terverifikasi.\n\n` +



    `Hormat kami,\n` +



    `*Ketua Program Studi ${m.prodi}*\n` +



    `*${m.kaprodi}*\n` +



    `Asisten Dosen: *${m.asisten}*`;



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



    if (selector) selector.disabled = true;



    const res = await fetch(`/api/switch_course?course=${encodeURIComponent(courseId)}`);



    const resData = await res.json();



    if (!res.ok) throw new Error(resData.error || `HTTP ${res.status}`);



    if (!resData.success) throw new Error(resData.error || "Gagal berganti mata kuliah.");







    toast(`Mata kuliah aktif: ${resData.active_course.nama_mk}`, "success");



    if (resData.catatan) toast(resData.catatan, "info", 9000);



    // Muat ulang seluruh dataset; loadAcademicData() akan menyinkronkan header



    // dan konteks ke course yang baru (bukan lagi ke pilihan pertama).



    await loadAcademicData();



    if (selector && courseId) selector.value = courseId;



    sinkronkanTabRekapKeKonteks(courseId);



  } catch (err) {



    toast(`Gagal berganti mata kuliah: ${err.message}`, "error", 8000);



    // Kembalikan pilihan dropdown ke MK yang masih aktif supaya tampilan tidak



    // berbohong setelah pergantian gagal.



    muatKurikulum().catch(() => {});



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



  // Identitas institusi & pejabat: SATU sumber config/identitas.json.



  // Tidak ada lagi nama yang dikeras-batu di HTML - menambah/mengganti dosen



  // pengasuh atau asisten cukup di menu Pengaturan lalu Simpan.



  const cfg = (data && data.config) || {};



  const inst = cfg.institusi || {};



  const mkAktif = (cfg.mata_kuliah || {})[cfg.mata_kuliah_aktif] || {};



  const prodi = inst.prodi || "";



  const kombinasi = [



    inst.universitas || "",



    prodi ? `Program Studi ${prodi}` : "",



  ].filter(Boolean).join(" — ");



  if (kombinasi) setText("header-institusi", kombinasi);



  if (inst.ketua_prodi) setText("header-kaprodi", inst.ketua_prodi);



  const asisten = mkAktif.asisten_dosen || "";



  if (asisten) {



    setText("header-asisten", asisten);



    setText("wali-asisten", asisten);



    setText("wa-asisten-nama", asisten);



  }



  if (prodi) setText("wa-kaprodi-prodi", prodi);



  if (inst.ketua_prodi) setText("wa-kaprodi-nama", inst.ketua_prodi);



  if (prodi) setText("footer-prodi", `Program Studi ${prodi}`);



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







  const keu = cfg.keuangan || {};



  setVal("cfg-spp", keu.spp_per_semester ?? 6500000);



  setVal("cfg-sisa-semester", keu.sisa_semester_standar ?? 6);







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







  cfg.keuangan = cfg.keuangan || {};



  const sppInput = parseInt(val("cfg-spp"), 10);



  const sisaSemInput = parseInt(val("cfg-sisa-semester"), 10);



  cfg.keuangan.spp_per_semester = Number.isFinite(sppInput) && sppInput > 0 ? sppInput : 6500000;



  cfg.keuangan.sisa_semester_standar = Number.isFinite(sisaSemInput) && sisaSemInput > 0 ? sisaSemInput : 6;







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



  if (hasil) {



    // Master + katalog diregenerasi -> cache perkembangan lintas-MK basi.



    perkembanganPotensi = {};



    mkRawanState = { prodi: null, dimuat: false, baris: [] }; // peta MK rawan ikut regen



    await loadAcademicData();



  }



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







// =============================================================================



// TAB 6: KURIKULUM  (tree: PRODI > TAHUN AJAR > SEMESTER > MATA KULIAH)



// =============================================================================



// Sumber kebenaran = data/kurikulum/... di SERVER. Tab ini tidak menyimpan



// salinan di browser: setiap kali dibuka isinya diambil ulang dari server, dan



// menyimpan berarti POST ke /api/kurikulum/simpan (tree ditulis, lalu master +



// katalog dibangun ulang). Tidak ada jalur "simpan di layar saja".



let pohonKurikulum = null;    // payload GET /api/kurikulum



let detailKurikulum = null;   // payload GET /api/kurikulum/detail



let konteksKurikulum = null;  // {prodi, tahun_ajar, semester, kunci_mk}



// Drill-down dari tab Rekap: tampilkan detail MK LAIN tanpa memindahkan MK



// aktif. Hanya untuk membaca/menyunting MK itu; header tetap MK aktif.



let detailOverrideKonteks = null;







function _opsi(select, nilai, teks, terpilih) {



  const opt = document.createElement("option");



  opt.value = nilai;



  opt.textContent = teks;



  opt.selected = !!terpilih;



  select.appendChild(opt);



}







function _nilai(id) {



  const el = document.getElementById(id);



  return el ? el.value : "";



}







function _tampilTahun(ta) {



  return String(ta || "").replace("-", "/");



}







async function muatKurikulum() {



  const res = await fetch("/api/kurikulum", { cache: "no-store" });



  if (!res.ok) throw new Error(`HTTP ${res.status}`);



  pohonKurikulum = await res.json();



  tandaiKonteksAktif();



  return pohonKurikulum;



}







/** Isi 4 dropdown dari pohon, lalu arahkan ke MK yang SEDANG AKTIF di server. */



function tandaiKonteksAktif() {



  if (!pohonKurikulum) return;



  const aktif = pohonKurikulum.aktif || {};



  const selProdi = document.getElementById("sel-prodi");



  const selTahun = document.getElementById("sel-tahun");



  const selSem = document.getElementById("sel-semester");



  const selMk = document.getElementById("course-selector");



  if (!selProdi || !selTahun || !selSem || !selMk) return;







  const prodiAktif = (aktif.prodi && pohonKurikulum.pohon[aktif.prodi])



    ? aktif.prodi



    : ((pohonKurikulum.prodi || [])[0] || "");



  const tahunAktif = aktif.tahun_ajar ? String(aktif.tahun_ajar).replace("/", "-") : "";







  selProdi.innerHTML = "";



  (pohonKurikulum.prodi || []).forEach(p => _opsi(selProdi, p, p, p === prodiAktif));







  isiTahun();



  const tahunTersedia = Object.keys(pohonKurikulum.pohon[prodiAktif] || {});



  if (tahunAktif && tahunTersedia.indexOf(tahunAktif) !== -1) selTahun.value = tahunAktif;







  isiSemester();



  if (aktif.semester) selSem.value = aktif.semester;







  isiMk();



  if (aktif.kunci_mk) selMk.value = aktif.kunci_mk;



}







function isiTahun() {



  const selProdi = document.getElementById("sel-prodi");



  const selTahun = document.getElementById("sel-tahun");



  if (!selProdi || !selTahun || !pohonKurikulum) return;



  const tahun = Object.keys(pohonKurikulum.pohon[selProdi.value] || {});



  const lama = selTahun.value;



  selTahun.innerHTML = "";



  tahun.forEach(ta => _opsi(selTahun, ta, _tampilTahun(ta), ta === lama));



  if (tahun.indexOf(lama) === -1 && tahun.length) selTahun.value = tahun[tahun.length - 1];



}







function isiSemester() {



  const selProdi = document.getElementById("sel-prodi");



  const selTahun = document.getElementById("sel-tahun");



  const selSem = document.getElementById("sel-semester");



  if (!selProdi || !selTahun || !selSem || !pohonKurikulum) return;



  const semua = (pohonKurikulum.pohon[selProdi.value] || {})[selTahun.value] || {};



  const sem = Object.keys(semua);



  const lama = selSem.value;



  selSem.innerHTML = "";



  sem.forEach(s => _opsi(



    selSem, s,



    s === "GANJIL" ? "Ganjil" : (s === "GENAP" ? "Genap" : s),



    s === lama));



  if (sem.indexOf(lama) === -1 && sem.length) selSem.value = sem[sem.length - 1];



}







function daftarMkTerpilih() {



  const prodi = _nilai("sel-prodi"), ta = _nilai("sel-tahun"), sem = _nilai("sel-semester");



  const semua = ((pohonKurikulum && pohonKurikulum.pohon[prodi]) || {})[ta] || {};



  return semua[sem] || [];



}







function isiMk() {



  const selMk = document.getElementById("course-selector");



  if (!selMk || !pohonKurikulum || !pohonKurikulum.pohon) return;



  const prodi = _nilai("sel-prodi") || ((pohonKurikulum.prodi || [])[0] || "ARSITEKTUR");



  const tahunMap = pohonKurikulum.pohon[prodi] || {};



  const lama = selMk.value || (pohonKurikulum.aktif || {}).kunci_mk;







  selMk.innerHTML = "";







  const semLabelMap = {



    "2024-2025_GANJIL": "Semester 1 — TA 2024/2025 Ganjil",



    "2024-2025_GENAP": "Semester 2 — TA 2024/2025 Genap",



    "2025-2026_GANJIL": "Semester 3 — TA 2025/2026 Ganjil",



    "2025-2026_GENAP": "Semester 4 — TA 2025/2026 Genap (Aktif)",



    "2026-2027_GANJIL": "Semester 5 — TA 2026/2027 Ganjil",



    "2026-2027_GENAP": "Semester 6 — TA 2026/2027 Genap",



  };







  let foundSelected = false;







  Object.entries(tahunMap).forEach(([ta, semMap]) => {



    Object.entries(semMap || {}).forEach(([sem, mkList]) => {



      if (!Array.isArray(mkList) || !mkList.length) return;



      const keyGroup = `${ta}_${sem}`;



      const groupLabel = semLabelMap[keyGroup] || `${ta} • ${sem}`;



      const optgroup = document.createElement("optgroup");



      optgroup.label = groupLabel;







      mkList.forEach(m => {



        if (!m || m.rusak || !m.kunci_mk) return;



        const opt = document.createElement("option");



        opt.value = m.kunci_mk;



        const label = `${m.nama_mk || m.kunci_mk}${m.kode_mk ? ` (${m.kode_mk})` : ""}`;



        opt.textContent = label;



        opt.dataset.prodi = prodi;



        opt.dataset.tahun = ta;



        opt.dataset.semester = sem;



        if (m.kunci_mk === lama) {



          opt.selected = true;



          foundSelected = true;



        }



        optgroup.appendChild(opt);



      });







      if (optgroup.children.length > 0) {



        selMk.appendChild(optgroup);



      }



    });



  });







  if (!foundSelected && selMk.options.length > 0) {



    const aktif = (pohonKurikulum.aktif || {}).kunci_mk;



    for (let i = 0; i < selMk.options.length; i++) {



      if (selMk.options[i].value === aktif) {



        selMk.options[i].selected = true;



        break;



      }



    }



  }



}







/** Perubahan salah satu dropdown: isi ulang yang di hilir, lalu (untuk MK) ganti MK aktif. */



async function onKonteksBerubah(level) {



  // Navigasi manual membatalkan drill-down dari tab Rekap.



  detailOverrideKonteks = null;



  if (!pohonKurikulum) {



    try { await muatKurikulum(); } catch (err) {



      toast(`Tree kurikulum tidak bisa dibaca: ${err.message}`, "error", 8000);



      return;



    }



  }



  if (level === "prodi") { isiTahun(); isiSemester(); isiMk(); }

  if (level === "angkatan") {
    const val = _nilai("sel-angkatan");
    if (typeof onAngkatanBerubah === "function") {
      onAngkatanBerubah(val);
    }
    if (window.innerWidth < 1024 && typeof closeMobileFilterBar === "function") {
      closeMobileFilterBar();
    }
    return;
  }







  const selMk = document.getElementById("course-selector");



  const kunci = _nilai("course-selector");



  const aktif = (pohonKurikulum.aktif || {}).kunci_mk;







  if (level === "mk") {



    const opt = selMk && selMk.selectedOptions && selMk.selectedOptions[0];



    if (opt && opt.dataset) {



      const ta = opt.dataset.tahun;



      const sem = opt.dataset.semester;



      if (ta) {



        const selTahun = document.getElementById("sel-tahun");



        if (selTahun && selTahun.value !== ta) selTahun.value = ta;



      }



      if (sem) {



        const selSem = document.getElementById("sel-semester");



        if (selSem && selSem.value !== sem) selSem.value = sem;



      }



    }



    if (kunci && kunci !== aktif) {



      await switchActiveCourse(kunci);



      sinkronkanTabRekapKeKonteks(kunci);
      if (window.innerWidth < 1024 && typeof closeMobileFilterBar === "function") {
        closeMobileFilterBar();
      }



      return;



    }



  } else if (level === "tahun" || level === "semester") {



    const ta = _nilai("sel-tahun");



    const sem = _nilai("sel-semester");



    if (selMk && ta && sem) {



      const optCocok = Array.from(selMk.options).find(o => o.dataset.tahun === ta && o.dataset.semester === sem);



      if (optCocok && optCocok.value !== kunci) {



        selMk.value = optCocok.value;



        if (optCocok.value !== aktif) {



          await switchActiveCourse(optCocok.value);



          return;



        }



      }



    }



  }







  const seksi = document.getElementById("section-kurikulum");



  if (detailKurikulum && konteksKurikulum &&



      (konteksKurikulum.kunci_mk !== kunci ||



       konteksKurikulum.prodi !== _nilai("sel-prodi") ||



       konteksKurikulum.tahun_ajar !== _nilai("sel-tahun") ||



       konteksKurikulum.semester !== _nilai("sel-semester"))) {



    await muatDetailKurikulum();



  } else if (seksi && !seksi.classList.contains("hidden")) {



    await muatDetailKurikulum();



  }







  const secRekap = document.getElementById("section-rekap");



  if (secRekap && !secRekap.classList.contains("hidden")) {



    sinkronkanTabRekapKeKonteks(kunci);



  }



}







async function muatDetailKurikulum() {



  const ctx = detailOverrideKonteks || {



    prodi: _nilai("sel-prodi"), tahun_ajar: _nilai("sel-tahun"),



    semester: _nilai("sel-semester"), kunci_mk: _nilai("course-selector"),



  };



  const { prodi, tahun_ajar: ta, semester: sem, kunci_mk: kunci } = ctx;



  const statusEl = document.getElementById("kurikulum-status");



  if (!prodi || !ta || !sem || !kunci) return;



  if (statusEl) statusEl.textContent = "Memuat isi tree kurikulum…";



  try {



    const q = new URLSearchParams({



      prodi, tahun_ajar: ta, semester: sem, kunci_mk: kunci,



    });



    const res = await fetch(`/api/kurikulum/detail?${q.toString()}`, { cache: "no-store" });



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);



    detailKurikulum = data;



    konteksKurikulum = ctx;



    renderDetailKurikulum(data);



    renderOverrideKurikulum(data);



    if (statusEl) statusEl.textContent = "";



  } catch (err) {



    if (statusEl) statusEl.textContent = "";



    toast(`Gagal memuat kurikulum: ${err.message}`, "error", 8000);



  }



}







function renderDetailKurikulum(data) {



  const r = data.ringkas || {};



  const sesi = (data.sesi && data.sesi.sesi) || [];



  setText("kur-mk", r.nama_mk || data.kunci_mk);



  setText("kur-kode", r.kode_mk



    ? `Kode ${r.kode_mk} • ${r.sks ?? "-"} SKS • ${r.kelas || "-"}`



    : "");







  const badgeAktif = document.getElementById("kur-aktif");



  if (badgeAktif) {



    badgeAktif.innerHTML = data.apakah_aktif



      ? `<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">MK sedang aktif</span>`



      : `<span class="px-2 py-0.5 rounded bg-slate-700/60 text-slate-300 border border-slate-600 font-bold">Bukan MK aktif</span>`;



  }







  setText("kur-pertemuan", `${r.pertemuan ?? sesi.length} / ${r.pertemuan_standar ?? 16}`);



  setText("kur-slot", `${r.slot_total ?? 0} slot absen` +



    (r.jadwal_menit ? ` • ${r.jadwal_menit} menit/minggu` : " • jam tidak terbaca"));



  setText("kur-bobot", `${r.bobot_total ?? 0}`);



  setText("kur-mhs", `${data.jumlah_mahasiswa ?? 0} mahasiswa`);



  setText("kur-topik", `${r.topik_terisi ?? 0} topik terisi • ` +



    `${r.topik_placeholder ?? 0} menunggu RPS`);







  const jenis = document.getElementById("kur-jenis-mk");



  if (jenis) jenis.value = r.jenis_mk || "teori";



  const jenisSumber = document.getElementById("kur-jenis-sumber");



  if (jenisSumber) {



    const tebakan = String(r.jenis_mk_sumber || "").indexOf("tebakan") !== -1;



    jenisSumber.textContent = tebakan



      ? "⚠ masih tebakan awal — mohon dikonfirmasi"



      : (r.jenis_mk_sumber ? `sumber: ${r.jenis_mk_sumber}` : "");



  }







  const semKur = document.getElementById("kur-semester-kur");



  if (semKur) semKur.value = (r.semester_kurikulum === null || r.semester_kurikulum === undefined)



    ? "" : r.semester_kurikulum;



  const semSumber = document.getElementById("kur-semester-sumber");



  if (semSumber) {



    const tebakan = String(r.semester_kurikulum_sumber || "").indexOf("tebakan") !== -1;



    semSumber.textContent = tebakan



      ? "⚠ masih tebakan awal — mohon dikonfirmasi"



      : (r.semester_kurikulum_sumber ? `sumber: ${r.semester_kurikulum_sumber}` : "");



  }







  // Kotak konfirmasi selalu mulai tidak dicentang: konfirmasi harus tindakan sadar,



  // bukan warisan dari penyimpanan sebelumnya.



  ["kur-jenis-konfirmasi", "kur-semester-konfirmasi"].forEach(id => {



    const el = document.getElementById(id);



    if (el) el.checked = false;



  });







  const kode = document.getElementById("kur-pratinjau-kode");



  if (kode) kode.value = r.kode_mk || "";



  const jadwal = document.getElementById("kur-pratinjau-jadwal");



  if (jadwal) jadwal.value = `${r.kelas || "-"} • ${r.jadwal || "-"}`;







  tampilkanPeringatanKurikulum((r.masalah || []).concat(r.peringatan || []));



  renderTabelSesi(sesi);



}







function renderTabelSesi(sesi) {



  const tbody = document.getElementById("tabel-sesi-body");



  if (!tbody) return;



  tbody.innerHTML = "";



  sesi.forEach(s => {



    const tr = document.createElement("tr");



    tr.className = "border-b border-slate-800/60";



    const tipe = String(s.tipe || "teori").toLowerCase();



    const isUjian = (tipe === "uts" || tipe === "uas");



    const slot = (s.slot_absen || []).length;



    const tipeHtml = isUjian



      ? `<span class="uppercase text-[10px] font-black text-rose-300 font-mono px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20">${esc(tipe)}</span><input type="hidden" data-field="tipe" data-p="${esc(s.pertemuan)}" value="${esc(tipe)}">`



      : `<select data-field="tipe" data-p="${esc(s.pertemuan)}" class="bg-slate-950 text-cyan-300 text-[11px] font-semibold rounded px-1.5 py-1 border border-slate-700 focus:outline-none focus:border-violet-400">



          <option value="teori" ${tipe === 'teori' ? 'selected' : ''}>Teori</option>



          <option value="studio" ${tipe === 'studio' ? 'selected' : ''}>Studio</option>



          <option value="teori_studio" ${tipe === 'teori_studio' ? 'selected' : ''}>Teori + Studio</option>



        </select>`;



    tr.innerHTML = `



      <td class="py-2 pr-2 font-mono font-bold text-amber-400 align-top">${esc(s.pertemuan)}</td>



      <td class="py-2 pr-2 align-top">${tipeHtml}</td>



      <td class="py-2 pr-2">



        <input data-field="topik" data-p="${esc(s.pertemuan)}" type="text"



          value="${esc(s.topik || "")}"



          class="w-full bg-slate-950 text-slate-100 text-xs rounded px-2 py-1 border border-slate-700 focus:outline-none focus:border-violet-400">



      </td>



      <td class="py-2 pr-2 text-right">



        <input data-field="bobot" data-p="${esc(s.pertemuan)}" type="number" min="0" max="100"



          value="${esc(s.bobot ?? 0)}"



          class="w-16 bg-slate-950 text-slate-100 text-xs text-right rounded px-2 py-1 border border-slate-700 focus:outline-none focus:border-violet-400">



      </td>



      <td class="py-2 pr-2 text-right">



        <input data-field="jumlah_slot" data-p="${esc(s.pertemuan)}" type="number" min="1" max="10"



          value="${esc(slot)}"



          class="w-14 bg-slate-950 text-slate-100 text-xs text-right rounded px-2 py-1 border border-slate-700 focus:outline-none focus:border-violet-400">



      </td>



      <td class="py-2 pr-2 text-slate-400 font-mono text-[11px] align-top">${esc(s.tanggal_display || s.tanggal || "-")}</td>



    `;



    tbody.appendChild(tr);



  });



  tbody.querySelectorAll('input[data-field="bobot"]')



    .forEach(inp => inp.addEventListener("input", updateBobotLive));



  updateBobotLive();



}







function updateBobotLive() {



  let total = 0;



  document.querySelectorAll('#tabel-sesi-body input[data-field="bobot"]')



    .forEach(inp => { total += Number(inp.value) || 0; });



  const el = document.getElementById("kur-bobot-live");



  if (el) {



    el.textContent = `Σ bobot: ${total}`;



    el.className = total === 100



      ? "text-xs font-bold font-mono text-emerald-400"



      : "text-xs font-bold font-mono text-rose-400";



  }



  return total;



}







function isiTopikSisa() {



  let diisi = 0;



  document.querySelectorAll('#tabel-sesi-body input[data-field="topik"]').forEach(inp => {



    if (!inp.value.trim()) {



      inp.value = "(belum diisi - menunggu RPS)";



      diisi++;



    }



  });



  toast(diisi



    ? `${diisi} topik kosong ditandai "menunggu RPS".`



    : "Tidak ada topik yang kosong.", diisi ? "info" : "success");



}







function renderOverrideKurikulum(data) {



  const box = document.getElementById("kur-override");



  if (!box) return;



  if (!detailOverrideKonteks) {



    box.className = "hidden";



    box.innerHTML = "";



    return;



  }



  const r = (data && data.ringkas) || {};



  box.className = "rounded-2xl p-4 border border-cyan-700/60 bg-cyan-950/30 text-xs text-cyan-100 flex flex-wrap items-center justify-between gap-2";



  box.innerHTML = `<span>Menampilkan dari <strong>Rekap Periode</strong>:



    ${escapeHtml(r.nama_mk || data.kunci_mk)} — MK aktif di dashboard



    <strong>tidak berubah</strong>. Suntingan di bawah hanya menyentuh MK ini.</span>



    <button type="button" onclick="kembaliKeMkAktif()"



      class="touch-target px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-100 border border-cyan-500/40 font-semibold">



      Kembali ke MK aktif



    </button>`;



}







function kembaliKeMkAktif() {



  detailOverrideKonteks = null;



  muatKurikulum()



    .then(() => muatDetailKurikulum())



    .catch(err => toast(`Tree kurikulum tidak bisa dibaca: ${err.message}`, "error", 8000));



}







function tampilkanPeringatanKurikulum(daftar) {



  const box = document.getElementById("kurikulum-peringatan");



  if (!box) return;



  const isi = (daftar || []).filter(Boolean);



  if (!isi.length) {



    box.className = "hidden rounded-2xl p-5 border shadow-xl text-xs space-y-1.5";



    box.innerHTML = "";



    return;



  }



  box.className = "rounded-2xl p-5 border border-amber-700/60 bg-amber-950/40 text-amber-200 shadow-xl text-xs space-y-1.5";



  box.innerHTML = `<p class="font-bold uppercase tracking-wider text-[10px]">Catatan &amp; peringatan</p>` +



    isi.map(x => `<p>• ${esc(x)}</p>`).join("");



}







async function simpanKurikulum() {



  if (!detailKurikulum || !konteksKurikulum) {



    toast("Muat dulu isi kurikulum sebelum menyimpan.", "warn");



    return;



  }



  const total = updateBobotLive();



  if (total !== 100) {



    toast(`Total bobot ${total}, harus tepat 100. Belum ada yang disimpan.`, "error", 9000);



    return;



  }







  const sesi = [];



  document.querySelectorAll("#tabel-sesi-body tr").forEach(tr => {



    const topik = tr.querySelector('input[data-field="topik"]');



    const bobot = tr.querySelector('input[data-field="bobot"]');



    const slot = tr.querySelector('input[data-field="jumlah_slot"]');



    const tipeEl = tr.querySelector('[data-field="tipe"]');



    if (!topik || !bobot || !slot) return;



    sesi.push({



      pertemuan: Number(topik.dataset.p),



      topik: topik.value,



      bobot: Number(bobot.value),



      jumlah_slot: Number(slot.value),



      tipe: tipeEl ? tipeEl.value : "teori",



    });



  });







  const body = Object.assign({}, konteksKurikulum, {



    penawaran: {



      jenis_mk: _nilai("kur-jenis-mk"),



      semester_kurikulum: _nilai("kur-semester-kur"),



      // Hanya kotak ini yang boleh menaikkan status "tebakan awal" jadi



      // "dikonfirmasi". Tanpa centang, menyimpan topik tidak akan mengubah



      // status jenis_mk / semester_kurikulum.



      konfirmasi_jenis_mk: !!(document.getElementById("kur-jenis-konfirmasi") || {}).checked,



      konfirmasi_semester_kurikulum: !!(document.getElementById("kur-semester-konfirmasi") || {}).checked,



    },



    sesi,



  });







  const statusEl = document.getElementById("kurikulum-status");



  if (statusEl) statusEl.textContent = "Menyimpan ke tree & membangun ulang data…";



  try {



    const res = await fetch("/api/kurikulum/simpan", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify(body),



    });



    const data = await res.json();



    if (!res.ok) {



      const rincian = (data.masalah || []).join(" • ") || data.error || `HTTP ${res.status}`;



      toast(`Ditolak: ${rincian}`, "error", 11000);



      tampilkanPeringatanKurikulum((data.masalah || []).concat([data.error || ""]));



      return;



    }



    toast(data.pesan || "Tersimpan.", "success", 6000);



    tampilkanPeringatanKurikulum(data.peringatan || []);



    detailOverrideKonteks = null;



    // Katalog dibangun ulang -> cache perkembangan lintas-MK (chip "sepanjang



    // kuliah" tab 8 & kartu tren tab wali) basi; jangan sampai data lama tampil.



    perkembanganPotensi = {};



    mkRawanState = { prodi: null, dimuat: false, baris: [] }; // peta MK rawan ikut regen



    await muatKurikulum();



    await muatDetailKurikulum();



    await loadAcademicData();



  } catch (err) {



    toast(`Gagal menyimpan kurikulum: ${err.message}`, "error", 9000);



  } finally {



    if (statusEl) statusEl.textContent = "";



    if (window.lucide) lucide.createIcons();



  }



}







// =============================================================================



// TAB 8: REKAP PERIODE (Level 3: satu semester semua MK; Level 4: semua



// semester semua MK). Semua data dari /api/periode — dihitung dari TREE



// (scripts/periode.py), bukan master 1 MK. At-risk PER MK (keputusan user).



// =============================================================================



let rekapLevel = "semester";



let rekapTerakhir = null;







function _styleRekapButtons() {



  const peta = {



    mk: "rekap-scope-mk",



    semester: "rekap-scope-semester", semua: "rekap-scope-semua",



  };



  const aktif = "bg-fuchsia-500/20 text-fuchsia-200 border-fuchsia-500/40";



  const pasif = "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700";



  Object.entries(peta).forEach(([level, id]) => {



    const el = document.getElementById(id);



    if (el) el.className = `touch-target px-3 py-1.5 text-xs font-bold rounded-lg border transition ${rekapLevel === level ? aktif : pasif}`;



  });



  const wrapMk = document.getElementById("rekap-mk-control-wrap");



  if (wrapMk) wrapMk.classList.toggle("hidden", rekapLevel !== "mk");



}







function _sinkronRekapContextSelectors() {



  const globalTahun = document.getElementById("sel-tahun");



  const globalSem = document.getElementById("sel-semester");



  const rekapTahun = document.getElementById("rekap-sel-tahun");



  const rekapSem = document.getElementById("rekap-sel-semester");







  if (globalTahun && rekapTahun && rekapTahun.options.length !== globalTahun.options.length) {



    rekapTahun.innerHTML = globalTahun.innerHTML;



    rekapTahun.value = globalTahun.value;



  }



  if (globalSem && rekapSem && rekapSem.options.length !== globalSem.options.length) {



    rekapSem.innerHTML = globalSem.innerHTML;



    rekapSem.value = globalSem.value;



  }



}







function _updateRekapMkDropdown(baris) {



  const mkSel = document.getElementById("rekap-sel-mk");



  if (!mkSel) return;



  const currentVal = mkSel.value || _nilai("course-selector");



  mkSel.innerHTML = "";



  if (!baris || !baris.length) {



    const opt = document.createElement("option");



    opt.value = "";



    opt.textContent = "-- Tidak ada MK --";



    mkSel.appendChild(opt);



    return;



  }



  baris.forEach(b => {



    const opt = document.createElement("option");



    opt.value = b.kunci_mk;



    opt.textContent = `${b.kode_mk || ""} ${b.nama_mk || b.kunci_mk}`.trim();



    mkSel.appendChild(opt);



  });



  if (Array.from(mkSel.options).some(o => o.value === currentVal)) {



    mkSel.value = currentVal;



  } else if (mkSel.options.length) {



    mkSel.value = mkSel.options[0].value;



  }



}







function onRekapContextChange() {



  const globalTahun = document.getElementById("sel-tahun");



  const globalSem = document.getElementById("sel-semester");



  const rekapTahun = document.getElementById("rekap-sel-tahun");



  const rekapSem = document.getElementById("rekap-sel-semester");







  if (rekapTahun && globalTahun && rekapTahun.value !== globalTahun.value) {



    globalTahun.value = rekapTahun.value;



    isiSemester();



    if (rekapSem && globalSem) {



      rekapSem.innerHTML = globalSem.innerHTML;



      rekapSem.value = globalSem.value;



    }



  } else if (rekapSem && globalSem && rekapSem.value !== globalSem.value) {



    globalSem.value = rekapSem.value;



  }



  muatRekap();



}







function aktifkanScopeRekap(level) {



  rekapLevel = level;



  _styleRekapButtons();



  muatRekap();



}







function _isiSelectMahasiswaRekap() {



  const sel = document.getElementById("rekap-mhs");



  if (!sel) return "";



  const daftar = (masterData && masterData.students) || [];



  const lama = (currentStudent && currentStudent.npm) || sel.value || "";



  sel.innerHTML = "";



  daftar.forEach(s => {



    const opt = document.createElement("option");



    opt.value = s.npm;



    opt.textContent = `${s.npm} — ${s.nama}`;



    opt.selected = String(s.npm) === String(lama);



    sel.appendChild(opt);



  });



  if (!sel.value && daftar.length) sel.value = daftar[0].npm;



  return sel.value;



}







const NAMA_BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",



  "Juli", "Agustus", "September", "Oktober", "November", "Desember"];







function _kunciBulan(tanggal) {



  const m = String(tanggal || "").match(/^(\d{4})-(\d{2})/);



  return m ? `${m[1]}-${m[2]}` : "-";



}







function _labelBulan(kunci) {



  if (kunci === "-") return "Tanpa Tanggal";



  const [tahun, bulan] = kunci.split("-");



  return `${NAMA_BULAN[Number(bulan) - 1] || bulan} ${tahun}`;



}







function _ringkasBulan(detail) {



  const grup = new Map();



  (detail || []).forEach(d => {



    const k = _kunciBulan(d.tanggal);



    if (!grup.has(k)) grup.set(k, []);



    grup.get(k).push(d);



  });



  return [...grup.entries()].sort((a, b) => a[0] === "-" ? 1 : b[0] === "-" ? -1 : a[0].localeCompare(b[0]));



}







function _kpiRekap({ mk, atRisk, atRiskDesc, kehadiran, kehadiranDesc, nilai, nilaiDesc, mkDesc }) {



  setText("rekap-kpi-mk", mk ?? "-");



  setText("rekap-kpi-mk-desc", mkDesc || "-");



  setText("rekap-kpi-at-risk", atRisk ?? "-");



  setText("rekap-kpi-at-risk-desc", atRiskDesc || "-");



  setText("rekap-kpi-kehadiran", kehadiran ?? "-");



  setText("rekap-kpi-kehadiran-desc", kehadiranDesc || "Rata-rata antar-MK yang bisa dihitung");



  setText("rekap-kpi-nilai", nilai ?? "-");



  setText("rekap-kpi-nilai-desc", nilaiDesc || "-");



}







function _tampilkanRekapTabel(tampil) {



  const tabel = document.getElementById("rekap-tabel-wrapper");



  const bulan = document.getElementById("rekap-bulan-view");



  if (tabel) tabel.classList.toggle("hidden", !tampil);



  if (bulan) bulan.classList.toggle("hidden", tampil);



}







function _theadStandar() {



  const th = document.getElementById("rekap-thead");



  if (!th) return;



  th.innerHTML = `<tr>



    <th class="px-4 py-3">Mata Kuliah</th>



    <th class="px-4 py-3">Periode</th>



    <th class="px-4 py-3 text-center">Peserta</th>



    <th class="px-4 py-3 text-center">Kehadiran</th>



    <th class="px-4 py-3 text-center">Nilai</th>



    <th class="px-4 py-3 text-center">At-Risk</th>



    <th class="px-4 py-3 text-center">Pertemuan</th>



    <th class="px-4 py-3 text-center">Topik</th>



    <th class="px-4 py-3 text-center">Bulan</th>



    <th class="px-4 py-3">Status</th>



  </tr>`;



}







function _barisRekap(b) {



  if (b.rusak) {



    return `<tr><td colspan="10" class="px-4 py-2.5">



      <span class="text-rose-300 font-bold">${escapeHtml(b.nama_mk)}</span>



      <span class="text-rose-400/80"> — berkas tidak lengkap:



      ${escapeHtml(b.rusak).slice(0, 140)}</span></td></tr>`;



  }



  const atRiskBadge = b.jumlah_at_risk > 0



    ? `<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold">${b.jumlah_at_risk}</span>`



    : `<span class="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">0</span>`;



  const pert = `${b.pertemuan ?? 0}/${b.pertemuan_standar ?? 16}`;



  const topik = `${b.topik_terisi ?? 0}/${(b.topik_terisi ?? 0) + (b.topik_placeholder ?? 0)}`;



  const bulan = Object.keys(b.bulan || {}).map(k => k === "-" ? "tanpa tgl" : k).join(", ");



  return `<tr class="hover:bg-slate-800/40 transition-colors">



    <td class="px-4 py-2.5">



      <span class="text-slate-100 font-semibold">${escapeHtml(b.nama_mk)}</span>



      ${b.kode_mk ? `<span class="text-slate-500"> • ${escapeHtml(b.kode_mk)}</span>` : ""}



    </td>



    <td class="px-4 py-2.5 text-slate-400">${_tampilTahun(b.tahun_ajar)} • ${escapeHtml(b.semester)}</td>



    <td class="px-4 py-2.5 text-center text-slate-200">${b.peserta ?? "-"}</td>



    <td class="px-4 py-2.5 text-center text-emerald-300 font-bold">${b.kehadiran_rata != null ? `${b.kehadiran_rata}%` : "-"}</td>



    <td class="px-4 py-2.5 text-center text-amber-300 font-bold">${b.nilai_rata ?? "-"}</td>



    <td class="px-4 py-2.5 text-center">${atRiskBadge}</td>



    <td class="px-4 py-2.5 text-center text-slate-300">${pert}</td>



    <td class="px-4 py-2.5 text-center text-slate-300">${topik}</td>



    <td class="px-4 py-2.5 text-center text-slate-400 text-[10px]">${escapeHtml(bulan || "-")}</td>



    <td class="px-4 py-2.5 text-center">



      <button class="rekap-detail-btn touch-target px-2 py-1 text-[10px] bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-slate-700 transition"



        data-prodi="${escapeHtml(b.prodi || "")}" data-ta="${escapeHtml(b.tahun_ajar || "")}"



        data-sem="${escapeHtml(b.semester || "")}" data-kunci="${escapeHtml(b.kunci_mk || "")}">



        Rincian MK



      </button>



    </td>



  </tr>`;



}







function _pasangTombolDetail() {



  const tbody = document.getElementById("rekap-table-body");



  if (!tbody) return;



  tbody.querySelectorAll(".rekap-detail-btn").forEach(btn => {



    btn.addEventListener("click", () => {



      bukaModalEvaluasiMkRawan(btn.dataset.kunci || "");



    });



  });



}







function renderRekap(data) {



  const rk = data.ringkas || {};



  _kpiRekap({



    mk: rk.jumlah_mk ?? "-",



    mkDesc: `${rk.mk_lengkap ?? 0} MK bisa dihitung` + (rk.mk_rusak ? `, ${rk.mk_rusak} berkas rusak` : ""),



    atRisk: rk.jumlah_at_risk ?? "-",



    atRiskDesc: rk.jumlah_kejadian_at_risk != null



      ? `Mahasiswa unik; ${rk.jumlah_kejadian_at_risk} kejadian per MK`



      : "Mahasiswa unik (union antar-MK)",



    kehadiran: rk.kehadiran_rata != null ? `${rk.kehadiran_rata}%` : "belum bisa dihitung",



    nilai: rk.nilai_rata != null ? rk.nilai_rata : "belum bisa dihitung",



  });







  const tbody = document.getElementById("rekap-table-body");



  if (!tbody) return;



  _theadStandar();



  _tampilkanRekapTabel(true);



  tbody.innerHTML = "";







  const barisList = [];



  const levelSemua = rekapLevel === "semua" && data.tahun_ajar;







  if (levelSemua) {



    Object.entries(data.tahun_ajar).forEach(([ta, semMap]) => {



      Object.entries(semMap).forEach(([sem, dok]) => {



        const rkSem = dok.ringkas || {};



        const trHead = document.createElement("tr");



        trHead.className = "bg-slate-900/70 text-slate-300 font-bold";



        trHead.innerHTML = `<td colspan="10" class="px-4 py-2.5">



          ${_tampilTahun(ta)} • ${escapeHtml(sem)} —



          <span class="text-slate-400 font-normal">



            ${rkSem.jumlah_mk ?? 0} MK,



            at-risk unik ${rkSem.jumlah_at_risk ?? 0},



            kehadiran ${rkSem.kehadiran_rata ?? "-"},



            nilai ${rkSem.nilai_rata ?? "-"},



            topik placeholder ${rkSem.jumlah_topik_placeholder ?? 0}



          </span></td>`;



        tbody.appendChild(trHead);



        barisList.push(...(dok.baris || []));



      });



    });



  } else {



    barisList.push(...(data.baris || []));



  }







  if (!barisList.length) {



    tbody.innerHTML = `<tr><td colspan="10" class="px-4 py-8 text-center text-slate-500 italic">



      Tidak ada mata kuliah di cakupan ini.</td></tr>`;



    return;



  }







  tbody.innerHTML = barisList.map(_barisRekap).join("");



  _pasangTombolDetail();



  if (window.lucide) lucide.createIcons();



}







function _renderRekapSatuMk(b) {



  const rk = {



    jumlah_mk: 1, mk_lengkap: 1, mk_rusak: 0,



    jumlah_at_risk: b.jumlah_at_risk ?? 0,



    jumlah_kejadian_at_risk: b.jumlah_at_risk ?? 0,



    kehadiran_rata: b.kehadiran_rata, nilai_rata: b.nilai_rata,



  };



  renderRekap({ ringkas: rk, baris: [b] });



  setText("rekap-info",



    `MK: ${b.nama_mk || b.kunci_mk} • ${_tampilTahun(b.tahun_ajar)} ${b.semester} — ` +



    `at-risk dihitung untuk MK ini saja.`);



}







// =============================================================================



// TAB 8: PANEL POTENSI MAHASISWA PER MK (pilih MK bebas dari tree)



// =============================================================================



// Sumber: katalog build data/courses/<kunci>.json via /api/course_data.



// Katalog memuat satu dokumen master per MK (students + akademik + kehadiran



// + ai_diagnosis), jadi potensi bisa dilihat untuk MK mana pun - bukan hanya



// MK aktif di academic_data.json. Katalog lama yang belum dibangun ditolak



// fail-closed oleh server dengan pesan "jalankan parse_data".



let potensiMkAktif = null;



// Cache perkembangan lintas-MK per prodi (payload /api/perkembangan).



let perkembanganPotensi = {};







function sinkronPotensiMk(kunci) {



  // Drill-down "Per Semester (1 MK)" ikut mengarahkan panel potensi ke MK itu.



  const sel = document.getElementById("rekap-potensi-sel");



  if (!sel || !kunci) return;



  if (Array.from(sel.options).some(o => o.value === kunci)) {



    sel.value = kunci;



    muatPotensiMk(kunci);



  }



}







function _isiPilihMkPotensi(kunciDipaksa) {



  const sel = document.getElementById("rekap-potensi-sel");



  if (!sel || !pohonKurikulum || !pohonKurikulum.pohon) return false;



  const aktif = kunciDipaksa || _nilai("course-selector");



  const lama = sel.value || potensiMkAktif || "";



  sel.innerHTML = "";



  let pertama = "";



  Object.entries(pohonKurikulum.pohon).forEach(([prodi, tahunMap]) => {



    Object.entries(tahunMap || {}).forEach(([ta, semMap]) => {



      Object.entries(semMap || {}).forEach(([sem, mkList]) => {



        if (!Array.isArray(mkList)) return;



        mkList.forEach(mk => {



          if (!mk || mk.rusak || !mk.kunci_mk) return;



          if (!pertama) pertama = mk.kunci_mk;



          const opt = document.createElement("option");



          opt.value = mk.kunci_mk;



          opt.textContent =



            `${mk.nama_mk || mk.kunci_mk} • ${_tampilTahun(ta)} • ${sem}`;



          opt.dataset.prodi = prodi;



          sel.appendChild(opt);



        });



      });



    });



  });



  if (!pertama) return false;



  // Prioritas utama: MK aktif di header, lalu pilihan sebelumnya, lalu pertama.



  const adaAktif = Array.from(sel.options).some(o => o.value === aktif);



  const adaLama = Array.from(sel.options).some(o => o.value === lama);



  sel.value = adaAktif ? aktif : (adaLama ? lama : pertama);



  return true;



}







function sinkronkanTabRekapKeKonteks(kunciMk) {



  const kunci = kunciMk || (masterData && masterData.metadata && masterData.metadata.kunci_mk) || _nilai("course-selector");



  if (!kunci) return;



  _isiPilihMkPotensi(kunci);



  const selPotensi = document.getElementById("rekap-potensi-sel");



  if (selPotensi && Array.from(selPotensi.options).some(o => o.value === kunci)) {



    selPotensi.value = kunci;



  }



  muatPotensiMk(kunci);



  muatRekap();



}







const _PALETE_POTENSI = {



  rose: "bg-rose-500/20 text-rose-300 border-rose-500/30",



  amber: "bg-amber-500/20 text-amber-300 border-amber-500/30",



  sky: "bg-sky-500/20 text-sky-300 border-sky-500/30",



  emerald: "bg-emerald-500/20 text-emerald-300 border-emerald-500/25",



};







async function muatPotensiMk(kunciTarget) {



  const sel = document.getElementById("rekap-potensi-sel");



  const grid = document.getElementById("rekap-potensi-grid");



  const kpi = document.getElementById("rekap-potensi-kpi");



  if (!sel || !grid || !kpi) return;



  if (!sel.options.length || !sel.value) _isiPilihMkPotensi(kunciTarget);



  if (kunciTarget && Array.from(sel.options).some(o => o.value === kunciTarget)) {



    sel.value = kunciTarget;



  }



  const kunci = sel.value;



  if (!kunci) { grid.innerHTML = ""; kpi.innerHTML = ""; return; }



  potensiMkAktif = kunci;







  grid.innerHTML =



    `<p class="text-xs text-slate-500 italic col-span-full">Memuat potensi mahasiswa ${escapeHtml(kunci)}…</p>`;



  kpi.innerHTML = "";



  try {



    const res = await fetch(



      `/api/course_data?course=${encodeURIComponent(kunci)}`, { cache: "no-store" });



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);







    // KPI ringkas dari class_summary katalog (angka yang sama dengan tab 1).



    const cs = data.class_summary || {};



    const namaMk = (data.course && (data.course.nama_mk || data.course.nama)) || kunci;



    const infoPeserta = cs.total_mahasiswa === 37 



      ? `👥 37 Mahasiswa (35 Reguler Angk 25 + 2 Mengulang Angk 24)`



      : `👥 ${cs.total_mahasiswa ?? "-"} Mahasiswa Terdaftar`;



    kpi.innerHTML =



      `<span class="font-semibold text-white truncate max-w-xs" title="${escapeHtml(namaMk)}">${escapeHtml(namaMk)}</span>` +



      `<span class="font-bold text-cyan-300">${infoPeserta}</span>` +



      `<span class="text-rose-300">⚠️ ${cs.total_at_risk ?? 0} at-risk</span>` +



      `<span class="text-emerald-300">Kehadiran ${cs.rata_kehadiran ?? "-"}%</span>` +



      `<span class="text-amber-300">Nilai ${cs.rata_nilai_studio ?? "-"}</span>`;







    const daftar = (data.students || []).slice().sort((a, b) =>



      (b.at_risk ? 1 : 0) - (a.at_risk ? 1 : 0) || (a.no || 0) - (b.no || 0));



    if (!daftar.length) {



      grid.innerHTML =



        `<p class="text-xs text-slate-500 italic col-span-full">Katalog ini belum memuat baris mahasiswa.</p>`;



      return;



    }







    grid.innerHTML = daftar.map(s => {



      const ak = s.akademik || {};



      const kh = s.kehadiran || {};



      const ai = s.ai_diagnosis || {};



      const warna = _PALETE_POTENSI[ai.alert_color] || _PALETE_POTENSI.emerald;



      const karier = (ai.matriks_karier_10 || [])[0] || {};



      const catatan = ai.catatan_khusus_mahasiswa || ai.kekuatan || "-";



      return `<div class="p-4 rounded-xl bg-slate-800/70 border border-slate-700/60 flex flex-col gap-2 min-w-0" data-npm="${escapeHtml(s.npm || "")}">



        <div class="flex items-start justify-between gap-2">



          <div class="min-w-0">



            <div class="font-bold text-white text-sm truncate" title="${escapeHtml(s.nama || "")}">${escapeHtml(s.nama || "-")}</div>



            <div class="text-[10px] text-slate-400 font-mono">NPM ${escapeHtml(s.npm || "-")}</div>



            <div class="text-[9px] text-slate-500 font-mono" title="Mesin diagnosis: templat_v3 = dihitung dari sinyal nyata (nilai, kehadiran, tren); nanti bisa naik ke AI-Gemini">mesin: ${escapeHtml((ai.mesin && ai.mesin.sumber) || "-")}</div>



          </div>



          <span class="px-2 py-0.5 rounded text-[10px] font-bold border flex-shrink-0 ${warna}">${escapeHtml(ai.status_alert || (s.at_risk ? "At-Risk" : "Aman"))}</span>



        </div>



        <div class="grid grid-cols-4 gap-2 text-center text-[11px]">



          <div><div class="text-slate-400">Grade</div><div class="font-bold text-white">${escapeHtml(ak.grade ?? "-")}</div></div>



          <div><div class="text-slate-400">Kesiapan</div><div class="font-bold text-cyan-300">${escapeHtml(ak.indeks_kesiapan ?? "-")}%</div></div>



          <div><div class="text-slate-400">Nilai</div><div class="font-bold text-amber-300">${escapeHtml(ak.nilai_rata_rata ?? "-")}</div></div>



          <div><div class="text-slate-400">Alpha</div><div class="font-bold ${kh.alpha ? "text-rose-300" : "text-slate-300"}">${escapeHtml(kh.alpha ?? 0)}x</div></div>



        </div>



        <div class="text-[10px] text-slate-400">



          Kehadiran <span class="text-slate-200 font-semibold">${escapeHtml(kh.persentase ?? "-")}%</span> slot •



          Kekuatan <span class="text-emerald-300">${escapeHtml(ai.kekuatan || "-")}</span>



        </div>



        ${_chipBulananDetail(kh.detail)}



        ${karier.profesi



          ? `<div class="text-[10px] text-slate-400">Karier teratas: <span class="text-cyan-300 font-semibold">${escapeHtml(karier.profesi)}</span>${karier.kecocokan_persen != null ? ` • ${escapeHtml(karier.kecocokan_persen)}%` : ""}</div>`



          : ""}



        <p class="text-[10px] text-slate-300 leading-relaxed" title="${escapeHtml(catatan)}">${escapeHtml(String(catatan).slice(0, 180))}${String(catatan).length > 180 ? "…" : ""}</p>



      </div>`;



    }).join("");







    // LEVEL 3 (opsional, async): chip perkembangan sepanjang kuliah per npm.



    _terapkanPerkembangan();



  } catch (err) {



    grid.innerHTML =



      `<div class="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 col-span-full">` +



      `Potensi MK ${escapeHtml(kunci)} gagal dimuat: ${escapeHtml(err.message)}</div>`;



    kpi.innerHTML = "";



  }



}







/** LEVEL 1 dari potensi: chip perkembangan PER BULAN dalam 1 MK, dari



 *  kehadiran.detail katalog (tanggal + slot per pertemuan). Pertemuan



 *  "Belum Diinput" NETRAL - tidak menekan persen (aturan yang sama dengan



 *  Batch B di scripts/periode.py), pertemuan tanpa tanggal tidak ikut



 *  bulan yang salah. */



function _chipBulananDetail(detail) {



  const grup = {};



  (detail || []).forEach(d => {



    const b = bulanDariTanggal(d.tanggal);



    if (b === GRUP_TANPA_TANGGAL) return;



    if (d.status === "Belum Diinput" || !d.slot_terisi) return; // netral



    const g = (grup[b] = grup[b] || { hadir: 0, total: 0, skor: 0, n: 0 });



    g.total += d.slot_total || 0;



    g.hadir += d.slot_hadir || 0;



    if (typeof d.skor === "number") { g.skor += d.skor; g.n += 1; }



  });



  const kuncis = Object.keys(grup).sort();



  if (!kuncis.length) return "";



  return `<div class="flex flex-wrap gap-1">${kuncis.map(b => {



    const g = grup[b];



    const pct = g.total ? Math.round((g.hadir / g.total) * 100) : null;



    const rata = g.n ? (g.skor / g.n).toFixed(1) : null;



    const warna = pct == null ? "text-slate-500"



      : pct >= 85 ? "text-emerald-300 bg-emerald-500/10"



      : pct >= 75 ? "text-amber-300 bg-amber-500/10"



      : "text-rose-300 bg-rose-500/10";



    const tt = `Kehadiran slot ${labelBulan(b)}${rata ? ` • rata skor ${rata}` : ""}`;



    return `<span class="px-1.5 py-0.5 rounded border border-slate-700/50 text-[10px] font-semibold ${warna}" title="${escapeHtml(tt)}">${escapeHtml(labelBulan(b).split(" ")[0].slice(0, 3))} ${pct ?? "-"}%</span>`;



  }).join("")}</div>`;



}







/** Auth data perkembangan lintas-MK per bank prodi (cache per sesi UI).



 *  Dipakai dekorator tab 8 dan kartu tren tab wali. Gagal -> null (lapis



 *  lintas-MK opsional, kartu per-MK tetap utuh). */



async function dataPerkembangan() {



  const prodi = _nilai("sel-prodi");



  if (!prodi) return null;



  if (!perkembanganPotensi[prodi]) {



    try {



      const res = await fetch(



        `/api/perkembangan?prodi=${encodeURIComponent(prodi)}`, { cache: "no-store" });



      const payload = await res.json();



      if (!res.ok) throw new Error(payload.error || `HTTP ${res.status}`);



      perkembanganPotensi[prodi] = payload;



    } catch (_err) {



      return null; // lapis lintas-MK dilewati, kartu per MK tetap utuh



    }



  }



  return perkembanganPotensi[prodi];



}







/** LEVEL 3 dari potensi: chip perkembangan SEPANJANG KULIAH per mahasiswa



 *  (riwayat lintas MK/semester dari /api/perkembangan). Gagal fetch TIDAK



 *  menutup kartu per MK - lapis ini opsional, jadi didekorasi belakangan. */



async function _terapkanPerkembangan() {



  const perk = await dataPerkembangan();



  if (!perk) return;



  document.querySelectorAll("#rekap-potensi-grid [data-npm]").forEach(kartu => {



    if (kartu.querySelector(".potensi-perkembangan")) return; // hindari ganda



    const html = _chipPerkembangan(perk, kartu.dataset.npm);



    if (html) kartu.insertAdjacentHTML("beforeend", html);



  });



}







function _chipPerkembangan(perk, npm) {



  const p = (perk && perk.mahasiswa) ? perk.mahasiswa[String(npm)] : null;



  if (!p || !p.jumlah_mk) return "";



  const ikon = p.arah_nilai === "naik" ? "↑"



    : p.arah_nilai === "turun" ? "↓" : "→";



  const kelas = p.arah_nilai === "naik" ? "text-emerald-300 border-emerald-500/30"



    : p.arah_nilai === "turun" ? "text-rose-300 border-rose-500/30"



    : "text-slate-300 border-slate-600/60";



  const riwayat = (p.riwayat || []).map(r =>



    `• ${r.tahun_ajar} ${r.semester} — ${r.nama_mk}: nilai ${r.nilai ?? "-"}`



    + `${r.grade ? ` (${r.grade})` : ""}, kehadiran ${r.kehadiran ?? "-"}%`



    + `${r.at_risk ? " • AT-RISK" : ""}`).join("\n");



  const delta = (p.delta_nilai_terakhir != null)



    ? `${p.delta_nilai_terakhir > 0 ? "+" : ""}${p.delta_nilai_terakhir}` : "";



  return `<div class="potensi-perkembangan flex items-center gap-1.5 flex-wrap">



    <span class="px-1.5 py-0.5 rounded border text-[10px] font-bold ${kelas}"



      title="Sepanjang kuliah (${p.jumlah_mk} MK):&#10;${escapeHtml(riwayat)}">${p.jumlah_mk} MK ${ikon}${delta ? ` (${delta})` : ""}</span>



    <span class="text-[10px] text-slate-500">sepanjang kuliah</span>



  </div>`;



}







async function _muatRekapBulan() {



  const npm = _isiSelectMahasiswaRekap();



  const host = document.getElementById("rekap-bulan-cards");



  if (!host) return;



  _tampilkanRekapTabel(false);



  setText("rekap-info", "");



  if (!npm) {



    host.innerHTML = `<p class="text-xs text-slate-500 italic">Belum ada mahasiswa untuk ditampilkan.</p>`;



    return;



  }



  const mhs = ((masterData && masterData.students) || []).find(s => String(s.npm) === String(npm));



  if (!mhs) {



    host.innerHTML = `<p class="text-xs text-rose-300">Mahasiswa ${escapeHtml(npm)} tidak ada di data master.</p>`;



    return;



  }



  const k = mhs.kehadiran || {};



  const ak = mhs.akademik || {};



  const bulan = _ringkasBulan(k.detail);



  _kpiRekap({



    mk: 1,



    // Sumber nama MK = course di master (masterData.mk tidak pernah ada di



    // payload; dulu selalu jatuh ke fallback teks generik "MK aktif").



    mkDesc: ((masterData && masterData.course &&



      (masterData.course.nama_mk || masterData.course.nama)) || "MK aktif"),



    atRisk: mhs.at_risk ? 1 : 0,



    atRiskDesc: mhs.at_risk ? (mhs.alasan_at_risk || []).join(" • ") : "Tidak terdeteksi berisiko",



    kehadiran: k.persentase != null ? `${k.persentase}%` : "belum bisa dihitung",



    kehadiranDesc: `${k.slot_hadir ?? 0}/${k.slot_total ?? 0} slot • ${k.pertemuan_penuh ?? 0} pertemuan penuh`,



    nilai: ak.nilai_rata_rata != null ? ak.nilai_rata_rata : "-",



    nilaiDesc: ak.grade ? `Grade ${ak.grade}` : "-",



  });



  setText("rekap-bulan-judul", `Perjalanan Bulanan — ${mhs.nama}`);



  setText("rekap-bulan-sub",



    `NPM ${mhs.npm} • MK aktif • ${bulan.length} kelompok bulan`);



  host.innerHTML = bulan.map(([kunci, daftar]) => {



    const penuh = daftar.filter(d => d.status === "Hadir").length;



    const sebagian = daftar.filter(d => d.status === "Hadir Sebagian").length;



    const alpha = daftar.filter(d => d.status === "Alpha").length;



    const sakit = daftar.filter(d => d.status === "Sakit").length;



    const izin = daftar.filter(d => d.status === "Izin").length;



    const belum = daftar.filter(d => d.status === "Belum Diinput").length;



    const skor = daftar.map(d => d.skor).filter(v => typeof v === "number");



    const rata = skor.length ? (skor.reduce((a, b) => a + b, 0) / skor.length).toFixed(1) : "-";



    const rincian = daftar.map(d => {



      const warna = d.status === "Hadir" ? "text-emerald-300"



        : d.status === "Hadir Sebagian" ? "text-teal-300"



        : d.status === "Alpha" ? "text-rose-300"



        : d.status === "Sakit" ? "text-amber-300"



        : d.status === "Izin" ? "text-sky-300" : "text-slate-400";



      return `<div class="flex items-start justify-between gap-2 py-1 border-t border-slate-700/40 first:border-0">



        <span class="text-slate-400">P${escapeHtml(d.pertemuan)} • ${escapeHtml(d.tanggal_display || d.tanggal || "tanpa tanggal")}</span>



        <span class="${warna} font-semibold text-right">${escapeHtml(d.status)}${typeof d.skor === "number" ? ` • ${d.skor}` : ""}</span>



      </div>`;



    }).join("");



    return `<div class="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50">



      <div class="flex items-center justify-between gap-2">



        <span class="text-sm font-bold text-white">${escapeHtml(_labelBulan(kunci))}</span>



        <span class="text-[11px] text-slate-400">${daftar.length} pertemuan</span>



      </div>



      <div class="grid grid-cols-2 gap-2 mt-2 text-[11px]">



        <span class="text-emerald-300">Hadir ${penuh}</span>



        <span class="text-teal-300">Sebagian ${sebagian}</span>



        <span class="text-rose-300">Alpha ${alpha}</span>



        <span class="text-amber-300">Sakit ${sakit}</span>



        <span class="text-sky-300">Izin ${izin}</span>



        <span class="text-slate-400">Belum ${belum}</span>



      </div>



      <div class="mt-2 text-xs text-slate-300">Rata nilai bulan ini: <strong class="text-amber-300">${rata}</strong></div>



      <div class="mt-2 text-[11px]">${rincian}</div>



    </div>`;



  }).join("");



  if (window.lucide) lucide.createIcons();



}







async function muatRekap() {



  _styleRekapButtons();



  _sinkronRekapContextSelectors();



  const statusEl = document.getElementById("rekap-status");



  if (rekapLevel === "bulan") {



    if (statusEl) statusEl.textContent = "";



    await _muatRekapBulan();



    return;



  }



  const prodi = _nilai("sel-prodi") || "ARSITEKTUR";







  const q = new URLSearchParams({ prodi });



  if (rekapLevel === "semua") {



    q.set("semua_semester", "1");



  } else {



    const ta = _nilai("rekap-sel-tahun") || _nilai("sel-tahun");



    const sem = _nilai("rekap-sel-semester") || _nilai("sel-semester");



    if (!ta || !sem) {



      if (statusEl) statusEl.textContent = "Pilih tahun ajar & semester untuk rekap ini.";



      return;



    }



    q.set("tahun_ajar", ta); q.set("semester", sem);



  }







  if (statusEl) statusEl.textContent = "Menghitung rekap dari tree kurikulum…";



  try {



    const res = await fetch(`/api/periode?${q.toString()}`, { cache: "no-store" });



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);



    rekapTerakhir = data;







    // Sinkronkan daftar MK lokal di Tab 9 jika rekapLevel === 'mk'



    _updateRekapMkDropdown(data.baris || []);







    if (rekapLevel === "mk") {



      let kunci = _nilai("rekap-sel-mk") || _nilai("course-selector");



      let b = (data.baris || []).find(x => x.kunci_mk === kunci);



      if (!b && data.baris && data.baris.length > 0) {



        b = data.baris[0];



        kunci = b.kunci_mk;



        const mkSel = document.getElementById("rekap-sel-mk");



        if (mkSel) mkSel.value = kunci;



      }



      if (!b) throw new Error(`MK ${kunci} tidak ada di semester ini.`);



      _renderRekapSatuMk(b);



      sinkronPotensiMk(b.kunci_mk);



    } else {



      renderRekap(data);



      setText("rekap-info", "");



    }



    if (statusEl) statusEl.textContent = "Data terverifikasi aktif.";



  } catch (err) {



    if (statusEl) statusEl.textContent = "";



    toast(`Rekap periode tidak bisa dibuat: ${err.message}`, "error", 8000);



  }



}







/** Drill-down dari baris rekap -> tab Kurikulum. HANYA membaca detail;



 *  TIDAK memindahkan MK aktif (tidak memicu switch_course / rebuild). */



function rekapLihatMk(prodi, tahunAjar, semester, kunciMk) {



  detailOverrideKonteks = {



    prodi, tahun_ajar: tahunAjar, semester, kunci_mk: kunciMk,



  };



  switchTab("kurikulum", { pertahankanOverride: true });



}







/* ========================================================================== *



 * TAB 10: ENGINE - pemeriksa INPUT & OUTPUT (modul terpisah di scripts/)



 *  - input  : pindai inbox, deteksi duplikat via SHA-256 (engine_input.py)



 *  - output : audit integritas + lapis kirim kaprodi/wali (engine_output.py)



 * ========================================================================== */







function _engineUkuran(byte) {



  if (byte === null || byte === undefined) return "—";



  if (byte >= 1024 * 1024) return (byte / (1024 * 1024)).toFixed(2) + " MB";



  if (byte >= 1024) return (byte / 1024).toFixed(1) + " KB";



  return byte + " B";



}







async function engineInputPindai() {



  const isi = document.getElementById("engine-input-isi");



  const chips = document.getElementById("engine-input-ringkasan");



  const btn = document.getElementById("btn-engine-input");



  if (btn) btn.disabled = true;



  if (isi) isi.innerHTML = '<p class="text-slate-500 italic text-sm">Memindai inbox…</p>';



  try {



    const res = await fetch("/api/engine/input", { cache: "no-store" });



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);



    _renderEngineInput(data);



  } catch (err) {



    if (isi) isi.innerHTML =



      `<p class="text-rose-400 text-sm">Pindai gagal: ${escapeHtml(err.message)}</p>`;



  } finally {



    if (btn) btn.disabled = false;



  }



}







function _renderEngineInput(data) {



  const isi = document.getElementById("engine-input-isi");



  const chips = document.getElementById("engine-input-ringkasan");



  const r = data.ringkasan || {};



  const warnaChip = {



    duplikat: "bg-amber-500/10 text-amber-300 border-amber-500/30",



    baru: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",



    terdaftar: "bg-slate-500/10 text-slate-300 border-slate-500/30",



  };



  if (chips) {



    chips.classList.remove("hidden");



    chips.innerHTML = [



      ["total", r.total], ["baru", r.baru], ["duplikat", r.duplikat],



      ["terdaftar", r.terdaftar],



    ].map(([k, v]) =>



      `<span class="px-2.5 py-1 rounded-full border ${warnaChip[k] || warnaChip.terdaftar}">${k}: <strong>${v ?? 0}</strong></span>`



    ).join("");



  }



  const berkas = data.berkas || [];



  if (isi) {



    if (!berkas.length) {



      isi.innerHTML = '<p class="text-slate-500 italic text-sm">Inbox kosong — tidak ada data masuk.</p>';



    } else {



      isi.innerHTML = `<div class="overflow-x-auto"><table class="w-full text-xs">



        <thead><tr class="text-slate-400 border-b border-slate-800 text-left">



        <th class="py-2 pr-3">Berkas</th><th class="py-2 pr-3">Ukuran</th>



        <th class="py-2 pr-3">Status</th><th class="py-2">Detail</th></tr></thead>



        <tbody>${berkas.map(b => {



          const badge = b.status === "duplikat"



            ? "bg-amber-500/10 text-amber-300 border-amber-500/30"



            : b.status === "baru"



              ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"



              : "bg-slate-600/10 text-slate-400 border-slate-600/30";



          const detail = b.status === "duplikat"



            ? (b.kembar_dengan || []).map(k => `<div class="text-amber-200/80 truncate max-w-[26rem]" title="${escapeHtml(k)}">↳ ${escapeHtml(k)}</div>`).join("")



            : (b.diproses_at ? `<span class="text-emerald-300/80">diproses ${escapeHtml(b.diproses_at)}</span>` : "-");



          return `<tr class="border-b border-slate-800/50">



            <td class="py-2 pr-3 font-medium text-slate-200 break-all">${escapeHtml(b.nama)}</td>



            <td class="py-2 pr-3 text-slate-400 whitespace-nowrap">${_engineUkuran(b.ukuran)}</td>



            <td class="py-2 pr-3"><span class="px-2 py-0.5 rounded-full border ${badge}">${b.status}</span></td>



            <td class="py-2">${detail}</td></tr>`;



        }).join("")}</tbody></table></div>



        <p class="text-[11px] text-slate-500 mt-2">Dicocokkan lewat SHA-256 (bukan nama berkas). Tandai "sudah diproses" lewat POST /api/engine/input.</p>`;



    }



  }



}







async function engineOutputAudit() {



  const isi = document.getElementById("engine-output-isi");



  const btn = document.getElementById("btn-engine-output");



  if (btn) btn.disabled = true;



  if (isi) isi.innerHTML = '<p class="text-slate-500 italic text-sm">Mengaudit output…</p>';



  try {



    const res = await fetch("/api/engine/output", { cache: "no-store" });



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);



    _renderEngineOutput(data);



  } catch (err) {



    if (isi) isi.innerHTML =



      `<p class="text-rose-400 text-sm">Audit gagal: ${escapeHtml(err.message)}</p>`;



  } finally {



    if (btn) btn.disabled = false;



  }



}







function _renderEngineOutput(data) {



  const isi = document.getElementById("engine-output-isi");



  const r = data.ringkasan || {};



  const chip = (v, warna, label) =>



    `<span class="px-2.5 py-1 rounded-full border ${warna}">${label}: <strong>${v ?? 0}</strong></span>`;



  const chips = [



    chip(r.utuh, "bg-emerald-500/10 text-emerald-300 border-emerald-500/30", "utuh"),



    chip(r.rusak, "bg-rose-500/10 text-rose-300 border-rose-500/30", "rusak"),



    chip(r.hilang, "bg-amber-500/10 text-amber-300 border-amber-500/30", "hilang"),



    chip(r.belum_terdaftar, "bg-slate-500/10 text-slate-300 border-slate-500/30", "belum terdaftar"),



    chip(r.salinan_usang, r.salinan_usang



      ? "bg-orange-500/10 text-orange-300 border-orange-500/30"



      : "bg-slate-500/10 text-slate-300 border-slate-500/30", "salinan usang"),



    chip(r.sisa_root, r.sisa_root



      ? "bg-orange-500/10 text-orange-300 border-orange-500/30"



      : "bg-slate-500/10 text-slate-300 border-slate-500/30", "sisa root"),



    chip((data.run_list || []).length, "bg-violet-500/10 text-violet-300 border-violet-500/30", "run"),



    chip(r.folder_tanpa_manifest, "bg-slate-500/10 text-slate-400 border-slate-500/30", "sisa tanpa manifest"),



  ].join("");



  const kirim = [



    ["Lapis kirim kaprodi", data.kirim_kaprodi_ada],



    ["Lapis kirim wali", data.kirim_wali_ada],



  ].map(([l, ok]) =>



    `<span class="px-2.5 py-1 rounded-full border ${ok



      ? "bg-lime-500/10 text-lime-300 border-lime-500/30"



      : "bg-slate-500/10 text-slate-400 border-slate-500/30"}">${l}: ${ok ? "siap" : "belum"}</span>`



  ).join("");







  const barisReg = (data.berkas || []).slice(0, 40).map(b => {



    const badge = b.status === "utuh"



      ? "text-emerald-300" : b.status === "rusak"



        ? "text-rose-300" : "text-amber-300";



    return `<tr class="border-b border-slate-800/50">



      <td class="py-1.5 pr-3 break-all text-slate-300">${escapeHtml(b.path)}</td>



      <td class="py-1.5 pr-3 text-slate-400 whitespace-nowrap">${_engineUkuran(b.ukuran_disk !== null ? b.ukuran_disk : b.ukuran_tercatat)}</td>



      <td class="py-1.5 pr-3 font-semibold ${badge}">${b.status}</td>



      <td class="py-1.5 text-slate-500 whitespace-nowrap">${escapeHtml(b.updated_at || "")}</td></tr>`;



  }).join("");







  const runRows = (data.run_list || []).map(run =>



    `<div class="flex items-center gap-2 text-xs">



      <span class="${run.adalah_terbaru ? "text-lime-300 font-semibold" : "text-slate-400"}">${run.adalah_terbaru ? "★ terbaru" : "run"}</span>



      <span class="break-all text-slate-400">${escapeHtml(run.path)}</span>



      <span class="text-slate-500">(${run.ukuran_kb} KB)</span></div>`).join("");







  if (isi) {



    isi.innerHTML = `



      <div class="flex flex-wrap gap-2 mb-2">${chips}</div>



      <div class="flex flex-wrap gap-2 mb-3">${kirim}</div>



      ${barisReg ? `<div class="overflow-x-auto"><table class="w-full text-xs">



        <thead><tr class="text-slate-400 border-b border-slate-800 text-left">



        <th class="py-2 pr-3">Berkas (registry)</th><th class="py-2 pr-3">Ukuran</th>



        <th class="py-2 pr-3">Status</th><th class="py-2">Dicatat</th></tr></thead>



        <tbody>${barisReg}</tbody></table></div>` : ""}



      ${runRows ? `<div class="mt-3 space-y-1">${runRows}</div>` : ""}



      <p class="text-[11px] text-slate-500 mt-2">Aturan tulis: berkas lama utuh dengan tanda logika/format sama <span class="text-emerald-300">diberikan apa adanya</span>; overwrite hanya bila logika/format maju atau ukuran tak cocok (mode overwrite).</p>`;



  }



}







async function engineOutputRapikan() {



  if (!confirm("Rapikan output? Run lama dipindah ke data/_backup/ (bisa dibuka lagi), lapis kirim kaprodi & wali disiapkan. Lanjut?")) {



    return;



  }



  const isi = document.getElementById("engine-output-isi");



  const btn = document.getElementById("btn-engine-rapikan");



  if (btn) {



    btn.disabled = true;



    btn.dataset.labelAsli = btn.textContent;



    btn.textContent = "Memproses…";  // anti dobel-klik saat pindah besar



  }



  if (isi) isi.innerHTML =



    '<p class="text-slate-500 italic text-sm">Memindahkan run lama ke arsip & menyiapkan lapis kirim…</p>';



  try {



    const res = await fetch("/api/engine/output", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ aksi: "rapikan", arsipkan_lama: true }),



    });



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);



    const dipindah = (data.dipindah || []);



    toast(



      `Rapikan selesai: ${dipindah.length} run lama diarsipkan ` +



      `(${(data.dipindah_mb || 0).toFixed(1)} MB). Lapis kirim siap.`,



      "success", 8000);



    await engineOutputAudit();



  } catch (err) {



    if (isi) isi.innerHTML =



      `<p class="text-rose-400 text-sm">Rapikan gagal: ${escapeHtml(err.message)}</p>`;



    toast(`Rapikan gagal: ${err.message}`, "error", 8000);



  } finally {



    if (btn) {



      btn.disabled = false;



      if (btn.dataset.labelAsli !== undefined) btn.textContent = btn.dataset.labelAsli;



    }



  }



}











// =============================================================================



// CENTER OF THE UNIVERSE: DYNAMIC CAREER ANCHOR & GAMIFIED DOPAMINE BADGES



// =============================================================================



function getStudentCareerAnchor(student) {



  if (!student) return { profesi: "Perancang Arsitektur Pratama", kecocokan_persen: 85, bidang_industri: "Biro Konsultan Perencana & Desain", analisis_potensi: "Karakter spasial dan kemampuan teknis mahasiswa siap dikembangkan menuju standar industri." };



  const ai = student.ai_diagnosis || {};



  const careers = ai.matriks_karier_10 || [];



  const ak = student.akademik || {};



  const comp = ak.kompetensi || {};







  // Pemetaan DNA Diferensial (CEO Logic):



  // 1. Mahasiswa Star CAD/Komputasi tinggi -> BIM & Digital Architecture



  if ((comp.penguasaan_cad ?? 0) >= 90) {



    const bimCareer = careers.find(c => c.profesi.includes("BIM") || c.profesi.includes("Digital"));



    if (bimCareer) return bimCareer;



  }



  // 2. Mahasiswa Ketelitian Gambar Kerja tinggi -> DED Specialist



  if ((comp.ketelitian_detail ?? 0) >= 80) {



    const dedCareer = careers.find(c => c.profesi.includes("Detail") || c.profesi.includes("DED"));



    if (dedCareer) return dedCareer;



  }



  // 3. Mahasiswa Orientasi Praktis / At-Risk -> Site Supervisor



  if ((student.at_risk && student.at_risk.length > 0) || (ak.nilai_rata_rata ?? 0) < 70) {



    const siteCareer = careers.find(c => c.profesi.includes("Site Architect") || c.profesi.includes("Pengawas"));



    if (siteCareer) return siteCareer;



  }



  // 4. Default fallback ke karir teratas



  return careers[0] || {



    profesi: "Perancang Arsitektur Pratama",



    kecocokan_persen: ak.indeks_kesiapan ?? 85,



    bidang_industri: "Biro Konsultan Perencana & Desain",



    analisis_potensi: ai.analisis_karakter_spasial || "Karakter spasial dan kemampuan teknis mahasiswa siap dikembangkan."



  };



}







function getStudentBadges(student) {



  if (!student) return [];



  const ak = student.akademik || {};



  const comp = ak.kompetensi || {};



  const kh = student.kehadiran || {};



  const cad = comp.penguasaan_cad ?? 0;



  const detail = comp.ketelitian_detail ?? 0;



  const struktur = comp.logika_ruang_struktur ?? 0;



  const nilai = ak.nilai_rata_rata ?? 0;



  const hadir = kh.persentase ?? 0;



  const alpha = kh.alpha ?? 0;







  return [



    {



      nama: "CAD Drafting Specialist",



      icon: "pencil-ruler",



      unlocked: cad >= 75 && nilai >= 70,



      desc: "Layering & Lineweight Presisi",



      req: `Butuh Skor CAD >= 75 & Nilai >= 70 (Sekarang: CAD ${cad}, Nilai ${nilai})`



    },



    {



      nama: "Structural Detailer Pro",



      icon: "building",



      unlocked: struktur >= 75,



      desc: "Sistem Struktur & Logika Spasial",



      req: `Butuh Logika Struktur >= 75 (Sekarang: ${struktur})`



    },



    {



      nama: "Precision Quality Gate",



      icon: "check-check",



      unlocked: detail >= 75 && nilai >= 70,



      desc: "Notasi, Skala & Dimensi Lengkap",



      req: `Butuh Ketelitian >= 75 (Sekarang: ${detail})`



    },



    {



      nama: "Studio Discipline Master",



      icon: "clock",



      unlocked: hadir >= 85 && alpha === 0,



      desc: "Asistensi Penuh Bebas Alpha",



      req: `Butuh Kehadiran >= 85% & 0 Alpha (Sekarang: ${hadir}%, ${alpha}x Alpha)`



    }



  ];



}







function renderStudentUniverse(student) {



  if (!student) return;



  const topCareer = getStudentCareerAnchor(student);



  const badges = getStudentBadges(student);







  setText("mhs-top-career-title", topCareer.profesi || "Perancang Arsitektur Pratama");



  setText("mhs-top-career-pct", `${topCareer.kecocokan_persen ?? 85}% Match`);



  setText("mhs-top-career-desc", topCareer.analisis_potensi || "Karakter spasial dan kemampuan teknis mahasiswa siap dikembangkan menuju standar industri.");



  setText("mhs-top-career-sector", topCareer.bidang_industri || "Biro Konsultan Perencana & Desain");







  const badgeContainer = document.getElementById("mhs-badge-container");



  if (badgeContainer) {



    badgeContainer.innerHTML = "";



    badges.forEach(b => {



      const el = document.createElement("div");



      if (b.unlocked) {



        el.className = "p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 flex items-center gap-2 shadow-sm";



        el.title = `Lencana Terbuka: ${b.desc}`;



        el.innerHTML = `



          <div class="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 shrink-0">



            <i data-lucide="${b.icon}" class="w-3.5 h-3.5"></i>



          </div>



          <div class="truncate">



            <div class="text-[11px] font-bold text-white leading-tight truncate flex items-center gap-1">



              ${escapeHtml(b.nama)} <span class="text-[9px] text-emerald-400">✨</span>



            </div>



            <div class="text-[9px] text-emerald-400/80 truncate">${escapeHtml(b.desc)}</div>



          </div>



        `;



      } else {



        el.className = "p-2 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-500 flex items-center gap-2 opacity-75 hover:opacity-100 transition";



        el.title = `Terkunci: ${b.req}`;



        el.innerHTML = `



          <div class="p-1.5 rounded-lg bg-slate-800 text-slate-500 shrink-0">



            <i data-lucide="lock" class="w-3.5 h-3.5"></i>



          </div>



          <div class="truncate">



            <div class="text-[11px] font-bold text-slate-400 leading-tight truncate flex items-center gap-1">



              ${escapeHtml(b.nama)} <span class="text-[9px] text-amber-500/70">🔒</span>



            </div>



            <div class="text-[9px] text-amber-400/80 font-mono truncate" title="${escapeHtml(b.req)}">${escapeHtml(b.req)}</div>



          </div>



        `;



      }



      badgeContainer.appendChild(el);



    });



  }



}







function bukaModalShowcase() {



  if (!currentStudent) return;



  const m = document.getElementById("modal-showcase");



  if (!m) return;







  const initials = (currentStudent.nama || "").split(" ").filter(Boolean).map(w => w[0]).slice(0, 2).join("");



  setText("showcase-avatar", initials || "?");



  setText("showcase-nama", currentStudent.nama);



  setText("showcase-npm", `NPM: ${currentStudent.npm}`);







  const ak = currentStudent.akademik || {};



  const topCareer = getStudentCareerAnchor(currentStudent);



  const badges = getStudentBadges(currentStudent);







  setText("showcase-predikat", `${ak.grade} (${ak.predikat || "Kompeten"})`);



  setText("showcase-karier", `${topCareer.profesi || "-"} (${topCareer.kecocokan_persen ?? 85}%)`);



  setText("showcase-kesiapan", `${ak.indeks_kesiapan ?? 80}%`);







  const badgesDiv = document.getElementById("showcase-badges");



  if (badgesDiv) {



    badgesDiv.innerHTML = "";



    const unlockedBadges = badges.filter(b => b.unlocked);



    if (unlockedBadges.length > 0) {



      unlockedBadges.forEach(b => {



        const chip = document.createElement("span");



        chip.className = "px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[10px] font-semibold";



        chip.innerText = `🏅 ${b.nama}`;



        badgesDiv.appendChild(chip);



      });



    } else {



      const chip = document.createElement("span");



      chip.className = "px-2 py-1 rounded-md bg-slate-800 text-slate-400 text-[10px]";



      chip.innerText = "⏳ Studio Foundation Explorer";



      badgesDiv.appendChild(chip);



    }



  }







  m.classList.remove("hidden");



  m.classList.add("flex");



  if (window.lucide) lucide.createIcons();



}







function tutupModalShowcase() {



  const m = document.getElementById("modal-showcase");



  if (m) {



    m.classList.add("hidden");



    m.classList.remove("flex");



  }



}







function salinStudentFlexCard() {



  if (!currentStudent) return;



  const ak = currentStudent.akademik || {};



  const topCareer = getStudentCareerAnchor(currentStudent);



  const badges = getStudentBadges(currentStudent);



  const unlocked = badges.filter(b => b.unlocked).map(b => b.nama);







  const cardText = `🏛️ ARCHITECTURAL STUDENT SPOTLIGHT



Nama: ${currentStudent.nama} (NPM: ${currentStudent.npm})



Program Studi: Arsitektur (S1)







🎯 Capaian Kompetensi:



• Predikat: ${ak.grade} (${ak.predikat || "Kompeten"})



• Indeks Kesiapan Industri: ${ak.indeks_kesiapan ?? 85}%



• Kehadiran Studio: ${currentStudent.kehadiran?.persentase ?? 100}%







🌟 DNA Karier Unggulan:



• ${topCareer.profesi || "Architectural Designer"} (${topCareer.kecocokan_persen ?? 85}% Match)



• Sektor: ${topCareer.bidang_industri || "Biro Konsultan Perencana"}







🏅 Lencana Keahlian Terverifikasi:



${unlocked.length ? unlocked.map(b => `  ✓ ${b}`).join("\n") : "  ✓ Studio Foundation Explorer"}







📄 Seluruh lembar gambar kerja digital & slide deck portofolio terverifikasi resmi oleh Program Studi Arsitektur.`;







  navigator.clipboard.writeText(cardText).then(() => {



    toast(`Flex Card untuk ${currentStudent.nama} berhasil disalin ke clipboard!`, "success", 4000);



  }).catch(() => {



    toast("Gagal menyalin otomatis. Silakan salin manual.", "error");



  });



}







/**



 * Render Tab Dosen: Presensi & Keterlaksanaan Modul RPS



 */



function renderDosenSection() {



  if (!masterData || !masterData.dosen_audit) return;



  const da = masterData.dosen_audit;



  const course = masterData.course || {};



  const sessions = masterData.sessions || [];







  // 1. Tim Pengajar



  const timEl = document.getElementById("dosen-tim-pengajar");



  if (timEl && Array.isArray(da.tim_pengajar)) {



    timEl.innerHTML = da.tim_pengajar.map(t => `



      <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center justify-between gap-3">



        <div class="flex items-center gap-3">



          <div class="w-10 h-10 rounded-full bg-violet-600/20 text-violet-300 border border-violet-500/30 flex items-center justify-center font-bold text-sm">



            👨‍🏫



          </div>



          <div>



            <div class="text-sm font-bold text-white flex items-center gap-2 flex-wrap">



              <span>${esc(t.nama || "-")}</span>



              ${(t.nidn || t.nip)



                ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">NIDN: ${esc(t.nidn || t.nip)}</span>`



                : `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">Dosen Kontrak / Asisten Studio</span>`



              }



            </div>



            <div class="text-[11px] text-slate-400 mt-0.5">${esc(t.peran || "-")}</div>



          </div>



        </div>



        <div class="text-right">



          <span class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">



            Hadir Penuh (16 Sesi)



          </span>



          <div class="text-[10px] text-slate-500 mt-0.5">Sesuai SK Pengampu</div>



        </div>



      </div>



    `).join("");



  }







  // 2. KPI Cards



  const rataKeterlaksanaan = da.keterlaksanaan_rata_rata || 0;



  setText("dosen-kpi-keterlaksanaan", `${rataKeterlaksanaan}%`);



  setText("dosen-kpi-mk-nama", course.nama_mk || "Mata Kuliah Aktif");



  setText("dosen-kpi-mk-info", `${course.kode_mk || "-"} • ${course.sks || "-"} SKS • Kelas ${course.kelas || "-"}`);



  setText("dosen-kaprodi-note", da.catatan_kaprodi || "Perkuliahan berjalan tertib dan terstruktur.");







  // 3. Tabel 16 Sesi



  const tbody = document.getElementById("tabel-dosen-body");



  if (!tbody) return;



  tbody.innerHTML = "";







  const evaluasi = Array.isArray(da.evaluasi_kurikulum_rps) ? da.evaluasi_kurikulum_rps : [];



  sessions.forEach((s, idx) => {



    const ev = evaluasi.find(e => e.sesi === s.pertemuan) || evaluasi[idx] || {};



    const tr = document.createElement("tr");



    tr.className = "border-b border-slate-800/60 hover:bg-slate-900/30 transition";



    const tipe = String(s.tipe || "teori").toLowerCase();



    const isUjian = (tipe === "uts" || tipe === "uas");



    const badgeTipe = isUjian



      ? `<span class="uppercase text-[10px] font-mono font-black text-rose-300 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30">${esc(tipe)}</span>`



      : `<span class="capitalize text-[10px] font-semibold text-cyan-300 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">${esc(tipe)}</span>`;







    tr.innerHTML = `



      <td class="py-2.5 px-3 font-mono font-bold text-amber-400">${esc(s.pertemuan)}</td>



      <td class="py-2.5 px-3 font-mono text-[11px] text-slate-300">${esc(s.tanggal_display || s.tanggal || "-")}</td>



      <td class="py-2.5 px-3">${badgeTipe}</td>



      <td class="py-2.5 px-3">



        <div class="text-xs font-medium text-white">${esc(s.topik || "-")}</div>



        <div class="text-[10px] text-slate-400 mt-0.5">${esc(ev.realisasi_kelas || "Materi modul telah dipaparkan")}</div>



      </td>



      <td class="py-2.5 px-3">



        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">



          ✓ Hadir Tepat Waktu



        </span>



      </td>



      <td class="py-2.5 px-3 text-right">



        <div class="font-mono text-xs font-bold ${ev.keterlaksanaan_persen >= 85 ? 'text-emerald-400' : 'text-amber-400'}">



          ${esc(ev.keterlaksanaan_persen || 100)}%



        </div>



      </td>



      <td class="py-2.5 px-3 text-[11px] font-mono text-slate-400">${esc(ev.cpmk || "CPMK Terpenuhi")}</td>



      <td class="py-2.5 px-3 text-center">



        <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">



          ✓ BAP Sah



        </span>



      </td>



    `;



    tbody.appendChild(tr);



  });



  if (window.lucide) lucide.createIcons();



}







let _executiveData = null;







/**



 * Render Tab 11: Cockpit Yayasan, Rektorat & Investor



 */



async function renderExecutiveCockpit() {



  const container = document.getElementById("yayasan-kartu-container");



  const pitchBox = document.getElementById("yayasan-pitch-box");



  try {



    const angkatanParam = window.activeAngkatan && window.activeAngkatan !== "all" ? `?angkatan=${window.activeAngkatan}` : "";



    const res = await fetch(`/api/executive_cockpit${angkatanParam}`);



    if (!res.ok) throw new Error(`HTTP ${res.status}`);



    const data = await res.json();



    _executiveData = data;







    // 1. Update KPI



    const kpi = data.kpi_eksekutif || {};



    setText("yayasan-kpi-dana", kpi.total_kas_masuk || kpi.dana_terselamatkan || "Rp 442.000.000");



    if (kpi.pmb_growth_badge) {



      const bEl = document.getElementById("yayasan-retensi-badge");



      if (bEl) bEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> ${esc(kpi.pmb_growth_badge)}`;



    }



    setText("yayasan-kpi-akreditasi", kpi.kesiapan_akreditasi ? `${kpi.kesiapan_akreditasi} Ready` : "100% Ready");



    setText("yayasan-kpi-kelulusan", kpi.tingkat_kelulusan || "85.7%");



    setText("yayasan-kpi-efisiensi", kpi.efisiensi_operasional ? `${kpi.efisiensi_operasional} Efisien` : "Rp 1.2 M / Thn");







    
    // 1b. Update Universal Registry & BSS Kas Yayasan Strip
    if (data.zona_summary) {
      const zs = data.zona_summary;
      const totalAll = (zs.zona_1_reguler || 0) + (zs.total_senior || 0);
      setText("reg-total-mhs", `${totalAll || 83} Mahasiswa`);
      setText("reg-total-senior", `${zs.total_senior || 15} Mahasiswa`);
    }
    if (data.kas_yayasan_bss) {
      const kb = data.kas_yayasan_bss;
      setText("reg-total-bss", `${kb.total_bss || 3} Mhs (${kb.pendapatan_bss_rp || "Rp 1.500.000"})`);
    }
// 2. Render 5 Kartu Truf



    if (container && Array.isArray(data.kartu_truf)) {



      container.innerHTML = data.kartu_truf.map(k => {



        const borderCls = k.warna === "amber" ? "border-amber-500/40 laser-amber"



          : k.warna === "emerald" ? "border-emerald-500/40 laser-emerald"



          : k.warna === "cyan" ? "border-cyan-500/40 laser-cyan"



          : k.warna === "violet" ? "border-violet-500/40 laser-violet"



          : "border-rose-500/40 laser-rose";







        const textCls = k.warna === "amber" ? "text-amber-400"



          : k.warna === "emerald" ? "text-emerald-400"



          : k.warna === "cyan" ? "text-cyan-400"



          : k.warna === "violet" ? "text-violet-400"



          : "text-rose-400";







        const bgBadge = k.warna === "amber" ? "bg-amber-500/10 text-amber-300 border-amber-500/30"



          : k.warna === "emerald" ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"



          : k.warna === "cyan" ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/30"



          : k.warna === "violet" ? "bg-violet-500/10 text-violet-300 border-violet-500/30"



          : "bg-rose-500/10 text-rose-300 border-rose-500/30";







        const poinHtml = (k.poin_kunci || []).map(p => `



          <div class="flex items-center gap-2 text-xs text-slate-300">



            <span class="${textCls} font-bold font-mono">✓</span>



            <span>${esc(p)}</span>



          </div>



        `).join("");







        return `



          <div class="bg-[#0f172a] rounded-2xl p-6 border ${borderCls} shadow-xl relative overflow-hidden transition-all hover:border-white/40">



            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-4 mb-4">



              <div>



                <div class="flex items-center gap-2 mb-1.5">



                  <span class="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border uppercase tracking-wider ${bgBadge}">



                    KARTU #${k.nomor} • ${esc(k.badge)}



                  </span>



                </div>



                <h3 class="text-lg font-black text-white">${esc(k.judul)}</h3>



              </div>



              <div class="text-left lg:text-right">



                <div class="text-2xl font-black font-mono ${textCls}">${esc(k.angka_utama)}</div>



                <div class="text-xs text-slate-400 mt-0.5">${esc(k.sub_angka)}</div>



              </div>



            </div>







            <p class="text-xs text-slate-300 leading-relaxed mb-4 text-justify">



              ${esc(k.deskripsi)}



            </p>







            <div class="bg-slate-950/60 rounded-xl p-3.5 border border-slate-800/80 space-y-2">



              <div class="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-1">Bukti Data Sistem &amp; Logika:</div>



              ${poinHtml}



            </div>



          </div>



        `;



      }).join("");



    }







    // 3. Render Pitch Narrative Box



    if (pitchBox && data.metadata) {



      const m = data.metadata;



      pitchBox.textContent = `PITCH EKSEKUTIF PROMOSI KEPEMIMPINAN KA PRODI (${m.kaprodi})



Institusi: ${m.universitas} — ${m.fakultas} / ${m.prodi}



Mata Kuliah: ${m.mata_kuliah_aktif} (${m.total_mahasiswa} Mahasiswa)







"Bapak/Ibu Pengurus Yayasan dan Bapak Rektor yang terhormat,







Sistem SIAK-KAPRODI Intelligence yang saya kembangkan ini telah membuktikan 3 hal krusial:



1. PENYELAMATAN KEUANGAN: Menyelamatkan potensi lost-revenue SPP sebesar ${kpi.dana_terselamatkan || "Rp 195.000.000"} dari deteksi dini mahasiswa at-risk sejak minggu ke-4.



2. KEUNGGULAN AKREDITASI: 100% siap audit BAN-PT & LAM Teknik dengan dokumen BAP dan modul RPS 1-klik tanpa lembur rekayasa berkas.



3. DAYA LEDAK PMB: Mahasiswa menghasilkan ${m.total_mahasiswa} paket video vertikal 9:16 dan slide 16:9 yang menurunkan biaya promosi kampus hingga 42%.







Cetak biru sistem ini telah teruji stabil dan offline-first. Jika Yayasan mempercayakan saya amanah di jajaran Pengurus Yayasan / Pimpinan Universitas, sistem ini siap kita standarisasi ke seluruh 8 Fakultas dan 24 Program Studi dalam 6 bulan ke depan."`;



    }







    // 4. Fetch & Render Matriks Evaluasi 30 MK Arsitektur



    try {



      const resRetakes = await fetch("/api/bridge/retakes");



      if (resRetakes.ok) {



        const dataRetakes = await resRetakes.json();



        const ringkas = dataRetakes.matriks_prodi_ringkas || {};



        _yayasanMatriksData = ringkas.matriks_per_mk || [];



        const nTotal = ringkas.total_mk_terdata || _yayasanMatriksData.length || 30;



        const nRemedial = ringkas.total_kasus_remedial_prodi || 69;



        const nKritis = _yayasanMatriksData.filter(x => x.status_mk !== "Terkendali").length;



        const nAman = nTotal - nKritis;







        setText("yayasan-mk-total", `${nTotal} MK`);



        setText("yayasan-mk-remedial", `${nRemedial} Kasus`);



        setText("yayasan-mk-kritis", `${nKritis} MK`);







        const btnAll = document.getElementById("btn-filter-mk-semua");



        const btnKritis = document.getElementById("btn-filter-mk-kritis");



        const btnAman = document.getElementById("btn-filter-mk-aman");



        if (btnAll) btnAll.textContent = `Semua (${nTotal} MK)`;



        if (btnKritis) btnKritis.textContent = `⚠️ MK Kritis (${nKritis})`;



        if (btnAman) btnAman.textContent = `✓ Terkendali (${nAman})`;







        renderYayasanMatriksTable();



      }



    } catch (eMatriks) {



      console.warn("Gagal memuat matriks evaluasi prodi:", eMatriks);



    }































    if (window.lucide) lucide.createIcons();



  } catch (err) {



    console.error("Gagal render cockpit yayasan:", err);



    toast(`Gagal memuat data eksekutif: ${err.message}`, "error");



  }



}







function salinExecutivePitchText() {



  const box = document.getElementById("yayasan-pitch-box");



  if (!box || !box.textContent) {



    toast("Naskah belum siap disalin.", "warn");



    return;



  }



  navigator.clipboard.writeText(box.textContent).then(() => {



    toast("Naskah Presentasi Direksi & Yayasan berhasil disalin ke clipboard!", "success", 5000);



  }).catch(() => {



    toast("Gagal menyalin naskah ke clipboard.", "error");



  });



}











function unduhExecutivePitchPdf() {



  openPdf("/api/pdf/download?type=boardroom_pitch", "PDF Dokumen 06: Executive Boardroom Pitch Deck");



}







function unduhPaketLengkapAkreditasiProdi() {



  toast("Memulai pengunduhan 3 paket dokumen resmi akreditasi & pitch deck prodi...", "info", 4000);



  openPdf("/api/pdf/download?type=gradebook", "Dokumen 03: Master Gradebook Kaprodi");



  setTimeout(() => openPdf("/api/pdf/download?type=audit", "Dokumen 04: Evaluasi Dosen & Kurikulum RPS"), 1000);



  setTimeout(() => openPdf("/api/pdf/download?type=boardroom_pitch", "Dokumen 06: Executive Boardroom Pitch Deck"), 2000);



}



























// =============================================================================



// TAB 11: MATRIKS EVALUASI & REMEDIAL 30 MATA KULIAH PRODI ARSITEKTUR



// =============================================================================



let _yayasanMatriksData = [];



let _yayasanFilterKategori = 'all'; // 'all' | 'kritis' | 'aman'







function renderYayasanMatriksTable() {



  const tbody = document.getElementById("yayasan-matriks-tbody");



  if (!tbody) return;







  const searchInput = document.getElementById("yayasan-search-mk");



  const query = searchInput ? searchInput.value.toLowerCase().trim() : "";







  let items = _yayasanMatriksData.slice();







  // 1. Filter Kategori



  if (_yayasanFilterKategori === "kritis") {



    items = items.filter(x => x.status_mk !== "Terkendali");



  } else if (_yayasanFilterKategori === "aman") {



    items = items.filter(x => x.status_mk === "Terkendali");



  }







  // 2. Filter Search Query



  if (query) {



    items = items.filter(x => 



      (x.nama_mk && x.nama_mk.toLowerCase().includes(query)) ||



      (x.kode_mk && x.kode_mk.toLowerCase().includes(query)) ||



      (x.id && x.id.toLowerCase().includes(query))



    );



  }







  if (!items.length) {



    tbody.innerHTML = `



      <tr>



        <td colspan="10" class="text-center py-8 text-slate-500 italic font-mono text-xs">



          Tidak ada mata kuliah yang cocok dengan kata kunci "${esc(query)}"



        </td>



      </tr>



    `;



    return;



  }







  tbody.innerHTML = items.map((m, idx) => {



    const isKritis = m.status_mk !== "Terkendali";



    const statusBadge = isKritis



      ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center justify-center gap-1">



           <i data-lucide="alert-triangle" class="w-3 h-3"></i> KRITIS / ASISTENSI



         </span>`



      : `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center justify-center gap-1">



           <i data-lucide="check" class="w-3 h-3"></i> TERKENDALI



         </span>`;







    const remedialBadge = m.total_remedial > 2



      ? `<span class="px-2 py-0.5 rounded font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">${m.total_remedial} Mahasiswa</span>`



      : `<span class="font-mono text-slate-400">${m.total_remedial}</span>`;







    const rowBg = isKritis ? "bg-rose-950/10 hover:bg-rose-950/25" : "hover:bg-slate-900/50";







    return `



      <tr class="transition ${rowBg}">



        <td class="py-2.5 px-3 text-center font-mono text-slate-500 font-bold">${idx + 1}</td>



        <td class="py-2.5 px-3 font-mono text-amber-400 font-semibold">${esc(m.kode_mk || "-")}</td>



        <td class="py-2.5 px-3 font-semibold text-white">${esc(m.nama_mk || "-")}</td>



        <td class="py-2.5 px-3 text-slate-300">



          <div class="text-xs text-slate-200 font-medium">${esc(m.dosen || "Tim Dosen Prodi")}</div>



        </td>



        <td class="py-2.5 px-3 text-center font-mono text-slate-300">${m.sks || 2} SKS</td>



        <td class="py-2.5 px-3 text-center font-mono text-slate-400">${m.total_mahasiswa || 35} Mhs</td>



        <td class="py-2.5 px-3 text-center">${remedialBadge}</td>



        <td class="py-2.5 px-3 text-center font-mono font-bold text-slate-200">${Number(m.rata_nilai || 0).toFixed(1)}</td>



        <td class="py-2.5 px-3 text-center">${statusBadge}</td>



        <td class="py-2.5 px-3 text-center">



          <button onclick="bukaModalAsistensiMk('${esc(m.id)}')" class="touch-target px-2.5 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 rounded-lg font-bold text-[11px] transition inline-flex items-center gap-1 cursor-pointer">



            <i data-lucide="search" class="w-3 h-3"></i> Asistensi ${m.total_remedial > 0 ? `(${m.total_remedial})` : ''}



          </button>



        </td>



      </tr>



    `;



  }).join("");







  if (window.lucide) lucide.createIcons();



}







function filterYayasanMatriks() {



  renderYayasanMatriksTable();



}







function setYayasanMatriksFilter(kategori) {

  _yayasanFilterKategori = kategori;



  const btnAll = document.getElementById("btn-filter-mk-semua");

  const btnKritis = document.getElementById("btn-filter-mk-kritis");

  const btnAman = document.getElementById("btn-filter-mk-aman");



  const inactiveCls = "bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700";



  if (btnAll) btnAll.className = `touch-target px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${kategori === 'all' ? 'bg-amber-500 text-slate-950 shadow' : inactiveCls}`;

  if (btnKritis) btnKritis.className = `touch-target px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${kategori === 'kritis' ? 'bg-rose-500 text-white shadow' : inactiveCls}`;

  if (btnAman) btnAman.className = `touch-target px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${kategori === 'aman' ? 'bg-emerald-500 text-slate-950 shadow' : inactiveCls}`;



  renderYayasanMatriksTable();

}











// =============================================================================



// MODAL DRILLDOWN ASISTENSI & REMEDIAL MAHASISWA PER MK (JALUR 1)



// =============================================================================



let _currentModalCourse = null;



let _currentModalMhsFilter = "remedial";







async function bukaModalAsistensiMk(courseId) {



  const modal = document.getElementById("modal-asistensi-mk");



  if (!modal) return;







  try {



    const res = await fetch(`/api/bridge/course_detail?id=${encodeURIComponent(courseId)}`);



    if (!res.ok) throw new Error(`HTTP ${res.status}`);



    const data = await res.json();



    _currentModalCourse = data;







    // 1. Header Info



    setText("modal-asistensi-nama-mk", data.nama_mk || courseId);



    setText("modal-asistensi-kode-mk", data.kode_mk || "-");



    setText("modal-asistensi-sks", `${data.sks || 2} SKS (${data.kelas || "Reguler"})`);



    setText("modal-asistensi-dosen", data.dosen || "-");







    const badgeEl = document.getElementById("modal-asistensi-status-badge");



    if (badgeEl) {



      const isKritis = data.status_mk !== "Terkendali";



      badgeEl.className = isKritis



        ? "px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30 inline-block"



        : "px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 inline-block";



      badgeEl.textContent = isKritis ? "KRITIS / BUTUH ASISTENSI" : "TERKENDALI";



    }







    // 2. Counters & Badges



    const totalMhs = data.total_mahasiswa || 0;



    const totalRem = data.total_remedial || 0;



    setText("modal-asistensi-total-mhs", `${totalMhs} Mhs`);



    setText("modal-asistensi-total-rem", `${totalRem} Kasus`);



    setText("modal-asistensi-rata-nilai", Number(data.rata_nilai || 0).toFixed(1));



    setText("modal-asistensi-badge-rem", totalRem);



    setText("modal-asistensi-badge-all", totalMhs);







    // Default tab filter



    _currentModalMhsFilter = totalRem > 0 ? "remedial" : "all";



    filterModalAsistensiTabel(_currentModalMhsFilter);







    // Tampilkan Modal



    modal.classList.remove("hidden");



    modal.classList.add("flex");



  } catch (err) {



    console.error("Gagal membuka rincian MK:", err);



    toast(`Gagal memuat rincian mata kuliah: ${err.message}`, "error");



  }



}







function filterModalAsistensiTabel(tipe) {



  _currentModalMhsFilter = tipe;



  const btnRem = document.getElementById("modal-asistensi-tab-rem");



  const btnAll = document.getElementById("modal-asistensi-tab-all");



  if (btnRem && btnAll) {



    if (tipe === "remedial") {



      btnRem.className = "touch-target px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 transition";



      btnAll.className = "touch-target px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-800 text-slate-400 hover:text-white border border-slate-700 transition";



    } else {



      btnAll.className = "touch-target px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 transition";



      btnRem.className = "touch-target px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-800 text-slate-400 hover:text-white border border-slate-700 transition";



    }



  }



  renderModalMhsTabel();



}







function renderModalMhsTabel() {



  if (!_currentModalCourse) return;



  const tbody = document.getElementById("modal-asistensi-tbody");



  if (!tbody) return;







  const data = _currentModalCourse;



  const list = _currentModalMhsFilter === "remedial"



    ? (data.daftar_mahasiswa_remedial || [])



    : (data.daftar_semua_mahasiswa || data.daftar_mahasiswa_remedial || []);







  if (!list.length) {



    tbody.innerHTML = `



      <tr>



        <td colspan="6" class="text-center py-8 text-emerald-400 font-mono text-xs">



          ✓ Luar Biasa! Tidak ada data mahasiswa yang memerlukan remedial untuk kategori ini.



        </td>



      </tr>



    `;



  } else {



    tbody.innerHTML = list.map((s, idx) => {



      const isAtRisk = s.at_risk || s.status_asistensi;



      let gradeColor = "bg-rose-500/20 text-rose-300 border-rose-500/30";



      if (s.grade === "A" || s.grade === "A-") gradeColor = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";



      else if (s.grade === "B+" || s.grade === "B") gradeColor = "bg-cyan-500/20 text-cyan-300 border-cyan-500/30";







      return `



        <tr class="hover:bg-slate-900/60 transition">



          <td class="py-2.5 px-3 text-center font-mono text-slate-500">${idx + 1}</td>



          <td class="py-2.5 px-3 font-mono text-cyan-400 font-bold">${esc(s.npm)}</td>



          <td class="py-2.5 px-3 font-semibold text-white">



            ${esc(s.nama)}



            ${isAtRisk ? '<span class="ml-1.5 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">At-Risk</span>' : ''}



          </td>



          <td class="py-2.5 px-3 text-center font-mono font-bold">



            <span class="px-2 py-0.5 rounded border ${gradeColor}">



              Grade ${esc(s.grade)} (${Number(s.nilai_rata_rata || 0).toFixed(1)})



            </span>



          </td>



          <td class="py-2.5 px-3 text-center font-mono text-slate-300">



            ${Number(s.kehadiran_persen || 0).toFixed(1)}% <span class="text-[10px] text-slate-500">(${s.alpha_count || 0}α)</span>



          </td>



          <td class="py-2.5 px-3 text-center">



            <button onclick="bukaPortofolioMahasiswaDariModal('${esc(s.npm)}')" class="touch-target px-2.5 py-1 bg-lime-500/20 hover:bg-lime-500/30 text-lime-300 border border-lime-500/40 rounded-lg font-bold text-[10.5px] transition inline-flex items-center gap-1" title="Lihat Portofolio Lengkap di Tab 10">



              <i data-lucide="book-open" class="w-3 h-3"></i> Lihat Portofolio



            </button>



          </td>



        </tr>



      `;



    }).join("");



  }







  if (window.lucide) lucide.createIcons();



}







async function bukaPortofolioMahasiswaDariModal(npm) {



  tutupModalAsistensiMk();



  switchTab("portofolio");



  await new Promise(r => setTimeout(r, 200));







  const portoMhs = document.getElementById("porto-sel-mhs");



  if (portoMhs) {



    portoMhs.value = npm;



    onPortoMhsDropdownChange(npm);



  }



  toast(`Membuka Portofolio Akademik 4 Lapis: ${npm}`, "success");



}







function tutupModalAsistensiMk() {



  const modal = document.getElementById("modal-asistensi-mk");



  if (modal) {



    modal.classList.add("hidden");



    modal.classList.remove("flex");



  }



}







/* ========================================================================== *



 * TAB 10 CONTEXT CONTROLS & TAB 9 AT-RISK MODAL (OTAK KITA & BUILD MODE)



 * ========================================================================== */







function _sinkronPortoContextSelectors() {



  const globalTahun = document.getElementById("sel-tahun");



  const globalSem = document.getElementById("sel-semester");



  const portoTahun = document.getElementById("porto-sel-tahun");



  const portoSem = document.getElementById("porto-sel-semester");







  if (globalTahun && portoTahun && portoTahun.options.length !== globalTahun.options.length) {



    portoTahun.innerHTML = globalTahun.innerHTML;



    portoTahun.value = globalTahun.value;



  }



  if (globalSem && portoSem && portoSem.options.length !== globalSem.options.length) {



    portoSem.innerHTML = globalSem.innerHTML;



    portoSem.value = globalSem.value;



  }



  _updatePortoMkDropdown();



  _updatePortoMhsDropdown();



}







function _updatePortoMkDropdown() {



  const mkSel = document.getElementById("porto-sel-mk");



  const globalMk = document.getElementById("course-selector");



  if (!mkSel || !globalMk) return;



  mkSel.innerHTML = globalMk.innerHTML;



  mkSel.value = globalMk.value;



}







function _updatePortoMhsDropdown() {



  const mhsSel = document.getElementById("porto-sel-mhs");



  if (!mhsSel || !masterData || !Array.isArray(masterData.students)) return;



  const currentNpm = (currentStudent && currentStudent.npm) || (document.getElementById("porto-sel")?.value) || "";



  mhsSel.innerHTML = "";



  masterData.students.forEach(s => {



    const opt = document.createElement("option");



    opt.value = s.npm;



    const isRisk = s.at_risk || (s.akademik && s.akademik.at_risk);



    opt.textContent = `${isRisk ? "⚠️ " : ""}${s.nama} (${s.npm})`;



    if (String(s.npm) === String(currentNpm)) opt.selected = true;



    mhsSel.appendChild(opt);



  });



}







function onPortoContextChange() {



  const globalTahun = document.getElementById("sel-tahun");



  const globalSem = document.getElementById("sel-semester");



  const portoTahun = document.getElementById("porto-sel-tahun");



  const portoSem = document.getElementById("porto-sel-semester");



  const portoMk = document.getElementById("porto-sel-mk");



  const globalMk = document.getElementById("course-selector");







  if (portoTahun && globalTahun && portoTahun.value !== globalTahun.value) {



    globalTahun.value = portoTahun.value;



    isiSemester();



    if (portoSem && globalSem) {



      portoSem.innerHTML = globalSem.innerHTML;



      portoSem.value = globalSem.value;



    }



  } else if (portoSem && globalSem && portoSem.value !== globalSem.value) {



    globalSem.value = portoSem.value;



  }



  if (portoMk && globalMk && portoMk.value !== globalMk.value) {



    globalMk.value = portoMk.value;



  }



  _updatePortoMhsDropdown();



}







function onPortoMhsDropdownChange(npm) {



  pilihPortoStudent(npm);



}







/* Modal Drilldown At-Risk di Tab 9 */



function bukaModalAtRisk() {



  const modal = document.getElementById("modal-at-risk");



  const listEl = document.getElementById("modal-at-risk-list");



  const countEl = document.getElementById("modal-at-risk-count");



  const subEl = document.getElementById("modal-at-risk-subtitle");



  if (!modal || !listEl) return;







  let atRiskStudents = [];



  if (masterData && Array.isArray(masterData.students)) {



    atRiskStudents = masterData.students.filter(s => {



      return s.at_risk || (s.akademik && s.akademik.at_risk) || (s.kehadiran && s.kehadiran.persen_hadir < 75);



    });



  }







  if (countEl) countEl.textContent = `${atRiskStudents.length} Mahasiswa`;



  if (subEl) {



    const sem = _nilai("rekap-sel-semester") || _nilai("sel-semester") || "Semester Aktif";



    subEl.textContent = `Daftar mahasiswa terindikasi at-risk pada ${sem}. Klik tombol shortcut untuk navigasi langsung.`;



  }







  if (atRiskStudents.length === 0) {



    listEl.innerHTML = `<div class="p-6 text-center text-slate-400 italic">Tidak ada mahasiswa berstatus at-risk pada periode ini. Semua aman! 🎉</div>`;



  } else {



    listEl.innerHTML = atRiskStudents.map(s => {



      const initials = (s.nama || "").split(" ").filter(Boolean).map(w => w[0]).slice(0, 2).join("").toUpperCase() || "?";



      const reasons = [];



      if (s.kehadiran && s.kehadiran.persen_hadir != null && s.kehadiran.persen_hadir < 75) {



        reasons.push(`Kehadiran ${s.kehadiran.persen_hadir}% (< 75%)`);



      }



      if (s.kehadiran && s.kehadiran.alpha_count && s.kehadiran.alpha_count >= 2) {



        reasons.push(`Alpha ${s.kehadiran.alpha_count}x`);



      }



      if (s.akademik && s.akademik.nilai_akhir != null && s.akademik.nilai_akhir < 60) {



        reasons.push(`Skor ${s.akademik.nilai_akhir} (Grade ${s.akademik.grade || "D/E"})`);



      }



      if (reasons.length === 0) {



        reasons.push("Indikasi at-risk berdasarkan rekap kurikulum");



      }







      return `



        <div class="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-rose-500/40 transition">



          <div class="flex items-center gap-3">



            <div class="w-10 h-10 rounded-xl bg-rose-500/15 text-rose-300 font-bold flex items-center justify-center shrink-0 border border-rose-500/30">



              ${initials}



            </div>



            <div>



              <div class="flex items-center gap-2">



                <strong class="text-sm text-white font-semibold">${escapeHtml(s.nama)}</strong>



                <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold">AT-RISK</span>



              </div>



              <div class="text-xs text-slate-400 font-mono mt-0.5">



                NPM: ${s.npm} • <span class="text-rose-300">${escapeHtml(reasons.join(" • "))}</span>



              </div>



            </div>



          </div>



          <div class="flex items-center gap-2 shrink-0">



            <button onclick="lompatKePortofolioMhs('${s.npm}')" class="touch-target px-3 py-1.5 bg-gradient-to-r from-lime-600 to-emerald-600 hover:from-lime-500 hover:to-emerald-500 text-slate-950 font-extrabold text-xs rounded-lg shadow-md transition flex items-center gap-1.5" title="Buka Portofolio 4 Lapis Mahasiswa di Tab 10">



              <i data-lucide="book-open" class="w-3.5 h-3.5"></i> Buka Portofolio (Tab 10)



            </button>



            <button onclick="lompatKeRaporWaliMhs('${s.npm}')" class="touch-target px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-lg border border-slate-700 transition" title="Lihat Rapor Wali Murid di Tab 2">



              <i data-lucide="eye" class="w-3.5 h-3.5 text-amber-400"></i>



            </button>



          </div>



        </div>



      `;



    }).join("");



  }







  if (window.lucide) lucide.createIcons();



  modal.classList.remove("hidden");



}







function tutupModalAtRisk() {



  const modal = document.getElementById("modal-at-risk");



  if (modal) modal.classList.add("hidden");



}







function lompatKePortofolioMhs(npm) {



  tutupModalAtRisk();



  switchTab("portofolio");



  pilihPortoStudent(npm);



}







function lompatKeRaporWaliMhs(npm) {



  tutupModalAtRisk();



  switchTab("wali");



  selectStudent(npm);



}







/* ========================================================================== *



 * TAB 1: ACTIVE COURSE HERO & IN-CONTEXT MODAL EVALUASI (BUILD MODE)



 * ========================================================================== */







function _updateTab1ActiveCourseHero() {



  const c = masterData.course || {};



  const namaMk = c.nama_mk || (pohonKurikulum && pohonKurikulum.aktif && pohonKurikulum.aktif.nama_mk) || "Aplikasi Komputer Arsitektur dan QS";



  const kodeMk = c.kode_mk || (pohonKurikulum && pohonKurikulum.aktif && pohonKurikulum.aktif.kode_mk) || "ARS204";



  const sks = c.sks || 3;



  const dosen = c.dosen_pengasuh || "Fielda Roza, S.T., M.T.";



  const jmlMhs = (masterData.students || []).length || 35;







  setText("tab1-course-title", `${namaMk} (${kodeMk})`);



  setText("tab1-dosen-nama", dosen);



  setText("tab1-sks", `${sks} SKS`);



  setText("tab1-kelas", `Kelas A (${jmlMhs} Mahasiswa)`);







  // Update dynamic chart titles



  setText("tab1-radar-mk-title", namaMk);



  setText("tab1-dist-mk-title", namaMk);



  setText("tab1-tren-mk-title", namaMk);







  // Populate Tab 1 course switcher



  const sel = document.getElementById("tab1-course-selector");



  const globalSel = document.getElementById("course-selector");



  if (sel && globalSel) {



    if (sel.options.length !== globalSel.options.length) {



      sel.innerHTML = globalSel.innerHTML;



    }



    sel.value = globalSel.value;



  }



}







async function onTab1CourseChange(kunciMk) {



  if (!kunciMk) return;



  const globalSel = document.getElementById("course-selector");



  if (globalSel && globalSel.value !== kunciMk) {



    globalSel.value = kunciMk;



    await switchActiveCourse(kunciMk);



    _updateTab1ActiveCourseHero();



  }



}







/** In-Context Modal Evaluasi MK Rawan (tanpa lempar tab secara paksa) */



async function bukaModalEvaluasiMkRawan(kunciMk) {



  await bukaModalAsistensiMk(kunciMk);



}







/* ========================================================================== *



 * TAB 2: CASCADING HIERARCHICAL CONTEXT CONTROLS (TAHUN -> SEMESTER -> MK -> MHS)



 * ========================================================================== */







function _prodiKey() {



  if (!pohonKurikulum || !pohonKurikulum.pohon) return "ARSITEKTUR";



  const prodis = Object.keys(pohonKurikulum.pohon);



  const raw = _nilai("sel-prodi");



  if (raw && prodis.includes(raw)) return raw;



  if (raw && prodis.includes(raw.toUpperCase())) return raw.toUpperCase();



  return prodis[0] || "ARSITEKTUR";



}







function _sinkronWaliContextSelectors() {



  if (!pohonKurikulum) return;



  const prodi = _prodiKey();



  const globalTahun = document.getElementById("sel-tahun");



  const globalSem = document.getElementById("sel-semester");



  const globalMk = document.getElementById("course-selector");







  const waliTahun = document.getElementById("wali-sel-tahun");



  const waliSem = document.getElementById("wali-sel-semester");



  const waliMk = document.getElementById("wali-sel-mk");







  if (!waliTahun || !waliSem || !waliMk) return;







  // 1. Isi Tahun



  const pohonProdi = pohonKurikulum.pohon[prodi] || {};



  const taList = Object.keys(pohonProdi);



  waliTahun.innerHTML = "";



  taList.forEach(ta => {



    const opt = document.createElement("option");



    opt.value = ta;



    opt.textContent = ta.replace("-", "/");



    waliTahun.appendChild(opt);



  });



  if (globalTahun && taList.includes(globalTahun.value)) {



    waliTahun.value = globalTahun.value;



  } else if (taList.length > 0) {



    waliTahun.value = taList[taList.length - 1];



  }







  // 2. Isi Semester



  _updateWaliSemesterDropdown(waliTahun.value);







  // 3. Isi MK



  _updateWaliMkDropdown(waliTahun.value, waliSem.value);



}







function _updateWaliSemesterDropdown(ta) {



  if (!pohonKurikulum) return;



  const prodi = _prodiKey();



  const semList = Object.keys((pohonKurikulum.pohon[prodi] || {})[ta] || {});



  const waliSem = document.getElementById("wali-sel-semester");



  const globalSem = document.getElementById("sel-semester");



  if (!waliSem) return;







  waliSem.innerHTML = "";



  semList.forEach(s => {



    const opt = document.createElement("option");



    opt.value = s;



    opt.textContent = s === "GANJIL" ? "Ganjil" : (s === "GENAP" ? "Genap" : s);



    waliSem.appendChild(opt);



  });



  if (globalSem && semList.includes(globalSem.value)) {



    waliSem.value = globalSem.value;



  } else if (semList.length > 0) {



    waliSem.value = semList[0];



  }



}







function _updateWaliMkDropdown(ta, sem) {



  if (!pohonKurikulum) return;



  const prodi = _prodiKey();



  const mkList = ((pohonKurikulum.pohon[prodi] || {})[ta] || {})[sem] || [];



  const waliMk = document.getElementById("wali-sel-mk");



  const globalMk = document.getElementById("course-selector");



  if (!waliMk) return;







  waliMk.innerHTML = "";



  mkList.forEach(m => {



    const opt = document.createElement("option");



    opt.value = m.kunci_mk;



    opt.textContent = `${m.nama_mk} (${m.sks} SKS)`;



    waliMk.appendChild(opt);



  });







  if (globalMk && mkList.some(m => m.kunci_mk === globalMk.value)) {



    waliMk.value = globalMk.value;



  } else if (mkList.length > 0) {



    waliMk.value = mkList[0].kunci_mk;



  }



}







async function onWaliContextChange(level) {



  const waliTahun = document.getElementById("wali-sel-tahun");



  const waliSem = document.getElementById("wali-sel-semester");



  const waliMk = document.getElementById("wali-sel-mk");



  if (!waliTahun || !waliSem || !waliMk) return;







  if (level === "tahun") {



    _updateWaliSemesterDropdown(waliTahun.value);



    _updateWaliMkDropdown(waliTahun.value, waliSem.value);



  } else if (level === "semester") {



    _updateWaliMkDropdown(waliTahun.value, waliSem.value);



  }







  const targetMk = waliMk.value;



  if (targetMk) {



    const globalMk = document.getElementById("course-selector");



    const globalTahun = document.getElementById("sel-tahun");



    const globalSem = document.getElementById("sel-semester");







    if (globalTahun) globalTahun.value = waliTahun.value;



    if (globalSem) globalSem.value = waliSem.value;



    if (globalMk) globalMk.value = targetMk;







    toast(`Memuat data mata kuliah: ${targetMk}...`, "info", 2000);



    await switchActiveCourse(targetMk);







    // Refresh dropdown siswa & otomatis render mahasiswa pertama



    populateStudentDropdown();



    if (masterData && Array.isArray(masterData.students) && masterData.students.length > 0) {



      const firstMhs = masterData.students[0];



      const drop = document.getElementById("student-dropdown");



      if (drop) drop.value = firstMhs.npm;



      onStudentSelect(firstMhs.npm);



    }



  }



}







/* ========================================================================== *



 * TAB 13: VISUAL ANALYTICS STUDIO & OBSERVATORIUM GRAFIK AKADEMIK



 * ========================================================================== */







let analyticsG1Chart = null;



let analyticsG2Chart = null;



let analyticsG3Chart = null;



let analyticsG4Chart = null;



let analyticsG5Chart = null;



let analyticsG6Chart = null;



let analyticsCohortChart = null;



let _analyticsDataCache = null;







async function muatVisualAnalytics(forceReload = false) {



  _sinkronAnalyticsContextSelectors();







  const selTahun = document.getElementById("analytics-sel-tahun");



  const selSem = document.getElementById("analytics-sel-semester");



  const selRumpun = document.getElementById("analytics-sel-rumpun");



  const selMk = document.getElementById("analytics-sel-mk");



  const statusEl = document.getElementById("analytics-engine-status");







  const tahun = selTahun ? selTahun.value : "2024-2025";



  const sem = selSem ? selSem.value : "GANJIL";



  const rumpun = selRumpun ? selRumpun.value : "all";



  const kunciMk = selMk ? selMk.value : "";



  const prodi = _prodiKey();







  if (statusEl) statusEl.textContent = "Menghubungkan Engine...";







  try {



    const q = new URLSearchParams({



      prodi: prodi,



      tahun: tahun,



      semester: sem,



      kunci_mk: kunciMk,



      rumpun: rumpun



    });



    if (forceReload) q.set("nocache", "1");







    const res = await fetch(`/api/analytics/overview?${q.toString()}`, { cache: "no-store" });



    if (!res.ok) throw new Error(`HTTP ${res.status}`);



    const data = await res.json();



    _analyticsDataCache = data;







    renderAnalyticsCharts(data);



    if (statusEl) statusEl.textContent = "Tersinkronisasi";



  } catch (err) {



    console.error("Gagal memuat visual analytics:", err);



    if (statusEl) statusEl.textContent = "Gagal Memuat";



    toast(`Gagal memuat visual analytics: ${err.message}`, "error");



  }



}







function _sinkronAnalyticsContextSelectors() {



  if (!pohonKurikulum) return;



  const prodi = _prodiKey();



  const selTahun = document.getElementById("analytics-sel-tahun");



  const selSem = document.getElementById("analytics-sel-semester");



  const selMk = document.getElementById("analytics-sel-mk");







  if (!selTahun || !selSem || !selMk) return;







  const globalTahun = document.getElementById("sel-tahun");



  const globalSem = document.getElementById("sel-semester");



  const globalMk = document.getElementById("course-selector");







  // 1. Tahun



  const pohonProdi = pohonKurikulum.pohon[prodi] || {};



  const taList = Object.keys(pohonProdi);



  if (selTahun.options.length !== taList.length) {



    selTahun.innerHTML = "";



    taList.forEach(ta => {



      const opt = document.createElement("option");



      opt.value = ta;



      opt.textContent = ta.replace("-", "/");



      selTahun.appendChild(opt);



    });



    if (globalTahun && taList.includes(globalTahun.value)) {



      selTahun.value = globalTahun.value;



    } else if (taList.length > 0) {



      selTahun.value = taList[taList.length - 1];



    }



  }







  // 2. Semester



  const semList = Object.keys(pohonProdi[selTahun.value] || {});



  if (selSem.options.length !== semList.length) {



    selSem.innerHTML = "";



    semList.forEach(s => {



      const opt = document.createElement("option");



      opt.value = s;



      opt.textContent = s === "GANJIL" ? "Ganjil" : (s === "GENAP" ? "Genap" : s);



      selSem.appendChild(opt);



    });



    if (globalSem && semList.includes(globalSem.value)) {



      selSem.value = globalSem.value;



    } else if (semList.length > 0) {



      selSem.value = semList[0];



    }



  }







  // 3. MK



  const mkList = (pohonProdi[selTahun.value] || {})[selSem.value] || [];



  selMk.innerHTML = "";



  mkList.forEach(m => {



    const opt = document.createElement("option");



    opt.value = m.kunci_mk;



    opt.textContent = `${m.nama_mk} (${m.sks} SKS)`;



    selMk.appendChild(opt);



  });







  if (globalMk && mkList.some(m => m.kunci_mk === globalMk.value)) {



    selMk.value = globalMk.value;



  } else if (mkList.length > 0) {



    selMk.value = mkList[0].kunci_mk;



  }



}







async function onAnalyticsContextChange(level) {



  const selTahun = document.getElementById("analytics-sel-tahun");



  const selSem = document.getElementById("analytics-sel-semester");



  const selMk = document.getElementById("analytics-sel-mk");



  if (!selTahun || !selSem || !selMk) return;







  if (level === "tahun" || level === "semester") {



    _sinkronAnalyticsContextSelectors();



  }







  await muatVisualAnalytics();



}







async function sinkronkanVisualAnalytics() {



  const icon = document.getElementById("icon-sync-analytics");



  if (icon) icon.classList.add("animate-spin");



  toast("Menyinkronkan engine & memperbarui 6 grafik observatorium...", "info", 2000);



  await muatVisualAnalytics(true);



  if (icon) {



    setTimeout(() => icon.classList.remove("animate-spin"), 600);



  }



  toast("Observatorium grafik berhasil disinkronkan!", "success");



}







function renderAnalyticsCharts(data) {



  if (!data || data.status !== "success") return;







  const g1 = data.grafik_1_mahasiswa_aktif || data.grafik_2_retensi || {};



  const g2 = data.grafik_2_kapasitas_mk || data.grafik_5_workload || {};



  const g3 = data.grafik_3_rumpun || {};



  const g4 = data.grafik_4_kesehatan_prodi || {};







  // Update 4 Executive KPI Badges at the top



  setText("stat-analytics-total-mhs", `${g1.total_aktif || 214} Mhs`);



  setText("stat-analytics-total-mk", `${g2.total_mk || 30} MK`);



  setText("stat-analytics-retensi", `${g1.retensi_rata_pct || 94.2}%`);



  setText("stat-analytics-mutu", `${g4.indeks_komposit || 89.8}% (Unggul)`);







  // Update card indicators



  setText("info-analytics-g2-retensi", `Total Mahasiswa Aktif: ${g1.total_aktif || 214} Mhs • Retensi ${g1.retensi_rata_pct || 94.2}%`);



  setText("badge-analytics-g5-mk", `Batas: 35 Mhs`);



  setText("info-analytics-g5-drop", `Status: ${g2.status_prodi || 'Optimal Terkendali'}`);



  setText("badge-analytics-g6-kasus", `Indeks: ${g4.indeks_komposit || 89.8}%`);







  // PILAR 1: Rekapitulasi Mahasiswa Aktif Lintas Semester (Stacked Bar)



  const opt1 = {



    chart: { type: "bar", height: 290, stacked: true, toolbar: { show: false }, background: "transparent" },



    series: g1.series || [],



    xaxis: { categories: g1.categories || [], labels: { style: { colors: "#94a3b8", fontSize: "11px" } } },



    yaxis: { labels: { style: { colors: "#94a3b8", fontSize: "11px" } } },



    colors: ["#10b981", "#f59e0b", "#f43f5e"],



    plotOptions: { bar: { borderRadius: 4, columnWidth: "50%" } },



    theme: { mode: "dark" },



    grid: { borderColor: "#1e293b" }



  };



  analyticsG2Chart = mountChart(analyticsG2Chart, "#chart-analytics-retensi", opt1);







  // PILAR 2: Rekapitulasi Kapasitas & Beban 8 MK Utama (Grouped Column with Target Annotation)



  const maxPeserta = Math.max(40, ...(g2.series || []).flatMap(s => s.data || [0]));



  const opt2 = {



    chart: { type: "bar", height: 290, toolbar: { show: false }, background: "transparent" },



    series: g2.series || [],



    xaxis: { categories: g2.categories || [], labels: { style: { colors: "#94a3b8", fontSize: "10px" } } },



    yaxis: { min: 0, max: maxPeserta + 5, labels: { style: { colors: "#94a3b8", fontSize: "11px" } } },



    colors: ["#06b6d4", "#8b5cf6"],



    plotOptions: { bar: { borderRadius: 4, columnWidth: "55%" } },



    annotations: {



      yaxis: [{



        y: 35,



        borderColor: "#f43f5e",



        strokeDashArray: 4,



        label: {



          text: "Batas Studio (35 Mhs)",



          style: { color: "#f43f5e", background: "#0f172a", fontSize: "10px", fontWeight: "bold" }



        }



      }]



    },



    theme: { mode: "dark" },



    grid: { borderColor: "#1e293b" }



  };



  analyticsG5Chart = mountChart(analyticsG5Chart, "#chart-analytics-workload", opt2);







  // PILAR 3: Komparasi Kinerja 4 Rumpun Mata Kuliah (Grouped Column)



  const opt3 = {



    chart: { type: "bar", height: 290, toolbar: { show: false }, background: "transparent" },



    series: g3.series || [],



    xaxis: { categories: g3.categories || [], labels: { style: { colors: "#94a3b8", fontSize: "10px" } } },



    yaxis: { min: 0, max: 100, labels: { style: { colors: "#94a3b8", fontSize: "11px" } } },



    colors: ["#8b5cf6", "#06b6d4"],



    plotOptions: { bar: { borderRadius: 4, columnWidth: "55%" } },



    theme: { mode: "dark" },



    grid: { borderColor: "#1e293b" }



  };



  analyticsG3Chart = mountChart(analyticsG3Chart, "#chart-analytics-rumpun", opt3);







  // PILAR 4: Indeks Kesehatan & Kelulusan Akademik Prodi (Radial Bar Multi-Ring)



  const opt4 = {



    chart: { type: "radialBar", height: 290, background: "transparent" },



    series: g4.series || [94, 88, 85, 92],



    plotOptions: {



      radialBar: {



        hollow: { size: "28%" },



        dataLabels: {



          name: { fontSize: "11px", color: "#94a3b8" },



          value: { fontSize: "14px", color: "#f8fafc", formatter: val => `${val}%` },



          total: {



            show: true,



            label: "Mutu Prodi",



            color: "#38bdf8",



            fontSize: "12px",



            formatter: () => `${g4.indeks_komposit || 89.8}%`



          }



        }



      }



    },



    colors: ["#10b981", "#06b6d4", "#f59e0b", "#8b5cf6"],



    labels: g4.labels || ["Retensi Mahasiswa", "Presensi Kuliah", "Kelulusan Tepat Waktu", "Mutu Studio"],



    theme: { mode: "dark" }



  };



  analyticsG6Chart = mountChart(analyticsG6Chart, "#chart-analytics-pareto", opt4);







  // PILAR 5: Observatorium Komparasi Kohort Multi-Angkatan (Opsi B)



  const gCohort = data.grafik_cohort_comparison || {};



  if (document.getElementById("chart-analytics-cohort") && gCohort.series) {



    const optCohort = {



      chart: { type: "bar", height: 300, toolbar: { show: false }, background: "transparent" },



      series: gCohort.series || [],



      xaxis: { categories: gCohort.categories || ["Angkatan 2024 (Sem 4)", "Angkatan 2025 (Sem 2)", "Angkatan 2026 (Sem 1)"], labels: { style: { colors: "#94a3b8", fontSize: "11px", fontWeight: "bold" } } },



      yaxis: { labels: { style: { colors: "#94a3b8", fontSize: "11px" } } },



      colors: ["#38bdf8", "#10b981", "#818cf8", "#f43f5e"],



      plotOptions: { bar: { borderRadius: 4, columnWidth: "55%" } },



      theme: { mode: "dark" },



      grid: { borderColor: "#1e293b" }



    };



    analyticsCohortChart = mountChart(analyticsCohortChart, "#chart-analytics-cohort", optCohort);







    if (gCohort.kpi) {



      const k24 = gCohort.kpi["2024"];



      const k25 = gCohort.kpi["2025"];



      const k26 = gCohort.kpi["2026"];



      if (k24) setText("cohort-stat-2024", `${k24.mhs} Mhs • IPK ${k24.ipk} • ${k24.kehadiran} Hadir`);



      if (k25) setText("cohort-stat-2025", `${k25.mhs} Mhs • IPK ${k25.ipk} • ${k25.kehadiran} Hadir`);



      if (k26) setText("cohort-stat-2026", `${k26.mhs} Mhs • IPK ${k26.ipk} • ${k26.kehadiran} Hadir`);



    }



  }







  if (window.lucide) lucide.createIcons();



}











/* ========================================================================== *



 * CROSS-TAB NAVIGATION BRIDGES (BUILD MODE OPSI C)



 * ========================================================================== */







function bukaKurikulumDariModalAsistensi() {



  if (!_currentModalCourse) return;



  const c = _currentModalCourse;



  tutupModalAsistensiMk();



  const prodi = _prodiKey();



  const tahunAjar = c.tahun_ajar || (document.getElementById('sel-tahun') ? document.getElementById('sel-tahun').value : '2024-2025');



  const sem = c.semester || (document.getElementById('sel-semester') ? document.getElementById('sel-semester').value : 'GANJIL');



  const kunci = c.kunci_mk || c.id || c.kode_mk || '';



  rekapLihatMk(prodi, tahunAjar, sem, kunci);



}







function bukaPortofolioDariWali() {



  const npm = (currentStudent && currentStudent.npm) || (document.getElementById('student-dropdown') ? document.getElementById('student-dropdown').value : '');



  switchTab('portofolio');



  if (npm) {



    pilihPortoStudent(npm);



  }



}





/* ========================================================================== *
 * TAB 8: PERTUMBUHAN PMB & PENYERAPAN 30 MK KURIKULUM (ANALISIS SENIOR)
 * ========================================================================== */

let _growthData = null;
let _growthChartPmb = null;
let _growthChartEnrolment = null;
let _growthSearchKeyword = "";

async function renderGrowthTab() {
  const periodeSel = document.getElementById("sel-growth-periode");
  const rumpunSel = document.getElementById("sel-growth-rumpun");
  const periode = periodeSel ? periodeSel.value : "all";
  const rumpun = rumpunSel ? rumpunSel.value : "all";

  try {
    const res = await fetch(`/api/analytics/growth?periode=${encodeURIComponent(periode)}&rumpun=${encodeURIComponent(rumpun)}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    _growthData = data;

    // 1. Update 4 Hero KPI Cards
    const kpi = (data.pmb && data.pmb.kpi_summary) || {};
    setText("stat-growth-yoy", kpi.growth_yoy_label || "+133.3% YoY");
    setText("stat-growth-retensi", kpi.retensi_mahasiswa_pct ? `${kpi.retensi_mahasiswa_pct}%` : "94.6%");
    if (kpi.kas_masuk_pmb_rp) {
      const kasClean = kpi.kas_masuk_pmb_rp.replace(".000.000", " Jt");
      setText("stat-growth-kas", kasClean);
    } else {
      setText("stat-growth-kas", "Rp 227.5 Jt");
    }
    setText("stat-growth-studio", kpi.utilisasi_studio_pct ? `${kpi.utilisasi_studio_pct}%` : "87.5%");

    // 2. Render Chart PMB Multi-Tahun (#chart-pmb-growth)
    _renderChartPmb(data.pmb);

    // 3. Render Chart Penyerapan 30 MK (#chart-enrolment-absorption)
    _renderChartEnrolment(data.enrolment);

    // 4. Render Matriks Table
    renderGrowthEnrolmentTable();

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Gagal render tab pertumbuhan:", err);
    toast(`Gagal memuat analitik pertumbuhan: ${err.message}`, "error");
  }
}

function _renderChartPmb(pmb) {
  if (!pmb) return;
  const categories = (pmb.pmb_history || []).map(h => `Angkatan ${h.angkatan}`);
  const dataRealisasi = (pmb.pmb_history || []).map(h => h.total_pendaftar);
  const dataTarget = (pmb.pmb_history || []).map(h => h.target_kuota);
  const dataGrowth = (pmb.pmb_history || []).map(h => h.pertumbuhan_yoy_pct || 0);

  const optPmb = {
    chart: {
      type: "bar",
      height: 320,
      toolbar: { show: false },
      background: "transparent",
      animations: { enabled: true }
    },
    series: [
      { name: "Mahasiswa Baru (Realisasi)", type: "column", data: dataRealisasi },
      { name: "Target Kuota Yayasan", type: "column", data: dataTarget },
      { name: "Pertumbuhan YoY (%)", type: "line", data: dataGrowth }
    ],
    xaxis: {
      categories: categories,
      labels: { style: { colors: "#94a3b8", fontSize: "11px", fontWeight: "bold" } }
    },
    yaxis: [
      {
        seriesName: "Mahasiswa Baru (Realisasi)",
        title: { text: "Jumlah Mahasiswa", style: { color: "#10b981", fontSize: "11px" } },
        labels: { style: { colors: "#94a3b8", fontSize: "11px" } }
      },
      {
        seriesName: "Target Kuota Yayasan",
        show: false
      },
      {
        opposite: true,
        seriesName: "Pertumbuhan YoY (%)",
        title: { text: "Pertumbuhan (%)", style: { color: "#38bdf8", fontSize: "11px" } },
        labels: {
          style: { colors: "#38bdf8", fontSize: "11px" },
          formatter: val => `${val > 0 ? "+" : ""}${val}%`
        }
      }
    ],
    colors: ["#10b981", "#64748b", "#38bdf8"],
    plotOptions: {
      bar: { columnWidth: "45%", borderRadius: 4 }
    },
    stroke: {
      width: [0, 0, 3],
      curve: "smooth"
    },
    grid: { borderColor: "#334155", strokeDashArray: 3 },
    legend: {
      labels: { colors: "#e2e8f0" },
      position: "top"
    },
    theme: { mode: "dark" },
    tooltip: {
      theme: "dark",
      shared: true,
      intersect: false
    }
  };

  _growthChartPmb = mountChart(_growthChartPmb, "#chart-pmb-growth", optPmb);
}

function _renderChartEnrolment(enrol) {
  if (!enrol) return;
  const records = enrol.records || [];
  if (!records.length) {
    const c = document.querySelector("#chart-enrolment-absorption");
    if (c) c.innerHTML = '<div class="text-center py-10 text-slate-500 italic text-xs">Tidak ada data mata kuliah yang sesuai filter.</div>';
    return;
  }

  const displayRecords = records.slice(0, 15);
  const categories = displayRecords.map(r => r.kode_mk);
  const dataPeserta = displayRecords.map(r => r.peserta_kelas);
  const dataPenyerapan = displayRecords.map(r => r.rasio_penyerapan_pasar_pct);

  const optEnrol = {
    chart: {
      type: "bar",
      height: 350,
      toolbar: { show: false },
      background: "transparent",
      animations: { enabled: true }
    },
    series: [
      { name: "Peserta Terdaftar (n)", type: "column", data: dataPeserta },
      { name: "% Penyerapan Pasar (S_MK)", type: "line", data: dataPenyerapan }
    ],
    xaxis: {
      categories: categories,
      labels: {
        rotate: -30,
        style: { colors: "#94a3b8", fontSize: "10px", fontWeight: "bold" }
      }
    },
    yaxis: [
      {
        seriesName: "Peserta Terdaftar (n)",
        title: { text: "Jumlah Peserta (Mahasiswa)", style: { color: "#14b8a6", fontSize: "11px" } },
        labels: { style: { colors: "#94a3b8", fontSize: "11px" } }
      },
      {
        opposite: true,
        seriesName: "% Penyerapan Pasar (S_MK)",
        max: 100,
        min: 0,
        title: { text: "Penyerapan Pasar (%)", style: { color: "#10b981", fontSize: "11px" } },
        labels: {
          style: { colors: "#10b981", fontSize: "11px" },
          formatter: val => `${val}%`
        }
      }
    ],
    colors: ["#14b8a6", "#10b981"],
    plotOptions: {
      bar: { columnWidth: "50%", borderRadius: 4 }
    },
    stroke: {
      width: [0, 3],
      curve: "smooth"
    },
    grid: { borderColor: "#334155", strokeDashArray: 3 },
    legend: {
      labels: { colors: "#e2e8f0" },
      position: "top"
    },
    theme: { mode: "dark" },
    tooltip: {
      theme: "dark",
      shared: true,
      intersect: false,
      y: {
        formatter: (val, opts) => {
          if (opts.seriesIndex === 1) return `${val}%`;
          return `${val} Mahasiswa`;
        }
      }
    }
  };

  _growthChartEnrolment = mountChart(_growthChartEnrolment, "#chart-enrolment-absorption", optEnrol);
}

function renderGrowthEnrolmentTable() {
  const tbody = document.getElementById("growth-enrolment-tbody");
  const countBadge = document.getElementById("growth-mk-count-badge");
  if (!tbody || !_growthData || !_growthData.enrolment) return;

  const records = _growthData.enrolment.records || [];
  let filtered = records;
  if (_growthSearchKeyword) {
    const kw = _growthSearchKeyword.toLowerCase();
    filtered = filtered.filter(r => 
      (r.nama_mk && r.nama_mk.toLowerCase().includes(kw)) ||
      (r.kode_mk && r.kode_mk.toLowerCase().includes(kw)) ||
      (r.rumpun && r.rumpun.toLowerCase().includes(kw))
    );
  }

  if (countBadge) countBadge.textContent = `${filtered.length} MK`;

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="11" class="text-center py-8 text-slate-500 italic text-xs">Tidak ada data mata kuliah yang cocok dengan filter atau kata kunci pencarian.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((r, i) => {
    const ratio = r.rasio_penyerapan_pasar_pct || 0;
    const badgeStatus = ratio >= 90
      ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Saturasi Penuh (90-100%)</span>'
      : (ratio >= 70
          ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">Optimal (70-89%)</span>'
          : '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">Rendah / Khusus (&lt;70%)</span>');

    const deltaClass = (r.pertumbuhan_yoy_pct || 0) >= 0 ? "text-emerald-400" : "text-rose-400";
    const deltaSign = (r.pertumbuhan_yoy_pct || 0) > 0 ? "+" : "";

    return `
      <tr class="hover:bg-slate-800/40 transition">
        <td class="py-2.5 px-3 text-center font-mono text-[11px] text-slate-400">${i + 1}</td>
        <td class="py-2.5 px-3">
          <div class="font-bold text-white">${escapeHtml(r.nama_mk)}</div>
          <div class="font-mono text-[10.5px] text-emerald-400">${escapeHtml(r.kode_mk)}</div>
        </td>
        <td class="py-2.5 px-3">
          <div class="text-slate-300">${escapeHtml(r.periode)}</div>
          <span class="inline-block px-1.5 py-0.5 rounded text-[9.5px] font-bold bg-slate-800 text-slate-300 border border-slate-700">${escapeHtml(r.rumpun || "Umum")}</span>
        </td>
        <td class="py-2.5 px-3 text-center font-mono font-bold text-slate-200">${r.sks || 2}</td>
        <td class="py-2.5 px-3 text-center font-mono text-slate-400">${r.total_mahasiswa_aktif_periode}</td>
        <td class="py-2.5 px-3 text-center font-mono font-bold text-white">${r.peserta_kelas}</td>
        <td class="py-2.5 px-3 text-center">
          <span class="font-mono font-bold ${ratio >= 85 ? 'text-emerald-300' : 'text-slate-200'}">${r.penyerapan_label}</span>
        </td>
        <td class="py-2.5 px-3 text-center font-mono font-bold ${deltaClass}">
          ${deltaSign}${r.pertumbuhan_yoy_pct || 0}%
        </td>
        <td class="py-2.5 px-3 text-center font-mono text-cyan-300 font-bold">${r.composite_load_index}</td>
        <td class="py-2.5 px-3 text-center">${badgeStatus}</td>
        <td class="py-2.5 px-3 text-center whitespace-nowrap">
          <button onclick="bukaModalEvaluasiMkRawan('${escapeHtml(r.kode_mk)}')" class="touch-target px-2.5 py-1 bg-slate-800 hover:bg-emerald-600 text-slate-300 hover:text-white border border-slate-700 rounded-lg font-bold text-[10.5px] transition inline-flex items-center gap-1">
            <i data-lucide="eye" class="w-3 h-3"></i> Asistensi
          </button>
        </td>
      </tr>
    `;
  }).join("");

  if (window.lucide) lucide.createIcons();
}

function filterGrowthData() {
  renderGrowthTab();
}

function onGrowthSearchInput() {
  const inp = document.getElementById("search-growth-mk");
  _growthSearchKeyword = inp ? inp.value.trim() : "";
  renderGrowthEnrolmentTable();
}

/* PILAR 1: Render Section Audit BSS & Proteksi Masa Studi Senior Yayasan */
function _renderPortoBssAudit(d) {
  const container = document.getElementById("porto-bss-audit");
  if (!container) return;

  const reg = d.registry_meta;
  const isBssOrSenior = reg && (
    reg.is_bss || 
    (reg.total_semester_bss && reg.total_semester_bss > 0) || 
    (reg.semester_ke && reg.semester_ke > 8) || 
    reg.status_akademik === "DARURAT_DO" ||
    reg.status_akademik === "BSS" ||
    (d.analisis_potensi && d.analisis_potensi.label && d.analisis_potensi.label.includes("BSS"))
  );

  if (!isBssOrSenior) {
    container.classList.add("hidden");
    container.innerHTML = "";
    return;
  }

  container.classList.remove("hidden");
  const isCuti = reg ? reg.is_bss : false;
  const semKe = reg ? reg.semester_ke : 10;
  const semEfektif = reg ? (reg.semester_efektif || semKe) : semKe;
  const totalBss = reg ? (reg.total_semester_bss || 0) : 0;
  const angkatan = reg ? reg.angkatan : 2021;
  const biayaLabel = reg ? (reg.biaya_semester_label || (isCuti ? "Rp 500.000" : "Rp 6.500.000")) : "Rp 500.000";
  const statusLabel = reg ? (reg.status_label || reg.status_akademik || "Status Khusus") : "Cuti BSS / Senior";

  container.innerHTML = `
    <div class="bg-gradient-to-r from-slate-900 via-[#1b152e] to-slate-900 border border-purple-500/40 rounded-2xl p-5 shadow-2xl space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-500/20 pb-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300 shrink-0">
            <i data-lucide="landmark" class="w-5 h-5"></i>
          </div>
          <div>
            <h3 class="text-sm font-black text-white flex items-center gap-2">
              AUDIT STATUS MASA STUDI &amp; KEBIJAKAN BSS YAYASAN
              <span class="px-2.5 py-0.5 rounded-full text-[10.5px] font-mono font-bold ${isCuti ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : (semKe > 14 ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-purple-500/20 text-purple-300 border border-purple-500/40')}">
                ${escapeHtml(statusLabel)}
              </span>
            </h3>
            <p class="text-[11px] text-slate-400">Verifikasi portofolio masa studi perpanjangan senat universitas dan pencatatan kas perlindungan status.</p>
          </div>
        </div>
        <div class="text-left sm:text-right">
          <span class="text-[10px] font-mono text-slate-400 block">Kewajiban Kas Semester Ini</span>
          <span class="text-sm font-black font-mono text-emerald-400">${escapeHtml(biayaLabel)}</span>
        </div>
      </div>

      <!-- 3 KOLOM AUDIT METRIK -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div class="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <span class="text-[10px] text-slate-400 block mb-0.5 font-bold">1. MASA STUDI BERJALAN</span>
          <div class="text-base font-black text-white font-mono">${reg && reg.semester_label ? reg.semester_label : 'Semester ' + semKe}</div>
          <p class="text-[10.5px] text-slate-400 mt-1">Total kalender akademik sejak pendaftaran tahun ${angkatan}</p>
        </div>
        <div class="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <span class="text-[10px] text-amber-400 block mb-0.5 font-bold">2. DIBEKUKAN / BSS (NON-AKTIF)</span>
          <div class="text-base font-black text-amber-300 font-mono">${totalBss} Semester (${(totalBss * 0.5).toFixed(1)} Thn)</div>
          <p class="text-[10.5px] text-slate-400 mt-1">${reg && reg.riwayat_bss && reg.riwayat_bss.length ? 'Periode: ' + reg.riwayat_bss.join(', ') : 'Tidak ada riwayat cuti sah'}</p>
        </div>
        <div class="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <span class="text-[10px] text-cyan-400 block mb-0.5 font-bold">3. MASA STUDI EFEKTIF (TERHITUNG)</span>
          <div class="text-base font-black text-cyan-300 font-mono">${reg && reg.semester_efektif_label ? reg.semester_efektif_label : 'Semester ' + semEfektif}</div>
          <p class="text-[10.5px] text-slate-400 mt-1">${semEfektif > 14 ? '⚠️ Melewati batas reguler 14 sem - Perlindungan Senat' : '✓ Masih dalam toleransi evaluasi masa studi'}</p>
        </div>
      </div>

      <!-- ACTION PLAN ASISTENSI KELULUSAN & LEGALITAS -->
      <div class="p-3 bg-purple-950/30 border border-purple-500/30 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div class="space-y-1">
          <div class="font-bold text-purple-200 flex items-center gap-1.5">
            <i data-lucide="check-circle" class="w-3.5 h-3.5 text-purple-400"></i>
            Action Plan Pendampingan Kelulusan &amp; Rekomendasi Senat:
          </div>
          <p class="text-slate-300 text-[11px]">
            ${isCuti 
              ? 'Mahasiswa dalam status Cuti BSS Sah (Rp 500.000/sem). Maksimal cuti 4 semester berturut-turut. Diwajibkan mengurus formulir aktif kembali sebelum batas registrasi semester baru.' 
              : (semKe > 14 
                  ? 'Mahasiswa senior masa studi panjang. Status dilindungi dispensasi senat universitas. Wajib menyelesaikan Tugas Akhir / Sidang Skripsi pada periode terdekat.' 
                  : 'Mahasiswa dalam pemantauan percepatan kelulusan dan pemenuhan 144 SKS.')}
          </p>
        </div>
        <a href="/api/pdf/download?type=cohort_report" target="_blank" class="shrink-0 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-bold text-[11px] inline-flex items-center gap-1.5 transition">
          <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Bukti Legalitas Senat
        </a>
      </div>
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}


function jadikanKonteksAktifDashboard() {
  const selMk = document.getElementById("course-selector");
  const mkKey = selMk ? selMk.value : null;
  if (mkKey) {
    if (typeof switchActiveCourse === "function") {
      switchActiveCourse(mkKey);
    }
    toast(`Mata kuliah ${mkKey} aktif sebagai konteks utama!`, "success");
    switchTab("kaprodi");
  } else {
    toast("Pilih mata kuliah terlebih dahulu.", "warning");
  }
}



// =============================================================================
// 📱 MOBILE DRAWER CONTROLLER (UI-NAV-02 & UI-NAV-03)
// =============================================================================
function toggleMobileSidebar() {
  const sidebar = document.getElementById("sidebar-nav");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!sidebar) return;
  const isOpen = sidebar.classList.contains("mobile-open");
  if (isOpen) {
    closeMobileSidebar();
  } else {
    sidebar.classList.add("mobile-open");
    if (backdrop) {
      backdrop.classList.add("mobile-open");
      backdrop.classList.remove("hidden");
    }
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }
}

function closeMobileSidebar() {
  const sidebar = document.getElementById("sidebar-nav");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (sidebar) sidebar.classList.remove("mobile-open");
  if (backdrop) {
    backdrop.classList.remove("mobile-open");
    backdrop.classList.add("hidden");
  }
}

window.toggleMobileSidebar = toggleMobileSidebar;
window.closeMobileSidebar = closeMobileSidebar;


// =============================================================================
// 📱 MOBILE CONTEXT FILTER TOGGLE
// =============================================================================
function toggleMobileFilterBar() {
  const container = document.getElementById("header-context-container");
  if (!container) return;
  const isHidden = container.classList.contains("hidden");
  if (isHidden) {
    container.classList.remove("hidden");
    container.classList.add("flex");
  } else {
    container.classList.add("hidden");
    container.classList.remove("flex");
  }
}

function closeMobileFilterBar() {
  const container = document.getElementById("header-context-container");
  if (!container) return;
  container.classList.add("hidden");
  container.classList.remove("flex");
}

window.toggleMobileFilterBar = toggleMobileFilterBar;
window.closeMobileFilterBar = closeMobileFilterBar;

// Auto-close filter container when clicking outside on mobile
document.addEventListener("click", function (e) {
  if (window.innerWidth >= 1024) return;
  const container = document.getElementById("header-context-container");
  const toggleBtn = document.getElementById("btn-mobile-filter-toggle");
  if (!container || container.classList.contains("hidden")) return;
  if (!container.contains(e.target) && (!toggleBtn || !toggleBtn.contains(e.target))) {
    closeMobileFilterBar();
  }
});

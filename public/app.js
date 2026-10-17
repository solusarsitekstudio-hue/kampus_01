// App Controller for SIAK-KAPRODI (Arsitektur Intelligence)

let masterData = null;
let currentStudent = null;
let currentSlideIndex = 0;
let videoPlaying = false;
let videoTimerInterval = null;
let videoCurrentSecond = 0;

// Chart instances
let attendanceTrendChart = null;
let gradeDistChart = null;
let radarCompetencyChart = null;

// On Page Load
document.addEventListener("DOMContentLoaded", async () => {
  await loadAcademicData();
  lucide.createIcons();
});

// Fetch Data from Server API
async function loadAcademicData() {
  try {
    const res = await fetch("/api/data");
    masterData = await res.json();
    console.log("Master Academic Data loaded:", masterData);

    renderKaprodiDashboard();
    populateStudentDropdown();
    
    // Select first student by default (M Yazid Zidane Mulyadi)
    if (masterData.students && masterData.students.length > 0) {
      selectStudent(masterData.students[0].npm);
    }
  } catch (err) {
    console.error("Failed to load academic data:", err);
  }
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

  // Refresh charts if needed
  if (tabName === "wali" && radarCompetencyChart) {
    setTimeout(() => radarCompetencyChart.render(), 100);
  }
  lucide.createIcons();
}

// =============================================================================
// TAB 1: EXECUTIVE KAPRODI DASHBOARD RENDERING
// =============================================================================
function renderKaprodiDashboard() {
  if (!masterData) return;

  const summary = masterData.class_summary;
  document.getElementById("kpi-total-mhs").innerText = summary.total_mahasiswa;
  document.getElementById("kpi-kehadiran").innerText = summary.rata_kehadiran + "%";
  document.getElementById("kpi-nilai").innerText = summary.rata_nilai_studio;
  document.getElementById("kpi-at-risk").innerText = `${summary.total_at_risk} Mahasiswa`;

  renderAttendanceTrendChart(summary.tren_kehadiran_sesi);
  renderGradeDistChart(summary.distribusi_grade);
  renderAttendanceTable();
}

function renderAttendanceTrendChart(trends) {
  const categories = trends.map(t => `Sesi ${t.pertemuan}`);
  const hadirData = trends.map(t => t.hadir);
  const absentData = trends.map(t => t.sakit + t.izin + t.alpha);

  const options = {
    series: [
      { name: "Hadir di Lab", data: hadirData, color: "#10b981" },
      { name: "Izin / Sakit / Alpha", data: absentData, color: "#f43f5e" }
    ],
    chart: {
      type: "bar",
      height: 260,
      stacked: true,
      toolbar: { show: false },
      background: "transparent"
    },
    theme: { mode: "dark" },
    plotOptions: {
      bar: {
        borderRadius: 6,
        columnWidth: "40%"
      }
    },
    xaxis: {
      categories: categories,
      labels: { style: { colors: "#94a3b8", fontSize: "11px" } },
      axisBorder: { color: "#334155" }
    },
    yaxis: {
      max: masterData.class_summary.total_mahasiswa,
      labels: { style: { colors: "#94a3b8", fontSize: "11px" } }
    },
    legend: {
      position: "top",
      horizontalAlign: "right",
      labels: { colors: "#cbd5e1" }
    },
    grid: { borderColor: "#1e293b" }
  };

  const chartContainer = document.querySelector("#chart-attendance-trend");
  chartContainer.innerHTML = "";
  attendanceTrendChart = new ApexCharts(chartContainer, options);
  attendanceTrendChart.render();
}

function renderGradeDistChart(dist) {
  const labels = Object.keys(dist);
  const series = Object.values(dist);

  const options = {
    series: series,
    chart: {
      type: "donut",
      height: 230,
      background: "transparent"
    },
    labels: labels,
    colors: ["#10b981", "#06b6d4", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"],
    theme: { mode: "dark" },
    legend: {
      position: "bottom",
      labels: { colors: "#cbd5e1", fontSize: "10px" }
    },
    stroke: { width: 2, colors: ["#0f172a"] },
    dataLabels: {
      enabled: true,
      style: { fontSize: "10px" }
    }
  };

  const chartContainer = document.querySelector("#chart-grade-dist");
  chartContainer.innerHTML = "";
  gradeDistChart = new ApexCharts(chartContainer, options);
  gradeDistChart.render();
}

function renderAttendanceTable() {
  const tbody = document.getElementById("attendance-table-body");
  tbody.innerHTML = "";

  const searchVal = document.getElementById("table-search").value.toLowerCase();
  const sessionVal = document.getElementById("filter-session").value;
  const statusVal = document.getElementById("filter-status").value;

  masterData.students.forEach((s) => {
    // Check search match
    const matchSearch = s.nama.toLowerCase().includes(searchVal) || s.npm.includes(searchVal);
    if (!matchSearch) return;

    s.kehadiran.detail.forEach((sess) => {
      // Check session filter
      if (sessionVal !== "all" && sess.pertemuan.toString() !== sessionVal) return;
      // Check status filter
      if (statusVal !== "all" && sess.status !== statusVal) return;

      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-800/40 transition";

      // Status pill styling
      let statusBadge = "";
      if (sess.status === "Hadir") {
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Hadir</span>`;
      } else if (sess.status === "Sakit") {
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">Sakit</span>`;
      } else if (sess.status === "Izin") {
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">Izin</span>`;
      } else {
        statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">Alpha</span>`;
      }

      // Alpha count pill
      let alphaBadge = `<span class="font-mono text-slate-400">${s.kehadiran.alpha}x</span>`;
      if (s.kehadiran.alpha >= 2) {
        alphaBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 font-mono">${s.kehadiran.alpha}x (At-Risk)</span>`;
      }

      tr.innerHTML = `
        <td class="px-4 py-3 text-slate-400">${s.no}</td>
        <td class="px-4 py-3 font-mono text-amber-400 font-semibold">${s.npm}</td>
        <td class="px-4 py-3 text-white font-medium">${s.nama}</td>
        <td class="px-4 py-3 text-slate-300 font-mono">Sesi ${sess.pertemuan} • ${sess.tanggal}</td>
        <td class="px-4 py-3 text-slate-300 max-w-xs truncate" title="${sess.topik}">${sess.topik}</td>
        <td class="px-4 py-3">${statusBadge}</td>
        <td class="px-4 py-3 text-slate-400 italic">${sess.alasan}</td>
        <td class="px-4 py-3 text-center">${alphaBadge}</td>
        <td class="px-4 py-3 text-right">
          <button onclick="selectQuickStudent('${s.npm}')" class="px-2.5 py-1 bg-slate-800 hover:bg-amber-500 hover:text-slate-950 text-slate-300 rounded-lg text-[11px] font-medium transition flex items-center gap-1 ml-auto">
            <span>Rapor</span> <i data-lucide="chevron-right" class="w-3 h-3"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  });

  lucide.createIcons();
}

function filterTable() {
  renderAttendanceTable();
}

// =============================================================================
// TAB 2: PORTAL RAPOR WALI MURID RENDERING
// =============================================================================
function populateStudentDropdown() {
  const dropdown = document.getElementById("student-dropdown");
  dropdown.innerHTML = "";
  masterData.students.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.npm;
    opt.innerText = `${s.nama} (${s.npm}) - Grade: ${s.akademik.grade}`;
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
  currentStudent = masterData.students.find(s => s.npm === npm);
  if (!currentStudent) return;

  // Sync dropdown
  document.getElementById("student-dropdown").value = npm;

  // Render Profile Hero
  const initials = currentStudent.nama.split(" ").map(w => w[0]).slice(0, 2).join("");
  document.getElementById("mhs-avatar").innerText = initials;
  document.getElementById("mhs-nama").innerText = currentStudent.nama;
  document.getElementById("mhs-npm").innerText = currentStudent.npm;

  // Alert badge
  const alertBadge = document.getElementById("mhs-alert-badge");
  alertBadge.innerText = currentStudent.ai_diagnosis.status_alert;
  if (currentStudent.ai_diagnosis.alert_color === "rose") {
    alertBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30";
  } else if (currentStudent.ai_diagnosis.alert_color === "sky") {
    alertBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30";
  } else {
    alertBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
  }

  // Quick stats
  document.getElementById("mhs-stat-kehadiran").innerText = currentStudent.kehadiran.persentase + "%";
  document.getElementById("mhs-stat-absen-desc").innerText = `${currentStudent.kehadiran.hadir} / 6 Sesi Hadir`;
  document.getElementById("mhs-stat-nilai").innerText = currentStudent.akademik.nilai_rata_rata;
  document.getElementById("mhs-stat-grade").innerText = `Grade: ${currentStudent.akademik.grade}`;
  document.getElementById("mhs-stat-alpha").innerText = `${currentStudent.kehadiran.alpha}x`;

  // Render Radar Competency Chart
  renderRadarCompetencyChart(currentStudent.akademik.kompetensi);

  // Render AI SWOT Card
  document.getElementById("ai-kekuatan").innerText = currentStudent.ai_diagnosis.kekuatan;
  document.getElementById("ai-kelemahan").innerText = currentStudent.ai_diagnosis.kelemahan;
  document.getElementById("ai-saran").innerText = currentStudent.ai_diagnosis.saran_wali_murid;

  // Render Session Cards
  renderStudentSessionCards(currentStudent.kehadiran.detail);

  // Update Marketing Engine Components (Tabs 3 & 4)
  currentSlideIndex = 0;
  renderCarouselSlide(currentSlideIndex);
  renderVideoStory(currentStudent);
  renderWhatsAppSimulation(currentStudent);

  lucide.createIcons();
}

function renderRadarCompetencyChart(comp) {
  document.getElementById("radar-val-cad").innerText = comp.penguasaan_cad;
  document.getElementById("radar-val-detail").innerText = comp.ketelitian_detail;
  document.getElementById("radar-val-disiplin").innerText = comp.kedisiplinan_asistensi;
  document.getElementById("radar-val-ruang").innerText = comp.logika_ruang_struktur;

  const options = {
    series: [
      {
        name: "Skor Mahasiswa",
        data: [
          comp.penguasaan_cad,
          comp.ketelitian_detail,
          comp.kedisiplinan_asistensi,
          comp.logika_ruang_struktur,
          comp.manajemen_waktu
        ]
      }
    ],
    chart: {
      type: "radar",
      height: 290,
      toolbar: { show: false },
      background: "transparent"
    },
    labels: [
      "Penguasaan CAD",
      "Detail & Presisi",
      "Kedisiplinan Studio",
      "Logika Ruang/Struktur",
      "Manajemen Waktu"
    ],
    colors: ["#f59e0b"],
    markers: { size: 4, colors: ["#ffc800"] },
    fill: { opacity: 0.35, colors: ["#f59e0b"] },
    yaxis: {
      max: 100,
      show: false
    },
    xaxis: {
      labels: {
        style: {
          colors: ["#cbd5e1", "#cbd5e1", "#cbd5e1", "#cbd5e1", "#cbd5e1"],
          fontSize: "11px",
          fontWeight: 600
        }
      }
    },
    theme: { mode: "dark" }
  };

  const chartContainer = document.querySelector("#chart-radar-competency");
  chartContainer.innerHTML = "";
  radarCompetencyChart = new ApexCharts(chartContainer, options);
  radarCompetencyChart.render();
}

function renderStudentSessionCards(detailList) {
  const container = document.getElementById("student-session-cards");
  container.innerHTML = "";

  detailList.forEach(item => {
    const card = document.createElement("div");
    card.className = "p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-3 text-xs";

    let statPill = "";
    if (item.status === "Hadir") {
      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">Hadir</span>`;
    } else if (item.status === "Sakit") {
      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400">Sakit</span>`;
    } else if (item.status === "Izin") {
      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400">Izin</span>`;
    } else {
      statPill = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400">Alpha</span>`;
    }

    card.innerHTML = `
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center font-mono font-bold text-amber-400 text-xs">
          P${item.pertemuan}
        </div>
        <div>
          <div class="font-bold text-white">${item.topik}</div>
          <div class="text-[11px] text-slate-400 font-mono">${item.tanggal} • ${item.alasan}</div>
        </div>
      </div>
      <div class="flex items-center gap-3">
        ${statPill}
        <div class="text-right">
          <div class="text-xs font-mono font-bold text-amber-400">${item.skor_sesi}</div>
          <div class="text-[10px] text-slate-500">Nilai Praktikum</div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// =============================================================================
// TAB 3: VIRAL MARKETING ENGINE (CAROUSEL & VIDEO 9:16)
// =============================================================================
function renderCarouselSlide(index) {
  if (!currentStudent || !currentStudent.marketing.carousel) return;
  const slides = currentStudent.marketing.carousel;
  const slide = slides[index];

  document.getElementById("carousel-indicator").innerText = `Slide ${index + 1} / ${slides.length}`;
  document.getElementById("slide-stage-counter").innerText = `0${index + 1} / 0${slides.length}`;
  document.getElementById("slide-stage-badge").innerText = slide.badge;
  document.getElementById("slide-stage-title").innerText = slide.headline;
  document.getElementById("slide-stage-desc").innerText = slide.subline;
  document.getElementById("slide-stage-highlight").innerText = slide.highlight;

  // Active thumb highlights
  for (let i = 0; i < 4; i++) {
    const thumb = document.getElementById(`thumb-${i}`);
    if (thumb) {
      if (i === index) {
        thumb.classList.add("active-thumb");
      } else {
        thumb.classList.remove("active-thumb");
      }
    }
  }

  // Visual Box Architectural Vector Rendering
  const visualBox = document.getElementById("slide-visual-box");
  if (index === 0) {
    // Cover & Achievement Badge
    visualBox.innerHTML = `
      <div class="text-center space-y-2">
        <div class="w-16 h-16 rounded-2xl bg-amber-500/20 text-amber-400 mx-auto flex items-center justify-center text-3xl border border-amber-500/40 shadow-lg">
          🏆
        </div>
        <div class="text-xs font-bold text-white tracking-wide uppercase">Prestasi Studio Arsitektur</div>
        <div class="text-[11px] font-mono text-amber-400">Predikat: ${currentStudent.akademik.grade} (${currentStudent.akademik.nilai_rata_rata})</div>
      </div>
    `;
  } else if (index === 1) {
    // Studio Lab Activity Vector
    visualBox.innerHTML = `
      <div class="text-center space-y-2">
        <div class="w-16 h-16 rounded-2xl bg-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center text-3xl border border-emerald-500/40 shadow-lg">
          💻
        </div>
        <div class="text-xs font-bold text-white tracking-wide uppercase">Studio Asistensi Lab LIKDA</div>
        <div class="text-[11px] text-slate-300">AutoCAD Modeling & Sinkronisasi Gambar Kerja</div>
      </div>
    `;
  } else if (index === 2) {
    // Architectural Drawings Blueprint Vector
    visualBox.innerHTML = `
      <div class="text-center space-y-2">
        <div class="w-16 h-16 rounded-2xl bg-cyan-500/20 text-cyan-400 mx-auto flex items-center justify-center text-3xl border border-cyan-500/40 shadow-lg">
          📐
        </div>
        <div class="text-xs font-bold text-white tracking-wide uppercase">Denah, Potongan & Detail Pondasi</div>
        <div class="text-[11px] text-cyan-300 font-mono">Standar Cetak Sheet A3 Arsitektur</div>
      </div>
    `;
  } else {
    // Official Pride Badge
    visualBox.innerHTML = `
      <div class="text-center space-y-2">
        <div class="w-16 h-16 rounded-2xl bg-amber-500/20 text-amber-400 mx-auto flex items-center justify-center text-3xl border border-amber-500/40 shadow-lg">
          🏛️
        </div>
        <div class="text-xs font-bold text-amber-400 tracking-wide uppercase">PROGRAM STUDI ARSITEKTUR</div>
        <div class="text-[11px] text-slate-300">Mencetak Generasi Arsitek Muda Indonesia</div>
      </div>
    `;
  }
}

function nextSlide() {
  if (!currentStudent) return;
  currentSlideIndex = (currentSlideIndex + 1) % 4;
  renderCarouselSlide(currentSlideIndex);
}

function prevSlide() {
  if (!currentStudent) return;
  currentSlideIndex = (currentSlideIndex - 1 + 4) % 4;
  renderCarouselSlide(currentSlideIndex);
}

function goToSlide(index) {
  currentSlideIndex = index;
  renderCarouselSlide(currentSlideIndex);
}

// 9:16 Video Player Simulation
function renderVideoStory(student) {
  const vid = student.marketing.video;
  document.getElementById("video-full-script").innerText = `"${vid.voiceover_script}"`;
  document.getElementById("video-voiceover-text").innerText = `"${vid.voiceover_script.slice(0, 95)}..."`;
  resetVideo();
}

function toggleVideoPlayback() {
  const btn = document.getElementById("video-play-btn");
  if (videoPlaying) {
    // Pause
    clearInterval(videoTimerInterval);
    videoPlaying = false;
    btn.innerHTML = `<i data-lucide="play" class="w-3.5 h-3.5"></i> <span>Play Preview</span>`;
  } else {
    // Play
    videoPlaying = true;
    btn.innerHTML = `<i data-lucide="pause" class="w-3.5 h-3.5"></i> <span>Pause</span>`;
    videoTimerInterval = setInterval(updateVideoTick, 1000);
  }
  lucide.createIcons();
}

function resetVideo() {
  clearInterval(videoTimerInterval);
  videoPlaying = false;
  videoCurrentSecond = 0;
  document.getElementById("video-timer").innerText = "00:00 / 00:32";
  const btn = document.getElementById("video-play-btn");
  if (btn) btn.innerHTML = `<i data-lucide="play" class="w-3.5 h-3.5"></i> <span>Play Preview</span>`;
}

function updateVideoTick() {
  videoCurrentSecond++;
  if (videoCurrentSecond > 32) {
    resetVideo();
    return;
  }

  const secStr = videoCurrentSecond < 10 ? `0${videoCurrentSecond}` : `${videoCurrentSecond}`;
  document.getElementById("video-timer").innerText = `00:${secStr} / 00:32`;

  const sceneIcon = document.getElementById("video-scene-icon");
  const sceneLabel = document.getElementById("video-scene-label");
  const sceneTime = document.getElementById("video-scene-time");
  const subText = document.getElementById("video-voiceover-text");
  const fullScript = currentStudent.marketing.video.voiceover_script;

  if (videoCurrentSecond <= 6) {
    sceneIcon.innerText = "🏆";
    sceneLabel.innerText = `Scene 1: Pencapaian Ananda ${currentStudent.nama.split(" ")[0]}`;
    sceneTime.innerText = "00:00 - 00:06";
    subText.innerText = `"${fullScript.slice(0, 50)}..."`;
  } else if (videoCurrentSecond <= 16) {
    sceneIcon.innerText = "💻";
    sceneLabel.innerText = "Scene 2: Praktikum AutoCAD di Lab LIKDA";
    sceneTime.innerText = "00:06 - 00:16";
    subText.innerText = `"${fullScript.slice(50, 115)}..."`;
  } else if (videoCurrentSecond <= 25) {
    sceneIcon.innerText = "📐";
    sceneLabel.innerText = "Scene 3: Karya Gambar Denah & Detail Potongan";
    sceneTime.innerText = "00:16 - 00:25";
    subText.innerText = `"${fullScript.slice(115, 175)}..."`;
  } else {
    sceneIcon.innerText = "🏛️";
    sceneLabel.innerText = "Scene 4: Kebanggaan Program Studi Arsitektur";
    sceneTime.innerText = "00:25 - 00:32";
    subText.innerText = `"${fullScript.slice(175)}"` ;
  }
}

// Copy Instagram Caption
function copyInstagramCaption() {
  if (!currentStudent) return;
  const caption = `Alhamdulillah! Progres pembelajaran ananda ${currentStudent.nama} di Program Studi Arsitektur bulan ini menunjukkan dedikasi luar biasa.\n\n` +
    `Mulai dari perancangan denah presisi hingga kalkulasi detail potongan dan estimasi volume, karya nyata siap portofolio telah tuntas dengan predikat ${currentStudent.akademik.grade}.\n\n` +
    `Bangga bersama Program Studi Arsitektur!\n` +
    `#Arsitektur #MahasiswaArsitektur #KaryaArsitektur #AutoCAD #DesainBangunan #GenerasiUnggul`;
  
  navigator.clipboard.writeText(caption).then(() => {
    alert("Caption Instagram & Hashtag berhasil disalin ke Clipboard!");
  });
}

// =============================================================================
// TAB 4: WHATSAPP SIMULATOR RENDERING
// =============================================================================
function renderWhatsAppSimulation(student) {
  document.getElementById("wa-recipient-name").innerText = `Wali Murid ${student.nama}`;
  document.getElementById("wa-chat-bubble").innerText = student.marketing.wa_text;
  document.getElementById("wa-simulated-link").innerText = `https://siak-arsitektur.ac.id/rapor/mhs/${student.npm}`;
}

function copyWhatsAppMessage() {
  if (!currentStudent) return;
  navigator.clipboard.writeText(currentStudent.marketing.wa_text).then(() => {
    alert("Pesan WhatsApp resmi berhasil disalin ke Clipboard!");
  });
}

function openWhatsAppDirect() {
  if (!currentStudent) return;
  const encoded = encodeURIComponent(currentStudent.marketing.wa_text);
  window.open(`https://api.whatsapp.com/send?text=${encoded}`, "_blank");
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

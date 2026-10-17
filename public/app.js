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

    // Fetch Output Run Hierarchy Info
    fetch("/api/runs")
      .then(r => r.json())
      .then(runsData => {
        if (runsData && runsData.latest && runsData.latest.latest_timestamp) {
          const folderEl = document.getElementById("output-folder-display");
          const timeEl = document.getElementById("output-timestamp-text");
          if (folderEl) folderEl.innerText = `output/${runsData.latest.latest_course}/${runsData.latest.latest_timestamp}/`;
          if (timeEl) timeEl.innerText = `Sesi Terakhir: ${runsData.latest.latest_timestamp}`;
        }
      })
      .catch(e => console.log("Runs info fetch error:", e));

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

  // Profil Indeks Kompetensi Mandiri & Kesiapan Profesi (Pengganti Ranking Kelas)
  const statusKompetensi = currentStudent.akademik.status_kompetensi || "Kompeten Unggul";
  const kesiapanProfesi = currentStudent.akademik.kesiapan_profesi || "Kesiapan Industri Tinggi";
  const indeksKesiapan = currentStudent.akademik.indeks_kesiapan || 95;

  const rankPill = document.getElementById("mhs-ranking-pill");
  if (rankPill) {
    rankPill.innerText = `🎯 INDEKS KESIAPAN: ${indeksKesiapan}% (${statusKompetensi.toUpperCase()})`;
    if (indeksKesiapan >= 90) {
      rankPill.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono";
    } else if (indeksKesiapan >= 80) {
      rankPill.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-mono";
    } else {
      rankPill.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono";
    }
  }

  const statKompetensi = document.getElementById("mhs-stat-kompetensi");
  if (statKompetensi) statKompetensi.innerText = statusKompetensi;
  const statKesiapan = document.getElementById("mhs-stat-kesiapan");
  if (statKesiapan) statKesiapan.innerText = `Kesiapan: ${indeksKesiapan}%`;

  // Quick stats
  document.getElementById("mhs-stat-kehadiran").innerText = currentStudent.kehadiran.persentase + "%";
  document.getElementById("mhs-stat-absen-desc").innerText = `${currentStudent.kehadiran.hadir} / 6 Sesi Hadir`;
  document.getElementById("mhs-stat-nilai").innerText = currentStudent.akademik.nilai_rata_rata;
  document.getElementById("mhs-stat-grade").innerText = `Grade: ${currentStudent.akademik.grade}`;
  document.getElementById("mhs-stat-alpha").innerText = `${currentStudent.kehadiran.alpha}x`;

  // Render Radar Competency Chart
  renderRadarCompetencyChart(currentStudent.akademik.kompetensi);

  // Render 4 Deep AI Narrative Sections
  const ai = currentStudent.ai_diagnosis;
  const elKarakter = document.getElementById("ai-karakter-spasial");
  if (elKarakter) elKarakter.innerText = ai.analisis_karakter_spasial || ai.kekuatan || "";
  const elPotensi = document.getElementById("ai-potensi-kedepan");
  if (elPotensi) elPotensi.innerText = ai.potensi_kedepan || "";
  const elCatatan = document.getElementById("ai-catatan-mahasiswa");
  if (elCatatan) elCatatan.innerText = ai.catatan_khusus_mahasiswa || ai.kelemahan || "";
  const elPanduan = document.getElementById("ai-panduan-wali");
  if (elPanduan) elPanduan.innerText = ai.panduan_wali_murid || ai.saran_wali_murid || "";

  // Render 10 Real Future Careers Matrix
  renderCareerMatrix(ai.matriks_karier_10 || []);

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
          <div class="text-xs font-mono font-bold text-amber-400">${item.skor !== undefined ? item.skor : (item.skor_sesi || 85)}</div>
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

    const score = item.kecocokan_persen || 85;
    let badgeClass = "bg-slate-700 text-slate-300";
    let scoreColor = "text-amber-400";
    let barGradient = "from-amber-500 to-yellow-400";

    if (item.kategori_kecocokan === "Sangat Tinggi" || score >= 95) {
      badgeClass = "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
      scoreColor = "text-emerald-400";
      barGradient = "from-emerald-500 to-teal-400";
    } else if (item.kategori_kecocokan === "Tinggi" || score >= 90) {
      badgeClass = "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40";
      scoreColor = "text-cyan-400";
      barGradient = "from-cyan-500 to-blue-400";
    } else {
      badgeClass = "bg-amber-500/20 text-amber-300 border border-amber-500/40";
      scoreColor = "text-amber-400";
      barGradient = "from-amber-500 to-orange-400";
    }

    const skills = item.keterampilan_kunci ? item.keterampilan_kunci.split(",") : [];
    const skillsHtml = skills.map(sk => `<span class="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700/80 text-[10px] text-slate-300 font-mono">${sk.trim()}</span>`).join("");

    tr.innerHTML = `
      <td class="py-3 px-3 text-center font-mono font-bold text-slate-400">${item.id || idx + 1}</td>
      <td class="py-3 px-4">
        <div class="font-bold text-white text-xs">${item.profesi}</div>
        <div class="text-[11px] text-slate-400 font-mono mt-0.5">${item.bidang_industri}</div>
      </td>
      <td class="py-3 px-4 w-44">
        <div class="flex justify-between items-center mb-1">
          <span class="text-xs font-mono font-bold ${scoreColor}">${score}%</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold ${badgeClass}">${item.kategori_kecocokan}</span>
        </div>
        <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div class="h-1.5 rounded-full bg-gradient-to-r ${barGradient}" style="width: ${score}%"></div>
        </div>
      </td>
      <td class="py-3 px-4">
        <div class="flex flex-wrap gap-1 max-w-xs">
          ${skillsHtml}
        </div>
      </td>
      <td class="py-3 px-4 text-xs leading-relaxed">
        <p class="text-slate-200 mb-1.5 text-justify">${item.analisis_potensi}</p>
        <div class="p-1.5 rounded bg-slate-900/90 border border-amber-500/30 text-amber-300 text-[11px] flex items-start gap-1.5">
          <i data-lucide="sparkles" class="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5"></i>
          <span><strong>Langkah Pengembangan:</strong> ${item.saran_pengembangan}</span>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
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

  // Visual Box Architectural Vector Rendering (Eye-Catching Vector Blueprints)
  const visualBox = document.getElementById("slide-visual-box");
  if (index === 0) {
    // Slide 1: 3D Axonometric Wireframe House in glowing SVG
    visualBox.innerHTML = `
      <div class="w-full h-full flex flex-col items-center justify-center p-1 bg-slate-950/80 rounded-lg">
        <svg viewBox="0 0 160 100" class="w-full h-24">
          <polygon points="80,75 135,50 80,25 25,50" fill="rgba(0,240,255,0.12)" stroke="#00f0ff" stroke-width="1.5"/>
          <polygon points="50,40 105,15 105,45 50,70" fill="rgba(56,189,248,0.22)" stroke="#38bdf8" stroke-width="1.2"/>
          <polygon points="40,35 90,10 145,38 95,62" fill="rgba(255,183,3,0.18)" stroke="#ffb703" stroke-width="1.8"/>
          <line x1="50" y1="70" x2="50" y2="78" stroke="#00f0ff" stroke-width="2"/>
          <line x1="105" y1="65" x2="105" y2="73" stroke="#00f0ff" stroke-width="2"/>
        </svg>
        <div class="text-[9.5px] font-mono text-cyan-300 font-bold tracking-wider">3D AXONOMETRIC WIREFRAME</div>
      </div>
    `;
  } else if (index === 1) {
    // Slide 2: Interactive CAD Layer Palette & Lineweight Specs
    visualBox.innerHTML = `
      <div class="w-full h-full flex flex-col justify-center p-2.5 bg-slate-950/80 rounded-lg font-mono text-[9px] space-y-1">
        <div class="flex justify-between text-cyan-400 font-bold border-b border-slate-800 pb-1"><span>LAYER CAD</span><span>TEBAL</span></div>
        <div class="flex justify-between text-slate-300"><span>• Dinding 15cm</span><span class="text-cyan-300">0.50 mm</span></div>
        <div class="flex justify-between text-slate-300"><span>• Kusen Pintu</span><span class="text-sky-300">0.25 mm</span></div>
        <div class="flex justify-between text-slate-300"><span>• Garis Dimensi</span><span class="text-amber-300">0.13 mm</span></div>
        <div class="flex justify-between text-slate-400"><span>• Arsiran Hatch</span><span>0.05 mm</span></div>
      </div>
    `;
  } else if (index === 2) {
    // Slide 3: Architectural Floor Plan Blueprint (Scale 1:100)
    visualBox.innerHTML = `
      <div class="w-full h-full flex flex-col items-center justify-center p-1 bg-slate-950/80 rounded-lg">
        <svg viewBox="0 0 150 90" class="w-full h-20">
          <rect x="25" y="15" width="100" height="60" fill="none" stroke="#00f0ff" stroke-width="1.5"/>
          <line x1="75" y1="15" x2="75" y2="75" stroke="#00f0ff" stroke-width="1.2"/>
          <line x1="25" y1="45" x2="75" y2="45" stroke="#00f0ff" stroke-width="1.2"/>
          <circle cx="25" cy="15" r="3" fill="#ffb703"/>
          <circle cx="75" cy="15" r="3" fill="#ffb703"/>
          <circle cx="125" cy="15" r="3" fill="#ffb703"/>
          <text x="35" y="32" fill="#fff" font-size="6" font-family="Plus Jakarta Sans">K. TIDUR</text>
          <text x="85" y="45" fill="#fff" font-size="6" font-family="Plus Jakarta Sans">R. TAMU</text>
          <line x1="25" y1="82" x2="125" y2="82" stroke="#ffb703" stroke-width="0.8"/>
          <text x="65" y="87" fill="#ffb703" font-size="6" font-family="JetBrains Mono">7.50 m</text>
        </svg>
        <div class="text-[9.5px] font-mono text-cyan-300 font-bold">DENAH DWG SCALE 1:100</div>
      </div>
    `;
  } else {
    // Slide 4: Official Certificate Seal
    visualBox.innerHTML = `
      <div class="w-full h-full flex flex-col items-center justify-center p-1 text-center bg-slate-950/80 rounded-lg">
        <div class="w-12 h-12 rounded-full border-2 border-dashed border-amber-400 flex flex-col items-center justify-center bg-amber-500/10 shadow-lg shadow-amber-500/20 mb-1">
          <span class="text-base">🏛️</span>
          <span class="text-[6.5px] font-black text-amber-400 font-mono">IAI UNGGUL</span>
        </div>
        <div class="text-[9.5px] font-bold text-white uppercase">SERTIFIKASI STUDIO</div>
        <div class="text-[8.5px] font-mono text-amber-400">Akreditasi BAN-PT</div>
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
// TAB 4: WHATSAPP SIMULATOR RENDERING (DENGAN LAMPIRAN PDF)
// =============================================================================
function renderWhatsAppSimulation(student) {
  document.getElementById("wa-recipient-name").innerText = `Wali Murid ${student.nama}`;
  
  const courseName = (masterData && masterData.course && masterData.course.nama_mk) ? masterData.course.nama_mk : "Aplikasi Komputer Arsitektur & QS";
  const openingText = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\nKepada Yth. Bapak/Ibu Wali Murid dari *${student.nama}*,\n\nSalam hangat dan salam sejahtera dari Program Studi Arsitektur, Fakultas Teknik & Desain.\n\nBerikut kami sampaikan Surat Resmi Perkembangan Akademik, Portofolio Pembelajaran, dan Pemetaan 10 Karier Masa Depan ananda pada mata kuliah *${courseName}* untuk periode semester berjalan:`;
  document.getElementById("wa-opening-text").innerText = openingText;

  const sanitizedName = student.nama.replace(/\s+/g, "_");
  document.getElementById("wa-card-file-1").innerText = `01_rekap_kehadiran_${student.npm}.pdf`;
  document.getElementById("wa-card-file-2").innerText = `02_rapor_akhir_kompetensi_${student.npm}.pdf`;
  document.getElementById("wa-card-file-3").innerText = `05_deckcraft_portofolio_${student.npm}.pdf`;
}

function copyWhatsAppMessage() {
  if (!currentStudent) return;
  const courseName = (masterData && masterData.course && masterData.course.nama_mk) ? masterData.course.nama_mk : "Aplikasi Komputer Arsitektur & QS";
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

  navigator.clipboard.writeText(fullMsg).then(() => {
    alert("Pesan pembuka resmi & daftar lampiran WhatsApp berhasil disalin!");
  });
}

function openWhatsAppDirect() {
  if (!currentStudent) return;
  const fullMsg = `Assalamu’alaikum Warahmatullahi Wabarakatuh.\n` +
    `Kepada Yth. Bapak/Ibu Wali Murid dari *${currentStudent.nama}*,\n\n` +
    `Berikut kami sampaikan berkas Laporan Hasil Belajar & Portofolio Arsitektur ananda dalam 3 lampiran dokumen PDF resmi terverifikasi. Terima kasih atas bimbingan dan dukungan Bapak/Ibu di rumah.\n\n` +
    `Hormat kami,\nProgram Studi Arsitektur`;
  const encoded = encodeURIComponent(fullMsg);
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

// =============================================================================
// PDF DOWNLOAD CONTROLLER FUNCTIONS (LIVE ON-DEMAND DYNAMIC SYNC)
// =============================================================================
function downloadKaprodiGradebook() {
  window.open("/api/pdf/download?type=gradebook", "_blank");
}

function downloadDosenAuditPDF() {
  window.open("/api/pdf/download?type=audit", "_blank");
}

function downloadCurrentStudentMonthlyPDF() {
  if (!currentStudent) return;
  window.open(`/api/pdf/download?type=monthly&npm=${currentStudent.npm}`, "_blank");
}

function downloadCurrentStudentFinalPDF() {
  if (!currentStudent) return;
  window.open(`/api/pdf/download?type=rapor&npm=${currentStudent.npm}`, "_blank");
}

function downloadCurrentStudentDeckcraftPDF() {
  if (!currentStudent) return;
  window.open(`/api/pdf/download?type=deckcraft&npm=${currentStudent.npm}`, "_blank");
}

function downloadAll3StudentPDFs() {
  if (!currentStudent) return;
  downloadCurrentStudentMonthlyPDF();
  setTimeout(() => downloadCurrentStudentFinalPDF(), 400);
  setTimeout(() => downloadCurrentStudentDeckcraftPDF(), 800);
}

// Live Interactive 16:9 Presentation Viewer
function openLiveDeckcraft() {
  if (!currentStudent) return;
  window.open(`/api/deckcraft_html?npm=${currentStudent.npm}`, "_blank");
}

// Dynamic Course Switcher
async function switchActiveCourse(courseId) {
  try {
    const res = await fetch(`/api/switch_course?course=${encodeURIComponent(courseId)}`);
    const resData = await res.json();
    if (resData.success) {
      console.log("[COURSE SWITCHED] Active:", resData.active_course.nama_mk);
      // Reload entire academic dataset & views
      await loadAcademicData();
      const titleEl = document.getElementById("current-course-title");
      if (titleEl) titleEl.innerText = resData.active_course.nama_mk;
      
      // Update select value if not matching
      const sel = document.getElementById("course-selector");
      if (sel) sel.value = courseId;
    }
  } catch (err) {
    console.error("Failed to switch course:", err);
  }
}


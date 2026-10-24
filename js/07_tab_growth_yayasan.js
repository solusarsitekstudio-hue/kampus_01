/* =============================================================================
 * MODUL: public/js/07_tab_growth_yayasan.js
 * DESKRIPSI: Tab Pertumbuhan PMB, Matriks 30 MK & Modal Asistensi
 * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)
 * ============================================================================= */

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
          <button onclick="bukaModalEvaluasiMkRawan('${escapeHtml(r.id || r.kode_mk)}')" class="touch-target px-2.5 py-1 bg-slate-800 hover:bg-emerald-600 text-slate-300 hover:text-white border border-slate-700 rounded-lg font-bold text-[10.5px] transition inline-flex items-center gap-1">
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

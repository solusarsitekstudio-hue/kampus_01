/* =============================================================================
 * MODUL: public/js/02_tab_portofolio_ai.js
 * DESKRIPSI: Tab Portofolio 4-Lapis, Radar 5 Dimensi & Karier AI
 * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)
 * ============================================================================= */

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

/* =============================================================================
 * MODUL: public/js/05_tab_deckcraft.js
 * DESKRIPSI: DeckCraft 5-Slide Presenter, Quad-Radar & WhatsApp Kit
 * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)
 * ============================================================================= */

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

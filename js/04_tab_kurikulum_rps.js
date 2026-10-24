/* =============================================================================
 * MODUL: public/js/04_tab_kurikulum_rps.js
 * DESKRIPSI: Tab Kurikulum Bertingkat, Tree 30 MK & RPS Editor
 * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)
 * ============================================================================= */

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

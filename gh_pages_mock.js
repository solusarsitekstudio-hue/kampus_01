/**
 * gh_pages_mock.js - Client-Side Mock Fetch Interceptor for GitHub Pages
 * SIAK-KAPRODI (Architecture Program Studi)
 * 
 * Memungkinkan 100% dashboard berjalan di lingkungan hosting statis (GitHub Pages)
 * tanpa backend Python aktif, dengan mengarahkan API GET ke file JSON pre-baked.
 */

(function () {
  console.log("[SHOWCASE] Inisialisasi GitHub Pages Static Interceptor...");

  const STATIC_API_MAP = {
    "/api/data": "./static_api/data.json",
    "/api/courses": "./static_api/courses.json",
    "/api/kurikulum": "./static_api/kurikulum.json",
    "/api/identitas": "./static_api/identitas.json",
    "/api/registry/cohorts": "./static_api/registry_cohorts.json",
    "/api/analytics/growth": "./static_api/analytics_growth.json",
    "/api/analytics/overview": "./static_api/analytics_overview.json",
    "/api/bridge/summary": "./static_api/bridge_summary.json",
    "/api/bridge/retakes": "./static_api/bridge_retakes.json",
    "/api/executive_cockpit": "./static_api/executive_cockpit.json",
    "/api/runs": "./static_api/runs.json",
    "/api/periode": "./static_api/periode.json",
    "/api/perkembangan": "./static_api/perkembangan.json",
    "/api/portofolio": "./static_api/portofolio.json"
  };

  const _origFetch = window.fetch;

  window.fetch = async function (input, init = {}) {
    let url = typeof input === "string" ? input : input.url || "";
    const method = (init.method || "GET").toUpperCase();

    // Normalisasi url jika menggunakan absolute domain 127.0.0.1
    if (url.includes("/api/")) {
      const parsedPath = url.split("?")[0].replace(/^https?:\/\/[^/]+/, "");
      
      // Handle POST actions in showcase mode
      if (method === "POST") {
        if (parsedPath === "/api/auth/verify_pin") {
          let reqPin = "";
          try {
            if (init.headers && (init.headers["X-Kaprodi-PIN"] || (init.headers.get && init.headers.get("X-Kaprodi-PIN")))) {
              reqPin = init.headers["X-Kaprodi-PIN"] || init.headers.get("X-Kaprodi-PIN");
            } else if (init.body) {
              const bodyObj = typeof init.body === "string" ? JSON.parse(init.body) : init.body;
              reqPin = bodyObj.pin || "";
            }
          } catch (e) {}

          if (String(reqPin).trim() === "404040") {
            return new Response(JSON.stringify({ status: "ok", authenticated: true }), {
              status: 200,
              headers: { "Content-Type": "application/json" }
            });
          } else {
            return new Response(JSON.stringify({ status: "error", message: "PIN Kaprodi salah." }), {
              status: 401,
              headers: { "Content-Type": "application/json" }
            });
          }
        }

        console.warn(`[SHOWCASE MOCK] Aksi ${method} ${parsedPath} ditangkap dalam mode statis.`);
        alert("🔒 MODE SHOWCASE GITHUB PAGES (READ-ONLY)\n\nFitur mutasi data (Simpan Kurikulum / Konfigurasi Identitas / Regenerasi Master) dinonaktifkan di hosting statis publik demi keamanan data.\n\nUntuk operasional penuh, jalankan server operasional lokal via START_TUNNEL.bat.");
        return new Response(JSON.stringify({ status: "ok", message: "Showcase mode read-only", mock: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        });
      }

      // Handle Auth Status in showcase mode
      if (parsedPath === "/api/auth/status") {
        const authed = sessionStorage.getItem("siak_kaprodi_auth") === "unlocked";
        return new Response(JSON.stringify({ external: true, pin_required: true, pin_verified: authed }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        });
      }

      // Handle PDF Download redirection in showcase
      if (parsedPath.includes("/api/pdf/download")) {
        const urlParams = new URLSearchParams(url.split("?")[1] || "");
        const rawType = (urlParams.get("type") || "03").toLowerCase();
        let targetPdf = "./generated_pdfs/03_laporan_penilaian_kaprodi_master_gradebook.pdf";
        if (["01", "monthly", "presensi", "rekap", "rekap_kehadiran"].includes(rawType)) {
          targetPdf = "./generated_pdfs/01_sample_master.pdf";
        } else if (["02", "rapor", "final", "rapor_studio"].includes(rawType)) {
          targetPdf = "./generated_pdfs/02_sample_master.pdf";
        } else if (["04", "evaluasi", "dosen", "audit", "evaluasi_dosen"].includes(rawType)) {
          targetPdf = "./generated_pdfs/04_laporan_evaluasi_dosen_dan_kurikulum_rps.pdf";
        } else if (["05", "deckcraft", "deck"].includes(rawType)) {
          targetPdf = "./generated_pdfs/05_sample_master.pdf";
        } else if (["05b", "portofolio_lengkap", "porto4", "porto_lengkap", "portofolio"].includes(rawType)) {
          targetPdf = "./generated_pdfs/05b_sample_master.pdf";
        } else if (["06", "boardroom", "boardroom_pitch", "executive_pitch"].includes(rawType)) {
          targetPdf = "./generated_pdfs/06_boardroom_pitch_deck_yayasan.pdf";
        } else if (["07", "cohort", "cohort_report", "laporan_kohort", "yayasan", "laporan_yayasan"].includes(rawType)) {
          targetPdf = "./generated_pdfs/07_laporan_audit_kohort_multitahun_dan_kas_bss.pdf";
        }
        
        window.open(targetPdf, "_blank");
        return new Response(new Blob(["mock"]), { status: 200 });
      }

      // Map GET routes to static pre-baked JSON
      for (const [route, staticFile] of Object.entries(STATIC_API_MAP)) {
        if (parsedPath === route || parsedPath.startsWith(route)) {
          return _origFetch(staticFile, init);
        }
      }

      // Fallback untuk student detail / kurikulum detail
      if (parsedPath.startsWith("/api/student/")) {
        return _origFetch("./static_api/student_sample.json", init);
      }
      if (parsedPath.startsWith("/api/registry/student")) {
        return _origFetch("./static_api/registry_student.json", init);
      }
      if (parsedPath.startsWith("/api/kurikulum/detail")) {
        return _origFetch("./static_api/kurikulum_detail.json", init);
      }
      if (parsedPath.startsWith("/api/bridge/presensi")) {
        return _origFetch("./static_api/bridge_presensi.json", init);
      }
      if (parsedPath.startsWith("/api/bridge/nilai")) {
        return _origFetch("./static_api/bridge_nilai.json", init);
      }
      if (parsedPath.startsWith("/api/bridge/course_detail")) {
        const urlParams = new URLSearchParams(url.split("?")[1] || "");
        const cid = (urlParams.get("id") || "").trim();
        try {
          const allRes = await _origFetch("./static_api/bridge_course_detail_all.json", init);
          if (allRes.ok) {
            const allMap = await allRes.json();
            if (allMap && cid && allMap[cid]) {
              return new Response(JSON.stringify(allMap[cid]), {
                status: 200,
                headers: { "Content-Type": "application/json" }
              });
            }
          }
        } catch (e) {}
        return _origFetch("./static_api/bridge_course_detail.json", init);
      }
    }

    return _origFetch(input, init);
  };

  // Tampilkan Banner Showcase Halus di Atas Layar (Desktop only, disembunyikan di Mobile)
  window.addEventListener("DOMContentLoaded", function () {
    const bannerStyle = document.createElement("style");
    bannerStyle.textContent = `
      @media (max-width: 768px) {
        #showcase-gh-pages-banner {
          display: none !important;
          pointer-events: none !important;
        }
        body {
          padding-top: 0px !important;
        }
      }
    `;
    document.head.appendChild(bannerStyle);

    const banner = document.createElement("div");
    banner.id = "showcase-gh-pages-banner";
    banner.style.cssText = "position:fixed;top:0;left:0;right:0;height:32px;background:linear-gradient(90deg,#0f172a,#1e293b);color:#38bdf8;font-size:12px;font-weight:600;display:flex;align-items:center;justify-content:space-between;padding:0 16px;z-index:99999;border-bottom:1px solid #334155;box-shadow:0 2px 8px rgba(0,0,0,0.4);font-family:ui-sans-serif,system-ui,sans-serif;";
    banner.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="background:#0284c7;color:#fff;padding:2px 8px;border-radius:999px;font-size:10px;letter-spacing:0.05em;text-transform:uppercase;">Showcase 24/7</span>
        <span>SIAK-KAPRODI (Arsitektur Intelligence) — Live Public Static Demo di GitHub Pages</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;font-size:11px;color:#94a3b8;">
        <span>🔒 Mode Read-Only Interaktif</span>
        <span style="color:#64748b;">|</span>
        <span style="color:#e2e8f0;">Operasional Lengkap: PC Kaprodi (Local / Tunnel)</span>
      </div>
    `;
    document.body.prepend(banner);
    if (window.innerWidth > 768) {
      document.body.style.paddingTop = "32px";
    }
  });
})();

# 🗺️ BUG MAPPING & SURGICAL DISPATCH: SIAK-KAPRODI UI BUTTON AUDIT
**Tanggal Temuan:** 2026-10-24 15:35:00  
**Tanggal Penyelesaian:** 2026-10-24 15:50:00  
**Total Temuan:** 8 Bug (3 🔴 Critical, 3 🟡 Warning, 2 🟢 Minor)  
**Status Eksekusi:** ALL_RESOLVED  

---

## 💥 1. LAPIS 1: ALUR VISUAL KONSLET (STATUS: TERATASI 100%)

```mermaid
flowchart TD
    subgraph KONSLET_1["✅ Tab 7 (Cockpit Yayasan) - FIXED"]
        A1["Klik Tombol Unduh Paket Akreditasi"] -->|Memanggil Handler Resmi| B1["unduhPaketLengkapAkreditasiProdi()"]
        B1 -->|Terhubung ke Backend & Static Mock| C1["✅ BUG-02: Paket Berhasil Diunduh"]
        C1 -->|Ditambah 3 Tombol Eksekutif| D1["Pitch Deck PDF, Salin Naskah, Refresh Cockpit Aktif"]
    end

    subgraph KONSLET_2["✅ Tab 2 (Wali Murid) - FIXED"]
        A2["User Akses Tab 2 (Wali)"] -->|Memilih Layer Radar| B2["4 Tombol Switcher Aktif"]
        B2 -->|switchRadarLayer('softskill' / 'modul_mk' / 'semester' / 'potensi_cr')| C2["✅ BUG-05: Radar Dinamis Berputar"]
        C2 -->|Breakdown 5 Dimensi Terupdate| D2["Visual Kompetensi Arsitektur Interaktif 100%"]
    end

    subgraph KONSLET_3["✅ Sidebar Hotkey & Form Anchoring - FIXED"]
        A3["User Navigasi Cepat"] -->|4 Hotkey Siaga (At-Risk, Gradebook, Dosen, Grafik)| B3["✅ BUG-04 & BUG-06: Hotkey Lengkap & Form Anchored"]
        B3 -->|Simpan Identitas & Kurikulum Ber-ID Kabel| D3["Navigasi Instan & Form Sinkron Sesuai MAPPING_UI.md"]
    end

    style C1 fill:#10b981,stroke:#059669,color:#fff
    style D1 fill:#10b981,stroke:#059669,color:#fff
    style C2 fill:#10b981,stroke:#059669,color:#fff
    style D2 fill:#10b981,stroke:#059669,color:#fff
    style B3 fill:#10b981,stroke:#059669,color:#fff
    style D3 fill:#10b981,stroke:#059669,color:#fff
```

---

## 📋 2. TABEL KOORDINAT BEDAH (FAST-TRACK FIX DISPATCH)

| ID Bug | Severity | Titik Konslet (Root Cause) | Aliran Transmisi Error | Dampak Kabel (Blast Radius) | Tindakan Bedah (Surgical Fix) | Status |
|---|---|---|---|---|---|---|
| `BUG-01` | 🔴 Critical | [`public/index.html#L1708`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | Arbitrary Tailwind class tidak ada di CSS $\to$ modal transparan & angka melayang. | `UI-AUTH-01` & Visual Dashboard | Definisikan CSS baku eksplisit di [`public/style.css`](file:///e:/WORKSPACE/KAMPUS_01/public/style.css). | `[✅ FIXED]` |
| `BUG-02` | 🔴 Critical | [`public/index.html#L1878`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | Memanggil fungsi `downloadExecutivePackagePDF()` yang TIDAK ADA di `app.js`. | `UI-TAB7-02` | Ganti target onclick menjadi `unduhPaketLengkapAkreditasiProdi()` dan sematkan ID `#btn-yayasan-unduh-paket`. | `[✅ FIXED]` |
| `BUG-03` | 🔴 Critical | [`public/index.html#L1875`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | 3 Tombol Eksekutif Yayasan hilang dari header Tab 7 padahal fungsi di `app.js` sudah siap. | `UI-TAB7-03`, `UI-TAB7-04`, `UI-TAB7-05` | Pasang 3 tombol: Unduh PDF 06 (`#btn-yayasan-unduh-pdf`), Salin Naskah Pitch (`#btn-yayasan-copy-pitch`), Refresh Realtime (`#btn-yayasan-refresh`). | `[✅ FIXED]` |
| `BUG-04` | 🟡 Warning | [`public/index.html#L240`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | Hotkey sidebar footer hanya ada 2 tombol (At-Risk & Gradebook), 2 tombol lain hilang. | `UI-HK-02`, `UI-HK-03` | Tambahkan `#btn-quick-audit-dosen` (`switchTab('dosen')`) dan `#btn-quick-observatorium` (`switchTab('analytics')`) ke grid hotkey sidebar. | `[✅ FIXED]` |
| `BUG-05` | 🟡 Warning | [`public/index.html#L625`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | 4 Tombol Switcher Layer Radar Kompetensi Arsitektur tidak dipasang di atas radar chart. | `UI-TAB2-03`, `UI-TAB2-04`, `UI-TAB2-05` | Pasang switcher 4 tombol: `#btn-radar-softskill`, `#btn-radar-modul_mk`, `#btn-radar-semester`, `#btn-radar-potensi_cr` serta elemen `#radar-breakdown-grid`. | `[✅ FIXED]` |
| `BUG-06` | 🟡 Warning | [`public/index.html#L1284`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) & [`#L1436`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | Tombol "Simpan Identitas" & "Simpan ke Tree Kurikulum" berupa `type="submit"` polos tanpa ID dan onclick langsung. | `UI-TAB12-02`, `UI-TAB3-02` | Berikan `id="btn-simpan-identitas"` + `onclick="simpanIdentitas()"` dan `id="btn-simpan-kurikulum"` + `onclick="simpanKurikulum()"`. | `[✅ FIXED]` |
| `BUG-07` | 🟢 Minor | [`public/index.html#L1029-1064`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | 3 Tombol ikon download di kartu WhatsApp tidak memiliki `onclick` dan `type="button"`. | `UI-TAB11-03`, `UI-TAB11-04`, `UI-TAB11-05` | Tambahkan `type="button"` dan `onclick` eksplisit pada masing-masing tombol ikon download kartu. | `[✅ FIXED]` |
| `BUG-08` | 🟢 Minor | Multi-file [`public/index.html`](file:///e:/WORKSPACE/KAMPUS_01/public/index.html) | Tombol aksi utama (Gradebook, Dosen Audit, JSON, Rekap, Portofolio, Shortcut At-Risk) tidak ber-ID kabel. | Wire Integrasi `MAPPING_UI.md` | Tambahkan ID kabel baku (`#btn-unduh-gradebook`, `#btn-unduh-audit-dosen`, `#btn-export-json`, `#btn-unduh-monthly`, `#btn-unduh-rapor`, `#btn-kpi-at-risk-shortcut`, dll). | `[✅ FIXED]` |

---

## ⚡ 3. FAST-TRACK OPERATIONAL COMMANDS (KONTROL EKSEKUSI)
- Status: **ALL RESOLVED**. Seluruh 8 bug tombol UI telah diperbaiki, diverifikasi via Playwright automated headless probe, dan terbukti 100% bebas error konsol!

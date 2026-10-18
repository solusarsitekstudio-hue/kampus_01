/**
 * tailwind.config.js - Konfigurasi Tailwind untuk SIAK-KAPRODI
 * ===========================================================
 * TAHAP C-1.
 *
 * Dua hal penting di sini:
 *
 * 1. FONT AKHIRNYA DIPAKAI.
 *    index.html sudah lama memuat "Plus Jakarta Sans" dan "JetBrains Mono"
 *    dari Google Fonts, dan seluruh halaman memakai class `font-sans` /
 *    `font-mono`. Tapi keduanya TIDAK PERNAH didaftarkan ke tema Tailwind,
 *    jadi Tailwind menjatuhkan `font-sans` ke daftar font bawaan sistem dan
 *    `font-mono` ke Consolas/Menlo. Artinya: dua keluarga font diunduh
 *    (bandwidth terbuang) tetapi nol kelas terender dengan font itu.
 *    Sekarang didaftarkan, jadi desain tampil sesuai maksudnya.
 *
 * 2. `content` hanya menyasar file yang benar-benar ada.
 *    Kalau ada HTML yang dibangun server dan memakai class Tailwind,
 *    tambahkan file/sumbernya di sini, karena JIT hanya mengekstrak class
 *    yang terlihat di file yang dipindai.
 */
const defaultTheme = require("tailwindcss/defaultTheme");

module.exports = {
  content: [
    "../../public/index.html",
    "../../public/app.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', ...defaultTheme.fontFamily.sans],
        mono: ['"JetBrains Mono"', ...defaultTheme.fontFamily.mono],
      },
    },
  },
  plugins: [],
};

/* =============================================================================
 * MODUL: public/js/08_mobile_drawer.js
 * DESKRIPSI: Mobile Drawer & Context Filter Toggle
 * SISTEM: AL-ANALISIS / SIAK-KAPRODI (Arsitektur Intelligence)
 * ============================================================================= */

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

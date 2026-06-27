const API = window.location.origin;

const theme = {
  init() {
    const saved = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
    this._sync(saved);
  },
  toggle() {
    const cur = document.documentElement.getAttribute("data-theme");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    this._sync(next);
  },
  _sync(t) {
    document.querySelectorAll(".theme-toggle").forEach(b => {
      b.innerHTML = t === "dark"
        ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg> Light`
        : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg> Dark`;
    });
  }
};

const auth = {
  getToken() { return localStorage.getItem("token"); },
  setToken(t) { localStorage.setItem("token", t); },
  getUser() { try { return JSON.parse(localStorage.getItem("user")); } catch { return null; } },
  setUser(u) { localStorage.setItem("user", JSON.stringify(u)); },
  logout() { localStorage.clear(); window.location.href = "/login.html"; },
  require() { if (!this.getToken()) { window.location.href = "/login.html"; return false; } return true; }
};

async function apiFetch(path, options = {}) {
  const token = auth.getToken();
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (res.status === 401) { auth.logout(); return null; }
  return res;
}

function formatSize(b) {
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b/1024).toFixed(1)} KB`;
  if (b < 1073741824) return `${(b/1048576).toFixed(1)} MB`;
  return `${(b/1073741824).toFixed(1)} GB`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function fileEmoji(type) {
  if (!type) return "📄";
  if (type.startsWith("image/")) return "🖼️";
  if (type.startsWith("video/")) return "🎬";
  if (type.startsWith("audio/")) return "🎵";
  if (type.includes("pdf")) return "📕";
  if (type.includes("zip")||type.includes("tar")||type.includes("gz")) return "📦";
  if (type.includes("text")||type.includes("json")) return "📝";
  return "📄";
}

function showAlert(el, msg, type = "error") { el.textContent = msg; el.className = `alert alert-${type} show`; }
function hideAlert(el) { el.className = "alert"; }

document.addEventListener("DOMContentLoaded", () => {
  theme.init();
  document.querySelectorAll(".theme-toggle").forEach(b => b.addEventListener("click", () => theme.toggle()));
});
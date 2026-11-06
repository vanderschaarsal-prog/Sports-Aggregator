const SPORTS = {
  all:      { label: "All",          emoji: "📰", color: "#6366f1" },
  football: { label: "Football",     emoji: "⚽", color: "#22c55e" },
  f1:       { label: "Formula 1",    emoji: "🏎️", color: "#ef4444" },
  nfl:      { label: "NFL",          emoji: "🏈", color: "#3b82f6" },
  nba:      { label: "NBA",          emoji: "🏀", color: "#f97316" },
  tennis:   { label: "Tennis",       emoji: "🎾", color: "#eab308" },
  cycling:  { label: "Cycling",      emoji: "🚴", color: "#06b6d4" },
  skating:  { label: "Skating",      emoji: "⛸️", color: "#8b5cf6" },
  mlb:      { label: "MLB",          emoji: "⚾", color: "#dc2626" },
  darts:    { label: "Darts",        emoji: "🎯", color: "#10b981" },
  mma:      { label: "MMA / UFC",    emoji: "🥊", color: "#f59e0b" },
  nhl:      { label: "NHL",          emoji: "🏒", color: "#0ea5e9" },
  dutch:    { label: "Dutch Sports", emoji: "🇳🇱", color: "#ff6600" },
  olympics: { label: "Olympics",     emoji: "🏅", color: "#0077c8" },
};

const API_URL = "/api/news";

let activeSport = "all";
let allArticles = [];
let fetchedAt = null;
let refreshTimer = null;

const feed = document.getElementById("feed");
const status = document.getElementById("status");
const refreshBtn = document.getElementById("refresh-btn");
const refreshIcon = document.getElementById("refresh-icon");

function timeAgo(ts) {
  if (!ts) return "";
  const diff = Math.floor((Date.now() / 1000) - ts);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function buildTabs() {
  const tabs = document.getElementById("tabs");
  tabs.innerHTML = "";
  for (const [key, cfg] of Object.entries(SPORTS)) {
    const btn = document.createElement("button");
    btn.className = "tab" + (key === activeSport ? " active" : "");
    btn.dataset.sport = key;
    btn.style.setProperty("--sport-color", cfg.color);
    btn.textContent = `${cfg.emoji} ${cfg.label}`;
    btn.addEventListener("click", () => switchSport(key));
    tabs.appendChild(btn);
  }
}

function switchSport(sport) {
  activeSport = sport;
  document.querySelectorAll(".tab").forEach(t => {
    const active = t.dataset.sport === sport;
    t.classList.toggle("active", active);
    if (active) t.style.setProperty("--sport-color", SPORTS[sport].color);
  });
  renderArticles();
}

function renderSkeletons() {
  feed.innerHTML = Array.from({ length: 9 }, () => `
    <div class="skeleton">
      <div class="skel-line" style="height:14px;width:40%"></div>
      <div class="skel-line" style="height:16px;width:90%"></div>
      <div class="skel-line" style="height:16px;width:75%"></div>
      <div class="skel-line" style="height:12px;width:60%"></div>
    </div>
  `).join("");
}

function renderArticles() {
  const filtered = activeSport === "all"
    ? allArticles
    : allArticles.filter(a => a.sport === activeSport);

  if (!filtered.length) {
    feed.innerHTML = `<div id="empty"><span style="font-size:40px">📭</span><p>No articles found for this sport.<br>Some feeds may be unavailable.</p></div>`;
    return;
  }

  feed.innerHTML = filtered.map(a => {
    const cfg = SPORTS[a.sport] || SPORTS.all;
    return `
      <a class="card" href="${escHtml(a.link)}" target="_blank" rel="noopener noreferrer"
         style="--sport-color:${cfg.color}">
        <div class="card-meta">
          <span class="sport-badge">${cfg.emoji} ${cfg.label}</span>
          <span class="source">${escHtml(a.source)}</span>
          <span class="time">${timeAgo(a.published)}</span>
        </div>
        <div class="card-title">${escHtml(a.title)}</div>
        ${a.summary ? `<div class="card-summary">${escHtml(a.summary)}</div>` : ""}
      </a>
    `;
  }).join("");
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function updateStatus() {
  if (!fetchedAt) { status.textContent = ""; return; }
  const mins = Math.floor((Date.now() - fetchedAt) / 60000);
  status.textContent = mins < 1 ? "Updated just now" : `Updated ${mins}m ago`;
}

async function loadNews(force = false) {
  refreshBtn.classList.add("loading");
  refreshIcon.textContent = "↻";

  if (!allArticles.length) renderSkeletons();

  try {
    const url = API_URL + (force ? `?_=${Date.now()}` : "");
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    allArticles = data.articles || [];
    fetchedAt = Date.now();
    updateStatus();
    renderArticles();
  } catch (err) {
    if (!allArticles.length) {
      feed.innerHTML = `<div id="empty"><span style="font-size:40px">⚠️</span><p>Could not load news.<br><small>${escHtml(err.message)}</small></p></div>`;
    }
    status.textContent = "Failed to refresh";
  } finally {
    refreshBtn.classList.remove("loading");
    refreshIcon.textContent = "↻";
  }
}

function scheduleAutoRefresh() {
  clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    loadNews();
    updateStatus();
  }, 15 * 60 * 1000);

  setInterval(updateStatus, 60 * 1000);
}

refreshBtn.addEventListener("click", () => loadNews(true));

buildTabs();
loadNews();
scheduleAutoRefresh();

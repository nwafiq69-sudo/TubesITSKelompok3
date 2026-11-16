/* ==========================================================================
   Gamified ITS - Adaptive Learning & Engagement Engine
   Frontend Application Script (Vanilla JS + Fetch API)
   ========================================================================== */
"use strict";

const $ = (id) => document.getElementById(id);

const state = {
  player: null,
  meta: null,
  history: [],
  quiz: null,
  timer: null,
  currentTab: "dashboard",
};

const FEATURED_PLAYER_IDS = Object.freeze({
  "arif anggraini": "STD047",
  "naufal lestari": "STD139",
  "dimas wijaya": "STD057",
});

// ------------------------------------------------------------------ Utilities
function el(tag, props, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k === "html") node.innerHTML = v;
    else node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c != null) {
      if (typeof c === "string" || typeof c === "number") {
        node.append(document.createTextNode(String(c)));
      } else {
        node.append(c);
      }
    }
  }
  return node;
}

function toast(msg, kind = "success") {
  const t = $("toast");
  t.dataset.kind = kind;
  const close = el("button", { type: "button", class: "toast-close", "aria-label": "Tutup notifikasi", text: "×" });
  close.addEventListener("click", () => { t.hidden = true; });
  t.replaceChildren(
    el("span", { class: "toast-icon", html: svgIcon(kind === "error" ? "warning" : "check", 18) }),
    el("span", { class: "toast-message", text: msg }),
    close,
  );
  t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.hidden = true), 4000);
}

function askConfirmation(title, message) {
  const dialog = $("confirm-dialog");
  if (dialog.open) return Promise.resolve(false);
  $("confirm-title").textContent = title;
  $("confirm-message").textContent = message;

  return new Promise((resolve) => {
    const accept = $("confirm-accept");
    const cancel = $("confirm-cancel");
    const close = $("confirm-close");
    let settled = false;
    const finish = (approved) => {
      if (settled) return;
      settled = true;
      accept.removeEventListener("click", onAccept);
      cancel.removeEventListener("click", onDismiss);
      close.removeEventListener("click", onDismiss);
      dialog.removeEventListener("cancel", onEscape);
      dialog.removeEventListener("click", onBackdrop);
      dialog.removeEventListener("close", onClosed);
      if (dialog.open) dialog.close();
      resolve(approved);
    };
    const onAccept = () => finish(true);
    const onDismiss = () => finish(false);
    const onEscape = (event) => { event.preventDefault(); finish(false); };
    const onBackdrop = (event) => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) finish(false);
    };
    const onClosed = () => finish(false);
    accept.addEventListener("click", onAccept);
    cancel.addEventListener("click", onDismiss);
    close.addEventListener("click", onDismiss);
    dialog.addEventListener("cancel", onEscape);
    dialog.addEventListener("click", onBackdrop);
    dialog.addEventListener("close", onClosed);
    dialog.showModal();
    cancel.focus();
  });
}

async function api(path, options = {}) {
  const opts = { headers: { "Content-Type": "application/json" }, ...options };
  if (opts.body && typeof opts.body !== "string") opts.body = JSON.stringify(opts.body);
  let res;
  try {
    res = await fetch(path, opts);
  } catch (e) {
    throw new Error("Tidak bisa menghubungi server. Pastikan backend uvicorn berjalan.");
  }
  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    /* bukan format JSON */
  }
  if (!res.ok) {
    let msg = (data && (data.message || data.detail)) || `Terjadi kesalahan (${res.status})`;
    if (data && Array.isArray(data.errors) && data.errors.length) {
      msg += ": " + data.errors.map((e) => `${e.field} - ${e.message}`).join("; ");
    }
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

const store = {
  get() {
    try { return localStorage.getItem("its_player_id"); } catch (e) { return null; }
  },
  set(v) {
    try { localStorage.setItem("its_player_id", v); } catch (e) { /* no-op */ }
  },
  clear() {
    try { localStorage.removeItem("its_player_id"); } catch (e) { /* no-op */ }
  },
};

const fmtTime = (s) => String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");

const BADGE_ICON = {
  "Quiz Finisher": "🏁",
  "High Achiever": "🌟",
  "Persistent Learner": "💪",
  "Learning Streak": "🔥",
  "Remedial Cleared": "🛠️",
};

const XP_LABEL = {
  skor: "Skor kuis",
  bonus_akurasi: "Bonus akurasi tinggi (≥85%)",
  bonus_selesai: "Bonus selesai 100%",
  bonus_streak: "Bonus streak aktif",
  penalti_hint: "Penalti penggunaan hint",
};

// One consistent line icon set for navigation, course topics, and states.
const ICON_PATHS = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  quiz: '<path d="M8 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8l-5-5h-3"/><path d="M8 3h8v5h5M8 13h8M8 17h5"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
  badge: '<circle cx="12" cy="8" r="5"/><path d="m8 12-2 9 6-3 6 3-2-9"/>',
  streak: '<path d="M12 22c4.5 0 7-3 7-7 0-3-2-5-3-6 .2 3-1 4-1 4-1-3-3-4-3-9-3 2-4 5-4 7-1-1-1-2-1-3-2 2-3 4-3 7 0 4 3 7 8 7Z"/>',
  levels: '<path d="m12 2 4 4-4 4-4-4 4-4ZM4 14l4-4 4 4-4 4-4-4ZM16 14l4-4 4 4-4 4-4-4ZM12 18l4-4 4 4-4 4-4-4Z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  trophy: '<path d="M8 3h8v8a4 4 0 0 1-8 0V3ZM8 5H4v3a4 4 0 0 0 4 4M16 5h4v3a4 4 0 0 1-4 4M12 15v4M8 21h8"/>',
  brain: '<path d="M12 5a3 3 0 0 0-6 0 4 4 0 0 0-2 7 4 4 0 0 0 3 7 3 3 0 0 0 5 1V5ZM12 5a3 3 0 0 1 6 0 4 4 0 0 1 2 7 4 4 0 0 1-3 7 3 3 0 0 1-5 1V5Z"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  panel: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M14 9l-3 3 3 3"/>',
  code: '<path d="m8 8-4 4 4 4m8-8 4 4-4 4m-3-14-4 20"/>',
  branch: '<path d="M6 3v12a4 4 0 0 0 4 4h8M6 9a4 4 0 0 0 4-4h8M4 3h4M16 3h4M16 17h4"/>',
  loop: '<path d="M20 7V3l-3 3a8 8 0 1 0 2 10M20 3h-5"/>',
  function: '<path d="M5 12h4m7 0h3M10 5c-2 0-2 3-2 7s0 7-2 7m8-14c2 0 2 3 2 7s0 7 2 7"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  warning: '<path d="M12 3 2.5 20h19L12 3Z"/><path d="M12 9v5m0 3h.01"/>',
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>',
};
const svgIcon = (name, size = 22) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON_PATHS[name] || ICON_PATHS.code}</svg>`;

// Rich text renderer: code blocks and inline formatting
function renderRichText(container, text) {
  container.replaceChildren();
  if (!text) return;
  text.split("```").forEach((part, i) => {
    if (i % 2 === 1) {
      container.append(el("pre", {}, el("code", { text: part.replace(/^\n/, "").replace(/\n$/, "") })));
    } else if (part.trim()) {
      const p = el("p");
      part.trim().split("`").forEach((seg, j) => {
        p.append(j % 2 === 1 ? el("code", { text: seg }) : document.createTextNode(seg));
      });
      container.append(p);
    }
  });
}

// ------------------------------------------------------------------ Tab & Navigation
function showTab(name) {
  state.currentTab = name;
  document.querySelectorAll(".sidebar-nav .nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === name);
  });

  const tabTitles = {
    dashboard: "Dashboard",
    quiz: "Kuis Interaktif",
    history: "Hasil Kuis",
    badges: "XP & Badges",
    streak: "Learning Streak",
    "dynamic-level": "Dynamic Level",
    recommendation: "Rekomendasi",
    leaderboard: "Leaderboard",
    "evaluasi-ml": "Evaluasi ML",
    "dataset-riiid": "Dataset Riiid",
  };

  const title = tabTitles[name] || "Dashboard";
  const bCur = $("breadcrumb-current");
  if (bCur) bCur.textContent = title;

  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.hidden = panel.id !== "tab-" + name;
  });

  // Close mobile sidebar if open
  closeSidebar();

  // Lazy render tabs
  if (name === "dashboard") renderDashboard();
  else if (name === "quiz") {
    if (!state.quiz) renderLevelSelect();
  } else if (name === "history") loadHistory();
  else if (name === "badges") renderBadgesTab();
  else if (name === "streak") renderStreakTab();
  else if (name === "dynamic-level") renderDynamicLevelTab();
  else if (name === "recommendation") renderRecommendationTab();
  else if (name === "leaderboard") loadLeaderboard();
  else if (name === "evaluasi-ml") renderEvaluasiMLTab();
  else if (name === "dataset-riiid") renderDatasetRiiidTab();
}

function openSidebar() {
  $("sidebar").classList.add("open");
  $("sidebar-overlay").classList.add("active");
}

function toggleSidebarWidth() {
  const layout = document.querySelector(".layout-wrapper");
  const collapsed = layout.classList.toggle("sidebar-collapsed");
  const button = $("btn-collapse-sidebar");
  button.setAttribute("aria-label", collapsed ? "Besarkan menu" : "Kecilkan menu");
  button.title = collapsed ? "Besarkan menu" : "Kecilkan menu";
  try { localStorage.setItem("its_sidebar_collapsed", collapsed ? "1" : "0"); } catch (e) { /* no-op */ }
}

function closeSidebar() {
  $("sidebar").classList.remove("open");
  $("sidebar-overlay").classList.remove("active");
}

// ------------------------------------------------------------------ Authentication
function showLogin() {
  closeSidebar();
  document.querySelector(".layout-wrapper").classList.add("logged-out");
  $("view-login").hidden = false;
  $("view-app").hidden = true;
  $("breadcrumb-current").textContent = "Mulai Belajar";
  $("input-name").focus();
}

function applyPlayer(p) {
  const changingPlayer = state.player && state.player.id !== p.id;
  if (changingPlayer) state.history = [];
  state.player = p;
  document.querySelector(".layout-wrapper").classList.remove("logged-out");
  $("view-login").hidden = true;
  $("view-app").hidden = false;

  const sideAvatar = $("side-avatar");
  if (sideAvatar) sideAvatar.textContent = (p.name || "N").charAt(0).toUpperCase();

  const sideName = $("side-user-name");
  if (sideName) sideName.textContent = p.name;

  const sideRole = $("side-user-role");
  if (sideRole) sideRole.textContent = "Mahasiswa";

  renderDashboard();
  loadHistory();
}

async function login() {
  const name = $("input-name").value.trim();
  if (name.length < 2) return toast("Nama mahasiswa minimal 2 karakter.", "error");
  $("btn-login").disabled = true;
  try {
    const featuredId = FEATURED_PLAYER_IDS[name.replace(/\s+/g, " ").toLowerCase()];
    const p = featuredId
      ? await api(`/api/players/${featuredId}`)
      : await api("/api/players", { method: "POST", body: { name } });
    store.set(p.id);
    applyPlayer(p);
    showTab("dashboard");
    toast(`Selamat datang, ${p.name}!`);
  } catch (e) {
    toast(e.message, "error");
  } finally {
    $("btn-login").disabled = false;
  }
}

function logout() {
  store.clear();
  stopTimer();
  state.player = null;
  state.quiz = null;
  state.history = [];
  state.currentTab = "dashboard";
  $("input-name").value = "";
  $("quiz-select").hidden = false;
  $("quiz-play").hidden = true;
  $("quiz-result").hidden = true;
  $("toast").hidden = true;
  showLogin();
}

// ------------------------------------------------------------------ Dashboard Rendering
function renderDashboard() {
  const p = state.player;
  if (!p) return;

  // Hero Card text
  const heroSub = $("hero-subinfo");
  if (heroSub) {
    heroSub.textContent = `Level ${p.level} · ${state.meta.levels[p.level]}`;
  }

  const heroName = $("hero-name");
  if (heroName) heroName.textContent = p.name;

  const isMandiri = (p.rata_rata_skor >= 75) || (p.level >= 3);
  const statusStr = !p.jumlah_kuis ? "Belum mulai" : isMandiri ? "Mandiri" : "Perlu Bimbingan";

  const heroStatusText = $("hero-status-text");
  if (heroStatusText) heroStatusText.textContent = statusStr;

  const heroKnn = $("hero-knn-status");
  if (heroKnn) heroKnn.textContent = statusStr;

  const heroJst = $("hero-jst-status");
  if (heroJst) heroJst.textContent = statusStr;

  // Hero Metrics
  const dashXp = $("dash-xp");
  if (dashXp) dashXp.textContent = p.total_xp;

  const totalBadgesCount = state.meta ? Object.keys(state.meta.badges).length : 5;
  const dashBadges = $("dash-badges");
  if (dashBadges) dashBadges.textContent = `${p.badges.length} / ${totalBadgesCount}`;

  const dashStreak = $("dash-streak");
  if (dashStreak) dashStreak.textContent = `${p.streak} Hari`;
  document.querySelectorAll(".streak-mini-mascot, .streak-mascot").forEach((icon) => {
    icon.classList.toggle("mascot-idle", p.streak === 0);
  });

  const dashRank = $("dash-rank-name");
  if (dashRank) dashRank.textContent = p.rank_xp.rank;

  const dashLevelCap = $("dash-level-caption");
  const dashLevelPct = $("dash-level-percent");
  const dashLevelBar = $("dash-level-bar");

  const pct = Math.min(100, Math.round((p.level / 5) * 100));
  if (dashLevelCap) {
    dashLevelCap.textContent = p.level >= 5
      ? "Semua level terbuka"
      : `Level ${p.level} dari 5 terbuka`;
  }
  if (dashLevelPct) dashLevelPct.textContent = `${pct}%`;
  if (dashLevelBar) dashLevelBar.style.width = `${pct}%`;

  // 5 KPI Cards
  const avgScore = Number(p.rata_rata_skor || 0).toFixed(1);
  const kpiAvg = $("kpi-avg-score");
  if (kpiAvg) kpiAvg.textContent = avgScore;

  // Last score from history or fallback
  const lastScore = state.history[0] ? Number(state.history[0].score).toFixed(1) : "0.0";
  const kpiLast = $("kpi-last-score");
  if (kpiLast) kpiLast.textContent = lastScore;

  const kpiDelta = $("kpi-delta-text");
  if (kpiDelta) kpiDelta.textContent = state.history.length > 1
    ? `Delta: ${(state.history[0].score - state.history[1].score).toFixed(1)} poin`
    : "Belum ada perbandingan";

  const quizCount = p.jumlah_kuis || 0;
  const kpiQuiz = $("kpi-quiz-count");
  if (kpiQuiz) kpiQuiz.textContent = quizCount;

  const kpiMod = $("kpi-unique-modules");
  if (kpiMod) {
    const triedLevels = p.level_pernah_dikerjakan || [...new Set(state.history.map((h) => h.level))];
    kpiMod.textContent = `${triedLevels.length} level pernah dicoba`;
  }

  const kpiAcc = $("kpi-accuracy");
  if (kpiAcc) kpiAcc.textContent = `${avgScore}%`;

  const kpiTime = $("kpi-avg-time");
  if (kpiTime) kpiTime.textContent = "—";

  const perfBadge = $("dash-perf-badge-text");
  if (perfBadge) perfBadge.textContent = statusStr;

  // Render Charts
  renderScoreChart();
  renderXPChart();

  // Quest Line
  renderQuestLine($("dash-quest-line"), p);

  // Badge preview
  renderBadgePreview($("dash-badge-preview"), p);
}

function renderScoreChart() {
  const box = $("chart-scores-bars");
  if (!box) return;
  box.replaceChildren();

  const points = state.history.slice(0, 7).reverse().map((h, i) => ({
    label: `Kuis ${i + 1}`,
    val: Math.round(h.score),
  }));

  if (!points.length) {
    box.append(el("p", { class: "chart-empty", text: "Belum ada nilai kuis. Kerjakan kuis pertama untuk melihat progresmu." }));
    return;
  }

  points.forEach((pt) => {
    const item = el("div", { class: "chart-bar-item" },
      el("div", { class: "chart-bar-rect", style: `height: ${Math.max(15, pt.val)}%;` },
        el("div", { class: "chart-bar-tooltip", text: `${pt.val} Poin` })
      ),
      el("span", { class: "chart-bar-label", text: pt.label })
    );
    box.append(item);
  });
}

function renderXPChart() {
  const box = $("chart-xp-bars");
  if (!box) return;
  box.replaceChildren();

  const recent = state.history.slice(0, 7).reverse();
  if (!recent.length) {
    box.append(el("p", { class: "chart-empty", text: "XP masih 0. Selesaikan kuis untuk mulai mengumpulkannya." }));
    return;
  }
  let cumulative = state.player.total_xp - recent.reduce((sum, h) => sum + h.xp, 0);
  const xpPoints = recent.map((h, i) => {
    cumulative += h.xp;
    return { label: `Kuis ${i + 1}`, val: cumulative };
  });
  const maxVal = Math.max(...xpPoints.map((x) => x.val), 1);

  xpPoints.forEach((pt) => {
    const pct = Math.min(100, Math.max(8, Math.round((pt.val / maxVal) * 100)));
    const item = el("div", { class: "chart-bar-item" },
      el("div", {
        class: "chart-bar-rect",
        style: `height: ${pct}%; background: linear-gradient(180deg, #8b5cf6, #6d28d9);`,
      },
        el("div", { class: "chart-bar-tooltip", text: `${pt.val} XP` })
      ),
      el("span", { class: "chart-bar-label", text: pt.label })
    );
    box.append(item);
  });
}

function renderQuestLine(container, p) {
  if (!container || !state.meta) return;
  container.replaceChildren();
  for (let lv = 1; lv <= 5; lv++) {
    const cls = lv === p.level ? "current" : lv <= p.level_terbuka ? "open" : "";
    container.append(
      el("li", { class: cls },
        el("div", { class: "node", text: lv <= p.level_terbuka ? String(lv) : "🔒" }),
        el("div", { text: state.meta.levels[lv] || `Level ${lv}` })
      )
    );
  }
}

function renderBadgePreview(container, p) {
  if (!container || !state.meta) return;
  container.replaceChildren();
  for (const [name, desc] of Object.entries(state.meta.badges)) {
    const earned = p.badges.includes(name);
    container.append(
      el("div", { class: "badge-compact-pill" + (earned ? " earned" : "") },
        el("span", { text: BADGE_ICON[name] || "🏅" }),
        el("span", { text: name })
      )
    );
  }
}

// ------------------------------------------------------------------ History Loading
async function loadHistory() {
  if (!state.player) return;
  const playerId = state.player.id;
  const body = $("history-body");
  try {
    const data = await api(`/api/players/${encodeURIComponent(playerId)}`);
    if (!state.player || state.player.id !== playerId) return;
    state.history = data.riwayat || [];
    renderDashboard();
    if (state.currentTab === "quiz" && !state.quiz) renderLevelSelect();
    if (!body) return;
    body.replaceChildren();

    if (!state.history.length) {
      body.append(
        el("tr", {},
          el("td", { colspan: "5", class: "muted", text: "Belum ada riwayat pengerjaan kuis. Mulai kuis pertamamu sekarang!" })
        )
      );
      return;
    }

    state.history.forEach((h) => {
      body.append(
        el("tr", {},
          el("td", { text: h.created_at.replace("T", " ") }),
          el("td", { text: `Level ${h.level} - ${(state.meta && state.meta.levels[h.level]) || 'Materi'}` }),
          el("td", { text: `${Math.round(h.score)} / 100` }),
          el("td", {}, el("span", { class: "pill " + (h.status === "Tuntas" ? "pill-mandiri" : "pill-dark"), text: h.status })),
          el("td", { text: `+${h.xp} XP` })
        )
      );
    });
  } catch (e) {
    toast(e.message, "error");
  }
}

// ------------------------------------------------------------------ 10 Questions Interactive Quiz
function renderLevelSelect() {
  const p = state.player;
  if (!p || !state.meta) return;

  const recoText = $("quiz-reco-text");
  if (recoText) {
    recoText.textContent = `Level rekomendasi untukmu: Level ${p.level} - ${state.meta.levels[p.level]}. `
      + `Setiap kuis kini berisi 10 soal interaktif dengan durasi pengerjaan 10 menit. Navigasi nomor soal di samping dapat diklik langsung.`;
  }

  const grid = $("level-grid");
  if (!grid) return;
  grid.replaceChildren();

  const courseIcons = ["code", "branch", "loop", "function", "brain"];
  for (let lv = 1; lv <= 5; lv++) {
    const locked = lv > p.level_terbuka;
    const isReco = lv === p.level;
    const completed = (p.level_pernah_dikerjakan || []).includes(lv) || state.history.some((h) => Number(h.level) === lv);
    const title = state.meta.levels[lv] || `Level ${lv}`;
    const status = locked ? "Terkunci" : completed ? "Sudah dikerjakan" : "Siap dikerjakan";
    const statusIcon = locked ? "lock" : completed ? "check" : "arrow";
    const detail = el("details", { class: `course-item${locked ? " locked" : ""}${completed ? " completed" : ""}${isReco ? " reco" : ""}` });
    const summary = el("summary", { class: "course-summary" },
      el("span", { class: `course-icon course-icon-${lv}`, html: svgIcon(courseIcons[lv - 1], 26) }),
      el("span", { class: "course-copy" },
        el("small", { text: `MATERI ${String(lv).padStart(2, "0")}${isReco ? " · DIREKOMENDASIKAN" : ""}` }),
        el("strong", { text: title }),
        el("span", { class: "course-status", html: svgIcon(statusIcon, 16) + status })
      ),
      el("span", { class: "course-chevron", html: svgIcon("chevron", 20) })
    );
    detail.append(summary);
    const content = el("div", { class: "course-content" },
      el("p", { text: locked ? "Selesaikan materi sebelumnya untuk membuka kuis ini." : completed ? "Materi ini sudah kamu kerjakan. Ulangi untuk memperkuat pemahaman dan meningkatkan skor." : "Kerjakan 10 soal interaktif untuk menguji pemahamanmu pada materi ini." })
    );
    if (!locked) {
      const action = el("button", { type: "button", class: "btn btn-primary course-action", html: `${svgIcon(completed ? "loop" : "arrow", 18)} ${completed ? "Ulangi Kuis" : "Mulai Kuis"}` });
      action.addEventListener("click", () => startQuiz(lv));
      content.append(action);
    }
    detail.append(content);
    detail.addEventListener("toggle", () => {
      if (detail.open) grid.querySelectorAll(".course-item").forEach((other) => { if (other !== detail) other.open = false; });
    });
    if (isReco && !locked) detail.open = true;
    grid.append(detail);
  }
}

function startTimer() {
  stopTimer();
  state.quiz.t0 = Date.now();
  const timerElem = $("quiz-timer");
  if (timerElem) timerElem.textContent = "00:00";
  state.timer = setInterval(() => {
    const sec = Math.floor((Date.now() - state.quiz.t0) / 1000);
    if (timerElem) timerElem.textContent = fmtTime(sec);
  }, 1000);
}

function stopTimer() {
  if (state.timer) clearInterval(state.timer);
  state.timer = null;
}

async function startQuiz(level) {
  if (!state.player) return;
  const playerId = state.player.id;
  try {
    const q = await api(`/api/quiz/${level}?player_id=${encodeURIComponent(playerId)}`);
    if (!state.player || state.player.id !== playerId) return;
    state.quiz = {
      level,
      judul: q.judul,
      soal: q.soal,               // 10 questions
      currentIndex: 0,            // active question index (0..9)
      jawaban: {},                // map question_idx -> { question_id, selected_index, hint_digunakan }
      feedback: {},               // map question_idx -> { benar, jawaban_benar, penjelasan }
      feedbackViews: 0,
      t0: Date.now(),
    };

    $("quiz-select").hidden = true;
    $("quiz-result").hidden = true;
    $("quiz-play").hidden = false;

    startTimer();
    renderQuestion(0);
    renderNavGrid();
  } catch (e) {
    toast(e.message, "error");
  }
}

// Render active question (Left Column)
function renderQuestion(idx) {
  const z = state.quiz;
  if (!z || !z.soal || !z.soal[idx]) return;

  z.currentIndex = idx;
  const s = z.soal[idx];
  const letters = ["A", "B", "C", "D"];

  // Header info
  const qNum = $("quiz-q-num");
  if (qNum) qNum.textContent = `Soal ${idx + 1} / ${z.soal.length}`;

  const qTopic = $("quiz-q-topic");
  if (qTopic) qTopic.textContent = `Topik: ${s.topic || state.meta.levels[z.level] || 'ITS Engine'}`;

  // Question Prompt
  renderRichText($("quiz-question"), s.text);

  // Options (A, B, C, D)
  const optionsBox = $("quiz-options");
  optionsBox.replaceChildren();

  const currentAnswer = z.jawaban[idx];
  const currentFb = z.feedback[idx];

  s.options.forEach((optText, optIdx) => {
    const optBtn = el("button", {
      type: "button",
      class: "quiz-option-btn",
    },
      el("span", { class: "option-badge", text: letters[optIdx] }),
      el("span", { class: "option-text", text: optText })
    );

    // If already answered, show verification state
    if (currentAnswer) {
      optBtn.disabled = true;
      if (currentFb) {
        if (optIdx === currentFb.jawaban_benar) {
          optBtn.classList.add("correct");
        }
        if (!currentFb.benar && optIdx === currentAnswer.selected_index) {
          optBtn.classList.add("wrong");
        }
      }
      if (optIdx === currentAnswer.selected_index) {
        optBtn.classList.add("selected");
      }
    } else {
      optBtn.addEventListener("click", () => answerQuestion(optIdx));
    }

    optionsBox.append(optBtn);
  });

  // Hint
  const hintBtn = $("btn-hint");
  const hintTxt = $("hint-text");
  if (currentAnswer && currentAnswer.hint_digunakan) {
    if (hintBtn) hintBtn.disabled = true;
    if (hintTxt) hintTxt.textContent = "Hint: " + s.hint;
  } else if (currentAnswer) {
    if (hintBtn) hintBtn.disabled = true;
    if (hintTxt) hintTxt.textContent = "";
  } else {
    if (hintBtn) hintBtn.disabled = false;
    if (hintTxt) hintTxt.textContent = "";
  }

  // Feedback Panel
  const fbPanel = $("quiz-feedback");
  const fbVerdict = $("fb-verdict");
  const fbExplain = $("fb-explain");
  const btnExplain = $("btn-explain");

  if (currentFb) {
    fbPanel.hidden = false;
    fbVerdict.textContent = currentFb.benar
      ? "✅ Benar! Kerja bagus."
      : "❌ Belum tepat. Jawaban yang benar telah ditandai.";
    fbVerdict.className = "fb-verdict " + (currentFb.benar ? "ok" : "bad");
    renderRichText(fbExplain, currentFb.penjelasan);
    fbExplain.hidden = false;
    if (btnExplain) btnExplain.hidden = true;
  } else {
    fbPanel.hidden = true;
    if (fbExplain) fbExplain.hidden = true;
    if (btnExplain) btnExplain.hidden = false;
  }

  // Prev & Next Buttons
  const btnPrev = $("btn-quiz-prev");
  if (btnPrev) {
    btnPrev.disabled = idx === 0;
  }

  const btnNext = $("btn-quiz-next");
  if (btnNext) {
    btnNext.textContent = idx === z.soal.length - 1 ? "Selesaikan Kuis →" : "Berikutnya →";
  }

  // Refresh navigation active highlight
  updateNavGridActiveState();
}

// Answer selection handler
async function answerQuestion(optionIdx) {
  const z = state.quiz;
  const idx = z.currentIndex;
  if (!z || z.jawaban[idx]) return;

  const s = z.soal[idx];
  const hintUsed = $("hint-text").textContent.length > 0;

  // Optimistically disable option buttons
  const optButtons = [...$("quiz-options").children];
  optButtons.forEach((b) => (b.disabled = true));
  $("btn-hint").disabled = true;

  try {
    const r = await api("/api/quiz/check", {
      method: "POST",
      body: { question_id: s.id, selected_index: optionIdx },
    });

    // Store answer & feedback
    z.jawaban[idx] = { question_id: s.id, selected_index: optionIdx, hint_digunakan: hintUsed };
    z.feedback[idx] = r;

    // Apply visual feedback
    optButtons[r.jawaban_benar].classList.add("correct");
    if (!r.benar) {
      optButtons[optionIdx].classList.add("wrong");
    }
    optButtons[optionIdx].classList.add("selected");

    const fbPanel = $("quiz-feedback");
    const fbVerdict = $("fb-verdict");
    const fbExplain = $("fb-explain");
    fbVerdict.textContent = r.benar
      ? "✅ Benar! Kerja bagus."
      : "❌ Belum tepat. Jawaban yang benar sudah ditandai hijau.";
    fbVerdict.className = "fb-verdict " + (r.benar ? "ok" : "bad");
    renderRichText(fbExplain, r.penjelasan);
    fbExplain.hidden = false;
    fbPanel.hidden = false;

    // Update Question Navigation Card (Right Card)
    renderNavGrid();
  } catch (e) {
    toast(e.message, "error");
    optButtons.forEach((b) => (b.disabled = false));
  }
}

// Render Question Navigation Grid (Right Card - "card soal disamping buat jadi interaktif")
function renderNavGrid() {
  const z = state.quiz;
  if (!z) return;

  const grid = $("quiz-nav-grid");
  if (!grid) return;
  grid.replaceChildren();

  const total = z.soal.length;
  let answeredCount = 0;

  for (let i = 0; i < total; i++) {
    const isAnswered = Boolean(z.jawaban[i]);
    if (isAnswered) answeredCount += 1;
    const isActive = i === z.currentIndex;

    let stateClass = "unanswered";
    if (isAnswered) stateClass = "answered";
    if (isActive) stateClass = "active";

    const btn = el("button", {
      type: "button",
      class: `q-nav-num-btn ${stateClass}`,
      text: String(i + 1),
      title: `Buka Soal Nomor ${i + 1}`,
    });

    // Interactive jump to question
    btn.addEventListener("click", () => {
      renderQuestion(i);
    });

    grid.append(btn);
  }

  const ratio = $("nav-answered-ratio");
  if (ratio) ratio.textContent = `${answeredCount} / ${total}`;
}

function updateNavGridActiveState() {
  const z = state.quiz;
  if (!z) return;
  const grid = $("quiz-nav-grid");
  if (!grid) return;

  const buttons = grid.children;
  for (let i = 0; i < buttons.length; i++) {
    const isAnswered = Boolean(z.jawaban[i]);
    const isActive = i === z.currentIndex;

    buttons[i].className = "q-nav-num-btn " + (isActive ? "active" : isAnswered ? "answered" : "unanswered");
  }
}

function useHint() {
  const z = state.quiz;
  if (!z) return;
  const idx = z.currentIndex;
  if (z.jawaban[idx]) return;

  const s = z.soal[idx];
  $("hint-text").textContent = "Hint: " + s.hint;
  $("btn-hint").disabled = true;
}

function showExplanation() {
  const z = state.quiz;
  if (!z) return;
  $("fb-explain").hidden = false;
  $("btn-explain").hidden = true;
  z.feedbackViews += 1;
}

function prevQuestion() {
  const z = state.quiz;
  if (!z || z.currentIndex <= 0) return;
  renderQuestion(z.currentIndex - 1);
}

function nextQuestion() {
  const z = state.quiz;
  if (!z) return;
  if (z.currentIndex < z.soal.length - 1) {
    renderQuestion(z.currentIndex + 1);
  } else {
    finishAndSubmitQuiz();
  }
}

async function finishAndSubmitQuiz() {
  const z = state.quiz;
  if (!z || !state.player) return;
  const playerId = state.player.id;

  const total = z.soal.length;
  const answeredCount = Object.keys(z.jawaban).length;

  if (answeredCount < total) {
    const un = total - answeredCount;
    const ok = await askConfirmation("Kirim kuis sekarang?", `Masih ada ${un} soal yang belum dijawab. Kamu bisa kembali mengerjakan atau mengirim jawaban yang sudah ada.`);
    if (!ok || state.quiz !== z || !state.player || state.player.id !== playerId) return;
  }

  stopTimer();
  $("btn-quiz-submit").disabled = true;
  const durasi = Math.max(1, Math.round((Date.now() - z.t0) / 1000));

  // Build answers list
  const answersList = [];
  for (let i = 0; i < total; i++) {
    const j = z.jawaban[i];
    if (j) {
      answersList.push(j);
    } else {
      answersList.push({
        question_id: z.soal[i].id,
        selected_index: null,
        hint_digunakan: false,
      });
    }
  }

  try {
    const hasil = await api("/api/quiz/submit", {
      method: "POST",
      body: {
        player_id: playerId,
        level: z.level,
        jawaban: answersList,
        duration_seconds: durasi,
        feedback_views: z.feedbackViews,
      },
    });

    if (!state.player || state.player.id !== playerId || state.quiz !== z) return;

    state.quiz = null;
    $("quiz-play").hidden = true;
    renderResult(hasil, z.level);
    applyPlayer(hasil.pemain);
    toast("Kuis berhasil dikirim! Performa telah dicatat.");
  } catch (e) {
    if (state.player && state.player.id === playerId && state.quiz === z) {
      toast(e.message, "error");
      startTimer();
    }
  } finally {
    $("btn-quiz-submit").disabled = false;
  }
}

// ------------------------------------------------------------------ Result Card
function renderResult(h, levelKuis) {
  const box = $("quiz-result");
  if (!box) return;
  box.replaceChildren();

  const g = h.gamifikasi;
  const k = h.klasifikasi;
  const ok = k.status_rule === "Tuntas";

  box.append(
    el("div", { class: "result-head" },
      el("h3", { text: "Hasil Evaluasi Kuis Adaptif" }),
      el("div", { class: "score-ring " + (ok ? "ok" : "bad"), text: String(Math.round(h.hasil_kuis.skor)) }),
      el("span", { class: "pill " + (ok ? "pill-mandiri" : "pill-dark"), text: `Status: ${k.status_rule}` }),
      el("p", {
        class: "muted small",
        text: `Akurasi ${h.hasil_kuis.akurasi}% · Kelengkapan Soal ${h.hasil_kuis.kelengkapan}%`,
      })
    )
  );

  // Level Up / Level Adjustment Banner
  if (g.level_terbuka_baru) {
    box.append(
      el("div", { class: "banner up", text: `🎉 Selamat! Level ${g.level_baru} berhasil terbuka. Tantangan baru telah menantimu.` })
    );
  } else if (g.level_baru > g.level_lama) {
    box.append(
      el("div", { class: "banner up", text: `⬆️ Hebat! Level kamu naik ke level ${g.level_baru}.` })
    );
  } else if (g.level_baru < g.level_lama) {
    box.append(
      el("div", { class: "banner", text: `📘 Level disesuaikan ke level ${g.level_baru} untuk penguatan materi dasar.` })
    );
  }

  if (g.badge_baru && g.badge_baru.length) {
    box.append(
      el("div", { class: "banner up", text: "🏅 Badge baru didapatkan: " + g.badge_baru.join(", ") })
    );
  }

  // XP breakdown
  const xpBox = el("div", { class: "box" }, el("h4", { text: "Rincian Perolehan XP" }));
  for (const [key, val] of Object.entries(g.rincian_xp)) {
    xpBox.append(
      el("div", { class: "xp-line" },
        el("span", { text: XP_LABEL[key] || key }),
        el("span", { class: val < 0 ? "neg" : "", text: (val > 0 ? "+" : "") + val })
      )
    );
  }
  xpBox.append(
    el("div", { class: "xp-line total" },
      el("span", { text: "Total XP Didapat" }),
      el("span", { text: `+${g.xp_didapat} XP` })
    )
  );

  // ITS AI Analysis Box
  const aiBox = el("div", { class: "box" },
    el("h4", { text: "Analisis Intelligent Tutor System" }),
    el("p", {
      class: "small",
      text: `Model ${k.model} memprediksi peluang kebutuhan remedial: ${Math.round(k.prob_perlu_remedial * 100)}% (Prediksi: ${k.prediksi_model}).`,
    }),
    el("p", { class: "small", text: `Skor Keterlibatan (Engagement Score): ${h.engagement_estimasi} / 100.` }),
    el("p", { class: "small", text: `Learning Streak: 🔥 ${g.streak_hari} hari berturut-turut.` })
  );

  box.append(el("div", { class: "result-grid" }, xpBox, aiBox));

  // Adaptive Feedback
  box.append(
    el("div", { class: "box", style: "margin-top: 1rem;" },
      el("h4", { text: "Umpan Balik Adaptif · " + h.umpan_balik.rekomendasi }),
      el("p", { text: h.umpan_balik.pesan })
    )
  );

  // Action Buttons
  const again = el("button", { type: "button", class: "btn btn-primary", text: "Kerjakan Kuis Lagi" });
  again.addEventListener("click", () => {
    box.hidden = true;
    $("quiz-select").hidden = false;
    renderLevelSelect();
  });

  const dash = el("button", { type: "button", class: "btn btn-secondary", text: "Kembali ke Dashboard" });
  dash.addEventListener("click", () => {
    box.hidden = true;
    $("quiz-select").hidden = false;
    showTab("dashboard");
  });

  box.append(el("div", { style: "display: flex; gap: 0.8rem; margin-top: 1.2rem;" }, again, dash));
  box.hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ------------------------------------------------------------------ Badges & Streak Tabs
function renderBadgesTab() {
  const p = state.player;
  if (!p || !state.meta) return;

  const r = p.rank_xp;
  $("tab-rank-pill").textContent = r.rank;
  $("tab-rank-bar").style.width = r.persen + "%";
  $("tab-rank-text").textContent = r.rank_berikutnya
    ? `${p.total_xp} / ${r.xp_target} XP menuju rank ${r.rank_berikutnya}`
    : `${p.total_xp} XP — Rank tertinggi tercapai!`;

  const grid = $("tab-badge-grid");
  grid.replaceChildren();

  for (const [name, desc] of Object.entries(state.meta.badges)) {
    const earned = p.badges.includes(name);
    grid.append(
      el("div", { class: "badge-item" + (earned ? " earned" : "") },
        el("span", { class: "badge-icon", text: BADGE_ICON[name] || "🏅" }),
        el("strong", { text: name }),
        el("span", { class: "badge-desc", text: desc })
      )
    );
  }
}

function renderStreakTab() {
  const p = state.player;
  if (!p) return;

  const streakDays = p.streak;
  const dayElem = $("streak-tab-days");
  if (dayElem) dayElem.textContent = `${streakDays} Hari`;
  const caption = $("streak-tab-caption");
  if (caption) caption.textContent = streakDays ? "Learning Streak Aktif" : "Belum ada streak";

  const track = $("streak-week-track");
  if (!track) return;
  track.replaceChildren();

  const daysOfWeek = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
  daysOfWeek.forEach((d, i) => {
    const isActive = i >= 7 - Math.min(7, streakDays);
    track.append(
      el("div", { class: "streak-day-box" + (isActive ? " active" : "") },
        el("span", { class: "day-name", text: d }),
        el("span", { class: "day-icon streak-flame" + (isActive ? " lit" : ""), "aria-label": isActive ? "Api streak menyala" : "Api belum menyala", html: svgIcon("streak", 24) }),
        el("small", { class: "muted", text: isActive ? "Menyala" : "Belum" })
      )
    );
  });
}

function renderDynamicLevelTab() {
  renderQuestLine($("tab-quest-line"), state.player);
}

function renderRecommendationTab() {
  const p = state.player;
  if (!p) return;

  const isMandiri = (p.rata_rata_skor >= 75) || (p.level >= 3);
  const pill = $("reco-status-pill");
  if (pill) pill.textContent = !p.jumlah_kuis ? "Belum mulai" : isMandiri ? "Mandiri" : "Perlu Bimbingan";

  const title = $("reco-title");
  const desc = $("reco-description");
  if (!p.jumlah_kuis) {
    if (title) title.textContent = "Mulai dari Level 1";
    if (desc) desc.textContent = "Kerjakan kuis pertamamu agar sistem dapat memberi rekomendasi sesuai hasil belajarmu.";
  } else if (isMandiri) {
    if (title) title.textContent = `Lanjutkan ke Modul Pengayaan Level ${p.level}`;
    if (desc) {
      desc.textContent = `Performa belajarmu sangat baik dengan rata-rata skor ${p.rata_rata_skor}%. Pertahankan keterlibatan belajar dan selesaikan tantangan tingkat lanjut pada level ${p.level}.`;
    }
  } else {
    if (title) title.textContent = `Fokus Penguatan Materi Dasar (Level ${Math.max(1, p.level - 1)})`;
    if (desc) {
      desc.textContent = `Sistem mendeteksi kamu perlu penguatan konsep dasar sebelum melangkah ke level berikutnya. Pelajari kembali penjelasan materi dan manfaatkan fitur hint saat latihan.`;
    }
  }
}

// ------------------------------------------------------------------ Leaderboard
async function loadLeaderboard() {
  if (!state.player) return;
  const playerId = state.player.id;
  try {
    const d = await api(`/api/leaderboard?limit=15&player_id=${encodeURIComponent(playerId)}`);
    if (!state.player || state.player.id !== playerId) return;
    const body = $("lb-body");
    body.replaceChildren();

    const podium = $("lb-podium");
    podium.replaceChildren();
    [2, 1, 3].forEach((rank) => {
      const r = d.top.find((entry) => entry.rank === rank);
      if (!r) return;
      const me = r.id === playerId;
      podium.append(el("div", { class: `podium-card podium-rank-${rank}${me ? " me" : ""}` },
        el("div", { class: "podium-avatar", text: r.name.trim().charAt(0).toUpperCase() }),
        el("div", { class: "podium-rank", text: `#${rank}` }),
        el("strong", { text: r.name + (me ? " · Kamu" : "") }),
        el("span", { text: `${r.total_xp} XP` }),
        el("small", { text: `Level ${r.level} · Skor ${r.avg_score}%` })
      ));
    });

    const row = (r, me) =>
      el("tr", { class: me ? "me" : "" },
        el("td", { "data-label": "Peringkat", text: `#${r.rank}` }),
        el("td", { "data-label": "Pemain" }, el("span", { class: "lb-avatar", text: r.name.trim().charAt(0).toUpperCase() }), el("strong", { text: r.name + (me ? " · Kamu" : "") })),
        el("td", { "data-label": "XP", text: `${r.total_xp} XP` }),
        el("td", { "data-label": "Level", text: `Level ${r.level}` }),
        el("td", { "data-label": "Skor rata-rata", text: `${r.avg_score}%` })
      );

    d.top.filter((r) => r.rank > 3).forEach((r) => body.append(row(r, r.id === playerId)));

    if (d.posisi_kamu && d.posisi_kamu.rank > d.top.length) {
      body.append(el("tr", {}, el("td", { colspan: "5", class: "muted", text: "…" })));
      body.append(row(d.posisi_kamu, true));
    }

    const info = $("lb-info");
    if (info) {
      info.textContent = `Total ${d.total_pemain} mahasiswa terdaftar · Peringkat diurutkan menurut Total XP, lalu rata-rata skor.`;
    }
  } catch (e) {
    toast(e.message, "error");
  }
}

// ------------------------------------------------------------------ Evaluasi ML & Dataset Riiid Tabs
function renderEvaluasiMLTab() {
  if (!state.meta || !state.meta.evaluasi_ml) return;
  const body = $("ml-eval-body");
  if (!body) return;
  body.replaceChildren();

  state.meta.evaluasi_ml.forEach((m) => {
    body.append(
      el("tr", {},
        el("td", {},
          el("strong", { text: m.model }),
          el("div", { class: "muted small", text: m.desc })
        ),
        el("td", { text: String(m.accuracy) }),
        el("td", { text: String(m.precision) }),
        el("td", { text: String(m.recall) }),
        el("td", { text: String(m.f1) }),
        el("td", { text: String(m.cv_acc) })
      )
    );
  });
}

function renderDatasetRiiidTab() {
  if (!state.meta || !state.meta.dataset_info) return;
  const list = $("dataset-features-list");
  if (!list) return;
  list.replaceChildren();

  state.meta.dataset_info.features.forEach((f) => {
    list.append(
      el("div", { class: "dfeature-item" },
        el("span", { class: "dfeature-code", text: f.name }),
        el("span", { class: "dfeature-desc", text: f.desc })
      )
    );
  });
}

// ------------------------------------------------------------------ Initialization
async function init() {
  document.querySelectorAll("[data-icon]").forEach((node) => { node.innerHTML = svgIcon(node.dataset.icon); });
  document.querySelectorAll(".sidebar-nav .nav-item").forEach((btn) => { btn.title = btn.querySelector(".nav-text").textContent; });
  try {
    if (localStorage.getItem("its_sidebar_collapsed") === "1") {
      document.querySelector(".layout-wrapper").classList.add("sidebar-collapsed");
      $("btn-collapse-sidebar").setAttribute("aria-label", "Besarkan menu");
      $("btn-collapse-sidebar").title = "Besarkan menu";
    }
  } catch (e) { /* no-op */ }
  // Navigation sidebar item clicks
  document.querySelectorAll(".sidebar-nav .nav-item").forEach((btn) => {
    btn.addEventListener("click", () => showTab(btn.dataset.tab));
  });

  // Mobile sidebar toggle
  $("btn-toggle-sidebar").addEventListener("click", openSidebar);
  $("btn-collapse-sidebar").addEventListener("click", toggleSidebarWidth);
  $("btn-close-sidebar").addEventListener("click", closeSidebar);
  $("sidebar-overlay").addEventListener("click", closeSidebar);

  // Authentication buttons
  $("btn-login").addEventListener("click", login);
  document.querySelectorAll(".demo-player").forEach((btn) => {
    btn.addEventListener("click", () => {
      $("input-name").value = btn.dataset.playerName;
      login();
    });
  });
  $("input-name").addEventListener("keydown", (e) => {
    if (e.key === "Enter") login();
  });
  $("btn-side-logout").addEventListener("click", logout);

  // Hero Quick Actions
  $("btn-hero-quiz").addEventListener("click", () => {
    showTab("quiz");
  });
  $("btn-hero-reco").addEventListener("click", () => {
    showTab("recommendation");
  });

  // Quiz control buttons
  $("btn-hint").addEventListener("click", useHint);
  $("btn-explain").addEventListener("click", showExplanation);
  $("btn-quiz-prev").addEventListener("click", prevQuestion);
  $("btn-quiz-next").addEventListener("click", nextQuestion);
  $("btn-quiz-submit").addEventListener("click", finishAndSubmitQuiz);

  // Leaderboard refresh
  $("btn-refresh-lb").addEventListener("click", loadLeaderboard);

  // Generic data-goto buttons
  document.querySelectorAll("[data-goto]").forEach((btn) => {
    btn.addEventListener("click", () => showTab(btn.dataset.goto));
  });

  // Fetch meta info from server
  try {
    state.meta = await api("/api/meta");
  } catch (e) {
    toast(e.message, "error");
    return showLogin();
  }

  // Continue the currently selected player, if there is one.
  const savedId = store.get();
  if (savedId) {
    try {
      const p = await api(`/api/players/${encodeURIComponent(savedId)}`);
      applyPlayer(p);
      showTab("dashboard");
      return;
    } catch (e) {
      store.clear();
    }
  }

  showLogin();
}

init();

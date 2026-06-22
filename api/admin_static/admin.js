// Free Claude Code — Dashboard JS
(function() {
  "use strict";

  var $ = function(sel) { return document.querySelector(sel); };
  var nav = $("#mainNav");
  var views = $("#viewsContainer");
  var pageTitle = $("#pageTitle");
  var menuToggle = $("#menuToggle");
  var sidebar = document.querySelector(".sidebar");
  var toastContainer = $("#toastContainer");

  var currentView = "overview";
  var statusTimer = null;
  var refreshTimer = null;

  function api(path, opts) {
    try {
      return fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, opts))
        .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .catch(function(e) { toast("API error: " + e.message, "err"); return null; });
    } catch(e) { return Promise.resolve(null); }
  }

  function fmt(n) {
    n = n || 0;
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
    return String(n);
  }
  function fmtDate(s) { return s ? s.slice(0, 10) : "—"; }
  function fmtDateTime(s) { return s ? s.replace("T", " ").slice(0, 19) : "—"; }
  function timeAgo(s) {
    if (!s) return "—";
    var d = (Date.now() - new Date(s).getTime()) / 1000;
    if (d < 60) return Math.floor(d) + "s ago";
    if (d < 3600) return Math.floor(d / 60) + "m ago";
    if (d < 86400) return Math.floor(d / 3600) + "h ago";
    return Math.floor(d / 86400) + "d ago";
  }

  function toast(msg, type) {
    var el = document.createElement("div");
    el.className = "toast toast-" + (type || "info");
    el.textContent = msg;
    toastContainer.appendChild(el);
    setTimeout(function() { el.classList.add("toast-out"); }, 3500);
    setTimeout(function() { el.remove(); }, 4000);
  }

  var NAV = [
    { id: "overview", label: "Overview", icon: "grid" },
    { id: "tokens", label: "Token Usage", icon: "chart" },
    { id: "sessions", label: "Sessions", icon: "users" },
    { id: "providers", label: "Providers", icon: "server" },
    { id: "models", label: "Models", icon: "cpu" },
    { id: "messaging", label: "Messaging", icon: "message" },
    { id: "system", label: "System", icon: "settings" },
  ];

  var ICONS = {
    grid: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 16l4-6 4 3 5-7"/>',
    users: '<path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>',
    server: '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
    cpu: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
    message: '<path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>',
  };

  function iconSvg(name) { return ICONS[name] || ICONS.grid; }
  function navLabel(id) { var n = NAV.find(function(x){return x.id===id;}); return n?n.label:id; }
  function esc(s) { var d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

  function renderNav() {
    nav.innerHTML = NAV.map(function(n) {
      var cls = n.id === currentView ? "nav-item nav-item-active" : "nav-item";
      return '<button class="' + cls + '" data-view="' + n.id + '" title="' + n.label + '">' +
        '<svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + iconSvg(n.icon) + '</svg>' +
        '<span class="nav-label">' + n.label + '</span></button>';
    }).join("");
    nav.querySelectorAll(".nav-item").forEach(function(btn) {
      btn.addEventListener("click", function() {
        setView(btn.dataset.view);
        if (window.innerWidth <= 768) sidebar.classList.remove("sidebar-open");
      });
    });
  }

  var VIEW_FNS = {
    overview: renderOverview, tokens: renderTokens, sessions: renderSessions,
    providers: renderProviders, models: renderModels, messaging: renderMessaging, system: renderSystem,
  };

  function setView(id) {
    currentView = id;
    pageTitle.textContent = navLabel(id);
    renderNav();
    var fn = VIEW_FNS[id];
    if (fn) fn(); else views.innerHTML = "<p>View not found</p>";
  }

  function statCard(label, value, sub) {
    return '<div class="stat-card"><div class="stat-label">' + label + '</div><div class="stat-value">' + value + '</div>' + (sub ? '<div class="stat-sub">' + sub + '</div>' : "") + '</div>';
  }
  function section(title) { return '<div class="section"><h2 class="section-title">' + title + '</h2></div>'; }

  function renderDailyBars(daily) {
    if (!daily || !daily.length) return '<div class="empty-state">No usage data yet</div>';
    var last7 = daily.slice(-7);
    var max = 1;
    last7.forEach(function(d){ var t=(d.input_tokens||0)+(d.output_tokens||0); if(t>max)max=t; });
    return '<div class="bar-chart">' + last7.map(function(d) {
      var total = (d.input_tokens||0)+(d.output_tokens||0);
      var pct = Math.max(2, (total/max)*100);
      return '<div class="bar-row"><span class="bar-label">'+fmtDate(d.date)+'</span><div class="bar-track"><div class="bar-fill" style="width:'+pct+'%"></div></div><span class="bar-val">'+fmt(total)+'</span></div>';
    }).join("") + '</div>';
  }

  function renderOverview() {
    views.innerHTML = '<div class="loading">Loading…</div>';
    Promise.all([api("/admin/api/status"), api("/admin/api/tokens/summary"), api("/admin/api/config")])
      .then(function(results) {
        var status = results[0], summary = results[1], config = results[2];
        if (!status && !summary) { views.innerHTML='<div class="empty-state">Failed to load</div>'; return; }
        var tok = summary || {};
        var today = tok.today || {};
        var total = tok.total || {};
        var dot = $("#serverStatusDot"), txt = $("#serverStatusText");
        if (status && status.status === "running") { dot.className="status-dot dot-green"; txt.textContent="Connected"; }
        else { dot.className="status-dot dot-red"; txt.textContent="Disconnected"; }
        $("#uptimeBadge").textContent = status ? "Running" : "—";
        var modelList = "—";
        if (status && status.cached_models) {
          modelList = Object.entries(status.cached_models).map(function(e){ return '<span class="pill">'+e[0]+': '+e[1].length+' model(s)</span>'; }).join(" ");
        }
        var provStatus = "—";
        if (config && config.fields) {
          provStatus = config.fields.filter(function(f){return f.key==="PROVIDER_TYPE"||f.key==="MODEL";}).map(function(f){return '<div class="kv"><span class="kv-key">'+f.key+'</span><span class="kv-val">'+(f.value||"—")+'</span></div>';}).join("");
        }
        views.innerHTML =
          '<div class="grid-4">' +
          statCard("Total Tokens", fmt((total.input_tokens||0)+(total.output_tokens||0)), fmt(total.input_tokens||0)+" in / "+fmt(total.output_tokens||0)+" out") +
          statCard("Today Tokens", fmt((today.input_tokens||0)+(today.output_tokens||0)), (today.request_count||0)+" requests") +
          statCard("Active Sessions", tok.active_sessions||0, (tok.daily_usage||[]).length+" days tracked") +
          statCard("Total Requests", fmt(total.request_count||0), "All time") +
          '</div>' +
          section("Daily Usage (Last 7 Days)") + renderDailyBars(tok.daily_usage) +
          section("Configuration") +
          '<div class="provider-grid"><div class="card"><div class="card-body">'+provStatus+'</div></div><div class="card"><div class="card-body">'+modelList+'</div></div></div>';
      });
  }

  function renderTokens() {
    views.innerHTML = '<div class="loading">Loading token data…</div>';
    Promise.all([api("/admin/api/tokens/summary"), api("/admin/api/tokens/daily")])
      .then(function(results) {
        var summary = results[0], daily = results[1];
        if (!summary && !daily) { views.innerHTML='<div class="empty-state">Failed to load</div>'; return; }
        var tot = (summary&&summary.total)||{}, today=(summary&&summary.today)||{};
        var dailyData = (daily&&daily.daily)||(summary&&summary.daily_usage)||[];
        views.innerHTML =
          '<div class="grid-4">' +
          statCard("Today Input", fmt(today.input_tokens||0), (today.request_count||0)+" reqs") +
          statCard("Today Output", fmt(today.output_tokens||0), "Generated") +
          statCard("All-Time Input", fmt(tot.input_tokens||0), "Total") +
          statCard("All-Time Output", fmt(tot.output_tokens||0), "Total") +
          '</div>' +
          section("Daily Breakdown") + renderDailyBars(dailyData) +
          section("Per-Day Detail") +
          '<div class="card"><table class="tbl"><thead><tr><th>Date</th><th>Input</th><th>Output</th><th>Total</th><th>Requests</th></tr></thead><tbody>' +
          dailyData.slice().reverse().map(function(d){ return '<tr><td>'+fmtDate(d.date)+'</td><td>'+fmt(d.input_tokens||0)+'</td><td>'+fmt(d.output_tokens||0)+'</td><td><strong>'+fmt((d.input_tokens||0)+(d.output_tokens||0))+'</strong></td><td>'+(d.request_count||0)+'</td></tr>'; }).join("") +
          '</tbody></table></div>';
      });
  }

  function renderSessions() {
    views.innerHTML = '<div class="loading">Loading sessions…</div>';
    api("/admin/api/tokens/sessions").then(function(data) {
      var sessions = (data&&data.sessions)||[];
      if (!sessions.length) { views.innerHTML="<p>No sessions tracked yet</p>"; return; }
      var totalTokens=0, totalReqs=0;
      sessions.forEach(function(s){ totalTokens+=(s.input_tokens||0)+(s.output_tokens||0); totalReqs+=(s.request_count||0); });
      var sorted = sessions.slice().sort(function(a,b){ return (b.last_activity||"").localeCompare(a.last_activity||""); });
      views.innerHTML =
        '<div class="grid-4">' +
        statCard("Total Sessions", sessions.length, "All time") +
        statCard("Active", sessions.filter(function(s){return s.is_active;}).length, "Currently") +
        statCard("Total Tokens", fmt(totalTokens), "All sessions") +
        statCard("Total Requests", fmt(totalReqs), "") +
        '</div>' +
        section("Session List") +
        '<div class="session-list">' + sorted.map(function(s) {
          return '<details class="session-card"><summary>' +
            '<span class="session-status '+(s.is_active?"session-active":"session-inactive")+'"></span>' +
            '<code>'+s.session_id.slice(0,16)+'…</code>' +
            '<span class="pill">'+(s.model||"—")+'</span>' +
            '<span class="session-tokens">'+fmt((s.input_tokens||0)+(s.output_tokens||0))+' tok</span>' +
            '<span class="session-time">'+timeAgo(s.last_activity)+'</span>' +
            '</summary><div class="session-detail"><div class="kv-grid">' +
            '<div class="kv"><span class="kv-key">Session ID</span><span class="kv-val"><code>'+s.session_id+'</code></span></div>' +
            '<div class="kv"><span class="kv-key">Started</span><span class="kv-val">'+fmtDateTime(s.started_at)+'</span></div>' +
            '<div class="kv"><span class="kv-key">Last Active</span><span class="kv-val">'+fmtDateTime(s.last_activity)+'</span></div>' +
            '<div class="kv"><span class="kv-key">Input</span><span class="kv-val">'+fmt(s.input_tokens||0)+'</span></div>' +
            '<div class="kv"><span class="kv-key">Output</span><span class="kv-val">'+fmt(s.output_tokens||0)+'</span></div>' +
            '<div class="kv"><span class="kv-key">Requests</span><span class="kv-val">'+(s.request_count||0)+'</span></div>' +
            '</div></div></details>';
        }).join("") + '</div>';
    });
  }

  function renderProviders() {
    views.innerHTML = '<div class="loading">Loading providers…</div>';
    Promise.all([api("/admin/api/config"), api("/admin/api/providers/local-status")])
      .then(function(results) {
        var config = results[0], local = results[1];
        if (!config) { views.innerHTML='<div class="empty-state">Failed to load</div>'; return; }
        var fields = (config.fields||[]).filter(function(f){ return f.key.match(/PROVIDER|BASE_URL|API_KEY|MODEL|HOST|PORT/i); });
        var localHtml = "—";
        if (local && local.providers) {
          localHtml = local.providers.map(function(p){ return '<div class="kv"><span class="kv-key">'+p.provider_id+'</span><span class="pill '+(p.status==="reachable"?"pill-green":"pill-red")+'">'+p.label+'</span></div>'; }).join("");
        }
        views.innerHTML =
          '<div class="card" style="margin-bottom:16px"><h3 class="section-title">Local Providers</h3><div class="kv-grid">'+localHtml+'</div></div>' +
          section("Provider Config") +
          '<div class="card"><table class="tbl"><thead><tr><th>Key</th><th>Value</th></tr></thead><tbody>' +
          fields.map(function(f){ return '<tr><td>'+f.key+'</td><td><code>'+(f.secret?"••••••":(f.value||"—"))+'</code></td></tr>'; }).join("") +
          '</tbody></table></div>';
      });
  }

  function renderModels() {
    views.innerHTML = '<div class="loading">Loading models…</div>';
    api("/admin/api/status").then(function(status) {
      var cached = (status&&status.cached_models)||{};
      var cards = Object.entries(cached).map(function(e){
        return '<div class="card"><h3 class="card-title">'+e[0]+'</h3><div class="model-list">'+(e[1]||[]).map(function(m){return '<span class="pill">'+m+'</span>';}).join(" ")+'</div></div>';
      }).join("");
      views.innerHTML = '<div class="provider-grid">'+(cards||"No models cached")+'</div>';
    });
  }

  function renderMessaging() {
    views.innerHTML = section("Messaging Channels") + '<div class="card"><div class="card-body">Discord, Telegram, Slack status here</div></div>';
  }

  function renderSystem() {
    views.innerHTML = '<div class="loading">Loading system…</div>';
    Promise.all([api("/admin/api/status"), api("/admin/api/system/metrics")])
      .then(function(results) {
        var status = results[0], metrics = results[1];
        views.innerHTML =
          '<div class="card" style="margin-bottom:16px"><h3 class="section-title">Server</h3><div class="kv-grid">' +
          '<div class="kv"><span class="kv-key">Status</span><span class="pill '+(status&&status.status==="running"?"pill-green":"pill-red")+'">'+((status&&status.status)||"—")+'</span></div>' +
          '<div class="kv"><span class="kv-key">Host</span><span>'+((status&&status.host)||"—")+'</span></div>' +
          '<div class="kv"><span class="kv-key">Port</span><span>'+((status&&status.port)||"—")+'</span></div>' +
          '<div class="kv"><span class="kv-key">Model</span><span>'+((status&&status.model)||"—")+'</span></div>' +
          '<div class="kv"><span class="kv-key">Provider</span><span>'+((status&&status.provider)||"—")+'</span></div>' +
          '</div></div>' +
          section("System Metrics") +
          '<div class="card"><div class="kv-grid">' +
          '<div class="kv"><span class="kv-key">Uptime</span><span>'+((metrics&&metrics.uptime)||"—")+'</span></div>' +
          '<div class="kv"><span class="kv-key">CPU</span><span>'+((metrics&&metrics.cpu_percent)||"—")+'%</span></div>' +
          '<div class="kv"><span class="kv-key">Memory</span><span>'+((metrics&&metrics.memory_mb)||"—")+' MB</span></div>' +
          '</div></div>';
      });
  }

  function pollStatus() {
    api("/admin/api/status").then(function(s) {
      var dot = $("#serverStatusDot"), txt = $("#serverStatusText");
      if (s && s.status === "running") { dot.className="status-dot dot-green"; txt.textContent="Connected"; }
      else { dot.className="status-dot dot-red"; txt.textContent="Disconnected"; }
    });
  }

  function init() {
    renderNav();
    setView("overview");
    menuToggle.addEventListener("click", function(){ sidebar.classList.toggle("sidebar-open"); });
    document.addEventListener("click", function(e){
      if (window.innerWidth<=768 && !sidebar.contains(e.target) && !menuToggle.contains(e.target)) sidebar.classList.remove("sidebar-open");
    });
    pollStatus();
    statusTimer = setInterval(pollStatus, 15000);
    refreshTimer = setInterval(function(){ setView(currentView); }, 30000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
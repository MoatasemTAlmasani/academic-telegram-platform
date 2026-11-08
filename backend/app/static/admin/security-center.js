(function () {
  "use strict";
  var statusFilter = "active";
  var searchValue = "";
  var searchTimer = null;
  var bound = false;
  var labels = {
    en: {
      refresh: "Refresh", sessions: "User sessions", sessionsSub: "Active and historical sessions across accounts",
      search: "Search user, email or IP…", user: "USER", ip: "IP ADDRESS", device: "DEVICE",
      lastSeen: "LAST SEEN", expires: "EXPIRES", status: "STATUS", action: "ACTION",
      failed: "Recent failed sign-ins", failedSub: "Latest unsuccessful authentication attempts",
      activeSessions: "Active sessions", failed24h: "Failed sign-ins · 24h", locked: "Locked accounts", suspended: "Suspended accounts",
      active: "Active", revoked: "Revoked", expired: "Expired", all: "All sessions", revoke: "Revoke",
      self: "Your account", noSessions: "No sessions match this filter.", noFailed: "No failed sign-ins recorded.",
      loading: "Loading security data…", error: "Security data could not be loaded.", confirm: "Revoke this session? The user will need to sign in again.",
      success: "Session revoked and recorded in the audit trail.", failedLoad: "Could not load sessions.", identity: "IDENTITY", attempted: "ATTEMPTED",
      unavailable: "—", retry: "Try again"
    },
    ar: {
      refresh: "تحديث", sessions: "جلسات المستخدمين", sessionsSub: "الجلسات النشطة والسابقة لجميع الحسابات",
      search: "ابحث باسم المستخدم أو البريد أو IP…", user: "المستخدم", ip: "عنوان IP", device: "الجهاز والمتصفح",
      lastSeen: "آخر نشاط", expires: "تنتهي في", status: "الحالة", action: "الإجراء",
      failed: "محاولات الدخول الفاشلة الأخيرة", failedSub: "أحدث محاولات المصادقة غير الناجحة",
      activeSessions: "الجلسات النشطة", failed24h: "محاولات فاشلة · 24 ساعة", locked: "الحسابات المقفلة", suspended: "الحسابات الموقوفة",
      active: "نشطة", revoked: "ملغاة", expired: "منتهية", all: "كل الجلسات", revoke: "إلغاء الجلسة",
      self: "حسابك", noSessions: "لا توجد جلسات مطابقة لهذا الفلتر.", noFailed: "لا توجد محاولات دخول فاشلة مسجلة.",
      loading: "جارٍ تحميل بيانات الأمان…", error: "تعذر تحميل بيانات الأمان.", confirm: "هل تريد إلغاء هذه الجلسة؟ سيحتاج المستخدم إلى تسجيل الدخول مجددًا.",
      success: "تم إلغاء الجلسة وتسجيل العملية في سجل التدقيق.", failedLoad: "تعذر تحميل الجلسات.", identity: "الحساب", attempted: "وقت المحاولة",
      unavailable: "—", retry: "إعادة المحاولة"
    }
  };
  function lang() { return localStorage.getItem("ehteraf_admin_lang") === "en" ? "en" : "ar"; }
  function t(key) { return labels[lang()][key] || labels.en[key] || key; }
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }
  function number(value) { return new Intl.NumberFormat(lang() === "ar" ? "ar" : "en-US").format(Number(value || 0)); }
  function date(value) {
    if (!value) return t("unavailable");
    var parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? t("unavailable") : new Intl.DateTimeFormat(lang() === "ar" ? "ar" : "en-GB", { dateStyle: "medium", timeStyle: "short" }).format(parsed);
  }
  function token() { return localStorage.getItem("admin_access_token") || ""; }
  async function request(path, options) {
    var response = await fetch("/api/v1/admin/dashboard" + path, Object.assign({
      credentials: "same-origin",
      headers: { Accept: "application/json", Authorization: "Bearer " + token() }
    }, options || {}));
    if (!response.ok) {
      var detail = "HTTP " + response.status;
      try { var body = await response.json(); detail = body.detail || detail; } catch (_) { /* response may not be JSON */ }
      throw new Error(detail);
    }
    return response.json();
  }
  function applyLabels() {
    document.querySelectorAll("[data-security-label]").forEach(function (element) {
      element.textContent = t(element.dataset.securityLabel);
    });
    document.querySelectorAll("[data-security-placeholder]").forEach(function (element) {
      element.placeholder = t(element.dataset.securityPlaceholder);
    });
    var select = document.getElementById("securitySessionStatus");
    if (select) Array.prototype.forEach.call(select.options, function (option) { option.textContent = t(option.value); });
  }
  function setFeedback(message, isError) {
    var target = document.getElementById("securityFeedback");
    if (!target) return;
    target.textContent = message || "";
    target.classList.toggle("is-error", !!isError);
    target.classList.toggle("is-success", !isError && !!message);
  }
  function renderMetrics(metrics) {
    var target = document.getElementById("securityMetrics");
    var items = [
      ["activeSessions", metrics.active_sessions, "◉", "blue"],
      ["failed24h", metrics.failed_logins_24h, "⌁", "amber"],
      ["locked", metrics.locked_accounts, "⊘", "rose"],
      ["suspended", metrics.suspended_accounts, "▣", "slate"]
    ];
    target.innerHTML = items.map(function (item) {
      return '<article class="security-metric"><div class="security-metric-top"><span>' + esc(t(item[0])) + '</span><span class="security-metric-icon ' + item[3] + '">' + item[2] + '</span></div><strong>' + number(item[1]) + '</strong><small>' + esc(lang() === "ar" ? "بيانات من سجلات النظام" : "From persisted platform records") + '</small></article>';
    }).join("");
  }
  function renderSessions(payload) {
    var body = document.getElementById("securitySessionsBody");
    var rows = payload.items || [];
    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="7" class="empty-cell">' + esc(t("noSessions")) + '</td></tr>';
      return;
    }
    body.innerHTML = rows.map(function (item) {
      var state = item.revoked_at ? "revoked" : item.is_active ? "active" : "expired";
      var device = item.user_agent || t("unavailable");
      if (device.length > 68) device = device.slice(0, 65) + "…";
      var action = item.can_revoke
        ? '<button type="button" class="security-revoke" data-security-revoke="' + esc(item.id) + '">' + esc(t("revoke")) + '</button>'
        : '<span class="security-no-action">' + esc(item.is_own_account ? t("self") : "—") + '</span>';
      return '<tr><td><strong>' + esc(item.user_name) + '</strong><small>' + esc(item.username || item.email || "") + '</small></td><td dir="ltr">' + esc(item.ip_address || "—") + '</td><td class="security-device" title="' + esc(item.user_agent || "") + '">' + esc(device) + '</td><td>' + date(item.last_seen_at || item.created_at) + '</td><td>' + date(item.expires_at) + '</td><td><span class="security-status ' + state + '">' + esc(t(state)) + '</span></td><td>' + action + '</td></tr>';
    }).join("");
  }
  function renderFailed(items) {
    var target = document.getElementById("securityFailedLogins");
    if (!items || !items.length) {
      target.innerHTML = '<div class="security-empty">' + esc(t("noFailed")) + '</div>';
      return;
    }
    target.innerHTML = items.map(function (item) {
      return '<article class="security-failed-item"><span class="security-failed-mark">!</span><div><strong>' + esc(item.identity) + '</strong><small>' + esc(item.ip_address || "—") + '</small></div><time>' + date(item.attempted_at) + '</time></article>';
    }).join("");
  }
  async function loadSecurityCenter() {
    var body = document.getElementById("securitySessionsBody");
    if (!body) return;
    applyLabels();
    setFeedback("");
    body.innerHTML = '<tr><td colspan="7" class="empty-cell">' + esc(t("loading")) + '</td></tr>';
    try {
      var query = "?status=" + encodeURIComponent(statusFilter) + "&limit=100" + (searchValue ? "&search=" + encodeURIComponent(searchValue) : "");
      var results = await Promise.all([request("/security/overview"), request("/security/sessions" + query)]);
      renderMetrics(results[0].metrics || {});
      renderFailed(results[0].recent_failed_logins || []);
      renderSessions(results[1]);
    } catch (error) {
      body.innerHTML = '<tr><td colspan="7" class="empty-cell">' + esc(t("error")) + '</td></tr>';
      setFeedback(error.message || t("error"), true);
    }
  }
  function bind() {
    if (bound) return;
    bound = true;
    var filter = document.getElementById("securitySessionStatus");
    var search = document.getElementById("securitySessionSearch");
    var refresh = document.getElementById("securityRefresh");
    if (filter) filter.addEventListener("change", function () { statusFilter = filter.value; loadSecurityCenter(); });
    if (search) search.addEventListener("input", function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(function () { searchValue = search.value.trim(); loadSecurityCenter(); }, 300);
    });
    if (refresh) refresh.addEventListener("click", loadSecurityCenter);
    document.addEventListener("click", async function (event) {
      var button = event.target.closest && event.target.closest("[data-security-revoke]");
      if (!button || button.disabled) return;
      if (!window.confirm(t("confirm"))) return;
      button.disabled = true;
      try {
        await request("/security/sessions/" + encodeURIComponent(button.dataset.securityRevoke) + "/revoke", { method: "POST" });
        setFeedback(t("success"), false);
        await loadSecurityCenter();
      } catch (error) {
        button.disabled = false;
        setFeedback(error.message || t("failedLoad"), true);
      }
    });
  }
  window.loadSecurityCenter = function () { bind(); return loadSecurityCenter(); };
})();

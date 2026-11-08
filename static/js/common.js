/**
 * Obsluga — общий код страниц tickets.html и admin.html.
 *
 * Права проверяются на сервере; проверка роли здесь нужна только для того,
 * чтобы отправить человека на «его» страницу и не показывать чужие кнопки.
 *
 * Роли (perm из GET /api/auth/me): 1 — Сотрудник, 2 — Инженер, 3 — Администратор.
 */
(function (global) {
  "use strict";

  var STATUS_LABEL = { new: "Новая", progress: "В работе", closed: "Закрыта" };
  var STATUS_BADGE_CLASS = { new: "badge-new", progress: "badge-progress", closed: "badge-closed" };
  var ROLE_BADGE_CLASS = { 1: "badge-role-employee", 2: "badge-role-engineer", 3: "badge-role-admin" };

  function readToken() {
    try {
      return global.sessionStorage.getItem("token") || global.localStorage.getItem("token") || "";
    } catch (e) {
      return "";
    }
  }

  function clearSession() {
    ["token", "profile"].forEach(function (key) {
      try {
        global.localStorage.removeItem(key);
        global.sessionStorage.removeItem(key);
      } catch (e) { /* хранилище недоступно — нечего чистить */ }
    });
  }

  function homeFor(perm) {
    return perm === 3 ? "admin.html" : "tickets.html";
  }

  function goToLogin() {
    clearSession();
    global.location.assign("login.html");
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fmtDate(iso) {
    if (!iso) return "—";
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "—";
    var months = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
    return d.getDate() + " " + months[d.getMonth()] + ", " +
      String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  function extractDetail(data) {
    if (!data || !data.detail) return null;
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map(function (item) { return item.msg; }).join("; ");
    }
    return String(data.detail);
  }

  /** fetch с Bearer-токеном. 401 → на страницу входа; остальные ошибки → Error(detail) со status. */
  function api(url, method, body) {
    var headers = {};
    var token = readToken();
    if (token) headers.Authorization = "Bearer " + token;
    var options = { method: method || "GET", headers: headers };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    return fetch(url, options).then(function (res) {
      if (res.status === 401) {
        goToLogin();
        var expired = new Error("Сессия истекла. Войдите снова");
        expired.status = 401;
        throw expired;
      }
      return res.json().catch(function () { return null; }).then(function (data) {
        if (!res.ok) {
          var err = new Error(extractDetail(data) || "Ошибка сервера (" + res.status + ")");
          err.status = res.status;
          throw err;
        }
        return data;
      });
    });
  }

  /**
   * Проверяет, что вошёл пользователь с нужной ролью. Иначе уводит на login.html
   * или на страницу его роли; промис при этом не завершается, и страница дальше не грузится.
   */
  function requireRole(allowedPerms) {
    var never = new Promise(function () {});
    if (!readToken()) {
      global.location.replace("login.html");
      return never;
    }
    return api("/api/auth/me").then(function (profile) {
      if (allowedPerms.indexOf(profile.perm) === -1) {
        global.location.replace(homeFor(profile.perm));
        return never;
      }
      return profile;
    });
  }

  function renderUser(profile) {
    document.querySelectorAll("[data-user-name]").forEach(function (node) {
      node.textContent = profile.full_name;
    });
    document.querySelectorAll("[data-user-dept]").forEach(function (node) {
      node.textContent = profile.department;
    });
    document.querySelectorAll("[data-user-role]").forEach(function (node) {
      node.textContent = profile.role;
      node.className = "badge " + (ROLE_BADGE_CLASS[profile.perm] || "");
    });
  }

  function showToast(message, ms) {
    var toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    global.clearTimeout(showToast._t);
    showToast._t = global.setTimeout(function () {
      toast.classList.remove("is-visible");
    }, ms || 3200);
  }

  /** Ошибки показываем дольше обычных уведомлений: их нужно успеть прочитать. */
  function showError(prefix, err) {
    if (err && err.status === 401) return;
    var text = err && err.message ? err.message : "Сервер недоступен. Попробуйте позже";
    showToast(prefix + ": " + text, 6000);
  }

  function statusBadge(status) {
    return '<span class="badge ' + (STATUS_BADGE_CLASS[status] || "") + '">' +
      escapeHtml(STATUS_LABEL[status] || status) + "</span>";
  }

  function roleBadge(perm, name) {
    return '<span class="badge ' + (ROLE_BADGE_CLASS[perm] || "") + '">' + escapeHtml(name) + "</span>";
  }

  /** Кнопки [data-close-dialog], закрытие по клику на подложку. */
  function initDialogs() {
    document.querySelectorAll("[data-close-dialog]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var dialog = document.getElementById(btn.dataset.closeDialog);
        if (dialog) dialog.close();
      });
    });
    document.querySelectorAll("dialog").forEach(function (dialog) {
      dialog.addEventListener("click", function (e) {
        if (e.target === dialog) dialog.close();
      });
    });
  }

  function initLogout() {
    document.querySelectorAll("[data-logout]").forEach(function (link) {
      link.addEventListener("click", clearSession);
    });
  }

  /** Фильтр-вкладки: рисует кнопки с счётчиками и вызывает onChange(filterValue). */
  function renderTabs(container, tabs, active, counts) {
    container.innerHTML = tabs.map(function (tab) {
      var count = counts && counts[tab.value] != null ? ' <span class="tab-count">' + counts[tab.value] + "</span>" : "";
      return '<button type="button" data-filter="' + escapeHtml(tab.value) + '" aria-pressed="' +
        String(tab.value === active) + '">' + escapeHtml(tab.label) + count + "</button>";
    }).join("");
  }

  global.Obsluga = {
    api: api,
    requireRole: requireRole,
    renderUser: renderUser,
    renderTabs: renderTabs,
    showToast: showToast,
    showError: showError,
    escapeHtml: escapeHtml,
    fmtDate: fmtDate,
    statusBadge: statusBadge,
    roleBadge: roleBadge,
    initDialogs: initDialogs,
    initLogout: initLogout,
    STATUS_LABEL: STATUS_LABEL
  };
})(window);

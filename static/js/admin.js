/**
 * Obsluga — admin panel interactions.
 *
 * Data flows:
 *   GET    /api/tickets       -> TICKETS (table)
 *   GET    /api/equipment     -> <select> in #createTicketForm
 *   GET    /api/auth/me       -> user meta in the sidebar
 *   POST   /api/tickets       -> createTicketForm submit
 *   PATCH  /api/tickets/:id   -> detailForm submit
 *
 * Ticket shape: { id, equipment, description, reporter, engineer, status, updated, diagnosis, workDone }
 * status is one of: "new" | "progress" | "closed"
 */
(function () {
  "use strict";

  var TOKEN = window.localStorage.token || window.sessionStorage.token || "";

  var STATUS_LABEL = { new: "Новая", progress: "В работе", closed: "Закрыта" };
  var STATUS_BADGE_CLASS = { new: "badge-new", progress: "badge-progress", closed: "badge-closed" };

  var TICKETS = [];
  var state = { filter: "all", query: "" };
  var activeTicketId = null;

  var tbody = document.getElementById("ticketTableBody");

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fmtDate(iso) {
    var d = new Date(iso);
    var months = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
    return d.getDate() + " " + months[d.getMonth()] + ", " +
      String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  function apiRequest(url, method, body) {
    var options = { method: method };
    var headers = {};
    if (TOKEN) {
      headers.Authorization = "Bearer " + TOKEN;
    }
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    options.headers = headers;

    return fetch(url, options).then(function (res) {
      if (res.status === 401) {
        window.location.assign("login.html");
        throw new Error("401");
      }
      return res.json().then(function (data) {
        if (!res.ok) {
          var detail = null;
          if (data && data.detail) {
            detail = typeof data.detail === "string"
              ? data.detail
              : Array.isArray(data.detail)
                ? data.detail.map(function (item) { return item.msg; }).join("; ")
                : String(data.detail);
          }
          throw new Error(detail || "Ошибка сервера (" + res.status + ")");
        }
        return data;
      });
    });
  }

  function findTicketById(id) {
    for (var i = 0; i < TICKETS.length; i++) {
      if (TICKETS[i].id === id) return TICKETS[i];
    }
    return null;
  }

  function renderTable() {
    var rows = TICKETS.filter(function (t) {
      var matchesFilter = state.filter === "all" || t.status === state.filter;
      var q = state.query.trim().toLowerCase();
      var matchesQuery = !q ||
        t.equipment.toLowerCase().indexOf(q) !== -1 ||
        String(t.id).indexOf(q) !== -1;
      return matchesFilter && matchesQuery;
    });

    if (!rows.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Заявок по такому запросу не найдено.</td></tr>';
      return;
    }

    tbody.innerHTML = rows.map(function (t) {
      return (
        '<tr>' +
          '<td>№' + t.id + '</td>' +
          '<td class="ticket-equipment">' + escapeHtml(t.equipment) + '</td>' +
          '<td class="ticket-desc" title="' + escapeHtml(t.description) + '">' + escapeHtml(t.description) + '</td>' +
          '<td><span class="badge ' + STATUS_BADGE_CLASS[t.status] + '">' + STATUS_LABEL[t.status] + '</span></td>' +
          '<td>' + escapeHtml(t.engineer || "—") + '</td>' +
          '<td>' + fmtDate(t.updated) + '</td>' +
          '<td><button type="button" class="btn btn-ghost btn-sm" data-open-ticket="' + t.id + '">Открыть</button></td>' +
        '</tr>'
      );
    }).join("");
  }

  function initFilters() {
    var buttons = document.querySelectorAll(".filter-tabs button");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        btn.setAttribute("aria-pressed", "true");
        state.filter = btn.dataset.filter;
        renderTable();
      });
    });
  }

  function initSearch() {
    var input = document.getElementById("ticketSearch");
    input.addEventListener("input", function () {
      state.query = input.value;
      renderTable();
    });
  }

  function showToast(message) {
    var toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(function () {
      toast.classList.remove("is-visible");
    }, 3200);
  }

  function initDialogClosers() {
    document.querySelectorAll("[data-close-dialog]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var dialog = document.getElementById(btn.dataset.closeDialog);
        if (dialog) dialog.close();
      });
    });
  }

  function initCreateDialog() {
    var dialog = document.getElementById("createDialog");
    var form = document.getElementById("createTicketForm");

    document.getElementById("openCreateDialog").addEventListener("click", function () {
      form.reset();
      dialog.showModal();
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;

      apiRequest("/api/tickets", "POST", {
        equipment_id: Number(form.elements.equipment.value),
        description: form.elements.description.value
      }).then(function (ticket) {
        TICKETS.unshift(ticket);
        dialog.close();
        renderTable();
        showToast("Заявка №" + ticket.id + " создана");
      }).catch(function (err) {
        if (err.message !== "401") {
          showToast("Не удалось создать заявку: " + err.message);
        }
      });
    });
  }

  function openDetailDialog(ticketId) {
    var ticket = findTicketById(ticketId);
    if (!ticket) return;
    activeTicketId = ticketId;

    document.getElementById("detailDialogTitle").textContent = "Заявка №" + ticket.id;
    document.getElementById("detailMeta").innerHTML =
      '<span><strong>Оборудование:</strong> ' + escapeHtml(ticket.equipment) + '</span>' +
      '<span><strong>Подал заявку:</strong> ' + escapeHtml(ticket.reporter) + '</span>' +
      '<span><strong>Неисправность:</strong> ' + escapeHtml(ticket.description) + '</span>';

    document.getElementById("detail-status").value = ticket.status;
    document.getElementById("detail-diagnosis").value = ticket.diagnosis || "";
    document.getElementById("detail-work").value = ticket.workDone || "";

    document.getElementById("detailDialog").showModal();
  }

  function initDetailDialog() {
    tbody.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-open-ticket]");
      if (!btn) return;
      openDetailDialog(Number(btn.dataset.openTicket));
    });

    var form = document.getElementById("detailForm");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (activeTicketId == null) return;

      apiRequest("/api/tickets/" + activeTicketId, "PATCH", {
        status: form.elements.status.value,
        diagnosis: form.elements.diagnosis.value,
        workDone: form.elements.workDone.value
      }).then(function (ticket) {
        for (var i = 0; i < TICKETS.length; i++) {
          if (TICKETS[i].id === ticket.id) {
            TICKETS[i] = ticket;
            break;
          }
        }
        document.getElementById("detailDialog").close();
        renderTable();
        showToast("Заявка №" + ticket.id + " обновлена");
      }).catch(function (err) {
        if (err.message !== "401") {
          showToast("Не удалось сохранить заявку: " + err.message);
        }
      });
    });
  }

  function initUserMeta() {
    apiRequest("/api/auth/me", "GET").then(function (profile) {
      var meta = document.querySelector(".admin-user-meta");
      if (!meta) return;
      var strong = document.createElement("strong");
      strong.textContent = profile.full_name;
      var span = document.createElement("span");
      span.textContent = profile.role + " · " + profile.department;
      meta.innerHTML = "";
      meta.appendChild(strong);
      meta.appendChild(span);
    }).catch(function () {
      /* 401 уже редиректит на login.html */
    });
  }

  function initLogout() {
    var link = document.querySelector(".admin-user a");
    if (!link) return;
    link.addEventListener("click", function () {
      window.localStorage.removeItem("token");
      window.sessionStorage.removeItem("token");
      window.localStorage.removeItem("profile");
      window.sessionStorage.removeItem("profile");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initFilters();
    initSearch();
    initDialogClosers();
    initCreateDialog();
    initDetailDialog();
    initUserMeta();
    initLogout();

    apiRequest("/api/equipment", "GET").then(function (items) {
      var select = document.getElementById("create-equipment");
      items.forEach(function (item) {
        var option = document.createElement("option");
        option.value = String(item.id);
        option.textContent = item.name;
        select.appendChild(option);
      });
    }).catch(function () {});

    apiRequest("/api/tickets", "GET").then(function (items) {
      TICKETS = items;
      renderTable();
    }).catch(function () {});
  });
})();

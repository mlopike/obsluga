/**
 * Obsluga — панель администратора (admin.html). Только perm = 3.
 *
 *   GET   /api/tickets              все заявки
 *   GET   /api/users                пользователи (admin)
 *   PATCH /api/users/:id { role }   «Сотрудник» ⇄ «Инженер»
 *   POST  /api/tickets/:id/assign { engineer_id }   назначить / переназначить инженера
 *
 * Администратор не правит диагноз и не закрывает заявки — это делает инженер.
 */
(function () {
  "use strict";

  var O = window.Obsluga;
  var esc = O.escapeHtml;

  var TABS = [
    { value: "all", label: "Все" }, { value: "new", label: "Новые" },
    { value: "progress", label: "В работе" }, { value: "closed", label: "Закрытые" }
  ];

  var tickets = [];
  var users = [];
  var state = { filter: "all", query: "", userQuery: "" };
  var activeId = null;

  var tbody = document.getElementById("ticketTableBody");
  var userBody = document.getElementById("userTableBody");
  var tabsBox = document.getElementById("filterTabs");

  function byId(id) {
    for (var i = 0; i < tickets.length; i++) if (tickets[i].id === id) return tickets[i];
    return null;
  }

  function engineers() {
    return users.filter(function (u) { return u.perm === 2; });
  }

  /* ---------- заявки ---------- */

  function renderTickets() {
    var c = { all: tickets.length, new: 0, progress: 0, closed: 0 };
    tickets.forEach(function (t) { c[t.status] = (c[t.status] || 0) + 1; });
    O.renderTabs(tabsBox, TABS, state.filter, c);

    var q = state.query.trim().toLowerCase();
    var rows = tickets.filter(function (t) {
      return (state.filter === "all" || t.status === state.filter) &&
        (!q || t.equipment.toLowerCase().indexOf(q) !== -1 || String(t.id).indexOf(q) !== -1);
    });
    if (!rows.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Заявок по такому запросу не найдено.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (t) {
      var action = t.status === "closed" ? "Подробнее" : (t.engineer ? "Переназначить" : "Назначить");
      return "<tr>" +
        "<td>№" + t.id + "</td>" +
        '<td class="ticket-equipment">' + esc(t.equipment) + "</td>" +
        '<td class="ticket-desc" title="' + esc(t.description) + '">' + esc(t.description) + "</td>" +
        "<td>" + O.statusBadge(t.status) + "</td>" +
        "<td>" + esc(t.engineer || "—") + "</td>" +
        "<td>" + O.fmtDate(t.updated) + "</td>" +
        '<td><button type="button" class="btn btn-ghost btn-sm" data-open-ticket="' + t.id + '">' + action + "</button></td>" +
        "</tr>";
    }).join("");
  }

  function fact(term, value) {
    return "<div><dt>" + esc(term) + "</dt><dd>" + value + "</dd></div>";
  }

  function openTicket(id) {
    var t = byId(id);
    if (!t) return;
    activeId = id;
    document.getElementById("detailDialogTitle").textContent = "Заявка №" + t.id;

    var html =
      fact("Статус", O.statusBadge(t.status)) +
      fact("Оборудование", esc(t.equipment)) +
      fact("Цех", esc(t.department)) +
      fact("Подал заявку", esc(t.reporter) + " (" + esc(t.reporter_department) + ")") +
      fact("Инженер", esc(t.engineer || "не назначен")) +
      fact("Обновлено", O.fmtDate(t.updated)) +
      '<div class="fact-wide"><dt>Неисправность</dt><dd>' + esc(t.description) + "</dd></div>";
    if (t.diagnosis) html += '<div class="fact-wide"><dt>Диагноз</dt><dd>' + esc(t.diagnosis) + "</dd></div>";
    if (t.workDone) html += '<div class="fact-wide"><dt>Выполненные работы</dt><dd>' + esc(t.workDone) + "</dd></div>";
    document.getElementById("detailMeta").innerHTML = html;

    var canAssign = t.status !== "closed";
    var select = document.getElementById("assign-engineer");
    select.innerHTML = '<option value="" disabled>Выберите инженера</option>' +
      engineers().map(function (e) {
        return '<option value="' + e.id + '">' + esc(e.full_name) + " — " + esc(e.department) + "</option>";
      }).join("");
    select.value = t.engineer_id != null ? String(t.engineer_id) : "";
    if (select.value === "") select.selectedIndex = 0;
    select.disabled = !engineers().length;

    document.getElementById("assignField").hidden = !canAssign;
    document.getElementById("assignBtn").hidden = !canAssign;
    if (canAssign && !engineers().length) {
      O.showToast("Нет инженеров. Назначьте их в разделе «Пользователи»", 5000);
    }
    document.getElementById("detailDialog").showModal();
  }

  function initTickets() {
    tabsBox.addEventListener("click", function (e) {
      var b = e.target.closest("[data-filter]");
      if (!b) return;
      state.filter = b.dataset.filter;
      renderTickets();
    });
    document.getElementById("ticketSearch").addEventListener("input", function (e) {
      state.query = e.target.value;
      renderTickets();
    });
    tbody.addEventListener("click", function (e) {
      var b = e.target.closest("[data-open-ticket]");
      if (b) openTicket(Number(b.dataset.openTicket));
    });
    document.getElementById("assignForm").addEventListener("submit", function (e) {
      e.preventDefault();
      var engineerId = Number(document.getElementById("assign-engineer").value);
      if (!engineerId) return;
      O.api("/api/tickets/" + activeId + "/assign", "POST", { engineer_id: engineerId }).then(function (t) {
        for (var i = 0; i < tickets.length; i++) if (tickets[i].id === t.id) tickets[i] = t;
        document.getElementById("detailDialog").close();
        renderTickets();
        O.showToast("Заявка №" + t.id + ": инженер " + t.engineer);
      }).catch(function (err) { O.showError("Не удалось назначить инженера", err); });
    });
  }

  /* ---------- пользователи ---------- */

  function renderUsers() {
    var q = state.userQuery.trim().toLowerCase();
    var rows = users.filter(function (u) {
      return !q || u.full_name.toLowerCase().indexOf(q) !== -1 || u.email.toLowerCase().indexOf(q) !== -1;
    });
    if (!rows.length) {
      userBody.innerHTML = '<tr class="empty-row"><td colspan="4">Пользователей не найдено.</td></tr>';
      return;
    }
    userBody.innerHTML = rows.map(function (u) {
      var roleCell;
      if (u.perm === 3) {
        roleCell = O.roleBadge(u.perm, u.role);
      } else {
        roleCell = '<label class="visually-hidden" for="role-' + u.id + '">Роль: ' + esc(u.full_name) + "</label>" +
          '<select class="input input-sm" id="role-' + u.id + '" data-user-id="' + u.id + '">' +
          '<option value="Сотрудник"' + (u.perm === 1 ? " selected" : "") + ">Сотрудник</option>" +
          '<option value="Инженер"' + (u.perm === 2 ? " selected" : "") + ">Инженер</option></select>";
      }
      return "<tr>" +
        '<td class="ticket-equipment">' + esc(u.full_name) + "</td>" +
        "<td>" + esc(u.email) + "</td>" +
        "<td>" + esc(u.department) + "</td>" +
        "<td>" + roleCell + "</td></tr>";
    }).join("");
  }

  function loadUsers() {
    return O.api("/api/users").then(function (items) {
      users = items;
      renderUsers();
    }).catch(function (err) { O.showError("Не удалось загрузить пользователей", err); });
  }

  function initUsers() {
    document.getElementById("userSearch").addEventListener("input", function (e) {
      state.userQuery = e.target.value;
      renderUsers();
    });
    userBody.addEventListener("change", function (e) {
      var select = e.target.closest("select[data-user-id]");
      if (!select) return;
      O.api("/api/users/" + select.dataset.userId, "PATCH", { role: select.value }).then(function (u) {
        for (var i = 0; i < users.length; i++) if (users[i].id === u.id) users[i] = u;
        renderUsers();
        O.showToast(u.full_name + ": роль «" + u.role + "»");
      }).catch(function (err) {
        O.showError("Не удалось изменить роль", err);
        loadUsers();
      });
    });
  }

  /* ---------- разделы ---------- */

  function showSection(name) {
    if (name !== "users") name = "tickets";
    ["tickets", "users"].forEach(function (s) {
      document.getElementById("section-" + s).hidden = s !== name;
    });
    document.querySelectorAll("[data-section]").forEach(function (a) {
      if (a.dataset.section === name) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    O.initDialogs();
    O.initLogout();

    O.requireRole([3]).then(function (profile) {
      O.renderUser(profile);
      initTickets();
      initUsers();
      showSection(window.location.hash.slice(1));
      window.addEventListener("hashchange", function () { showSection(window.location.hash.slice(1)); });

      return Promise.all([
        loadUsers(),
        O.api("/api/tickets").then(function (items) {
          tickets = items;
          renderTickets();
        }).catch(function (err) { O.showError("Не удалось загрузить заявки", err); })
      ]);
    });
  });
})();

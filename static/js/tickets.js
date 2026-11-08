/**
 * Obsluga — кабинет сотрудника и инженера (tickets.html).
 *
 * Сотрудник: подаёт заявки, видит свои, карточка только для чтения.
 * Инженер:   видит очередь новых заявок и свои; берёт в работу, фиксирует диагноз
 *            и работы, закрывает.
 *
 *   GET  /api/auth/me            профиль и роль
 *   GET  /api/equipment          список для формы создания
 *   GET  /api/tickets            заявки (сервер сам отбирает нужные для роли)
 *   POST /api/tickets            создание (сотрудник)
 *   POST /api/tickets/:id/take   взять в работу (инженер)
 *   PATCH /api/tickets/:id       диагноз / работы / закрытие (инженер)
 */
(function () {
  "use strict";

  var O = window.Obsluga;
  var esc = O.escapeHtml;

  var TABS_EMPLOYEE = [
    { value: "all", label: "Все" }, { value: "new", label: "Новые" },
    { value: "progress", label: "В работе" }, { value: "closed", label: "Закрытые" }
  ];
  var TABS_ENGINEER = [
    { value: "new", label: "Очередь" }, { value: "progress", label: "Мои в работе" },
    { value: "closed", label: "Закрытые" }
  ];

  var profile = null;
  var isEngineer = false;
  var tickets = [];
  var state = { filter: "all", query: "" };
  var activeId = null;

  var tbody = document.getElementById("ticketTableBody");
  var tabsBox = document.getElementById("filterTabs");
  var detailForm = document.getElementById("detailForm");

  function byId(id) {
    for (var i = 0; i < tickets.length; i++) if (tickets[i].id === id) return tickets[i];
    return null;
  }

  function replaceTicket(updated) {
    for (var i = 0; i < tickets.length; i++) {
      if (tickets[i].id === updated.id) { tickets[i] = updated; return; }
    }
    tickets.unshift(updated);
  }

  function counts() {
    var c = { all: tickets.length, new: 0, progress: 0, closed: 0 };
    tickets.forEach(function (t) { c[t.status] = (c[t.status] || 0) + 1; });
    return c;
  }

  function renderTabs() {
    O.renderTabs(tabsBox, isEngineer ? TABS_ENGINEER : TABS_EMPLOYEE, state.filter, counts());
  }

  function emptyText() {
    if (state.query.trim()) return "По такому запросу заявок не найдено.";
    if (isEngineer) {
      return { new: "Очередь пуста — новых заявок нет.", progress: "У вас нет заявок в работе.", closed: "Закрытых заявок пока нет." }[state.filter];
    }
    return "У вас пока нет заявок. Нажмите «Новая заявка», чтобы сообщить о неисправности.";
  }

  function renderTable() {
    var q = state.query.trim().toLowerCase();
    var rows = tickets.filter(function (t) {
      var okFilter = state.filter === "all" || t.status === state.filter;
      var okQuery = !q || t.equipment.toLowerCase().indexOf(q) !== -1 || String(t.id).indexOf(q) !== -1;
      return okFilter && okQuery;
    });
    renderTabs();

    if (!rows.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="7">' + esc(emptyText()) + "</td></tr>";
      return;
    }
    tbody.innerHTML = rows.map(function (t) {
      var label = isEngineer && t.status === "new" ? "Открыть" : "Подробнее";
      return "<tr>" +
        "<td>№" + t.id + "</td>" +
        '<td class="ticket-equipment">' + esc(t.equipment) + "</td>" +
        '<td class="ticket-desc" title="' + esc(t.description) + '">' + esc(t.description) + "</td>" +
        "<td>" + O.statusBadge(t.status) + "</td>" +
        "<td>" + esc(t.engineer || "—") + "</td>" +
        "<td>" + O.fmtDate(t.updated) + "</td>" +
        '<td><button type="button" class="btn btn-ghost btn-sm" data-open-ticket="' + t.id + '">' + label + "</button></td>" +
        "</tr>";
    }).join("");
  }

  function fact(term, value) {
    return "<div><dt>" + esc(term) + "</dt><dd>" + value + "</dd></div>";
  }

  function openDetail(id) {
    var t = byId(id);
    if (!t) return;
    activeId = id;

    document.getElementById("detailDialogTitle").textContent = "Заявка №" + t.id;
    document.getElementById("detailMeta").innerHTML =
      fact("Статус", O.statusBadge(t.status)) +
      fact("Оборудование", esc(t.equipment)) +
      fact("Цех", esc(t.department)) +
      fact("Подал заявку", esc(t.reporter) + " (" + esc(t.reporter_department) + ")") +
      fact("Инженер", esc(t.engineer || "ещё не назначен")) +
      fact("Обновлено", O.fmtDate(t.updated)) +
      '<div class="fact-wide"><dt>Неисправность</dt><dd>' + esc(t.description) + "</dd></div>";

    var mine = isEngineer && t.engineer_id === profile.id;
    var editable = mine && t.status === "progress";
    var diagnosis = document.getElementById("detail-diagnosis");
    var work = document.getElementById("detail-work");
    diagnosis.value = t.diagnosis || "";
    work.value = t.workDone || "";
    diagnosis.readOnly = work.readOnly = !editable;
    // Пустые поля у не-редактируемой заявки не показываем
    diagnosis.closest(".field").hidden = !editable && !t.diagnosis;
    work.closest(".field").hidden = !editable && !t.workDone;

    document.getElementById("takeBtn").hidden = !(isEngineer && t.status === "new");
    document.getElementById("saveBtn").hidden = !editable;
    document.getElementById("closeTicketBtn").hidden = !editable;

    document.getElementById("detailDialog").showModal();
  }

  function afterChange(updated, message) {
    replaceTicket(updated);
    renderTable();
    O.showToast(message);
  }

  function initDetail() {
    tbody.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-open-ticket]");
      if (btn) openDetail(Number(btn.dataset.openTicket));
    });

    document.getElementById("takeBtn").addEventListener("click", function () {
      O.api("/api/tickets/" + activeId + "/take", "POST").then(function (t) {
        document.getElementById("detailDialog").close();
        state.filter = "progress";
        afterChange(t, "Заявка №" + t.id + " взята в работу");
      }).catch(function (err) {
        O.showError("Не удалось взять заявку", err);
        reload();
      });
    });

    function save(close) {
      var body = {
        diagnosis: detailForm.elements.diagnosis.value,
        workDone: detailForm.elements.workDone.value
      };
      if (close) body.status = "closed";
      return O.api("/api/tickets/" + activeId, "PATCH", body).then(function (t) {
        document.getElementById("detailDialog").close();
        if (close) state.filter = "closed";
        afterChange(t, close ? "Заявка №" + t.id + " закрыта" : "Изменения по заявке №" + t.id + " сохранены");
      }).catch(function (err) {
        O.showError(close ? "Не удалось закрыть заявку" : "Не удалось сохранить", err);
      });
    }

    detailForm.addEventListener("submit", function (e) { e.preventDefault(); save(false); });
    document.getElementById("closeTicketBtn").addEventListener("click", function () { save(true); });
  }

  function initCreate() {
    var btn = document.getElementById("openCreateDialog");
    var dialog = document.getElementById("createDialog");
    var form = document.getElementById("createTicketForm");
    btn.hidden = false;

    O.api("/api/equipment").then(function (items) {
      var select = document.getElementById("create-equipment");
      items.forEach(function (item) {
        var option = document.createElement("option");
        option.value = String(item.id);
        option.textContent = item.name + " — " + item.department;
        select.appendChild(option);
      });
    }).catch(function (err) { O.showError("Не удалось загрузить оборудование", err); });

    btn.addEventListener("click", function () { form.reset(); dialog.showModal(); });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      O.api("/api/tickets", "POST", {
        equipment_id: Number(form.elements.equipment.value),
        description: form.elements.description.value
      }).then(function (t) {
        dialog.close();
        state.filter = "all";
        afterChange(t, "Заявка №" + t.id + " создана");
      }).catch(function (err) { O.showError("Не удалось создать заявку", err); });
    });
  }

  function reload() {
    return O.api("/api/tickets").then(function (items) {
      tickets = items;
      renderTable();
    }).catch(function (err) { O.showError("Не удалось загрузить заявки", err); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    O.initDialogs();
    O.initLogout();

    O.requireRole([1, 2]).then(function (p) {
      profile = p;
      isEngineer = p.perm === 2;
      O.renderUser(p);

      state.filter = isEngineer ? "new" : "all";
      document.getElementById("pageTitle").textContent = isEngineer ? "Заявки инженера" : "Мои заявки";
      document.getElementById("pageLede").textContent = isEngineer
        ? "Возьмите заявку из очереди, зафиксируйте диагноз и выполненные работы, затем закройте её."
        : "Сообщите о неисправности и следите за ходом ремонта.";
      document.getElementById("tableCaption").textContent = isEngineer
        ? "Новые заявки и заявки, назначенные вам."
        : "Заявки, поданные вами.";
      if (!isEngineer) initCreate();

      tabsBox.addEventListener("click", function (e) {
        var b = e.target.closest("[data-filter]");
        if (!b) return;
        state.filter = b.dataset.filter;
        renderTable();
      });
      document.getElementById("ticketSearch").addEventListener("input", function (e) {
        state.query = e.target.value;
        renderTable();
      });
      initDetail();
      return reload().then(function () {
        // Если инженеру уже назначены заявки, сразу показываем их, а не пустую/чужую очередь
        if (isEngineer && counts().progress > 0) {
          state.filter = "progress";
          renderTable();
        }
      });
    });
  });
})();

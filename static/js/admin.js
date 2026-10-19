/**
 * Obsluga — admin panel interactions.
 *
 * BACKEND INTEGRATION POINTS
 * ---------------------------------------------------------------------
 * Every place data is currently read from or written to MOCK_TICKETS
 * below is marked with a TODO(backend) comment. The intended shape:
 *
 *   GET    /api/tickets                 -> Ticket[]              (replaces MOCK_TICKETS)
 *   GET    /api/equipment               -> Equipment[]           (fills the <select> in #createTicketForm)
 *   POST   /api/tickets                 -> Ticket                (createTicketForm submit)
 *   PATCH  /api/tickets/:id             -> Ticket                (detailForm submit)
 *
 * Ticket shape used throughout this file:
 *   { id, department, equipment, description, reporter, engineer, status, updated, diagnosis, workDone }
 *   status is one of: "new" | "progress" | "closed"
 * ---------------------------------------------------------------------
 */
(function () {
  "use strict";

  // TODO(backend): replace with data fetched from GET /api/tickets
  var MOCK_TICKETS = [
    { id: 1248, department: "Цех №2", equipment: "Компрессор ВК-25", description: "Падает давление на выходе, слышен посторонний стук.", reporter: "Олег Петров", engineer: "Мария Кузнецова", status: "progress", updated: "24 сен, 14:10", diagnosis: "Износ клапанной группы.", workDone: "Заменена клапанная плита, проверено давление." },
    { id: 1247, department: "Цех №1", equipment: "Токарный станок 16К20", description: "Не включается шпиндель, срабатывает автомат защиты.", reporter: "Ирина Волкова", engineer: "—", status: "new", updated: "26 сен, 09:02", diagnosis: "", workDone: "" },
    { id: 1246, department: "Цех №3", equipment: "Конвейерная лента №3", description: "Лента съезжает в сторону на участке загрузки.", reporter: "Сергей Титов", engineer: "Андрей Носов", status: "closed", updated: "22 сен, 17:40", diagnosis: "Разбалансировка натяжного ролика.", workDone: "Отрегулировано натяжение, лента выровнена." },
    { id: 1245, department: "Цех №2", equipment: "Сварочный аппарат ТДМ-317", description: "Нестабильная дуга, перегрев кабеля.", reporter: "Дмитрий Орлов", engineer: "Мария Кузнецова", status: "progress", updated: "25 сен, 11:20", diagnosis: "Повреждена изоляция силового кабеля.", workDone: "Кабель заменён, тест под нагрузкой в процессе." },
    { id: 1244, department: "Цех №4", equipment: "Насос ЦНС 60-99", description: "Протечка по сальниковому уплотнению.", reporter: "Наталья Быкова", engineer: "—", status: "new", updated: "26 сен, 08:15", diagnosis: "", workDone: "" },
    { id: 1243, department: "Цех №1", equipment: "Пресс гидравлический ПГ-100", description: "Медленный подъём плиты, падает рабочее давление.", reporter: "Игорь Соколов", engineer: "Андрей Носов", status: "closed", updated: "20 сен, 16:05", diagnosis: "Загрязнение гидравлического фильтра.", workDone: "Заменён фильтр и рабочая жидкость." },
    { id: 1242, department: "Цех №3", equipment: "Электропогрузчик EP-16", description: "Не держит заряд аккумулятор, разряжается за смену.", reporter: "Павел Гришин", engineer: "Мария Кузнецова", status: "new", updated: "26 сен, 10:40", diagnosis: "", workDone: "" },
    { id: 1241, department: "Цех №2", equipment: "Компрессор ВК-25", description: "Автоматическое отключение при достижении половины давления.", reporter: "Олег Петров", engineer: "Андрей Носов", status: "closed", updated: "18 сен, 13:00", diagnosis: "Неисправность реле давления.", workDone: "Реле давления заменено, проведён тестовый цикл." }
  ];

  var STATUS_LABEL = { new: "Новая", progress: "В работе", closed: "Закрыта" };
  var STATUS_BADGE_CLASS = { new: "badge-new", progress: "badge-progress", closed: "badge-closed" };

  var state = { filter: "all", query: "" };
  var activeTicketId = null;

  var tbody = document.getElementById("ticketTableBody");

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function renderTable() {
    var rows = MOCK_TICKETS.filter(function (t) {
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
          '<td>' + escapeHtml(t.engineer) + '</td>' +
          '<td>' + t.updated + '</td>' +
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

      // TODO(backend): POST /api/tickets with the fields below instead of unshifting into MOCK_TICKETS
      var nextId = Math.max.apply(null, MOCK_TICKETS.map(function (t) { return t.id; })) + 1;
      MOCK_TICKETS.unshift({
        id: nextId,
        // TODO(backend): цех берётся из профиля пользователя (указывается при регистрации), а не из формы
        department: form.elements.department.value,
        equipment: form.elements.equipment.value,
        description: form.elements.description.value,
        reporter: form.elements.reporter.value,
        engineer: "—",
        status: "new",
        updated: "только что",
        diagnosis: "",
        workDone: ""
      });

      dialog.close();
      renderTable();
      showToast("Заявка №" + nextId + " создана (демонстрационный режим, бэкенд ещё не подключён).");
    });
  }

  function openDetailDialog(ticketId) {
    var ticket = MOCK_TICKETS.filter(function (t) { return t.id === ticketId; })[0];
    if (!ticket) return;
    activeTicketId = ticketId;

    document.getElementById("detailDialogTitle").textContent = "Заявка №" + ticket.id;
    document.getElementById("detailMeta").innerHTML =
      '<span><strong>Цех:</strong> ' + escapeHtml(ticket.department) + '</span>' +
      '<span><strong>Оборудование:</strong> ' + escapeHtml(ticket.equipment) + '</span>' +
      '<span><strong>Подал заявку:</strong> ' + escapeHtml(ticket.reporter) + '</span>' +
      '<span><strong>Неисправность:</strong> ' + escapeHtml(ticket.description) + '</span>';

    document.getElementById("detail-status").value = ticket.status;
    document.getElementById("detail-diagnosis").value = ticket.diagnosis;
    document.getElementById("detail-work").value = ticket.workDone;

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

      // TODO(backend): PATCH /api/tickets/:id with { status, diagnosis, workDone }
      var ticket = MOCK_TICKETS.filter(function (t) { return t.id === activeTicketId; })[0];
      if (ticket) {
        ticket.status = form.elements.status.value;
        ticket.diagnosis = form.elements.diagnosis.value;
        ticket.workDone = form.elements.workDone.value;
        ticket.updated = "только что";
        if (ticket.engineer === "—" && ticket.status !== "new") {
          ticket.engineer = "Мария Кузнецова";
        }
      }

      document.getElementById("detailDialog").close();
      renderTable();
      showToast("Заявка №" + activeTicketId + " обновлена (демонстрационный режим, бэкенд ещё не подключён).");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderTable();
    initFilters();
    initSearch();
    initDialogClosers();
    initCreateDialog();
    initDetailDialog();
  });
})();

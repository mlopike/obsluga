/**
 * Obsluga — homepage interactions.
 * No backend calls on this page: the status demo below is a static
 * illustration of what a real ticket's status widget will look like
 * once tickets are served from an API (see js/admin.js for the shape
 * that integration is expected to take).
 */
(function () {
  "use strict";

  var STATUS_CONFIG = {
    new: {
      label: "Новая",
      badgeClass: "badge-new",
      progress: "20%",
      color: "var(--peach-400)",
      note: "Заявка зарегистрирована и ждёт, пока инженер возьмёт её в работу."
    },
    progress: {
      label: "В работе",
      badgeClass: "badge-progress",
      progress: "65%",
      color: "var(--teal-400)",
      note: "Инженер проводит диагностику и ремонт компрессора."
    },
    closed: {
      label: "Закрыта",
      badgeClass: "badge-closed",
      progress: "100%",
      color: "var(--indigo-600)",
      note: "Ремонт завершён, результат зафиксирован в истории оборудования."
    }
  };

  function initStatusDemo() {
    var buttons = document.querySelectorAll(".demo-steps button");
    var badge = document.getElementById("demoBadge");
    var progressBar = document.getElementById("demoProgress");
    var note = document.getElementById("demoNote");
    if (!buttons.length || !badge || !progressBar || !note) return;

    function applyStatus(status) {
      var config = STATUS_CONFIG[status];
      if (!config) return;

      badge.textContent = config.label;
      badge.className = "badge " + config.badgeClass;
      progressBar.style.width = config.progress;
      progressBar.style.backgroundColor = config.color;
      note.textContent = config.note;

      buttons.forEach(function (btn) {
        btn.setAttribute("aria-pressed", String(btn.dataset.status === status));
      });
    }

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        applyStatus(btn.dataset.status);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", initStatusDemo);
})();

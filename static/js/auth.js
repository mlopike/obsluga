/**
 * Obsluga — auth page interactions.
 *
 * BACKEND INTEGRATION POINTS
 * ---------------------------------------------------------------------
 * Both forms currently only validate on the client and show a mock
 * confirmation message. Replace the two `// TODO(backend)` blocks below
 * with real fetch() calls once the API exists, e.g.:
 *
 *   const res = await fetch('/api/auth/login', {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json' },
 *     body: JSON.stringify({ email, password })
 *   });
 *
 * On success, redirect to admin.html (engineer) or a future employee
 * dashboard; on failure, show the returned error in #formMessage.
 * ---------------------------------------------------------------------
 */
(function () {
  "use strict";

  function initTabs() {
    var tabs = document.querySelectorAll('[role="tab"]');
    var panels = {
      "tab-login": document.getElementById("panel-login"),
      "tab-register": document.getElementById("panel-register")
    };

    function selectTab(tab) {
      tabs.forEach(function (t) {
        var isSelected = t === tab;
        t.setAttribute("aria-selected", String(isSelected));
        panels[t.id].hidden = !isSelected;
      });
      hideMessage();
      tab.focus();
    }

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () { selectTab(tab); });
    });

    document.querySelectorAll("[data-switch-to]").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        var targetTab = document.getElementById("tab-" + link.dataset.switchTo);
        if (targetTab) selectTab(targetTab);
      });
    });

    // Open the register tab directly when the page is loaded as login.html#register
    if (window.location.hash === "#register") {
      selectTab(document.getElementById("tab-register"));
    }
  }

  function initPasswordToggles() {
    document.querySelectorAll(".password-toggle").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = document.getElementById(btn.dataset.toggleFor);
        if (!input) return;
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.setAttribute("aria-pressed", String(show));
        btn.setAttribute("aria-label", show ? "Скрыть пароль" : "Показать пароль");
      });
    });
  }

  function showMessage(text) {
    var box = document.getElementById("formMessage");
    box.textContent = text;
    box.classList.add("is-visible");
  }

  function hideMessage() {
    var box = document.getElementById("formMessage");
    box.classList.remove("is-visible");
    box.textContent = "";
  }

  function initLoginForm() {
    var form = document.getElementById("loginForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;

      // TODO(backend): send { email, password, remember } to POST /api/auth/login
      var email = form.elements.email.value;
      showMessage("Демонстрационный режим: данные для входа (" + email + ") пока не отправляются на сервер — бэкенд ещё не подключён.");
    });
  }

  function initRegisterForm() {
    var form = document.getElementById("registerForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;

      var password = form.elements.password.value;
      var confirm = form.elements.passwordConfirm.value;
      if (password !== confirm) {
        showMessage("Пароли не совпадают. Проверьте оба поля и попробуйте снова.");
        form.elements.passwordConfirm.focus();
        return;
      }

      // TODO(backend): send { fullName, email, department, role, password } to POST /api/auth/register
      showMessage("Демонстрационный режим: аккаунт пока не создаётся — бэкенд ещё не подключён.");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTabs();
    initPasswordToggles();
    initLoginForm();
    initRegisterForm();
  });
})();

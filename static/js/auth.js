/**
 * Obsluga — auth page interactions.
 *
 * Login:  POST /api/auth/login    { email, password, remember }
 * Register: POST /api/auth/register { full_name, email, department, role, password }
 * On success the token and profile are stored (localStorage for "remember",
 * sessionStorage otherwise) and the page redirects to admin.html.
 * On failure the API error detail is shown in #formMessage.
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

  function storeSession(token, profile, remember) {
    var storage = remember ? window.localStorage : window.sessionStorage;
    storage.setItem("token", token);
    storage.setItem("profile", JSON.stringify(profile));
  }

  function extractDetail(data) {
    if (!data || !data.detail) return null;
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map(function (item) { return item.msg; }).join("; ");
    }
    return String(data.detail);
  }

  function showError(response) {
    response.json().then(function (data) {
      showMessage(extractDetail(data) || "Не удалось выполнить запрос. Попробуйте позже.");
    }).catch(function () {
      showMessage("Не удалось выполнить запрос. Попробуйте позже.");
    });
  }

  function initLoginForm() {
    var form = document.getElementById("loginForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      hideMessage();

      var body = {
        email: form.elements.email.value,
        password: form.elements.password.value,
        remember: form.elements.remember.checked
      };

      fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      }).then(function (res) {
        if (res.ok) {
          return res.json().then(function (data) {
            storeSession(data.token, data.profile, body.remember);
            window.location.assign("admin.html");
          });
        }
        showError(res);
      }).catch(function () {
        showMessage("Сервер недоступен. Попробуйте позже.");
      });
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
      hideMessage();

      var body = {
        full_name: form.elements.fullName.value,
        email: form.elements.email.value,
        department: form.elements.department.value,
        role: form.elements.role.value,
        password: password
      };

      fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      }).then(function (res) {
        if (res.ok) {
          return res.json().then(function (data) {
            // Токен регистрации короткий (remember=False) — сессионное хранилище
            storeSession(data.token, data.profile, false);
            window.location.assign("admin.html");
          });
        }
        showError(res);
      }).catch(function () {
        showMessage("Сервер недоступен. Попробуйте позже.");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTabs();
    initPasswordToggles();
    initLoginForm();
    initRegisterForm();
  });
})();

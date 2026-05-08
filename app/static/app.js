window.HOIISP = {
  async handleFormSubmit(form) {
    const result = document.getElementById("form-result");
    const url = form.getAttribute("data-post");
    const body = new FormData(form);
    const res = await fetch(url, { method: "POST", body });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const errs = data.errors || [data];
      const msg = errs.map((e) => e.message || e.error || "Request failed").join(" | ");
      if (result) result.innerHTML = `<p class="error">${msg}</p>`;
      return;
    }
    if (result) result.innerHTML = `<p class="ok">${data.message || "Success."}</p>`;
    if (data.redirect) window.location.href = data.redirect;
    if (form.getAttribute("data-reload") === "1") window.location.reload();
  },

  bindForms() {
    document.querySelectorAll("form[data-post]").forEach((form) => {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        await window.HOIISP.handleFormSubmit(form);
      });
    });
  },

  startLeaderboardSSE() {
    const tbody = document.getElementById("leaderboard-body");
    if (!tbody) return;
    const sort = tbody.getAttribute("data-sort") || "stars";
    const ev = new EventSource("/api/stream/leaderboard");
    ev.addEventListener("refresh", async (event) => {
      const payload = JSON.parse(event.data);
      tbody.innerHTML = payload.tbody;
      const stats = document.getElementById("stats");
      if (stats) stats.outerHTML = payload.stats;
    });
  },
};

document.addEventListener("DOMContentLoaded", () => window.HOIISP.bindForms());

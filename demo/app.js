import { els, request, setSessionLabel } from "./core.js";
import { resetSession, submitChat } from "./chat.js";
import { createReminder, loadReminders, setDefaultReminderTime } from "./reminders.js";
import { loadServices } from "./services.js";

async function checkHealth() {
  try {
    const health = await request("/healthz");
    els.apiStatus.textContent = `API ok / rules ${health.rules_loaded}`;
    els.apiStatus.className = "status-pill ok";
  } catch {
    els.apiStatus.textContent = "API 未連線";
    els.apiStatus.className = "status-pill bad";
  }
}

function bindEvents() {
  els.chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitChat(els.messageInput.value);
  });
  document.querySelectorAll("[data-sample]").forEach((button) => {
    button.addEventListener("click", () => {
      els.messageInput.value = button.dataset.sample || "";
      submitChat(els.messageInput.value);
    });
  });
  els.resetButton.addEventListener("click", resetSession);
  els.refreshServices.addEventListener("click", loadServices);
  els.reminderForm.addEventListener("submit", createReminder);
  els.closeDialog.addEventListener("click", () => els.sourceDialog.close());
}

bindEvents();
setSessionLabel();
setDefaultReminderTime();
checkHealth();
loadServices();
loadReminders();
// Poll so a due reminder visibly flips to 已送達 during a demo (ADR-0006 sweep).
setInterval(loadReminders, 15000);

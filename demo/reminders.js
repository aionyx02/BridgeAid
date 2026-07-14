import { els, request, state } from "./core.js";

const REMINDER_TYPE_LABELS = {
  document: "補件",
  deadline: "期限",
  renewal: "續辦",
  eligibility: "即將符合",
};
const REMINDER_STATUS_LABELS = {
  pending: "待送達",
  sent: "已送達",
  cancelled: "已取消",
};
const CHANNEL_LABELS = { line: "LINE", email: "Email" };

export function prefillReminder(service) {
  // Mirror the LINE flow: deadline minus 7 days at 09:00, else a week from now;
  // consent stays unchecked — the human must opt in themselves (ADR-0005).
  const deadlines = (service.application_process || [])
    .map((step) => step.deadline_at)
    .filter(Boolean)
    .map((value) => new Date(`${value}T09:00:00`))
    .filter((date) => !Number.isNaN(date.getTime()));
  const target = deadlines.length
    ? new Date(Math.min(...deadlines))
    : new Date(Date.now() + 7 * 86400000);
  if (deadlines.length) {
    target.setDate(target.getDate() - 7);
  }
  const floor = new Date(Date.now() + 86400000);
  floor.setHours(9, 0, 0, 0);
  const chosen = target > floor ? target : floor;
  chosen.setHours(9, 0, 0, 0);

  els.reminderForm.reminder_type.value = "deadline";
  els.scheduledAt.value = new Date(chosen.getTime() - chosen.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
  els.reminderForm.note.value = service.service_name.slice(0, 80);
  els.reminderStatus.textContent = "已帶入提醒內容，勾選同意後送出即可建立。";
  els.reminderForm.scrollIntoView({ behavior: "smooth", block: "start" });
  els.reminderForm.consent.focus();
}

export function setDefaultReminderTime() {
  const date = new Date();
  date.setDate(date.getDate() + 7);
  date.setHours(9, 0, 0, 0);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
  els.scheduledAt.value = local;
}

function formatScheduledAt(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-TW", { dateStyle: "medium", timeStyle: "short" });
}

export async function loadReminders() {
  try {
    const body = await request(`/reminders/${state.sessionId}`);
    if (!body.reminders.length) {
      els.reminderList.className = "reminder-list empty-state";
      els.reminderList.textContent = "此 session 尚無提醒";
      return;
    }
    els.reminderList.className = "reminder-list";
    els.reminderList.replaceChildren(
      ...body.reminders.map((reminder) => {
        const row = document.createElement("article");
        row.className = "reminder-row";
        const summary = document.createElement("strong");
        const typeLabel = REMINDER_TYPE_LABELS[reminder.reminder_type] || reminder.reminder_type;
        summary.textContent = `${typeLabel}提醒 · ${CHANNEL_LABELS[reminder.channel] || reminder.channel}`;
        const badge = document.createElement("span");
        badge.className = `badge status-${reminder.status}`;
        badge.textContent = REMINDER_STATUS_LABELS[reminder.status] || reminder.status;
        const meta = document.createElement("p");
        meta.className = "meta";
        meta.textContent = formatScheduledAt(reminder.scheduled_at);
        if (reminder.note) {
          meta.textContent += ` · ${reminder.note}`;
        }
        const cancel = document.createElement("button");
        cancel.type = "button";
        cancel.textContent = "取消";
        cancel.disabled = reminder.status !== "pending";
        cancel.addEventListener("click", () => cancelReminder(reminder.id));
        row.append(summary, badge, meta, cancel);
        return row;
      }),
    );
  } catch (error) {
    els.reminderStatus.textContent = `提醒載入失敗：${error.message}`;
  }
}

async function cancelReminder(reminderId) {
  try {
    await request(`/reminders/${reminderId}?session_id=${encodeURIComponent(state.sessionId)}`, {
      method: "DELETE",
    });
    els.reminderStatus.textContent = "已取消提醒";
    await loadReminders();
  } catch (error) {
    els.reminderStatus.textContent = `取消失敗：${error.message}`;
  }
}

export async function createReminder(event) {
  event.preventDefault();
  const form = new FormData(els.reminderForm);
  const payload = {
    session_id: state.sessionId,
    reminder_type: form.get("reminder_type"),
    scheduled_at: form.get("scheduled_at"),
    channel: form.get("channel"),
    consent: form.get("consent") === "on",
    note: form.get("note") || null,
  };
  if (!payload.consent) {
    els.reminderStatus.textContent = "請先勾選「同意建立提醒」（提醒為 opt-in）";
    return;
  }
  try {
    await request("/reminders", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    els.reminderStatus.textContent = "已建立提醒";
    await loadReminders();
  } catch (error) {
    els.reminderStatus.textContent = `建立失敗：${error.message}`;
  }
}

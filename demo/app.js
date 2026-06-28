const state = {
  sessionId: getSessionId(),
  messages: [],
  lastReply: null,
};

const els = {
  apiStatus: document.querySelector("#apiStatus"),
  sessionLabel: document.querySelector("#sessionLabel"),
  messages: document.querySelector("#messages"),
  quickReplies: document.querySelector("#quickReplies"),
  chatForm: document.querySelector("#chatForm"),
  messageInput: document.querySelector("#messageInput"),
  resetButton: document.querySelector("#resetButton"),
  resultSummary: document.querySelector("#resultSummary"),
  resultCards: document.querySelector("#resultCards"),
  conflicts: document.querySelector("#conflicts"),
  documentChecklist: document.querySelector("#documentChecklist"),
  serviceList: document.querySelector("#serviceList"),
  refreshServices: document.querySelector("#refreshServices"),
  reminderForm: document.querySelector("#reminderForm"),
  reminderStatus: document.querySelector("#reminderStatus"),
  reminderList: document.querySelector("#reminderList"),
  scheduledAt: document.querySelector("#scheduledAt"),
  sourceDialog: document.querySelector("#sourceDialog"),
  sourceDetail: document.querySelector("#sourceDetail"),
  closeDialog: document.querySelector("#closeDialog"),
};

function getSessionId() {
  const saved = window.localStorage.getItem("bridgeaid-demo-session");
  if (saved) {
    return saved;
  }
  const created = `demo-${crypto.randomUUID()}`;
  window.localStorage.setItem("bridgeaid-demo-session", created);
  return created;
}

function setSessionLabel() {
  els.sessionLabel.textContent = state.sessionId.replace("demo-", "session ");
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail || detail;
    } catch {
      // Keep default detail.
    }
    throw new Error(`${response.status} ${detail}`);
  }
  return response.json();
}

function addMessage(role, text) {
  state.messages.push({ role, text });
  renderMessages();
}

function renderMessages() {
  els.messages.replaceChildren(
    ...state.messages.map((message) => {
      const item = document.createElement("li");
      item.className = `message ${message.role}`;
      item.textContent = message.text;
      return item;
    }),
  );
  els.messages.scrollTop = els.messages.scrollHeight;
}

function renderQuickReplies(options) {
  els.quickReplies.replaceChildren(
    ...options.map((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = option;
      button.addEventListener("click", () => submitChat(option));
      return button;
    }),
  );
}

async function submitChat(text) {
  const message = text.trim();
  if (!message) {
    return;
  }
  addMessage("user", message);
  els.messageInput.value = "";
  renderQuickReplies([]);

  try {
    const reply = await request("/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: state.sessionId, message }),
    });
    state.lastReply = reply;
    addMessage("assistant", reply.text);
    if (reply.kind === "question") {
      renderQuickReplies(reply.options || []);
      return;
    }
    renderResults(reply);
  } catch (error) {
    addMessage("assistant", `暫時無法取得回覆：${error.message}`);
  }
}

function renderResults(reply) {
  const results = reply.results || [];
  els.resultSummary.className = "empty-state";
  els.resultSummary.textContent = reply.text || "沒有推薦摘要";
  renderConflicts(reply.conflicts || []);
  renderCards(results);
  renderChecklist(reply.document_checklist || []);
}

function renderConflicts(conflicts) {
  if (!conflicts.length) {
    els.conflicts.hidden = true;
    els.conflicts.replaceChildren();
    return;
  }
  els.conflicts.hidden = false;
  const items = conflicts.map((conflict) => {
    const row = document.createElement("p");
    row.textContent = `${conflict.type}: ${conflict.service_ids.join(" / ")} - ${conflict.reason}`;
    return row;
  });
  els.conflicts.replaceChildren(...items);
}

function renderCards(results) {
  if (!results.length) {
    els.resultCards.replaceChildren();
    return;
  }
  els.resultCards.replaceChildren(
    ...results.map((service) => {
      const card = document.createElement("article");
      card.className = "result-card";

      const title = document.createElement("h3");
      title.textContent = service.service_name;

      const badge = document.createElement("span");
      badge.className = `badge${service.needs_review ? " review" : ""}`;
      badge.textContent = service.needs_review ? "需人工確認" : "可能符合";

      const source = document.createElement("p");
      source.className = "meta";
      source.textContent = `來源檢查：${service.source?.last_checked_at || "未提供"}`;

      const docs = document.createElement("ul");
      docs.className = "document-list";
      for (const documentName of service.documents || []) {
        const item = document.createElement("li");
        item.textContent = documentName;
        docs.append(item);
      }

      const sourceButton = document.createElement("button");
      sourceButton.type = "button";
      sourceButton.textContent = "查看來源";
      sourceButton.addEventListener("click", () => showSource(service.service_id));

      card.append(title, badge, source, docs, sourceButton);
      return card;
    }),
  );
}

function renderChecklist(items) {
  if (!items.length) {
    els.documentChecklist.className = "empty-state";
    els.documentChecklist.textContent = "尚無文件項目";
    return;
  }
  els.documentChecklist.className = "checklist-list";
  els.documentChecklist.replaceChildren(
    ...items.map((item) => {
      const label = document.createElement("label");
      label.className = "checklist-item";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      const text = document.createElement("span");
      text.textContent = `${item.document} (${item.services.join(", ")})`;
      label.append(checkbox, text);
      return label;
    }),
  );
}

async function loadServices() {
  els.serviceList.textContent = "載入中";
  try {
    const body = await request("/services");
    const rows = body.services.map((service) => {
      const row = document.createElement("article");
      row.className = "service-row";
      const name = document.createElement("strong");
      name.textContent = service.name;
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = `${service.category} / ${service.needs_review ? "需人工確認" : "active"}`;
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "來源";
      button.addEventListener("click", () => showSource(service.service_id));
      row.append(name, meta, button);
      return row;
    });
    els.serviceList.replaceChildren(...rows);
  } catch (error) {
    els.serviceList.textContent = `載入失敗：${error.message}`;
  }
}

async function showSource(serviceId) {
  els.sourceDetail.textContent = "載入中";
  els.sourceDialog.showModal();
  try {
    const source = await request(`/services/${serviceId}/source`);
    const link = document.createElement("a");
    link.className = "source-link";
    link.href = source.source.url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = source.source.url;

    const fields = [
      ["服務", source.service_name],
      ["版本", source.version],
      ["狀態", source.needs_review ? "需人工確認" : "active"],
      ["來源", source.source.title],
      ["檢查日期", source.source.last_checked_at],
    ];
    const list = document.createElement("dl");
    for (const [label, value] of fields) {
      const term = document.createElement("dt");
      term.textContent = label;
      const description = document.createElement("dd");
      description.textContent = value;
      list.append(term, description);
    }
    els.sourceDetail.replaceChildren(list, link);
  } catch (error) {
    els.sourceDetail.textContent = `載入失敗：${error.message}`;
  }
}

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

function setDefaultReminderTime() {
  const date = new Date();
  date.setDate(date.getDate() + 7);
  date.setHours(9, 0, 0, 0);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
  els.scheduledAt.value = local;
}

async function loadReminders() {
  try {
    const body = await request(`/reminders/${state.sessionId}`);
    if (!body.reminders.length) {
      els.reminderList.textContent = "";
      return;
    }
    els.reminderList.replaceChildren(
      ...body.reminders.map((reminder) => {
        const row = document.createElement("article");
        row.className = "reminder-row";
        const summary = document.createElement("strong");
        summary.textContent = `${reminder.reminder_type} / ${reminder.channel}`;
        const meta = document.createElement("p");
        meta.className = "meta";
        meta.textContent = `${reminder.scheduled_at} / ${reminder.status}`;
        const cancel = document.createElement("button");
        cancel.type = "button";
        cancel.textContent = "取消";
        cancel.disabled = reminder.status === "cancelled";
        cancel.addEventListener("click", () => cancelReminder(reminder.id));
        row.append(summary, meta, cancel);
        return row;
      }),
    );
  } catch (error) {
    els.reminderStatus.textContent = `提醒載入失敗：${error.message}`;
  }
}

async function cancelReminder(reminderId) {
  try {
    await fetch(`/reminders/${reminderId}?session_id=${encodeURIComponent(state.sessionId)}`, {
      method: "DELETE",
    });
    els.reminderStatus.textContent = "已取消提醒";
    await loadReminders();
  } catch (error) {
    els.reminderStatus.textContent = `取消失敗：${error.message}`;
  }
}

async function createReminder(event) {
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

function resetSession() {
  window.localStorage.removeItem("bridgeaid-demo-session");
  state.sessionId = getSessionId();
  state.messages = [];
  state.lastReply = null;
  renderMessages();
  renderQuickReplies([]);
  renderResults({ text: "尚未送出情境", results: [], conflicts: [], document_checklist: [] });
  setSessionLabel();
  loadReminders();
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

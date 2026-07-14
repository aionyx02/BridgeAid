import { els, state } from "./core.js";

const CONFLICT_TYPE_LABELS = { mutually_exclusive: "可能需擇一申請" };

export function addMessage(role, text) {
  state.messages.push({ role, text });
  renderMessages();
}

export function renderMessages() {
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

export function renderQuickReplies(options, onSelect) {
  els.quickReplies.replaceChildren(
    ...options.map((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = option;
      button.addEventListener("click", () => onSelect(option));
      return button;
    }),
  );
}

export function setChatBusy(busy) {
  const submit = els.chatForm.querySelector('button[type="submit"]');
  submit.disabled = busy;
  submit.textContent = busy ? "思考中…" : "送出";
}

export function renderResults(reply, actions = {}) {
  const results = reply.results || [];
  els.resultSummary.className = "empty-state";
  els.resultSummary.textContent = reply.text || "沒有推薦摘要";
  renderConflicts(reply.conflicts || []);
  renderCards(results, actions);
  renderChecklist(reply.document_checklist || []);
}

function renderConflicts(conflicts) {
  if (!conflicts.length) {
    els.conflicts.hidden = true;
    els.conflicts.replaceChildren();
    return;
  }
  els.conflicts.hidden = false;
  const nameById = new Map(
    (state.lastReply?.results || []).map((service) => [service.service_id, service.service_name]),
  );
  const items = conflicts.map((conflict) => {
    const row = document.createElement("p");
    const label = CONFLICT_TYPE_LABELS[conflict.type] || conflict.type;
    const names = conflict.service_ids.map((id) => nameById.get(id) || id).join("、");
    row.textContent = `${label}：${names}。${conflict.reason}`;
    return row;
  });
  els.conflicts.replaceChildren(...items);
}

function renderCards(results, actions) {
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
      sourceButton.addEventListener("click", () => actions.showSource?.(service.service_id));

      const remindButton = document.createElement("button");
      remindButton.type = "button";
      remindButton.textContent = "提醒我申請";
      remindButton.addEventListener("click", () => actions.prefillReminder?.(service));

      card.append(title, badge, source, docs);
      const steps = renderProcessSteps(service.application_process || []);
      if (steps) {
        card.append(steps);
      }
      card.append(sourceButton, remindButton);
      return card;
    }),
  );
}

function renderProcessSteps(processSteps) {
  if (!processSteps.length) {
    return null;
  }
  const wrapper = document.createElement("section");
  wrapper.className = "process";
  const heading = document.createElement("h4");
  heading.textContent = "申請流程";
  const list = document.createElement("ol");
  list.className = "process-steps";
  for (const step of processSteps) {
    const item = document.createElement("li");
    item.textContent = `${step.name}：${step.description}`;
    if (step.deadline) {
      const deadline = document.createElement("p");
      deadline.className = "deadline";
      deadline.textContent = `⏰ ${step.deadline}`;
      item.append(deadline);
    }
    if (step.url) {
      const link = document.createElement("a");
      link.href = step.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = `${step.url_title || "官方連結"} ↗`;
      const linkRow = document.createElement("p");
      linkRow.append(link);
      item.append(linkRow);
    }
    list.append(item);
  }
  wrapper.append(heading, list);
  return wrapper;
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

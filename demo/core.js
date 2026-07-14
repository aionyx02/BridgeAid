export const state = {
  sessionId: getSessionId(),
  messages: [],
  lastReply: null,
};

export const els = {
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

const SESSION_KEY = "bridgeaid-demo-session";

function getSessionId() {
  const saved = window.localStorage.getItem(SESSION_KEY);
  if (saved) {
    return saved;
  }
  const created = `demo-${crypto.randomUUID()}`;
  window.localStorage.setItem(SESSION_KEY, created);
  return created;
}

export function resetClientState() {
  window.localStorage.removeItem(SESSION_KEY);
  state.sessionId = getSessionId();
  state.messages = [];
  state.lastReply = null;
}

export function setSessionLabel() {
  els.sessionLabel.textContent = state.sessionId.replace("demo-", "session ");
}

export async function request(path, options = {}) {
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

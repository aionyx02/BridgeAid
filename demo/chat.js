import { els, request, resetClientState, setSessionLabel, state } from "./core.js";
import { loadReminders, prefillReminder } from "./reminders.js";
import {
  addMessage,
  renderMessages,
  renderQuickReplies,
  renderResults,
  setChatBusy,
} from "./render.js";
import { showSource } from "./services.js";

const resultActions = { showSource, prefillReminder };

export async function submitChat(text) {
  const message = text.trim();
  if (!message) {
    return;
  }
  addMessage("user", message);
  els.messageInput.value = "";
  renderQuickReplies([], submitChat);
  setChatBusy(true);

  try {
    const reply = await request("/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: state.sessionId, message }),
    });
    state.lastReply = reply;
    addMessage("assistant", reply.text);
    renderQuickReplies(reply.options || [], submitChat);
    if (reply.kind === "result") {
      renderResults(reply, resultActions);
    }
  } catch (error) {
    addMessage("assistant", `暫時無法取得回覆：${error.message}`);
  } finally {
    setChatBusy(false);
  }
}

export function resetSession() {
  resetClientState();
  renderMessages();
  renderQuickReplies([], submitChat);
  renderResults({ text: "尚未送出情境", results: [], conflicts: [], document_checklist: [] });
  setSessionLabel();
  loadReminders();
}

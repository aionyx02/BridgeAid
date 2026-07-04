"""LINE Flex Message rendering for recommendation results (TASK.015).

One bubble per possibly-eligible service: status line, administrative steps
(from the rule's `application_process`, TASK.014), deadline note, and footer
buttons — official application entry, traceable source, and an opt-in
"remind me" postback. Pure builders; no I/O.
"""

from __future__ import annotations

from typing import Any

MAX_BUBBLES = 10  # LINE allows 12; keep headroom
_LABEL_MAX = 20  # LINE action-label limit

STATUS_LINE = "可能符合（實際資格需承辦單位確認）"
REVIEW_LINE = "資料待人工確認，僅供參考"


def _label(text: str, fallback: str) -> str:
    return (text or fallback)[:_LABEL_MAX]


def _step_texts(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        rows.append(
            {
                "type": "text",
                "text": f"{index}. {step['name']}｜{step['description']}",
                "size": "xs",
                "color": "#555555",
                "wrap": True,
            }
        )
        if step.get("deadline"):
            rows.append(
                {
                    "type": "text",
                    "text": f"⏰ {step['deadline']}",
                    "size": "xs",
                    "color": "#B45309",
                    "wrap": True,
                }
            )
    return rows


def _entry_step(steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    """First step that carries an official URL (the application entry point)."""
    for step in steps:
        if step.get("url"):
            return step
    return None


def service_bubble(service: dict[str, Any]) -> dict[str, Any]:
    steps = service.get("application_process", [])
    status_text = REVIEW_LINE if service.get("needs_review") else STATUS_LINE
    body: list[dict[str, Any]] = [
        {"type": "text", "text": service["service_name"], "weight": "bold", "wrap": True},
        {"type": "text", "text": status_text, "size": "xs", "color": "#0F766E", "wrap": True},
    ]
    if steps:
        body.append({"type": "separator", "margin": "md"})
        body.append(
            {"type": "text", "text": "申請流程", "weight": "bold", "size": "sm", "margin": "md"}
        )
        body.extend(_step_texts(steps))

    footer: list[dict[str, Any]] = []
    entry = _entry_step(steps)
    if entry:
        footer.append(
            {
                "type": "button",
                "style": "primary",
                "height": "sm",
                "action": {
                    "type": "uri",
                    "label": _label(entry.get("url_title", ""), "官方申請入口"),
                    "uri": entry["url"],
                },
            }
        )
    source_url = (service.get("source") or {}).get("url")
    if source_url:
        footer.append(
            {
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {"type": "uri", "label": "資料來源", "uri": source_url},
            }
        )
    footer.append(
        {
            "type": "button",
            "style": "secondary",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": "提醒我申請",
                "data": f"action=remind&service={service['service_id']}",
                "displayText": f"提醒我申請{service['service_name']}"[:300],
            },
        }
    )

    return {
        "type": "bubble",
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": body},
        "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer},
    }


def results_flex_message(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Carousel of service bubbles, or None when there is nothing to show."""
    if not results:
        return None
    bubbles = [service_bubble(service) for service in results[:MAX_BUBBLES]]
    return {
        "type": "flex",
        "altText": "推薦服務與申請流程",
        "contents": {"type": "carousel", "contents": bubbles},
    }


def remind_consent_message(service_id: str, service_name: str) -> dict[str, Any]:
    """Opt-in confirmation before any reminder is stored (ADR-0005)."""
    return {
        "type": "text",
        "text": (
            f"要為「{service_name}」建立申請提醒，需要你的同意：\n"
            "系統只會保存提醒類型與時間（不含個人敘述），你可以隨時取消。"
        ),
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "同意，建立提醒",
                        "data": f"action=remind_ok&service={service_id}",
                        "displayText": "同意，建立提醒",
                    },
                },
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "先不要",
                        "data": "action=remind_no",
                        "displayText": "先不要",
                    },
                },
            ]
        },
    }

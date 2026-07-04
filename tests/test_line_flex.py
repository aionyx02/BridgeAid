"""Flex Message builders: process cards, entry buttons, opt-in postbacks."""

from __future__ import annotations

from app.line.flex import (
    MAX_BUBBLES,
    remind_consent_message,
    results_flex_message,
    service_bubble,
)


def _service(service_id: str = "rent_subsidy_central") -> dict:
    return {
        "service_id": service_id,
        "service_name": "300億元中央擴大租金補貼",
        "needs_review": False,
        "source": {"url": "https://www.nlma.gov.tw/", "last_checked_at": "2026-07-02"},
        "application_process": [
            {
                "name": "線上申請",
                "description": "至內政部租金補貼線上申請系統送件",
                "url": "https://has.nlma.gov.tw/house300e/",
                "url_title": "租金補貼線上申請",
                "deadline": "115年度受理至 2026-12-31",
                "deadline_at": "2026-12-31",
            },
            {"name": "審查", "description": "縣市政府審查資格與文件"},
        ],
    }


def test_bubble_has_steps_deadline_and_three_buttons():
    bubble = service_bubble(_service())
    body_texts = [c["text"] for c in bubble["body"]["contents"] if c["type"] == "text"]
    assert any("線上申請" in t for t in body_texts)
    assert any(t.startswith("⏰") for t in body_texts)

    actions = [b["action"] for b in bubble["footer"]["contents"]]
    assert actions[0]["type"] == "uri"
    assert actions[0]["uri"] == "https://has.nlma.gov.tw/house300e/"
    assert actions[1] == {"type": "uri", "label": "資料來源", "uri": "https://www.nlma.gov.tw/"}
    assert actions[2]["type"] == "postback"
    assert actions[2]["data"] == "action=remind&service=rent_subsidy_central"


def test_bubble_without_steps_still_offers_reminder():
    service = _service()
    service["application_process"] = []
    bubble = service_bubble(service)
    actions = [b["action"] for b in bubble["footer"]["contents"]]
    assert [a["type"] for a in actions] == ["uri", "postback"]  # source + remind only


def test_action_labels_respect_line_limit():
    service = _service()
    service["application_process"][0]["url_title"] = "超" * 40
    bubble = service_bubble(service)
    for button in bubble["footer"]["contents"]:
        assert len(button["action"]["label"]) <= 20


def test_carousel_caps_bubbles_and_empty_is_none():
    assert results_flex_message([]) is None
    message = results_flex_message([_service(f"s{i}") for i in range(MAX_BUBBLES + 3)])
    assert message["type"] == "flex"
    assert len(message["contents"]["contents"]) == MAX_BUBBLES


def test_consent_message_offers_ok_and_no_postbacks():
    message = remind_consent_message("rent_subsidy_central", "租金補貼")
    data = [item["action"]["data"] for item in message["quickReply"]["items"]]
    assert data == ["action=remind_ok&service=rent_subsidy_central", "action=remind_no"]

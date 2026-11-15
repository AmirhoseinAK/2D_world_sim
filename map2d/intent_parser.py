"""Turn player text into a structured room action via the LLM."""
from __future__ import annotations

from core.llm_client import LLMClient
from core.prompt_builder import build_intent_prompt
from core.response_parser import extract_json


def parse_intent(
    llm: LLMClient,
    room_label: str,
    depth: int,
    occupied: list[str],
    free: list[str],
    remaining: int,
    player_text: str,
) -> dict:
    if not free:
        return {
            "action": "reject",
            "message": "There's no space for a new door here.",
        }

    prompt = build_intent_prompt(
        room_label=room_label,
        depth=depth,
        occupied=occupied,
        free=free,
        remaining=remaining,
        player_text=player_text,
    )
    raw = llm.chat("You output JSON only.", prompt)
    data = extract_json(raw)

    if not data:
        return {
            "action": "reject",
            "message": "(The world stays silent.)",
        }

    if data.get("action") == "add_door":
        d = data.get("direction", "")
        if d not in free:
            return {
                "action": "reject",
                "message": "You can't go there right now.",
            }
        return {
            "action": "add_door",
            "direction": d,
            "label": str(data.get("label") or "New Room")[:40],
            "message": str(data.get("message") or "")[:120],
            "room_spec": data.get("room_spec") or {},
        }

    return {
        "action": "reject",
        "message": str(
            data.get("message") or "You can't go there right now."
        )[:120],
    }
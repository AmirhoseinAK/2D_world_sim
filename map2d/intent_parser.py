"""Unified turn parser + NPC dialogue parser."""
from __future__ import annotations

from core.llm_client import LLMClient
from core.prompt_builder import (
    build_birth_prompt,
    build_turn_prompt,
    build_entry_prompt,
    build_npc_dialogue_prompt,
)
from core.response_parser import extract_json


def parse_birth(llm: LLMClient, state):
    raw = llm.chat(
        "You output valid JSON only. No prose.",
        build_birth_prompt(state),
        max_tokens=400,
    )
    data = extract_json(raw) or {}
    name = str(data.get("name") or "Alex")[:30]
    city = str(data.get("city") or state.country)[:30]
    sprite = str(data.get("sprite") or "male_01")[:12]
    narrative = str(
        data.get("narrative")
        or f"You are born in {state.country}. Three years pass."
    )
    return name, city, sprite, narrative


def parse_turn(
    llm: LLMClient,
    state,
    room_label: str,
    depth: int,
    objects: list[dict],
    occupied: list[str],
    free: list[str],
    remaining: int,
    player_text: str,
) -> dict:
    if not free and depth < 2:
        return {
            "intent": "reject",
            "message": "There's no space for a new door here.",
        }

    prompt = build_turn_prompt(
        state=state,
        room_label=room_label,
        depth=depth,
        objects=objects,
        occupied=occupied,
        free=free,
        remaining=remaining,
        player_text=player_text,
    )
    raw = llm.chat("You output JSON only.", prompt)
    data = extract_json(raw)

    if not data:
        return {"intent": "reject", "message": "(The world stays silent.)"}

    intent = data.get("intent", "reject")

    if intent == "go":
        d = data.get("direction", "")
        if d not in free:
            return {"intent": "reject", "message": "You can't go there right now."}
        return {
            "intent": "go",
            "direction": d,
            "label": str(data.get("label") or "New Room")[:40],
            "message": str(data.get("message") or "")[:120],
            "entry_narrative": str(data.get("entry_narrative") or "")[:400],
            "room_spec": data.get("room_spec") or {},
            "deltas": data.get("deltas") or {},
        }

    if intent == "act":
        return {
            "intent": "act",
            "narrative": str(data.get("narrative") or "You wait.")[:600],
            "deltas": data.get("deltas") or {},
        }

    return {
        "intent": "reject",
        "message": str(data.get("message") or "You can't do that.")[:120],
    }


def narrate_entry(llm: LLMClient, state, room_label: str) -> str:
    raw = llm.chat(
        "You output JSON only.",
        build_entry_prompt(state, room_label),
    )
    data = extract_json(raw) or {}
    return str(data.get("entry") or f"You enter {room_label}.")[:200]


def parse_npc_dialogue(llm: LLMClient, state, npc, room_label, player_text):
    raw = llm.chat(
        "You output JSON only.",
        build_npc_dialogue_prompt(state, npc, room_label, player_text),
        max_tokens=400,
    )
    data = extract_json(raw) or {}
    response = str(data.get("response") or "...")[:400]
    deltas = data.get("deltas") or {}
    return response, deltas
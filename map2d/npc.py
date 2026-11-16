"""NPC helpers: detection, validation, distance, fallback generation."""
from __future__ import annotations

import random

from .constants import TILE

MAX_LOG = 8
DEFAULT_COLOR = (240, 240, 240)


DEFAULT_NPCS_BY_KEYWORD = [
    (("restaurant", "diner", "bistro", "tavern"),
     {"name": "Bella", "role": "cook", "color": (220, 180, 140),
      "personality": "warm and always busy"}),
    (("cafe", "coffee", "bar", "pub", "tea"),
     {"name": "Marco", "role": "barista", "color": (200, 170, 130),
      "personality": "friendly and quick"}),
    (("shop", "store", "market", "grocery", "boutique"),
     {"name": "Omar", "role": "shopkeeper", "color": (220, 200, 150),
      "personality": "quiet, watches customers"}),
    (("school", "classroom", "library", "university"),
     {"name": "Ms. Chen", "role": "teacher", "color": (200, 220, 240),
      "personality": "patient and firm"}),
    (("hospital", "ward", "clinic", "doctor", "pharmacy"),
     {"name": "Nora", "role": "nurse", "color": (240, 240, 250),
      "personality": "tired but kind"}),
    (("park", "garden", "square"),
     {"name": "A stranger", "role": "stranger", "color": (180, 180, 180),
      "personality": "unreadable, watching"}),
    (("house", "home", "apartment", "bedroom", "kitchen", "living"),
     {"name": "A sibling", "role": "family", "color": (240, 220, 180),
      "personality": "familiar and curious"}),
    (("office", "workplace", "study"),
     {"name": "A coworker", "role": "coworker", "color": (200, 200, 200),
      "personality": "focused and quiet"}),
]


def validate_npcs(raw_list, w, h):
    if not isinstance(raw_list, list):
        return []
    out = []
    used = set()
    for item in raw_list[:3]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "Someone")[:20]
        role = str(item.get("role") or "person")[:20]
        personality = str(item.get("personality") or "")[:120]
        try:
            x = int(item.get("pos", [0, 0])[0])
            y = int(item.get("pos", [0, 0])[1])
        except (TypeError, ValueError, IndexError):
            continue
        # Clamp instead of reject — keeps the NPC in the room even
        # if the LLM was slightly off.
        x = max(1, min(x, w - 2))
        y = max(1, min(y, h - 2))
        if (x, y) in used:
            continue
        used.add((x, y))
        color = _color(item.get("color"))
        out.append({
            "name": name,
            "role": role,
            "pos": (x, y),
            "color": color,
            "personality": personality,
            "conversation_log": [],
        })
    return out


def default_npc_for_room(label, w, h, occupied):
    """Return a list with one fallback NPC if the label warrants it."""
    label_l = label.lower()
    template = None
    for keywords, npc_tmpl in DEFAULT_NPCS_BY_KEYWORD:
        if any(kw in label_l for kw in keywords):
            template = npc_tmpl
            break
    if template is None:
        return []

    candidates = [
        (x, y) for x in range(2, w - 1) for y in range(2, h - 1)
        if (x, y) not in occupied
    ]
    if not candidates:
        return []
    pos = random.choice(candidates)

    return [{
        "name": template["name"],
        "role": template["role"],
        "pos": pos,
        "color": template["color"],
        "personality": template["personality"],
        "conversation_log": [],
    }]


def _color(c):
    if isinstance(c, (list, tuple)) and len(c) == 3:
        try:
            return tuple(max(0, min(255, int(v))) for v in c)
        except (TypeError, ValueError):
            pass
    return DEFAULT_COLOR


def nearest_npc(player, npcs, max_dist_tiles=2.0):
    if not npcs:
        return None
    max_dist_px = max_dist_tiles * TILE   # <-- تایل به پیکسل تبدیل شد
    best = None
    best_d = max_dist_px
    for npc in npcs:
        nx = npc["pos"][0] * TILE + TILE / 2.0
        ny = npc["pos"][1] * TILE + TILE / 2.0
        d = ((player.x - nx) ** 2 + (player.y - ny) ** 2) ** 0.5
        if d < best_d:
            best_d = d
            best = npc
    return best


def push_log(npc, role, text):
    npc["conversation_log"].append({"role": role, "text": text})
    if len(npc["conversation_log"]) > MAX_LOG:
        npc["conversation_log"] = npc["conversation_log"][-MAX_LOG:]
"""Save/load entire game to/from JSON."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAVES_DIR = PROJECT_ROOT / "saves"
SAVES_DIR.mkdir(exist_ok=True)

VERSION = 1


def list_saves() -> list[dict]:
    out = []
    for f in sorted(SAVES_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text("utf-8"))
        except Exception:
            continue
        state = data.get("state", {})
        world = data.get("world", {})
        rooms = world.get("rooms", {})
        cid = world.get("current_id", "")
        room_label = rooms.get(cid, {}).get("label", cid)
        out.append({
            "path": f,
            "filename": f.stem,
            "character": state.get("name", "?"),
            "age": state.get("age", 0),
            "room": room_label,
            "saved_at": data.get("saved_at", ""),
            "alive": state.get("alive", True),
        })
    return out


def save_game(path: Path, state_dict, world_dict, player_pos, last_tile) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": VERSION,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "state": state_dict,
        "world": world_dict,
        "player": {"x": float(player_pos[0]), "y": float(player_pos[1])},
        "last_tile": [int(last_tile[0]), int(last_tile[1])],
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_game(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def delete_save(path: Path) -> None:
    try:
        path.unlink()
    except Exception:
        pass


def generate_default_save_name(state) -> str:
    safe = "".join(
        c if c.isalnum() or c in "_-" else "_"
        for c in state.name
    ).strip("_") or "save"
    return f"{safe}_age_{state.age}"
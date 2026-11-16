"""Per-user settings stored in ~/.2d_world_sim/user_settings.json."""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS_DIR = Path.home() / ".2d_world_sim"
SETTINGS_FILE = SETTINGS_DIR / "user_settings.json"

DEFAULTS = {
    "base_url": "https://api.avalai.ir/v1",
    "api_key": "",
    "model": "gpt-4o-mini",
    "temperature": 0.8,
    "max_tokens": 1500,
    "timeout": 30,
}


def load_user_settings() -> dict:
    data = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            stored = json.loads(SETTINGS_FILE.read_text("utf-8"))
            if isinstance(stored, dict):
                data.update(stored)
        except Exception:
            pass
    return data


def save_user_settings(data: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def has_api_key() -> bool:
    return bool(load_user_settings().get("api_key", "").strip())
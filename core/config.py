"""Load config with priority: user_settings > config.yaml > env > defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .user_settings import load_user_settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.8
    max_tokens: int = 2000
    timeout: int = 60


@dataclass
class GameConfig:
    language: str = "en"
    save_dir: str = "saves"
    max_history: int = 20
    max_rooms: int = 12


@dataclass
class Map2DConfig:
    tile_size: int = 32
    fps: int = 60


@dataclass
class AppConfig:
    llm: LLMConfig
    game: GameConfig
    map2d: Map2DConfig


def _env_api_key(raw: dict) -> str:
    env_name = raw.get("api_key_env", "GEMINI_API_KEY")
    return os.getenv(env_name, "").strip()


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    cfg_path = PROJECT_ROOT / path
    raw: dict[str, Any] = {}
    if cfg_path.exists():
        try:
            raw = yaml.safe_load(cfg_path.read_text("utf-8")) or {}
        except Exception:
            raw = {}

    llm_raw = raw.get("llm", {})
    game_raw = raw.get("game", {})
    map_raw = raw.get("map2d", {})

    user = load_user_settings()
    user_key = (user.get("api_key") or "").strip()

    if user_key:
        llm = LLMConfig(
            base_url=user.get("base_url", "https://api.avalai.ir/v1"),
            api_key=user_key,
            model=user.get("model", "gpt-4o-mini"),
            temperature=float(user.get("temperature", 0.8)),
            max_tokens=int(user.get("max_tokens", 1500)),
            timeout=int(user.get("timeout", 30)),
        )
    else:
        llm = LLMConfig(
            base_url=llm_raw.get(
                "base_url",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            api_key=_env_api_key(llm_raw),
            model=llm_raw.get("model", "gemini-2.0-flash"),
            temperature=float(llm_raw.get("temperature", 0.8)),
            max_tokens=int(llm_raw.get("max_tokens", 2000)),
            timeout=int(llm_raw.get("timeout", 60)),
        )

    game = GameConfig(
        language=game_raw.get("language", "en"),
        save_dir=game_raw.get("save_dir", "saves"),
        max_history=int(game_raw.get("max_history", 20)),
        max_rooms=int(game_raw.get("max_rooms", 12)),
    )

    map2d = Map2DConfig(
        tile_size=int(map_raw.get("tile_size", 32)),
        fps=int(map_raw.get("fps", 60)),
    )

    return AppConfig(llm=llm, game=game, map2d=map2d)
"""Load config.yaml + .env into dataclasses."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

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


def _resolve_api_key(raw: dict) -> str:
    env_name = raw.get("api_key_env", "GEMINI_API_KEY")
    key = os.getenv(env_name, "").strip()
    if not key:
        raise ValueError(
            f"API key not found. Set '{env_name}' in your .env file."
        )
    return key


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    cfg_path = PROJECT_ROOT / path
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    with open(cfg_path, encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    llm_raw = raw.get("llm", {})
    game_raw = raw.get("game", {})
    map_raw = raw.get("map2d", {})

    return AppConfig(
        llm=LLMConfig(
            base_url=llm_raw.get("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/"),
            api_key=_resolve_api_key(llm_raw),
            model=llm_raw.get("model", "gemini-3.8-flash"),
            temperature=llm_raw.get("temperature", 0.8),
            max_tokens=llm_raw.get("max_tokens", 2000),
            timeout=llm_raw.get("timeout", 60),
        ),
        game=GameConfig(
            language=game_raw.get("language", "en"),
            save_dir=game_raw.get("save_dir", "saves"),
            max_history=game_raw.get("max_history", 20),
            max_rooms=game_raw.get("max_rooms", 12),
        ),
        map2d=Map2DConfig(
            tile_size=map_raw.get("tile_size", 32),
            fps=map_raw.get("fps", 60),
        ),
    )
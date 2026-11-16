"""Character state: age, health, money, history, save/load."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

MAX_AGE_PER_TURN = 5


@dataclass
class GameState:
    # Identity
    name: str = "Unnamed"
    gender: str = "unknown"
    country: str = ""
    city: str = ""
    family_wealth: str = "unknown"
    family_type: str = "unknown"
    # Stats
    age: int = 3
    health: int = 100
    money: float = 0.0
    job: str = "child"
    # Meta
    alive: bool = True
    turn: int = 0
    history: list[str] = field(default_factory=list)

    def add_event(self, summary: str, max_history: int = 20):
        self.history.append(summary)
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]

    def apply_delta(self, delta: dict):
        if not delta:
            return
        summary = delta.pop("summary", None)

        for key, value in delta.items():
            if not hasattr(self, key):
                continue
            current = getattr(self, key)

            if key == "age":
                try:
                    value = max(0, min(int(value), MAX_AGE_PER_TURN))
                except (TypeError, ValueError):
                    continue
                setattr(self, key, current + value)
            elif isinstance(current, (int, float)) and isinstance(value, (int, float)):
                setattr(self, key, current + value)
            elif isinstance(current, str) and isinstance(value, str):
                setattr(self, key, value)

        self.health = max(0, min(100, self.health))
        self.money = round(self.money, 2)
        if self.health <= 0:
            self.alive = False
        if summary:
            self.add_event(str(summary)[:120])
        self.turn += 1

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
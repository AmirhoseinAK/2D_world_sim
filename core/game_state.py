"""Character state: age, health, history, aging + mortality, save/load."""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Sanity bound only — not a gameplay cap
_AGE_DELTA_SANITY = 100


@dataclass
class GameState:
    name: str = "Unnamed"
    gender: str = "unknown"
    country: str = ""
    city: str = ""
    family_wealth: str = "unknown"
    family_type: str = "unknown"
    sprite: str = "male_01"

    age: int = 3
    health: int = 100
    money: float = 0.0
    job: str = "child"

    alive: bool = True
    turn: int = 0
    history: list[str] = field(default_factory=list)

    def add_event(self, summary: str, max_history: int = 20):
        self.history.append(summary)
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]

    def apply_delta(self, delta: dict):
        if not delta:
            self.turn += 1
            return

        summary = delta.pop("summary", None)

        # Extract age first; aging is processed year-by-year
        age_delta = 0
        if "age" in delta:
            try:
                age_delta = int(delta.pop("age"))
            except (TypeError, ValueError):
                age_delta = 0
            age_delta = max(0, min(age_delta, _AGE_DELTA_SANITY))

        # Apply non-age deltas
        for key, value in delta.items():
            if not hasattr(self, key):
                continue
            current = getattr(self, key)
            if isinstance(current, (int, float)) and isinstance(value, (int, float)):
                setattr(self, key, current + value)
            elif isinstance(current, str) and isinstance(value, str):
                setattr(self, key, value)

        self.health = max(0, min(100, self.health))
        if self.health <= 0:
            self.alive = False

        # Aging: one mortality roll per year
        for _ in range(age_delta):
            if not self.alive:
                break
            self.age += 1
            self._aging_tick()

        self.money = round(self.money, 2)

        # Update job label based on age
        if self.age < 6:
            self.job = "child"
        elif self.age < 18:
            self.job = "student"
        elif self.job == "child" or self.job == "student":
            self.job = "adult"

        if summary:
            self.add_event(str(summary)[:120])

        self.turn += 1

    def _aging_tick(self):
        """One year of aging: health decay + mortality roll."""

        # --- health decay (accelerating past 30) ---
        if self.age > 30:
            decay = 0.1 + (self.age - 30) * 0.03
            self.health -= decay
            self.health = max(0, min(100, self.health))

        if self.health <= 0:
            self.alive = False
            self.health = 0
            self.add_event(f"Died at age {self.age}.")
            return

        # --- mortality roll (Gompertz-Makeham + health multiplier) ---
        base = 0.0001                                    # accidents (never zero)
        age_term = 0.00004 * math.exp(0.085 * self.age)  # exponential with age
        hazard = base + age_term

        health_mult = (100.0 / max(self.health, 1.0)) ** 1.2
        death_chance = min(0.99, hazard * health_mult)

        if random.random() < death_chance:
            self.alive = False
            self.health = 0
            self.add_event(f"Died at age {self.age}.")

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
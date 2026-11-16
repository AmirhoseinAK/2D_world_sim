"""Random starting character generation."""
from __future__ import annotations

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

WEALTH_LEVELS = [
    ("poor", 30),
    ("lower-middle", 25),
    ("middle", 25),
    ("upper-middle", 15),
    ("rich", 5),
]

FAMILY_TYPES = [
    ("both parents", 50),
    ("single mother", 20),
    ("single father", 5),
    ("raised by grandparents", 10),
    ("orphanage", 5),
    ("adoptive parents", 10),
]


def _weighted_choice(options):
    choices, weights = zip(*options)
    return random.choices(choices, weights=weights, k=1)[0]


def load_country_names():
    data = json.loads((PROJECT_ROOT / "data" / "countries.json").read_text("utf-8"))
    return [c["name"] for c in data["countries"]]


def generate_character():
    return {
        "country": random.choice(load_country_names()),
        "gender": random.choice(["male", "female"]),
        "family_wealth": _weighted_choice(WEALTH_LEVELS),
        "family_type": _weighted_choice(FAMILY_TYPES),
    }
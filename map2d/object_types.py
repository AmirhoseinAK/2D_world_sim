"""Allowed object types (LLM must pick from this list)."""

OBJECT_TYPES = {
    "table":     (160, 100, 60),
    "chair":     (120, 90, 70),
    "bed":       (200, 200, 220),
    "counter":   (140, 90, 50),
    "shelf":     (180, 140, 90),
    "plant":     (60, 140, 60),
    "tree":      (50, 120, 50),
    "bench":     (160, 140, 100),
    "desk":      (140, 100, 70),
    "lamp":      (240, 220, 120),
    "rug":       (180, 60, 60),
    "barrel":    (120, 80, 40),
    "crate":     (150, 120, 80),
    "sofa":      (100, 120, 160),
    "bookshelf": (140, 100, 60),
}

ALLOWED_OBJECT_TYPES = list(OBJECT_TYPES.keys())
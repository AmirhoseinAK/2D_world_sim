"""Validate and normalize a room spec from the LLM."""
from __future__ import annotations

from .object_types import OBJECT_TYPES
from .npc import validate_npcs, default_npc_for_room

ROOM_W, ROOM_H = 15, 10
DEFAULT_FLOOR = (210, 200, 190)
DEFAULT_WALL = (60, 60, 70)
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def door_tile_for_side(side, w=ROOM_W, h=ROOM_H):
    if side == "north": return (w // 2, 0)
    if side == "south": return (w // 2, h - 1)
    if side == "west":  return (0, h // 2)
    if side == "east":  return (w - 1, h // 2)
    return (w // 2, h - 1)


def validate_room_spec(spec, door_side):
    w, h = ROOM_W, ROOM_H
    floor = _color(spec.get("floor_color"), DEFAULT_FLOOR)
    wall = _color(spec.get("wall_color"), DEFAULT_WALL)

    spawn = spec.get("spawn", [w // 2, h // 2])
    try:
        sx, sy = int(spawn[0]), int(spawn[1])
    except (TypeError, ValueError, IndexError):
        sx, sy = w // 2, h // 2
    sx = max(1, min(sx, w - 2))
    sy = max(1, min(sy, h - 2))

    door_tile = door_tile_for_side(door_side, w, h)

    occupied = {(sx, sy), door_tile}
    if door_side == "north":
        for dy in range(1, 4):
            for dx in range(-1, 2):
                x = (w // 2) + dx
                if 1 <= x <= w - 2:
                    occupied.add((x, dy))
    elif door_side == "south":
        for dy in range(1, 4):
            for dx in range(-1, 2):
                x = (w // 2) + dx
                if 1 <= x <= w - 2:
                    occupied.add((x, h - 1 - dy))
    elif door_side == "west":
        for dx in range(1, 4):
            for dy in range(-1, 2):
                y = (h // 2) + dy
                if 1 <= y <= h - 2:
                    occupied.add((dx, y))
    elif door_side == "east":
        for dx in range(1, 4):
            for dy in range(-1, 2):
                y = (h // 2) + dy
                if 1 <= y <= h - 2:
                    occupied.add((w - 1 - dx, y))

    objects = []
    for obj in spec.get("objects", []):
        if not isinstance(obj, dict):
            continue
        otype = obj.get("type", "")
        if otype not in OBJECT_TYPES:
            continue
        try:
            ox, oy = int(obj.get("x")), int(obj.get("y"))
        except (TypeError, ValueError):
            continue
        ox = max(1, min(ox, w - 2))
        oy = max(1, min(oy, h - 2))
        if (ox, oy) in occupied:
            continue
        occupied.add((ox, oy))
        objects.append({
            "pos": (ox, oy),
            "type": otype,
            "color": OBJECT_TYPES[otype],
        })

    # NPCs: use LLM's list, clamp positions, fall back to a default if empty
    npcs = validate_npcs(spec.get("npcs", []), w, h)
    for npc in npcs:
        occupied.add(npc["pos"])
    if not npcs:
        npcs = default_npc_for_room(
            str(spec.get("label", "Room")), w, h, occupied
        )

    return {
        "size": (w, h),
        "floor_color": floor,
        "wall_color": wall,
        "spawn": (sx, sy),
        "door_side": door_side,
        "door_tile": door_tile,
        "objects": objects,
        "npcs": npcs,
        "label": str(spec.get("label", "Room"))[:40],
    }


def _color(c, default):
    if isinstance(c, (list, tuple)) and len(c) == 3:
        try:
            return tuple(max(0, min(255, int(v))) for v in c)
        except (TypeError, ValueError):
            pass
    return default


def fallback_room_spec(label, door_side):
    return validate_room_spec(
        {
            "floor_color": [200, 200, 200],
            "wall_color": [60, 60, 70],
            "spawn": [7, 5],
            "objects": [
                {"type": "chair", "x": 3, "y": 3},
                {"type": "plant", "x": 11, "y": 3},
            ],
            "npcs": [],
            "label": label,
        },
        door_side,
    )
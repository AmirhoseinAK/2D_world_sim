"""Build a playable room dict from a validated spec."""
from __future__ import annotations


def build_room(spec, room_id, depth):
    w, h = spec["size"]
    walls = set()
    for x in range(w):
        walls.add((x, 0))
        walls.add((x, h - 1))
    for y in range(h):
        walls.add((0, y))
        walls.add((w - 1, y))

    door_tile = spec["door_tile"]
    walls.discard(door_tile)

    parsed_doors = {
        door_tile: {
            "target": None,
            "spawn_at": None,
            "label": spec["label"],
        }
    }

    objects = [
        {"pos": o["pos"], "color": o["color"]} for o in spec["objects"]
    ]

    return {
        "id": room_id,
        "size": (w, h),
        "floor_color": spec["floor_color"],
        "wall_color": spec["wall_color"],
        "walls": walls,
        "parsed_doors": parsed_doors,
        "objects": objects,
        "npcs": list(spec.get("npcs", [])),
        "player_spawn": spec["spawn"],
        "label": spec["label"],
        "depth": depth,
        "is_dynamic": True,
    }
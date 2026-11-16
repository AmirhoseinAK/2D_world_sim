"""Room graph with tree depth: street(0) -> building(1) -> room(2)."""
from __future__ import annotations

from copy import deepcopy

from .rooms import ROOMS
from .room_spec import validate_room_spec, fallback_room_spec
from .room_builder import build_room


OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}
DEFAULT_FLOOR = (225, 225, 228)
DEFAULT_WALL = (48, 48, 55)
MAX_DEPTH = 2


class World:
    def __init__(self, start_room: str = "hospital_lobby"):
        self._templates = ROOMS
        self.rooms: dict[str, dict] = {}
        self.current_id: str = start_room
        self._dynamic_counter = 0
        self.last_message = ""
        self.last_message_color = (240, 240, 240)
        self.enter_room(start_room)

    @property
    def current(self) -> dict:
        return self.rooms[self.current_id]

    def current_depth(self) -> int:
        return self.current.get("depth", 0)

    def current_label(self) -> str:
        return self.current.get("label", self.current_id.replace("_", " ").title())

    def can_add_door(self) -> bool:
        return self.current_depth() < MAX_DEPTH

    def enter_room(self, room_id: str) -> bool:
        if room_id in self.rooms:
            self.current_id = room_id
            return True
        if room_id in self._templates:
            self.rooms[room_id] = self._build_from_template(room_id)
            self.current_id = room_id
            return True
        return False

    def door_at(self, tile):
        return self.current["parsed_doors"].get(tile)

    def occupied_directions(self):
        return sorted({
            self._direction_of(pos, self.current)
            for pos in self.current["parsed_doors"]
        })

    def free_directions(self):
        return sorted(set(OPPOSITE.keys()) - set(self.occupied_directions()))

    def add_door(self, direction: str, room_spec: dict, label: str, entry_narrative: str = ""):
        if not self.can_add_door():
            return None, "You can't go any deeper from here. Go back first."
        if direction not in OPPOSITE:
            return None, "Invalid direction."
        pos = self._find_free_wall(self.current_id, direction)
        if pos is None:
            return None, "No space for a new door there."

        opposite = OPPOSITE[direction]
        room_id = f"dynamic_{self._dynamic_counter}"
        self._dynamic_counter += 1
        new_depth = self.current_depth() + 1

        try:
            validated = validate_room_spec(room_spec or {}, opposite)
        except Exception:
            validated = fallback_room_spec(label, opposite)

        room = build_room(validated, room_id, new_depth)

        ret_tile = validated["door_tile"]
        spawn_in_new = self._inside_of(ret_tile, room)
        room["player_spawn"] = spawn_in_new

        self.rooms[room_id] = room

        self.current["walls"].discard(pos)
        self.current["parsed_doors"][pos] = {
            "target": room_id,
            "spawn_at": spawn_in_new,
            "label": label,
            "entry_narrative": entry_narrative or "",
            "entry_narrated": False,
        }

        room["parsed_doors"][ret_tile] = {
            "target": self.current_id,
            "spawn_at": pos,
            "label": f"Back to {self.current_label()}",
            "entry_narrative": "",
            "entry_narrated": True,
        }

        return pos, None

    def _build_from_template(self, room_id: str) -> dict:
        template = self._templates[room_id]
        room = deepcopy(template)
        walls = set()
        doors = {}
        for y, row in enumerate(room["map"]):
            for x, ch in enumerate(row):
                if ch == "W":
                    walls.add((x, y))
                elif ch == "D":
                    doors[(x, y)] = dict(room["doors"].get((x, y), {}))
        room["walls"] = walls
        room["parsed_doors"] = doors
        room["size"] = (len(template["map"][0]), len(template["map"]))
        room.setdefault("floor_color", DEFAULT_FLOOR)
        room.setdefault("wall_color", DEFAULT_WALL)
        room["player_spawn"] = template["player_spawn"]
        room.setdefault("npcs", [])
        room.setdefault("depth", 0)
        room.setdefault("label", room_id.replace("_", " ").title())
        return room

    @staticmethod
    def _direction_of(pos, room):
        x, y = pos
        w, h = room.get("size", (15, 10))
        if y == 0: return "north"
        if y == h - 1: return "south"
        if x == 0: return "west"
        if x == w - 1: return "east"
        return "?"

    @staticmethod
    def _inside_of(pos, room):
        w, h = room.get("size", (15, 10))
        x, y = pos
        if y == 0: return (x, 1)
        if y == h - 1: return (x, h - 2)
        if x == 0: return (1, y)
        if x == w - 1: return (w - 2, y)
        return pos

    def _find_free_wall(self, room_id, direction):
        room = self.rooms.get(room_id)
        if room is None:
            return None
        w, h = room.get("size", (15, 10))

        if direction == "north":
            candidates = [(x, 0) for x in range(1, w - 1)]
            delta = (0, 1)
        elif direction == "south":
            candidates = [(x, h - 1) for x in range(1, w - 1)]
            delta = (0, -1)
        elif direction == "west":
            candidates = [(0, y) for y in range(1, h - 1)]
            delta = (1, 0)
        elif direction == "east":
            candidates = [(w - 1, y) for y in range(1, h - 1)]
            delta = (-1, 0)
        else:
            return None

        if direction in ("north", "south"):
            cx = w // 2
            candidates.sort(key=lambda p: abs(p[0] - cx))
        else:
            cy = h // 2
            candidates.sort(key=lambda p: abs(p[1] - cy))

        blocked = room["walls"] | {o["pos"] for o in room["objects"]}
        door_tiles = set(room["parsed_doors"].keys())

        for pos in candidates:
            if pos not in room["walls"]:
                continue
            if pos in door_tiles:
                continue
            ix, iy = pos[0] + delta[0], pos[1] + delta[1]
            if (ix, iy) in blocked:
                continue
            if (ix, iy) in door_tiles:
                continue
            return pos
        return None
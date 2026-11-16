"""Diagnostic: does the NPC pipeline work offline?"""
from map2d.room_spec import validate_room_spec
from map2d.room_builder import build_room

print("=" * 60)
print("TEST 1 — spec WITH npcs (simulating a good LLM response)")
print("=" * 60)
spec = {
    "label": "Bella's Restaurant",
    "floor_color": [210, 180, 140],
    "wall_color": [80, 50, 30],
    "spawn": [7, 7],
    "objects": [
        {"type": "table", "x": 4, "y": 3},
        {"type": "chair", "x": 4, "y": 4},
    ],
    "npcs": [
        {"name": "Bella", "role": "cook", "pos": [11, 6],
         "color": [220, 180, 140], "personality": "warm"}
    ],
}
validated = validate_room_spec(spec, "west")
print(f"  validated['npcs'] = {validated.get('npcs')}")
room = build_room(validated, "test1", 1)
print(f"  room['npcs']      = {room.get('npcs')}")
print()

print("=" * 60)
print("TEST 2 — spec WITHOUT npcs, label='Bella's Restaurant'")
print("=" * 60)
spec2 = {
    "label": "Bella's Restaurant",
    "floor_color": [210, 180, 140],
    "wall_color": [80, 50, 30],
    "spawn": [7, 7],
    "objects": [],
    "npcs": [],
}
validated2 = validate_room_spec(spec2, "west")
print(f"  validated['npcs'] = {validated2.get('npcs')}")
room2 = build_room(validated2, "test2", 1)
print(f"  room['npcs']      = {room2.get('npcs')}")
print()

print("=" * 60)
print("TEST 3 — spec WITHOUT npcs, label='Food Place' (generic)")
print("=" * 60)
spec3 = {
    "label": "Food Place",
    "floor_color": [200, 180, 150],
    "wall_color": [60, 60, 60],
    "spawn": [7, 7],
    "objects": [],
    "npcs": [],
}
validated3 = validate_room_spec(spec3, "west")
print(f"  validated['npcs'] = {validated3.get('npcs')}")
print()

print("=" * 60)
print("VERDICT")
print("=" * 60)
ok1 = bool(room.get("npcs"))
ok2 = bool(room2.get("npcs"))
ok3 = bool(validated3.get("npcs"))
print(f"  Test 1 (LLM gave npcs):     {'PASS' if ok1 else 'FAIL'}")
print(f"  Test 2 (keyword fallback):  {'PASS' if ok2 else 'FAIL'}")
print(f"  Test 3 (generic label):     {'PASS' if ok3 else 'FAIL'}")
print()
if ok1 and ok2:
    print("Pipeline is OK. NPC exists in the room dict.")
    print("=> Problem is in game.py / renderer.py (drawing or calling).")
elif not ok1 or not ok2:
    print("Pipeline is BROKEN. npcs are lost in validate/build.")
    print("=> Problem is in npc.py or room_spec.py or room_builder.py.")
"""LLM prompts: birth, unified turn, entry, NPC dialogue."""
from __future__ import annotations

from map2d.object_types import ALLOWED_OBJECT_TYPES


def build_birth_prompt(state) -> str:
    return f"""The player is born. Respond with JSON only, nothing else.

STARTING FACTS:
- Country: {state.country}
- Gender: {state.gender}
- Family wealth: {state.family_wealth}
- Family type: {state.family_type}

Return exactly this JSON shape:
{{
  "name": "<a single first name appropriate for {state.country} and {state.gender}>",
  "city": "<a plausible city in {state.country}>",
  "narrative": "<3 short sentences in 2nd person, present tense, describing birth sensations only. End with: Three years pass.>"
}}
"""


def build_turn_prompt(
    state,
    room_label: str,
    depth: int,
    objects: list[dict],
    occupied: list[str],
    free: list[str],
    remaining: int,
    player_text: str,
) -> str:
    allowed = ", ".join(ALLOWED_OBJECT_TYPES)
    obj_desc = ", ".join(o.get("type", "?") for o in objects) if objects else "nothing"
    free_str = free if free else ["none"]

    if depth == 0:
        depth_rule = (
            "You are on a STREET (depth 0).\n"
            "When the player mentions ANY of these, you MUST build it:\n"
            "  restaurant, cafe, bakery, fast food -> build a restaurant/cafe\n"
            "  shop, store, market, grocery -> build a shop\n"
            "  school, library, university -> build a school\n"
            "  house, home, apartment -> build a house\n"
            "  park, garden -> build a park\n"
            "  office, workplace -> build an office\n"
            "  hospital, doctor -> build a hospital entrance\n"
            "NEVER reject with phrases like 'you need a place' — the player\n"
            "just told you the place. Build it."
        )
    elif depth == 1:
        depth_rule = (
            "You are INSIDE a building (depth 1).\n"
            "When the player mentions ANY of these, build it (it's a sub-room):\n"
            "  bathroom, restroom, toilet -> build a bathroom\n"
            "  kitchen, cook -> build a kitchen\n"
            "  office, study -> build a small office\n"
            "  bedroom, sleep -> build a bedroom\n"
            "If the player asks for a DIFFERENT BUILDING (hospital, shop,\n"
            "restaurant) from inside a building, reject with exactly:\n"
            "\"You need to go back outside first.\"\n"
            "Do NOT reject room requests. Only reject cross-building requests."
        )
    else:
        depth_rule = (
            "You are at a DEAD END. You cannot add any new door.\n"
            "Always reject with: \"This is a dead end. Go back first.\""
        )

    return f"""You classify player intent and (if go) design a room. Output JSON only.

CURRENT:
- Character: {state.name} ({state.gender}, {state.age}y)
- Location: "{room_label}" (depth {depth}) — objects: {obj_desc}
- Free door directions: {free_str}
- Occupied: {occupied or ['none']}
- Rooms remaining: {remaining}

DEPTH RULE:
{depth_rule}

CLASSIFY the player intent, then output EXACTLY ONE of the three shapes.

===== SHAPE A: "go" (player wants to go somewhere new) =====
{{
  "intent": "go",
  "direction": "north|south|east|west",
  "label": "<short 2-4 word name>",
  "message": "<one sentence, max 15 words>",
  "entry_narrative": "<2-3 sentences, 2nd person 'you', sensory details>",
  "room_spec": {{
    "floor_color": [r, g, b],
    "wall_color": [r, g, b],
    "objects": [{{"type": "<allowed>", "x": int, "y": int}}],
    "npcs": [
      {{
        "name": "<first name>",
        "role": "<cook, waiter, nurse, stranger, etc.>",
        "pos": [x, y],
        "color": [r, g, b],
        "personality": "<one short line, max 15 words>"
      }}
    ]
  }},
  "deltas": {{"age": 0, "summary": "<short third-person>"}}
}}

===== SHAPE B: "act" (something happens in current room) =====
{{
  "intent": "act",
  "narrative": "<2-4 sentences, 2nd person 'you', present tense>",
  "deltas": {{
    "age": 0 or 1,
    "health": <int -5..+5>,
    "money": <int -20..+20>,
    "summary": "<short third-person>"
  }}
}}

===== SHAPE C: "reject" (only for unclear/implausible) =====
{{
  "intent": "reject",
  "message": "<short reason, max 15 words>"
}}

ALLOWED OBJECT TYPES: {allowed}
ROOM GRID: 15 wide x 10 tall. Coordinates x in [1,13], y in [1,8].

NPC RULES:
- A room may have 0 to 3 NPCs. Add 1-2 for lively places.
  * restaurant/cafe -> a waiter, a cook, or a customer
  * shop -> a shopkeeper
  * hospital/ward -> a nurse, a doctor
  * school -> a teacher, a student
  * park -> a stranger, a child
  * house -> a family member
- NPC "color" should suit their role:
  nurse (240,240,250), doctor (200,220,240), cook (220,180,140),
  shopkeeper (220,200,150), stranger (180,180,180), child (240,220,180).
- NPC "personality" is ONE short line, e.g. "tired but kind".
- NPC "pos" must be free (not on wall or object).

===== FEW-SHOT EXAMPLES =====

Player at depth 0 (street) says: "I want to eat at a restaurant"
{{"intent":"go","direction":"east","label":"Bella's Restaurant","message":"A warm door opens to the east.","entry_narrative":"You step inside. The smell of garlic and fresh bread greets you. Soft light warms the air.","room_spec":{{"floor_color":[210,180,140],"wall_color":[80,50,30],"objects":[{{"type":"table","x":4,"y":3}},{{"type":"chair","x":4,"y":4}},{{"type":"table","x":8,"y":3}},{{"type":"chair","x":8,"y":4}},{{"type":"counter","x":11,"y":5}}],"npcs":[{{"name":"Bella","role":"cook","pos":[11,6],"color":[220,180,140],"personality":"warm and loud, always busy"}}]}},"deltas":{{"age":0,"summary":"Found a restaurant on the street."}}}}

Player at depth 0 (street) says: "I want to buy something"
{{"intent":"go","direction":"south","label":"Small Shop","message":"A door slides open to the south.","entry_narrative":"You enter a cluttered shop. Shelves line the walls, and a small bell chimes as you step in.","room_spec":{{"floor_color":[220,220,200],"wall_color":[60,60,60],"objects":[{{"type":"shelf","x":3,"y":2}},{{"type":"shelf","x":5,"y":2}},{{"type":"counter","x":7,"y":7}},{{"type":"crate","x":11,"y":3}}],"npcs":[{{"name":"Omar","role":"shopkeeper","pos":[7,6],"color":[220,200,150],"personality":"quiet, watches customers closely"}}]}},"deltas":{{"age":0,"summary":"Entered a small shop."}}}}

Player at depth 1 (restaurant) says: "I want to use the bathroom"
{{"intent":"go","direction":"north","label":"Bathroom","message":"A narrow door opens to the north.","entry_narrative":"You step into a small tiled room. The air is cool and smells faintly of soap.","room_spec":{{"floor_color":[200,220,220],"wall_color":[150,150,150],"objects":[],"npcs":[]}},"deltas":{{"age":0,"summary":"Used the bathroom."}}}}

Player at depth 1 (restaurant) says: "I want to see the hospital"
{{"intent":"reject","message":"You need to go back outside first."}}

Player at depth 0 (street) says: "I cry"
{{"intent":"act","narrative":"Your tears fall on the pavement. A passerby glances at you but keeps walking. The cold wind stings your cheeks.","deltas":{{"age":0,"health":-1,"summary":"Cried alone on the street."}}}}

Player at depth 0 (street) says: "asdfghjkl"
{{"intent":"reject","message":"You can't do that."}}

===== END EXAMPLES =====

Now respond to the actual player.

PLAYER INTENT:
"{player_text}"

Output JSON only, no prose, no markdown fences.
"""


def build_entry_prompt(state, room_label: str) -> str:
    return f"""The player enters a room called "{room_label}" for the first time.
Age: {state.age}. Health: {state.health}.

Write ONE short sentence (max 15 words) in second person describing the first
impression. Focus on one sensory detail (sound, smell, light, temperature).

Output JSON only:
{{"entry": "<one sentence>"}}
"""


def build_npc_dialogue_prompt(state, npc, room_label, player_text: str) -> str:
    log_lines = []
    for entry in npc.get("conversation_log", [])[-6:]:
        speaker = npc["name"] if entry["role"] == "npc" else state.name
        log_lines.append(f"{speaker}: {entry['text']}")
    log_text = "\n".join(log_lines) if log_lines else "(this is your first conversation)"

    return f"""You are {npc['name']}, a {npc['role']} in {room_label}.

YOUR PERSONALITY: {npc.get('personality', 'an ordinary person')}

CONVERSATION SO FAR (most recent last):
{log_text}

PLAYER ({state.name}, age {state.age}, health {state.health}) says:
"{player_text}"

Respond in character. 1-3 sentences. Use *asterisks* for actions
(e.g. *smiles*, *looks away*). Do NOT narrate the player's actions.

Output JSON only:
{{
  "response": "<your words and actions as {npc['name']}>",
  "deltas": {{"health": 0, "money": 0, "summary": "<short third-person event>"}}
}}

If nothing changes, use empty deltas: "deltas": {{}}
"""
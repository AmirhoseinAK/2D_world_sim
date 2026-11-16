"""Main pygame loop with NPC support, threaded LLM calls, held-backspace."""
import sys
import textwrap

import pygame

from core.config import load_config
from core.llm_client import LLMClient
from core.game_state import GameState
from core.random_gen import generate_character
from .constants import (
    TILE, ROOM_W, ROOM_H, HUD_H, WINDOW_W, WINDOW_H, FPS,
    COLOR_HUD_BG, COLOR_HUD_TEXT, COLOR_HUD_DIM,
    COLOR_MSG_GOOD, COLOR_MSG_WARN,
)
from .player import Player
from .renderer import draw_room, draw_player, draw_npcs
from .world import World
from .intent_parser import parse_birth, parse_turn, parse_npc_dialogue
from .npc import nearest_npc, push_log
from .llm_task import LLMTask


INPUT_BOX_H = 30
INPUT_BOX_Y = WINDOW_H - INPUT_BOX_H - 8
INPUT_BOX_X = 8
INPUT_BOX_W = WINDOW_W - 16

# Delete-repeat tuning
BACKSPACE_INITIAL_DELAY = 0.35
BACKSPACE_REPEAT_INTERVAL = 0.03

P_BIRTH_LOADING = "birth_loading"
P_BIRTH_OVERLAY = "birth_overlay"
P_IDLE = "idle"
P_THINKING = "thinking"
P_ACT_OVERLAY = "act_overlay"
P_ENTRY_OVERLAY = "entry_overlay"
P_DEATH_OVERLAY = "death_overlay"
P_DIALOGUE = "dialogue"
P_DIALOGUE_THINKING = "dialogue_thinking"


def run(cfg=None):
    if cfg is None:
        cfg = load_config()
    llm = LLMClient(cfg.llm)

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("2D World Sim")
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("Arial", 15, bold=True)
    font_sm = pygame.font.SysFont("Arial", 13)
    font_input = pygame.font.SysFont("Consolas", 14)
    font_overlay = pygame.font.SysFont("Arial", 14)
    font_center = pygame.font.SysFont("Arial", 16, bold=True)

    profile = generate_character()
    state = GameState(
        country=profile["country"],
        gender=profile["gender"],
        family_wealth=profile["family_wealth"],
        family_type=profile["family_type"],
        age=3,
        job="child",
        money=0.0,
    )

    world = World(start_room="hospital_lobby")
    sx, sy = world.current["player_spawn"]
    player = Player(sx, sy)
    last_tile = player.center_tile()

    birth_task = LLMTask()
    turn_task = LLMTask()
    npc_task = LLMTask()
    birth_task.start(parse_birth, llm, state)

    phase = P_BIRTH_LOADING
    overlay_text = ""
    overlay_can_dismiss_at = 0.0
    transition_lock = 0.0
    LOCK_TIME = 0.30
    typing = False
    text_buffer = ""
    message = ""
    message_color = COLOR_HUD_TEXT
    max_rooms = cfg.game.max_rooms
    death_shown = False
    current_npc = None
    _pending_phase = [P_IDLE]
    _pending_overlay = [""]
    backspace_hold_started = None
    backspace_last_tick = 0.0
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        now = pygame.time.get_ticks() / 1000.0

        # ================= EVENTS =================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            # Clear backspace hold on release
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    backspace_hold_started = None
                continue

            if event.type != pygame.KEYDOWN:
                continue

            # ----- Overlays -----
            if phase in (P_BIRTH_OVERLAY, P_ACT_OVERLAY, P_ENTRY_OVERLAY, P_DEATH_OVERLAY):
                if now >= overlay_can_dismiss_at:
                    if phase == P_DEATH_OVERLAY:
                        running = False
                    else:
                        phase = P_IDLE
                        transition_lock = 0.2
                continue

            # ----- Birth loading -----
            if phase == P_BIRTH_LOADING:
                if event.key == pygame.K_ESCAPE:
                    state.name = "Alex"
                    state.city = state.country
                    overlay_text = (
                        f"You are born in {state.country}. Three years pass.\n\n"
                        "(Skipped.)\n\nPress any key to begin."
                    )
                    overlay_can_dismiss_at = now + 0.3
                    phase = P_BIRTH_OVERLAY
                continue

            # ----- Thinking -----
            if phase == P_THINKING:
                if event.key == pygame.K_ESCAPE:
                    message = "Please wait for the response..."
                    message_color = COLOR_MSG_WARN
                continue

            # ----- Dialogue input -----
            if phase == P_DIALOGUE:
                if event.key == pygame.K_ESCAPE:
                    current_npc = None
                    phase = P_IDLE
                    continue
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if text_buffer.strip() and current_npc is not None:
                        push_log(current_npc, "player", text_buffer.strip())
                        npc_task.start(
                            parse_npc_dialogue,
                            llm, state, current_npc,
                            world.current_label(),
                            text_buffer.strip(),
                        )
                        phase = P_DIALOGUE_THINKING
                        text_buffer = ""
                    continue
                if event.key == pygame.K_BACKSPACE:
                    text_buffer = text_buffer[:-1]
                    backspace_hold_started = now
                    backspace_last_tick = now
                    continue
                if event.unicode and event.unicode.isprintable():
                    if len(text_buffer) < 120:
                        text_buffer += event.unicode
                continue

            # ----- Dialogue thinking -----
            if phase == P_DIALOGUE_THINKING:
                if event.key == pygame.K_ESCAPE:
                    message = "Please wait..."
                    message_color = COLOR_MSG_WARN
                continue

            # ================= IDLE =================
            if event.key == pygame.K_ESCAPE:
                if typing:
                    typing = False
                    text_buffer = ""
                else:
                    running = False
                continue

            if event.key == pygame.K_e and not typing:
                near = nearest_npc(player, world.current.get("npcs", []))
                if near:
                    current_npc = near
                    text_buffer = ""
                    phase = P_DIALOGUE
                continue

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if not typing:
                    typing = True
                    text_buffer = ""
                elif text_buffer.strip():
                    remaining = max_rooms - len(world.rooms)
                    turn_task.start(
                        parse_turn,
                        llm, state,
                        world.current_label(),
                        world.current_depth(),
                        world.current["objects"],
                        world.occupied_directions(),
                        world.free_directions(),
                        remaining,
                        text_buffer.strip(),
                    )
                    phase = P_THINKING
                    typing = False
                    text_buffer = ""
                else:
                    typing = False
                    text_buffer = ""
                continue

            if typing and event.key == pygame.K_BACKSPACE:
                text_buffer = text_buffer[:-1]
                backspace_hold_started = now
                backspace_last_tick = now
                continue

            if typing and event.unicode and event.unicode.isprintable():
                if len(text_buffer) < 120:
                    text_buffer += event.unicode

        if not running:
            break

        # ================= BACKSPACE HOLD REPEAT =================
        if backspace_hold_started is not None:
            elapsed = now - backspace_hold_started
            if elapsed > BACKSPACE_INITIAL_DELAY:
                if now - backspace_last_tick >= BACKSPACE_REPEAT_INTERVAL:
                    if (phase == P_DIALOGUE) or (phase == P_IDLE and typing):
                        text_buffer = text_buffer[:-1]
                    backspace_last_tick = now

        # ================= TASKS =================
        birth_task.update()
        turn_task.update()
        npc_task.update()

        if phase == P_BIRTH_LOADING and birth_task.is_done():
            if birth_task.timed_out or birth_task.error:
                state.name = "Alex"
                state.city = state.country
                overlay_text = f"You are born in {state.country}. Three years pass."
            else:
                try:
                    name, city, narrative = birth_task.result
                    state.name = name
                    state.city = city
                    overlay_text = narrative
                except Exception:
                    state.name = "Alex"
                    state.city = state.country
                    overlay_text = f"You are born in {state.country}. Three years pass."
            overlay_text += "\n\nPress any key to begin."
            overlay_can_dismiss_at = now + 0.4
            phase = P_BIRTH_OVERLAY

        elif phase == P_THINKING and turn_task.is_done():
            _apply_turn_result(turn_task, world, state, cfg, _pending_phase, _pending_overlay)
            message = world.last_message
            message_color = world.last_message_color
            if _pending_phase[0] == P_ACT_OVERLAY:
                overlay_text = _pending_overlay[0]
                overlay_can_dismiss_at = now + 0.4
                phase = P_ACT_OVERLAY
            else:
                phase = P_IDLE

        elif phase == P_DIALOGUE_THINKING and npc_task.is_done():
            if npc_task.timed_out or npc_task.error:
                push_log(current_npc, "npc", "...")
                message = "The NPC stays silent."
                message_color = COLOR_MSG_WARN
            else:
                try:
                    response, deltas = npc_task.result
                    push_log(current_npc, "npc", response)
                    if deltas:
                        state.apply_delta(deltas)
                except Exception:
                    push_log(current_npc, "npc", "...")
            phase = P_DIALOGUE

        if not state.alive and not death_shown and phase == P_IDLE:
            death_shown = True
            overlay_text = (
                f"You have died at age {state.age}.\n\n"
                f"You lived in {state.city or state.country}.\n\n"
                "Press any key to exit."
            )
            overlay_can_dismiss_at = now + 0.4
            phase = P_DEATH_OVERLAY

        # ================= MOVEMENT =================
        transition_lock = max(0.0, transition_lock - dt)
        if phase == P_IDLE and not typing and state.alive:
            keys = pygame.key.get_pressed()
            dx = dy = 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
            if dx and dy:
                dx *= 0.70710678
                dy *= 0.70710678
            if transition_lock <= 0.0:
                blocked = (
                    world.current["walls"]
                    | {o["pos"] for o in world.current["objects"]}
                    | {n["pos"] for n in world.current.get("npcs", [])}
                )
                player.try_move(dx, dy, dt, blocked)

        # ================= DOOR =================
        if phase == P_IDLE and transition_lock <= 0.0 and state.alive:
            tile = player.center_tile()
            if tile != last_tile:
                door = world.door_at(tile)
                if door and door.get("target"):
                    if world.enter_room(door["target"]):
                        spawn = door["spawn_at"]
                        player.x = spawn[0] * TILE + TILE / 2.0
                        player.y = spawn[1] * TILE + TILE / 2.0
                        last_tile = player.center_tile()
                        transition_lock = LOCK_TIME
                        message = f"-> {world.current_label()}"
                        message_color = COLOR_MSG_GOOD
                        if door.get("entry_narrative") and not door.get("entry_narrated"):
                            door["entry_narrated"] = True
                            overlay_text = door["entry_narrative"]
                            overlay_can_dismiss_at = now + 0.4
                            phase = P_ENTRY_OVERLAY
                    else:
                        last_tile = tile
                else:
                    last_tile = tile

        # ================= DRAW =================
        if phase == P_BIRTH_LOADING:
            _draw_center_loading(screen, font_center, "Creating your life", birth_task.elapsed())
        elif phase in (P_DIALOGUE, P_DIALOGUE_THINKING):
            _draw_dialogue(
                screen, world, player, state, current_npc,
                font_big, font_sm, font_input, font_overlay,
                phase == P_DIALOGUE_THINKING, text_buffer,
                npc_task.elapsed() if phase == P_DIALOGUE_THINKING else 0.0,
            )
        else:
            near = nearest_npc(player, world.current.get("npcs", []))
            _draw_game(
                screen, world, player, state, font_big, font_sm, font_input,
                message, message_color, typing, text_buffer, near,
            )
            if phase == P_THINKING:
                _draw_center_thinking(screen, font_center, turn_task.elapsed())
            elif phase in (P_BIRTH_OVERLAY, P_ACT_OVERLAY, P_ENTRY_OVERLAY, P_DEATH_OVERLAY):
                _draw_text_overlay(screen, overlay_text, font_overlay)

        pygame.display.flip()

    return


def _apply_turn_result(task, world, state, cfg, pending_phase, pending_overlay):
    pending_phase[0] = P_IDLE
    pending_overlay[0] = ""

    if task.timed_out:
        world.last_message = "LLM timed out. Try again."
        world.last_message_color = COLOR_MSG_WARN
        return
    if task.error:
        world.last_message = f"LLM error: {str(task.error)[:60]}"
        world.last_message_color = COLOR_MSG_WARN
        return

    result = task.result
    if not isinstance(result, dict):
        world.last_message = "(no response)"
        world.last_message_color = COLOR_MSG_WARN
        return

    intent = result.get("intent", "reject")

    if intent == "go":
        remaining = cfg.game.max_rooms - len(world.rooms)
        if remaining <= 0:
            world.last_message = "You've explored enough for now."
            world.last_message_color = COLOR_MSG_WARN
            return
        pos, err = world.add_door(
            direction=result["direction"],
            room_spec=result.get("room_spec", {}),
            label=result["label"],
            entry_narrative=result.get("entry_narrative", ""),
        )
        if pos:
            world.last_message = result.get("message") or f"New door: {result['label']}"
            world.last_message_color = COLOR_MSG_GOOD
        else:
            world.last_message = err or "No space for a new door."
            world.last_message_color = COLOR_MSG_WARN
        if result.get("deltas"):
            state.apply_delta(result["deltas"])
        return

    if intent == "act":
        if result.get("deltas"):
            state.apply_delta(result["deltas"])
            if state.history:
                world.last_message = state.history[-1]
            else:
                world.last_message = "You act."
        else:
            world.last_message = "You act."
        world.last_message_color = COLOR_MSG_GOOD
        pending_phase[0] = P_ACT_OVERLAY
        pending_overlay[0] = result.get("narrative") or "..."
        return

    world.last_message = result.get("message") or "You can't do that."
    world.last_message_color = COLOR_MSG_WARN


def _draw_game(screen, world, player, state, font_big, font_sm, font_input,
               message, message_color, typing, text_buffer, near_npc):
    screen.fill(COLOR_HUD_BG)
    draw_room(screen, world.current)
    draw_npcs(screen, world.current, player, highlight_npc=near_npc)
    draw_player(screen, player)

    hud_y = ROOM_H * TILE
    pygame.draw.rect(screen, COLOR_HUD_BG, (0, hud_y, WINDOW_W, HUD_H))
    pygame.draw.line(screen, COLOR_MSG_GOOD, (0, hud_y), (WINDOW_W, hud_y), 2)

    stats = f"{state.name}, {state.age}y | HP:{state.health} | ${int(state.money)}"
    screen.blit(font_big.render(stats, True, COLOR_HUD_TEXT), (12, hud_y + 6))

    depth = world.current_depth()
    badge = {0: "[street]", 1: "[building]"}.get(depth, "[room]")
    loc = f"{world.current_label()} {badge} | job: {state.job}"
    screen.blit(font_sm.render(loc, True, COLOR_HUD_DIM), (12, hud_y + 26))

    if near_npc and not typing:
        hint = f"[E] Talk to {near_npc['name']} ({near_npc['role']})"
        screen.blit(font_sm.render(hint, True, (255, 230, 80)), (12, hud_y + 46))
    else:
        if message_color == COLOR_MSG_WARN:
            msg_surf = font_big.render(message[:60], True, message_color)
        else:
            msg_surf = font_sm.render(message[:72], True, message_color)
        screen.blit(msg_surf, (12, hud_y + 46))

    box_border = (60, 120, 200) if typing else (50, 50, 60)
    pygame.draw.rect(screen, (20, 20, 26),
                     (INPUT_BOX_X, INPUT_BOX_Y, INPUT_BOX_W, INPUT_BOX_H))
    pygame.draw.rect(screen, box_border,
                     (INPUT_BOX_X, INPUT_BOX_Y, INPUT_BOX_W, INPUT_BOX_H), 2)
    display = ("> " + text_buffer + "|") if typing else "> (press / or Enter)"
    screen.blit(font_input.render(display, True, COLOR_HUD_TEXT),
                (INPUT_BOX_X + 6, INPUT_BOX_Y + 7))


def _draw_dialogue(screen, world, player, state, npc,
                   font_big, font_sm, font_input, font_overlay,
                   thinking, text_buffer, elapsed):
    screen.fill(COLOR_HUD_BG)
    draw_room(screen, world.current)
    draw_npcs(screen, world.current, player, highlight_npc=npc)
    draw_player(screen, player)

    rect = pygame.Rect(20, 20, WINDOW_W - 40, ROOM_H * TILE - 40)
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    s.fill((10, 10, 20, 240))
    screen.blit(s, rect.topleft)
    pygame.draw.rect(screen, (255, 230, 80), rect, 2)

    header = f"{npc['name']} — {npc['role']}"
    screen.blit(font_big.render(header, True, (255, 230, 80)),
                (rect.x + 12, rect.y + 10))
    screen.blit(font_sm.render(npc.get("personality", ""), True, COLOR_HUD_DIM),
                (rect.x + 12, rect.y + 30))

    y = rect.y + 56
    for entry in npc.get("conversation_log", [])[-5:]:
        speaker = npc["name"] if entry["role"] == "npc" else state.name
        text = f"{speaker}: {entry['text']}"
        chars = max(30, (rect.w - 24) // 7)
        for line in textwrap.wrap(text, width=chars)[:2]:
            screen.blit(font_overlay.render(line, True, COLOR_HUD_TEXT),
                        (rect.x + 12, y))
            y += 18
        y += 2

    if thinking:
        dots = "." * (int(elapsed * 3) % 4)
        screen.blit(font_overlay.render(f"{npc['name']} is thinking{dots}",
                                        True, COLOR_MSG_GOOD),
                    (rect.x + 12, rect.y + rect.h - 70))
    else:
        screen.blit(font_overlay.render("(ESC to leave the conversation)",
                                        True, COLOR_HUD_DIM),
                    (rect.x + 12, rect.y + rect.h - 70))

    box_y = rect.y + rect.h - 42
    pygame.draw.rect(screen, (20, 20, 26),
                     (rect.x + 12, box_y, rect.w - 24, 30))
    pygame.draw.rect(screen, (255, 230, 80),
                     (rect.x + 12, box_y, rect.w - 24, 30), 2)
    display = ("> " + text_buffer + "|") if not thinking else "> ..."
    screen.blit(font_input.render(display, True, COLOR_HUD_TEXT),
                (rect.x + 18, box_y + 7))


def _draw_text_overlay(screen, text, font):
    rect = pygame.Rect(20, 20, WINDOW_W - 40, ROOM_H * TILE - 40)
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    s.fill((10, 10, 20, 240))
    screen.blit(s, rect.topleft)
    pygame.draw.rect(screen, COLOR_MSG_GOOD, rect, 2)
    chars = max(20, (rect.w - 24) // 7)
    lines = textwrap.wrap(text, width=chars) or [text]
    y = rect.y + 14
    for line in lines[:16]:
        screen.blit(font.render(line, True, COLOR_HUD_TEXT), (rect.x + 12, y))
        y += 19
    hint = font.render("(press any key to continue)", True, COLOR_HUD_DIM)
    screen.blit(hint, (rect.x + 12, rect.y + rect.h - 26))


def _draw_center_loading(screen, font, label, elapsed):
    screen.fill(COLOR_HUD_BG)
    dots = "." * (int(elapsed * 3) % 4)
    text = f"{label}{dots}  ({elapsed:.0f}s)"
    surf = font.render(text, True, COLOR_HUD_TEXT)
    screen.blit(surf, surf.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2)))
    sub = font.render("(this may take a few seconds)", True, COLOR_HUD_DIM)
    screen.blit(sub, sub.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 + 26)))


def _draw_center_thinking(screen, font, elapsed):
    dots = "." * (int(elapsed * 3) % 4)
    surf = font.render(f"Thinking{dots}", True, COLOR_MSG_GOOD)
    rect = surf.get_rect(center=(WINDOW_W // 2, ROOM_H * TILE // 2))
    bg = pygame.Surface((rect.w + 24, rect.h + 16), pygame.SRCALPHA)
    bg.fill((10, 10, 20, 220))
    screen.blit(bg, (rect.x - 12, rect.y - 8))
    screen.blit(surf, rect)
"""Main pygame loop for the 2D layer."""
import sys

import pygame

from core.config import load_config
from core.llm_client import LLMClient
from .constants import (
    TILE, ROOM_W, ROOM_H, HUD_H, WINDOW_W, WINDOW_H, FPS,
    COLOR_HUD_BG, COLOR_HUD_TEXT, COLOR_HUD_DIM,
    COLOR_MSG_GOOD, COLOR_MSG_WARN,
)
from .player import Player
from .renderer import draw_room, draw_player
from .world import World, MAX_DEPTH
from .intent_parser import parse_intent


INPUT_BOX_H = 30
INPUT_BOX_Y = WINDOW_H - INPUT_BOX_H - 8
INPUT_BOX_X = 8
INPUT_BOX_W = WINDOW_W - 16


def run():
    cfg = load_config()
    llm = LLMClient(cfg.llm)

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("2D World Sim")
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("Arial", 15, bold=True)
    font_sm = pygame.font.SysFont("Arial", 13)
    font_input = pygame.font.SysFont("Consolas", 14)

    world = World(start_room="hospital_lobby")
    sx, sy = world.current["player_spawn"]
    player = Player(sx, sy)
    last_tile = player.center_tile()

    message = "WASD walk | / or Enter to type | ESC quit"
    message_color = COLOR_HUD_TEXT
    transition_lock = 0.0
    LOCK_TIME = 0.30
    typing = False
    text_buffer = ""
    max_rooms = cfg.game.max_rooms

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if typing:
                        typing = False
                        text_buffer = ""
                    else:
                        running = False
                    continue

                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if not typing:
                        typing = True
                        text_buffer = ""
                    elif text_buffer.strip():
                        _show_thinking(screen, world, player, font_big, font_sm)
                        _submit_intent(
                            world=world, llm=llm,
                            text=text_buffer.strip(),
                            max_rooms=max_rooms,
                        )
                        message = world.last_message
                        message_color = world.last_message_color
                        typing = False
                        text_buffer = ""
                    else:
                        typing = False
                        text_buffer = ""
                    continue

                if typing and event.key == pygame.K_BACKSPACE:
                    text_buffer = text_buffer[:-1]
                    continue

                if typing and event.unicode and event.unicode.isprintable():
                    if len(text_buffer) < 120:
                        text_buffer += event.unicode

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if not typing:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
            if dx and dy:
                dx *= 0.70710678
                dy *= 0.70710678

        if transition_lock <= 0.0 and not typing:
            blocked = world.current["walls"] | {
                o["pos"] for o in world.current["objects"]
            }
            player.try_move(dx, dy, dt, blocked)

        transition_lock = max(0.0, transition_lock - dt)

        tile = player.center_tile()
        if transition_lock <= 0.0 and tile != last_tile:
            door = world.door_at(tile)
            if door:
                target = door.get("target")
                if target and world.enter_room(target):
                    spawn = door.get("spawn_at", (7, 5))
                    player.x = spawn[0] * TILE + TILE / 2.0
                    player.y = spawn[1] * TILE + TILE / 2.0
                    last_tile = player.center_tile()
                    message = f"-> {world.current_label()}"
                    message_color = COLOR_MSG_GOOD
                    transition_lock = LOCK_TIME
                else:
                    message = "This door leads nowhere yet."
                    message_color = COLOR_MSG_WARN
                    last_tile = tile
            else:
                last_tile = tile

        _draw_frame(
            screen, world, player, font_big, font_sm, font_input,
            message, message_color, typing, text_buffer,
        )
        pygame.display.flip()

    pygame.quit()
    sys.exit()


def _draw_frame(screen, world, player, font_big, font_sm, font_input,
                message, message_color, typing, text_buffer):
    screen.fill(COLOR_HUD_BG)
    draw_room(screen, world.current)
    draw_player(screen, player)

    hud_y = ROOM_H * TILE
    pygame.draw.rect(screen, COLOR_HUD_BG, (0, hud_y, WINDOW_W, HUD_H))
    pygame.draw.line(screen, COLOR_MSG_GOOD, (0, hud_y), (WINDOW_W, hud_y), 2)

    depth = world.current_depth()
    depth_marker = ""
    if depth == 0:
        depth_marker = " [street]"
    elif depth == 1:
        depth_marker = " [building]"
    else:
        depth_marker = " [room]"

    screen.blit(
        font_big.render(
            f"{world.current_label()}{depth_marker}",
            True, COLOR_HUD_TEXT,
        ),
        (12, hud_y + 6),
    )
    screen.blit(
        font_sm.render(message[:70], True, message_color),
        (12, hud_y + 26),
    )

    if not world.can_add_door():
        hint = "Dead end. Go back to explore further."
        hint_color = COLOR_MSG_WARN
    else:
        hint = "WASD walk | / or Enter to type | ESC quit"
        hint_color = COLOR_HUD_DIM
    screen.blit(
        font_sm.render(hint, True, hint_color),
        (12, hud_y + 44),
    )

    box_border = (60, 120, 200) if typing else (50, 50, 60)
    pygame.draw.rect(
        screen, (20, 20, 26),
        (INPUT_BOX_X, INPUT_BOX_Y, INPUT_BOX_W, INPUT_BOX_H),
    )
    pygame.draw.rect(
        screen, box_border,
        (INPUT_BOX_X, INPUT_BOX_Y, INPUT_BOX_W, INPUT_BOX_H), 2,
    )
    display = "> " + text_buffer + "|" if typing else "> (press / or Enter)"
    screen.blit(
        font_input.render(display, True, COLOR_HUD_TEXT),
        (INPUT_BOX_X + 6, INPUT_BOX_Y + 7),
    )


def _show_thinking(screen, world, player, font_big, font_sm):
    screen.fill(COLOR_HUD_BG)
    draw_room(screen, world.current)
    draw_player(screen, player)
    hud_y = ROOM_H * TILE
    pygame.draw.rect(screen, COLOR_HUD_BG, (0, hud_y, WINDOW_W, HUD_H))
    pygame.draw.line(screen, COLOR_MSG_GOOD, (0, hud_y), (WINDOW_W, hud_y), 2)
    screen.blit(
        font_big.render(world.current_label(), True, COLOR_HUD_TEXT),
        (12, hud_y + 6),
    )
    screen.blit(
        font_sm.render("Thinking...", True, COLOR_MSG_GOOD),
        (12, hud_y + 26),
    )
    pygame.display.flip()


def _submit_intent(world, llm, text, max_rooms):
    if not world.can_add_door():
        world.last_message = "This is a dead end. Go back first."
        world.last_message_color = COLOR_MSG_WARN
        return

    remaining = max_rooms - len(world.rooms)
    if remaining <= 0:
        world.last_message = "You've explored enough for now."
        world.last_message_color = COLOR_MSG_WARN
        return

    result = parse_intent(
        llm=llm,
        room_label=world.current_label(),
        depth=world.current_depth(),
        occupied=world.occupied_directions(),
        free=world.free_directions(),
        remaining=remaining,
        player_text=text,
    )

    if result["action"] == "add_door":
        pos, err = world.add_door(
            direction=result["direction"],
            room_spec=result.get("room_spec", {}),
            label=result["label"],
        )
        if pos:
            world.last_message = (
                result["message"] or f"New door: {result['label']}"
            )
            world.last_message_color = COLOR_MSG_GOOD
        else:
            world.last_message = err or "No space for a new door there."
            world.last_message_color = COLOR_MSG_WARN
    else:
        world.last_message = result["message"] or "You can't go there."
        world.last_message_color = COLOR_MSG_WARN
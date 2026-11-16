"""Draw rooms, walls, doors, objects, player (age-aware), NPCs."""
import pygame

from .constants import (
    TILE, ROOM_W, ROOM_H,
    COLOR_FLOOR, COLOR_WALL, COLOR_WALL_EDGE,
    COLOR_DOOR, COLOR_DOOR_GLOW,
    COLOR_PLAYER, COLOR_PLAYER_RING,
)
from .assets import get_char_frame


ANIM_FPS = 8.0


def _age_size(age: int) -> int:
    if age < 13:
        return 30    # child
    if age < 18:
        return 40    # teen
    if age < 60:
        return 48    # adult
    if age < 75:
        return 46    # middle-age
    if age < 90:
        return 42    # elder
    return 38        # ancient


def _age_gray_amount(age: int) -> int:
    """Alpha of the grayscale overlay (0 = no gray, 255 = fully gray)."""
    if age < 60:
        return 0
    if age < 75:
        return 55
    if age < 90:
        return 110
    return 170


def _apply_aging(sprite: pygame.Surface, age: int) -> pygame.Surface:
    alpha = _age_gray_amount(age)
    if alpha == 0:
        return sprite
    result = sprite.copy()
    gray = pygame.Surface(result.get_size(), pygame.SRCALPHA)
    try:
        pygame.transform.grayscale(result, gray)
    except Exception:
        return sprite
    gray.set_alpha(alpha)
    result.blit(gray, (0, 0))
    return result


def draw_room(screen, room):
    w, h = room.get("size", (ROOM_W, ROOM_H))
    floor = room.get("floor_color", COLOR_FLOOR)
    wall = room.get("wall_color", COLOR_WALL)

    pygame.draw.rect(screen, floor, (0, 0, w * TILE, h * TILE))

    for obj in room["objects"]:
        ox, oy = obj["pos"]
        rect = pygame.Rect(ox * TILE + 3, oy * TILE + 3, TILE - 6, TILE - 6)
        pygame.draw.rect(screen, obj["color"], rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1, border_radius=4)

    for (dx, dy), _ in room["parsed_doors"].items():
        rect = pygame.Rect(dx * TILE, dy * TILE, TILE, TILE)
        pygame.draw.rect(screen, COLOR_DOOR, rect)
        pygame.draw.rect(screen, COLOR_WALL_EDGE, rect, 2)
        cx = dx * TILE + TILE // 2
        cy = dy * TILE + TILE // 2
        pygame.draw.circle(screen, COLOR_DOOR_GLOW, (cx, cy), 4)

    for (wx, wy) in room["walls"]:
        rect = pygame.Rect(wx * TILE, wy * TILE, TILE, TILE)
        pygame.draw.rect(screen, wall, rect)
        pygame.draw.rect(screen, COLOR_WALL_EDGE, rect, 1)


def draw_player(screen, player, age: int = 3):
    if player.is_moving:
        frame_idx = 1 + int(player.anim_timer * ANIM_FPS) % 4
    else:
        frame_idx = 0

    size = _age_size(age)
    sprite = get_char_frame(
        player.sprite_id, player.facing, frame_idx, size,
    )
    sprite = _apply_aging(sprite, age)

    rect = sprite.get_rect(center=(int(player.x), int(player.y)))
    screen.blit(sprite, rect)


def draw_npcs(screen, room, player=None, highlight_npc=None):
    npcs = room.get("npcs", [])
    if not npcs:
        return

    font = pygame.font.SysFont("Arial", 12, bold=True)

    for npc in npcs:
        nx = npc["pos"][0] * TILE + TILE // 2
        ny = npc["pos"][1] * TILE + TILE // 2

        pygame.draw.circle(screen, (40, 40, 40), (nx + 1, ny + 2), 11)
        pygame.draw.circle(screen, tuple(npc["color"]), (nx, ny), 11)
        pygame.draw.circle(screen, (30, 30, 30), (nx, ny), 11, 2)

        if highlight_npc is not None and highlight_npc is npc:
            pygame.draw.circle(screen, (255, 230, 80), (nx, ny), 15, 2)

        letter = font.render(npc["name"][:1].upper(), True, (20, 20, 20))
        screen.blit(letter, letter.get_rect(center=(nx, ny)))
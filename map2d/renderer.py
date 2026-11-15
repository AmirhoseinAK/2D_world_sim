"""Draw rooms, walls, doors, objects, player."""
import pygame

from .constants import (
    TILE, ROOM_W, ROOM_H,
    COLOR_FLOOR, COLOR_WALL, COLOR_WALL_EDGE,
    COLOR_DOOR, COLOR_DOOR_GLOW,
    COLOR_PLAYER, COLOR_PLAYER_RING,
)


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


def draw_player(screen, player):
    cx, cy = int(player.x), int(player.y)
    pygame.draw.circle(screen, COLOR_PLAYER, (cx, cy), int(player.radius))
    pygame.draw.circle(screen, COLOR_PLAYER_RING, (cx, cy), int(player.radius), 2)
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 3)
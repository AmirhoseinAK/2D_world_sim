"""Load sprites: static tiles from top-down pack, characters from LPC."""
from __future__ import annotations

from pathlib import Path

import pygame

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TILES_DIR = PROJECT_ROOT / "assets" / "top-down-pack-2" / "tiles"
CHAR_DIR = PROJECT_ROOT / "assets" / "characters"

# Character sprites per gender (populated by build_characters.py)
MALE_SPRITES = [f"male_{i:02d}" for i in range(1, 7)]
FEMALE_SPRITES = [f"female_{i:02d}" for i in range(1, 7)]

SPRITE_MAP = {
    "floor_grass": 1,
    "floor_dirt": 13,
    "floor_stone": 25,
    "floor_wood": 85,
    "wall_brick": 61,
    "wall_dark": 73,
    "table": 113,
    "chair": 109,
    "counter": 114,
    "plant": 119,
    "tree": 118,
    "fire": 116,
    "rock": 120,
    "barrel": 121,
    "door": 106,
}

# LPC walking rows: 8=up, 9=left, 10=down, 11=right
FACING_ROW = {"up": 8, "left": 9, "down": 10, "right": 11}
WALK_FRAMES = [1, 3, 5, 7]  # 4-frame cycle
IDLE_FRAME = 0
LPC_FRAME_SIZE = 64

_tile_cache: dict[str, pygame.Surface] = {}
_char_sheet_cache: dict[str, pygame.Surface] = {}
_char_frame_cache: dict[tuple, pygame.Surface] = {}


def get_sprite(name: str) -> pygame.Surface:
    if name in _tile_cache:
        return _tile_cache[name]
    if name not in SPRITE_MAP:
        surf = pygame.Surface((16, 16))
        surf.fill((255, 0, 255))
        return surf
    path = TILES_DIR / f"Slice {SPRITE_MAP[name]}.png"
    if not path.exists():
        print(f"[warn] missing tile: {path}")
        surf = pygame.Surface((16, 16))
        surf.fill((255, 0, 255))
        return surf
    try:
        img = pygame.image.load(str(path)).convert_alpha()
        from .constants import TILE
        scaled = pygame.transform.scale(img, (TILE, TILE))
        _tile_cache[name] = scaled
        return scaled
    except Exception as e:
        print(f"[error] {name}: {e}")
        surf = pygame.Surface((16, 16))
        surf.fill((255, 0, 255))
        return surf


def _load_char_sheet(sprite_id: str) -> pygame.Surface:
    if sprite_id in _char_sheet_cache:
        return _char_sheet_cache[sprite_id]
    path = CHAR_DIR / f"{sprite_id}.png"
    if not path.exists():
        print(f"[warn] missing character sheet: {path}")
        surf = pygame.Surface((LPC_FRAME_SIZE, LPC_FRAME_SIZE), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 255))
        return surf
    sheet = pygame.image.load(str(path)).convert_alpha()
    _char_sheet_cache[sprite_id] = sheet
    return sheet


def get_char_frame(
    sprite_id: str,
    facing: str,
    frame_idx: int,
    display_size: int,
    flip: bool = False,
) -> pygame.Surface:
    """Return one frame of a character, scaled. frame_idx: 0=idle, else 0-3 for walk."""
    key = (sprite_id, facing, frame_idx, display_size, flip)
    if key in _char_frame_cache:
        return _char_frame_cache[key]

    sheet = _load_char_sheet(sprite_id)
    row = FACING_ROW.get(facing, 10)
    col = IDLE_FRAME if frame_idx == 0 else WALK_FRAMES[frame_idx % len(WALK_FRAMES)]

    src = pygame.Rect(
        col * LPC_FRAME_SIZE, row * LPC_FRAME_SIZE,
        LPC_FRAME_SIZE, LPC_FRAME_SIZE,
    )
    try:
        frame = sheet.subsurface(src).copy()
    except ValueError:
        frame = pygame.Surface((LPC_FRAME_SIZE, LPC_FRAME_SIZE), pygame.SRCALPHA)

    frame = pygame.transform.scale(frame, (display_size, display_size))
    if flip:
        frame = pygame.transform.flip(frame, True, False)

    _char_frame_cache[key] = frame
    return frame
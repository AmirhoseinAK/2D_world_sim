"""Player position, movement, and collision."""
from .constants import TILE, ROOM_W, ROOM_H


class Player:
    def __init__(self, tile_x, tile_y):
        self.x = tile_x * TILE + TILE / 2.0
        self.y = tile_y * TILE + TILE / 2.0
        self.speed = 180.0
        self.radius = 11.0

    def center_tile(self):
        return int(self.x // TILE), int(self.y // TILE)

    def try_move(self, dx, dy, dt, blocked):
        if dx:
            nx = self.x + dx * self.speed * dt
            if not self._collides(nx, self.y, blocked):
                self.x = nx
        if dy:
            ny = self.y + dy * self.speed * dt
            if not self._collides(self.x, ny, blocked):
                self.y = ny

    def _collides(self, px, py, blocked):
        r = self.radius
        for cx, cy in (
            (px - r, py - r),
            (px + r, py - r),
            (px - r, py + r),
            (px + r, py + r),
        ):
            gx = int(cx // TILE)
            gy = int(cy // TILE)
            if gx < 0 or gy < 0 or gx >= ROOM_W or gy >= ROOM_H:
                return True
            if (gx, gy) in blocked:
                return True
        return False
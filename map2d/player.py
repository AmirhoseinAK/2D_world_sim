"""Player position, movement, collision, animation state."""
from .constants import TILE


class Player:
    def __init__(self, tile_x, tile_y, sprite_id: str = "male_01"):
        self.x = tile_x * TILE + TILE / 2.0
        self.y = tile_y * TILE + TILE / 2.0
        self.speed = 180.0
        self.radius = 11.0
        self.facing = "down"
        self.is_moving = False
        self.anim_timer = 0.0
        self.sprite_id = sprite_id

    def center_tile(self):
        return int(self.x // TILE), int(self.y // TILE)

    def try_move(self, dx, dy, dt, blocked):
        moved = False

        if dx < 0:
            self.facing = "left"
        elif dx > 0:
            self.facing = "right"
        elif dy < 0:
            self.facing = "up"
        elif dy > 0:
            self.facing = "down"

        if dx:
            nx = self.x + dx * self.speed * dt
            if not self._collides(nx, self.y, blocked):
                self.x = nx
                moved = True
        if dy:
            ny = self.y + dy * self.speed * dt
            if not self._collides(self.x, ny, blocked):
                self.y = ny
                moved = True

        self.is_moving = moved
        if moved:
            self.anim_timer += dt
        else:
            self.anim_timer = 0.0

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
            if (gx, gy) in blocked:
                return True
        return False
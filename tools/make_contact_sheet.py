"""Generate a numbered contact sheet of all tiles for visual identification."""
from pathlib import Path

import pygame

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
TILES_DIR = ASSETS_DIR / "tiles"
OUT_FILE = ASSETS_DIR / "contact_sheet.png"

COLS = 12
TILE_DISPLAY = 32
LABEL_H = 16
CELL_W = TILE_DISPLAY + 4
CELL_H = TILE_DISPLAY + LABEL_H + 4


def main():
    pygame.init()
    try:
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
    except AttributeError:
        pygame.display.set_mode((1, 1))

    if not TILES_DIR.exists():
        print(f"ERROR: {TILES_DIR} not found")
        return

    tiles = sorted(
        TILES_DIR.glob("Slice *.png"),
        key=lambda p: int(p.stem.split()[1]),
    )
    if not tiles:
        print(f"ERROR: no 'Slice N.png' files in {TILES_DIR}")
        return

    print(f"Found {len(tiles)} tiles")

    main_path = ASSETS_DIR / "top-down-pack-2.png"
    if main_path.exists():
        m = pygame.image.load(str(main_path))
        print(f"Main sheet {main_path.name}: {m.get_size()}")

    first = pygame.image.load(str(tiles[0]))
    print(f"First tile size: {first.get_size()}")

    rows = (len(tiles) + COLS - 1) // COLS
    W = COLS * CELL_W + 4
    H = rows * CELL_H + 4
    sheet = pygame.Surface((W, H))
    sheet.fill((24, 24, 30))

    label_font = pygame.font.SysFont("Consolas", 10)

    for i, t in enumerate(tiles):
        c = i % COLS
        r = i // COLS
        x = c * CELL_W + 4
        y = r * CELL_H + 4
        try:
            spr = pygame.image.load(str(t)).convert_alpha()
            spr = pygame.transform.scale(spr, (TILE_DISPLAY, TILE_DISPLAY))
            sheet.blit(spr, (x, y))
        except Exception as e:
            print(f"  skip {t.name}: {e}")

        num = int(t.stem.split()[1])
        label = label_font.render(str(num), True, (220, 220, 220))
        sheet.blit(label, (x + 2, y + TILE_DISPLAY))

    pygame.image.save(sheet, str(OUT_FILE))
    print(f"\nSaved contact sheet: {OUT_FILE} ({W}x{H})")
    print("Open this image and tell me which slice numbers are:")
    print("  - player (idle + walk in 4 directions)")
    print("  - floor tiles, wall tiles, door")
    print("  - table, chair, bed, counter, plant, tree, etc.")
    print("  - NPC characters (cook, nurse, shopkeeper, stranger)")


if __name__ == "__main__":
    main()
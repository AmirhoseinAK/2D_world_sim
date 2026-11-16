"""Compose 12 complete character sprites from LPC layers."""
from pathlib import Path

import pygame

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LPC = PROJECT_ROOT / "assets" / "lpc"
OUT = PROJECT_ROOT / "assets" / "characters"
OUT.mkdir(parents=True, exist_ok=True)

# Distribution: 2 light, 2 tanned, 2 dark per gender
SKIN_PLAN = [("light", 2), ("tanned", 2), ("dark", 2)]

MALE_HAIR_STYLES = [
    "plain", "messy1", "swoop", "parted", "shortknot", "messy2",
]

FEMALE_HAIR_STYLES = [
    "long", "plain", "ponytail", "bangs", "princess", "page",
]

SHIRT_CATEGORY = {"male": "longsleeve", "female": "sleeveless"}


def pick_hair(gender, style, index):
    base = LPC / "hair" / gender
    folder = base / style
    if folder.is_dir():
        pngs = sorted(folder.glob("*.png"))
        if pngs:
            return pngs[index % len(pngs)]
    file = base / f"{style}.png"
    return file if file.exists() else None


def pick_shirt(gender, index):
    cat = SHIRT_CATEGORY[gender]
    folder = LPC / "torso" / "shirts" / cat / gender
    if folder.is_dir():
        pngs = sorted(folder.glob("*.png"))
        if pngs:
            return pngs[index % len(pngs)]
    return None


def build_one(gender, skin, hair_path, shirt_path):
    body_path = LPC / "body" / gender / f"{skin}.png"
    if not body_path.exists():
        print(f"  [skip] no body: {body_path}")
        return None
    base = pygame.image.load(str(body_path)).convert_alpha()
    if shirt_path and shirt_path.exists():
        shirt = pygame.image.load(str(shirt_path)).convert_alpha()
        base.blit(shirt, (0, 0))
    if hair_path and hair_path.exists():
        hair = pygame.image.load(str(hair_path)).convert_alpha()
        base.blit(hair, (0, 0))
    return base


def main():
    pygame.init()
    try:
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
    except AttributeError:
        pygame.display.set_mode((1, 1))

    for gender in ["male", "female"]:
        hair_pool = MALE_HAIR_STYLES if gender == "male" else FEMALE_HAIR_STYLES
        idx = 0
        for skin, count in SKIN_PLAN:
            for _ in range(count):
                style = hair_pool[idx % len(hair_pool)]
                hair_path = pick_hair(gender, style, idx)
                shirt_path = pick_shirt(gender, idx)
                sheet = build_one(gender, skin, hair_path, shirt_path)
                if sheet is None:
                    idx += 1
                    continue
                out_name = f"{gender}_{idx + 1:02d}.png"
                pygame.image.save(sheet, str(OUT / out_name))
                hair_label = hair_path.name if hair_path else "-"
                shirt_label = shirt_path.name if shirt_path else "-"
                print(f"  built {out_name}  skin={skin}  hair={style}/{hair_label}  shirt={shirt_label}")
                idx += 1

    print(f"\nDone. Output: {OUT}")


if __name__ == "__main__":
    main()
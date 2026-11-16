"""App orchestrator: settings first, then game."""
from __future__ import annotations

import pygame

from core.config import load_config
from .settings_screen import run_settings_screen


def run_app():
    pygame.init()

    ok = run_settings_screen()
    if not ok:
        pygame.quit()
        return

    cfg = load_config()

    from .game import run
    run(cfg)

    pygame.quit()
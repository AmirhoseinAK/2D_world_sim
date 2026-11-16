"""App orchestrator: settings → start menu → game."""
from __future__ import annotations

import pygame

from core.config import load_config
from .settings_screen import run_settings_screen
from .start_menu import run_start_menu


def run_app():
    pygame.init()

    # 1) Settings (always shown)
    if not run_settings_screen():
        pygame.quit()
        return

    cfg = load_config()

    # 2) Start menu (New / Load / Quit)
    action, data = run_start_menu()
    if action == "quit":
        pygame.quit()
        return

    # 3) Game
    from .game import run
    if action == "load" and data:
        run(cfg, loaded_data=data)
    else:
        run(cfg)

    pygame.quit()
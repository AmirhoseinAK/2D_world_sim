"""Main menu shown after settings."""
from __future__ import annotations

import pygame

from core.save_manager import list_saves


MENU_W, MENU_H = 600, 500
BG = (18, 18, 24)
PANEL = (30, 30, 38)
BORDER = (70, 70, 90)
BORDER_HOVER = (100, 160, 240)
TEXT = (240, 240, 240)
DIM = (140, 140, 150)
TITLE = (180, 220, 255)
BTN_NEW = (50, 140, 80)
BTN_LOAD = (60, 130, 170)
BTN_QUIT = (90, 90, 100)
BTN_DISABLED = (50, 50, 60)


def _lighten(color, hover, amount=40):
    if not hover:
        return color
    return tuple(min(255, c + amount) for c in color)


def run_start_menu() -> tuple[str, dict | None]:
    """Returns ("new", None) or ("load", data) or ("quit", None)."""
    screen = pygame.display.get_surface()
    if screen is None:
        pygame.init()
        screen = pygame.display.set_mode((MENU_W, MENU_H))
    else:
        screen = pygame.display.set_mode((MENU_W, MENU_H))
    pygame.display.set_caption("2D World Sim — Main Menu")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Arial", 30, bold=True)
    font_sub = pygame.font.SysFont("Arial", 13)
    font_btn = pygame.font.SysFont("Arial", 18, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)

    saves = list_saves()
    has_saves = len(saves) > 0

    btn_w, btn_h = 260, 50
    btn_x = (MENU_W - btn_w) // 2
    btn_new = pygame.Rect(btn_x, 200, btn_w, btn_h)
    btn_load = pygame.Rect(btn_x, 270, btn_w, btn_h)
    btn_quit = pygame.Rect(btn_x, 340, btn_w, btn_h)

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ("quit", None)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return ("quit", None)
                if event.key == pygame.K_n:
                    return ("new", None)
                if event.key == pygame.K_l and has_saves:
                    from .save_load_ui import run_load_dialog
                    data = run_load_dialog(screen)
                    if data:
                        return ("load", data)
                if event.key == pygame.K_q:
                    return ("quit", None)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if btn_new.collidepoint(mx, my):
                    return ("new", None)
                if btn_load.collidepoint(mx, my) and has_saves:
                    from .save_load_ui import run_load_dialog
                    data = run_load_dialog(screen)
                    if data:
                        return ("load", data)
                if btn_quit.collidepoint(mx, my):
                    return ("quit", None)

        # ---- draw ----
        screen.fill(BG)

        title = font_title.render("2D WORLD SIM", True, TITLE)
        screen.blit(title, title.get_rect(center=(MENU_W // 2, 90)))

        sub = font_sub.render("A life simulation", True, DIM)
        screen.blit(sub, sub.get_rect(center=(MENU_W // 2, 130)))

        mx, my = pygame.mouse.get_pos()

        # New Game
        hover = btn_new.collidepoint(mx, my)
        pygame.draw.rect(screen, _lighten(BTN_NEW, hover), btn_new, border_radius=6)
        pygame.draw.rect(screen, (80, 200, 120) if hover else (70, 180, 110), btn_new, 2, border_radius=6)
        label = font_btn.render("New Game", True, TEXT)
        screen.blit(label, label.get_rect(center=btn_new.center))
        hint = font_sm.render("start a new life  (N)", True, DIM)
        screen.blit(hint, (btn_new.x + 10, btn_new.y + btn_new.h + 4))

        # Load Game
        if has_saves:
            hover = btn_load.collidepoint(mx, my)
            pygame.draw.rect(screen, _lighten(BTN_LOAD, hover), btn_load, border_radius=6)
            pygame.draw.rect(screen, (100, 180, 230) if hover else (80, 150, 200), btn_load, 2, border_radius=6)
            label = font_btn.render("Load Game", True, TEXT)
            screen.blit(label, label.get_rect(center=btn_load.center))
            hint = font_sm.render(f"{len(saves)} save(s) available  (L)", True, DIM)
            screen.blit(hint, (btn_load.x + 10, btn_load.y + btn_load.h + 4))
        else:
            pygame.draw.rect(screen, BTN_DISABLED, btn_load, border_radius=6)
            pygame.draw.rect(screen, BORDER, btn_load, 2, border_radius=6)
            label = font_btn.render("Load Game", True, (90, 90, 100))
            screen.blit(label, label.get_rect(center=btn_load.center))
            hint = font_sm.render("no saves yet", True, DIM)
            screen.blit(hint, (btn_load.x + 10, btn_load.y + btn_load.h + 4))

        # Quit
        hover = btn_quit.collidepoint(mx, my)
        pygame.draw.rect(screen, _lighten(BTN_QUIT, hover), btn_quit, border_radius=6)
        pygame.draw.rect(screen, (120, 120, 140) if hover else BORDER, btn_quit, 2, border_radius=6)
        label = font_btn.render("Quit", True, TEXT)
        screen.blit(label, label.get_rect(center=btn_quit.center))
        hint = font_sm.render("exit  (Q)", True, DIM)
        screen.blit(hint, (btn_quit.x + 10, btn_quit.y + btn_quit.h + 4))

        footer = font_sm.render("Esc = quit   ↑↓/click = select", True, DIM)
        screen.blit(footer, (20, MENU_H - 24))

        pygame.display.flip()
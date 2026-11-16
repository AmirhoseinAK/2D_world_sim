"""Modal overlay dialogs for save/load. Drawn on the existing game screen."""
from __future__ import annotations

import time

import pygame

from core.save_manager import (
    SAVES_DIR,
    delete_save,
    generate_default_save_name,
    list_saves,
    load_game,
    save_game,
)

FPS = 60

DIM_BG = (10, 10, 15, 220)
PANEL_BG = (30, 30, 38)
PANEL_BORDER = (100, 160, 240)
TEXT = (240, 240, 240)
DIM = (140, 140, 150)
TITLE = (180, 220, 255)
GOOD = (150, 255, 180)
WARN = (240, 200, 120)

BTN_PRIMARY = (50, 140, 80)
BTN_SECONDARY = (90, 90, 100)
BTN_DANGER = (150, 60, 60)

BACKSPACE_INITIAL_DELAY = 0.35
BACKSPACE_REPEAT_INTERVAL = 0.03


def _get_clipboard() -> str:
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        try:
            return r.clipboard_get() or ""
        finally:
            r.destroy()
    except Exception:
        return ""


def _set_clipboard(text: str) -> bool:
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        try:
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
        finally:
            r.destroy()
        return True
    except Exception:
        return False


def _draw_dim_overlay(screen):
    size = screen.get_size()
    s = pygame.Surface(size, pygame.SRCALPHA)
    s.fill(DIM_BG)
    screen.blit(s, (0, 0))


def _draw_panel(screen, rect):
    pygame.draw.rect(screen, PANEL_BG, rect)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 2)


def _hover_lighten(color, hover, amount=30):
    if not hover:
        return color
    return tuple(min(255, c + amount) for c in color)


# =============================================================
# SAVE DIALOG
# =============================================================
def run_save_dialog(screen, state, world, player, last_tile) -> bool:
    clock = pygame.time.Clock()
    sw, sh = screen.get_size()

    font_title = pygame.font.SysFont("Arial", 18, bold=True)
    font_label = pygame.font.SysFont("Arial", 12, bold=True)
    font_input = pygame.font.SysFont("Consolas", 14)
    font_sm = pygame.font.SysFont("Arial", 11)
    font_btn = pygame.font.SysFont("Arial", 13, bold=True)

    panel_w = min(sw - 40, 440)
    panel_h = min(sh - 40, 380)
    panel = pygame.Rect((sw - panel_w) // 2, (sh - panel_h) // 2, panel_w, panel_h)

    save_name = generate_default_save_name(state)
    existing_names = {s["filename"] for s in list_saves()}

    input_rect = pygame.Rect(panel.x + 20, panel.y + 90, panel.w - 40, 34)
    btn_save = pygame.Rect(panel.x + 20, panel.y + panel.h - 60, 130, 38)
    btn_cancel = pygame.Rect(panel.x + panel.w - 120, panel.y + panel.h - 60, 100, 38)

    status = ""
    status_color = DIM
    cursor_blink = 0.0
    backspace_hold_started = None
    backspace_last_tick = 0.0

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        now = time.time()
        cursor_blink = (cursor_blink + dt) % 1.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    backspace_hold_started = None
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if event.button == 1:
                    if btn_save.collidepoint(mx, my):
                        if not save_name.strip():
                            status = "Name can't be empty"
                            status_color = WARN
                        else:
                            path = SAVES_DIR / f"{save_name.strip()}.json"
                            save_game(path, state.to_dict(), world.to_dict(),
                                      (player.x, player.y), last_tile)
                            return True
                    elif btn_cancel.collidepoint(mx, my):
                        return False
                elif event.button == 3:
                    clip = _get_clipboard().strip()
                    if clip:
                        save_name = (save_name + clip)[:80]
                        status = f"Pasted {len(clip)}"
                        status_color = GOOD
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                return False

            ctrl = bool(event.mod & pygame.KMOD_CTRL)

            if ctrl and event.key == pygame.K_v:
                clip = _get_clipboard().strip()
                if clip:
                    save_name = (save_name + clip)[:80]
                    status = f"Pasted {len(clip)}"
                    status_color = GOOD
                continue

            if event.key == pygame.K_BACKSPACE:
                save_name = save_name[:-1]
                backspace_hold_started = now
                backspace_last_tick = now
                continue

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if save_name.strip():
                    path = SAVES_DIR / f"{save_name.strip()}.json"
                    save_game(path, state.to_dict(), world.to_dict(),
                              (player.x, player.y), last_tile)
                    return True
                continue

            if event.unicode and event.unicode.isprintable():
                if len(save_name) < 80:
                    save_name += event.unicode

        if backspace_hold_started is not None:
            if now - backspace_hold_started > BACKSPACE_INITIAL_DELAY:
                if now - backspace_last_tick >= BACKSPACE_REPEAT_INTERVAL:
                    save_name = save_name[:-1]
                    backspace_last_tick = now

        # ---- draw ----
        _draw_dim_overlay(screen)
        _draw_panel(screen, panel)

        screen.blit(font_title.render("Save Game", True, TITLE),
                    (panel.x + 20, panel.y + 18))

        screen.blit(font_label.render("Save name:", True, TEXT),
                    (panel.x + 20, panel.y + 66))

        pygame.draw.rect(screen, (20, 20, 26), input_rect)
        pygame.draw.rect(screen, (100, 160, 240), input_rect, 2)
        cursor = "|" if cursor_blink < 0.5 else ""
        display_name = save_name
        if len(display_name) > 30:
            display_name = "..." + display_name[-27:]
        screen.blit(font_input.render(display_name + cursor, True, TEXT),
                    (input_rect.x + 8, input_rect.y + 9))

        if save_name.strip() in existing_names:
            screen.blit(font_sm.render("⚠ will overwrite existing save", True, WARN),
                        (panel.x + 20, panel.y + 132))

        summary = f"{state.name}, {state.age}y — {world.current_label()}"
        screen.blit(font_sm.render(summary[:60], True, DIM),
                    (panel.x + 20, panel.y + 155))

        mx, my = pygame.mouse.get_pos()

        pygame.draw.rect(screen, _hover_lighten(BTN_PRIMARY, btn_save.collidepoint(mx, my)), btn_save)
        screen.blit(font_btn.render("Save", True, TEXT),
                    (btn_save.x + 46, btn_save.y + 11))

        pygame.draw.rect(screen, _hover_lighten(BTN_SECONDARY, btn_cancel.collidepoint(mx, my)), btn_cancel)
        screen.blit(font_btn.render("Cancel", True, TEXT),
                    (btn_cancel.x + 24, btn_cancel.y + 11))

        if status:
            screen.blit(font_sm.render(status[:60], True, status_color),
                        (panel.x + 20, panel.y + panel.h - 90))

        screen.blit(font_sm.render("Enter = save   Esc = cancel   Ctrl+V = paste",
                                    True, DIM),
                    (panel.x + 20, panel.y + panel.h - 20))

        pygame.display.flip()


# =============================================================
# LOAD DIALOG
# =============================================================
def run_load_dialog(screen) -> dict | None:
    clock = pygame.time.Clock()
    sw, sh = screen.get_size()

    font_title = pygame.font.SysFont("Arial", 18, bold=True)
    font_row = pygame.font.SysFont("Arial", 12)
    font_meta = pygame.font.SysFont("Arial", 10)
    font_sm = pygame.font.SysFont("Arial", 11)
    font_btn = pygame.font.SysFont("Arial", 13, bold=True)

    panel_w = min(sw - 40, 440)
    panel_h = min(sh - 40, 400)
    panel = pygame.Rect((sw - panel_w) // 2, (sh - panel_h) // 2, panel_w, panel_h)

    saves = list_saves()
    selected_idx = 0 if saves else -1
    scroll = 0
    visible_rows = 5
    row_h = 36

    list_top = panel.y + 65
    btn_load = pygame.Rect(panel.x + panel.w - 260, panel.y + panel.h - 55, 110, 36)
    btn_delete = pygame.Rect(panel.x + panel.w - 145, panel.y + panel.h - 55, 90, 36)
    btn_cancel = pygame.Rect(panel.x + 20, panel.y + panel.h - 55, 90, 36)

    status = ""
    status_color = DIM

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_DOWN and saves:
                    selected_idx = min(selected_idx + 1, len(saves) - 1)
                    if selected_idx - scroll >= visible_rows:
                        scroll = selected_idx - visible_rows + 1
                elif event.key == pygame.K_UP and saves:
                    selected_idx = max(selected_idx - 1, 0)
                    if selected_idx < scroll:
                        scroll = selected_idx
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if saves and selected_idx >= 0:
                        try:
                            return load_game(saves[selected_idx]["path"])
                        except Exception as e:
                            status = f"Failed: {e}"
                            status_color = WARN

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for i in range(visible_rows):
                    idx = scroll + i
                    if idx >= len(saves):
                        break
                    row_rect = pygame.Rect(panel.x + 20, list_top + i * row_h,
                                            panel.w - 40, row_h - 4)
                    if row_rect.collidepoint(mx, my):
                        selected_idx = idx
                        break
                if btn_load.collidepoint(mx, my) and saves and selected_idx >= 0:
                    try:
                        return load_game(saves[selected_idx]["path"])
                    except Exception as e:
                        status = f"Failed: {e}"
                        status_color = WARN
                elif btn_cancel.collidepoint(mx, my):
                    return None
                elif btn_delete.collidepoint(mx, my) and saves and selected_idx >= 0:
                    delete_save(saves[selected_idx]["path"])
                    saves = list_saves()
                    if not saves:
                        selected_idx = -1
                    else:
                        selected_idx = min(selected_idx, len(saves) - 1)
                        scroll = max(0, min(scroll, len(saves) - visible_rows))
                    status = "Deleted"
                    status_color = GOOD

            if event.type == pygame.MOUSEWHEEL:
                if saves:
                    scroll = max(0, min(scroll - event.y, max(0, len(saves) - visible_rows)))

        # ---- draw ----
        _draw_dim_overlay(screen)
        _draw_panel(screen, panel)

        screen.blit(font_title.render("Load Game", True, TITLE),
                    (panel.x + 20, panel.y + 18))
        screen.blit(font_sm.render(f"{len(saves)} save(s) in {SAVES_DIR.name}/", True, DIM),
                    (panel.x + 20, panel.y + 46))

        if not saves:
            screen.blit(font_sm.render("No saves yet. Press F5 or click Save.",
                                        True, DIM),
                        (panel.x + 20, list_top + 40))
        else:
            for i in range(visible_rows):
                idx = scroll + i
                if idx >= len(saves):
                    break
                s = saves[idx]
                row_rect = pygame.Rect(panel.x + 20, list_top + i * row_h,
                                        panel.w - 40, row_h - 4)
                is_sel = (idx == selected_idx)
                pygame.draw.rect(screen,
                                  (48, 58, 80) if is_sel else (24, 24, 30),
                                  row_rect)
                pygame.draw.rect(screen,
                                  (100, 160, 240) if is_sel else (60, 60, 75),
                                  row_rect, 2 if is_sel else 1)

                title_line = f"{s['character']}, age {s['age']} — {s['room']}"
                screen.blit(font_row.render(title_line[:60], True, TEXT),
                            (row_rect.x + 8, row_rect.y + 3))
                meta = f"{s['filename']}  •  {s['saved_at']}"
                screen.blit(font_meta.render(meta[:70], True, DIM),
                            (row_rect.x + 8, row_rect.y + 19))

        mx, my = pygame.mouse.get_pos()
        enabled = bool(saves) and selected_idx >= 0

        c = BTN_PRIMARY if enabled else (60, 60, 70)
        pygame.draw.rect(screen, _hover_lighten(c, enabled and btn_load.collidepoint(mx, my)), btn_load)
        screen.blit(font_btn.render("Load", True, TEXT),
                    (btn_load.x + 32, btn_load.y + 10))

        c = BTN_DANGER if enabled else (60, 60, 70)
        pygame.draw.rect(screen, _hover_lighten(c, enabled and btn_delete.collidepoint(mx, my)), btn_delete)
        screen.blit(font_btn.render("Delete", True, TEXT),
                    (btn_delete.x + 20, btn_delete.y + 10))

        pygame.draw.rect(screen, _hover_lighten(BTN_SECONDARY, btn_cancel.collidepoint(mx, my)), btn_cancel)
        screen.blit(font_btn.render("Cancel", True, TEXT),
                    (btn_cancel.x + 20, btn_cancel.y + 10))

        if status:
            screen.blit(font_sm.render(status[:60], True, status_color),
                        (panel.x + 130, panel.y + panel.h - 45))

        screen.blit(font_sm.render("↑↓ select   Enter = load   Esc = cancel",
                                    True, DIM),
                    (panel.x + 20, panel.y + panel.h - 18))

        pygame.display.flip()
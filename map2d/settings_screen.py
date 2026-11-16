"""Settings screen — always shown; Continue if a key is already saved."""
from __future__ import annotations

import sys
import threading
import time

import pygame

from core.user_settings import load_user_settings, save_user_settings


SETTINGS_W, SETTINGS_H = 820, 600
FPS = 60

BG = (18, 18, 24)
PANEL = (30, 30, 38)
BORDER = (70, 70, 90)
BORDER_FOCUS = (100, 160, 240)
BTN_TEST = (60, 100, 170)
BTN_SAVE = (50, 140, 80)
BTN_CONTINUE = (60, 130, 170)
BTN_EXIT = (90, 90, 100)
TEXT = (240, 240, 240)
DIM = (140, 140, 150)
TITLE = (180, 220, 255)
GOOD = (150, 255, 180)
WARN = (240, 200, 120)

BACKSPACE_INITIAL_DELAY = 0.35
BACKSPACE_REPEAT_INTERVAL = 0.03

FIELDS = [
    ("base_url", "Base URL", False),
    ("api_key", "API Key", True),
    ("model", "Model", False),
]


def _get_clipboard() -> str:
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        try:
            text = r.clipboard_get()
        finally:
            r.destroy()
        return text or ""
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


def _paste_into(data, key, status_pair):
    cur = str(data.get(key, ""))
    clip = _get_clipboard().strip()
    if not clip:
        status_pair[0] = "Clipboard is empty"
        status_pair[1] = WARN
        return
    space = 500 - len(cur)
    if space <= 0:
        return
    data[key] = cur + clip[:space]
    status_pair[0] = f"Pasted {len(clip)} characters"
    status_pair[1] = GOOD


class _TestTask:
    TIMEOUT = 20

    def __init__(self):
        self.running = False
        self.result = None
        self.error = None
        self._started = 0.0

    def start(self, cfg):
        if self.running:
            return
        self.running = True
        self.result = None
        self.error = None
        self._started = time.time()

        def _work():
            try:
                from core.llm_client import LLMClient
                c = LLMClient(cfg)
                reply = c.chat(
                    "You are a test.",
                    "Say 'OK' and nothing else.",
                    max_tokens=10,
                )
                self.result = reply
            except Exception as e:
                self.error = str(e)
            finally:
                self.running = False

        threading.Thread(target=_work, daemon=True).start()

    def update(self):
        if self.running and time.time() - self._started > self.TIMEOUT:
            self.running = False
            self.error = "Timed out"


def run_settings_screen() -> bool:
    """Returns True to start the game, False to exit the app."""
    pygame.init()
    screen = pygame.display.set_mode((SETTINGS_W, SETTINGS_H))
    pygame.display.set_caption("2D World Sim — Settings")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Arial", 24, bold=True)
    font_label = pygame.font.SysFont("Arial", 14, bold=True)
    font_input = pygame.font.SysFont("Consolas", 16)
    font_sm = pygame.font.SysFont("Arial", 12)
    font_btn = pygame.font.SysFont("Arial", 14, bold=True)

    saved = load_user_settings()
    has_saved_key = bool(saved.get("api_key", "").strip())
    data = dict(saved)

    focus_idx = 0
    cursor_blink = 0.0
    status_pair = ["", DIM]
    test_task = _TestTask()

    backspace_hold_started = None
    backspace_last_tick = 0.0

    field_rects = [
        pygame.Rect(80, 160 + i * 80, SETTINGS_W - 160, 42)
        for i in range(len(FIELDS))
    ]

    y_btn = 160 + len(FIELDS) * 80 + 30

    btn_test = pygame.Rect(80, y_btn, 180, 42)
    btn_save = pygame.Rect(620, y_btn, 180, 42)
    if has_saved_key:
        btn_continue = pygame.Rect(435, y_btn, 170, 42)
        btn_exit = pygame.Rect(340, y_btn, 80, 42)
    else:
        btn_continue = None
        btn_exit = pygame.Rect(525, y_btn, 80, 42)

    if has_saved_key:
        title = "Settings — API Configuration"
    else:
        title = "Welcome — Enter your API to begin"

    running = True

    while running:
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
                    for i, r in enumerate(field_rects):
                        if r.collidepoint(mx, my):
                            focus_idx = i
                            break

                    if btn_save.collidepoint(mx, my):
                        if not data.get("api_key", "").strip():
                            status_pair[0] = "API key is empty — please fill it in."
                            status_pair[1] = WARN
                        else:
                            save_user_settings(data)
                            return True

                    elif has_saved_key and btn_continue is not None and btn_continue.collidepoint(mx, my):
                        return True

                    elif btn_exit.collidepoint(mx, my):
                        return False

                    elif btn_test.collidepoint(mx, my) and not test_task.running:
                        try:
                            from core.config import LLMConfig
                            cfg = LLMConfig(
                                base_url=data.get("base_url", ""),
                                api_key=data.get("api_key", ""),
                                model=data.get("model", ""),
                                temperature=float(data.get("temperature", 0.8)),
                                max_tokens=int(data.get("max_tokens", 1500)),
                                timeout=30,
                            )
                            test_task.start(cfg)
                            status_pair[0] = "Testing connection..."
                            status_pair[1] = DIM
                        except Exception as e:
                            status_pair[0] = f"Config error: {e}"
                            status_pair[1] = WARN

                elif event.button == 3:
                    for i, r in enumerate(field_rects):
                        if r.collidepoint(mx, my):
                            focus_idx = i
                            break
                    key = FIELDS[focus_idx][0]
                    _paste_into(data, key, status_pair)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if event.key == pygame.K_TAB:
                    focus_idx = (focus_idx + 1) % len(FIELDS)
                    continue

                ctrl = bool(event.mod & pygame.KMOD_CTRL)
                key = FIELDS[focus_idx][0]
                cur = str(data.get(key, ""))

                if ctrl and event.key == pygame.K_v:
                    _paste_into(data, key, status_pair)
                    continue

                if ctrl and event.key == pygame.K_c:
                    if cur:
                        if _set_clipboard(cur):
                            status_pair[0] = "Copied to clipboard"
                            status_pair[1] = GOOD
                    continue

                if ctrl and event.key == pygame.K_a:
                    data[key] = ""
                    status_pair[0] = "Field cleared"
                    status_pair[1] = DIM
                    continue

                if ctrl and event.key == pygame.K_BACKSPACE:
                    data[key] = ""
                    continue

                if event.key == pygame.K_BACKSPACE:
                    data[key] = cur[:-1]
                    backspace_hold_started = now
                    backspace_last_tick = now
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    focus_idx = (focus_idx + 1) % len(FIELDS)
                elif event.unicode and event.unicode.isprintable():
                    if len(cur) < 500:
                        data[key] = cur + event.unicode

        # ---- Backspace hold repeat ----
        if backspace_hold_started is not None:
            elapsed = now - backspace_hold_started
            if elapsed > BACKSPACE_INITIAL_DELAY:
                if now - backspace_last_tick >= BACKSPACE_REPEAT_INTERVAL:
                    key = FIELDS[focus_idx][0]
                    data[key] = str(data.get(key, ""))[:-1]
                    backspace_last_tick = now

        # ---- Test result ----
        test_task.update()
        if (not test_task.running) and (test_task.result or test_task.error):
            if test_task.result:
                status_pair[0] = f"Connected: {str(test_task.result)[:50]}"
                status_pair[1] = GOOD
            else:
                status_pair[0] = f"Failed: {str(test_task.error)[:70]}"
                status_pair[1] = WARN
            test_task.result = None
            test_task.error = None

        # ============ DRAW ============
        screen.fill(BG)

        screen.blit(font_title.render(title, True, TITLE), (80, 50))
        screen.blit(
            font_sm.render(
                "Stored only on this computer "
                "(~/.2d_world_sim/user_settings.json).",
                True, DIM,
            ),
            (80, 90),
        )
        screen.blit(
            font_sm.render(
                "Tip: click Test Connection before saving to verify the key.",
                True, DIM,
            ),
            (80, 110),
        )

        for i, (key, label, is_secret) in enumerate(FIELDS):
            r = field_rects[i]
            focused = (i == focus_idx)
            screen.blit(font_label.render(label, True, TEXT), (r.x, r.y - 22))
            pygame.draw.rect(screen, PANEL, r)
            pygame.draw.rect(screen, BORDER_FOCUS if focused else BORDER, r, 2)

            val = str(data.get(key, ""))
            display = ("*" * len(val)) if is_secret else val
            cursor = "|" if focused and cursor_blink < 0.5 else ""
            screen.blit(font_input.render(display + cursor, True, TEXT),
                        (r.x + 10, r.y + 11))

        mx, my = pygame.mouse.get_pos()

        # Test
        hover = btn_test.collidepoint(mx, my) and not test_task.running
        pygame.draw.rect(screen, (90, 140, 220) if hover else BTN_TEST, btn_test)
        lbl = "Testing..." if test_task.running else "Test Connection"
        screen.blit(font_btn.render(lbl, True, TEXT),
                    (btn_test.x + 16, btn_test.y + 13))

        # Exit
        hover = btn_exit.collidepoint(mx, my)
        pygame.draw.rect(screen, (120, 120, 130) if hover else BTN_EXIT, btn_exit)
        screen.blit(font_btn.render("Exit", True, TEXT),
                    (btn_exit.x + 22, btn_exit.y + 13))

        # Continue (only if saved key exists)
        if btn_continue is not None:
            hover = btn_continue.collidepoint(mx, my)
            pygame.draw.rect(screen, (80, 160, 200) if hover else BTN_CONTINUE, btn_continue)
            screen.blit(font_btn.render("Continue", True, TEXT),
                        (btn_continue.x + 50, btn_continue.y + 13))

        # Save & Start
        hover = btn_save.collidepoint(mx, my)
        pygame.draw.rect(screen, (70, 180, 110) if hover else BTN_SAVE, btn_save)
        save_label = "Update & Start" if has_saved_key else "Save & Start"
        screen.blit(font_btn.render(save_label, True, TEXT),
                    (btn_save.x + 18, btn_save.y + 13))

        if status_pair[0]:
            screen.blit(font_sm.render(status_pair[0][:120], True, status_pair[1]),
                        (80, y_btn + 70))

        screen.blit(
            font_sm.render(
                "Tab/Enter = next   Ctrl+V or right-click = paste   "
                "Ctrl+A = clear   Esc = exit",
                True, DIM,
            ),
            (80, SETTINGS_H - 30),
        )

        pygame.display.flip()

    return False
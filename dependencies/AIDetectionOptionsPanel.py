from __future__ import annotations

from dataclasses import dataclass

import pygame

from dependencies.TelemetryPanels import draw_panel_bg


@dataclass
class AIDetectionOptionsState:
    enabled: bool = True
    tracking: bool = True


def _toggle_rect(rect: pygame.Rect, idx: int) -> pygame.Rect:
    x = rect.x + 20
    y = rect.y + 44 + idx * 28
    return pygame.Rect(x, y, rect.w - 40, 22)


def handle_ai_options_event(state: AIDetectionOptionsState, event, mouse_pos_virtual, rect: pygame.Rect) -> bool:
    if mouse_pos_virtual is None:
        return False
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False

    r0 = _toggle_rect(rect, 0)
    r1 = _toggle_rect(rect, 1)

    if r0.collidepoint(mouse_pos_virtual):
        state.enabled = not state.enabled
        return True
    if r1.collidepoint(mouse_pos_virtual):
        state.tracking = not state.tracking
        return True

    return False


def draw_ai_options_panel(surface: pygame.Surface, rect: pygame.Rect, font15, *, state: AIDetectionOptionsState) -> None:
    draw_panel_bg(surface, rect)

    title = font15.render("AI DETECTIONS OPTIONS", True, (240, 240, 240))
    surface.blit(title, (rect.x + 20, rect.y + 12))

    def _draw_toggle(y_idx: int, label: str, on: bool):
        r = _toggle_rect(rect, y_idx)
        pygame.draw.rect(surface, (30, 30, 30), r, border_radius=6)
        pygame.draw.rect(surface, (60, 60, 60), r, 1, border_radius=6)
        tag = "ON" if on else "OFF"
        t = font15.render(f"{label}: {tag}", True, (240, 240, 240))
        surface.blit(t, (r.x + 10, r.y + (r.h - t.get_height()) // 2))

    _draw_toggle(0, "Detections", state.enabled)
    _draw_toggle(1, "Tracking", state.tracking)

    note = font15.render("(Affects camera overlay)", True, (180, 180, 180))
    surface.blit(note, (rect.x + 20, rect.bottom - 24))

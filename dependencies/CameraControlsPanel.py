from __future__ import annotations

from dataclasses import dataclass

import pygame

from dependencies.TelemetryPanels import draw_panel_bg


@dataclass
class CameraControlsState:
    paused: bool = False


def _toggle_rect(rect: pygame.Rect, idx: int) -> pygame.Rect:
                         
    x = rect.x + 20
    y = rect.y + 44 + idx * 28
    return pygame.Rect(x, y, rect.w - 40, 22)


def handle_camera_controls_event(state: CameraControlsState, event, mouse_pos_virtual, rect: pygame.Rect) -> bool:
    if mouse_pos_virtual is None:
        return False
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False

    r0 = _toggle_rect(rect, 0)
    if r0.collidepoint(mouse_pos_virtual):
        state.paused = not state.paused
        return True

    return False


def draw_camera_controls_panel(surface: pygame.Surface, rect: pygame.Rect, font15, *, state: CameraControlsState) -> None:
    draw_panel_bg(surface, rect)

    title = font15.render("CAMERA CONTROLS", True, (240, 240, 240))
    surface.blit(title, (rect.x + 20, rect.y + 12))

    r0 = _toggle_rect(rect, 0)
    pygame.draw.rect(surface, (30, 30, 30), r0, border_radius=6)
    pygame.draw.rect(surface, (60, 60, 60), r0, 1, border_radius=6)
    label = "Pause video" if not state.paused else "Resume video"
    txt = font15.render(label, True, (240, 240, 240))
    surface.blit(txt, (r0.x + 10, r0.y + (r0.h - txt.get_height()) // 2))

    status = font15.render(f"State: {'PAUSED' if state.paused else 'LIVE'}", True, (210, 210, 210))
    surface.blit(status, (rect.x + 20, rect.bottom - 24))

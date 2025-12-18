from __future__ import annotations

import pygame

from dependencies.TelemetryPanels import draw_panel_bg


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def draw_thrusters_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    font15,
    *,
    left_cmd: float,
    right_cmd: float,
    speed: float,
) -> None:
    draw_panel_bg(surface, rect)

    title = font15.render("THRUSTERS / COMMANDES MOTEURS", True, (240, 240, 240))
    surface.blit(title, (rect.x + 20, rect.y + 12))

                                             
    left = _clamp(float(left_cmd), -100.0, 100.0)
    right = _clamp(float(right_cmd), -100.0, 100.0)

    y0 = rect.y + 44
    bar_w = rect.w - 40
    bar_h = 16

    def _bar(y, label, value, color):
        lab = font15.render(label, True, (220, 220, 220))
        surface.blit(lab, (rect.x + 20, y))

        track = pygame.Rect(rect.x + 140, y + 2, max(10, bar_w - 120), bar_h)
        pygame.draw.rect(surface, (45, 45, 45), track, border_radius=6)
        pygame.draw.rect(surface, (70, 70, 70), track, 1, border_radius=6)

        mid_x = track.centerx
        pygame.draw.line(surface, (85, 85, 85), (mid_x, track.y + 2), (mid_x, track.bottom - 2), 1)

                          
        frac = abs(value) / 100.0
        fill_w = int((track.w // 2) * frac)
        if value >= 0:
            fill = pygame.Rect(mid_x, track.y + 2, fill_w, track.h - 4)
        else:
            fill = pygame.Rect(mid_x - fill_w, track.y + 2, fill_w, track.h - 4)
        pygame.draw.rect(surface, color, fill, border_radius=6)

        txt = font15.render(f"{value:+.0f}%", True, (240, 240, 240))
        surface.blit(txt, (track.right - txt.get_width() - 6, y))

    _bar(y0, "LEFT", left, (110, 160, 255))
    _bar(y0 + 24, "RIGHT", right, (110, 160, 255))

    sp = font15.render(f"Speed: {speed:.1f}", True, (210, 210, 210))
    surface.blit(sp, (rect.x + 20, rect.bottom - 24))

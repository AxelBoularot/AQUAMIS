from __future__ import annotations

import pygame

from dependencies.TelemetryPanels import draw_panel_bg


def draw_power_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    font15,
    *,
    battery_percent: int,
    charging: bool,
    consumption_pct_per_min: float | None,
    remaining_min: float | None,
) -> None:
    draw_panel_bg(surface, rect)

    title = font15.render("POWER / CONSOMMATION", True, (240, 240, 240))
    surface.blit(title, (rect.x + 20, rect.y + 12))

    pct = int(max(0, min(100, battery_percent)))
    state = "CHARGING" if charging else "DISCHARGING"
    line1 = font15.render(f"Battery: {pct}%  ({state})", True, (240, 240, 240))
    surface.blit(line1, (rect.x + 20, rect.y + 42))

    if consumption_pct_per_min is not None:
        line2 = font15.render(f"Conso: {consumption_pct_per_min:.2f}% / min", True, (220, 220, 220))
        surface.blit(line2, (rect.x + 20, rect.y + 64))

    if (remaining_min is not None) and (not charging):
        if remaining_min >= 60:
            txt = f"Remaining: {remaining_min/60.0:.1f} h"
        else:
            txt = f"Remaining: {remaining_min:.0f} min"
        line3 = font15.render(txt, True, (220, 220, 220))
        surface.blit(line3, (rect.x + 20, rect.y + 86))

from __future__ import annotations

import pygame


def _scale_surf(surf: pygame.Surface, scale: float) -> pygame.Surface:
    if scale == 1.0:
        return surf
    return pygame.transform.smoothscale(
        surf,
        (max(1, int(surf.get_width() * scale)), max(1, int(surf.get_height() * scale))),
    )


def draw_panel_bg(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, (25, 25, 25), rect, border_radius=8)
    pygame.draw.rect(surface, (60, 60, 60), rect, 1, border_radius=8)


def draw_pressure_depth_panel(surface: pygame.Surface, rect: pygame.Rect, font15, pressure_bar: float, depth_m: float) -> None:
    draw_panel_bg(surface, rect)
    scale = max(0.6, min(2.0, min(rect.w / 160, rect.h / 160)))
    pad_x = int(14 * scale)
    pad_y = int(10 * scale)
    title = _scale_surf(font15.render("PRESSURE", True, (240, 240, 240)), scale)
    surface.blit(title, (rect.x + pad_x, rect.y + pad_y))

                                            
    squareish = rect.h >= 120 and abs(rect.w - rect.h) <= 40
    if squareish:
        p_txt = _scale_surf(font15.render(f"{pressure_bar:.2f} bar", True, (240, 240, 240)), scale)
        d_lbl = _scale_surf(font15.render("DEPTH", True, (200, 200, 200)), scale)
        d_txt = _scale_surf(font15.render(f"{depth_m:.2f} m", True, (240, 240, 240)), scale)

        cy = rect.centery
        surface.blit(p_txt, p_txt.get_rect(center=(rect.centerx, cy - int(28 * scale))))
        surface.blit(d_lbl, d_lbl.get_rect(center=(rect.centerx, cy + int(4 * scale))))
        surface.blit(d_txt, d_txt.get_rect(center=(rect.centerx, cy + int(28 * scale))))
    else:
        title2 = _scale_surf(font15.render("/ DEPTH", True, (240, 240, 240)), scale)
        surface.blit(title2, (rect.x + int(110 * scale), rect.y + pad_y))
        p = _scale_surf(font15.render(f"{pressure_bar:.2f} bar", True, (240, 240, 240)), scale)
        d = _scale_surf(font15.render(f"{depth_m:.2f} m", True, (240, 240, 240)), scale)
        surface.blit(p, (rect.x + int(20 * scale), rect.y + int(42 * scale)))
        surface.blit(d, (rect.x + int(20 * scale), rect.y + int(64 * scale)))


def draw_temp_panel(surface: pygame.Surface, rect: pygame.Rect, font15, temp_c: float) -> None:
    draw_panel_bg(surface, rect)
    scale = max(0.6, min(2.0, min(rect.w / 160, rect.h / 160)))
    pad_x = int(14 * scale)
    title = _scale_surf(font15.render("ELECTRONICS", True, (240, 240, 240)), scale)
    surface.blit(title, (rect.x + pad_x, rect.y + int(10 * scale)))
    title2 = _scale_surf(font15.render("TEMP", True, (240, 240, 240)), scale)
    surface.blit(title2, (rect.x + pad_x, rect.y + int(28 * scale)))

    color = (240, 240, 240)
    if temp_c >= 60:
        color = (255, 140, 80)
    if temp_c >= 75:
        color = (255, 90, 90)

    squareish = rect.h >= 120 and abs(rect.w - rect.h) <= 40
    t = _scale_surf(font15.render(f"{temp_c:.1f} C", True, color), scale)
    if squareish:
        surface.blit(t, t.get_rect(center=(rect.centerx, rect.centery + int(14 * scale))))
    else:
        surface.blit(t, (rect.x + int(20 * scale), rect.y + int(44 * scale)))

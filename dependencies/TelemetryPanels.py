from __future__ import annotations

import pygame


def draw_panel_bg(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, (25, 25, 25), rect, border_radius=8)
    pygame.draw.rect(surface, (60, 60, 60), rect, 1, border_radius=8)


def draw_pressure_depth_panel(surface: pygame.Surface, rect: pygame.Rect, font15, pressure_bar: float, depth_m: float) -> None:
    draw_panel_bg(surface, rect)
    title = font15.render("PRESSURE", True, (240, 240, 240))
    surface.blit(title, (rect.x + 14, rect.y + 10))

                                            
    squareish = rect.h >= 120 and abs(rect.w - rect.h) <= 40
    if squareish:
        p_txt = font15.render(f"{pressure_bar:.2f} bar", True, (240, 240, 240))
        d_lbl = font15.render("DEPTH", True, (200, 200, 200))
        d_txt = font15.render(f"{depth_m:.2f} m", True, (240, 240, 240))

        cy = rect.centery
        surface.blit(p_txt, p_txt.get_rect(center=(rect.centerx, cy - 28)))
        surface.blit(d_lbl, d_lbl.get_rect(center=(rect.centerx, cy + 4)))
        surface.blit(d_txt, d_txt.get_rect(center=(rect.centerx, cy + 28)))
    else:
        title2 = font15.render("/ DEPTH", True, (240, 240, 240))
        surface.blit(title2, (rect.x + 110, rect.y + 10))
        p = font15.render(f"{pressure_bar:.2f} bar", True, (240, 240, 240))
        d = font15.render(f"{depth_m:.2f} m", True, (240, 240, 240))
        surface.blit(p, (rect.x + 20, rect.y + 42))
        surface.blit(d, (rect.x + 20, rect.y + 64))


def draw_temp_panel(surface: pygame.Surface, rect: pygame.Rect, font15, temp_c: float) -> None:
    draw_panel_bg(surface, rect)
    title = font15.render("ELECTRONICS", True, (240, 240, 240))
    surface.blit(title, (rect.x + 14, rect.y + 10))
    title2 = font15.render("TEMP", True, (240, 240, 240))
    surface.blit(title2, (rect.x + 14, rect.y + 28))

    color = (240, 240, 240)
    if temp_c >= 60:
        color = (255, 140, 80)
    if temp_c >= 75:
        color = (255, 90, 90)

    squareish = rect.h >= 120 and abs(rect.w - rect.h) <= 40
    t = font15.render(f"{temp_c:.1f} C", True, color)
    if squareish:
        surface.blit(t, t.get_rect(center=(rect.centerx, rect.centery + 14)))
    else:
        surface.blit(t, (rect.x + 20, rect.y + 44))

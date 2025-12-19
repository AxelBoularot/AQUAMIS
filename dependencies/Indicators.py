import math
import pygame


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def draw_signal_indicator(surface: pygame.Surface, rect: pygame.Rect, strength_percent: int):
    strength_percent = int(_clamp(strength_percent, 0, 100))
    bars_on = int(round(strength_percent / 20.0))

    pad = 6
    bar_w = 3
    gap = 2
    max_h = rect.h - pad * 2
    x0 = rect.x + pad
    yb = rect.bottom - pad

    for i in range(5):
        h = int(max_h * ((i + 1) / 5.0))
        x = x0 + i * (bar_w + gap)
        color = (0, 255, 0) if i < bars_on else (70, 70, 70)
        pygame.draw.rect(surface, color, pygame.Rect(x, yb - h, bar_w, h), border_radius=2)


def draw_ballast_indicator(surface: pygame.Surface, rect: pygame.Rect, ballast_percent: int):
    ballast_percent = int(_clamp(ballast_percent, 0, 100))
                                   
    pad = 6
    icon_r = max(4, min(7, rect.h // 3))
    cx = rect.x + pad + icon_r
    cy = rect.centery

                                
    pygame.draw.circle(surface, (0, 140, 255), (cx, cy - 2), icon_r)
    tip = (cx, cy + icon_r + 3)
    left = (cx - icon_r, cy)
    right = (cx + icon_r, cy)
    pygame.draw.polygon(surface, (0, 140, 255), [left, right, tip])

    bar_x = cx + icon_r + 6
    bar_w = rect.right - pad - bar_x
    bar_h = 6
    bar_y = rect.centery - bar_h // 2
    if bar_w > 10:
        pygame.draw.rect(surface, (70, 70, 70), pygame.Rect(bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * (ballast_percent / 100.0))
        pygame.draw.rect(surface, (0, 0, 255), pygame.Rect(bar_x, bar_y, fill_w, bar_h), border_radius=4)


def draw_speed_indicator(surface: pygame.Surface, rect: pygame.Rect, speed_value: float, unit: str = "Knots"):
                                                 
    pad = 6
    r = max(7, min(10, rect.h // 2 - 4))
    cx = rect.x + pad + r
    cy = rect.centery + 2

         
    pygame.draw.circle(surface, (200, 200, 200), (cx, cy), r, 2)
    pygame.draw.rect(surface, (25, 25, 25), pygame.Rect(cx - r - 2, cy, (r + 2) * 2, r + 2))

            
    angle = -math.pi * 0.75 + (math.pi * 1.5) * _clamp(speed_value / 15.0, 0.0, 1.0)
    nx = int(cx + math.cos(angle) * (r - 2))
    ny = int(cy + math.sin(angle) * (r - 2))
    pygame.draw.line(surface, (255, 215, 0), (cx, cy), (nx, ny), 2)

                  
    txt = f"{speed_value:.1f}{'kt' if unit == 'Knots' else 'kmh'}"
                                                              
    return txt


def draw_battery_indicator(surface: pygame.Surface, rect: pygame.Rect, percent: int, charging: bool = False):
    percent = int(_clamp(percent, 0, 100))
    pad = 6
    body_w = max(18, rect.w - pad * 2 - 6)
    body_h = max(10, rect.h - pad * 2 - 2)
    x = rect.x + pad
    y = rect.centery - body_h // 2

    body = pygame.Rect(x, y, body_w, body_h)
    tip = pygame.Rect(body.right + 1, y + body_h // 3, 4, body_h // 3)

    pygame.draw.rect(surface, (220, 220, 220), body, 2, border_radius=3)
    pygame.draw.rect(surface, (220, 220, 220), tip, 0, border_radius=1)

    fill_w = int((body_w - 4) * (percent / 100.0))
    fill = pygame.Rect(body.x + 2, body.y + 2, fill_w, body_h - 4)
    fill_color = (0, 255, 0) if percent > 20 else (255, 80, 80)
    pygame.draw.rect(surface, fill_color, fill, border_radius=2)

    if charging:
                             
        bolt = [
            (body.centerx - 2, body.y + 2),
            (body.centerx + 4, body.y + 2),
            (body.centerx - 1, body.centery),
            (body.centerx + 2, body.centery),
            (body.centerx - 4, body.bottom - 2),
            (body.centerx - 1, body.bottom - 2),
            (body.centerx - 3, body.centery),
            (body.centerx - 5, body.centery),
        ]
        pygame.draw.polygon(surface, (255, 215, 0), bolt)


def draw_pressure_depth_indicator(surface: pygame.Surface, rect: pygame.Rect, font: pygame.font.Font, pressure_bar: float, depth_m: float):
    pygame.draw.rect(surface, (20, 20, 20), rect, border_radius=10)
    pygame.draw.rect(surface, (90, 90, 90), rect, width=1, border_radius=10)

    cx, cy = rect.x + 16, rect.centery
    pygame.draw.circle(surface, (120, 200, 255), (cx, cy - 3), 5)
    pygame.draw.circle(surface, (120, 200, 255), (cx, cy + 3), 3)

    txt = f"{depth_m:.1f}m"
    t = font.render(txt, True, (230, 230, 230))
    surface.blit(t, (rect.x + 28, rect.y + (rect.h - t.get_height()) // 2))


def draw_temp_indicator(surface: pygame.Surface, rect: pygame.Rect, font: pygame.font.Font, temp_c: float):
    pygame.draw.rect(surface, (20, 20, 20), rect, border_radius=10)
    pygame.draw.rect(surface, (90, 90, 90), rect, width=1, border_radius=10)

    cx, cy = rect.x + 16, rect.centery
    pygame.draw.circle(surface, (255, 120, 120), (cx, cy + 4), 4)
    pygame.draw.line(surface, (255, 120, 120), (cx, cy - 6), (cx, cy + 3), 2)

    txt = f"{temp_c:.0f}°C"
    t = font.render(txt, True, (230, 230, 230))
    surface.blit(t, (rect.x + 28, rect.y + (rect.h - t.get_height()) // 2))


def draw_position_indicator(surface: pygame.Surface, rect: pygame.Rect, font: pygame.font.Font, x: float, y: float, z: float):
    pygame.draw.rect(surface, (20, 20, 20), rect, border_radius=10)
    pygame.draw.rect(surface, (90, 90, 90), rect, width=1, border_radius=10)

    cx, cy = rect.x + 16, rect.centery
    pygame.draw.circle(surface, (180, 220, 180), (cx, cy), 6, 1)
    pygame.draw.line(surface, (180, 220, 180), (cx - 6, cy), (cx + 6, cy), 1)
    pygame.draw.line(surface, (180, 220, 180), (cx, cy - 6), (cx, cy + 6), 1)

    txt = f"{x:+.1f} {y:+.1f} {z:+.1f}"
    t = font.render(txt, True, (230, 230, 230))
    surface.blit(t, (rect.x + 30, rect.y + (rect.h - t.get_height()) // 2))

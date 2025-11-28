import pygame
import math
def load_brand_font(size:int, bold:bool=False):
    """Try loading Century Schoolbook or fallback; fallback to default system font.
    Pygame relies on system-installed fonts; if unavailable, it will fallback.
    """
    preferred = [
        ("Century Schoolbook", bold),
        ("Montserrat", bold),
        ("Roboto", bold),
        ("Arial", bold),
        (None, bold)  # pygame default
    ]
    for name, b in preferred:
        try:
            return pygame.font.SysFont(name, size, bold=b)
        except Exception:
            continue
    return pygame.font.SysFont(None, size, bold=bold)

# Animation helpers
def ease_in_out_cubic(t):
    """Easing function pour animations smooth"""
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_out_elastic(t):
    """Easing élastique pour effet de rebond"""
    c4 = (2 * math.pi) / 3
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def lerp(start, end, t):
    """Linear interpolation entre deux valeurs"""
    return start + (end - start) * t

def lerp_color(color1, color2, t):
    """Interpolation entre deux couleurs"""
    return tuple(int(lerp(c1, c2, t)) for c1, c2 in zip(color1, color2))
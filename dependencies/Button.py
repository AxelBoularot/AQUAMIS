import pygame
from dependencies.Variable import WHITE
BCP = (0, 74, 124)
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text, font, text_color, button_color, action=None, button_color_pressed=BCP, message=""):
        super().__init__()
        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(button_color)
        self.image_hovered = pygame.Surface((width, height))
        self.image_hovered.fill(button_color_pressed)
        self.image = self.image_normal.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.text = text
        self.font = font
        self.text_color = text_color
        self.action = action
        self.message = message
        self._draw_text()

    def _draw_text(self):
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(text_surface, text_rect)

    def update(self, mouse_pos):

        self.image = self.image_hovered.copy() if self.rect.collidepoint(mouse_pos) else self.image_normal.copy()
        self._draw_text()

    def click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            print(self.message)
            if self.action:
                self.action()

def draw_modern_button(surface, x, y, w, h, text, font, is_hovered, is_primary=True):
    """Bouton moderne pour thème sombre avec léger dégradé et halo au survol"""
    rect = pygame.Rect(int(x), int(y), int(w), int(h))
    corner = 15

    # Couleurs de base
    # Couleurs selon le type - inspiré du CSS rgb(0,140,255)
    if is_primary:
        base_color = (0, 140, 255)  # Bleu lumineux pour START
        glow_color = (0, 140, 255)
    else:
        base_color = (80, 90, 110)  # Gris pour QUIT
        glow_color = (100, 110, 130)

    # Effet glow multiple (box-shadow CSS: 0 0 25px, puis au hover: 5px, 25px, 50px, 100px)
    if is_hovered:
        # Glow intensifié au survol - réduit pour éviter trop de débordement
        glow_layers = [
            (40, 35),   # Couche la plus large réduite
            (25, 30),   # Couche moyenne
            (12, 25),   # Couche proche
            (5, 20)     # Couche la plus proche
        ]
        for blur_size, alpha in glow_layers:
            glow_surface = pygame.Surface((rect.width + blur_size * 2, rect.height + blur_size * 2), pygame.SRCALPHA)
            glow_rect = glow_surface.get_rect()
            pygame.draw.rect(glow_surface, (*glow_color, alpha), glow_rect, border_radius=corner + blur_size // 2)
            surface.blit(glow_surface, (rect.x - blur_size, rect.y - blur_size))
    else:
        # Glow de base (0 0 25px dans le CSS)
        glow_surface = pygame.Surface((rect.width + 30, rect.height + 30), pygame.SRCALPHA)
        glow_rect = glow_surface.get_rect()
        pygame.draw.rect(glow_surface, (*glow_color, 40), glow_rect, border_radius=corner + 8)
        surface.blit(glow_surface, (rect.x - 15, rect.y - 15))

    # Bouton principal (background: rgb(0,140,255))
    pygame.draw.rect(surface, base_color, rect, border_radius=corner)

    # Texte en majuscules avec espacement (letter-spacing: 4px, uppercase)
    label = font.render(text.upper(), True, WHITE)
    label_rect = label.get_rect(center=rect.center)
    surface.blit(label, label_rect)

    return rect
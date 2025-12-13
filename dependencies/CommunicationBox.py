import pygame
import random
GREEN = (30, 150, 95)
RED = (200, 50, 50)
class CommunicationBox(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, font, text_color, ok_color, not_ok_color, text):
        super().__init__()
        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(ok_color)
        self.image_error = pygame.Surface((width, height))
        self.image_error.fill(not_ok_color)
        self.image = self.image_normal.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.font = font
        self.text_color = text_color
        self.communication_ok = True
        self.text = text
        self._draw_text()

    def _draw_text(self):
        fill_color = GREEN if self.communication_ok else RED
        self.image.fill(fill_color)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(text_surface, text_rect)

    def update_status(self):
        self.communication_ok = random.choice([True, False])
        base_text = self.text.split(':')[0]
        self.text = f"{base_text}: OK" if self.communication_ok else f"{base_text}: Not OK"
        self.image = self.image_normal.copy() if self.communication_ok else self.image_error.copy()
        self._draw_text()

    def update(self, mouse_pos):
        pass 
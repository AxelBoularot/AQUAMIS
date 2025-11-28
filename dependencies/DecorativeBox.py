import pygame

class DecorativeBox(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, font, text_color, background_color, text, box_id='normal'):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.background_color = background_color
        self.text = text
        self.font = font
        self.text_color = text_color
        self.rect = self.image.get_rect(center=(x, y))
        self._draw_text(box_id)

    def _draw_text(self, box_id='normal'):
        fill_color = (100, 255, 100) if box_id == 'special' else self.background_color
        self.image.fill(fill_color)
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
            self.image.blit(text_surface, text_rect)
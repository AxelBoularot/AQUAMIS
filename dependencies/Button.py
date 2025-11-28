import pygame

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
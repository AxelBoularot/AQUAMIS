import pygame

WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 215, 0)
DARK_GRAY = (30, 30, 30)
BORDER_GRAY = (60, 60, 60)

BTN_BG_COLOR = (40, 40, 40)
BTN_HOVER_COLOR = (60, 60, 60)
BTN_TEXT_COLOR = (240, 240, 240)

class Dashboard:
    def __init__(self, font, font15, font18):
        self.font = font
        self.font15 = font15
        self.font18 = font18
        
        self.speed_unit = "Knots"
        self.ballast_level = 0
        self.signal_strength = 0
        self.speed_value = 0.0
        
        self.width = 370

                                                          
        self.signal_x = 10
        self.signal_y = 310
        self.signal_h = 110

        self.gap = 5
        self.ballast_x = 10
        self.ballast_y = self.signal_y + self.signal_h + self.gap
        self.ballast_h = 110

        self.speed_x = 10
        self.speed_y = self.ballast_y + self.ballast_h + self.gap
        self.speed_h = 110

        self._recalc_layout()

    def _recalc_layout(self):
        self.signal_rect = pygame.Rect(self.signal_x, self.signal_y, self.width, self.signal_h)
        self.ballast_rect = pygame.Rect(self.ballast_x, self.ballast_y, self.width, self.ballast_h)
        self.speed_rect = pygame.Rect(self.speed_x, self.speed_y, self.width, self.speed_h)
        self.speed_switch_rect = pygame.Rect(
            self.speed_rect.centerx - 50,
            self.speed_rect.bottom - 40,
            100,
            30,
        )

    def set_signal_position(self, x: int, y: int):
        if self.signal_x == x and self.signal_y == y:
            return
        self.signal_x = x
        self.signal_y = y
        self._recalc_layout()

    def set_ballast_position(self, x: int, y: int):
        if self.ballast_x == x and self.ballast_y == y:
            return
        self.ballast_x = x
        self.ballast_y = y
        self._recalc_layout()

    def set_speed_position(self, x: int, y: int):
        if self.speed_x == x and self.speed_y == y:
            return
        self.speed_x = x
        self.speed_y = y
        self._recalc_layout()

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.speed_switch_rect.collidepoint(mouse_pos):
                self.speed_unit = "Km/h" if self.speed_unit == "Knots" else "Knots"
                return True
        return False

    def update_data(self, speed=None, ballast=None, signal=None):
        if speed is not None: self.speed_value = speed
        if ballast is not None: self.ballast_level = ballast
        if signal is not None: self.signal_strength = signal

    def draw(self, surface, mouse_pos=None):
        self.draw_signal(surface, mouse_pos=mouse_pos)
        self.draw_ballast(surface, mouse_pos=mouse_pos)
        self.draw_speed(surface, mouse_pos=mouse_pos)

    def draw_signal(self, surface, mouse_pos=None):
        pygame.draw.rect(surface, DARK_GRAY, self.signal_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, self.signal_rect, 1, border_radius=8)

        surface.blit(self.font15.render("SIGNAL STRENGTH", True, WHITE), (self.signal_rect.x + 20, self.signal_rect.y + 15))
        for i in range(5):
            color = GREEN if i < (self.signal_strength / 20) else (50, 50, 50)
            pygame.draw.rect(surface, color, (self.signal_rect.x + 20 + (i * 30), self.signal_rect.y + 45, 20, 30))

        surface.blit(self.font15.render(f"{int(self.signal_strength)}%", True, WHITE), (self.signal_rect.right - 60, self.signal_rect.y + 18))

    def draw_ballast(self, surface, mouse_pos=None):
        pygame.draw.rect(surface, DARK_GRAY, self.ballast_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, self.ballast_rect, 1, border_radius=8)

        surface.blit(self.font15.render("BALLAST", True, WHITE), (self.ballast_rect.x + 20, self.ballast_rect.y + 15))
        surface.blit(self.font15.render(f"{int(self.ballast_level)}%", True, WHITE), (self.ballast_rect.right - 60, self.ballast_rect.y + 15))
        pygame.draw.rect(surface, (50, 50, 50), (self.ballast_rect.x + 20, self.ballast_rect.y + 55, 330, 20), border_radius=5)
        pygame.draw.rect(
            surface,
            BLUE,
            (self.ballast_rect.x + 20, self.ballast_rect.y + 55, 330 * (self.ballast_level / 100), 20),
            border_radius=5,
        )

    def draw_speed(self, surface, mouse_pos=None):
        pygame.draw.rect(surface, DARK_GRAY, self.speed_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, self.speed_rect, 1, border_radius=8)

        surface.blit(self.font15.render("SPEED", True, WHITE), (self.speed_rect.x + 20, self.speed_rect.y + 15))

        display_speed = self.speed_value
        if self.speed_unit == "Km/h":
            display_speed *= 1.852

        speed_text = self.font.render(f"{display_speed:.1f}", True, YELLOW)
        speed_text = pygame.transform.scale(speed_text, (int(speed_text.get_width() * 1.5), int(speed_text.get_height() * 1.5)))
        surface.blit(speed_text, (self.speed_rect.centerx - speed_text.get_width()//2, self.speed_rect.centery - 25))

        is_hovered = mouse_pos and self.speed_switch_rect.collidepoint(mouse_pos)
        btn_color = BTN_HOVER_COLOR if is_hovered else BTN_BG_COLOR

        pygame.draw.rect(surface, btn_color, self.speed_switch_rect, border_radius=5)
        if is_hovered:
            pygame.draw.rect(surface, BORDER_GRAY, self.speed_switch_rect, 1, border_radius=5)

        unit_text = self.font15.render(self.speed_unit, True, BTN_TEXT_COLOR)
        surface.blit(unit_text, (self.speed_switch_rect.centerx - unit_text.get_width()//2, self.speed_switch_rect.centery - unit_text.get_height()//2))

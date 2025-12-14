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
        
        self.x = 10
        self.width = 370
        
        self.box1_y = 310
        self.box1_height = 180
        
        self.gap = 5 
        self.box2_y = self.box1_y + self.box1_height + self.gap
        self.box2_height = 120 
        
        self.box1_rect = pygame.Rect(self.x, self.box1_y, self.width, self.box1_height)
        self.box2_rect = pygame.Rect(self.x, self.box2_y, self.width, self.box2_height)
        
        self.speed_switch_rect = pygame.Rect(
            self.box2_rect.centerx - 50, 
            self.box2_rect.bottom - 40, 
            100, 
            30
        )

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
        pygame.draw.rect(surface, DARK_GRAY, self.box1_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, self.box1_rect, 1, border_radius=8)
        
        surface.blit(self.font15.render("SIGNAL STRENGTH", True, WHITE), (self.box1_rect.x + 20, self.box1_rect.y + 15))
        for i in range(5):
            color = GREEN if i < (self.signal_strength / 20) else (50, 50, 50)
            pygame.draw.rect(surface, color, (self.box1_rect.x + 20 + (i * 30), self.box1_rect.y + 45, 20, 30))
        
        surface.blit(self.font15.render(f"BALLAST: {self.ballast_level}%", True, WHITE), (self.box1_rect.x + 20, self.box1_rect.y + 90))
        pygame.draw.rect(surface, (50, 50, 50), (self.box1_rect.x + 20, self.box1_rect.y + 120, 330, 20), border_radius=5)
        pygame.draw.rect(surface, BLUE, (self.box1_rect.x + 20, self.box1_rect.y + 120, 330 * (self.ballast_level / 100), 20), border_radius=5)

        pygame.draw.rect(surface, DARK_GRAY, self.box2_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, self.box2_rect, 1, border_radius=8)
        
        surface.blit(self.font15.render("SPEED", True, WHITE), (self.box2_rect.x + 20, self.box2_rect.y + 15))
        
        display_speed = self.speed_value
        if self.speed_unit == "Km/h":
            display_speed *= 1.852
        
        speed_text = self.font.render(f"{display_speed:.1f}", True, YELLOW)
        speed_text = pygame.transform.scale(speed_text, (int(speed_text.get_width() * 1.5), int(speed_text.get_height() * 1.5)))
        surface.blit(speed_text, (self.box2_rect.centerx - speed_text.get_width()//2, self.box2_rect.centery - 25))
        
        is_hovered = mouse_pos and self.speed_switch_rect.collidepoint(mouse_pos)
        btn_color = BTN_HOVER_COLOR if is_hovered else BTN_BG_COLOR
        
        pygame.draw.rect(surface, btn_color, self.speed_switch_rect, border_radius=5)
        if is_hovered:
            pygame.draw.rect(surface, BORDER_GRAY, self.speed_switch_rect, 1, border_radius=5)
            
        unit_text = self.font15.render(self.speed_unit, True, BTN_TEXT_COLOR)
        surface.blit(unit_text, (self.speed_switch_rect.centerx - unit_text.get_width()//2, self.speed_switch_rect.centery - unit_text.get_height()//2))

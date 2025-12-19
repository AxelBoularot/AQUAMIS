import pygame
from dependencies.Variable import WHITE

                
BCP = (0, 74, 124)                                      

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text, font, text_color, button_color, action=None, button_color_pressed=BCP, message=""):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.base_color = button_color
        self.hover_color = button_color_pressed
        self.action = action
        self.message = message
        
                                  
        self.border_radius = 10
        self.border_width = 1
        self.border_color = (255, 255, 255, 30)                                     
        
                           
        self.image_normal = self._create_surface(self.base_color)
        self.image_hovered = self._create_surface(self.hover_color, is_hover=True)
        
        self.image = self.image_normal

    def _create_surface(self, color, is_hover=False):
                                    
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
                                              
        pygame.draw.rect(surface, color, surface.get_rect(), border_radius=self.border_radius)
        
                            
        pygame.draw.rect(surface, self.border_color, surface.get_rect(), width=self.border_width, border_radius=self.border_radius)
        
                   
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        surface.blit(text_surf, text_rect)
        
        return surface

    def update(self, mouse_pos):
                            
        if self.rect.collidepoint(mouse_pos):
            self.image = self.image_hovered
        else:
            self.image = self.image_normal

    def click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            if self.message:
                print(self.message)
            if self.action:
                self.action()

def draw_modern_button(surface, x, y, w, h, text, font, is_hovered, is_primary=True):
    rect = pygame.Rect(int(x), int(y), int(w), int(h))
    
            
    base_color = (0, 120, 215) if is_primary else (60, 60, 60)
    hover_color = (0, 140, 255) if is_primary else (80, 80, 80)
    color = hover_color if is_hovered else base_color
    
                       
    pygame.draw.rect(surface, color, rect, border_radius=10)
    
            
    pygame.draw.rect(surface, (255, 255, 255, 40), rect, width=1, border_radius=10)

          
    label = font.render(text, True, WHITE)
    label_rect = label.get_rect(center=rect.center)
    surface.blit(label, label_rect)

    return rect
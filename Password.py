import pygame
import sys

class Special_button:
    def __init__(self, x, y, width, height, text, font, text_color, button_color, 
                 button_color_pressed, screen, action=None, message="", ):
        self.rect = pygame.Rect(x, y, width, height)
        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(button_color)
        self.image_hovered = pygame.Surface((width, height))
        self.image = self.image_normal.copy()
        self.image_hovered.fill(button_color_pressed)
        self.color = (139, 0, 0)
        self.text = text
        self.font = font
        self.action = action
        self.text_color = text_color
        self.message = message
        self.show_password_input = False
        self.show_confirmation_input = False
        self.password_text = ""
        self.correct_password = "a"
        self.correct_stop = "stop"
        self.screen = screen
        self._draw_text()

    def draw(self, screen, font):
        screen.blit(self.image, self.rect.topleft)
        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect.topleft)
        
        if self.show_confirmation_input:
            font12 = pygame.font.SysFont('CenturySchoolBook', 12)
            pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(20, 630, 170, 50))
            text = font12.render('ENTER STOP TO CONFIRM!', True, (255, 255, 255))
            pygame.draw.rect(screen, (0, 0, 0), (20, 630, 170, 100))
            text_center = text.get_rect(center=pygame.Rect(20, 630, 170, 50).center)
            input_box = pygame.Rect(20, 680, 170, 50)
            pygame.draw.rect(screen, (139, 0, 0), input_box, 5)
            password_surface = font.render(self.password_text, True, (255, 255, 255))
            password_rect = password_surface.get_rect(center=input_box.center)
            screen.blit(password_surface, password_rect.topleft)
            screen.blit(text, text_center)
    
        if self.show_password_input:
            target_screen = self.screen  
            font25 = pygame.font.SysFont('CenturySchoolBook', 25)
            text = font25.render('ENTER PASSWORD TO UNLOCK THE INTERFACE!', True, (255, 255, 255))
            text_center = text.get_rect(center=pygame.Rect(865, 600, 170, 50).center)
            input_box = pygame.Rect(700, 680, 500, 50)
            pygame.draw.rect(target_screen, (255, 255, 255), input_box, 5)
            password_surface = font.render(self.password_text, True, (255, 255, 255))
            password_rect = password_surface.get_rect(center=input_box.center)
            target_screen.blit(password_surface, password_rect.topleft)
            target_screen.blit(text, text_center)
    
    def _draw_text(self):
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(text_surface, text_rect)
        
    def update(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.image = self.image_hovered.copy()
        else:
            self.image = self.image_normal.copy()
        self._draw_text()
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos): 
            print(self.message)
            if self.action:
                self.action()
    
    def handle_event_start(self, event):
        if self.show_password_input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.password_text == self.correct_password:
                        print("\nInitializing System - AMIS has successfully started!\n\n" 
                              + "Timer has started!\n\n")
                        self.show_password_input = False
                        self.password_text = ""
                        if self.action:
                            self.action()
                        
                        return "switch_screen"
                    else:
                        print("\nWrong Password! Please try again.")
                        self.password_text = ""
                        return None
                elif event.key == pygame.K_ESCAPE:
                    self.show_password_input = False
                elif event.key == pygame.K_BACKSPACE:
                    self.password_text = self.password_text[:-1]
                else:
                    self.password_text += event.unicode
    
    def handle_event_stop(self, event):
        if self.show_confirmation_input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.password_text == self.correct_stop:
                        print("\nSuccessfully stopped AMIS!")
                        self.show_confirmation_input = False
                        sys.exit()
                        self.password_text = ""
                        if self.action:
                            self.action()
                    else:
                        print("\nIncorrect input!")
                        self.password_text = ""
                elif event.key == pygame.K_ESCAPE:
                    self.show_confirmation = False
                elif event.key == pygame.K_BACKSPACE:
                    self.password_text = self.password_text[:-1]
                else:
                    self.password_text += event.unicode
    
    def stop_trigger(self):
        self.show_confirmation_input = True
    
    def start_trigger(self):
        self.show_password_input = True

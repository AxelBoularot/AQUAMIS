import pygame
import sys
import math

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
        # Animation variables
        self.fade_alpha = 0
        self.fade_speed = 60
        self.target_alpha = 0
        self.error_message = ""
        self.error_time = 0
        # Mode test (téléphone)
        self.test_mode = False
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
            self._draw_modern_password_input(screen)
    
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
            # Gestion du clic sur le toggle
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hasattr(self, 'toggle_rect') and self.toggle_rect.collidepoint(event.pos):
                    self.test_mode = not self.test_mode
                    mode_text = "TEST MODE (Phone)" if self.test_mode else "NORMAL MODE (Satellite)"
                    print(f"\n🔄 Mode changed to: {mode_text}")
                    return None
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.password_text == self.correct_password:
                        mode_text = "TEST MODE (Phone)" if self.test_mode else "NORMAL MODE (Satellite)"
                        print(f"\nInitializing System - AMIS has successfully started in {mode_text}!\n\n" 
                              + "Timer has started!\n\n")
                        self.target_alpha = 0  # Fade out
                        self.password_text = ""
                        if self.action:
                            self.action()
                        # Attendre que le fade out soit terminé
                        if self.fade_alpha <= 0:
                            self.show_password_input = False
                            return "switch_screen"
                        return "switch_screen"
                    else:
                        print("\nWrong Password! Please try again.")
                        import time
                        self.error_message = "❌ Incorrect password"
                        self.error_time = time.time()
                        self.password_text = ""
                        return None
                elif event.key == pygame.K_ESCAPE:
                    self.target_alpha = 0  # Fade out
                    if self.fade_alpha <= 0:
                        self.show_password_input = False
                    self.password_text = ""
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
        self.target_alpha = 255
        self.error_message = ""
    
    def _draw_modern_password_input(self, screen):
        """Dessine une interface moderne de mot de passe avec animation de fondu"""
        import time
        
        # Animation de fade in/out
        if self.fade_alpha < self.target_alpha:
            self.fade_alpha = min(self.fade_alpha + self.fade_speed, self.target_alpha)
        elif self.fade_alpha > self.target_alpha:
            self.fade_alpha = max(self.fade_alpha - self.fade_speed, self.target_alpha)
        
        if self.fade_alpha <= 0:
            return
        
        # Dimensions de l'écran
        screen_width, screen_height = screen.get_size()
        
        # Arrière-plan flou avec effet de blur simulé
        blur_overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        blur_overlay.fill((10, 18, 28, int(220 * self.fade_alpha / 255)))
        screen.blit(blur_overlay, (0, 0))
        
        # Dimensions de la boîte de dialogue
        box_width = min(600, screen_width - 100)
        box_height = 280
        box_x = (screen_width - box_width) // 2
        box_y = (screen_height - box_height) // 2
        
        # Surface de la boîte avec transparence
        dialog_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        
        # Ombre de la boîte
        shadow_offset = 12
        shadow = pygame.Surface((box_width + shadow_offset * 2, box_height + shadow_offset * 2), pygame.SRCALPHA)
        for i in range(shadow_offset, 0, -1):
            alpha = int(30 * (shadow_offset - i) / shadow_offset * self.fade_alpha / 255)
            pygame.draw.rect(shadow, (0, 0, 0, alpha), 
                           (i, i, box_width + shadow_offset * 2 - i * 2, box_height + shadow_offset * 2 - i * 2), 
                           border_radius=20)
        screen.blit(shadow, (box_x - shadow_offset, box_y - shadow_offset))
        
        # Charger et afficher l'image de fond si elle existe
        try:
            import os
            back_image_path = r"C:\Users\FlowUP\Downloads\AQUAMIS-main\back.png"
            if os.path.exists(back_image_path):
                back_image = pygame.image.load(back_image_path)
                back_image = pygame.transform.scale(back_image, (box_width, box_height))
                back_image.set_alpha(int(245 * self.fade_alpha / 255))
                dialog_surface.blit(back_image, (0, 0))
            else:
                # Fond de la boîte avec dégradé si pas d'image
                for y in range(box_height):
                    progress = y / box_height
                    color_top = (25, 35, 50)
                    color_bottom = (15, 25, 40)
                    r = int(color_top[0] + (color_bottom[0] - color_top[0]) * progress)
                    g = int(color_top[1] + (color_bottom[1] - color_top[1]) * progress)
                    b = int(color_top[2] + (color_bottom[2] - color_top[2]) * progress)
                    pygame.draw.line(dialog_surface, (r, g, b, int(245 * self.fade_alpha / 255)), 
                                   (0, y), (box_width, y))
        except:
            # Fond de la boîte avec dégradé en cas d'erreur
            for y in range(box_height):
                progress = y / box_height
                color_top = (25, 35, 50)
                color_bottom = (15, 25, 40)
                r = int(color_top[0] + (color_bottom[0] - color_top[0]) * progress)
                g = int(color_top[1] + (color_bottom[1] - color_top[1]) * progress)
                b = int(color_top[2] + (color_bottom[2] - color_top[2]) * progress)
                pygame.draw.line(dialog_surface, (r, g, b, int(245 * self.fade_alpha / 255)), 
                               (0, y), (box_width, y))
        
        # Bordure avec glow - CORRIGÉ pour suivre exactement le cadre
        border_color = (0, 90, 156, int(self.fade_alpha))  # PRIMARY_BLUE
        border_rect = pygame.Rect(0, 0, box_width, box_height)
        pygame.draw.rect(dialog_surface, border_color, border_rect, 3, border_radius=20)
        
        # Titre
        title_font = pygame.font.SysFont('Arial', 28, bold=True)
        title_text = title_font.render("Authentication", True, (0, 90, 156))
        title_text.set_alpha(self.fade_alpha)
        title_rect = title_text.get_rect(centerx=box_width // 2, top=30)
        dialog_surface.blit(title_text, title_rect)
        
        # Sous-titre
        subtitle_font = pygame.font.SysFont('Arial', 16)
        subtitle_text = subtitle_font.render("Enter password to unlock interface", True, (150, 170, 190))
        subtitle_text.set_alpha(self.fade_alpha)
        subtitle_rect = subtitle_text.get_rect(centerx=box_width // 2, top=65)
        dialog_surface.blit(subtitle_text, subtitle_rect)
        
        # Champ de saisie
        input_width = box_width - 80
        input_height = 55
        input_x = 40
        input_y = 110
        
        # Fond du champ de saisie
        input_bg = pygame.Surface((input_width, input_height), pygame.SRCALPHA)
        pygame.draw.rect(input_bg, (40, 50, 70, int(200 * self.fade_alpha / 255)), 
                        (0, 0, input_width, input_height), border_radius=10)
        dialog_surface.blit(input_bg, (input_x, input_y))
        
        # Bordure du champ avec animation
        border_glow = int(50 + 30 * math.sin(time.time() * 3))
        pygame.draw.rect(dialog_surface, (70, 179, 230, int(border_glow * self.fade_alpha / 255)), 
                        (input_x, input_y, input_width, input_height), 2, border_radius=10)
        
        # Texte du mot de passe (masqué avec des points)
        password_font = pygame.font.SysFont('Arial', 24)
        masked_password = "•" * len(self.password_text)
        
        # Curseur clignotant
        if int(time.time() * 2) % 2 == 0:
            masked_password += "|"
        
        password_display = password_font.render(masked_password, True, (255, 255, 255))
        password_display.set_alpha(self.fade_alpha)
        password_rect = password_display.get_rect(centery=input_y + input_height // 2, left=input_x + 20)
        dialog_surface.blit(password_display, password_rect)
        
        # Message d'erreur si incorrect
        if self.error_message and time.time() - self.error_time < 2:
            error_font = pygame.font.SysFont('Arial', 14)
            error_text = error_font.render(self.error_message, True, (255, 80, 80))
            error_text.set_alpha(self.fade_alpha)
            error_rect = error_text.get_rect(centerx=box_width // 2, top=input_y + input_height + 15)
            dialog_surface.blit(error_text, error_rect)
        
        # Toggle Mode Test
        toggle_y = input_y + input_height + 50
        toggle_label_font = pygame.font.SysFont('Arial', 16, bold=True)
        toggle_label = toggle_label_font.render("🧪 Test Mode (Phone Sensors)", True, (180, 200, 220))
        toggle_label.set_alpha(self.fade_alpha)
        toggle_label_rect = toggle_label.get_rect(left=input_x + 50, centery=toggle_y)
        dialog_surface.blit(toggle_label, toggle_label_rect)
        
        # Toggle switch
        switch_width = 50
        switch_height = 26
        switch_x = box_width - input_x - switch_width - 50
        switch_y = toggle_y - switch_height // 2
        
        # Store toggle rect for click detection (relative to dialog box)
        self.toggle_rect = pygame.Rect(box_x + switch_x, box_y + switch_y, switch_width, switch_height)
        
        # Background du switch
        switch_bg_color = (70, 179, 230) if self.test_mode else (80, 90, 110)
        pygame.draw.rect(dialog_surface, switch_bg_color + (int(self.fade_alpha),), 
                        (switch_x, switch_y, switch_width, switch_height), border_radius=13)
        
        # Circle du switch
        circle_x = switch_x + switch_width - 15 if self.test_mode else switch_x + 13
        pygame.draw.circle(dialog_surface, (255, 255, 255, self.fade_alpha), 
                          (int(circle_x), int(switch_y + switch_height // 2)), 10)
        
        # Instructions
        hint_font = pygame.font.SysFont('Arial', 13)
        hint_text = hint_font.render("Press ENTER to confirm • ESC to cancel", True, (120, 140, 160))
        hint_text.set_alpha(int(self.fade_alpha * 0.8))
        hint_rect = hint_text.get_rect(centerx=box_width // 2, bottom=box_height - 25)
        dialog_surface.blit(hint_text, hint_rect)
        
        # Blit de la boîte de dialogue sur l'écran
        screen.blit(dialog_surface, (box_x, box_y))

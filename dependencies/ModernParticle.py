import pygame
import random

BASE_WIDTH = 1500
BASE_HEIGHT = 750
PRIMARY_BLUE = (0x00, 0x5A, 0x9C)   # #005A9C Bleu foncé IPSA
LIGHT_BLUE   = (0x46, 0xB3, 0xE6)   # #46B3E6 Bleu clair AMIS
TEXT_PRIMARY = (40, 55, 70)
TEXT_SECONDARY = (95, 115, 135)
class ModernParticle:
    def __init__(self, screen_width=BASE_WIDTH, screen_height=BASE_HEIGHT):
        self.x_ratio = random.random()
        self.y_ratio = random.random()
        self.base_size = random.uniform(0.5, 2.5)
        self.brightness = random.randint(80, 255)
        self.twinkle_speed = random.uniform(0.3, 1.5)
        
        self.color = random.choice([
            LIGHT_BLUE, PRIMARY_BLUE,
            TEXT_SECONDARY, TEXT_PRIMARY
        ])
        
        self.vx = random.uniform(-0.0001, 0.0001)
        self.vy = random.uniform(-0.0001, 0.0001)
        
        self.glow_intensity = random.uniform(0.3, 0.8)

    def update(self):
        self.brightness += self.twinkle_speed
        if self.brightness > 255:
            self.brightness = 255
            self.twinkle_speed *= -1
        elif self.brightness < 80:
            self.brightness = 80
            self.twinkle_speed *= -1
        
        self.x_ratio += self.vx
        self.y_ratio += self.vy
        
        if self.x_ratio > 1:
            self.x_ratio = 0
        elif self.x_ratio < 0:
            self.x_ratio = 1
        if self.y_ratio > 1:
            self.y_ratio = 0
        elif self.y_ratio < 0:
            self.y_ratio = 1

    def draw(self, screen):
        width, height = screen.get_size()
        x = int(self.x_ratio * width)
        y = int(self.y_ratio * height)
        scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
        size = self.base_size * scale
        
        alpha = int(self.brightness)
        glow_radius = size * 3
        
        for i in range(3):
            glow_alpha = int(alpha * self.glow_intensity * (1 - i * 0.3))
            if glow_alpha > 0:
                glow_size = size + (glow_radius - size) * (i / 3)
                glow_surf = pygame.Surface((glow_size * 4, glow_size * 4), pygame.SRCALPHA)
                color_with_alpha = (*self.color[:3], glow_alpha // (i + 1))
                pygame.draw.circle(glow_surf, color_with_alpha, 
                                 (glow_size * 2, glow_size * 2), glow_size)
                screen.blit(glow_surf, (x - glow_size * 2, y - glow_size * 2))
        
        core_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        core_color = (*self.color[:3], alpha)
        pygame.draw.circle(core_surf, core_color, (size * 2, size * 2), size)
        screen.blit(core_surf, (x - size * 2, y - size * 2))
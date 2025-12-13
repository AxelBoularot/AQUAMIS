import pygame
from datetime import datetime
# Color definitions
WHITE = (255, 255, 255)
BLUE = (100, 149, 237)
YELLOW = (255, 215, 0)
RED = (220, 20, 60)

# ============================================================
# Log System Class
# ============================================================
class LogSystem:
    def __init__(self, font, max_logs=100):
        self.font = font
        self.max_logs = max_logs
        self.logs = []  # List of (timestamp, message, color)
        self.scroll_offset = 0
        self.line_height = 20
        self.visible_lines = 7  # Adjust based on zone height

    def add_log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "info":
            color = BLUE
        elif level == "warning":
            color = YELLOW
        elif level == "error":
            color = RED
        else:
            color = WHITE
        self.logs.append((timestamp, message, color))
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

    def handle_scroll(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset += event.y
            self.scroll_offset = max(0, min(self.scroll_offset, max(0, len(self.logs) - self.visible_lines)))

    def draw(self, surface, x, y, width, height):
        # Draw background
        pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))
        pygame.draw.rect(surface, WHITE, (x, y, width, height), 1)
        
        # Draw title
        title_surf = self.font.render("System Logs", True, YELLOW)
        surface.blit(title_surf, (x + 5, y + 5))
        
        # Draw logs
        start_idx = self.scroll_offset
        for i in range(self.visible_lines):
            idx = start_idx + i
            if idx >= len(self.logs):
                break
            timestamp, message, color = self.logs[idx]
            text = f"[{timestamp}] {message}"
            text_surf = self.font.render(text, True, color)
            surface.blit(text_surf, (x + 5, y + 25 + i * self.line_height))

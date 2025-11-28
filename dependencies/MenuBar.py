import pygame
WHITE        = (0xFF, 0xFF, 0xFF)   # Blanc principal

class MenuBar:
    """Simple Windows-like menu bar with dropdowns implemented in pygame.
    Items: list of tuples (label, [(submenu_label, action), ...]) or action None
    """
    def __init__(self, font, items, bg_color=(40,40,40), fg_color=WHITE, hover_color=(70,70,70)):
        self.font = font
        self.items = items
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.spacing = 14
        self.item_rects = []
        self.open_index = None
        self.hover_index = None
        self.menu_height = 0

    def _build_rects(self, screen_width):
        """Build menu item rects dynamically based on screen width."""
        rects = []
        cx = 10
        for label, submenu in self.items:
            surf = self.font.render(label, True, self.fg_color)
            rect = pygame.Rect(cx, 4, surf.get_width() + 16, surf.get_height() + 8)
            rects.append((label, rect, submenu))
            cx += rect.width + self.spacing
        return rects

    def update(self, mouse_pos):
        self.hover_index = None
        for i, (_, rect, _) in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.hover_index = i
                break

    def draw(self, surface):
        """Draw menu bar at top of screen, responsive to screen width."""
        screen_width = surface.get_width()
        
        # Rebuild rects for current window width
        self.item_rects = self._build_rects(screen_width)
        
        # Calculate bar height
        height = 0
        if self.item_rects:
            height = self.item_rects[0][1].height + 8
        self.menu_height = height + 8
        
        # Draw background bar full width
        pygame.draw.rect(surface, self.bg_color, (0, 0, screen_width, self.menu_height))
        
        # draw items
        for i, (label, rect, submenu) in enumerate(self.item_rects):
            color = self.hover_color if i == self.hover_index or i == self.open_index else self.bg_color
            pygame.draw.rect(surface, color, rect)
            txt = self.font.render(label, True, self.fg_color)
            surface.blit(txt, (rect.x + 8, rect.y + 4))

        # draw open submenu
        if self.open_index is not None:
            _, parent_rect, submenu = self.item_rects[self.open_index]
            if submenu:
                # calculate dropdown rect
                item_h = self.font.get_height() + 8
                w = max((self.font.render(s[0], True, self.fg_color).get_width() for s in submenu), default=100) + 16
                h = item_h * len(submenu)
                drop_rect = pygame.Rect(parent_rect.x, parent_rect.y + parent_rect.height + 2, w, h)
                pygame.draw.rect(surface, (50,50,50), drop_rect)
                for idx, (label, action) in enumerate(submenu):
                    r = pygame.Rect(drop_rect.x, drop_rect.y + idx * item_h, w, item_h)
                    pygame.draw.rect(surface, (70,70,70) if r.collidepoint(pygame.mouse.get_pos()) else (50,50,50), r)
                    surface.blit(self.font.render(label, True, self.fg_color), (r.x + 8, r.y + 4))

    def handle_click(self, mouse_pos):
        # Top item clicked?
        for i, (_, rect, submenu) in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                # toggle open
                if self.open_index == i:
                    self.open_index = None
                else:
                    self.open_index = i
                return True

        # If a submenu is open, check selection
        if self.open_index is not None:
            _, parent_rect, submenu = self.item_rects[self.open_index]
            if submenu:
                item_h = self.font.get_height() + 8
                w = max(self.font.render(s[0], True, self.fg_color).get_width() for s in submenu) + 16
                drop_rect = pygame.Rect(parent_rect.x, parent_rect.y + parent_rect.height + 2, w, item_h * len(submenu))
                if drop_rect.collidepoint(mouse_pos):
                    idx = (mouse_pos[1] - drop_rect.y) // item_h
                    if 0 <= idx < len(submenu):
                        label, action = submenu[idx]
                        if action:
                            action()
                        self.open_index = None
                        return True
            self.open_index = None
        return False
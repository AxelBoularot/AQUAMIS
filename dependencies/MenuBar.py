import pygame

# Modern Color Palette (React Base-UI Dark Theme inspired)
BG_COLOR = (25, 25, 25)       # Deep dark background
ITEM_BG_COLOR = (25, 25, 25)  # Transparent-ish
HOVER_COLOR = (45, 45, 45)    # Subtle hover
ACTIVE_COLOR = (60, 60, 60)   # Active/Selected
TEXT_COLOR = (240, 240, 240)  # Off-white
BORDER_COLOR = (60, 60, 60)   # Subtle borders
SHADOW_COLOR = (0, 0, 0, 100) # Shadow (alpha handled via surface)

class MenuBar:
    """
    Modern, floating Menu Bar inspired by React Base-UI components.
    Features rounded corners, floating dropdowns, and a sleek dark theme.
    """
    def __init__(self, font, items, bg_color=None, fg_color=None, hover_color=None):
        # Note: bg_color, fg_color, hover_color args kept for compatibility but ignored in favor of theme
        self.font = font
        self.items = items
        
        # Layout configuration
        self.padding_x = 16
        self.padding_y = 8
        self.item_spacing = 4
        self.bar_margin_top = 10
        self.bar_margin_left = 10
        self.bar_height = 0 # Calculated dynamically
        self.bar_width = 0  # Calculated dynamically
        self.menu_height = 0 # For external layout compatibility
        
        # State
        self.item_rects = []
        self.open_index = None
        self.hover_index = None
        self.hover_sub_index = None
        
        # Cache for text surfaces to avoid re-rendering every frame
        self._text_cache = {}

    def _get_text_surf(self, text):
        if text not in self._text_cache:
            self._text_cache[text] = self.font.render(text, True, TEXT_COLOR)
        return self._text_cache[text]

    def _build_layout(self):
        """Calculate positions for the main menu bar items."""
        rects = []
        current_x = self.bar_margin_left + self.padding_x
        
        # Calculate height based on font
        sample_surf = self._get_text_surf("Test")
        item_height = sample_surf.get_height() + self.padding_y * 2
        self.bar_height = item_height
        self.menu_height = self.bar_margin_top + self.bar_height + 10 # Expose total height for main.py layout

        for label, submenu in self.items:
            surf = self._get_text_surf(label)
            item_width = surf.get_width() + self.padding_x * 2
            
            # Create rect for this item relative to screen
            rect = pygame.Rect(current_x, self.bar_margin_top, item_width, item_height)
            rects.append((label, rect, submenu))
            
            current_x += item_width + self.item_spacing
            
        self.bar_width = current_x - self.bar_margin_left + self.padding_x - self.item_spacing
        return rects

    def update(self, mouse_pos):
        """Update hover states."""
        self.hover_index = None
        self.hover_sub_index = None
        
        # Check main bar items
        for i, (_, rect, _) in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.hover_index = i
                break
        
        # Check dropdown items if open
        if self.open_index is not None:
            _, parent_rect, submenu = self.item_rects[self.open_index]
            if submenu:
                dropdown_rect, item_height, _ = self._calculate_dropdown_geometry(parent_rect, submenu)
                if dropdown_rect.collidepoint(mouse_pos):
                    # Calculate which sub-item is hovered
                    relative_y = mouse_pos[1] - dropdown_rect.y - 4 # 4 is padding
                    idx = relative_y // item_height
                    if 0 <= idx < len(submenu):
                        self.hover_sub_index = idx

    def _calculate_dropdown_geometry(self, parent_rect, submenu):
        """Calculate the geometry for the dropdown menu."""
        item_height = self.font.get_height() + 12 # More padding for dropdowns
        
        # Find max width needed
        max_w = 0
        for label, _ in submenu:
            w = self._get_text_surf(label).get_width()
            if w > max_w:
                max_w = w
        
        menu_width = max_w + 40 # Padding for text
        menu_height = len(submenu) * item_height + 8 # Vertical padding
        
        # Position: aligned left with parent, slightly below
        x = parent_rect.x
        y = parent_rect.bottom + 4
        
        return pygame.Rect(x, y, menu_width, menu_height), item_height, menu_width

    def draw(self, surface):
        """Draw the menu bar and any open dropdowns."""
        # Rebuild layout (in case of dynamic changes, though usually static)
        self.item_rects = self._build_layout()
        
        # 1. Draw Main Bar Background (Floating Pill)
        bar_bg_rect = pygame.Rect(
            self.bar_margin_left, 
            self.bar_margin_top, 
            self.bar_width, 
            self.bar_height
        )
        
        # Shadow for main bar
        shadow_rect = bar_bg_rect.copy()
        shadow_rect.move_ip(2, 2)
        pygame.draw.rect(surface, (10, 10, 10), shadow_rect, border_radius=8)
        
        # Main bar body
        pygame.draw.rect(surface, BG_COLOR, bar_bg_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_COLOR, bar_bg_rect, width=1, border_radius=8)

        # 2. Draw Main Items
        for i, (label, rect, submenu) in enumerate(self.item_rects):
            is_hovered = (i == self.hover_index)
            is_open = (i == self.open_index)
            
            # Draw item background if hovered or open
            if is_hovered or is_open:
                color = ACTIVE_COLOR if is_open else HOVER_COLOR
                # Adjust rect slightly for visual padding inside the bar
                bg_rect = rect.inflate(-4, -4)
                pygame.draw.rect(surface, color, bg_rect, border_radius=6)

            # Draw text
            text_surf = self._get_text_surf(label)
            text_rect = text_surf.get_rect(center=rect.center)
            surface.blit(text_surf, text_rect)

        # 3. Draw Dropdown if open
        if self.open_index is not None:
            _, parent_rect, submenu = self.item_rects[self.open_index]
            if submenu:
                dropdown_rect, item_height, menu_width = self._calculate_dropdown_geometry(parent_rect, submenu)
                
                # Dropdown Shadow
                drop_shadow = dropdown_rect.copy()
                drop_shadow.move_ip(4, 4)
                s = pygame.Surface((drop_shadow.width, drop_shadow.height), pygame.SRCALPHA)
                pygame.draw.rect(s, SHADOW_COLOR, s.get_rect(), border_radius=8)
                surface.blit(s, drop_shadow.topleft)

                # Dropdown Background
                pygame.draw.rect(surface, BG_COLOR, dropdown_rect, border_radius=8)
                pygame.draw.rect(surface, BORDER_COLOR, dropdown_rect, width=1, border_radius=8)

                # Dropdown Items
                for idx, (label, action) in enumerate(submenu):
                    item_y = dropdown_rect.y + 4 + (idx * item_height)
                    item_rect = pygame.Rect(dropdown_rect.x + 4, item_y, menu_width - 8, item_height)
                    
                    # Hover effect for dropdown item
                    if idx == self.hover_sub_index:
                        pygame.draw.rect(surface, HOVER_COLOR, item_rect, border_radius=4)
                    
                    # Text
                    text_surf = self._get_text_surf(label)
                    # Left align text in dropdown
                    surface.blit(text_surf, (item_rect.x + 12, item_rect.centery - text_surf.get_height()//2))

    def handle_click(self, mouse_pos):
        """Handle mouse clicks. Returns True if a menu action was taken."""
        
        # 1. Check if clicking inside an open dropdown
        if self.open_index is not None:
            _, parent_rect, submenu = self.item_rects[self.open_index]
            if submenu:
                dropdown_rect, item_height, _ = self._calculate_dropdown_geometry(parent_rect, submenu)
                
                if dropdown_rect.collidepoint(mouse_pos):
                    # Clicked inside dropdown
                    relative_y = mouse_pos[1] - dropdown_rect.y - 4
                    idx = relative_y // item_height
                    if 0 <= idx < len(submenu):
                        # Execute action
                        _, action = submenu[idx]
                        if action:
                            action()
                        self.open_index = None # Close menu after action
                        return True
                    return True # Clicked in dropdown but missed item, consume click
                
                # If clicked outside dropdown but NOT on the main bar, close it
                # We check main bar next, so just pass for now
        
        # 2. Check main bar items
        clicked_on_bar = False
        for i, (_, rect, submenu) in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                clicked_on_bar = True
                if self.open_index == i:
                    self.open_index = None # Toggle close
                else:
                    self.open_index = i # Open this one
                return True

        # 3. Clicked outside everything -> Close menu
        if self.open_index is not None and not clicked_on_bar:
            self.open_index = None
            return True
            
        return False
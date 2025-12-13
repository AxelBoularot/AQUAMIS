import pygame

# Palette de couleurs (Thème Sombre)
BG_COLOR = (25, 25, 25)
HOVER_COLOR = (45, 45, 45)
ACTIVE_COLOR = (60, 60, 60)
TEXT_COLOR = (240, 240, 240)
BORDER_COLOR = (60, 60, 60)
SHADOW_COLOR = (0, 0, 0, 100)

class MenuBar:
    def __init__(self, font, items):
        self.font = font
        self.items = items
        
        # Configuration Layout
        self.padding_x = 16
        self.padding_y = 8
        self.item_spacing = 4
        self.bar_margin_top = 10
        self.bar_margin_left = 10
        self.bar_height = 0
        self.bar_width = 0
        
        # --- CORRECTION ICI : Initialisation de l'attribut manquant ---
        self.menu_height = 0 
        
        # État
        self.item_rects = []
        self.open_index = None
        self.hover_index = None
        self.hover_sub_index = None
        
        # Cache texte
        self._text_cache = {}

        # On construit le layout une première fois pour avoir une menu_height valide dès le début
        self._build_layout()

    def _get_text_surf(self, text):
        if text not in self._text_cache:
            self._text_cache[text] = self.font.render(text, True, TEXT_COLOR)
        return self._text_cache[text]

    def _build_layout(self):
        """Calcule les positions des éléments de la barre principale."""
        rects = []
        current_x = self.bar_margin_left + self.padding_x
        
        # Calcul de la hauteur basé sur la police
        sample_surf = self._get_text_surf("Test")
        item_height = sample_surf.get_height() + self.padding_y * 2
        self.bar_height = item_height

        # --- CORRECTION ICI : Calcul de la hauteur totale pour l'extérieur ---
        self.menu_height = self.bar_margin_top + self.bar_height + 10

        for label, submenu in self.items:
            surf = self._get_text_surf(label)
            item_width = surf.get_width() + self.padding_x * 2
            
            rect = pygame.Rect(current_x, self.bar_margin_top, item_width, item_height)
            rects.append((label, rect, submenu))
            
            current_x += item_width + self.item_spacing
            
        self.bar_width = current_x - self.bar_margin_left + self.padding_x - self.item_spacing
        return rects

    def update(self, mouse_pos):
        """Met à jour les survols (hovers)."""
        self.hover_index = None
        self.hover_sub_index = None
        
        # Vérification barre principale
        for i, (_, rect, _) in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.hover_index = i
                break
        
        # Vérification sous-menu ouvert
        if self.open_index is not None:
            _, parent_rect, submenu = self.item_rects[self.open_index]
            if submenu:
                dropdown_rect, item_height, _ = self._calculate_dropdown_geometry(parent_rect, submenu)
                if dropdown_rect.collidepoint(mouse_pos):
                    relative_y = mouse_pos[1] - dropdown_rect.y - 4
                    idx = relative_y // item_height
                    if 0 <= idx < len(submenu):
                        self.hover_sub_index = idx

    def _calculate_dropdown_geometry(self, parent_rect, submenu, screen_height=None):
        item_height = self.font.get_height() + 12
        
        max_w = 0
        for label, _ in submenu:
            w = self._get_text_surf(label).get_width()
            if w > max_w: max_w = w
        
        menu_width = max_w + 40
        menu_height = len(submenu) * item_height + 8
        
        x = parent_rect.x
        y = parent_rect.bottom + 4
        
        # Gestion dépassement écran
        if screen_height and y + menu_height > screen_height:
            y = parent_rect.top - menu_height - 4
        
        return pygame.Rect(x, y, menu_width, menu_height), item_height, menu_width

    def draw_bar(self, surface):
        """Dessine UNIQUEMENT la barre (à appeler AVANT l'interface)."""
        if surface is None: return
        
        # On ne recalcule le layout que si nécessaire, mais pour être sûr on le fait ici
        # pour gérer les changements dynamiques éventuels
        self.item_rects = self._build_layout()
        
        # 1. Fond de la barre
        bar_bg_rect = pygame.Rect(self.bar_margin_left, self.bar_margin_top, self.bar_width, self.bar_height)
        
        # Ombre
        shadow_rect = bar_bg_rect.copy()
        shadow_rect.move_ip(2, 2)
        pygame.draw.rect(surface, (10, 10, 10), shadow_rect, border_radius=8)
        
        # Corps
        pygame.draw.rect(surface, BG_COLOR, bar_bg_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_COLOR, bar_bg_rect, width=1, border_radius=8)

        # 2. Éléments
        for i, (label, rect, submenu) in enumerate(self.item_rects):
            is_hovered = (i == self.hover_index)
            is_open = (i == self.open_index)
            
            if is_hovered or is_open:
                color = ACTIVE_COLOR if is_open else HOVER_COLOR
                bg_rect = rect.inflate(-4, -4)
                pygame.draw.rect(surface, color, bg_rect, border_radius=6)

            text_surf = self._get_text_surf(label)
            text_rect = text_surf.get_rect(center=rect.center)
            surface.blit(text_surf, text_rect)

    def draw_dropdown(self, surface):
        """Dessine UNIQUEMENT le menu déroulant (à appeler APRÈS l'interface)."""
        if surface is None or self.open_index is None: return

        _, parent_rect, submenu = self.item_rects[self.open_index]
        if not submenu: return

        dropdown_rect, item_height, menu_width = self._calculate_dropdown_geometry(parent_rect, submenu, surface.get_height())
        
        # Ombre
        drop_shadow = dropdown_rect.copy()
        drop_shadow.move_ip(4, 4)
        s = pygame.Surface((drop_shadow.width, drop_shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s, SHADOW_COLOR, s.get_rect(), border_radius=8)
        surface.blit(s, drop_shadow.topleft)

        # Fond
        pygame.draw.rect(surface, BG_COLOR, dropdown_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_COLOR, dropdown_rect, width=1, border_radius=8)

        # Éléments liste
        for idx, (label, action) in enumerate(submenu):
            item_y = dropdown_rect.y + 4 + (idx * item_height)
            item_rect = pygame.Rect(dropdown_rect.x + 4, item_y, menu_width - 8, item_height)
            
            if idx == self.hover_sub_index:
                pygame.draw.rect(surface, HOVER_COLOR, item_rect, border_radius=4)
            
            text_surf = self._get_text_surf(label)
            surface.blit(text_surf, (item_rect.x + 12, item_rect.centery - text_surf.get_height()//2))

    def draw(self, surface):
        self.draw_bar(surface)
        self.draw_dropdown(surface)

    def handle_click(self, mouse_pos):
        """Gère les clics."""
        # 1. Clic dans le menu déroulant
        if self.open_index is not None:
            _, parent_rect, submenu = self.item_rects[self.open_index]
            if submenu:
                dropdown_rect, item_height, _ = self._calculate_dropdown_geometry(parent_rect, submenu)
                if dropdown_rect.collidepoint(mouse_pos):
                    relative_y = mouse_pos[1] - dropdown_rect.y - 4
                    idx = relative_y // item_height
                    if 0 <= idx < len(submenu):
                        _, action = submenu[idx]
                        if action: action()
                        self.open_index = None
                        return True
                    return True 
        
        # 2. Clic sur la barre
        clicked_on_bar = False
        for i, (_, rect, submenu) in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                clicked_on_bar = True
                if self.open_index == i:
                    self.open_index = None
                else:
                    self.open_index = i
                return True

        # 3. Clic dehors
        if self.open_index is not None and not clicked_on_bar:
            self.open_index = None
            return True
            
        return False
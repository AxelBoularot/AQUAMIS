import pygame


class DraggableWindow:
    def __init__(self, rect: pygame.Rect, titlebar_height: int = 8, padding: int = 1):
        self.rect = rect
        self.titlebar_height = titlebar_height
        self.padding = padding
        self._dragging = False
        self._drag_offset = (0, 0)

    def titlebar_rect(self) -> pygame.Rect:
        inner = self.rect.inflate(-self.padding * 2, -self.padding * 2)
        return pygame.Rect(inner.x, inner.y, inner.w, min(self.titlebar_height, inner.h))

    def handle_event(self, event: pygame.event.Event, mouse_pos, bounds_size=None, bounds_rect: pygame.Rect | None = None) -> bool:
                                                                                         
        if mouse_pos is None:
            return False

        if bounds_rect is None and bounds_size is not None:
            bounds_rect = pygame.Rect(0, 0, int(bounds_size[0]), int(bounds_size[1]))

        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if self.titlebar_rect().collidepoint(mouse_pos):
                self._dragging = True
                self._drag_offset = (mouse_pos[0] - self.rect.x, mouse_pos[1] - self.rect.y)
                return True

        if event.type == pygame.MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            self._dragging = False
            return False

        if event.type == pygame.MOUSEMOTION and self._dragging:
            new_x = mouse_pos[0] - self._drag_offset[0]
            new_y = mouse_pos[1] - self._drag_offset[1]

            if bounds_rect is not None:
                min_x = int(bounds_rect.x)
                min_y = int(bounds_rect.y)
                max_x = int(bounds_rect.right - self.rect.w)
                max_y = int(bounds_rect.bottom - self.rect.h)
                if max_x < min_x:
                    max_x = min_x
                if max_y < min_y:
                    max_y = min_y
                new_x = max(min_x, min(int(new_x), max_x))
                new_y = max(min_y, min(int(new_y), max_y))

            self.rect.x = int(new_x)
            self.rect.y = int(new_y)
            return True

        return False

    def draw_titlebar_hover(self, surface: pygame.Surface, mouse_pos) -> None:
        if mouse_pos is None:
            return

        bar = self.titlebar_rect()
        if bar.w <= 0 or bar.h <= 0:
            return

        if bar.collidepoint(mouse_pos) or self._dragging:
            alpha = 35 if bar.collidepoint(mouse_pos) else 24
            overlay = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, alpha))
            surface.blit(overlay, (bar.x, bar.y))

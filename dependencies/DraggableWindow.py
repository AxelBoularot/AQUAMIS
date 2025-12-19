import pygame


class DraggableWindow:
    def __init__(
        self,
        rect: pygame.Rect,
        titlebar_height: int = 8,
        padding: int = 1,
        *,
        resize_grip_size: int = 12,
        min_size: tuple[int, int] = (80, 60),
    ):
        self.rect = rect
        self.titlebar_height = titlebar_height
        self.padding = padding
        self.resize_grip_size = int(resize_grip_size)
        self.min_size = (int(min_size[0]), int(min_size[1]))
        self._dragging = False
        self._drag_offset = (0, 0)

        self._resizing = False
        self._resize_start_mouse = (0, 0)
        self._resize_start_size = (0, 0)

    def titlebar_rect(self) -> pygame.Rect:
        inner = self.rect.inflate(-self.padding * 2, -self.padding * 2)
        return pygame.Rect(inner.x, inner.y, inner.w, min(self.titlebar_height, inner.h))

    def resize_grip_rect(self) -> pygame.Rect:
        inner = self.rect.inflate(-self.padding * 2, -self.padding * 2)
        size = max(8, int(self.resize_grip_size))
        return pygame.Rect(inner.right - size, inner.bottom - size, size, size)

    def handle_event(self, event: pygame.event.Event, mouse_pos, bounds_size=None, bounds_rect: pygame.Rect | None = None) -> bool:
                                                                                         
        if mouse_pos is None:
            return False

        if bounds_rect is None and bounds_size is not None:
            bounds_rect = pygame.Rect(0, 0, int(bounds_size[0]), int(bounds_size[1]))

        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            if self.resize_grip_rect().collidepoint(mouse_pos):
                self._resizing = True
                self._resize_start_mouse = (int(mouse_pos[0]), int(mouse_pos[1]))
                self._resize_start_size = (int(self.rect.w), int(self.rect.h))
                self._dragging = False
                return True

            if self.titlebar_rect().collidepoint(mouse_pos):
                self._dragging = True
                self._drag_offset = (mouse_pos[0] - self.rect.x, mouse_pos[1] - self.rect.y)
                self._resizing = False
                return True

        if event.type == pygame.MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            self._dragging = False
            self._resizing = False
            return False

        if event.type == pygame.MOUSEMOTION and self._resizing:
            start_w, start_h = self._resize_start_size
            if start_w <= 0 or start_h <= 0:
                return False

            dx = int(mouse_pos[0]) - int(self._resize_start_mouse[0])
            dy = int(mouse_pos[1]) - int(self._resize_start_mouse[1])

            min_w, min_h = self.min_size
            target_w = max(min_w, int(start_w + dx))
            target_h = max(min_h, int(start_h + dy))

            if bounds_rect is not None:
                max_w = max(min_w, int(bounds_rect.right - self.rect.x))
                max_h = max(min_h, int(bounds_rect.bottom - self.rect.y))
                target_w = min(target_w, max_w)
                target_h = min(target_h, max_h)

            self.rect.w = int(target_w)
            self.rect.h = int(target_h)
            return True

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
            self.draw_resize_grip(surface, mouse_pos)
            return

        bar = self.titlebar_rect()
        if bar.w <= 0 or bar.h <= 0:
            return

        if bar.collidepoint(mouse_pos) or self._dragging:
            alpha = 35 if bar.collidepoint(mouse_pos) else 24
            overlay = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, alpha))
            surface.blit(overlay, (bar.x, bar.y))

        self.draw_resize_grip(surface, mouse_pos)

    def draw_resize_grip(self, surface: pygame.Surface, mouse_pos) -> None:
        grip = self.resize_grip_rect()
        if grip.w <= 0 or grip.h <= 0:
            return

        hovered = mouse_pos is not None and grip.collidepoint(mouse_pos)
        active = self._resizing

        fill = (35, 35, 35) if hovered or active else (25, 25, 25)
        border = (80, 80, 80) if hovered or active else (60, 60, 60)
        pygame.draw.rect(surface, fill, grip, border_radius=3)
        pygame.draw.rect(surface, border, grip, 1, border_radius=3)

        c = (240, 240, 240)
        pad = 3
        pygame.draw.line(surface, c, (grip.right - pad, grip.bottom - pad - 6), (grip.right - pad - 6, grip.bottom - pad), 1)
        pygame.draw.line(surface, c, (grip.right - pad, grip.bottom - pad - 3), (grip.right - pad - 3, grip.bottom - pad), 1)
        pygame.draw.line(surface, c, (grip.right - pad, grip.bottom - pad), (grip.right - pad - 1, grip.bottom - pad - 1), 1)

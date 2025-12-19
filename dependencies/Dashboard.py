import pygame

WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 215, 0)
DARK_GRAY = (30, 30, 30)
BORDER_GRAY = (60, 60, 60)

BTN_BG_COLOR = (40, 40, 40)
BTN_HOVER_COLOR = (60, 60, 60)
BTN_TEXT_COLOR = (240, 240, 240)

class Dashboard:
    def __init__(self, font, font15, font18):
        self.font = font
        self.font15 = font15
        self.font18 = font18
        
        self.speed_unit = "Knots"
        self.ballast_level = 0
        self.signal_strength = 0
        self.speed_value = 0.0
        
        self.width = 370

                                                          
        self.signal_x = 10
        self.signal_y = 310
        self.signal_h = 110

        self.gap = 5
        self.ballast_x = 10
        self.ballast_y = self.signal_y + self.signal_h + self.gap
        self.ballast_h = 110

        self.speed_x = 10
        self.speed_y = self.ballast_y + self.ballast_h + self.gap
        self.speed_h = 110

        self._signal_rect_override: pygame.Rect | None = None
        self._ballast_rect_override: pygame.Rect | None = None
        self._speed_rect_override: pygame.Rect | None = None
        self._speed_switch_rect_override: pygame.Rect | None = None

        self._recalc_layout()

    def set_signal_rect(self, rect: pygame.Rect | None) -> None:
        self._signal_rect_override = rect.copy() if rect is not None else None

    def set_ballast_rect(self, rect: pygame.Rect | None) -> None:
        self._ballast_rect_override = rect.copy() if rect is not None else None

    def set_speed_rect(self, rect: pygame.Rect | None) -> None:
        self._speed_rect_override = rect.copy() if rect is not None else None
        if rect is None:
            self._speed_switch_rect_override = None
            return

        btn_w = min(120, max(80, rect.w // 3))
        btn_h = min(34, max(22, rect.h // 4))
        self._speed_switch_rect_override = pygame.Rect(
            rect.centerx - btn_w // 2,
            rect.bottom - btn_h - max(8, rect.h // 10),
            btn_w,
            btn_h,
        )

    def _recalc_layout(self):
        self.signal_rect = pygame.Rect(self.signal_x, self.signal_y, self.width, self.signal_h)
        self.ballast_rect = pygame.Rect(self.ballast_x, self.ballast_y, self.width, self.ballast_h)
        self.speed_rect = pygame.Rect(self.speed_x, self.speed_y, self.width, self.speed_h)
        self.speed_switch_rect = pygame.Rect(
            self.speed_rect.centerx - 50,
            self.speed_rect.bottom - 40,
            100,
            30,
        )

    def set_signal_position(self, x: int, y: int):
        if self.signal_x == x and self.signal_y == y:
            return
        self.signal_x = x
        self.signal_y = y
        self._recalc_layout()

    def set_ballast_position(self, x: int, y: int):
        if self.ballast_x == x and self.ballast_y == y:
            return
        self.ballast_x = x
        self.ballast_y = y
        self._recalc_layout()

    def set_speed_position(self, x: int, y: int):
        if self.speed_x == x and self.speed_y == y:
            return
        self.speed_x = x
        self.speed_y = y
        self._recalc_layout()

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            active_rect = self._speed_switch_rect_override or self.speed_switch_rect
            if active_rect.collidepoint(mouse_pos):
                self.speed_unit = "Km/h" if self.speed_unit == "Knots" else "Knots"
                return True
        return False

    def update_data(self, speed=None, ballast=None, signal=None):
        if speed is not None: self.speed_value = speed
        if ballast is not None: self.ballast_level = ballast
        if signal is not None: self.signal_strength = signal

    def draw(self, surface, mouse_pos=None):
        self.draw_signal(surface, mouse_pos=mouse_pos)
        self.draw_ballast(surface, mouse_pos=mouse_pos)
        self.draw_speed(surface, mouse_pos=mouse_pos)

    def draw_signal(self, surface, mouse_pos=None):
        rect = self._signal_rect_override or self.signal_rect
        scale = max(0.6, min(2.0, min(rect.w / 370, rect.h / 110)))
        pygame.draw.rect(surface, DARK_GRAY, rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, rect, 1, border_radius=8)

        pad_x = max(10, rect.w // 18)
        pad_y = max(8, rect.h // 12)
        title_surf = self.font15.render("SIGNAL STRENGTH", True, WHITE)
        if scale != 1.0:
            title_surf = pygame.transform.smoothscale(
                title_surf,
                (max(1, int(title_surf.get_width() * scale)), max(1, int(title_surf.get_height() * scale))),
            )
        surface.blit(title_surf, (rect.x + pad_x, rect.y + pad_y))

        pct_surf = self.font15.render(f"{int(self.signal_strength)}%", True, WHITE)
        if scale != 1.0:
            pct_surf = pygame.transform.smoothscale(
                pct_surf,
                (max(1, int(pct_surf.get_width() * scale)), max(1, int(pct_surf.get_height() * scale))),
            )
        surface.blit(pct_surf, (rect.right - pct_surf.get_width() - pad_x, rect.y + pad_y))

        n = 5
        bar_area_y = rect.y + pad_y + title_surf.get_height() + max(6, rect.h // 10)
        bar_h = min(32, max(18, rect.h // 3))
        bar_w_total = max(0, rect.w - pad_x * 2)
        gap = max(4, bar_w_total // 40)
        bar_w = max(8, (bar_w_total - gap * (n - 1)) // n) if n > 0 else 0
        filled = int(self.signal_strength // 20)

        for i in range(n):
            color = GREEN if i < filled else (50, 50, 50)
            bx = rect.x + pad_x + i * (bar_w + gap)
            by = bar_area_y
            pygame.draw.rect(surface, color, (bx, by, bar_w, bar_h), border_radius=3)

    def draw_ballast(self, surface, mouse_pos=None):
        rect = self._ballast_rect_override or self.ballast_rect
        scale = max(0.6, min(2.0, min(rect.w / 370, rect.h / 110)))
        pygame.draw.rect(surface, DARK_GRAY, rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, rect, 1, border_radius=8)

        pad_x = max(10, rect.w // 18)
        pad_y = max(8, rect.h // 12)
        title_surf = self.font15.render("BALLAST", True, WHITE)
        if scale != 1.0:
            title_surf = pygame.transform.smoothscale(
                title_surf,
                (max(1, int(title_surf.get_width() * scale)), max(1, int(title_surf.get_height() * scale))),
            )
        surface.blit(title_surf, (rect.x + pad_x, rect.y + pad_y))

        pct_surf = self.font15.render(f"{int(self.ballast_level)}%", True, WHITE)
        if scale != 1.0:
            pct_surf = pygame.transform.smoothscale(
                pct_surf,
                (max(1, int(pct_surf.get_width() * scale)), max(1, int(pct_surf.get_height() * scale))),
            )
        surface.blit(pct_surf, (rect.right - pct_surf.get_width() - pad_x, rect.y + pad_y))

        bar_y = rect.y + pad_y + title_surf.get_height() + max(6, rect.h // 10)
        bar_h = min(22, max(14, rect.h // 4))
        bar_w = max(20, rect.w - pad_x * 2)
        bg_bar = pygame.Rect(rect.x + pad_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (50, 50, 50), bg_bar, border_radius=5)

        fill_w = int(bg_bar.w * (self.ballast_level / 100))
        fg_bar = pygame.Rect(bg_bar.x, bg_bar.y, max(0, fill_w), bg_bar.h)
        pygame.draw.rect(surface, BLUE, fg_bar, border_radius=5)

    def draw_speed(self, surface, mouse_pos=None):
        rect = self._speed_rect_override or self.speed_rect
        speed_switch_rect = self._speed_switch_rect_override or self.speed_switch_rect
        scale = max(0.6, min(2.0, min(rect.w / 370, rect.h / 110)))

        pygame.draw.rect(surface, DARK_GRAY, rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_GRAY, rect, 1, border_radius=8)

        pad_x = max(10, rect.w // 18)
        pad_y = max(8, rect.h // 12)
        title_surf = self.font15.render("SPEED", True, WHITE)
        if scale != 1.0:
            title_surf = pygame.transform.smoothscale(
                title_surf,
                (max(1, int(title_surf.get_width() * scale)), max(1, int(title_surf.get_height() * scale))),
            )
        surface.blit(title_surf, (rect.x + pad_x, rect.y + pad_y))

        display_speed = self.speed_value
        if self.speed_unit == "Km/h":
            display_speed *= 1.852

        speed_text = self.font.render(f"{display_speed:.1f}", True, YELLOW)
        num_scale = 1.5 * scale
        if num_scale != 1.0:
            speed_text = pygame.transform.smoothscale(
                speed_text,
                (max(1, int(speed_text.get_width() * num_scale)), max(1, int(speed_text.get_height() * num_scale))),
            )
        surface.blit(speed_text, (rect.centerx - speed_text.get_width()//2, rect.centery - int(25 * scale)))

        is_hovered = mouse_pos and speed_switch_rect.collidepoint(mouse_pos)
        btn_color = BTN_HOVER_COLOR if is_hovered else BTN_BG_COLOR

        pygame.draw.rect(surface, btn_color, speed_switch_rect, border_radius=5)
        if is_hovered:
            pygame.draw.rect(surface, BORDER_GRAY, speed_switch_rect, 1, border_radius=5)

        unit_text = self.font15.render(self.speed_unit, True, BTN_TEXT_COLOR)
        if scale != 1.0:
            unit_text = pygame.transform.smoothscale(
                unit_text,
                (max(1, int(unit_text.get_width() * scale)), max(1, int(unit_text.get_height() * scale))),
            )
        surface.blit(unit_text, (speed_switch_rect.centerx - unit_text.get_width()//2, speed_switch_rect.centery - unit_text.get_height()//2))

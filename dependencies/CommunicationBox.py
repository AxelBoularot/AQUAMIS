import pygame
import random

from dependencies.Variable import BLACK, CARD_BG, GRAY


def _clamp(v: int, lo: int, hi: int) -> int:
    return lo if v < lo else hi if v > hi else v


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )
class CommunicationBox(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, font, text_color, ok_color, not_ok_color, text):
        super().__init__()
        self.ok_color = ok_color
        self.not_ok_color = not_ok_color

        self.image_normal = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image_error = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image = self.image_normal.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.font = font
        self.text_color = text_color
        self.communication_ok = True
        self.text = text
        self._draw_text()

    def _draw_text(self):
        w, h = self.image.get_width(), self.image.get_height()
        self.image.fill((0, 0, 0, 0))

        pad = 6
        radius = 8
        panel = pygame.Rect(0, 0, w, h)

        pygame.draw.rect(self.image, BLACK, panel, border_radius=radius)
        pygame.draw.rect(self.image, GRAY, panel, 1, border_radius=radius)

        base_text = self.text.split(":")[0].strip() if ":" in self.text else self.text.strip()
        is_on = bool(self.communication_ok)
        state_text = "ON" if is_on else "OFF"
        accent = self.ok_color if is_on else self.not_ok_color

        label_surf = self.font.render(base_text, True, self.text_color)
        state_surf = self.font.render(state_text, True, accent)

        switch_w = max(34, int(w * 0.28))
        switch_rect = pygame.Rect(pad, pad, switch_w, h - 2 * pad)

        housing_radius = 6
        pygame.draw.rect(self.image, CARD_BG, switch_rect, border_radius=housing_radius)
        pygame.draw.rect(self.image, GRAY, switch_rect, 1, border_radius=housing_radius)

        led_r = max(3, int(min(switch_rect.w, switch_rect.h) * 0.11))
        led_cx = switch_rect.centerx
        led_cy = switch_rect.y + led_r + 4
        pygame.draw.circle(self.image, accent, (led_cx, led_cy), led_r)
        pygame.draw.circle(self.image, BLACK, (led_cx, led_cy), led_r, 1)

        slot_pad = 5
        slot_rect = pygame.Rect(
            switch_rect.x + slot_pad,
            switch_rect.y + slot_pad + 10,
            switch_rect.w - 2 * slot_pad,
            switch_rect.h - 2 * slot_pad - 14,
        )
        pygame.draw.rect(self.image, BLACK, slot_rect, border_radius=4)
        pygame.draw.rect(self.image, GRAY, slot_rect, 1, border_radius=4)

        lever_h = max(14, int(slot_rect.h * 0.38))
        lever_w = slot_rect.w - 6
        lever_x = slot_rect.x + (slot_rect.w - lever_w) // 2
        if is_on:
            lever_y = slot_rect.y + 4
        else:
            lever_y = slot_rect.bottom - lever_h - 4
        lever_rect = pygame.Rect(lever_x, lever_y, lever_w, lever_h)

        lever_top = _mix(accent, (255, 255, 255), 0.35)
        lever_bot = _mix(accent, BLACK, 0.25)
        pygame.draw.rect(self.image, lever_bot, lever_rect, border_radius=4)
        pygame.draw.rect(self.image, lever_top, lever_rect.inflate(-2, -2), border_radius=3)
        pygame.draw.rect(self.image, BLACK, lever_rect, 1, border_radius=4)

        text_x = switch_rect.right + 8
        text_area_w = max(0, w - text_x - pad)

        if label_surf.get_width() > text_area_w and text_area_w > 0:
            clipped = pygame.Surface((text_area_w, label_surf.get_height()), pygame.SRCALPHA)
            clipped.blit(label_surf, (0, 0))
            label_surf = clipped

        if state_surf.get_width() > text_area_w and text_area_w > 0:
            clipped = pygame.Surface((text_area_w, state_surf.get_height()), pygame.SRCALPHA)
            clipped.blit(state_surf, (0, 0))
            state_surf = clipped

        label_y = pad + 2
        state_y = h - pad - state_surf.get_height() - 2
        self.image.blit(label_surf, (text_x, label_y))
        self.image.blit(state_surf, (text_x, state_y))

    def update_status(self):
        self.set_ok(random.choice([True, False]))

    def set_ok(self, ok: bool) -> None:
        self.communication_ok = bool(ok)
        base_text = self.text.split(':')[0]
        self.text = f"{base_text}: OK" if self.communication_ok else f"{base_text}: Not OK"
        self.image = self.image_normal.copy() if self.communication_ok else self.image_error.copy()
        self._draw_text()

    def toggle_ok(self) -> None:
        self.set_ok(not bool(self.communication_ok))

    def update(self, mouse_pos):
        pass 
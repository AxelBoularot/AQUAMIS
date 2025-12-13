import pygame
import math

class KeyCluster:
    def __init__(self, base_width, base_height, font, lift=40):
        # two rows: row1 AZE, row2 QSD
        labels_row1 = ["A", "Z", "E"]
        labels_row2 = ["Q", "S", "D"]
        self.key_map = {
            "A": pygame.K_a, "Z": pygame.K_z, "E": pygame.K_e,
            "Q": pygame.K_q, "S": pygame.K_s, "D": pygame.K_d
        }
        # visual layout
        btn_w, btn_h = 70, 54
        gap = 12
        # row1 (moved up by lift)
        total_w_row1 = len(labels_row1) * btn_w + (len(labels_row1) - 1) * gap
        start_x_row1 = base_width // 2 - total_w_row1 // 2
        y_row1 = base_height - 120 - lift
        # row2 (centered under row1)
        total_w_row2 = len(labels_row2) * btn_w + (len(labels_row2) - 1) * gap
        start_x_row2 = base_width // 2 - total_w_row2 // 2
        y_row2 = base_height - 48 - lift

        self.font = font
        self.buttons = {}
        for i, lab in enumerate(labels_row1):
            x = start_x_row1 + i * (btn_w + gap)
            self.buttons[lab] = {"rect": pygame.Rect(x, y_row1, btn_w, btn_h), "pressed": False, "label": lab}
        for i, lab in enumerate(labels_row2):
            x = start_x_row2 + i * (btn_w + gap)
            self.buttons[lab] = {"rect": pygame.Rect(x, y_row2, btn_w, btn_h), "pressed": False, "label": lab}

    def handle_event(self, event):
        # keyboard press/release
        if event.type == pygame.KEYDOWN:
            for lab, kc in self.key_map.items():
                if event.key == kc:
                    self.buttons[lab]["pressed"] = True
        elif event.type == pygame.KEYUP:
            for lab, kc in self.key_map.items():
                if event.key == kc:
                    self.buttons[lab]["pressed"] = False
        # optional: allow clicking with mouse to toggle visual state (does not send keys)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for info in self.buttons.values():
                if info["rect"].collidepoint(pos):
                    info["pressed"] = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = event.pos
            for info in self.buttons.values():
                if info["rect"].collidepoint(pos):
                    info["pressed"] = False

    def draw(self, surface):
        for info in self.buttons.values():
            r = info["rect"]
            pressed = info["pressed"]
            # light shadow
            shadow_rect = r.move(3, 3)
            pygame.draw.rect(surface, (8,8,8), shadow_rect, border_radius=10)
            # outline only: white when pressed else gray
            if pressed:
                border_color = (255,255,255)
                border_w = 4
                label_color = (255,255,255)
            else:
                border_color = (110,110,110)
                border_w = 2
                label_color = (220,220,220)
            pygame.draw.rect(surface, border_color, r, border_w, border_radius=10)
            # centered label
            lbl = self.font.render(info["label"], True, label_color)
            surface.blit(lbl, lbl.get_rect(center=r.center))
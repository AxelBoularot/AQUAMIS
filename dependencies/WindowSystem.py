from __future__ import annotations

import pygame

from dependencies.DraggableWindow import DraggableWindow


class WindowSystem:
       

    def __init__(self, font15, menu_bar):
        self.font15 = font15
        self.menu_bar = menu_bar

                                     
        self.windows: dict[str, dict] = {}

                                               
        self.z_order: list[str] = []

                             
        self.default_layout: dict[str, tuple[int, int, int, int]] = {}

                                                               
        self.default_minimized: dict[str, bool] = {}

                                           
        self.taskbar_buttons: list[tuple[pygame.Rect, str]] = []
        self.status_buttons: list[tuple[pygame.Rect, str]] = []

    def add_window(self, key: str, win: DraggableWindow, *, kind: str = "generic", start_minimized: bool = False) -> None:
        self.windows[key] = {"win": win, "min": bool(start_minimized), "kind": kind}
        if key not in self.default_minimized:
            self.default_minimized[key] = bool(start_minimized)
        if key not in self.z_order:
            self.z_order.append(key)

    def set_default_minimized(self, key: str, minimized: bool) -> None:
        self.default_minimized[key] = bool(minimized)
        if key in self.windows:
            self.windows[key]["min"] = bool(minimized)

    def set_minimized(self, key: str, minimized: bool) -> None:
        if key in self.windows:
            self.windows[key]["min"] = bool(minimized)

    def bring_to_front(self, key: str) -> None:
        if key not in self.z_order:
            return
        self.z_order.remove(key)
        self.z_order.append(key)

    def handle_focus_click(self, mouse_pos_virtual) -> bool:
                                                                           
        if mouse_pos_virtual is None:
            return False
        for key in reversed(self.z_order):
            meta = self.windows.get(key)
            if not meta or meta["min"]:
                continue
            if meta["win"].rect.collidepoint(mouse_pos_virtual):
                self.bring_to_front(key)
                return True
        return False

    def set_default_layout(self, key: str, rect_tuple: tuple[int, int, int, int]) -> None:
        self.default_layout[key] = rect_tuple

    def reset_layout(self) -> None:
        for key, rect_tuple in self.default_layout.items():
            if key in self.windows:
                self.windows[key]["win"].rect.update(*rect_tuple)
        for key, meta in self.windows.items():
            meta["min"] = bool(self.default_minimized.get(key, False))

    def is_minimized(self, key: str) -> bool:
        return bool(self.windows[key]["min"])

    def _minimize_button_rect(self, win: DraggableWindow) -> pygame.Rect:
        bar = win.titlebar_rect()
        size = max(10, bar.h)
        return pygame.Rect(bar.right - size - 2, bar.y, size, bar.h)

    def draw_minimize_button(self, surface: pygame.Surface, win: DraggableWindow, mouse_pos_virtual) -> None:
        btn = self._minimize_button_rect(win)
        if btn.w <= 0 or btn.h <= 0:
            return
        hovered = mouse_pos_virtual is not None and btn.collidepoint(mouse_pos_virtual)
        fill = (35, 35, 35) if hovered else (25, 25, 25)
        pygame.draw.rect(surface, fill, btn, border_radius=4)
        pygame.draw.rect(surface, (60, 60, 60), btn, 1, border_radius=4)
        y = btn.centery
        pygame.draw.line(surface, (240, 240, 240), (btn.x + 3, y), (btn.right - 3, y), 2)

    def handle_minimize_click(self, mouse_pos_virtual) -> bool:
                                                                   
        if mouse_pos_virtual is None:
            return False
        for key in reversed(self.z_order):
            meta = self.windows.get(key)
            if not meta or meta["min"]:
                continue
            btn = self._minimize_button_rect(meta["win"])
            if btn.collidepoint(mouse_pos_virtual):
                meta["min"] = True
                return True
        return False

    def handle_drag_event(self, event, mouse_pos_virtual, *, bounds_size=None, bounds_rect: pygame.Rect | None = None) -> bool:
                                                        
        if mouse_pos_virtual is None:
            return False
        for key in reversed(self.z_order):
            meta = self.windows.get(key)
            if not meta or meta["min"]:
                continue
            if meta["win"].handle_event(event, mouse_pos_virtual, bounds_size=bounds_size, bounds_rect=bounds_rect):
                                                                               
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.bring_to_front(key)
                return True
        return False

    def handle_restore_click(self, mouse_pos_real) -> bool:
                                                                 
        for rect, key in self.taskbar_buttons + self.status_buttons:
            if rect.collidepoint(mouse_pos_real) and key in self.windows:
                self.windows[key]["min"] = False
                self.bring_to_front(key)
                return True
        return False

    def draw_topbars(
        self,
        screen: pygame.Surface,
        *,
        mode_x: int,
        mode_y: int,
        mode_h: int,
        status_drawers: dict[str, callable] | None = None,
    ) -> None:
           
        if status_drawers is None:
            status_drawers = {}

        self.taskbar_buttons = []
        self.status_buttons = []

        y = self.menu_bar.bar_margin_top
        h = self.menu_bar.bar_height

        left_limit = self.menu_bar.bar_margin_left + self.menu_bar.bar_width + 10
        right_limit = mode_x - 10
        available_w = max(0, right_limit - left_limit)

                                                                        
        status_order = [
            "Battery",
            "Speed",
            "Ballast",
            "Signal",
            "PressureDepth",
            "Temp",
        ]
        status_items = [
            k
            for k in status_order
            if k in self.windows and self.windows[k]["min"] and self.windows[k].get("kind") == "status"
        ]
                                                           
        for k, meta in self.windows.items():
            if meta.get("kind") == "status" and meta["min"] and k not in status_items:
                status_items.append(k)

                                                                                       
        status_widths = {
            "Signal": 54,
            "Ballast": 70,
            "Speed": 76,
            "Battery": 70,
            "PressureDepth": 110,
            "Temp": 80,
        }
        gap = 6

        x = right_limit
        for key in status_items:
            w = status_widths.get(key, 70)
            rect = pygame.Rect(x - w, y, w, h)
            if rect.x < left_limit:
                break
            pygame.draw.rect(screen, (25, 25, 25), rect, border_radius=8)
            pygame.draw.rect(screen, (60, 60, 60), rect, 1, border_radius=8)

            drawer = status_drawers.get(key)
            if drawer is not None:
                drawer(screen, rect)
            else:
                text = self.font15.render(key, True, (240, 240, 240))
                screen.blit(text, (rect.x + 8, rect.centery - text.get_height() // 2))

            self.status_buttons.append((rect, key))
            x = rect.x - gap

                                                                   
        def _ellipsize(text: str, max_px: int) -> str:
            if max_px <= 0:
                return ""
            if self.font15.size(text)[0] <= max_px:
                return text
                                  
            ell = "…"
            lo, hi = 0, len(text)
            best = ell
            while lo <= hi:
                mid = (lo + hi) // 2
                cand = text[:mid] + ell
                if self.font15.size(cand)[0] <= max_px:
                    best = cand
                    lo = mid + 1
                else:
                    hi = mid - 1
            return best

        generic_items = []
        for key, meta in self.windows.items():
            if meta["min"] and meta.get("kind") != "status":
                generic_items.append(key)

        generic_gap = 6

                                                                                                      
        right_block_limit = x - 10                                         
        generic_right_limit = max(left_limit, min(right_limit, right_block_limit))
        generic_available = max(0, generic_right_limit - left_limit)

        if not generic_items:
            return

                                                               
        n = len(generic_items)
        max_w = 180
        min_w = 70
        base_ws = []
        for key in generic_items:
            text_w = self.font15.size(key)[0]
            base_ws.append(min(max_w, text_w + 26))

        total_base = sum(base_ws) + generic_gap * max(0, n - 1)
        if total_base <= generic_available:
            widths = base_ws
        else:
                                  
            uniform = (generic_available - generic_gap * max(0, n - 1)) // max(1, n)
            uniform = max(min_w, int(uniform))
            widths = [min(max_w, uniform) for _ in generic_items]

        total_w = sum(widths) + generic_gap * max(0, n - 1)
        gx = left_limit + max(0, (generic_available - total_w) // 2)

        for key, w in zip(generic_items, widths):
            if gx + w > generic_right_limit:
                break
            rect = pygame.Rect(gx, y, w, h)
            pygame.draw.rect(screen, (25, 25, 25), rect, border_radius=8)
            pygame.draw.rect(screen, (60, 60, 60), rect, 1, border_radius=8)

            label = _ellipsize(key, max(0, rect.w - 24))
            text = self.font15.render(label, True, (240, 240, 240))
            screen.blit(text, (rect.x + 12, rect.centery - text.get_height() // 2))
            self.taskbar_buttons.append((rect, key))
            gx += w + generic_gap

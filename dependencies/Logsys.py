from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import pygame

                   
WHITE = (240, 240, 240)
BLUE = (100, 149, 237)
YELLOW = (255, 215, 0)
RED = (220, 20, 60)
BG_COLOR = (25, 25, 25)
SCROLLBAR_BG = (40, 40, 40)
SCROLLBAR_THUMB = (80, 80, 80)
SCROLLBAR_THUMB_HOVER = (100, 100, 100)


@dataclass(frozen=True)
class _LogEntry:
    timestamp: str
    message: str
    color: tuple[int, int, int]
    levelno: int


def _parse_level(level: int | str) -> int:
    if isinstance(level, int):
        return int(level)
    s = str(level).strip()
    if not s:
        return logging.INFO

    name = s.upper()
    if name in ("WARN",):
        name = "WARNING"

    if name in logging._nameToLevel:
        return int(logging._nameToLevel[name])

    legacy = s.lower()
    if legacy == "info":
        return logging.INFO
    if legacy == "warning":
        return logging.WARNING
    if legacy == "error":
        return logging.ERROR
    if legacy == "debug":
        return logging.DEBUG
    if legacy == "critical":
        return logging.CRITICAL

    return logging.INFO


def _level_color(levelno: int) -> tuple[int, int, int]:
    if levelno >= logging.ERROR:
        return RED
    if levelno >= logging.WARNING:
        return YELLOW
    if levelno >= logging.INFO:
        return BLUE
    return WHITE


class UILogHandler(logging.Handler):
    def __init__(self, log_system: "LogSystem"):
        super().__init__(level=logging.DEBUG)
        self._log_system = log_system

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            self._log_system.add_record(int(record.levelno), msg, timestamp=ts)
        except Exception:
            self.handleError(record)

class LogSystem:
    def __init__(self, font, max_logs=100):
        self.font = font
        self.max_logs = max_logs
        self.logs: list[_LogEntry] = []

        self.min_level = logging.INFO
        
        self.scroll_y = 0
        self.max_scroll = 0
        self.viewport_height = 0
        self.content_height = 0
        self.is_dragging = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0
        
        self.padding = 10
        self.line_spacing = 4
        self.line_height = self.font.get_height() + self.line_spacing
        
        self.surface_cache = None
        self.needs_redraw = True

    def set_min_level(self, level: int | str) -> None:
        self.min_level = _parse_level(level)
        self.needs_redraw = True
        self._recalculate_layout()
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

    def get_min_level_name(self) -> str:
        return logging.getLevelName(self.min_level)

    def add_log(self, message, level="info"):
        levelno = _parse_level(level)
        self.add_record(levelno, str(message))

    def add_record(self, levelno: int, message: str, *, timestamp: str | None = None) -> None:
        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        color = _level_color(levelno)
        self.logs.append(_LogEntry(ts, message, color, levelno))
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

        self.needs_redraw = True
        self._recalculate_layout()
        self.scroll_y = self.max_scroll

    def _filtered_logs(self) -> list[_LogEntry]:
        if self.min_level <= logging.DEBUG:
            return self.logs
        return [e for e in self.logs if e.levelno >= self.min_level]

    def _recalculate_layout(self):
        self.content_height = len(self._filtered_logs()) * self.line_height + self.padding * 2
        if self.viewport_height > 0:
            self.max_scroll = max(0, self.content_height - self.viewport_height)
        else:
            self.max_scroll = 0

    def handle_event(self, event, rect, mouse_pos=None):
        current_pos = mouse_pos if mouse_pos else pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEWHEEL:
            if rect.collidepoint(current_pos):
                self.scroll_y -= event.y * 20
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                thumb_rect = self._get_scrollbar_rect(rect)
                if thumb_rect and thumb_rect.collidepoint(current_pos):
                    self.is_dragging = True
                    self.drag_start_y = current_pos[1]
                    self.drag_start_scroll = self.scroll_y
                    return True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                delta_y = current_pos[1] - self.drag_start_y
                
                track_height = rect.height - 4
                if self.content_height > rect.height:
                    thumb_height = max(20, (rect.height / self.content_height) * track_height)
                    scrollable_track = track_height - thumb_height
                    if scrollable_track > 0:
                        scroll_ratio = delta_y / scrollable_track
                        self.scroll_y = self.drag_start_scroll + (scroll_ratio * self.max_scroll)
                        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

    def _get_scrollbar_rect(self, viewport_rect):
        if self.content_height <= viewport_rect.height:
            return None
            
        track_height = viewport_rect.height - 4
        thumb_height = max(20, (viewport_rect.height / self.content_height) * track_height)
        
        scroll_ratio = self.scroll_y / self.max_scroll if self.max_scroll > 0 else 0
        thumb_y = viewport_rect.y + 2 + (scroll_ratio * (track_height - thumb_height))
        
        return pygame.Rect(viewport_rect.right - 12, thumb_y, 8, thumb_height)

    def draw(self, surface, x, y, width, height, mouse_pos=None):
        self.viewport_height = height
        self._recalculate_layout()
        
        viewport_rect = pygame.Rect(x, y, width, height)
        current_pos = mouse_pos if mouse_pos else pygame.mouse.get_pos()
        
                       
        pygame.draw.rect(surface, BG_COLOR, viewport_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 60, 60), viewport_rect, 1, border_radius=8)
        
                             
                                             
        old_clip = surface.get_clip()
        surface.set_clip(viewport_rect.inflate(-4, -4))          
        
        start_y = y + self.padding - self.scroll_y

        logs_to_draw = self._filtered_logs()
        for i, entry in enumerate(logs_to_draw):
            line_y = start_y + (i * self.line_height)
            
                                                   
            if line_y + self.line_height < y or line_y > y + height:
                continue
                
            text = f"[{entry.timestamp}] {entry.message}"
            text_surf = self.font.render(text, True, entry.color)
            surface.blit(text_surf, (x + 10, line_y))
            
        surface.set_clip(old_clip)
        
                      
        thumb_rect = self._get_scrollbar_rect(viewport_rect)
        if thumb_rect:
                   
            track_rect = pygame.Rect(viewport_rect.right - 14, viewport_rect.y + 2, 12, height - 4)
            pygame.draw.rect(surface, SCROLLBAR_BG, track_rect, border_radius=6)
            
                   
            color = SCROLLBAR_THUMB_HOVER if self.is_dragging or thumb_rect.collidepoint(current_pos) else SCROLLBAR_THUMB
            pygame.draw.rect(surface, color, thumb_rect, border_radius=4)

                                 
                                                                             
                                                    

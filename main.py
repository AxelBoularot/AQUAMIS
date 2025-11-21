import pygame, math, random, time, dependencies.Cube as Cube, sys
from dependencies.Password import Special_button
from dependencies.progress_bar import ProgressBar
from dependencies.Graph_Pressure_Depth import Graphs_Main
from dependencies.Graph_Angles import Graphs_Angles
from dependencies.lib_backend import VideoReceiver, DataHandler, SocketClient
import numpy as np
import tkinter as tk
import json
import pandas as pd
from tkinter import filedialog
import cv2
import os
import threading
import subprocess
from ultralytics import YOLO
import torch
import face_recognition
import re
print("CUDA available:", torch.cuda.is_available())

#lancement de la fonctionnalité de face recognition
# video_capture.set(5,1)
known_face_encodings = []
known_face_names = []
known_faces_filenames = []
for (dirpath, dirnames, filenames) in os.walk('test_folder/assets/'):
    known_faces_filenames.extend(filenames)
    break
for filename in known_faces_filenames:
    face = face_recognition.load_image_file('test_folder/assets/' + filename)
    known_face_names.append(re.sub("[0-9]",'', filename[:-4]))
    known_face_encodings.append(face_recognition.face_encodings(face)[0])
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

id_person = {}
# Detect device and load the YOLO11 model onto the appropriate device
# Force CPU - RTX 5070 sm_120 architecture not supported yet
device = "cpu"
print(f"Using device: {device}")
# Load the YOLO11 model
model = YOLO("object_detection_lib/yolo11n.pt").to(device)

# Utility: crop and save detected person images with tracking IDs
def save_person_crops(frame_bgr, results, save_dir="detected_persons", max_per_frame=10):
    """Crop person detections from a BGR frame using YOLO `results` and save them.
    Filenames include the class label (usually 'person'), track id if present and a timestamp.
    """
    try:
        os.makedirs(save_dir, exist_ok=True)
    except Exception:
        return

    if results is None or len(results) == 0:
        return

    r = results[0]
    boxes = getattr(r, 'boxes', None)
    if boxes is None:
        return

    # Try to obtain arrays of xyxy, cls and ids in a few different ways
    try:
        xyxy = boxes.xyxy.cpu().numpy()
    except Exception:
        try:
            xyxy = boxes.xyxy.numpy()
        except Exception:
            # Fallback: try to read .xyxy attribute directly
            xyxy = getattr(boxes, 'xyxy', None)
    if xyxy is None:
        return

    # class indices (if available)
    cls_array = None
    try:
        cls_array = boxes.cls.cpu().numpy()
    except Exception:
        try:
            cls_array = boxes.cls.numpy()
        except Exception:
            cls_array = None

    # track ids (if available)
    ids = None
    if hasattr(boxes, 'id'):
        try:
            ids = boxes.id.cpu().numpy()
        except Exception:
            try:
                ids = boxes.id.numpy()
            except Exception:
                ids = None

    # Determine the person class index from model.names if possible
    person_class_index = None
    try:
        for k, v in model.names.items():
            if str(v).lower() == 'person':
                person_class_index = int(k)
                break
    except Exception:
        person_class_index = None

    saved = 0
    for i, box in enumerate(xyxy):
        if saved >= max_per_frame:
            break
        try:
            x1, y1, x2, y2 = map(int, box[:4])
        except Exception:
            continue

        # check cls if present: only keep 'person'
        if cls_array is not None and person_class_index is not None:
            try:
                if int(cls_array[i]) != person_class_index:
                    continue
            except Exception:
                pass

        # otherwise try to infer label via model.names and boxes.cls when available
        label = 'object'
        try:
            if cls_array is not None and hasattr(model, 'names'):
                label = str(model.names.get(int(cls_array[i]), 'object'))
        except Exception:
            label = 'object'

        track_id = None
        if ids is not None:
            try:
                track_id = int(ids[i])
            except Exception:
                track_id = None

        crop = frame_bgr[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
        if crop is None or crop.size == 0:
            continue

        ts = int(time.time())
        id_part = f"_id{track_id}" if track_id is not None else ""
        filename = f"{label}{id_part}_{ts}_{i}.jpg"
        out_path = os.path.join(save_dir, filename)
        try:
            cv2.imwrite(out_path, crop)
            saved += 1
        except Exception:
            continue

# Open the video file
#D:/Videos/WIN_20241015_08_21_58_Pro.mp4


USE_PHONE_SENSORS = False  # Défini par l'interface de démarrage

# IP du téléphone (définie par l'utilisateur dans l'interface)
PHONE_IP = "192.168.1.100"

# URL du flux vidéo du téléphone (ex: IP Webcam sur Android)
# Format: http://IP_DU_TELEPHONE:PORT/video
# Avec IP Webcam: http://192.168.1.100:8080/video (ou /videofeed)
PHONE_VIDEO_URL = "http://192.168.1.100:8080/videofeed"

# Fichier JSON contenant les données des capteurs du téléphone
# Généré par phone_sensor.py
SENSOR_DATA_FILE = "sensor_data.json"


# Global variables for phone video stream
phone_video_frame = None
phone_video_lock = threading.Lock()

def phone_video_stream_worker(url):
    """Worker function to capture video from phone in a separate thread."""
    global phone_video_frame
    cap = None
    print(f"📱 Démarrage du thread pour le flux vidéo du téléphone depuis: {url}")
    while True: # Boucle pour gérer la reconnexion
        try:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                print(f"❌ ERREUR: Impossible d'ouvrir le flux vidéo depuis {url}. Nouvelle tentative dans 5s.")
                time.sleep(5)
                continue

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ Avertissement: Image non reçue. Le flux est peut-être terminé. Tentative de reconnexion...")
                    break # Sortir pour tenter de se reconnecter

                with phone_video_lock:
                    phone_video_frame = frame
        except Exception as e:
            print(f"❌ Erreur dans le thread vidéo: {e}")
        finally:
            if cap:
                cap.release()
            print("Flux vidéo arrêté. Tentative de reconnexion dans 5 secondes.")
            time.sleep(5)


# ============================================================
# Initialisation de Pygame
# ============================================================

# Pygame's initialization - AMIS' LOGO - Interface's name

pygame.init()
pygame.display.set_caption("AQUAMIS' Interface of Control")
logo = pygame.image.load("picture/Logo_AMIS.png")
pygame.display.set_icon(logo)

# Resolution and scaling system
BASE_WIDTH = 1500
BASE_HEIGHT = 750

def get_scaling_factors(screen):
    """Calculate scaling factors based on current window size"""
    current_width, current_height = screen.get_size()
    scale_x = current_width / BASE_WIDTH
    scale_y = current_height / BASE_HEIGHT
    return scale_x, scale_y

def scale_pos(x, y, scale_x, scale_y):
    """Scale a position based on scaling factors"""
    return int(x * scale_x), int(y * scale_y)

def scale_size(width, height, scale_x, scale_y):
    """Scale dimensions based on scaling factors"""
    return int(width * scale_x), int(height * scale_y)

def convert_mouse_pos(mouse_pos, screen):
    """Convert mouse position from actual screen to virtual screen coordinates"""
    current_size = screen.get_size()
    if current_size == (BASE_WIDTH, BASE_HEIGHT):
        return mouse_pos
    
    scale_x = current_size[0] / BASE_WIDTH
    scale_y = current_size[1] / BASE_HEIGHT
    scale = min(scale_x, scale_y)
    
    new_width = int(BASE_WIDTH * scale)
    new_height = int(BASE_HEIGHT * scale)
    
    x_offset = (current_size[0] - new_width) // 2
    y_offset = (current_size[1] - new_height) // 2
    
    # Convert to virtual coordinates
    virtual_x = int((mouse_pos[0] - x_offset) / scale)
    virtual_y = int((mouse_pos[1] - y_offset) / scale)
    
    # Clamp to virtual screen bounds
    virtual_x = max(0, min(BASE_WIDTH - 1, virtual_x))
    virtual_y = max(0, min(BASE_HEIGHT - 1, virtual_y))
    
    return (virtual_x, virtual_y)

"""Brand palette & typography helpers (IPSA / AMIS guideline)"""
# Primary brand colors
PRIMARY_BLUE = (0x00, 0x5A, 0x9C)   # #005A9C Bleu foncé IPSA
LIGHT_BLUE   = (0x46, 0xB3, 0xE6)   # #46B3E6 Bleu clair AMIS
WHITE        = (0xFF, 0xFF, 0xFF)   # Blanc principal

# Supporting neutrals & semantic colors
NEUTRAL_LIGHT = (245, 247, 250)
NEUTRAL_BORDER = (215, 222, 230)
NEUTRAL_TEXT = (40, 55, 70)
NEUTRAL_SECONDARY = (95, 115, 135)
ERROR = (220, 60, 60)
WARNING = (250, 170, 40)
SUCCESS = (30, 150, 95)

# Mapped legacy names (maintain compatibility)
BLUE = PRIMARY_BLUE
YELLOW = WARNING
RED = ERROR
GREEN = SUCCESS
BLACK = (10, 20, 30)  # Used sparingly for shadows / outlines
GRAY = NEUTRAL_BORDER
TEXT_PRIMARY = NEUTRAL_TEXT
TEXT_SECONDARY = NEUTRAL_SECONDARY
TEXT_MUTED = (140, 155, 170)

# Card / surfaces
CARD_BG = WHITE
SURFACE = NEUTRAL_LIGHT

# Button pressed color (slightly darker primary)
BCP = (0, 74, 124)

def load_brand_font(size:int, bold:bool=False):
    """Try loading Century Schoolbook or fallback; fallback to default system font.
    Pygame relies on system-installed fonts; if unavailable, it will fallback.
    """
    preferred = [
        ("Century Schoolbook", bold),
        ("Montserrat", bold),
        ("Roboto", bold),
        ("Arial", bold),
        (None, bold)  # pygame default
    ]
    for name, b in preferred:
        try:
            return pygame.font.SysFont(name, size, bold=b)
        except Exception:
            continue
    return pygame.font.SysFont(None, size, bold=bold)

# Animation helpers
def ease_in_out_cubic(t):
    """Easing function pour animations smooth"""
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_out_elastic(t):
    """Easing élastique pour effet de rebond"""
    c4 = (2 * math.pi) / 3
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def lerp(start, end, t):
    """Linear interpolation entre deux valeurs"""
    return start + (end - start) * t

def lerp_color(color1, color2, t):
    """Interpolation entre deux couleurs"""
    return tuple(int(lerp(c1, c2, t)) for c1, c2 in zip(color1, color2))

    # Classes modernes pour l'interface

    class ModernButton(pygame.sprite.Sprite):
        """Bouton moderne avec glassmorphism et animations"""
        def __init__(self, x, y, width, height, text, font, action=None, 
                     button_type='primary', icon=None, message=""):
            super().__init__()
            self.base_x = x
            self.base_y = y
            self.base_width = width
            self.base_height = height
            self.text = text
            self.font = font
            self.action = action
            self.message = message
            self.button_type = button_type
            self.icon = icon
            self.hover_progress = 0
            self.click_progress = 0
            self.is_hovered = False
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.rect = self.image.get_rect(topleft=(x, y))
            self._update_appearance()
    
        def _get_colors(self):
            """Retourne les couleurs selon le type de bouton"""
            colors = {
                'primary': (CYAN, TEXT_PRIMARY),
                'success': (SUCCESS, TEXT_PRIMARY),
                'danger': (ERROR, TEXT_PRIMARY),
                'secondary': (SURFACE, TEXT_SECONDARY),
                'warning': (WARNING, DEEP_DARK)
            }
            return colors.get(self.button_type, colors['primary'])
    
        def _update_appearance(self):
            """Met à jour l'apparence du bouton"""
            self.image.fill((0, 0, 0, 0))
            bg_color, text_color = self._get_colors()
            bg_alpha = 30 + int(self.hover_progress * 40)
            bg_surf = pygame.Surface((self.base_width, self.base_height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (*bg_color[:3], bg_alpha), 
                            (0, 0, self.base_width, self.base_height), border_radius=12)
            self.image.blit(bg_surf, (0, 0))
            border_width = 2 + int(self.hover_progress * 1)
            border_color = lerp_color(bg_color, text_color, self.hover_progress)
            pygame.draw.rect(self.image, border_color,
                            (0, 0, self.base_width, self.base_height), border_width, border_radius=12)
            text_surf = self.font.render(self.text, True, text_color)
            text_rect = text_surf.get_rect(center=(self.base_width // 2, self.base_height // 2))
            if self.hover_progress > 0:
                shadow_surf = self.font.render(self.text, True, (0, 0, 0, 100))
                self.image.blit(shadow_surf, (text_rect.x + 1, text_rect.y + 1))
            self.image.blit(text_surf, text_rect)
    
        def update(self, mouse_pos):
            """Anime le bouton"""
            self.is_hovered = self.rect.collidepoint(mouse_pos)
            target = 1 if self.is_hovered else 0
            self.hover_progress = lerp(self.hover_progress, target, 0.2)
            if self.click_progress > 0:
                self.click_progress = max(0, self.click_progress - 0.1)
            if abs(self.hover_progress - target) > 0.01 or self.click_progress > 0:
                self._update_appearance()
    
        def click(self, mouse_pos):
            """Gère le clic"""
            if self.rect.collidepoint(mouse_pos):
                self.click_progress = 1
                if self.message:
                    print(self.message)
                if self.action:
                    self.action()
                return True
            return False

# Classes used to create buttons, decorations and communication boxes

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text, font, text_color, button_color, action=None, button_color_pressed=BCP, message=""):
        super().__init__()
        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(button_color)
        self.image_hovered = pygame.Surface((width, height))
        self.image_hovered.fill(button_color_pressed)
        self.image = self.image_normal.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.text = text
        self.font = font
        self.text_color = text_color
        self.action = action
        self.message = message
        self._draw_text()

    def _draw_text(self):
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(text_surface, text_rect)

    def update(self, mouse_pos):

        self.image = self.image_hovered.copy() if self.rect.collidepoint(mouse_pos) else self.image_normal.copy()
        self._draw_text()

    def click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            print(self.message)
            if self.action:
                self.action()

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

class DecorativeBox(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, font, text_color, background_color, text, box_id='normal'):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.background_color = background_color
        self.text = text
        self.font = font
        self.text_color = text_color
        self.rect = self.image.get_rect(center=(x, y))
        self._draw_text(box_id)

    def _draw_text(self, box_id='normal'):
        fill_color = (100, 255, 100) if box_id == 'special' else self.background_color
        self.image.fill(fill_color)
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
            self.image.blit(text_surface, text_rect)

class CommunicationBox(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, font, text_color, ok_color, not_ok_color, text):
        super().__init__()
        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(ok_color)
        self.image_error = pygame.Surface((width, height))
        self.image_error.fill(not_ok_color)
        self.image = self.image_normal.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.font = font
        self.text_color = text_color
        self.communication_ok = True
        self.text = text
        self._draw_text()

    class ModernCard(pygame.sprite.Sprite):
        """Card moderne avec glassmorphism pour les indicateurs de statut"""
        def __init__(self, x, y, width, height, font, text, icon_text=""):
            super().__init__()
            self.base_width = width
            self.base_height = height
            self.font = font
            self.small_font = pygame.font.SysFont('Century Schoolbook', 12)
            self.text = text
            self.icon_text = icon_text
            self.status = True  # True = OK, False = Error
            self.pulse = 0
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=(x, y))
            self._update_appearance()
    
        def _update_appearance(self):
            """Dessine la card avec glassmorphism"""
            self.image.fill((0, 0, 0, 0))
        
            # Status color
            status_color = SUCCESS if self.status else ERROR
            pulse_alpha = int(30 + 20 * math.sin(self.pulse))
        
            # Background glassmorphism
            bg_surf = pygame.Surface((self.base_width, self.base_height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (*CARD_BG, 180), 
                            (0, 0, self.base_width, self.base_height), border_radius=10)
            self.image.blit(bg_surf, (0, 0))
        
            # Status indicator (barre latérale)
            indicator_width = 4
            pygame.draw.rect(self.image, status_color,
                            (0, 5, indicator_width, self.base_height - 10), border_radius=2)
        
            # Border subtil
            border_color = lerp_color(status_color, TEXT_SECONDARY, 0.5)
            pygame.draw.rect(self.image, (*border_color, 100),
                            (0, 0, self.base_width, self.base_height), 2, border_radius=10)
        
            # Icon/Badge
            if self.icon_text:
                icon_size = 20
                icon_x = 15
                icon_y = self.base_height // 2 - icon_size // 2
                pygame.draw.circle(self.image, (*status_color, pulse_alpha),
                                 (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2)
                pygame.draw.circle(self.image, status_color,
                                 (icon_x + icon_size // 2, icon_y + icon_size // 2), icon_size // 2, 2)
        
            # Text
            text_x = 45 if self.icon_text else 15
            text_surf = self.font.render(self.text, True, TEXT_PRIMARY)
            self.image.blit(text_surf, (text_x, 8))
        
            # Status text
            status_text = "OK" if self.status else "ERROR"
            status_surf = self.small_font.render(status_text, True, status_color)
            self.image.blit(status_surf, (text_x, self.base_height - 20))
    
        def update(self, mouse_pos=None):
            """Anime la card"""
            self.pulse += 0.1
            if int(self.pulse * 10) % 10 == 0:  # Update appearance every ~10 frames
                self._update_appearance()
    
        def update_status(self, status=None):
            """Met à jour le statut"""
            if status is not None:
                self.status = status
            else:
                self.status = random.choice([True, False])
            self._update_appearance()

    def _draw_text(self):
        fill_color = GREEN if self.communication_ok else RED
        self.image.fill(fill_color)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(text_surface, text_rect)

    def update_status(self):
        self.communication_ok = random.choice([True, False])
        base_text = self.text.split(':')[0]
        self.text = f"{base_text}: OK" if self.communication_ok else f"{base_text}: Not OK"
        self.image = self.image_normal.copy() if self.communication_ok else self.image_error.copy()
        self._draw_text()

    def update(self, mouse_pos):
        pass 

earth_texture = pygame.image.load("picture/earth.png") 
moon_texture = pygame.image.load("picture/moon.png") 

class ModernParticle:
    """Particule moderne avec effet de glow et mouvement fluide"""
    def __init__(self, screen_width=BASE_WIDTH, screen_height=BASE_HEIGHT):
        self.x_ratio = random.random()
        self.y_ratio = random.random()
        self.base_size = random.uniform(0.5, 2.5)
        self.brightness = random.randint(80, 255)
        self.twinkle_speed = random.uniform(0.3, 1.5)
        
        # Couleurs modernes - cyan/bleu dominants
        self.color = random.choice([
            LIGHT_BLUE, PRIMARY_BLUE,
            TEXT_SECONDARY, TEXT_PRIMARY
        ])
        
        # Mouvement lent et fluide
        self.vx = random.uniform(-0.0001, 0.0001)
        self.vy = random.uniform(-0.0001, 0.0001)
        
        # Glow effect
        self.glow_intensity = random.uniform(0.3, 0.8)

    def update(self):
        """Animation de scintillement et mouvement"""
        self.brightness += self.twinkle_speed
        if self.brightness > 255:
            self.brightness = 255
            self.twinkle_speed *= -1
        elif self.brightness < 80:
            self.brightness = 80
            self.twinkle_speed *= -1
        
        # Mouvement fluide
        self.x_ratio += self.vx
        self.y_ratio += self.vy
        
        # Wrap around
        if self.x_ratio > 1:
            self.x_ratio = 0
        elif self.x_ratio < 0:
            self.x_ratio = 1
        if self.y_ratio > 1:
            self.y_ratio = 0
        elif self.y_ratio < 0:
            self.y_ratio = 1

    def draw(self, screen):
        """Dessine la particule avec effet glow"""
        width, height = screen.get_size()
        x = int(self.x_ratio * width)
        y = int(self.y_ratio * height)
        scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
        size = self.base_size * scale
        
        # Glow effect (cercles concentriques)
        alpha = int(self.brightness)
        glow_radius = size * 3
        
        for i in range(3):
            glow_alpha = int(alpha * self.glow_intensity * (1 - i * 0.3))
            if glow_alpha > 0:
                glow_size = size + (glow_radius - size) * (i / 3)
                glow_surf = pygame.Surface((glow_size * 4, glow_size * 4), pygame.SRCALPHA)
                color_with_alpha = (*self.color[:3], glow_alpha // (i + 1))
                pygame.draw.circle(glow_surf, color_with_alpha, 
                                 (glow_size * 2, glow_size * 2), glow_size)
                screen.blit(glow_surf, (x - glow_size * 2, y - glow_size * 2))
        
        # Core particule
        core_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        core_color = (*self.color[:3], alpha)
        pygame.draw.circle(core_surf, core_color, (size * 2, size * 2), size)
        screen.blit(core_surf, (x - size * 2, y - size * 2))


class EarthAndMoon:
    def __init__(self):
        self.earth_x_ratio = 1300 / BASE_WIDTH
        self.earth_y_ratio = 200 / BASE_HEIGHT
        self.base_earth_size = 100
        self.base_moon_size = 30
        self.moon_distance_ratio = 120 / BASE_WIDTH
        self.angle = 0
        self.rotation_speed = 0.001
        self.moon_z = 0
        self.earth_rotation_angle = 0
        self.earth_rotation_speed = 0.0005

    def update(self):
        self.angle += self.rotation_speed
        self.earth_rotation_angle += self.earth_rotation_speed
        
    def draw(self, screen):
        width, height = screen.get_size()
        scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
        
        earth_x = int(self.earth_x_ratio * width)
        earth_y = int(self.earth_y_ratio * height)
        moon_distance = self.moon_distance_ratio * width
        self.moon_z = math.sin(self.angle) * moon_distance
        
        earth_size = int(self.base_earth_size * scale)
        scaled_earth = pygame.transform.scale(earth_texture, (earth_size, earth_size))
        rotated_earth = pygame.transform.rotate(scaled_earth, math.degrees(self.earth_rotation_angle))
        earth_rect = rotated_earth.get_rect(center=(earth_x, earth_y))
        screen.blit(rotated_earth, earth_rect)
        
        moon_x = earth_x + math.cos(self.angle) * moon_distance
        moon_y = earth_y + math.sin(self.angle) * moon_distance
        base_moon_size = self.base_moon_size * scale
        moon_size = max(5 * scale, base_moon_size * (1 - abs(self.moon_z) / moon_distance))
        moon_alpha = int(255 * (1 - abs(self.moon_z) / moon_distance))
        moon_surface = pygame.Surface((moon_size * 2, moon_size * 2), pygame.SRCALPHA)
        scaled_moon = pygame.transform.scale(moon_texture, (int(moon_size * 2), int(moon_size * 2)))
        moon_surface.blit(scaled_moon, (0, 0))
        moon_surface.set_alpha(moon_alpha)
        screen.blit(moon_surface, (moon_x - moon_size, moon_y - moon_size))

# Create modern particles (remplace les étoiles)
particles = [ModernParticle() for _ in range(200)]

# Create the Earth and Moon
earth_and_moon = EarthAndMoon()

# Starting Screen

starting_screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
starting_font_text = load_brand_font(100, bold=True)
starting_font_button = load_brand_font(20, bold=True)

def draw_modern_button(surface, x, y, w, h, text, font, is_hovered, is_primary=True):
    """Bouton moderne pour thème sombre avec léger dégradé et halo au survol"""
    rect = pygame.Rect(int(x), int(y), int(w), int(h))
    corner = 15

    # Couleurs de base
    # Couleurs selon le type - inspiré du CSS rgb(0,140,255)
    if is_primary:
        base_color = (0, 140, 255)  # Bleu lumineux pour START
        glow_color = (0, 140, 255)
    else:
        base_color = (80, 90, 110)  # Gris pour QUIT
        glow_color = (100, 110, 130)

    # Effet glow multiple (box-shadow CSS: 0 0 25px, puis au hover: 5px, 25px, 50px, 100px)
    if is_hovered:
        # Glow intensifié au survol - réduit pour éviter trop de débordement
        glow_layers = [
            (40, 35),   # Couche la plus large réduite
            (25, 30),   # Couche moyenne
            (12, 25),   # Couche proche
            (5, 20)     # Couche la plus proche
        ]
        for blur_size, alpha in glow_layers:
            glow_surface = pygame.Surface((rect.width + blur_size * 2, rect.height + blur_size * 2), pygame.SRCALPHA)
            glow_rect = glow_surface.get_rect()
            pygame.draw.rect(glow_surface, (*glow_color, alpha), glow_rect, border_radius=corner + blur_size // 2)
            surface.blit(glow_surface, (rect.x - blur_size, rect.y - blur_size))
    else:
        # Glow de base (0 0 25px dans le CSS)
        glow_surface = pygame.Surface((rect.width + 30, rect.height + 30), pygame.SRCALPHA)
        glow_rect = glow_surface.get_rect()
        pygame.draw.rect(glow_surface, (*glow_color, 40), glow_rect, border_radius=corner + 8)
        surface.blit(glow_surface, (rect.x - 15, rect.y - 15))

    # Bouton principal (background: rgb(0,140,255))
    pygame.draw.rect(surface, base_color, rect, border_radius=corner)

    # Texte en majuscules avec espacement (letter-spacing: 4px, uppercase)
    label = font.render(text.upper(), True, WHITE)
    label_rect = label.get_rect(center=rect.center)
    surface.blit(label, label_rect)

    return rect

def show_start_screen():
    # Animation variables
    logo_pulse = 0
    title_fade = 0
    transition_fade = 0  # Pour l'animation de transition vers l'interface principale
    transitioning = False
    
    # Prepare password button ONCE (outside the loop to keep state)
    password_button = Special_button(200, 630, 170, 100, "START", starting_font_button, WHITE, PRIMARY_BLUE, 
                                     (0, 74, 124), starting_screen, action=lambda: None)
    
    while True:
        # Get current window size for responsive layout
        width, height = starting_screen.get_size()
        scale_x, scale_y = get_scaling_factors(starting_screen)
        scale = min(scale_x, scale_y)
        
        # Brand background: dark mode with IPSA blue accent
        # Subtle vertical gradient from deep dark to primary blue tint
        base_dark = (10, 18, 28)
        starting_screen.fill(base_dark)
        for y in range(height):
            t = y / max(1, height)
            row_color = lerp_color(base_dark, PRIMARY_BLUE, 0.18 * t)
            pygame.draw.line(starting_screen, row_color, (0, y), (width, y))

        # Animate particles
        for particle in particles:
            particle.update()
            particle.draw(starting_screen)

        # Animation du logo (pulse effect)
        logo_pulse += 0.05
        pulse_scale = 1 + math.sin(logo_pulse) * 0.05
        
        # Animation du titre (fade in)
        title_fade = min(1, title_fade + 0.02)
        
        # Logo avec effet de pulse (glow removed) - RESPONSIVE - AGRANDI ENCORE PLUS
        # Taille basée sur la largeur de la fenêtre (augmenté à 45% pour être plus visible)
        logo_base_size = min(width, height) * 0.45  # 45% de la plus petite dimension
        logo_size = int(logo_base_size * pulse_scale)
        logo_scaled = pygame.transform.scale(logo, (logo_size, logo_size))
        
        # Position du logo - 30% de la largeur, 35% de la hauteur
        logo_x = int(width * 0.30)
        logo_y = int(height * 0.35)
        
        logo_rect = logo_scaled.get_rect(center=(logo_x, logo_y))
        starting_screen.blit(logo_scaled, logo_rect)
        
        # Titre avec police simple - RESPONSIVE
        # Taille basée sur la largeur de la fenêtre
        title_font_size = int(width * 0.06)  # 6% de la largeur
        title_font = pygame.font.SysFont('Century Schoolbook', max(30, title_font_size), bold=True)
        
        # Texte simple sans effet de glow - positionné à 70% de la largeur
        text_x = int(width * 0.70)
        text_y = int(height * 0.35)
        text_surf = title_font.render("AQUAMIS", True, PRIMARY_BLUE)
        text_rect = text_surf.get_rect(center=(text_x, text_y))
        starting_screen.blit(text_surf, text_rect)
        
        # Sous-titre moderne - RESPONSIVE
        subtitle_font_size = int(width * 0.015)  # 1.5% de la largeur
        subtitle_font = pygame.font.SysFont('Century Schoolbook', max(15, subtitle_font_size))
        subtitle = subtitle_font.render("Interface of Control", True, TEXT_SECONDARY)
        subtitle_offset = int(height * 0.06)  # 6% de la hauteur sous le titre
        subtitle_rect = subtitle.get_rect(center=(text_x, text_y + subtitle_offset))
        starting_screen.blit(subtitle, subtitle_rect)
        
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        # Modern buttons - centrés dynamiquement
        button_font = load_brand_font(max(16, int(24 * scale)), bold=True)
        
        # Taille des boutons (proportionnelle à la taille de l'écran)
        button_width = int(width * 0.13)  # 13% de la largeur
        button_height = int(height * 0.09)  # 9% de la hauteur
        button_spacing = int(width * 0.04)  # 4% de la largeur pour l'espacement
        
        # Position Y des boutons (80% de la hauteur de la fenêtre)
        buttons_y = int(height * 0.8)
        
        # Start button (primary) - centré à gauche du centre
        start_x = (width // 2) - button_width - (button_spacing // 2)
        start_y = buttons_y
        start_rect = draw_modern_button(
            starting_screen, start_x, start_y, button_width, button_height,
            "START", button_font,
            pygame.Rect(start_x, start_y, button_width, button_height).collidepoint(mouse_pos),
            is_primary=True
        )
        
        # Quit button (secondary) - centré à droite du centre
        quit_x = (width // 2) + (button_spacing // 2)
        quit_y = buttons_y
        quit_rect = draw_modern_button(
            starting_screen, quit_x, quit_y, button_width, button_height,
            "QUIT", button_font,
            pygame.Rect(quit_x, quit_y, button_width, button_height).collidepoint(mouse_pos),
            is_primary=False
        )

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(mouse_pos):
                    # Invoke password modal instead of direct start
                    password_button.start_trigger()
                if quit_rect.collidepoint(mouse_pos):
                    sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    password_button.start_trigger()
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                # Toggle fullscreen avec F11
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

            # Route events to password handler when open
            result = password_button.handle_event_start(event)
            if result == "switch_screen":
                global USE_PHONE_SENSORS, PHONE_IP, PHONE_VIDEO_URL
                USE_PHONE_SENSORS = password_button.test_mode
                PHONE_IP = password_button.phone_ip
                # Mettre à jour l'URL vidéo avec la nouvelle IP
                PHONE_VIDEO_URL = f"http://{PHONE_IP}:8080/videofeed"
                mode_text = "TEST MODE (Phone Sensors)" if USE_PHONE_SENSORS else "NORMAL MODE (Satellite)"
                print(f"✅ System configured to: {mode_text}")
                if USE_PHONE_SENSORS:
                    print(f"📱 Phone IP (Sensors): {PHONE_IP}")
                    print(f"📹 Phone Video URL: {PHONE_VIDEO_URL}")
                    
                    # Lancer le listener des capteurs du téléphone
                    def start_phone_listener():
                        try:
                            subprocess.Popen([sys.executable, "dependencies/phone_sensor.py", PHONE_IP], 
                                           cwd=os.path.dirname(os.path.abspath(__file__)))
                        except Exception as e:
                            print(f"⚠️ Erreur lors du lancement du listener: {e}")
                    threading.Thread(target=start_phone_listener, daemon=True).start()

                    # Lancer le stream vidéo du téléphone
                    global phone_video_thread
                    phone_video_thread = threading.Thread(target=phone_video_stream_worker, args=(PHONE_VIDEO_URL,), daemon=True)
                    phone_video_thread.start()

                transitioning = True

        # Draw password overlay if active
        if getattr(password_button, 'show_password_input', False):
            # Dim background
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            starting_screen.blit(overlay, (0, 0))
            password_button.draw(starting_screen, starting_font_button)
        
        # Transition en fondu vers noir
        if transitioning:
            transition_fade += 60  # Vitesse du fondu (beaucoup plus rapide)
            fade_overlay = pygame.Surface((width, height))
            fade_overlay.fill((0, 0, 0))
            fade_overlay.set_alpha(min(255, transition_fade))
            starting_screen.blit(fade_overlay, (0, 0))
            
            # Quand le fondu est complet, retourner (l'écran de chargement sera géré dans main)
            if transition_fade >= 255:
                return
        
        pygame.display.flip()
        pygame.time.Clock().tick(60)

def show_loading_screen(continue_loading, get_current_step):
    """Affiche un écran de chargement avec effet radar/scanner circulaire animé
    continue_loading: fonction qui retourne True tant que le chargement doit continuer
    get_current_step: fonction qui retourne l'étape actuelle de chargement
    """
    width, height = starting_screen.get_size()
    radar_angle = 0  # Angle de rotation du radar
    
    while continue_loading():
        # Fond noir
        starting_screen.fill((0, 0, 0))
        
        center_x = width // 2
        center_y = height // 2
        loader_size = 150  # Taille du loader
        
        # Créer une surface pour le loader avec transparence
        loader_surface = pygame.Surface((loader_size * 2, loader_size * 2), pygame.SRCALPHA)
        loader_center = loader_size
        
        # Cercle extérieur avec ombre (box-shadow: 25px 25px 75px)
        shadow_surface = pygame.Surface((loader_size * 2 + 150, loader_size * 2 + 150), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surface, (0, 0, 0, 140), (loader_center + 75, loader_center + 75), loader_size, 0)
        starting_screen.blit(shadow_surface, (center_x - loader_size - 75 + 25, center_y - loader_size - 75 + 25))
        
        # Cercle principal (border: 1px solid #333)
        pygame.draw.circle(loader_surface, (51, 51, 51), (loader_center, loader_center), loader_size, 1)
        
        # Cercle intérieur avec border dashed (#444) - simulé avec segments
        inner_radius = loader_size - 20  # inset: 20px
        segments = 40
        for i in range(0, segments, 2):  # Dashed effect
            angle1 = (i / segments) * 2 * math.pi
            angle2 = ((i + 1) / segments) * 2 * math.pi
            x1 = loader_center + inner_radius * math.cos(angle1)
            y1 = loader_center + inner_radius * math.sin(angle1)
            x2 = loader_center + inner_radius * math.cos(angle2)
            y2 = loader_center + inner_radius * math.sin(angle2)
            pygame.draw.line(loader_surface, (68, 68, 68), (x1, y1), (x2, y2), 1)
        
        # Cercle central (50px diameter) avec border dashed
        center_radius = 25
        for i in range(0, segments, 2):
            angle1 = (i / segments) * 2 * math.pi
            angle2 = ((i + 1) / segments) * 2 * math.pi
            x1 = loader_center + center_radius * math.cos(angle1)
            y1 = loader_center + center_radius * math.sin(angle1)
            x2 = loader_center + center_radius * math.cos(angle2)
            y2 = loader_center + center_radius * math.sin(angle2)
            pygame.draw.line(loader_surface, (68, 68, 68), (x1, y1), (x2, y2), 1)
        
        # Ligne radar rotative (span avec border-top dashed)
        radar_angle += 3  # Vitesse de rotation (2s pour 360° = 3° par frame à 60fps)
        radar_rad = math.radians(radar_angle)
        
        # Ligne radar principale
        radar_x = loader_center + loader_size * math.cos(radar_rad)
        radar_y = loader_center + loader_size * math.sin(radar_rad)
        pygame.draw.line(loader_surface, (255, 255, 255), (loader_center, loader_center), (radar_x, radar_y), 1)
        
        # Effet blur/glow seagreen avec fondu radial (effet scan radar)
        glow_angle = 55  # Angle du secteur de balayage
        glow_surface = pygame.Surface((loader_size * 2, loader_size * 2), pygame.SRCALPHA)
        
        # Créer un effet de scan avec fondu radial depuis le centre vers l'extérieur
        # Diviser le secteur en plusieurs couches avec transparence décroissante
        num_layers = 20  # Nombre de couches pour le dégradé
        
        for i in range(num_layers):
            # Calculer le rayon de cette couche (du centre vers l'extérieur)
            layer_ratio = (i + 1) / num_layers
            layer_radius = loader_size * layer_ratio
            
            # Alpha décroissant du centre (opaque) vers l'extérieur (transparent)
            # Courbe exponentielle pour un effet de scan plus réaliste
            alpha = int(150 * (1 - layer_ratio) ** 2)
            
            # Couleur seagreen avec alpha décroissant
            layer_color = (46, 139, 87, alpha)
            
            # Créer les points du secteur pour cette couche
            # Triangle avec la ligne blanche (radar_rad) au milieu du secteur
            half_angle = math.radians(glow_angle / 2)
            points = [
                (loader_center, loader_center),
                (loader_center + layer_radius * math.cos(radar_rad + half_angle), 
                 loader_center + layer_radius * math.sin(radar_rad + half_angle)),
                (loader_center + layer_radius * math.cos(radar_rad - half_angle), 
                 loader_center + layer_radius * math.sin(radar_rad - half_angle))
            ]
            
            pygame.draw.polygon(glow_surface, layer_color, points, 0)
        
        # Ajouter un blur autour du secteur pour l'effet glow
        blur_layers = [20, 10, 5]
        for blur_size in blur_layers:
            blur_alpha = 15 - blur_size // 2
            half_angle = math.radians(glow_angle / 2)
            points = [
                (loader_center, loader_center),
                (loader_center + loader_size * math.cos(radar_rad + half_angle), loader_center + loader_size * math.sin(radar_rad + half_angle)),
                (loader_center + loader_size * math.cos(radar_rad - half_angle), 
                 loader_center + loader_size * math.sin(radar_rad - half_angle))
            ]
            for offset in range(-blur_size, blur_size + 1, 3):
                offset_points = [(p[0] + offset, p[1]) for p in points]
                if len(offset_points) >= 3:
                    pygame.draw.polygon(glow_surface, (46, 139, 87, blur_alpha), offset_points, 0)
        
        loader_surface.blit(glow_surface, (0, 0))
        
        # Afficher le loader sur l'écran principal
        starting_screen.blit(loader_surface, (center_x - loader_size, center_y - loader_size))
        
        # Texte "Loading..."
        loading_font = pygame.font.SysFont('Century Schoolbook', 24)
        dots = "." * ((radar_angle // 90) % 4)
        loading_text = loading_font.render(f"Loading{dots}", True, (150, 170, 190))
        text_rect = loading_text.get_rect(center=(center_x, center_y + loader_size + 40))
        starting_screen.blit(loading_text, text_rect)
        
        # Affichage de l'étape actuelle
        current_step = get_current_step()
        step_font = pygame.font.SysFont('Century Schoolbook', 18)
        step_text = step_font.render(current_step, True, (46, 139, 87))  # seagreen
        step_rect = step_text.get_rect(center=(center_x, center_y + loader_size + 75))
        starting_screen.blit(step_text, step_rect)
        
        pygame.display.flip()
        pygame.time.Clock().tick(60)

def save_ip(ip_address):
    """Sauvegarde l'adresse IP dans le fichier JSON."""
    # On suppose que le fichier JSON doit contenir un dictionnaire avec la clé "ip"
    data = {"ip": ip_address}
    with open("data/data.json", "w") as f:
        json.dump(data, f)
    print("Adresse IP sauvegardée :", ip_address)

def load_ip():
    with open("data/data.json", "r",encoding="utf-8") as f:
        return json.load(f)

def open_tk_window():
    """Ouvre une fenêtre Tkinter pour saisir l'adresse IP."""
    # Création de la fenêtre Tkinter
    root = tk.Tk()
    root.title("Entrer l'adresse IP")

    # Ajout d'un label et d'un champ de saisie
    label = tk.Label(root, text="Entrez l'adresse IP :")
    label.pack(padx=10, pady=5)

    entry = tk.Entry(root, width=30)
    entry.pack(padx=10, pady=5)

    def on_submit():
        ip = entry.get()
        if ip:
            save_ip(ip)
        # Ferme la fenêtre Tkinter une fois l'IP sauvegardée
        root.destroy()

    # Bouton pour sauvegarder
    submit_btn = tk.Button(root, text="Sauvegarder", command=on_submit)
    submit_btn.pack(padx=10, pady=10)

    # Lancement de la boucle principale Tkinter
    root.mainloop()

def open_excel_table_console(matrix):
    """
    Demande via la console :
    - Le nombre de lignes et de colonnes du tableau Excel.
    - Les valeurs de chaque ligne (les valeurs doivent être séparées par un espace).
    
    Puis utilise Tkinter pour ouvrir une boîte de dialogue permettant de choisir
    l'emplacement et le nom du fichier Excel. Le tableau est ensuite sauvegardé
    grâce à pandas.
    """
    
    # Utiliser Tkinter pour choisir le chemin d'enregistrement du fichier Excel
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale Tkinter
    file_path = filedialog.asksaveasfilename(
        title="Enregistrer le tableau Excel",
        defaultextension=".xlsx",
        filetypes=[("Fichiers Excel", "*.xlsx"), ("Tous les fichiers", "*.*")]
    )
    if file_path:
        df = pd.DataFrame(matrix)
        df.to_excel(file_path, index=False, header=False)
        print("Tableau Excel sauvegardé dans", file_path)
    else:
        print("Aucun chemin sélectionné, opération annulée.")
    root.destroy()

def main():
    # Variable pour contrôler l'écran de chargement
    loading_complete = False
    loading_progress = 0
    current_loading_step = "Initializing..."
    
    # Fonction pour vérifier si le chargement continue
    def is_loading():
        return not loading_complete
    
    # Fonction pour obtenir l'étape actuelle
    def get_current_step():
        return current_loading_step
    
    # Démarrer l'écran de chargement dans un thread séparé (simulé avec les étapes)
    import threading
    
    def load_resources():
        nonlocal loading_complete, loading_progress, current_loading_step
        global os, json, time, USE_PHONE_SENSORS, SENSOR_DATA_FILE
        
        loading_progress = 10
        current_loading_step = "Loading configuration..."
        host=load_ip()["ip"]
        print(f"Adresse ip sélectionné : {host}")
        
        # In phone mode, we just need to make sure the listener script is running.
        # No setup is needed here as we will read from a file.
        if USE_PHONE_SENSORS:
            current_loading_step = "Phone sensor mode. Run sensor_listener.py"
            # Create a dummy sensor file if it doesn't exist
            if not os.path.exists(SENSOR_DATA_FILE):
                with open(SENSOR_DATA_FILE, "w") as f:
                    json.dump({"roll": 0, "pitch": 0, "yaw": 0}, f)
            time.sleep(2) # Give user time to read the message

        loading_progress = 20
        current_loading_step = "Creating socket client..."
        socket_client = None
        if not USE_PHONE_SENSORS:
            socket_client = SocketClient(host)
        
        loading_progress = 30
        current_loading_step = "Initializing variables..."
        video_receiver = None
        data_handler = None
        envoie = {"info_fonction":[0,0,0,0,0]}
        roll = 0
        pitch = 0
        yaw = 0
        vitesse_droit = 0
        vitesse_gauche = 0
        data_text = {}

        loading_progress = 50
        current_loading_step = "Connecting to server..."
        if not USE_PHONE_SENSORS and socket_client:
            socket_client.connect()
            if not socket_client.running:
                print("Impossible de se connecter au serveur")
                current_loading_step = "Connection failed!"
        elif USE_PHONE_SENSORS:
            current_loading_step = "Phone sensor mode active"
            # In phone mode, we don't connect to the satellite server
            pass

        loading_progress = 70
        current_loading_step = "Starting data handlers..."
        # Démarrage des threads si connecté (satellite mode)
        if not USE_PHONE_SENSORS and socket_client and socket_client.running:
            video_receiver = VideoReceiver(socket_client)
            data_handler = DataHandler(socket_client)
            data_handler.message_to_send = envoie
            data_handler.start()
            video_receiver.start()
        elif USE_PHONE_SENSORS:
            current_loading_step = "Receiving phone data..."
            # No separate threads needed for phone as it's self-contained
            pass

        loading_progress = 90
        current_loading_step = "Preparing interface..."
        # Stockage des variables dans un dictionnaire pour les récupérer
        globals()['main_data'] = {
            'socket_client': socket_client,
            'video_receiver': video_receiver,
            'data_handler': data_handler,
            'envoie': envoie,
            'roll': roll,
            'pitch': pitch,
            'yaw': yaw,
            'vitesse_droit': vitesse_droit,
            'vitesse_gauche': vitesse_gauche,
            'data_text': data_text
        }
        
        loading_progress = 100
        current_loading_step = "Ready!"
        loading_complete = True
    
    # Démarrer le chargement en arrière-plan
    load_thread = threading.Thread(target=load_resources)
    load_thread.daemon = True
    load_thread.start()
    
    # Afficher l'écran de chargement jusqu'à ce que tout soit prêt
    show_loading_screen(is_loading, get_current_step)
    
    # Récupérer les données chargées
    data = globals()['main_data']
    socket_client = data['socket_client']
    video_receiver = data['video_receiver']
    data_handler = data['data_handler']
    envoie = data['envoie']
    roll = data['roll']
    pitch = data['pitch']
    yaw = data['yaw']
    vitesse_droit = data['vitesse_droit']
    vitesse_gauche = data['vitesse_gauche']
    data_text = data['data_text']

    # Utiliser la fenêtre existante (starting_screen) au lieu d'en créer une nouvelle
    screen = starting_screen  # Réutiliser la fenêtre du start screen
    
    # Animation de fondu entrant depuis le noir
    fade_in_alpha = 255
    
    # Create a virtual screen at base resolution for drawing
    virtual_screen = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
    clock = pygame.time.Clock()
    font  = load_brand_font(20, bold=False)
    font15 = load_brand_font(15, bold=False)
    font18 = load_brand_font(18, bold=False)
    start_time = time.time()

    # Creating communication boxes to verify the state of AMIS' components (using base resolution)

    BOX_WIDTH, BOX_HEIGHT = 170, 67

    comm_box            = CommunicationBox(1215, 543, BOX_WIDTH, BOX_HEIGHT, font15, WHITE, GREEN, RED, "COMMS: OK")
    cam_box             = CommunicationBox(1215, 620, BOX_WIDTH, BOX_HEIGHT, font15, WHITE, GREEN, RED, "CAM: OK")
    mpu_box             = CommunicationBox(1215, 697, BOX_WIDTH, BOX_HEIGHT, font15, WHITE, GREEN, RED, "MPU: OK")
    servo_box           = CommunicationBox(1395, 543, BOX_WIDTH, BOX_HEIGHT, font15, WHITE, GREEN, RED, "SERVO: OK")
    motor_box           = CommunicationBox(1395, 620, BOX_WIDTH, BOX_HEIGHT, font15, WHITE, GREEN, RED, "ENGINE: OK")
    pressure_sensor_box = CommunicationBox(1395, 697, BOX_WIDTH, BOX_HEIGHT, font15, WHITE, GREEN, RED, "PRESSURE: OK")

    # Creating decorative boxes (to make the interface well organized)

    BW, BH = 1500, 10

    # Horizontal lines

    lineh1 = DecorativeBox(750, 495, BW, BH, font15, YELLOW, GRAY, '')
    lineh2 = DecorativeBox(750, 745, BW, BH, font, YELLOW, GRAY, '')
    lineh3 = DecorativeBox(750, 5, BW, BH, font, YELLOW, GRAY, '')
    lineh4 = DecorativeBox(195, 385, 370, BH, font, GRAY, GRAY, '')
    lineh5 = DecorativeBox(1305, 385, 370, BH, font, GRAY, GRAY, '')

    # Vertical lines

    linev1 = DecorativeBox(1115, 375, BH, 750, font, GRAY, GRAY, "")
    linev2 = DecorativeBox(1495, 375, BH, 750, font, GRAY, GRAY, "")
    linev3 = DecorativeBox(5, 375, BH, 750, font, GRAY, GRAY, "")
    linev4 = DecorativeBox(385, 375, BH, 750, font, GRAY, GRAY, "")

    # Logo's box (the one in the middle of the direction commands)

    AMIS_box  = DecorativeBox(750, 620, 107, 67, font15, YELLOW, GRAY, '')

    # Creating diection commands

    button_color = (75, 75, 75)
    def forward():
       envoie["info_fonction"][3] = vitesse_droit
       envoie["info_fonction"][4] = vitesse_gauche

    def left():
       envoie["info_fonction"][3] = vitesse_gauche

    def right():
       envoie["info_fonction"][4] = vitesse_droit

    def backward():
        envoie["info_fonction"][3] = -vitesse_gauche
        envoie["info_fonction"][4] = -vitesse_droit

    def up():
        envoie["info_fonction"][0] = envoie["info_fonction"][0]+1

    def down():
        envoie["info_fonction"][0] = envoie["info_fonction"][0]-1
    
    def but_stop():
        if data_text == envoie:
            for i in range(1,5):
               envoie["info_fonction"][i] = 0

    def button_action(): 
        print("\n") # Allows for a clearer view in the terminal
        
    button_forward   = Button(697, 500, 107, 85, 'FORWARD', font15, WHITE, button_color, forward, BCP, "AMIS is going FORWARD!")
    button_left      = Button(577, 587, 118, 67, 'LEFT', font15, WHITE, button_color, left, BCP, "AMIS is going LEFT!")
    button_right     = Button(806, 587, 118, 67, 'RIGHT', font15, WHITE, button_color, right, BCP, "AMIS is going RIGHT!")
    button_backward  = Button(697, 655, 107, 84, 'BACKWARD', font15, WHITE, button_color, backward, BCP, "AMIS is going BACKWARD!" )
    button_up        = Button(500, 520, 180, 50, 'UPWARD', font15, WHITE, button_color, up, BCP,"AMIS is going UP!")
    button_down      = Button(820, 670, 180, 50, 'DOWNWARD', font15, WHITE, button_color, down, BCP,"AMIS is going DOWN!")

    # Start, Stop, Emergency Stop and Switch Com buttons

    # button_start supprimé - le START est géré par l'écran d'accueil avec password
    button_stop           = Special_button(20, 630, 170, 100, 'STOP', font, WHITE, (139,0,0),(255,100,100), but_stop,"")
    button_emergency_stop = Button(20, 510, 350, 110, 'EMERGENCY STOP', font, WHITE, (139,0,0), button_action, (255,100,100), 
                                   "EMERGENCY STOP HAS BEEN TRIGGERED - AMIS HAS BEEN STOPPED!")
    switch_com            = Button(20, 400, 350, 80, 'SWITCH COM', font, WHITE, button_color, button_action, BCP, "Comms have been switched!")

    # Display and Save Data buttons

    button_save_data = Button(1130, 400, 350, 80, 'SAVE DATA', font, WHITE, button_color, button_action, BCP, "Currently saving Data...")
    
    # Listing sprites
    
    all_buttons = [button_forward, button_left, button_right, button_backward,
                   button_up, button_down, button_stop, button_emergency_stop, 
                   switch_com, button_save_data]

    # --- Top menu bar (Windows-like) ---
    top_bar_y = 8
    # Define menu actions
    def action_open():
        # Open IP dialog
        open_tk_window()

    def action_exit():
        sys.exit()

    def action_toggle_fullscreen():
        pygame.display.toggle_fullscreen()

    def action_about():
        print("AQUAMIS - Interface v1.0")

    menu_items = [
        ("File", [("Open IP...", action_open), ("Exit", action_exit)]),
        ("View", [("Toggle Fullscreen", action_toggle_fullscreen)]),
        ("Tools", [("Restart Stream", lambda: print('Restart stream'))]),
        ("Help", [("About", action_about)])
    ]

    menu_bar = MenuBar(font15, menu_items)

    all_sprites = pygame.sprite.Group()
    all_sprites.add(
        button_forward, button_left, button_right, button_backward,
        switch_com, AMIS_box, button_up, button_down,
        button_save_data, button_emergency_stop,  
        comm_box, cam_box, mpu_box, servo_box, motor_box, 
        pressure_sensor_box, lineh1, lineh2, lineh3, lineh4, lineh5,
        linev1, linev2, linev3, linev4
    )

    # Creating Rotating Cube

    cube = Cube.Cube(position=(190, 180), size=1, fov=256, viewer_distance=4)
    cube_sprite_group = pygame.sprite.Group(cube) 

    # Defining Logos (decorative purpose)

    logo_amis_big   = pygame.transform.scale(logo, (70, 70))
    logo_amis_small = pygame.transform.scale(logo, (60, 60))
    logo_amis_big_rect   = logo_amis_big.get_rect(center=(50,50))
    logo_amis_small_rect = logo_amis_small.get_rect(center=(749,620))

    # Defining Speed Clock and progression bar

    speed_clock_lm = ProgressBar(435, 510, 30, 220)
    speed_clock_rm = ProgressBar(1040,510, 30, 220)

    # Variables

    input_active_lm = False
    input_text_lm = ""
    value = []

    input_active_rm = False
    input_text_rm = ""

    # Graphs Main

    graph_pressure_depth = Graphs_Main(
        virtual_screen, 240, 170, 255, 50, 
            (255, 0, 0), (0, 0, 255), 
            "", "", 
            target_pressure=6, target_depth=25
            )
    
    graph_angles = Graphs_Angles(virtual_screen, 240, 170, 180)

    # Defining Main 

    running = True

    while running:
        
        keys = pygame.key.get_pressed()
        speed_clock_lm.update(keys)
        speed_clock_rm.update(keys)
        
        # Animation de fondu entrant au début
        if fade_in_alpha > 0:
            fade_in_alpha = max(0, fade_in_alpha - 60)  # Vitesse augmentée nettement

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                # Toggle fullscreen avec F11
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                button_stop.handle_event_stop(event)
                comm_box.update_status() 

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = convert_mouse_pos(pygame.mouse.get_pos(), screen)
                virtual_event_pos = convert_mouse_pos(event.pos, screen)
                
                if 485 <= virtual_event_pos[0] <= 585 and 690 <= virtual_event_pos[1] <= 730:
                    input_active_lm = True
                    input_text_lm = ""
                else: 
                    input_active_lm = False

                if 915 <= virtual_event_pos[0] <= 1015 and 510 <= virtual_event_pos[1] <= 610:
                    input_active_rm = True
                    input_text_rm = ""
                else: 
                    input_active_rm = False
                
                if button_emergency_stop.rect.collidepoint(mouse_pos):  
                    print("🚨 EMERGENCY STOP ACTIVATED!")  
                    if socket_client.running:
                        socket_client.close()
                    if video_receiver:
                        video_receiver.running = False
                        video_receiver.join()
                    if data_handler:
                        data_handler.running = False
                        data_handler.join()
                        
                if switch_com.rect.collidepoint(mouse_pos):  
                    print("Veuillez entrer une nouvelle adresse ip")  
                    open_tk_window()
                    host=load_ip()["ip"]
                    print(f"Adresse ip sélectionné : {host}")
                    
                    # Si en mode téléphone, mettre à jour l'IP pour Phyphox et la vidéo
                    if USE_PHONE_SENSORS:
                        global PHONE_IP, PHONE_VIDEO_URL
                        PHONE_IP = host
                        PHONE_VIDEO_URL = f"http://{host}:8080/videofeed"
                        print(f"📱 Phone IP mis à jour : {PHONE_IP}")
                        print(f"📹 Phone Video URL mis à jour : {PHONE_VIDEO_URL}")
                        print("⚠️ Veuillez redémarrer l'application pour appliquer les changements")

                if button_stop.is_clicked(virtual_event_pos):
                    button_stop.stop_trigger()

                if button_save_data.rect.collidepoint(mouse_pos):
                    open_excel_table_console(value)
                
                # Menu bar click handling (use raw screen coordinates so the
                # bar is an overlay above the scaled virtual surface)
                raw_mouse = pygame.mouse.get_pos()
                menu_bar.handle_click(raw_mouse)

                for button in all_buttons:
                    if button.rect.collidepoint(mouse_pos):
                        button.click(mouse_pos)
                
            if event.type == pygame.KEYDOWN and input_active_lm:
                if event.key == pygame.K_RETURN:
                    if input_text_lm.isdigit():
                        new_speed = int(input_text_lm)
                        vitesse_gauche = new_speed
                        speed_clock_lm.set_speed(new_speed)
                    input_active_lm = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text_lm = input_text_lm[:-1]
                else:
                    input_text_lm += event.unicode

            if event.type == pygame.KEYDOWN and input_active_rm:
                if event.key == pygame.K_RETURN:
                    if input_text_rm.isdigit():
                        new_speed = int(input_text_rm)
                        vitesse_droit = new_speed
                        speed_clock_rm.set_speed(new_speed)
                    input_active_rm = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text_rm = input_text_rm[:-1]
                else:
                    input_text_rm += event.unicode
        

        # Draw everything on the virtual screen at base resolution
        virtual_screen.fill((0, 0, 0))
        
         # Lire les données des capteurs AVANT de mettre à jour le cube
        if USE_PHONE_SENSORS:
            try:
                with open(SENSOR_DATA_FILE, "r") as f:
                    sensor_data = json.load(f)
                roll = sensor_data.get('roll', roll)
                pitch = sensor_data.get('pitch', pitch)
                yaw = sensor_data.get('yaw', yaw)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        elif data_handler:
            with data_handler.data_lock:
                data_text = data_handler.received_data
                try:
                    if "AccX" in data_text.keys():
                        roll = data_text["AngleRoll"] + 90
                        pitch = data_text["AnglePitch"] + 90
                        yaw = data_text["AnglaYaw"]
                except:
                    pass
        
        value.append([roll,pitch,yaw])
        # Graphs in Main

        pygame.draw.rect(virtual_screen, (30, 30, 30), (1120, 10, 370, 370))
        
        if data_text == envoie:
            for i in range(1,5):
               envoie["info_fonction"][i] = 0
        
        roll_value_text = font15.render(f"ROLL: {int(roll)}", True, (255,0,0))
        pitch_value_text = font15.render(f"PITCH: {int(pitch)} ", True, (0,255,0))
        yaw_value_text = font15.render(f"YAW: {int(yaw)} ", True, BLUE)

        virtual_screen.blit(roll_value_text, (1390,50))
        virtual_screen.blit(pitch_value_text, (1390,75))
        virtual_screen.blit(yaw_value_text, (1390,100))
        
        pygame.draw.rect(virtual_screen, RED, (1120,195, 255, 2))
        pygame.draw.rect(virtual_screen, RED, (1375, 10, 2, 370))
        pygame.draw.rect(virtual_screen, RED, (1375, 165, 115, 60),2)
        graph_pressure_depth.update_graph_main()
        graph_angles.update_graph_angles(roll, pitch, yaw)

        # Speed bar

        pygame.draw.rect(virtual_screen, GRAY, (390, 490, 200, 300))
        pygame.draw.rect(virtual_screen, GRAY, (920, 490, 200, 300))
        
        speed_clock_lm.draw(virtual_screen)  
        speed_clock_rm.draw(virtual_screen)  

        pygame.draw.rect(virtual_screen, GRAY, (806, 500, 120, 85))
        pygame.draw.rect(virtual_screen, BLACK, (485, 690, 100, 40))
        pygame.draw.rect(virtual_screen, RED, (485, 690, 100, 40), 2)
        pygame.draw.rect(virtual_screen, BLACK, (915, 510, 100, 40))
        pygame.draw.rect(virtual_screen, RED, (915, 510, 100, 40), 2)
    
        speed_text_lm = font.render(input_text_lm if input_active_lm else str(speed_clock_lm.speed), True, (255, 255, 255))
        text_rect_lm = speed_text_lm.get_rect(center=(535,710))
        virtual_screen.blit(speed_text_lm, text_rect_lm)

        speed_text_rm = font.render(input_text_rm if input_active_rm else str(speed_clock_rm.speed), True, (255, 255, 255))
        text_rect_rm = speed_text_rm.get_rect(center=(965,530))
        virtual_screen.blit(speed_text_rm, text_rect_rm)
        
        # Displaying Timer

        elapsed_time = time.time() - start_time

        minutes = int(elapsed_time) // 60
        seconds = int(elapsed_time) % 60
        time_display = f"{minutes:02d} min {seconds:02d} s"
        time_surface = font18.render(time_display, True, WHITE)
        time_rect = time_surface.get_rect(center=(1433, 195))
        virtual_screen.blit(time_surface, time_rect)
        
        # Buttons' update and displaying of static sprites

        pygame.draw.rect(virtual_screen, GRAY, (575, 500, 120, 85))
        pygame.draw.rect(virtual_screen, GRAY, (806, 656, 120, 85))
        pygame.draw.rect(virtual_screen, RED, (498, 518, 184, 54), 2)
        pygame.draw.rect(virtual_screen, RED, (818, 668, 184, 54), 2)

        mouse_pos = convert_mouse_pos(pygame.mouse.get_pos(), screen)
        # Update menu bar using raw screen coords (it's an overlay)
        raw_mouse = pygame.mouse.get_pos()
        menu_bar.update(raw_mouse)
        for button in all_buttons:
            button.update(mouse_pos)
        all_sprites.draw(virtual_screen)
        
        # Dessiner button_stop après les sprites pour qu'il soit visible
        button_stop.update(mouse_pos)
        button_stop.draw(virtual_screen, font)
        all_sprites.draw(virtual_screen)

        # Initialization of the areas (cube and graphs)

        pygame.draw.rect(virtual_screen, (30, 30, 30), (12, 12, 368, 368))
        pygame.draw.rect(virtual_screen, RED, (10, 10, 370, 370), 2)
        pygame.draw.rect(virtual_screen, RED, (1120, 10, 370, 370), 2)

        # Animation and drawing of the cube
        cube_sprite_group.update(roll,pitch,yaw)
        cube_sprite_group.draw(virtual_screen)
        
        # More Decorations for aesthetic purposes

        pygame.draw.rect(virtual_screen, RED, (390, 10, 720, 480), 2)
        pygame.draw.rect(virtual_screen, RED, (575, 585, 350, 71), 2)
        pygame.draw.rect(virtual_screen, RED, (695, 500, 111, 240), 2)
        pygame.draw.rect(virtual_screen, GRAY, (585, 656, 110, 85))
        pygame.draw.rect(virtual_screen, RED,(1120,390,370,100),2)
        pygame.draw.rect(virtual_screen, RED, (10,390,370,100),2)
        pygame.draw.rect(virtual_screen, RED, (10,500,370,240),2)
        pygame.draw.rect(virtual_screen, RED, (1120,500,370,240),2)
        pygame.draw.rect(virtual_screen, GRAY, (390, 500, 31, 233))
        pygame.draw.rect(virtual_screen, GRAY, (390, 733, 180, 10))
        pygame.draw.rect(virtual_screen, GRAY, (390, 496, 180, 10))
        
        # Logo and associated text (bottom right corner)

        virtual_screen.blit(logo_amis_big, logo_amis_big_rect)
        virtual_screen.blit(logo_amis_small, logo_amis_small_rect)
        text = font.render("AQUAMIS", True, YELLOW)
        text_rect = text.get_rect(center=(320, 30))
        virtual_screen.blit(text, text_rect)
        
        # Central image display
        # Affichage de la vidéo
        frame = None
        
        # Si mode téléphone, utiliser le flux vidéo du téléphone
        if USE_PHONE_SENSORS and phone_video_frame is not None:
            with phone_video_lock:
                frame = phone_video_frame.copy()
        # Sinon, utiliser le flux vidéo satellite
        elif video_receiver and video_receiver.frame is not None:
            with video_receiver.frame_lock:
                frame = video_receiver.frame.copy()
        
        if frame is not None:
            # Optional desaturation to improve overlay contrast
            try:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                s = np.clip((s.astype(np.float32) * 0.85), 0, 255).astype(np.uint8)
                hsv_mod = cv2.merge([h, s, v])
                frame = cv2.cvtColor(hsv_mod, cv2.COLOR_HSV2RGB)
            except Exception:
                # Fallback: direct BGR->RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # At this point `frame` is in RGB (converted above). Run detection on
            # the unrotated image so annotations have the correct orientation.
            try:
                # YOLO attend BGR, donc reconvertir RGB -> BGR pour la détection
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                frame_for_model = np.ascontiguousarray(frame_bgr)
                results = model.track(frame_for_model, persist=True)
                # Save cropped person images (uses track IDs when available)
                try:
                    save_person_crops(frame_bgr, results, save_dir="detected_persons")
                except Exception:
                    pass
                # Update id_person mapping using face recognition on tracked person boxes
                try:
                    def update_id_person_from_tracks(frame_bgr, results, id_person_map, known_encs, known_names, tolerance=0.55):
                        if results is None or len(results) == 0:
                            return
                        r = results[0]
                        boxes = getattr(r, 'boxes', None)
                        if boxes is None:
                            return

                        # get xyxy, cls, ids robustly
                        try:
                            xyxy = boxes.xyxy.cpu().numpy()
                        except Exception:
                            try:
                                xyxy = boxes.xyxy.numpy()
                            except Exception:
                                xyxy = getattr(boxes, 'xyxy', None)
                        if xyxy is None:
                            return

                        cls_array = None
                        try:
                            cls_array = boxes.cls.cpu().numpy()
                        except Exception:
                            try:
                                cls_array = boxes.cls.numpy()
                            except Exception:
                                cls_array = None

                        ids = None
                        if hasattr(boxes, 'id'):
                            try:
                                ids = boxes.id.cpu().numpy()
                            except Exception:
                                try:
                                    ids = boxes.id.numpy()
                                except Exception:
                                    ids = None

                        # find person class index if possible
                        person_class_index = None
                        try:
                            for k, v in model.names.items():
                                if str(v).lower() == 'person':
                                    person_class_index = int(k)
                                    break
                        except Exception:
                            person_class_index = None

                        for i, box in enumerate(xyxy):
                            try:
                                x1, y1, x2, y2 = map(int, box[:4])
                            except Exception:
                                continue

                            # skip non-persons when class info available
                            if cls_array is not None and person_class_index is not None:
                                try:
                                    if int(cls_array[i]) != person_class_index:
                                        continue
                                except Exception:
                                    pass

                            track_id = None
                            if ids is not None:
                                try:
                                    track_id = int(ids[i])
                                except Exception:
                                    track_id = None

                            # If we already know this id is a person, skip
                            if track_id is not None and id_person_map.get(track_id) and id_person_map.get(track_id) != 'Unknown':
                                continue

                            # Crop from base BGR frame
                            h, w = frame_bgr.shape[:2]
                            x1c = max(0, min(w-1, x1))
                            x2c = max(0, min(w, x2))
                            y1c = max(0, min(h-1, y1))
                            y2c = max(0, min(h, y2))
                            if x2c <= x1c or y2c <= y1c:
                                continue
                            crop_bgr = frame_bgr[y1c:y2c, x1c:x2c]
                            if crop_bgr is None or crop_bgr.size == 0:
                                continue

                            # Convert to RGB for face_recognition
                            try:
                                crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
                            except Exception:
                                crop_rgb = crop_bgr[:, :, ::-1]

                            # Run face detection/encoding on crop
                            try:
                                locs = face_recognition.face_locations(crop_rgb)
                                encs = face_recognition.face_encodings(crop_rgb, locs)
                            except Exception:
                                locs = []
                                encs = []

                            name_for_id = 'Unknown'
                            if len(encs) > 0:
                                # compare to known faces
                                for enc in encs:
                                    try:
                                        matches = face_recognition.compare_faces(known_encs, enc, tolerance=tolerance)
                                        dists = face_recognition.face_distance(known_encs, enc)
                                        if len(dists) > 0:
                                            best_idx = np.argmin(dists)
                                            if matches[best_idx]:
                                                name_for_id = known_names[best_idx]
                                                break
                                    except Exception:
                                        continue

                            # Update mapping only if we have a track_id
                            if track_id is not None:
                                id_person_map[track_id] = name_for_id

                    update_id_person_from_tracks(frame_bgr, results, id_person, known_face_encodings, known_face_names)
                    print(id_person)
                except Exception:
                    pass
                # Prepare annotated_frame: inject temporary class indices so plot() shows person names
                annotated_frame = None
                try:
                    r = results[0]
                    boxes = getattr(r, 'boxes', None)
                    original_model_names = None
                    original_cls = None
                    if boxes is not None:
                        # read original cls values
                        try:
                            cls_vals = boxes.cls.cpu().numpy()
                            cls_is_torch = False
                        except Exception:
                            try:
                                cls_vals = boxes.cls.numpy()
                                cls_is_torch = False
                            except Exception:
                                try:
                                    cls_vals = boxes.cls
                                    cls_is_torch = True
                                except Exception:
                                    cls_vals = None
                                    cls_is_torch = False

                        # copy original for restore
                        try:
                            original_cls = None if cls_vals is None else cls_vals.copy()
                        except Exception:
                            original_cls = None

                        # backup model names
                        try:
                            original_model_names = dict(model.names)
                        except Exception:
                            original_model_names = None

                        # build map of name->new_index to reuse indices for identical names
                        next_index = 0
                        try:
                            existing_keys = [int(k) for k in model.names.keys()]
                            next_index = max(existing_keys) + 1 if existing_keys else 0
                        except Exception:
                            next_index = max(model.names.keys()) + 1 if hasattr(model, 'names') else 0

                        name_to_index = {}

                        # attempt to get ids array
                        ids = None
                        if hasattr(boxes, 'id'):
                            try:
                                ids = boxes.id.cpu().numpy()
                            except Exception:
                                try:
                                    ids = boxes.id.numpy()
                                except Exception:
                                    ids = None

                        # modify cls_vals for detections that have a known person name
                        if cls_vals is not None:
                            for i in range(len(cls_vals)):
                                track_id = None
                                if ids is not None:
                                    try:
                                        track_id = int(ids[i])
                                    except Exception:
                                        track_id = None

                                name = None
                                if track_id is not None and track_id in id_person and id_person.get(track_id) and id_person.get(track_id) != 'Unknown':
                                    name = id_person.get(track_id)

                                if name:
                                    # create or reuse an index for this name
                                    if name in name_to_index:
                                        idx = name_to_index[name]
                                    else:
                                        idx = next_index
                                        name_to_index[name] = idx
                                        next_index += 1
                                    # assign to cls_vals
                                    try:
                                        cls_vals[i] = idx
                                    except Exception:
                                        pass

                            # write back cls_vals into boxes.cls
                            try:
                                # if original was torch tensor, convert back
                                if hasattr(boxes.cls, 'device') and hasattr(boxes.cls, 'dtype'):
                                    device = boxes.cls.device
                                    dtype = boxes.cls.dtype
                                    import torch as _torch
                                    boxes.cls = _torch.tensor(cls_vals, dtype=dtype, device=device)
                                else:
                                    try:
                                        boxes.cls = cls_vals
                                    except Exception:
                                        pass
                            except Exception:
                                pass

                        # inject new names into model.names so plot() can use them
                        try:
                            for nm, idx in name_to_index.items():
                                model.names[int(idx)] = nm
                        except Exception:
                            pass

                    # now call plot()
                    annotated_frame = results[0].plot()

                except Exception as e:
                    print('Annotate/modify results error:', e)
                    import traceback
                    traceback.print_exc()
                    # Fallback: manually draw boxes and labels using id_person mapping
                    try:
                        if 'frame_bgr' in locals():
                            fallback_frame = frame_bgr.copy()
                        else:
                            fallback_frame = frame.copy() if 'frame' in locals() else None

                        boxes_local = locals().get('boxes', None)
                        if boxes_local is None and 'results' in locals() and results is not None and len(results) > 0:
                            boxes_local = getattr(results[0], 'boxes', None)

                        if fallback_frame is not None and boxes_local is not None:
                            # get xyxy robustly
                            try:
                                xyxy_fb = boxes_local.xyxy.cpu().numpy()
                            except Exception:
                                try:
                                    xyxy_fb = boxes_local.xyxy.numpy()
                                except Exception:
                                    xyxy_fb = getattr(boxes_local, 'xyxy', None)

                            ids_fb = None
                            if hasattr(boxes_local, 'id'):
                                try:
                                    ids_fb = boxes_local.id.cpu().numpy()
                                except Exception:
                                    try:
                                        ids_fb = boxes_local.id.numpy()
                                    except Exception:
                                        ids_fb = None

                            cls_fb = None
                            try:
                                cls_fb = boxes_local.cls.cpu().numpy()
                            except Exception:
                                try:
                                    cls_fb = boxes_local.cls.numpy()
                                except Exception:
                                    cls_fb = None

                            if xyxy_fb is not None:
                                for i, box in enumerate(xyxy_fb):
                                    try:
                                        x1, y1, x2, y2 = map(int, box[:4])
                                    except Exception:
                                        continue

                                    track_id = None
                                    if ids_fb is not None:
                                        try:
                                            track_id = int(ids_fb[i])
                                        except Exception:
                                            track_id = None

                                    label = ''
                                    if track_id is not None and track_id in id_person and id_person.get(track_id) and id_person.get(track_id) != 'Unknown':
                                        label = id_person.get(track_id)
                                    else:
                                        # fallback to class name if available
                                        try:
                                            if cls_fb is not None:
                                                cls_idx = int(cls_fb[i])
                                                # try original_model_names first, then model.names
                                                name_src = None
                                                if 'original_model_names' in locals() and original_model_names is not None:
                                                    name_src = original_model_names
                                                else:
                                                    name_src = getattr(model, 'names', None)
                                                if name_src is not None:
                                                    label = str(name_src.get(cls_idx, str(cls_idx)))
                                        except Exception:
                                            label = ''

                                    # draw rectangle and label
                                    try:
                                        color = (0, 200, 0) if label else (0, 120, 255)
                                        cv2.rectangle(fallback_frame, (x1, y1), (x2, y2), color, 2)
                                        if label:
                                            font = cv2.FONT_HERSHEY_SIMPLEX
                                            font_scale = 0.6
                                            thickness = 1
                                            (text_w, text_h), _ = cv2.getTextSize(label, font, font_scale, thickness)
                                            # background for text
                                            cv2.rectangle(fallback_frame, (x1, y1 - 20), (x1 + text_w + 6, y1), color, -1)
                                            cv2.putText(fallback_frame, label, (x1 + 3, y1 - 6), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
                                    except Exception:
                                        pass
                        else:
                            # If no boxes, just reuse the original frame
                            if fallback_frame is None:
                                annotated_frame = None
                            else:
                                annotated_frame = fallback_frame

                        # if we built a fallback_frame and haven't set annotated_frame yet, set it
                        if 'fallback_frame' in locals() and annotated_frame is None:
                            annotated_frame = fallback_frame
                    except Exception:
                        # If fallback overlay fails, give up and leave annotated_frame as None
                        annotated_frame = None
                finally:
                    # restore original cls and model.names
                    try:
                        if boxes is not None and original_cls is not None:
                            try:
                                if hasattr(boxes.cls, 'device') and hasattr(boxes.cls, 'dtype'):
                                    import torch as _torch
                                    boxes.cls = _torch.tensor(original_cls, dtype=boxes.cls.dtype, device=boxes.cls.device)
                                else:
                                    boxes.cls = original_cls
                            except Exception:
                                pass
                        if original_model_names is not None:
                            try:
                                model.names = dict(original_model_names)
                            except Exception:
                                pass
                    except Exception:
                        pass

                if annotated_frame is not None:
                    # annotated_frame est en BGR, reconvertir en RGB pour pygame
                    display_img = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                else:
                    display_img = frame
            except Exception as e:
                # If tracking fails, keep using the plain frame
                print("Tracking/Annotator error:", e)
                display_img = frame

            # Convert the numpy image (H, W, 3) to the format expected by
            # pygame.surfarray.make_surface which requires (W, H, 3).
            try:
                disp_arr = np.transpose(display_img, (1, 0, 2))
                disp_arr = np.ascontiguousarray(disp_arr)
                frame_surface = pygame.surfarray.make_surface(disp_arr)
            except Exception as e:
                # Fallback: if transpose fails for any reason, try to make a
                # surface from the raw array (may be mirrored/rotated).
                print("Surface conversion error:", e)
                fallback = np.ascontiguousarray(display_img)
                frame_surface = pygame.surfarray.make_surface(fallback)

            # Redimensionne l'image à (716, 476)
            frame_surface = pygame.transform.scale(frame_surface, (716, 476))
            # Place l'image au centre (750, 250)
            frame_rect = frame_surface.get_rect(center=(750, 250))
            virtual_screen.blit(frame_surface, frame_rect)
        
        # Telemetry (les données sont déjà lues en début de boucle)
        telemetry_font = pygame.font.SysFont('Century Schoolbook', 12)
        virtual_screen.blit(telemetry_font.render("ROLL :", True, (255,0,0)), (45, 347))
        virtual_screen.blit(telemetry_font.render("PITCH :", True, (0,255,0)), (150, 347))
        virtual_screen.blit(telemetry_font.render("YAW :", True, BLUE), (257, 347))
        
        # Indicateur de mode (en haut à droite)
        mode_font = pygame.font.SysFont('Century Schoolbook', 14, bold=True)
        if USE_PHONE_SENSORS:
            mode_text = f"🧪 TEST MODE"
            mode_color = (70, 179, 230)
            ip_text = f"📱 {PHONE_IP}"
            # Vérifier si le fichier sensor_data.json est récent (connexion active)
            try:
                import os
                file_age = time.time() - os.path.getmtime(SENSOR_DATA_FILE)
                if file_age < 1.0:  # Moins d'1 seconde = connexion active
                    status = "🟢 Connected"
                    status_color = (80, 255, 80)
                else:
                    status = "🔴 Disconnected"
                    status_color = (255, 80, 80)
            except:
                status = "⚪ No Data"
                status_color = (200, 200, 200)
        else:
            mode_text = "🛰️ SATELLITE MODE"
            mode_color = (255, 255, 255)
            ip_text = ""
            status = ""
            status_color = (255, 255, 255)
        
        # Afficher le mode et le statut
        mode_surface = mode_font.render(mode_text, True, mode_color)
        virtual_screen.blit(mode_surface, (virtual_screen.get_width() - mode_surface.get_width() - 20, 10))
        
        if USE_PHONE_SENSORS:
            ip_surface = mode_font.render(ip_text, True, (180, 200, 220))
            virtual_screen.blit(ip_surface, (virtual_screen.get_width() - ip_surface.get_width() - 20, 30))
            
            status_surface = mode_font.render(status, True, status_color)
            virtual_screen.blit(status_surface, (virtual_screen.get_width() - status_surface.get_width() - 20, 50))
        
        
        
        # Scale virtual screen to actual window size and display (with window-level background)
        current_size = screen.get_size()
        # Prepare and draw window background image
        if 'WINDOW_BG' not in globals():
            try:
                import os
                bg_path = "picture/back.png"
                globals()['WINDOW_BG'] = pygame.image.load(bg_path).convert() if os.path.exists(bg_path) else None
                globals()['WINDOW_BG_CACHE'] = {'size': None, 'surface': None, 'offset': (0,0)}
            except Exception:
                globals()['WINDOW_BG'] = None
                globals()['WINDOW_BG_CACHE'] = {'size': None, 'surface': None, 'offset': (0,0)}

        # Fill background with "cover" scaled image or black
        if globals().get('WINDOW_BG'):
            if globals()['WINDOW_BG_CACHE'].get('size') != current_size:
                # "Cover" scaling: preserve aspect ratio, crop overflow
                img = globals()['WINDOW_BG']
                img_w, img_h = img.get_size()
                win_w, win_h = current_size
                
                if img_w > 0 and img_h > 0:
                    # Determine the scale factor to ensure the image covers the entire window
                    scale = max(win_w / img_w, win_h / img_h)
                    scaled_w, scaled_h = int(img_w * scale), int(img_h * scale)
                    
                    # Scale the image smoothly to the new dimensions
                    scaled_img = pygame.transform.smoothscale(img, (scaled_w, scaled_h))
                    
                    # Center the scaled image to create the crop effect
                    offset_x = (win_w - scaled_w) // 2
                    offset_y = (win_h - scaled_h) // 2
                    
                    # Cache the results for performance
                    globals()['WINDOW_BG_CACHE'] = {
                        'size': current_size, 
                        'surface': scaled_img, 
                        'offset': (offset_x, offset_y)
                    }
                else: # Handle invalid image size by disabling it
                    globals()['WINDOW_BG_CACHE'] = {'size': current_size, 'surface': None, 'offset': (0,0)}

            # Blit the cached surface at the calculated offset
            cached_data = globals()['WINDOW_BG_CACHE']
            if cached_data.get('surface'):
                screen.blit(cached_data['surface'], cached_data['offset'])
            else:
                screen.fill((0, 0, 0))
        else:
            screen.fill((0, 0, 0))
        
        # Draw the menu bar first and get its height
        try:
            menu_bar.draw(screen)
            menu_height = menu_bar.menu_height
        except Exception:
            menu_height = 0
        
        # Calculate adjusted offsets for virtual_screen to sit below menu bar
        if current_size != (BASE_WIDTH, BASE_HEIGHT):
            # Calculate the best fit while maintaining aspect ratio
            # Account for menu bar height in available space
            available_height = current_size[1] - menu_height
            
            scale_x = current_size[0] / BASE_WIDTH
            scale_y = available_height / BASE_HEIGHT
            scale = min(scale_x, scale_y)
            
            new_width = int(BASE_WIDTH * scale)
            new_height = int(BASE_HEIGHT * scale)
            
            scaled_surface = pygame.transform.smoothscale(virtual_screen, (new_width, new_height))
            
            # Center the scaled surface horizontally and position below menu bar
            x_offset = (current_size[0] - new_width) // 2
            y_offset = menu_height + (available_height - new_height) // 2
            
            screen.blit(scaled_surface, (x_offset, y_offset))
        else:
            screen.blit(virtual_screen, (0, menu_height))
        
        # Appliquer le fondu entrant par-dessus l'interface
        if fade_in_alpha > 0:
            fade_overlay = pygame.Surface(current_size)
            fade_overlay.fill((0, 0, 0))
            fade_overlay.set_alpha(fade_in_alpha)
            screen.blit(fade_overlay, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    if not USE_PHONE_SENSORS and socket_client and socket_client.running:
        socket_client.close()
    if video_receiver:
        video_receiver.running = False
        video_receiver.join()
    if data_handler:
        data_handler.running = False
        data_handler.join()
    # No need to stop phone_server as it's a separate process
    pygame.quit()
    if not USE_PHONE_SENSORS and socket_client and socket_client.running:
        socket_client.close()
    if video_receiver:
        video_receiver.running = False
        video_receiver.join()
    if data_handler:
        data_handler.running = False
        data_handler.join()

show_start_screen()  

if __name__ == '__main__':
    main()
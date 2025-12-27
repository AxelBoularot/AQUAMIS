import pygame
from dependencies.Variable import BLUE, TEXT_SECONDARY, WHITE
from dependencies.Button import draw_modern_button
from dependencies.Font import load_brand_font
from dependencies.ModernParticle import ModernParticle
import sys
import math
import os
import threading
import subprocess
from dependencies.Password import Special_button
from dependencies.Font import lerp_color
import cv2
import time
from dependencies.Scaling import get_scaling_factors
from dependencies.IP_Config import ip_modal_handle_event, ip_modal_draw
from dependencies.Loading_Screen import show_loading_screen
from dependencies.Variable import BASE_WIDTH, BASE_HEIGHT

                                                
particles = [ModernParticle() for _ in range(200)]

USE_PHONE_SENSORS = False                                       

                                                              
                            
SENSOR_DATA_FILE = "sensor_data.json"

                                         
phone_video_frame = None
phone_video_lock = threading.Lock()
sensor_process = None                                              

def phone_video_stream_worker(url):
    global phone_video_frame
    cap = None
    while True:
        try:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                time.sleep(5)
                continue

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                with phone_video_lock:
                    phone_video_frame = frame
        except Exception as e:
            pass
        finally:
            if cap:
                cap.release()
            time.sleep(5)

def create_background(width, height, color_top, color_bottom):
    background = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height)
        row_color = lerp_color(color_top, color_bottom, t)
        pygame.draw.line(background, row_color, (0, y), (width, y))
    return background

def show_start_screen(starting_screen, logo, starting_font_button):
    logo_pulse = 0
    title_fade = 0
    transition_fade = 0
    transitioning = False
    clock = pygame.time.Clock()
    
    prev_w, prev_h = 0, 0
    
    background_surf = None
    title_surf = None
    subtitle_surf = None
    logo_scaled_base = None
    
    password_button = Special_button(200, 630, 170, 100, "START", starting_font_button, WHITE, BLUE, 
                                     (0, 74, 124), starting_screen, action=lambda: None)
    
    start_rect = pygame.Rect(0,0,1,1)
    quit_rect = pygame.Rect(0,0,1,1)
    
    title_font = None
    subtitle_font = None
    button_font = None

    running = True
    while running:
        width, height = starting_screen.get_size()
        
        if (width, height) != (prev_w, prev_h):
            prev_w, prev_h = width, height
            scale_x, scale_y = get_scaling_factors(starting_screen)
            scale = min(scale_x, scale_y)
            
            base_dark = (10, 18, 28)
            target_blue = lerp_color(base_dark, BLUE, 0.18)
            background_surf = create_background(width, height, base_dark, target_blue)
            
            title_font_size = int(width * 0.06)
            title_font = pygame.font.SysFont('Century Schoolbook', max(30, title_font_size), bold=True)
            text_surf = title_font.render("AQUAMIS", True, BLUE)
            
            subtitle_font_size = int(width * 0.02)
            subtitle_font = pygame.font.SysFont('Century Schoolbook', max(15, subtitle_font_size))
            subtitle_surf = subtitle_font.render("Interface of Control", True, (255, 255, 0))
            
            button_font = load_brand_font(max(16, int(24 * scale)), bold=True)
            
            logo_base_size = int(min(width, height) * 0.45)
            logo_x, logo_y = int(width * 0.30), int(height * 0.35)
            text_x, text_y = int(width * 0.70), int(height * 0.35)
            
            button_width = int(width * 0.13)
            button_height = int(height * 0.09)
            button_spacing = int(width * 0.04)
            buttons_y = int(height * 0.8)
            
            start_x = (width // 2) - button_width - (button_spacing // 2)
            quit_x = (width // 2) + (button_spacing // 2)
            
            start_rect = pygame.Rect(start_x, buttons_y, button_width, button_height)
            quit_rect = pygame.Rect(quit_x, buttons_y, button_width, button_height)

        mouse_pos = pygame.mouse.get_pos()
        
        for particle in particles:
            particle.update()
            
        logo_pulse += 0.05
        pulse_scale = 1 + math.sin(logo_pulse) * 0.05
        title_fade = min(1, title_fade + 0.02)

        starting_screen.blit(background_surf, (0, 0))
        
        for particle in particles:
            particle.draw(starting_screen)

        current_logo_size = int(logo_base_size * pulse_scale)
        logo_scaled = pygame.transform.scale(logo, (current_logo_size, current_logo_size))
        logo_rect = logo_scaled.get_rect(center=(logo_x, logo_y))
        starting_screen.blit(logo_scaled, logo_rect)
        
        text_rect = text_surf.get_rect(center=(text_x, text_y))
        starting_screen.blit(text_surf, text_rect)
        
        subtitle_offset = int(height * 0.10)
        sub_rect = subtitle_surf.get_rect(center=(text_x, text_y + subtitle_offset))
        starting_screen.blit(subtitle_surf, sub_rect)
        
        draw_modern_button(starting_screen, start_rect.x, start_rect.y, start_rect.width, start_rect.height,
                        "START", button_font, start_rect.collidepoint(mouse_pos), is_primary=True)

        draw_modern_button(starting_screen, quit_rect.x, quit_rect.y, quit_rect.width, quit_rect.height,
                        "QUIT", button_font, quit_rect.collidepoint(mouse_pos), is_primary=False)

        for event in pygame.event.get():
            if 'IP_MODAL' in globals() and ip_modal_handle_event(event):
                continue

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    password_button.start_trigger()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(mouse_pos):
                    password_button.start_trigger()
                elif quit_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

            result = password_button.handle_event_start(event)
            
            if result == "switch_screen":
                global USE_PHONE_SENSORS, PHONE_IP, PHONE_VIDEO_URL
                USE_PHONE_SENSORS = password_button.test_mode
                PHONE_IP = password_button.phone_ip
                PHONE_VIDEO_URL = f"http://{PHONE_IP}:8080/videofeed"
                
                if USE_PHONE_SENSORS:
                    def start_phone_listener():
                        global sensor_process
                        try:
                            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone_sensor.py")
                            sensor_process = subprocess.Popen([sys.executable, script_path, PHONE_IP])
                        except Exception as e:
                            pass
                    threading.Thread(target=start_phone_listener, daemon=True).start()

                    global phone_video_thread
                    phone_video_thread = threading.Thread(target=phone_video_stream_worker, args=(PHONE_VIDEO_URL,), daemon=True)
                    phone_video_thread.start()

                transitioning = True

        if getattr(password_button, 'show_password_input', False):
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            starting_screen.blit(overlay, (0, 0))
            password_button.draw(starting_screen, starting_font_button)

        if 'IP_MODAL' in globals():
            ip_modal_draw(starting_screen)

        if transitioning:
            transition_fade += 60
            fade_overlay = pygame.Surface((width, height))
            fade_overlay.fill((0, 0, 0))
            fade_overlay.set_alpha(min(255, transition_fade))
            starting_screen.blit(fade_overlay, (0, 0))
            
            if transition_fade >= 255:
                return                                       

        pygame.display.flip()
        clock.tick(60)
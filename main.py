import pygame
import time
import os
import threading
import json
import cv2
import numpy as np
import torch
from ultralytics import YOLO

# Dependencies
import dependencies.Cube as Cube
from dependencies.Password import Special_button
from dependencies.progress_bar import ProgressBar
from dependencies.Graph_Pressure_Depth import Graphs_Main
from dependencies.Graph_Angles import Graphs_Angles
from dependencies.lib_backend import VideoReceiver, DataHandler, SocketClient
from dependencies.Scaling import convert_mouse_pos
from dependencies.Font import load_brand_font
from dependencies.Button import Button
from dependencies.MenuBar import MenuBar
from dependencies.DecorativeBox import DecorativeBox
from dependencies.CommunicationBox import CommunicationBox
# J'ai retiré les variables inutilisées (LIGHT_BLUE, WARNING, ERROR, etc.) pour nettoyer
from dependencies.Variable import WHITE, BLUE, RED, BASE_WIDTH, BASE_HEIGHT, GREEN, BLACK, BCP, GRAY, YELLOW
from dependencies.Loading_Screen import show_loading_screen
from dependencies.IP_Config import load_ip, ip_modal_handle_event, ip_modal_draw, open_excel_table_console, open_tk_window
import dependencies.start_sreen as start_screen_module
from dependencies.start_sreen import show_start_screen, SENSOR_DATA_FILE

# ============================================================
# Initialisation AI & Device
# ============================================================
try:
    print("CUDA available:", torch.cuda.is_available())
except Exception as e:
    print(f"Error checking CUDA availability: {e}")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
# Load model once at startup
model = YOLO("object_detection_lib/yolo11n.pt").to(device)

# ============================================================
# Initialisation de Pygame
# ============================================================
pygame.init()
pygame.display.set_caption("AQUAMIS' Interface of Control")
try:
    logo = pygame.image.load("picture/Logo_AMIS.png")
    pygame.display.set_icon(logo)
except FileNotFoundError:
    logo = None
    print("Logo not found, skipping icon.")

starting_screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
starting_font_button = load_brand_font(20, bold=True)

class App():
    def __init__(self):
        self.running = True
        
        # --- Loading State ---
        self.loading_complete = False
        self.loading_progress = 0
        self.current_loading_step = "Initializing..."

        # --- System Components (Initialized in Thread) ---
        self.socket_client = None
        self.video_receiver = None
        self.data_handler = None
        self.envoie = {"info_fonction": [0, 0, 0, 0, 0]}
        
        # --- Telemetry Variables ---
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.vitesse_droit = 0
        self.vitesse_gauche = 0
        self.data_text = {}
        self.value = []

        # Start loading thread
        load_thread = threading.Thread(target=self.load_resources)
        load_thread.daemon = True
        load_thread.start()
        
        # Show Loading Screen (Blocking until ready)
        show_loading_screen(self.is_loading, self.get_current_step, starting_screen)
        
        # --- Interface Setup ---
        self.screen = starting_screen
        self.fade_in_alpha = 255
        self.virtual_screen = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font = load_brand_font(20, bold=False)
        self.font15 = load_brand_font(15, bold=False)
        self.font18 = load_brand_font(18, bold=False)
        self.start_time = time.time()

        # Background Image Management
        bg_path = "picture/back.png"
        self.bg_image = pygame.image.load(bg_path).convert() if os.path.exists(bg_path) else None
        self.bg_cache = {'size': None, 'surface': None, 'offset': (0,0)}

        # --- UI Components ---
        BOX_WIDTH, BOX_HEIGHT = 170, 67
        
        # Status Boxes
        self.comm_box = CommunicationBox(1215, 543, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "COMMS: OK")
        self.cam_box = CommunicationBox(1215, 620, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "CAM: OK")
        self.mpu_box = CommunicationBox(1215, 697, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "MPU: OK")
        self.servo_box = CommunicationBox(1395, 543, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "SERVO: OK")
        self.motor_box = CommunicationBox(1395, 620, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "ENGINE: OK")
        self.pressure_sensor_box = CommunicationBox(1395, 697, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "PRESSURE: OK")

        # Layout Lines
        BW, BH = 1500, 10
        self.lineh1 = DecorativeBox(750, 495, BW, BH, self.font15, YELLOW, GRAY, '')
        self.lineh2 = DecorativeBox(750, 745, BW, BH, self.font, YELLOW, GRAY, '')
        self.lineh3 = DecorativeBox(750, 5, BW, BH, self.font, YELLOW, GRAY, '')
        self.lineh4 = DecorativeBox(195, 385, 370, BH, self.font, GRAY, GRAY, '')
        self.lineh5 = DecorativeBox(1305, 385, 370, BH, self.font, GRAY, GRAY, '')

        self.linev1 = DecorativeBox(1115, 375, BH, 750, self.font, GRAY, GRAY, "")
        self.linev2 = DecorativeBox(1495, 375, BH, 750, self.font, GRAY, GRAY, "")
        self.linev3 = DecorativeBox(5, 375, BH, 750, self.font, GRAY, GRAY, "")
        self.linev4 = DecorativeBox(385, 375, BH, 750, self.font, GRAY, GRAY, "")

        self.AMIS_box = DecorativeBox(750, 620, 107, 67, self.font15, YELLOW, GRAY, '')

        # Buttons
        self.button_color = (75, 75, 75)
        self.button_forward = Button(697, 500, 107, 85, 'FORWARD', self.font15, WHITE, self.button_color, self.forward, BCP, "AMIS is going FORWARD!")
        self.button_left = Button(577, 587, 118, 67, 'LEFT', self.font15, WHITE, self.button_color, self.left, BCP, "AMIS is going LEFT!")
        self.button_right = Button(806, 587, 118, 67, 'RIGHT', self.font15, WHITE, self.button_color, self.right, BCP, "AMIS is going RIGHT!")
        self.button_backward = Button(697, 655, 107, 84, 'BACKWARD', self.font15, WHITE, self.button_color, self.backward, BCP, "AMIS is going BACKWARD!")
        self.button_up = Button(500, 520, 180, 50, 'UPWARD', self.font15, WHITE, self.button_color, self.up, BCP, "AMIS is going UP!")
        self.button_down = Button(820, 670, 180, 50, 'DOWNWARD', self.font15, WHITE, self.button_color, self.down, BCP, "AMIS is going DOWN!")

        self.button_start = Button(200, 630, 170, 100, 'ALREADY RUNNING', self.font15, WHITE, GREEN, self.button_start_action, (100, 255, 100), "START")
        self.button_stop = Special_button(20, 630, 170, 100, 'STOP', self.font, WHITE, (139, 0, 0), (255, 100, 100), starting_screen, self.but_stop, "")
        self.button_emergency_stop = Special_button(20, 510, 350, 110, 'EMERGENCY STOP', self.font, WHITE, (139, 0, 0), (255, 100, 100), starting_screen, self.button_action, "EMERGENCY STOP HAS BEEN TRIGGERED")
        self.switch_com = Button(20, 400, 350, 80, 'SWITCH COM', self.font, WHITE, self.button_color, self.button_action, BCP, "Comms have been switched!")
        self.button_save_data = Button(1130, 400, 350, 80, 'SAVE DATA', self.font, WHITE, self.button_color, self.button_action, BCP, "Currently saving Data...")

        self.all_buttons = [self.button_forward, self.button_left, self.button_right, self.button_backward,
                            self.button_up, self.button_down, self.button_stop, self.button_emergency_stop,
                            self.switch_com, self.button_save_data]

        # Menu Bar
        menu_items = [
            ("File", [("Open IP...", self.action_open), ("Exit", self.action_exit)]),
            ("View", [("Toggle Fullscreen", self.action_toggle_fullscreen)]),
            ("Tools", [("Restart Stream", lambda: print('Restart stream'))]),
            ("Help", [("About", self.action_about)])
        ]
        self.menu_bar = MenuBar(self.font15, menu_items)

        # Sprite Group
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(
            self.button_forward, self.button_left, self.button_right, self.button_backward,
            self.switch_com, self.AMIS_box, self.button_up, self.button_down,
            self.button_save_data, self.button_emergency_stop,
            self.comm_box, self.cam_box, self.mpu_box, self.servo_box, self.motor_box,
            self.pressure_sensor_box, self.lineh1, self.lineh2, self.lineh3, self.lineh4, self.lineh5,
            self.linev1, self.linev2, self.linev3, self.linev4
        )

        # 3D Cube
        self.cube = Cube.Cube(position=(800, 180), size=2, fov=256, viewer_distance=4)
        self.cube_sprite_group = pygame.sprite.Group(self.cube)

        # Logos
        if logo:
            self.logo_amis_big = pygame.transform.scale(logo, (70, 70))
            self.logo_amis_small = pygame.transform.scale(logo, (60, 60))
        else:
            self.logo_amis_big = pygame.Surface((70,70))
            self.logo_amis_small = pygame.Surface((60,60))
            
        self.logo_amis_big_rect = self.logo_amis_big.get_rect(center=(50, 50))
        self.logo_amis_small_rect = self.logo_amis_small.get_rect(center=(749, 620))

        # Inputs & Bars
        self.speed_clock_lm = ProgressBar(435, 510, 30, 220)
        self.speed_clock_rm = ProgressBar(1040, 510, 30, 220)
        self.input_active_lm = False
        self.input_text_lm = ""
        self.input_active_rm = False
        self.input_text_rm = ""

        # Graphs
        self.graph_pressure_depth = Graphs_Main(
            self.virtual_screen, 240, 170, 255, 50,
            (255, 0, 0), (0, 0, 255), "", "", target_pressure=6, target_depth=25
        )
        self.graph_angles = Graphs_Angles(self.virtual_screen, 240, 170, 180)

    # --- Loading Methods ---
    def is_loading(self):
        return not self.loading_complete

    def get_current_step(self):
        return self.current_loading_step

    def load_resources(self):
        # This runs in a separate thread
        self.loading_progress = 10
        self.current_loading_step = "Loading configuration..."
        host = load_ip()["ip"]
        print(f"Selected IP: {host}")

        # Setup dummy file for phone mode
        if start_screen_module.USE_PHONE_SENSORS:
            self.current_loading_step = "Phone sensor mode check..."
            if not os.path.exists(SENSOR_DATA_FILE):
                with open(SENSOR_DATA_FILE, "w") as f:
                    json.dump({"roll": 0, "pitch": 0, "yaw": 0}, f)
            time.sleep(1)

        self.loading_progress = 20
        self.current_loading_step = "Creating socket client..."
        if not start_screen_module.USE_PHONE_SENSORS:
            self.socket_client = SocketClient(host)

        self.loading_progress = 50
        self.current_loading_step = "Connecting to server..."
        if not start_screen_module.USE_PHONE_SENSORS and self.socket_client:
            self.socket_client.connect()
            if not self.socket_client.running:
                print("Failed to connect to server")
                self.current_loading_step = "Connection failed!"

        self.loading_progress = 70
        self.current_loading_step = "Starting handlers..."
        if not start_screen_module.USE_PHONE_SENSORS and self.socket_client and self.socket_client.running:
            self.video_receiver = VideoReceiver(self.socket_client)
            self.data_handler = DataHandler(self.socket_client)
            self.data_handler.message_to_send = self.envoie
            self.data_handler.start()
            self.video_receiver.start()

        self.loading_progress = 100
        self.current_loading_step = "Ready!"
        self.loading_complete = True

    # --- Movement Control ---
    def forward(self):
        self.envoie["info_fonction"][3] = self.vitesse_droit
        self.envoie["info_fonction"][4] = self.vitesse_gauche

    def left(self):
        self.envoie["info_fonction"][3] = self.vitesse_gauche

    def right(self):
        self.envoie["info_fonction"][4] = self.vitesse_droit

    def backward(self):
        self.envoie["info_fonction"][3] = -self.vitesse_gauche
        self.envoie["info_fonction"][4] = -self.vitesse_droit

    def up(self):
        self.envoie["info_fonction"][0] += 1

    def down(self):
        self.envoie["info_fonction"][0] -= 1

    def but_stop(self):
        # Simplified: Just reset commands
        for i in range(1, 5):
            self.envoie["info_fonction"][i] = 0

    def button_start_action(self):
        print("\n✅ System is already running - AMIS is LIVE!")

    def button_action(self):
        print("\nAction Triggered")

    # --- Menu Actions ---
    def action_open(self):
        open_tk_window()

    def action_exit(self):
        self.running = False

    def action_toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def action_about(self):
        print("AQUAMIS - Interface v1.1 - Optimized")

    # --- Main Loop ---
    def main(self):
        while self.running:
            # 1. Input Handling
            self.keys = pygame.key.get_pressed()
            self.speed_clock_lm.update(self.keys)
            self.speed_clock_rm.update(self.keys)

            if self.fade_in_alpha > 0:
                self.fade_in_alpha = max(0, self.fade_in_alpha - 60)

            for event in pygame.event.get():
                if 'IP_MODAL' in globals():
                    if ip_modal_handle_event(event): continue
                
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    self.button_stop.handle_event_stop(event)
                    result_emergency = self.button_emergency_stop.handle_event_emergency(event)
                    
                    if result_emergency == "emergency_stop":
                        print("🛑 EMERGENCY STOP - Stopping systems...")
                        if self.socket_client and hasattr(self.socket_client, 'running') and self.socket_client.running:
                            self.socket_client.close()
                        if self.video_receiver:
                            self.video_receiver.running = False
                        if self.data_handler:
                            self.data_handler.running = False
                        print("✅ Systems stopped.")
                    self.comm_box.update_status()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_emergency_stop.show_emergency_input: continue

                    mouse_pos = convert_mouse_pos(pygame.mouse.get_pos(), self.screen)
                    virtual_event_pos = convert_mouse_pos(event.pos, self.screen)

                    # Text Inputs
                    self.input_active_lm = (485 <= virtual_event_pos[0] <= 585 and 690 <= virtual_event_pos[1] <= 730)
                    if self.input_active_lm: self.input_text_lm = ""
                    
                    self.input_active_rm = (915 <= virtual_event_pos[0] <= 1015 and 510 <= virtual_event_pos[1] <= 610)
                    if self.input_active_rm: self.input_text_rm = ""

                    # Buttons checks
                    if self.button_emergency_stop.rect.collidepoint(mouse_pos):
                        self.button_emergency_stop.emergency_trigger()

                    if self.switch_com.rect.collidepoint(mouse_pos):
                        open_tk_window()

                    if self.button_stop.is_clicked(virtual_event_pos):
                        self.button_stop.stop_trigger()

                    if self.button_save_data.rect.collidepoint(mouse_pos):
                        open_excel_table_console(self.value)

                    if self.button_start.rect.collidepoint(mouse_pos):
                        self.button_start.click(mouse_pos)

                    self.menu_bar.handle_click(pygame.mouse.get_pos())

                    for button in self.all_buttons:
                        if button.rect.collidepoint(mouse_pos):
                            button.click(mouse_pos)

                # Text Entry Handling
                if event.type == pygame.KEYDOWN:
                    if self.input_active_lm:
                        if event.key == pygame.K_RETURN:
                            if self.input_text_lm.isdigit():
                                self.vitesse_gauche = int(self.input_text_lm)
                                self.speed_clock_lm.set_speed(self.vitesse_gauche)
                            self.input_active_lm = False
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text_lm = self.input_text_lm[:-1]
                        else:
                            self.input_text_lm += event.unicode
                    
                    if self.input_active_rm:
                        if event.key == pygame.K_RETURN:
                            if self.input_text_rm.isdigit():
                                self.vitesse_droit = int(self.input_text_rm)
                                self.speed_clock_rm.set_speed(self.vitesse_droit)
                            self.input_active_rm = False
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text_rm = self.input_text_rm[:-1]
                        else:
                            self.input_text_rm += event.unicode

            # 2. Data Updates & Logic
            self.virtual_screen.fill((0, 0, 0))

            if 'LAST_SAVED_IP' in globals():
                host = globals().pop('LAST_SAVED_IP')
                if start_screen_module.USE_PHONE_SENSORS:
                    start_screen_module.PHONE_IP = host
                    start_screen_module.PHONE_VIDEO_URL = f"http://{host}:8080/videofeed"

            # Sensor Data Reading
            if start_screen_module.USE_PHONE_SENSORS:
                try:
                    with open(SENSOR_DATA_FILE, "r") as f:
                        sensor_data = json.load(f)
                    self.roll = sensor_data.get('roll', self.roll)
                    self.pitch = sensor_data.get('pitch', self.pitch)
                    self.yaw = sensor_data.get('yaw', self.yaw)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass
            elif self.data_handler:
                with self.data_handler.data_lock:
                    data_text = self.data_handler.received_data
                    try:
                        if "AccX" in data_text.keys():
                            self.roll = data_text.get("AngleRoll", 0) + 90
                            self.pitch = data_text.get("AnglePitch", 0) + 90
                            self.yaw = data_text.get("AnglaYaw", 0)
                    except: pass
            
            self.value.append([self.roll, self.pitch, self.yaw])

            # Reset commands if received matches sent (Ack mechanism)
            if self.data_text == self.envoie:
                for i in range(1, 5): self.envoie["info_fonction"][i] = 0

            # 3. Drawing Main Interface Elements
            
            # Graphs Background
            pygame.draw.rect(self.virtual_screen, (30, 30, 30), (1120, 10, 370, 370))

            # Telemetry Text
            self.virtual_screen.blit(self.font15.render(f"ROLL: {int(self.roll)}", True, (255, 0, 0)), (1400, 75))
            self.virtual_screen.blit(self.font15.render(f"PITCH: {int(self.pitch)} ", True, (0, 255, 0)), (1400, 100))
            self.virtual_screen.blit(self.font15.render(f"YAW: {int(self.yaw)} ", True, BLUE), (1400, 125))

            # Update Graphs
            self.graph_pressure_depth.update_graph_main()
            self.graph_angles.update_graph_angles(self.roll, self.pitch, self.yaw)

            # Speed Controls Drawing
            pygame.draw.rect(self.virtual_screen, GRAY, (390, 490, 200, 300))
            pygame.draw.rect(self.virtual_screen, GRAY, (920, 490, 200, 300))
            self.speed_clock_lm.draw(self.virtual_screen)
            self.speed_clock_rm.draw(self.virtual_screen)
            
            # Speed Text
            txt_lm = self.input_text_lm if self.input_active_lm else str(self.speed_clock_lm.speed)
            txt_rm = self.input_text_rm if self.input_active_rm else str(self.speed_clock_rm.speed)
            self.virtual_screen.blit(self.font.render(txt_lm, True, WHITE), (535 - 10, 700))
            self.virtual_screen.blit(self.font.render(txt_rm, True, WHITE), (965 - 10, 520))

            # Timer
            elapsed = time.time() - self.start_time
            self.virtual_screen.blit(self.font18.render(f"{int(elapsed)//60:02d} min {int(elapsed)%60:02d} s", True, WHITE), (1390, 185))

            # Draw Static Sprites
            mouse_pos_virtual = convert_mouse_pos(pygame.mouse.get_pos(), self.screen)
            for button in self.all_buttons:
                button.update(mouse_pos_virtual)
            self.all_sprites.draw(self.virtual_screen)

            # Draw Start/Stop Buttons explicitly
            self.button_start.update(mouse_pos_virtual)
            self.virtual_screen.blit(self.button_start.image, self.button_start.rect)
            
            self.button_stop.update(mouse_pos_virtual)
            self.virtual_screen.blit(self.button_stop.image, self.button_stop.rect)
            self.button_stop.draw(self.virtual_screen, self.font)

            # Cube Animation
            self.cube_sprite_group.update(self.roll, self.pitch, self.yaw)
            self.cube_sprite_group.draw(self.virtual_screen)

            # Decorative Borders
            pygame.draw.rect(self.virtual_screen, BLUE, (390, 10, 720, 480), 2) # Main Vid Border
            
            # Logo
            self.virtual_screen.blit(self.logo_amis_big, self.logo_amis_big_rect)
            self.virtual_screen.blit(self.logo_amis_small, self.logo_amis_small_rect)
            self.virtual_screen.blit(self.font.render("AQUAMIS", True, YELLOW), (280, 20))

            # 4. Video & AI Processing (Optimized)
            frame = None
            if start_screen_module.USE_PHONE_SENSORS and start_screen_module.phone_video_frame is not None:
                with start_screen_module.phone_video_lock:
                    frame = start_screen_module.phone_video_frame.copy()
            elif self.video_receiver and self.video_receiver.frame is not None:
                with self.video_receiver.frame_lock:
                    frame = self.video_receiver.frame.copy()

            if frame is not None:
                try:
                    # OPTIMIZATION: Keep frame in BGR for YOLO, only convert once for Pygame
                    frame_bgr = np.ascontiguousarray(frame) # Ensure layout is correct
                    
                    # YOLO Tracking (Verbose=False to reduce console spam)
                    results = model.track(frame_bgr, persist=True, verbose=False)
                    
                    # Annotate (OpenCV uses BGR)
                    annotated_frame = results[0].plot() if results else frame_bgr
                    
                    # Final Conversion: BGR -> RGB for Pygame
                    frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    
                    # Transpose for Pygame surface (W, H, 3)
                    frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                    
                    # Scale and Blit
                    frame_surface = pygame.transform.scale(frame_surface, (716, 476))
                    frame_rect = frame_surface.get_rect(center=(750, 250))
                    self.virtual_screen.blit(frame_surface, frame_rect)
                    
                except Exception as e:
                    print(f"Video Error: {e}")

            # 5. Overlay Status
            mode_text = "🧪 TEST MODE" if start_screen_module.USE_PHONE_SENSORS else "🛰️ SATELLITE MODE"
            mode_color = (70, 179, 230) if start_screen_module.USE_PHONE_SENSORS else WHITE
            self.virtual_screen.blit(self.font.render(mode_text, True, mode_color), (1150, 20))

            # 6. Final Window Composition
            current_size = self.screen.get_size()
            
            # Draw Background (Cached)
            if self.bg_image:
                if self.bg_cache['size'] != current_size:
                    # Update cache if window size changed
                    img_w, img_h = self.bg_image.get_size()
                    win_w, win_h = current_size
                    scale = max(win_w / img_w, win_h / img_h)
                    scaled_img = pygame.transform.smoothscale(self.bg_image, (int(img_w * scale), int(img_h * scale)))
                    offset = ((win_w - scaled_img.get_width()) // 2, (win_h - scaled_img.get_height()) // 2)
                    self.bg_cache = {'size': current_size, 'surface': scaled_img, 'offset': offset}
                
                self.screen.blit(self.bg_cache['surface'], self.bg_cache['offset'])
            else:
                self.screen.fill(BLACK)

            # Draw Menu
            self.menu_bar.update(pygame.mouse.get_pos())
            self.menu_bar.draw(self.screen)
            menu_height = self.menu_bar.menu_height

            # Scale Virtual Screen to fit remaining space
            available_h = current_size[1] - menu_height
            scale = min(current_size[0] / BASE_WIDTH, available_h / BASE_HEIGHT)
            new_w, new_h = int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale)
            
            scaled_v_screen = pygame.transform.smoothscale(self.virtual_screen, (new_w, new_h))
            self.screen.blit(scaled_v_screen, ((current_size[0] - new_w)//2, menu_height + (available_h - new_h)//2))

            # Emergency Stop Overlay
            if self.button_emergency_stop.show_emergency_input:
                self.button_emergency_stop.draw(self.screen, self.font)
            
            # IP Modal
            if 'IP_MODAL' in globals():
                ip_modal_draw(self.screen)

            # Fade In
            if self.fade_in_alpha > 0:
                fade = pygame.Surface(current_size)
                fade.fill(BLACK)
                fade.set_alpha(self.fade_in_alpha)
                self.screen.blit(fade, (0,0))

            pygame.display.flip()
            self.clock.tick(60)

        # Cleanup
        pygame.quit()
        if not start_screen_module.USE_PHONE_SENSORS and self.socket_client:
            self.socket_client.close()
        if self.video_receiver:
            self.video_receiver.running = False
            self.video_receiver.join()
        if self.data_handler:
            self.data_handler.running = False
            self.data_handler.join()

show_start_screen(starting_font_button=starting_font_button, logo=logo, starting_screen=starting_screen)

if __name__ == '__main__':
    APP = App()
    APP.main()
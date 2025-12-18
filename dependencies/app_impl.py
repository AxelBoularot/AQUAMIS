import pygame
import time
import os
import threading
import json
import cv2
import numpy as np

              
import dependencies.Cube as Cube
from dependencies.Password import Special_button
from dependencies.Graph_Pressure_Depth import Graphs_Main
from dependencies.Graph_Angles import Graphs_Angles
from dependencies.lib_backend import VideoReceiver, DataHandler, SocketClient
from dependencies.Scaling import (
    convert_mouse_pos_with_menu,
    compute_transform_with_menu,
)
from dependencies.Font import load_brand_font
from dependencies.Button import Button
from dependencies.MenuBar import MenuBar
from dependencies.DecorativeBox import DecorativeBox
from dependencies.CommunicationBox import CommunicationBox
from dependencies.Variable import WHITE, BLUE, RED, BASE_WIDTH, BASE_HEIGHT, GREEN, BLACK, BCP, GRAY, YELLOW
from dependencies.Loading_Screen import show_loading_screen
from dependencies.IP_Config import load_ip, ip_modal_handle_event, ip_modal_draw, open_excel_table_console, open_tk_window
import dependencies.start_sreen as start_screen_module
from dependencies.start_sreen import show_start_screen, SENSOR_DATA_FILE
from dependencies.Logsys import LogSystem
from dependencies.AI_Config import load_yolo_model
from dependencies.Dashboard import Dashboard
from dependencies.DraggableWindow import DraggableWindow
from dependencies.WindowSystem import WindowSystem
from dependencies.Battery import BatterySimulator
from dependencies.TelemetryProvider import TelemetryProvider
from dependencies.TelemetryPanels import draw_pressure_depth_panel, draw_temp_panel
from dependencies.ThrustersPanel import draw_thrusters_panel
from dependencies.PowerPanel import draw_power_panel
from dependencies.CameraControlsPanel import CameraControlsState, draw_camera_controls_panel, handle_camera_controls_event
from dependencies.AIDetectionOptionsPanel import AIDetectionOptionsState, draw_ai_options_panel, handle_ai_options_event
from dependencies.Indicators import (
    draw_signal_indicator,
    draw_ballast_indicator,
    draw_speed_indicator,
    draw_battery_indicator,
    draw_pressure_depth_indicator,
    draw_temp_indicator,
)

model, device = load_yolo_model()

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

        self.loading_complete = False
        self.loading_progress = 0
        self.current_loading_step = "Initializing..."

        self.socket_client = None
        self.video_receiver = None
        self.data_handler = None
        self.envoie = {"info_fonction": [0, 0, 0, 0, 0]}

        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.vitesse_droit = 0
        self.vitesse_gauche = 0
        self.data_text = {}
        self.value = []
        self.font = load_brand_font(20, bold=False)
        self.font15 = load_brand_font(15, bold=False)
        self.font18 = load_brand_font(18, bold=False)

        self.dashboard = Dashboard(self.font, self.font15, self.font18)

        menu_items = [
            ("File", [("Open IP...", self.action_open), ("Save Data", self.action_save_data), ("Exit", self.action_exit)]),
            ("Start", self.action_start, (0, 150, 0)),               
            ("Stop", self.action_emergency_stop, (150, 0, 0)),                  
            ("View", [("Toggle Fullscreen", self.action_toggle_fullscreen), ("Reset Layout", self.action_reset_layout)]),
            ("Tools", [("Restart Stream", lambda: None)]),              
            ("Help", [("About", self.action_about)])
        ]
        self.menu_bar = MenuBar(self.font15, menu_items)

        self.camera_window = DraggableWindow(pygame.Rect(390, 10, 720, 480))
        self.right_graph_window = DraggableWindow(pygame.Rect(1120, 10, 370, 420))
        self.status_window = DraggableWindow(pygame.Rect(1120, 500, 370, 245))
        self.logs_window = DraggableWindow(pygame.Rect(10, 100, 370, 200))
        self.signal_window = DraggableWindow(pygame.Rect(10, 310, 370, 110))
        self.ballast_window = DraggableWindow(pygame.Rect(10, 425, 370, 110))
        self.speed_window = DraggableWindow(pygame.Rect(10, 540, 370, 110))
        self.battery_window = DraggableWindow(pygame.Rect(10, 655, 370, 90))

                                                        
        self.pressure_depth_window = DraggableWindow(pygame.Rect(390, 500, 160, 160))
        self.temp_window = DraggableWindow(pygame.Rect(560, 500, 160, 160))

                           
        self.thrusters_window = DraggableWindow(pygame.Rect(730, 500, 380, 120))
        self.power_window = DraggableWindow(pygame.Rect(730, 630, 380, 120))
        self.camera_controls_window = DraggableWindow(pygame.Rect(1120, 10, 370, 110))
        self.ai_options_window = DraggableWindow(pygame.Rect(1120, 130, 370, 120))

        self.window_system = WindowSystem(self.font15, self.menu_bar)
        self.window_system.add_window("Camera", self.camera_window, kind="generic")
        self.window_system.add_window("Graphs", self.right_graph_window, kind="generic")
        self.window_system.add_window("Status", self.status_window, kind="generic")
        self.window_system.add_window("Logs", self.logs_window, kind="generic")

        self.window_system.add_window("Signal", self.signal_window, kind="status")
        self.window_system.add_window("Ballast", self.ballast_window, kind="status")
        self.window_system.add_window("Speed", self.speed_window, kind="status")
        self.window_system.add_window("Battery", self.battery_window, kind="status")

        self.window_system.add_window("PressureDepth", self.pressure_depth_window, kind="generic", start_minimized=True)
        self.window_system.add_window("Temp", self.temp_window, kind="generic", start_minimized=True)

        self.window_system.add_window("Thrusters", self.thrusters_window, kind="generic", start_minimized=True)
        self.window_system.add_window("Power", self.power_window, kind="generic", start_minimized=True)
        self.window_system.add_window("CameraControls", self.camera_controls_window, kind="generic", start_minimized=True)
        self.window_system.add_window("AIOptions", self.ai_options_window, kind="generic", start_minimized=True)

        self.battery = BatterySimulator()
        self.telemetry = TelemetryProvider()
        self.camera_controls = CameraControlsState()
        self.ai_options = AIDetectionOptionsState()
        self._last_camera_frame = None

        load_thread = threading.Thread(target=self.load_resources)
        load_thread.daemon = True
        load_thread.start()

        show_loading_screen(self.is_loading, self.get_current_step, starting_screen)

        self.log_system = LogSystem(self.font15)
        self.log_system.add_log("System initialization complete", "info")
        if not start_screen_module.USE_PHONE_SENSORS and self.socket_client and self.socket_client.running:
            self.log_system.add_log("Connected to server successfully", "info")
        elif start_screen_module.USE_PHONE_SENSORS:
            self.log_system.add_log("Phone sensor mode activated", "info")
        else:
            self.log_system.add_log("Connection failed - check server", "error")

        self.screen = starting_screen
        self.fade_in_alpha = 255
        self.virtual_screen = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()

                                                                        
        self.max_width_crop_ratio = 0.0

        self.start_time = time.time()

        bg_path = "picture/back.png"
        self.bg_image = pygame.image.load(bg_path).convert() if os.path.exists(bg_path) else None
        self.bg_cache = {'size': None, 'surface': None, 'offset': (0,0)}

        BOX_WIDTH, BOX_HEIGHT = 170, 67

        self.comm_box = CommunicationBox(1215, 543, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "COMMS: OK")
        self.cam_box = CommunicationBox(1215, 620, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "CAM: OK")
        self.mpu_box = CommunicationBox(1215, 697, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "MPU: OK")
        self.servo_box = CommunicationBox(1395, 543, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "SERVO: OK")
        self.motor_box = CommunicationBox(1395, 620, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "ENGINE: OK")
        self.pressure_sensor_box = CommunicationBox(1395, 697, BOX_WIDTH, BOX_HEIGHT, self.font15, WHITE, GREEN, RED, "PRESSURE: OK")

        self._status_rel_centers = {}
        for box in (self.comm_box, self.cam_box, self.mpu_box, self.servo_box, self.motor_box, self.pressure_sensor_box):
            cx, cy = box.rect.center
            self._status_rel_centers[box] = (cx - self.status_window.rect.x, cy - self.status_window.rect.y)

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

        self.button_color = (75, 75, 75)
        self.button_start = Button(200, 630, 170, 100, 'ALREADY RUNNING', self.font15, WHITE, GREEN, self.button_start_action, (100, 255, 100), "START")
        self.button_stop = Special_button(20, 630, 170, 100, 'STOP', self.font, WHITE, (139, 0, 0), (255, 100, 100), starting_screen, self.but_stop, "")
        self.button_emergency_stop = Special_button(20, 510, 350, 110, 'EMERGENCY STOP', self.font, WHITE, (139, 0, 0), (255, 100, 100), starting_screen, self.button_action, "EMERGENCY STOP HAS BEEN TRIGGERED")
        self.switch_com = Button(20, 400, 350, 80, 'SWITCH COM', self.font, WHITE, self.button_color, self.button_action, BCP, "Comms have been switched!")

        self.all_buttons = []

        self.window_system.set_default_layout("Camera", (390, 10, 720, 480))
        self.window_system.set_default_layout("Graphs", (1120, 10, 370, 420))
        self.window_system.set_default_layout("Status", (1120, 500, 370, 245))
        self.window_system.set_default_layout("Logs", (10, 100, 370, 200))
        self.window_system.set_default_layout("Signal", (10, 310, 370, 110))
        self.window_system.set_default_layout("Ballast", (10, 425, 370, 110))
        self.window_system.set_default_layout("Speed", (10, 540, 370, 110))
        self.window_system.set_default_layout("Battery", (10, 655, 370, 90))

        self.window_system.set_default_layout("PressureDepth", (390, 500, 160, 160))
        self.window_system.set_default_layout("Temp", (560, 500, 160, 160))
        self.window_system.set_default_layout("Thrusters", (730, 500, 380, 120))
        self.window_system.set_default_layout("Power", (730, 630, 380, 120))
        self.window_system.set_default_layout("CameraControls", (1120, 10, 370, 110))
        self.window_system.set_default_layout("AIOptions", (1120, 130, 370, 120))

        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(
            self.comm_box, self.cam_box, self.mpu_box, self.servo_box, self.motor_box,
            self.pressure_sensor_box
        )

        self.cube = Cube.Cube(position=(1000, 100), size=0.5, fov=256, viewer_distance=4)
        self.cube_sprite_group = pygame.sprite.Group(self.cube)

        if logo:
            self.logo_amis_big = pygame.transform.scale(logo, (70, 70))
            self.logo_amis_small = pygame.transform.scale(logo, (60, 60))
        else:
            self.logo_amis_big = pygame.Surface((70,70))
            self.logo_amis_small = pygame.Surface((60,60))
            
        self.logo_amis_big_rect = self.logo_amis_big.get_rect(center=(50, 50))
        self.logo_amis_small_rect = self.logo_amis_small.get_rect(center=(749, 620))

        self.graph_pressure_depth = Graphs_Main(
            self.virtual_screen, 240, 170, 255, 50,
            (255, 0, 0), (0, 0, 255), "", "", target_pressure=6, target_depth=25
        )
        self.graph_angles = Graphs_Angles(self.virtual_screen, 240, 170, 180)

    def is_loading(self):
        return not self.loading_complete

    def get_current_step(self):
        return self.current_loading_step

    def load_resources(self):
        self.loading_progress = 10
        self.current_loading_step = "Loading configuration..."
        host = load_ip()["ip"]

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
        for i in range(1, 5):
            self.envoie["info_fonction"][i] = 0

    def button_start_action(self):
        print("\nSystem is already running - AMIS is LIVE!")

    def button_action(self):
        print("\nAction Triggered")

    def action_start(self):
        self.log_system.add_log("System Started", "info")
        print("\nSystem Started")

    def action_stop(self):
        self.but_stop()                 
        self.log_system.add_log("System Stopped", "warning")
        print("\nSystem Stopped")

    def action_emergency_stop(self):
        self.button_emergency_stop.emergency_trigger()
        self.log_system.add_log("Emergency Stop Requested", "warning")

    def action_open(self):
        open_tk_window()

    def action_save_data(self):
        open_excel_table_console(self.value)

    def action_exit(self):
        self.running = False

    def action_toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def action_reset_layout(self):
        self.window_system.reset_layout()

    def action_about(self):
        pass
                                                       

    def main(self):
        self.log_system.add_log("Main loop started", "info")
        while self.running:
            self.keys = pygame.key.get_pressed()

            menu_h = self.menu_bar.menu_height

            if self.fade_in_alpha > 0:
                self.fade_in_alpha = max(0, self.fade_in_alpha - 60)

            for event in pygame.event.get():
                if 'IP_MODAL' in globals():
                    if ip_modal_handle_event(event): continue
                
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    v_event_pos = convert_mouse_pos_with_menu(
                        getattr(event, 'pos', pygame.mouse.get_pos()),
                        self.screen,
                        menu_h,
                        max_width_crop_ratio=self.max_width_crop_ratio,
                    )
                    bounds_rect = pygame.Rect(0, -menu_h, BASE_WIDTH, BASE_HEIGHT + menu_h)

                    if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
                        self.window_system.handle_focus_click(v_event_pos)
                        if self.window_system.handle_minimize_click(v_event_pos):
                            continue

                    if self.window_system.handle_drag_event(event, v_event_pos, bounds_rect=bounds_rect):
                        continue

                if event.type in (pygame.MOUSEWHEEL, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    v_pos = convert_mouse_pos_with_menu(
                        pygame.mouse.get_pos(),
                        self.screen,
                        menu_h,
                        max_width_crop_ratio=self.max_width_crop_ratio,
                    )
                    self.log_system.handle_event(event, self.logs_window.rect, mouse_pos=v_pos)

                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    self.button_stop.handle_event_stop(event)
                    result_emergency = self.button_emergency_stop.handle_event_emergency(event)

                    if result_emergency == "emergency_stop":
                                                                       
                        if self.socket_client and hasattr(self.socket_client, 'running') and self.socket_client.running:
                            self.socket_client.close()
                        if self.video_receiver:
                            self.video_receiver.running = False
                        if self.data_handler:
                            self.data_handler.running = False
                                                   
                    self.comm_box.update_status()
               
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_emergency_stop.show_emergency_input: continue

                    mouse_pos = convert_mouse_pos_with_menu(
                        pygame.mouse.get_pos(),
                        self.screen,
                        menu_h,
                        max_width_crop_ratio=self.max_width_crop_ratio,
                    )
                    virtual_event_pos = convert_mouse_pos_with_menu(
                        event.pos,
                        self.screen,
                        menu_h,
                        max_width_crop_ratio=self.max_width_crop_ratio,
                    )

                    handled_panel = False
                    if not self.window_system.is_minimized("CameraControls"):
                        before_paused = self.camera_controls.paused
                        handled_panel |= handle_camera_controls_event(
                            self.camera_controls,
                            event,
                            virtual_event_pos,
                            self.camera_controls_window.rect,
                        )
                        if handled_panel and self.camera_controls.paused != before_paused:
                            self.log_system.add_log(
                                "Camera paused" if self.camera_controls.paused else "Camera resumed",
                                "info",
                            )
                    if not self.window_system.is_minimized("AIOptions"):
                        before_enabled = self.ai_options.enabled
                        before_tracking = self.ai_options.tracking
                        handled_panel |= handle_ai_options_event(
                            self.ai_options,
                            event,
                            virtual_event_pos,
                            self.ai_options_window.rect,
                        )
                        if handled_panel:
                            if self.ai_options.enabled != before_enabled:
                                self.log_system.add_log(
                                    f"AI detections {'enabled' if self.ai_options.enabled else 'disabled'}",
                                    "info",
                                )
                            if self.ai_options.tracking != before_tracking:
                                self.log_system.add_log(
                                    f"AI tracking {'enabled' if self.ai_options.tracking else 'disabled'}",
                                    "info",
                                )
                    if handled_panel:
                        continue

                    real_pos = pygame.mouse.get_pos()
                    restored = self.window_system.handle_restore_click(real_pos)
                    if not restored:
                        self.menu_bar.handle_click(real_pos)

                    if not self.window_system.is_minimized("Speed"):
                        self.dashboard.handle_event(event, virtual_event_pos)

                    for button in self.all_buttons:
                        if button.rect.collidepoint(mouse_pos):
                            button.click(mouse_pos)

            self.virtual_screen.fill((0, 0, 0, 0))

            if 'LAST_SAVED_IP' in globals():
                host = globals().pop('LAST_SAVED_IP')
                if start_screen_module.USE_PHONE_SENSORS:
                    start_screen_module.PHONE_IP = host
                    start_screen_module.PHONE_VIDEO_URL = f"http://{host}:8080/videofeed"

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

            if self.data_text == self.envoie:
                for i in range(1, 5): self.envoie["info_fonction"][i] = 0

            mouse_pos_virtual = convert_mouse_pos_with_menu(
                pygame.mouse.get_pos(),
                self.screen,
                menu_h,
                max_width_crop_ratio=self.max_width_crop_ratio,
            )

            self.battery.update()

            for box, (rx, ry) in self._status_rel_centers.items():
                box.rect.center = (self.status_window.rect.x + rx, self.status_window.rect.y + ry)

            self.dashboard.set_signal_position(self.signal_window.rect.x, self.signal_window.rect.y)
            self.dashboard.set_ballast_position(self.ballast_window.rect.x, self.ballast_window.rect.y)
            self.dashboard.set_speed_position(self.speed_window.rect.x, self.speed_window.rect.y)
            self.virtual_screen.blit(self.logo_amis_big, (20, 20))
            self.virtual_screen.blit(self.font.render("AQUAMIS", True, YELLOW), (100, 40))

            data_for_telemetry = None
            if (not start_screen_module.USE_PHONE_SENSORS) and self.data_handler:
                with self.data_handler.data_lock:
                    data_for_telemetry = dict(self.data_handler.received_data)

            snap = self.telemetry.snapshot(
                use_phone_sensors=start_screen_module.USE_PHONE_SENSORS,
                pitch=float(self.pitch),
                data=data_for_telemetry,
            )

            current_speed = snap.speed
            current_ballast = snap.ballast
            current_signal = snap.signal
            current_pressure = snap.pressure_bar
            current_depth = snap.depth_m
            current_temp = snap.elec_temp_c

            self.dashboard.update_data(speed=current_speed, ballast=current_ballast, signal=current_signal)
            for button in self.all_buttons:
                button.update(mouse_pos_virtual)

            frame = None
            if start_screen_module.USE_PHONE_SENSORS and start_screen_module.phone_video_frame is not None:
                with start_screen_module.phone_video_lock:
                    frame = start_screen_module.phone_video_frame.copy()
            elif self.video_receiver and self.video_receiver.frame is not None:
                with self.video_receiver.frame_lock:
                    frame = self.video_receiver.frame.copy()

            if frame is not None and not self.camera_controls.paused:
                self._last_camera_frame = frame.copy()
            if self.camera_controls.paused and self._last_camera_frame is not None:
                frame = self._last_camera_frame

            def _draw_graphs():
                if self.window_system.is_minimized("Graphs"):
                    return
                right_panel_rect = self.right_graph_window.rect
                pygame.draw.rect(self.virtual_screen, (25, 25, 25), right_panel_rect, border_radius=8)
                pygame.draw.rect(self.virtual_screen, (60, 60, 60), right_panel_rect, 1, border_radius=8)
                self.virtual_screen.blit(self.font15.render(f"ROLL: {int(self.roll)}", True, (255, 0, 0)), (right_panel_rect.x + 280, right_panel_rect.y + 65))
                self.virtual_screen.blit(self.font15.render(f"PITCH: {int(self.pitch)} ", True, (0, 255, 0)), (right_panel_rect.x + 280, right_panel_rect.y + 90))
                self.virtual_screen.blit(self.font15.render(f"YAW: {int(self.yaw)} ", True, BLUE), (right_panel_rect.x + 280, right_panel_rect.y + 115))

                title_gap = self.right_graph_window.titlebar_height + 12
                angles_y = right_panel_rect.y + title_gap
                pressure_y = angles_y + 170 + 20
                self.graph_angles.x_offset = right_panel_rect.x + 7
                self.graph_angles.y_offset = angles_y
                self.graph_pressure_depth.x_offset = right_panel_rect.x + 7
                self.graph_pressure_depth.y_offset = pressure_y
                self.graph_pressure_depth.update_graph_main()
                self.graph_angles.update_graph_angles(self.roll, self.pitch, self.yaw)

                elapsed = time.time() - self.start_time
                timer_surf = self.font15.render(f"{int(elapsed)//60:02d} min {int(elapsed)%60:02d} s", True, WHITE)
                timer_x = self.graph_angles.x_offset + 240 + 10
                timer_y = angles_y + 5
                self.virtual_screen.blit(timer_surf, (timer_x, timer_y))

                self.right_graph_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.right_graph_window, mouse_pos_virtual)

            def _draw_logs():
                if self.window_system.is_minimized("Logs"):
                    return
                self.log_system.draw(
                    self.virtual_screen,
                    self.logs_window.rect.x,
                    self.logs_window.rect.y,
                    self.logs_window.rect.w,
                    self.logs_window.rect.h,
                    mouse_pos=mouse_pos_virtual,
                )
                self.logs_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.logs_window, mouse_pos_virtual)

            def _draw_signal():
                if self.window_system.is_minimized("Signal"):
                    return
                self.dashboard.draw_signal(self.virtual_screen, mouse_pos=mouse_pos_virtual)
                self.signal_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.signal_window, mouse_pos_virtual)

            def _draw_ballast():
                if self.window_system.is_minimized("Ballast"):
                    return
                self.dashboard.draw_ballast(self.virtual_screen, mouse_pos=mouse_pos_virtual)
                self.ballast_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.ballast_window, mouse_pos_virtual)

            def _draw_speed():
                if self.window_system.is_minimized("Speed"):
                    return
                self.dashboard.draw_speed(self.virtual_screen, mouse_pos=mouse_pos_virtual)
                self.speed_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.speed_window, mouse_pos_virtual)

            def _draw_battery():
                if self.window_system.is_minimized("Battery"):
                    return
                bat_rect = self.battery_window.rect
                pygame.draw.rect(self.virtual_screen, (30, 30, 30), bat_rect, border_radius=8)
                pygame.draw.rect(self.virtual_screen, (60, 60, 60), bat_rect, 1, border_radius=8)
                title = self.font15.render("BATTERY", True, WHITE)
                self.virtual_screen.blit(title, (bat_rect.x + 20, bat_rect.y + 12))
                pct = self.battery.percent()
                pct_s = self.font15.render(f"{pct}%", True, WHITE)
                self.virtual_screen.blit(pct_s, (bat_rect.right - pct_s.get_width() - 20, bat_rect.y + 12))
                icon_rect = pygame.Rect(bat_rect.x + 20, bat_rect.y + 35, 120, 40)
                draw_battery_indicator(self.virtual_screen, icon_rect, pct, charging=self.battery.charging)
                self.battery_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.battery_window, mouse_pos_virtual)

            def _draw_pressure_depth():
                if self.window_system.is_minimized("PressureDepth"):
                    return
                draw_pressure_depth_panel(self.virtual_screen, self.pressure_depth_window.rect, self.font15, current_pressure, current_depth)
                self.pressure_depth_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.pressure_depth_window, mouse_pos_virtual)

            def _draw_temp():
                if self.window_system.is_minimized("Temp"):
                    return
                draw_temp_panel(self.virtual_screen, self.temp_window.rect, self.font15, current_temp)
                self.temp_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.temp_window, mouse_pos_virtual)

            def _draw_thrusters():
                if self.window_system.is_minimized("Thrusters"):
                    return
                info = self.envoie.get("info_fonction", [0, 0, 0, 0, 0])
                right_cmd = float(info[3]) if len(info) > 3 else 0.0
                left_cmd = float(info[4]) if len(info) > 4 else 0.0
                draw_thrusters_panel(
                    self.virtual_screen,
                    self.thrusters_window.rect,
                    self.font15,
                    left_cmd=left_cmd,
                    right_cmd=right_cmd,
                    speed=float(current_speed),
                )
                self.thrusters_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.thrusters_window, mouse_pos_virtual)

            def _draw_power():
                if self.window_system.is_minimized("Power"):
                    return
                pct = self.battery.percent()
                draw_power_panel(
                    self.virtual_screen,
                    self.power_window.rect,
                    self.font15,
                    battery_percent=pct,
                    charging=self.battery.charging,
                    consumption_pct_per_min=self.battery.consumption_pct_per_min(),
                    remaining_min=self.battery.remaining_minutes(),
                )
                self.power_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.power_window, mouse_pos_virtual)

            def _draw_camera_controls():
                if self.window_system.is_minimized("CameraControls"):
                    return
                draw_camera_controls_panel(
                    self.virtual_screen,
                    self.camera_controls_window.rect,
                    self.font15,
                    state=self.camera_controls,
                )
                self.camera_controls_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.camera_controls_window, mouse_pos_virtual)

            def _draw_ai_options():
                if self.window_system.is_minimized("AIOptions"):
                    return
                draw_ai_options_panel(
                    self.virtual_screen,
                    self.ai_options_window.rect,
                    self.font15,
                    state=self.ai_options,
                )
                self.ai_options_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.ai_options_window, mouse_pos_virtual)

            def _draw_status():
                if self.window_system.is_minimized("Status"):
                    return
                status_panel_rect = self.status_window.rect
                pygame.draw.rect(self.virtual_screen, (25, 25, 25), status_panel_rect, border_radius=8)
                pygame.draw.rect(self.virtual_screen, (60, 60, 60), status_panel_rect, 1, border_radius=8)
                self.all_sprites.draw(self.virtual_screen)
                self.status_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.status_window, mouse_pos_virtual)

            def _draw_camera():
                if self.window_system.is_minimized("Camera"):
                    return
                camera_rect = self.camera_window.rect
                pygame.draw.rect(self.virtual_screen, (0, 0, 0), camera_rect)
                pygame.draw.rect(self.virtual_screen, BLUE, camera_rect, 2)
                if frame is not None:
                    try:
                        frame_bgr = np.ascontiguousarray(frame)
                        if self.ai_options.enabled:
                            results = model.track(frame_bgr, persist=bool(self.ai_options.tracking), verbose=False)
                            annotated_frame = results[0].plot() if results else frame_bgr
                        else:
                            annotated_frame = frame_bgr
                        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                        frame_surface = pygame.transform.scale(frame_surface, (camera_rect.w - 4, camera_rect.h - 4))
                        frame_rect = frame_surface.get_rect(center=camera_rect.center)
                        self.virtual_screen.blit(frame_surface, frame_rect)
                    except Exception as e:
                        print(f"Video Error: {e}")

                self.cube.rect.center = (camera_rect.x + 610, camera_rect.y + 90)
                self.cube.position = self.cube.rect.center
                self.cube_sprite_group.update(self.roll, self.pitch, self.yaw)
                self.cube_sprite_group.draw(self.virtual_screen)

                self.camera_window.draw_titlebar_hover(self.virtual_screen, mouse_pos_virtual)
                self.window_system.draw_minimize_button(self.virtual_screen, self.camera_window, mouse_pos_virtual)
                pygame.draw.rect(self.virtual_screen, BLUE, camera_rect, 2)

            draw_map = {
                "Camera": _draw_camera,
                "Graphs": _draw_graphs,
                "Status": _draw_status,
                "Logs": _draw_logs,
                "Signal": _draw_signal,
                "Ballast": _draw_ballast,
                "Speed": _draw_speed,
                "Battery": _draw_battery,
                "PressureDepth": _draw_pressure_depth,
                "Temp": _draw_temp,
                "Thrusters": _draw_thrusters,
                "Power": _draw_power,
                "CameraControls": _draw_camera_controls,
                "AIOptions": _draw_ai_options,
            }

            for key in self.window_system.z_order:
                fn = draw_map.get(key)
                if fn is not None:
                    fn()

            current_size = self.screen.get_size()

            if self.bg_image:
                if self.bg_cache['size'] != current_size:
                    img_w, img_h = self.bg_image.get_size()
                    win_w, win_h = current_size
                    scale = max(win_w / img_w, win_h / img_h)
                    scaled_img = pygame.transform.smoothscale(self.bg_image, (int(img_w * scale), int(img_h * scale)))
                    offset = ((win_w - scaled_img.get_width()) // 2, (win_h - scaled_img.get_height()) // 2)
                    self.bg_cache = {'size': current_size, 'surface': scaled_img, 'offset': offset}

                self.screen.blit(self.bg_cache['surface'], self.bg_cache['offset'])
            else:
                self.screen.fill(BLACK)

            self.menu_bar.update(pygame.mouse.get_pos())
            self.menu_bar.draw_bar(self.screen)
            menu_height = self.menu_bar.menu_height

            mode_text = "TEST MODE" if start_screen_module.USE_PHONE_SENSORS else "SATELLITE MODE"
            mode_color = (70, 179, 230) if start_screen_module.USE_PHONE_SENSORS else WHITE
            mode_surf = self.font15.render(mode_text, True, mode_color)
            mode_y = self.menu_bar.bar_margin_top + (self.menu_bar.bar_height - mode_surf.get_height()) // 2
            mode_x = current_size[0] - mode_surf.get_width() - 20
            self.screen.blit(mode_surf, (mode_x, mode_y))

            def _drawer_signal(surf, rect):
                draw_signal_indicator(surf, rect, current_signal)

            def _drawer_ballast(surf, rect):
                draw_ballast_indicator(surf, rect, current_ballast)

            def _drawer_speed(surf, rect):
                txt = draw_speed_indicator(surf, rect, float(current_speed), unit=self.dashboard.speed_unit)
                t = self.font15.render(txt, True, (240, 240, 240))
                surf.blit(t, (rect.x + 28, rect.centery - t.get_height() // 2))

            def _drawer_battery(surf, rect):
                pct = self.battery.percent()
                draw_battery_indicator(surf, rect, pct, charging=self.battery.charging)
                t = self.font15.render(f"{pct}%", True, (240, 240, 240))
                surf.blit(t, (rect.x + 30, rect.centery - t.get_height() // 2))

            def _drawer_pressure_depth(surf, rect):
                draw_pressure_depth_indicator(surf, rect, self.font15, current_pressure, current_depth)

            def _drawer_temp(surf, rect):
                draw_temp_indicator(surf, rect, self.font15, current_temp)

            self.window_system.draw_topbars(
                self.screen,
                mode_x=mode_x,
                mode_y=mode_y,
                mode_h=mode_surf.get_height(),
                status_drawers={
                    "Signal": _drawer_signal,
                    "Ballast": _drawer_ballast,
                    "Speed": _drawer_speed,
                    "Battery": _drawer_battery,
                    "PressureDepth": _drawer_pressure_depth,
                    "Temp": _drawer_temp,
                },
            )

            available_h = current_size[1] - menu_height
            scale, x_offset, y_offset, new_w, new_h = compute_transform_with_menu(
                self.screen,
                menu_height,
                max_width_crop_ratio=self.max_width_crop_ratio,
            )
            
            scaled_v_screen = pygame.transform.smoothscale(self.virtual_screen, (new_w, new_h))
            self.screen.blit(scaled_v_screen, (x_offset, y_offset))

            self.menu_bar.draw_dropdown(self.screen)

            if self.button_emergency_stop.show_emergency_input:
                self.button_emergency_stop.draw(self.screen, self.font)

            if 'IP_MODAL' in globals():
                ip_modal_draw(self.screen)

            if self.fade_in_alpha > 0:
                fade = pygame.Surface(current_size)
                fade.fill(BLACK)
                fade.set_alpha(self.fade_in_alpha)
                self.screen.blit(fade, (0,0))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

        if start_screen_module.sensor_process:
            try:
                start_screen_module.sensor_process.terminate()
                start_screen_module.sensor_process = None
            except:
                pass

        if not start_screen_module.USE_PHONE_SENSORS and self.socket_client:
            self.socket_client.close()
        if self.video_receiver:
            self.video_receiver.running = False
            self.video_receiver.join()
        if self.data_handler:
            self.data_handler.running = False
            self.data_handler.join()


__all__ = ["App", "run"]

def run():
    show_start_screen(starting_font_button=starting_font_button, logo=logo, starting_screen=starting_screen)
    app = App()
    app.main()


if __name__ == '__main__':
    run()
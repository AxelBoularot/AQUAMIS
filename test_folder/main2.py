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
    
    def load_resources():
        nonlocal loading_complete, loading_progress, current_loading_step
        global os, json, time, SENSOR_DATA_FILE
        
        loading_progress = 10
        current_loading_step = "Loading configuration..."
        host=load_ip()["ip"]
        print(f"Adresse ip sélectionné : {host}")
        
        # In phone mode, we just need to make sure the listener script is running.
        # No setup is needed here as we will read from a file.
        if start_screen_module.USE_PHONE_SENSORS:
            current_loading_step = "Phone sensor mode. Run sensor_listener.py"
            # Create a dummy sensor file if it doesn't exist
            if not os.path.exists(SENSOR_DATA_FILE):
                with open(SENSOR_DATA_FILE, "w") as f:
                    json.dump({"roll": 0, "pitch": 0, "yaw": 0}, f)
            time.sleep(2) # Give user time to read the message

        loading_progress = 20
        current_loading_step = "Creating socket client..."
        socket_client = None
        if not start_screen_module.USE_PHONE_SENSORS:
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
        if not start_screen_module.USE_PHONE_SENSORS and socket_client:
            socket_client.connect()
            if not socket_client.running:
                print("Impossible de se connecter au serveur")
                current_loading_step = "Connection failed!"
        elif start_screen_module.USE_PHONE_SENSORS:
            current_loading_step = "Phone sensor mode active"
            # In phone mode, we don't connect to the satellite server
            pass

        loading_progress = 70
        current_loading_step = "Starting data handlers..."
        # Démarrage des threads si connecté (satellite mode)
        if not start_screen_module.USE_PHONE_SENSORS and socket_client and socket_client.running:
            video_receiver = VideoReceiver(socket_client)
            data_handler = DataHandler(socket_client)
            data_handler.message_to_send = envoie
            data_handler.start()
            video_receiver.start()
        elif start_screen_module.USE_PHONE_SENSORS:
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
    show_loading_screen(is_loading, get_current_step,starting_screen)
    
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

    def button_start_action():
        print("\n✅ System is already running - AMIS is LIVE!")
        
    def button_action(): 
        print("\n") # Allows for a clearer view in the terminal
        
    button_forward   = Button(697, 500, 107, 85, 'FORWARD', font15, WHITE, button_color, forward, BCP, "AMIS is going FORWARD!")
    button_left      = Button(577, 587, 118, 67, 'LEFT', font15, WHITE, button_color, left, BCP, "AMIS is going LEFT!")
    button_right     = Button(806, 587, 118, 67, 'RIGHT', font15, WHITE, button_color, right, BCP, "AMIS is going RIGHT!")
    button_backward  = Button(697, 655, 107, 84, 'BACKWARD', font15, WHITE, button_color, backward, BCP, "AMIS is going BACKWARD!" )
    button_up        = Button(500, 520, 180, 50, 'UPWARD', font15, WHITE, button_color, up, BCP,"AMIS is going UP!")
    button_down      = Button(820, 670, 180, 50, 'DOWNWARD', font15, WHITE, button_color, down, BCP,"AMIS is going DOWN!")

    # Start, Stop, Emergency Stop and Switch Com buttons

    button_start          = Button(200, 630, 170, 100, 'ALREADY RUNNING', font15, WHITE, GREEN, button_start_action, (100,255,100), "START")
    button_stop           = Special_button(20, 630, 170, 100, 'STOP', font, WHITE, (139,0,0),(255,100,100), starting_screen, but_stop,"")
    button_emergency_stop = Special_button(20, 510, 350, 110, 'EMERGENCY STOP', font, WHITE, (139,0,0), (255,100,100), starting_screen, button_action, 
                                   "EMERGENCY STOP HAS BEEN TRIGGERED")
    switch_com            = Button(20, 400, 350, 80, 'SWITCH COM', font, WHITE, button_color, button_action, BCP, "Comms have been switched!")

    # Display and Save Data buttons

    button_save_data = Button(1130, 400, 350, 80, 'SAVE DATA', font, WHITE, button_color, button_action, BCP, "Currently saving Data...")
    
    # Listing sprites
    
    all_buttons = [button_forward, button_left, button_right, button_backward,
                   button_up, button_down, button_stop, button_emergency_stop, 
                   switch_com, button_save_data]

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
            # If IP modal active, let it consume events first
            if 'IP_MODAL' in globals():
                if ip_modal_handle_event(event):
                    continue
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                # Toggle fullscreen avec F11
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                button_stop.handle_event_stop(event)
                result_emergency = button_emergency_stop.handle_event_emergency(event)
                if result_emergency == "emergency_stop":
                    # Stopper les systèmes mais rester dans l'interface
                    print("🛑 Stopping all systems...")
                    if not start_screen_module.USE_PHONE_SENSORS and socket_client is not None and hasattr(socket_client, 'running') and socket_client.running:
                        socket_client.close()
                    if video_receiver is not None:
                        video_receiver.running = False
                        video_receiver.join()
                    if data_handler is not None:
                        data_handler.running = False
                        data_handler.join()
                    print("✅ All systems have been stopped safely")
                comm_box.update_status()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Si l'emergency stop est actif, ignorer les clics sauf sur le dialogue
                if button_emergency_stop.show_emergency_input:
                    continue
                    
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
                    print("🚨 EMERGENCY STOP BUTTON CLICKED - AWAITING CONFIRMATION...")  
                    button_emergency_stop.emergency_trigger()
                        
                if switch_com.rect.collidepoint(mouse_pos):  
                    print("Veuillez entrer une nouvelle adresse ip")  
                    open_tk_window()

                if button_stop.is_clicked(virtual_event_pos):
                    button_stop.stop_trigger()

                if button_save_data.rect.collidepoint(mouse_pos):
                    open_excel_table_console(value)
                
                if button_start.rect.collidepoint(mouse_pos):
                    button_start.click(mouse_pos)
                
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

        # If an IP was saved by the modal, apply updates here so graphs keep running
        if 'LAST_SAVED_IP' in globals():
            host = globals().pop('LAST_SAVED_IP')
            print(f"Adresse ip sélectionné : {host}")
            if start_screen_module.USE_PHONE_SENSORS:
                start_screen_module.PHONE_IP = host
                start_screen_module.PHONE_VIDEO_URL = f"http://{host}:8080/videofeed"
                print(f"Phone IP mis à jour : {start_screen_module.PHONE_IP}")
                print(f"Phone Video URL mis à jour : {start_screen_module.PHONE_VIDEO_URL}")
                print("Veuillez redémarrer l'application pour appliquer les changements")
        
         # Lire les données des capteurs AVANT de mettre à jour le cube
        if start_screen_module.USE_PHONE_SENSORS:
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

        virtual_screen.blit(roll_value_text, (1400,75))
        virtual_screen.blit(pitch_value_text, (1400,100))
        virtual_screen.blit(yaw_value_text, (1400,125))
        
        pygame.draw.rect(virtual_screen, BLUE, (1120,195, 255, 2))
        pygame.draw.rect(virtual_screen, BLUE, (1375, 10, 2, 370))
        pygame.draw.rect(virtual_screen, BLUE, (1375, 165, 115, 60),2)
        graph_pressure_depth.update_graph_main()
        graph_angles.update_graph_angles(roll, pitch, yaw)

        # Speed bar

        pygame.draw.rect(virtual_screen, GRAY, (390, 490, 200, 300))
        pygame.draw.rect(virtual_screen, GRAY, (920, 490, 200, 300))
        
        speed_clock_lm.draw(virtual_screen)  
        speed_clock_rm.draw(virtual_screen)  

        pygame.draw.rect(virtual_screen, GRAY, (806, 500, 120, 85))
        pygame.draw.rect(virtual_screen, BLACK, (485, 690, 100, 40))
        pygame.draw.rect(virtual_screen, BLUE, (485, 690, 100, 40), 2)
        pygame.draw.rect(virtual_screen, BLACK, (915, 510, 100, 40))
        pygame.draw.rect(virtual_screen, BLUE, (915, 510, 100, 40), 2)
    
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
        pygame.draw.rect(virtual_screen, BLUE, (498, 518, 184, 54), 2)
        pygame.draw.rect(virtual_screen, BLUE, (818, 668, 184, 54), 2)

        mouse_pos = convert_mouse_pos(pygame.mouse.get_pos(), screen)
        # Update menu bar using raw screen coords (it's an overlay)
        raw_mouse = pygame.mouse.get_pos()
        menu_bar.update(raw_mouse)
        for button in all_buttons:
            button.update(mouse_pos)
        all_sprites.draw(virtual_screen)
        
        # Dessiner button_start et button_stop après les sprites pour qu'ils soient visibles
        button_start.update(mouse_pos)
        button_start.image.blit(button_start.font.render(button_start.text, True, button_start.text_color), 
                                (button_start.rect.width // 2 - button_start.font.render(button_start.text, True, button_start.text_color).get_width() // 2, 
                                 button_start.rect.height // 2 - button_start.font.render(button_start.text, True, button_start.text_color).get_height() // 2))
        virtual_screen.blit(button_start.image, button_start.rect)
        
        button_stop.update(mouse_pos)
        virtual_screen.blit(button_stop.image, button_stop.rect)
        stop_text_surface = font.render(button_stop.text, True, button_stop.text_color)
        stop_text_rect = stop_text_surface.get_rect(center=(button_stop.rect.centerx, button_stop.rect.centery))
        virtual_screen.blit(stop_text_surface, stop_text_rect)
        button_stop.draw(virtual_screen, font)
        all_sprites.draw(virtual_screen)

        # Initialization of the areas (cube and graphs)

        pygame.draw.rect(virtual_screen, (30, 30, 30), (12, 12, 368, 368))
        pygame.draw.rect(virtual_screen, BLUE, (10, 10, 370, 370), 2)
        pygame.draw.rect(virtual_screen, BLUE, (1120, 10, 370, 370), 2)

        # Animation and drawing of the cube
        cube_sprite_group.update(roll,pitch,yaw)
        cube_sprite_group.draw(virtual_screen)
        
        # More Decorations for aesthetic purposes

        pygame.draw.rect(virtual_screen, BLUE, (390, 10, 720, 480), 2)
        pygame.draw.rect(virtual_screen, BLUE, (575, 585, 350, 71), 2)
        pygame.draw.rect(virtual_screen, BLUE, (695, 500, 111, 240), 2)
        pygame.draw.rect(virtual_screen, GRAY, (585, 656, 110, 85))
        pygame.draw.rect(virtual_screen, BLUE,(1120,390,370,100),2)
        pygame.draw.rect(virtual_screen, BLUE, (10,390,370,100),2)
        pygame.draw.rect(virtual_screen, BLUE, (10,500,370,240),2)
        pygame.draw.rect(virtual_screen, BLUE, (1120,500,370,240),2)
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
        if start_screen_module.USE_PHONE_SENSORS and start_screen_module.phone_video_frame is not None:
            with start_screen_module.phone_video_lock:
                frame = start_screen_module.phone_video_frame.copy()
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
                display_img = results[0].plot() if results and hasattr(results[0], 'boxes') else frame_bgr
                try:
                    display_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB) if isinstance(display_img, np.ndarray) and len(display_img.shape) == 3 else display_img
                except:
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
        if start_screen_module.USE_PHONE_SENSORS:
            mode_text = f"🧪 TEST MODE"
            mode_color = (70, 179, 230)
            ip_text = f"📱 {start_screen_module.PHONE_IP}"
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
        
        if start_screen_module.USE_PHONE_SENSORS:
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
        
        # Afficher le dialogue d'emergency stop si actif
        if button_emergency_stop.show_emergency_input:
            button_emergency_stop.draw(screen, font)

        # Draw IP modal if active (non-blocking)
        if 'IP_MODAL' in globals():
            ip_modal_draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    if not start_screen_module.USE_PHONE_SENSORS and socket_client and socket_client.running:
        socket_client.close()
    if video_receiver:
        video_receiver.running = False
        video_receiver.join()
    if data_handler:
        data_handler.running = False
        data_handler.join()
    # No need to stop phone_server as it's a separate process

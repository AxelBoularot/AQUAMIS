import pygame, math, random, time, Cube, sys
import tkinter as tk
from Password import Special_button
from progress_bar import ProgressBar
from Graphs_Data import GraphManager
from threading import Thread
from Graphs_Main import Graphs_Main
from tkinter import messagebox

# Pygame's initialization - AMIS' LOGO - Interface's name

pygame.init()
pygame.display.set_caption("AQUAMIS' Interface of Control")
logo = pygame.image.load("Logo_AMIS.png")
pygame.display.set_icon(logo)

# Defining colors

RED    = (139, 0, 0)
GREEN  = (0, 100, 0)
GRAY   = (45, 45, 45)
WHITE  = (255, 255, 255)
YELLOW  = (255, 255, 0)
BLACK  = (0, 0, 0)
BLUE   = (0, 0, 255)
DARK_BLUE = (10, 10, 30)

BCP = (150,150,150) # button_color_pressed

# Classes used to create data's interface, buttons, decorations and communication boxes

class PygameTkinterInterface:
    def __init__(self):
        pygame.init()

    def open_tkinter_window():
        
        root = tk.Tk()
        root.title("AQUAMIS' Data Menu")
        logo = tk.PhotoImage(file='Logo_AMIS.png')
        root.iconphoto(True, logo)  
        root.geometry("1500x750")
        
        graph_manager = GraphManager(root)
        graph_manager.run()

        root.mainloop()

    def run(self):

        running = True
        while running:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            pygame.display.flip()

        pygame.quit()

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

def button_action(): 
    print("\n") # Allows for a clearer view in the terminal

earth_texture = pygame.image.load("earth.png") 
earth_texture = pygame.transform.scale(earth_texture, (100, 100)) 
moon_texture = pygame.image.load("moon.png")  
moon_texture = pygame.transform.scale(moon_texture, (30, 30)) 

class Star:
    def __init__(self):
        self.x = random.randint(0, 1500)
        self.y = random.randint(0, 750)
        self.size = random.uniform(1, 3)
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.5, 2)
        self.color = random.choice([WHITE, YELLOW])

    def twinkle(self):
        self.brightness += self.twinkle_speed
        if self.brightness > 255:
            self.brightness = 255
            self.twinkle_speed *= -1
        elif self.brightness < 100:
            self.brightness = 100
            self.twinkle_speed *= -1

    def draw(self):
        alpha = int(self.brightness)
        color = (*self.color[:3], alpha)
        surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (self.size, self.size), self.size)
        starting_screen.blit(surface, (self.x - self.size, self.y - self.size))

# Earth and Moon class (same as you had before)
class EarthAndMoon:
    def __init__(self):
        self.earth_x = 1300
        self.earth_y = 200
        self.earth_radius = 50
        self.moon_radius = 10
        self.moon_distance = 120
        self.angle = 0
        self.rotation_speed = 0.001
        self.moon_z = 0
        self.earth_rotation_angle = 0
        self.earth_rotation_speed = 0.0005

    def update(self):
        self.angle += self.rotation_speed
        self.earth_rotation_angle += self.earth_rotation_speed
        self.moon_z = math.sin(self.angle) * self.moon_distance

    def draw(self):
        rotated_earth = pygame.transform.rotate(earth_texture, math.degrees(self.earth_rotation_angle))
        earth_rect = rotated_earth.get_rect(center=(self.earth_x, self.earth_y))
        starting_screen.blit(rotated_earth, earth_rect)
        moon_x = self.earth_x + math.cos(self.angle) * self.moon_distance
        moon_y = self.earth_y + math.sin(self.angle) * self.moon_distance
        moon_size = max(5, 30 * (1 - abs(self.moon_z) / self.moon_distance))
        moon_alpha = int(255 * (1 - abs(self.moon_z) / self.moon_distance))
        moon_surface = pygame.Surface((moon_size * 2, moon_size * 2), pygame.SRCALPHA)
        moon_surface.blit(pygame.transform.scale(moon_texture, (moon_size * 2, moon_size * 2)), (0, 0))
        moon_surface.set_alpha(moon_alpha)
        starting_screen.blit(moon_surface, (moon_x - moon_size, moon_y - moon_size))

# Create a list of stars
stars = [Star() for _ in range(300)]

# Create the Earth and Moon

earth_and_moon = EarthAndMoon()

# Starting Screen

starting_screen = pygame.display.set_mode((1500, 750))
starting_font_text = pygame.font.SysFont('CenturySchoolBook', 100)
starting_font_button = pygame.font.SysFont('CenturySchoolBook', 20)
logo_downscaled = pygame.transform.scale(logo, (300, 300))

def show_start_screen():
    start_button = Special_button(200, 630, 170, 100, "START", starting_font_button, WHITE, GREEN, (144, 238, 144), 
                                  starting_screen, action=lambda: None)
    quit_button = Button(16, 630, 170, 100, "QUIT", starting_font_button, WHITE, RED, action=lambda: None, button_color_pressed = (255, 150, 150),
                          message="\nYou have left AMIS' Interface of Control!")

    while True:
        starting_screen.fill((0, 0, 0))
        
        for y in range(750):
            color = (
                int(DARK_BLUE[0] * (y / 750)),
                int(DARK_BLUE[1] * (y / 750)),
                int(DARK_BLUE[2] * (y / 750))
            )
            pygame.draw.line(starting_screen, color, (0, y), (1500, y))

        for star in stars:
            star.twinkle()
            star.draw()

        earth_and_moon.update()
        earth_and_moon.draw()

        starting_screen.blit(quit_button.image, quit_button.rect)
        starting_screen.blit(start_button.image, start_button.rect)

        pygame.draw.rect(starting_screen, YELLOW, (198, 628, 174, 104), 2)
        pygame.draw.rect(starting_screen, YELLOW, (14, 628, 174, 104), 2)

        logo_downscaled_rect = logo_downscaled.get_rect(center=(465, 300))
        text = starting_font_text.render("AQUAMIS", True, YELLOW)
        text_rect = text.get_rect(center=(915, 300))
        starting_screen.blit(text, text_rect)
        starting_screen.blit(logo_downscaled, logo_downscaled_rect)
        start_button.draw(starting_screen, starting_font_button)

        mouse_pos = pygame.mouse.get_pos()
        start_button.update(mouse_pos)
        quit_button.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                start_button.click(mouse_pos)
                quit_button.click(mouse_pos)
                
                if quit_button.rect.collidepoint(mouse_pos):
                    sys.exit()
            
                if start_button.is_clicked(mouse_pos):
                    start_button.start_trigger()
                
            if event.type == pygame.KEYDOWN:
                result = start_button.handle_event_start(event)   
                if result == "switch_screen":
                    return
        
        pygame.display.flip()

def main():

    # Defining screen's dimesions - timer - font

    screen = pygame.display.set_mode((1500,750))
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont('CenturySchoolbook', 20)
    font2 = pygame.font.SysFont('CenturySchoolBook', 15)
    font4 = pygame.font.SysFont('CenturySchoolBook', 35)
    font18 = pygame.font.SysFont('CenturySchoolBook', 18)
    start_time = time.time()

    # Creating communication boxes to verify the state of AMIS' components

    BOX_WIDTH, BOX_HEIGHT = 170, 67

    comm_box            = CommunicationBox(1215, 543, BOX_WIDTH, BOX_HEIGHT, font2, WHITE, GREEN, RED, "COMMS: OK")
    cam_box             = CommunicationBox(1215, 620, BOX_WIDTH, BOX_HEIGHT, font2, WHITE, GREEN, RED, "CAM: OK")
    mpu_box             = CommunicationBox(1215, 697, BOX_WIDTH, BOX_HEIGHT, font2, WHITE, GREEN, RED, "MPU: OK")
    servo_box           = CommunicationBox(1395, 543, BOX_WIDTH, BOX_HEIGHT, font2, WHITE, GREEN, RED, "SERVO: OK")
    motor_box           = CommunicationBox(1395, 620, BOX_WIDTH, BOX_HEIGHT, font2, WHITE, GREEN, RED, "ENGINE: OK")
    pressure_sensor_box = CommunicationBox(1395, 697, BOX_WIDTH, BOX_HEIGHT, font2, WHITE, GREEN, RED, "PRESSURE: OK")

    # Creating decorative boxes (to make the interface well organized)

    BW, BH = 1500, 10

    # Horizontal lines

    lineh1 = DecorativeBox(750, 495, BW, BH, font2, YELLOW, GRAY, '')
    lineh2 = DecorativeBox(750, 745, BW, BH, font, YELLOW, GRAY, '')
    lineh3 = DecorativeBox(750, 5, BW, BH, font, YELLOW, GRAY, '')
    lineh4 = DecorativeBox(195, 385, 370, BH, font, GRAY, GRAY, '')
    lineh5 = DecorativeBox(1305, 385, 370, BH, font, GRAY, GRAY, '')

    # Vertical lines

    linev1 = DecorativeBox(1115, 375, BH, 750, font, GRAY, GRAY, "")
    linev2 = DecorativeBox(1495, 375, BH, 750, font, GRAY, GRAY, "")
    linev3 = DecorativeBox(5, 375, BH, 750, font, GRAY, GRAY, "")
    linev4 = DecorativeBox(385, 375, BH, 750, font, GRAY, GRAY, "")
    linev5 = DecorativeBox(930, 620, BH, 240, font, GRAY, GRAY, "")

    # Logo's box (the one in the middle of the direction commands)

    AMIS_box  = DecorativeBox(750, 620, 107, 67, font2, YELLOW, GRAY, '')

    # Creating diection commands

    button_color = (75, 75, 75)

    button_forward   = Button(697, 500, 107, 85, 'FORWARD', font2, WHITE, button_color, button_action, BCP, "AMIS is going FORWARD!")
    button_left      = Button(577, 587, 118, 67, 'LEFT', font2, WHITE, button_color, button_action, BCP, "AMIS is going LEFT!")
    button_right     = Button(806, 587, 118, 67, 'RIGHT', font2, WHITE, button_color, button_action, BCP, "AMIS is going RIGHT!")
    button_backward  = Button(697, 655, 107, 84, 'BACKWARD', font2, WHITE, button_color, button_action, BCP, "AMIS is going BACKWARD!" )
    button_up        = Button(970, 508, 108, 108, 'UPWARD', font2, WHITE, button_color, button_action, BCP,"AMIS is going UP!")
    button_down      = Button(970, 625, 108, 108, 'DOWNWARD', font2, WHITE, button_color, button_action, BCP,"AMIS is going DOWN!")

    # Start, Stop, Emergency Stop and Switch Com buttons

    button_start          = Button(200, 630, 170, 100, 'ALREADY RUNNING', font2, WHITE, GREEN, button_action, (100,255,100), "")
    button_stop           = Special_button(20, 630, 170, 100, 'STOP', font, WHITE, (139,0,0),(255,100,100), button_action,"")
    button_emergency_stop = Button(20, 510, 350, 110, 'EMERGENCY STOP', font, WHITE, (139,0,0), button_action, (255,100,100), 
                                   "EMERGENCY STOP HAS BEEN TRIGGERED - AMIS HAS BEEN STOPPED!")
    switch_com            = Button(20, 400, 350, 80, 'SWITCH COM', font, WHITE, button_color, button_action, BCP, "Comms have been switched!")

    # Display and Save Data buttons

    button_display_data = Button(1310, 400, 170, 80, 'DISPLAY DATA', font, WHITE, button_color, button_action, BCP, "Now displaying Data!")
    button_save_data = Button(1130, 400, 170, 80, 'SAVE DATA', font, WHITE, button_color, button_action, BCP, "Currently saving Data...")
    
    # Listing sprites
    
    all_buttons = [button_forward, button_left, button_right, button_backward,
                   button_up, button_down, button_emergency_stop, 
                   switch_com, button_display_data, button_save_data]

    all_sprites = pygame.sprite.Group()
    all_sprites.add(
        button_forward, button_left, button_right, button_backward,
        button_up, button_down, switch_com, AMIS_box,
        button_display_data, button_save_data, button_emergency_stop,  
        button_start, comm_box, cam_box, mpu_box, servo_box, motor_box, 
        pressure_sensor_box, lineh1, lineh2, lineh3, lineh4, lineh5,
        linev1, linev2, linev3, linev4, linev5,
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

    speed_clock = ProgressBar(435, 510, 30, 220)

    # Variables

    input_active = False
    input_text = ""

    # Graphs Main

    graph_motor_depth = Graphs_Main(
            screen, 240, 170, 255, 50, 
            (255, 0, 0), (0, 0, 255), 
            "", "", 
            target_motor=150, target_depth=25
            )

    # Defining Main 

    running = True

    while running:
        
        keys = pygame.key.get_pressed()
        speed_clock.update(keys)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                button_stop.handle_event_stop(event)
                comm_box.update_status() 

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if 485 <= event.pos[0] <= 585 and 690 <= event.pos[1] <= 730:
                    input_active = True
                    input_text = ""
                else: 
                    input_active = False
                
                if button_stop.is_clicked(event.pos):
                    button_stop.stop_trigger()

                if button_display_data.rect.collidepoint(mouse_pos):
                    thread = Thread(target=PygameTkinterInterface.open_tkinter_window)
                    thread.start()
                
                for button in all_buttons:
                    if button.rect.collidepoint(mouse_pos):
                        button.click(mouse_pos)
                
            if event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_RETURN:
                    if input_text.isdigit():
                        new_speed = int(input_text)
                        speed_clock.set_speed(new_speed)
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
        
        screen.fill((0, 0, 0))
        button_stop.draw(screen, font)
        
        # Graphs in Main
        
        pygame.draw.rect(screen, (30, 30, 30), (1120, 10, 370, 370))
        pygame.draw.rect(screen, RED, (1120,195, 255, 2))
        pygame.draw.rect(screen, RED, (1375, 10, 2, 370))
        pygame.draw.rect(screen, RED, (1375, 165, 115, 60),2)
        graph_motor_depth.update_graph_main()

        # Speed bar

        pygame.draw.rect(screen, GRAY, (390, 490, 200, 300))
        speed_clock.draw(screen)  

        pygame.draw.rect(screen, (0, 0, 0), (485, 690, 100, 40))
        pygame.draw.rect(screen, (139, 0, 0), (485, 690, 100, 40), 2)
    
        speed_text = font.render(input_text if input_active else str(speed_clock.speed), True, (255, 255, 255))
        text_rect = speed_text.get_rect(center=(535,710))
        screen.blit(speed_text, text_rect)
        
        # Displaying Timer

        elapsed_time = time.time() - start_time

        minutes = int(elapsed_time) // 60
        seconds = int(elapsed_time) % 60
        time_display = f"{minutes:02d} min {seconds:02d} s"
        time_surface = font18.render(time_display, True, WHITE)
        time_rect = time_surface.get_rect(center=(1433, 195))
        screen.blit(time_surface, time_rect)
        
        # Buttons' update and displaying of static sprites
        
        mouse_pos = pygame.mouse.get_pos()
        for button in all_buttons:
            button.update(mouse_pos)
        button_stop.update(mouse_pos)
        button_stop.draw(screen, font)
        all_sprites.draw(screen)

        # Initialization of the areas (cube and graphs)

        pygame.draw.rect(screen, (30, 30, 30), (12, 12, 368, 368))
        pygame.draw.rect(screen, RED, (10, 10, 370, 370), 2)
        pygame.draw.rect(screen, RED, (1120, 10, 370, 370), 2)

        # Animation and drawing of the cube

        cube_sprite_group.update()
        cube_sprite_group.draw(screen)
        
        # More Decorations for aesthetic purposes

        pygame.draw.rect(screen, RED, (390, 10, 720, 480), 2)
        pygame.draw.rect(screen, RED, (575, 585, 350, 71), 2)
        pygame.draw.rect(screen, RED, (695, 500, 111, 240), 2)
        pygame.draw.rect(screen, GRAY, (575, 500, 120, 85))
        pygame.draw.rect(screen, GRAY, (806, 500, 120, 85))
        pygame.draw.rect(screen, GRAY, (585, 656, 110, 85))
        pygame.draw.rect(screen, GRAY, (806, 656, 120, 85))
        pygame.draw.rect(screen, RED, (968, 506, 110, 110), 2)
        pygame.draw.rect(screen, RED, (968, 623, 110, 110), 2)
        pygame.draw.rect(screen, RED,(1120,390,370,100),2)
        pygame.draw.rect(screen, RED, (10,390,370,100),2)
        pygame.draw.rect(screen, RED, (10,500,370,240),2)
        pygame.draw.rect(screen, RED, (1120,500,370,240),2)
        pygame.draw.rect(screen, RED, (1130, 400, 170, 80),2)
        pygame.draw.rect(screen, RED, (1310, 400, 170, 80),2)
        pygame.draw.rect(screen, GRAY, (390, 500, 31, 233))
        pygame.draw.rect(screen, GRAY, (934, 500, 34, 233))
        pygame.draw.rect(screen, GRAY, (1078, 500, 34, 233))
        pygame.draw.rect(screen, GRAY, (390, 733, 180, 10))
        pygame.draw.rect(screen, GRAY, (930, 733, 180, 10))
        pygame.draw.rect(screen, GRAY, (390, 496, 180, 10))
        pygame.draw.rect(screen, GRAY, (930, 616, 180, 7))
        pygame.draw.rect(screen, GRAY, (930, 496, 180, 10))
        
        # Logo and associated text (bottom right corner)

        screen.blit(logo_amis_big, logo_amis_big_rect)
        screen.blit(logo_amis_small, logo_amis_small_rect)
        text = font.render("AQUAMIS", True, YELLOW)
        text_rect = text.get_rect(center=(320, 30))
        screen.blit(text, text_rect)
        
        # Central image display

        image = pygame.image.load("ISS.jpg")
        image = pygame.transform.scale(image, (716, 476))
        image_rect = image.get_rect(center=(750,250))
        screen.blit(image, image_rect)

        # Telemetry
        
        telemetry_font = pygame.font.SysFont('CenturySchoolbook', 12)
        screen.blit(telemetry_font.render("ROLL :", True, (255,0,0)), (45, 347))
        screen.blit(telemetry_font.render("PITCH :", True, (0,255,0)), (150, 347))
        screen.blit(telemetry_font.render("YAW :", True, BLUE), (257, 347))
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

show_start_screen()  

if __name__ == '__main__':
    main()
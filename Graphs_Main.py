import pygame
import random
import time

class Graphs_Main:
    def __init__(self, surface, width, height, max_value_motor, max_value_depth, color_motor, color_depth, label_motor, label_depth, target_motor, target_depth, x_offset=1127, y_offset=201, max_time=10, grid_spacing=20):
        self.surface = surface
        self.width = width
        self.height = height
        self.max_value_motor = max_value_motor
        self.max_value_depth = max_value_depth
        self.color_motor = color_motor
        self.color_depth = color_depth
        self.label_motor = label_motor
        self.label_depth = label_depth
        self.target_motor = target_motor  
        self.target_depth = target_depth  
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.max_time = max_time
        self.grid_spacing = grid_spacing  
        self.depth_progress = 0
        self.data_motor = []
        self.data_depth = []
        self.time_stamps = []
        
    def add_data(self, value_motor, value_depth):
        current_time = time.time()
        
        self.data_motor.append(value_motor)
        self.data_depth.append(value_depth)
        self.time_stamps.append(current_time)
        
        while self.time_stamps[0] < current_time - self.max_time:
            self.data_motor.pop(0)
            self.data_depth.pop(0)
            self.time_stamps.pop(0)
    
    def draw_grid(self):
       
        for x in range(self.x_offset, self.x_offset + self.width, self.grid_spacing):
            pygame.draw.line(self.surface, (50, 50, 50), (x, self.y_offset), (x, self.y_offset + self.height), 1)
        
        for y in range(self.y_offset, self.y_offset + self.height, self.grid_spacing):
            pygame.draw.line(self.surface, (50, 50, 50), (self.x_offset, y), (self.x_offset + self.width, y), 1)
    
    def draw(self):
        self.draw_grid()  
        
        font = pygame.font.SysFont('Arial', 20)
        text_motor = font.render(self.label_motor, True, (255, 255, 255))
        self.surface.blit(text_motor, (self.x_offset + 5, self.y_offset - 20))
        
        text_depth = font.render(self.label_depth, True, (255, 255, 255))
        self.surface.blit(text_depth, (self.x_offset + 5, self.y_offset - 40))
        
        legend_font = pygame.font.SysFont('CenturySchoolBook', 15)

        if len(self.data_motor) > 0 and len(self.data_depth) > 0:
            current_motor_value = self.data_motor[-1]
            current_depth_value = self.data_depth[-1]
            
            motor_value_text = legend_font.render(f"Motor: {int(current_motor_value)}", True, (255,255,255))
            depth_value_text = legend_font.render(f"Depth: {int(current_depth_value)} m", True, (255,255,255))
            
            self.surface.blit(motor_value_text, (self.x_offset + self.width + 20, self.y_offset + 70))
            self.surface.blit(depth_value_text, (self.x_offset + self.width + 20, self.y_offset + 100))

        if len(self.data_motor) > 1 and len(self.data_depth) > 1:
            start_time = self.time_stamps[0]
            
            for i in range(1, len(self.data_motor)):
                elapsed_time = self.time_stamps[i] - start_time  
                
                start_x_motor = self.x_offset + (elapsed_time) * (self.width / (self.time_stamps[-1] - start_time))
                start_y_motor = self.y_offset + self.height - (self.data_motor[i - 1] / self.max_value_motor) * self.height
                end_x_motor = self.x_offset + ((elapsed_time + (self.time_stamps[i] - self.time_stamps[i - 1])) * (self.width / (self.time_stamps[-1] - start_time)))
                end_y_motor = self.y_offset + self.height - (self.data_motor[i] / self.max_value_motor) * self.height
                
                pygame.draw.line(self.surface, self.color_motor, (start_x_motor, start_y_motor), (end_x_motor, end_y_motor), 2)
                
                start_x_depth = self.x_offset + (elapsed_time) * (self.width / (self.time_stamps[-1] - start_time))
                start_y_depth = self.y_offset + self.height - (self.data_depth[i - 1] / self.max_value_depth) * self.height
                end_x_depth = self.x_offset + ((elapsed_time + (self.time_stamps[i] - self.time_stamps[i - 1])) * (self.width / (self.time_stamps[-1] - start_time)))
                end_y_depth = self.y_offset + self.height - (self.data_depth[i] / self.max_value_depth) * self.height
                
                pygame.draw.line(self.surface, self.color_depth, (start_x_depth, start_y_depth), (end_x_depth, end_y_depth), 2)
        
        pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset+1, self.y_offset), (self.x_offset+1, self.y_offset + self.height), 4)
        pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset, self.y_offset + self.height), (self.x_offset + self.width, self.y_offset + self.height), 4)

    def update_graph_main(self):
        
        fluctuation_motor = random.randint(-10, 10)
        
        if self.depth_progress < 10:
                self.depth_progress += 0.01 
        else:
            self.depth_progress = 10

        fluctuation_depth = self.depth_progress

        new_motor_value = self.target_motor + fluctuation_motor
        new_depth_value = self.target_depth + fluctuation_depth

        new_motor_value = max(0, min(255, new_motor_value))
        new_depth_value = max(0, min(50, new_depth_value))
        
        self.add_data(new_motor_value, new_depth_value)
        self.draw()

import pygame
import random
import time

class Graphs_Main:
    def __init__(self, surface, width, height, max_value_pressure, max_value_depth, color_pressure, color_depth, label_pressure, label_depth, target_pressure, target_depth, x_offset=1127, y_offset=201, max_time=10, grid_spacing=20):
        self.surface = surface
        self.width = width
        self.height = height
        self.max_value_pressure = max_value_pressure
        self.max_value_depth = max_value_depth
        self.color_pressure = color_pressure
        self.color_depth = color_depth
        self.label_pressure = label_pressure
        self.label_depth = label_depth
        self.target_pressure = target_pressure  
        self.target_depth = target_depth  
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.max_time = max_time
        self.grid_spacing = grid_spacing  
        self.depth_progress = 0
        self.data_pressure = []
        self.data_depth = []
        self.time_stamps = []
        
    def add_data(self, value_pressure, value_depth):
        current_time = time.time()
        
        self.data_pressure.append(value_pressure)
        self.data_depth.append(value_depth)
        self.time_stamps.append(current_time)
        
        while self.time_stamps[0] < current_time - self.max_time:
            self.data_pressure.pop(0)
            self.data_depth.pop(0)
            self.time_stamps.pop(0)
    
    def draw_grid(self):
        return
    
    def draw(self):
        self.draw_grid()  
        
        font = pygame.font.SysFont('Arial', 20)
        text_pressure = font.render(self.label_pressure, True, (255, 255, 255))
        self.surface.blit(text_pressure, (self.x_offset + 5, self.y_offset - 20))
        
        text_depth = font.render(self.label_depth, True, (255, 255, 255))
        self.surface.blit(text_depth, (self.x_offset + 5, self.y_offset - 40))
        
        legend_font = pygame.font.SysFont('CenturySchoolBook', 15)

        if len(self.data_pressure) > 0 and len(self.data_depth) > 0:
            current_pressure_value = self.data_pressure[-1]
            current_depth_value = self.data_depth[-1]
            
            pressure_value_text = legend_font.render(f"Pressure: {int(current_pressure_value)}", True, (255,0,0))
            depth_value_text = legend_font.render(f"Depth: {int(current_depth_value)} m", True, (0,0,255))
            
            self.surface.blit(pressure_value_text, (self.x_offset + self.width + 20, self.y_offset + 100))
            self.surface.blit(depth_value_text, (self.x_offset + self.width + 20, self.y_offset + 70))

        if len(self.data_pressure) > 1 and len(self.data_depth) > 1:
            start_time = self.time_stamps[0]
            
            for i in range(1, len(self.data_pressure)):
                elapsed_time = self.time_stamps[i] - start_time  
                
                start_x_pressure = self.x_offset + (elapsed_time) * (self.width / (self.time_stamps[-1] - start_time))
                start_y_pressure = self.y_offset + self.height - (self.data_pressure[i - 1] / self.max_value_pressure) * self.height
                end_x_pressure = self.x_offset + ((elapsed_time + (self.time_stamps[i] - self.time_stamps[i - 1])) * (self.width / (self.time_stamps[-1] - start_time)))
                end_y_pressure = self.y_offset + self.height - (self.data_pressure[i] / self.max_value_pressure) * self.height
                
                pygame.draw.line(self.surface, self.color_pressure, (start_x_pressure, start_y_pressure), (end_x_pressure, end_y_pressure), 2)
                
                start_x_depth = self.x_offset + (elapsed_time) * (self.width / (self.time_stamps[-1] - start_time))
                start_y_depth = self.y_offset + self.height - (self.data_depth[i - 1] / self.max_value_depth) * self.height
                end_x_depth = self.x_offset + ((elapsed_time + (self.time_stamps[i] - self.time_stamps[i - 1])) * (self.width / (self.time_stamps[-1] - start_time)))
                end_y_depth = self.y_offset + self.height - (self.data_depth[i] / self.max_value_depth) * self.height
                
                pygame.draw.line(self.surface, self.color_depth, (start_x_depth, start_y_depth), (end_x_depth, end_y_depth), 2)
        
        pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset+1, self.y_offset), (self.x_offset+1, self.y_offset + self.height), 2)
        pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset, self.y_offset + self.height), (self.x_offset + self.width, self.y_offset + self.height), 2)

    def update_graph_main(self):
        fluctuation_pressure = random.uniform(-0.2, 0.2)
        new_pressure_value = self.target_pressure + fluctuation_pressure
        new_pressure_value = max(11.8, min(12.2, new_pressure_value))

        if self.depth_progress < 10:
            self.depth_progress += 0.01 
        else:
            self.depth_progress = 10

        new_depth_value = self.target_depth + self.depth_progress
        new_depth_value = max(0, min(self.max_value_depth, new_depth_value))
        
        self.add_data(new_pressure_value, new_depth_value)
        self.draw()

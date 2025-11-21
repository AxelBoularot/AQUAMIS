import pygame
import time

class Graphs_Angles:
    def __init__(self, surface, width, height, max_value, x_offset=1127, y_offset=19, max_time=10, grid_spacing=20):
        self.surface = surface
        self.width = width
        self.height = height
        self.max_value = max_value
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.max_time = max_time
        self.grid_spacing = grid_spacing
        
        self.data_roll = []
        self.data_pitch = []
        self.data_yaw = []
        self.time_stamps = []
    
    def add_data(self, roll, pitch, yaw):
        current_time = time.time()
        
        self.data_roll.append(roll)
        self.data_pitch.append(pitch)
        self.data_yaw.append(yaw)
        self.time_stamps.append(current_time)
        
        while self.time_stamps[0] < current_time - self.max_time:
            self.data_roll.pop(0)
            self.data_pitch.pop(0)
            self.data_yaw.pop(0)
            self.time_stamps.pop(0)
    
    def draw_grid(self):
        for x in range(self.x_offset, self.x_offset + self.width, self.grid_spacing):
            pygame.draw.line(self.surface, (50, 50, 50), (x, self.y_offset), (x, self.y_offset + self.height), 1)
        
        for y in range(self.y_offset, self.y_offset + self.height, self.grid_spacing):
            pygame.draw.line(self.surface, (50, 50, 50), (self.x_offset, y), (self.x_offset + self.width, y), 1)
    
    def draw(self):
        self.draw_grid()
        colors = {'roll': (255, 0, 0), 'pitch': (0, 255, 0), 'yaw': (0, 0, 255)}

        if len(self.data_roll) > 1:
            start_time = self.time_stamps[0]
            
            for i in range(1, len(self.data_roll)):
                elapsed_time = self.time_stamps[i] - start_time
                
                for data, color in zip([self.data_roll, self.data_pitch, self.data_yaw], colors.values()):
                    start_x = self.x_offset + elapsed_time * (self.width / self.max_time)
                    start_y = self.y_offset + self.height - (data[i-1] / self.max_value) * self.height
                    end_x = self.x_offset + (elapsed_time + (self.time_stamps[i] - self.time_stamps[i-1])) * (self.width / self.max_time)
                    end_y = self.y_offset + self.height - (data[i] / self.max_value) * self.height
                    
                    pygame.draw.line(self.surface, color, (start_x, start_y), (end_x, end_y), 2)
        
        pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset, self.y_offset), (self.x_offset, self.y_offset + self.height), 2)
        pygame.draw.line(self.surface, (255, 255, 255), (self.x_offset, self.y_offset + self.height), (self.x_offset + self.width, self.y_offset + self.height), 2)
    
    def update_graph_angles(self, roll, pitch, yaw):
        self.add_data(roll, pitch, yaw)
        self.draw()

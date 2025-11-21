import pygame
import math

def rotate_point(point, angle_x, angle_y, angle_z):
    # Conversion des angles de degrés en radians
    rad_x = math.radians(angle_x)
    rad_y = math.radians(angle_y)
    rad_z = math.radians(angle_z)
    
    x, y, z = point
    
    cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
    y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
    
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y
    
    cos_z, sin_z = math.cos(rad_z), math.sin(rad_z)
    x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z
    
    return (x, y, z)

def project_point(point, screen_width, screen_height, fov, viewer_distance):
    x, y, z = point
    factor = fov / (viewer_distance + z)
    x_proj = x * factor + screen_width / 2
    y_proj = -y * factor + screen_height / 2
    return (int(x_proj), int(y_proj))

class Cube(pygame.sprite.Sprite):
    def __init__(self, position=(200, 200), size=4, fov=256, viewer_distance=4):
        super().__init__()
        self.position = position
        self.size = size
        self.fov = fov
        self.viewer_distance = viewer_distance
        self.angle_x = 0
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.vertices = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ]
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        self.image = pygame.Surface((400, 400), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.position)
    
    def get_transformed_vertices(self, angle_x, angle_y, angle_z):
        return [rotate_point((v[0] * self.size, v[1] * self.size, v[2] * self.size), angle_x, angle_y, angle_z) for v in self.vertices]

    def update(self,angle_x,angle_y,angle_z):
        
        self.angle_x = (angle_x) % 360  
        self.angle_y = (angle_y) % 360  
        self.angle_z = (angle_z) % 360  

        self.image.fill((0, 0, 0, 0))
        transformed_vertices = self.get_transformed_vertices(self.angle_x, self.angle_y, self.angle_z)
        projected_points = [project_point(v, self.rect.width, self.rect.height, self.fov, self.viewer_distance) for v in transformed_vertices]
        for edge in self.edges:
            pygame.draw.line(self.image, (169, 169, 169), projected_points[edge[0]], projected_points[edge[1]], 2)
    
        center_transformed = rotate_point((0, 0, 0), self.angle_x, self.angle_y, self.angle_z)
        x_axis_transformed = rotate_point((2 * self.size, 0, 0), self.angle_x, self.angle_y, self.angle_z)
        y_axis_transformed = rotate_point((0, 2 * self.size, 0), self.angle_x, self.angle_y, self.angle_z)
        z_axis_transformed = rotate_point((0, 0, 2 * self.size), self.angle_x, self.angle_y, self.angle_z)
    
        center = project_point(center_transformed, self.rect.width, self.rect.height, self.fov, self.viewer_distance)
        x_axis = project_point(x_axis_transformed, self.rect.width, self.rect.height, self.fov, self.viewer_distance)
        y_axis = project_point(y_axis_transformed, self.rect.width, self.rect.height, self.fov, self.viewer_distance)
        z_axis = project_point(z_axis_transformed, self.rect.width, self.rect.height, self.fov, self.viewer_distance)
        
        pygame.draw.line(self.image, (255, 0, 0), center, x_axis, 2)  # Axe X en rouge
        pygame.draw.line(self.image, (0, 255, 0), center, y_axis, 2)  # Axe Y en vert
        pygame.draw.line(self.image, (0, 0, 255), center, z_axis, 2)  # Axe Z en bleu

        font = pygame.font.Font(None, 24)
        text_x = font.render(f"{self.angle_x:.2f}", True, (255, 0, 0))  # Rouge
        text_y = font.render(f"{self.angle_y:.2f}", True, (0, 255, 0))  # Vert
        text_z = font.render(f"{self.angle_z:.2f}", True, (0, 0, 255))  # Bleu
        self.image.blit(text_x, (105, 367))
        self.image.blit(text_y, (210, 367))
        self.image.blit(text_z, (310, 367))

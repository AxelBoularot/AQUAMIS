import pygame
import math
from dependencies.Variable import BLUE, YELLOW

def rotate_point(point, angle_x, angle_y, angle_z):
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
    den = viewer_distance + z
    if den <= 0.0001:
        den = 0.0001
    factor = fov / den
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
        # Angles initiaux pour que la face avant pointe vers l'utilisateur (vue 3/4)
        self.base_angle_x = 0.0   # Légère inclinaison vers le haut
        self.base_angle_y = 210.0  # 30° + 180° pour retourner la face avant
        self.base_angle_z = 0.0
        
        self.angle_x = 0
        self.angle_y = 0.0
        self.angle_z = 0.0

        # Translation offsets (visual displacement)
        self.tx = 0.0
        self.ty = 0.0
        self.tz = 0.0

        self.movement_vector = [0.0, 0.0, 0.0]  # [dx, dy, dz]

        self.vertices = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ]
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        # Face avant du cube (indices des sommets)
        self.front_face = [(4, 5), (5, 6), (6, 7), (7, 4)]
        
        self.image = pygame.Surface((400, 400), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.position)
    
    def get_transformed_vertices(self, angle_x, angle_y, angle_z):
        # Cube fixe: pas de translation (tx,ty,tz ignorés)
        transformed = []
        for v in self.vertices:
            vx = v[0] * self.size
            vy = v[1] * self.size
            vz = v[2] * self.size
            transformed.append(rotate_point((vx, vy, vz), angle_x, angle_y, angle_z))
        return transformed

    def move(self, dx, dy, dz):
        # Ne modifie pas la position, mémorise seulement le déplacement demandé
        self.movement_vector = [dx, dy, dz]

    def _draw_arrow(self, surf, start, end, color, thickness=2, head_len=10, head_w=6):
        # Ligne principale
        pygame.draw.line(surf, color, start, end, thickness)
        # Calcul flèche 2D
        vx = end[0] - start[0]
        vy = end[1] - start[1]
        length = math.hypot(vx, vy)
        if length < 1e-3:
            return
        ux, uy = vx / length, vy / length
        # Base de la flèche
        bx = end[0] - ux * head_len
        by = end[1] - uy * head_len
        # Perp
        px, py = -uy, ux
        left = (int(bx + px * head_w), int(by + py * head_w))
        right = (int(bx - px * head_w), int(by - py * head_w))
        pygame.draw.polygon(surf, color, [end, left, right])

    def update(self, angle_x, angle_y, angle_z):
        # Ajouter les angles du capteur aux angles de base
        self.angle_x = (angle_x + self.base_angle_x) % 360  
        self.angle_y = (angle_y + self.base_angle_y) % 360  
        self.angle_z = (angle_z + self.base_angle_z) % 360  

        self.image.fill((0, 0, 0, 0))
        transformed_vertices = self.get_transformed_vertices(self.angle_x, self.angle_y, self.angle_z)
        projected_points = [project_point(v, self.rect.width, self.rect.height, self.fov, self.viewer_distance) for v in transformed_vertices]

        # Arêtes du cube
        for edge in self.edges:
            pygame.draw.line(self.image, (0, 0, 0), projected_points[edge[0]], projected_points[edge[1]], 4)
            pygame.draw.line(self.image, (169, 169, 169), projected_points[edge[0]], projected_points[edge[1]], 2)

        # Contour face avant
        for edge in self.front_face:
            pygame.draw.line(self.image, BLUE, projected_points[edge[0]], projected_points[edge[1]], 3)

        # Flèche de déplacement uniquement si un axe est actif
        dx, dy, dz = self.movement_vector
        eps = 1e-6
        if abs(dx) > eps or abs(dy) > eps or abs(dz) > eps:
            center = project_point(rotate_point((0, 0, 0), self.angle_x, self.angle_y, self.angle_z), self.rect.width, self.rect.height, self.fov, self.viewer_distance)
            axis_len = 2 * self.size
            x_pos = project_point(rotate_point((axis_len, 0, 0), self.angle_x, self.angle_y, self.angle_z), self.rect.width, self.rect.height, self.fov, self.viewer_distance)
            x_neg = project_point(rotate_point((-axis_len, 0, 0), self.angle_x, self.angle_y, self.angle_z), self.rect.width, self.rect.height, self.fov, self.viewer_distance)
            y_pos = project_point(rotate_point((0, axis_len, 0), self.angle_x, self.angle_y, self.angle_z), self.rect.width, self.rect.height, self.fov, self.viewer_distance)
            y_neg = project_point(rotate_point((0, -axis_len, 0), self.angle_x, self.angle_y, self.angle_z), self.rect.width, self.rect.height, self.fov, self.viewer_distance)
            z_pos = project_point(rotate_point((0, 0, axis_len), self.angle_x, self.angle_y, self.angle_z), self.rect.width, self.rect.height, self.fov, self.viewer_distance)
            z_neg = project_point(rotate_point((0, 0, -axis_len), self.angle_x, self.angle_y, self.angle_z), self.rect.width, self.rect.height, self.fov, self.viewer_distance)

            # Sélection de l’axe dominant (toutes les flèches en jaune)
            candidates = [
                ('z', abs(dz), z_pos if dz > 0 else z_neg, YELLOW),
                ('x', abs(dx), x_pos if dx > 0 else x_neg, YELLOW),
                ('y', abs(dy), y_pos if dy > 0 else y_neg, YELLOW),
            ]
            candidates.sort(key=lambda t: t[1], reverse=True)
            axis, mag, end, color = candidates[0]
            if mag > eps:
                self._draw_arrow(self.image, center, end, color, thickness=2, head_len=10, head_w=6)

        font = pygame.font.Font(None, 24)
        """text_x = font.render(f"{self.angle_x:.2f}", True, (255, 0, 0))
        text_y = font.render(f"{self.angle_y:.2f}", True, (0, 255, 0))
        text_z = font.render(f"{self.angle_z:.2f}", True, (0, 0, 255))
        self.image.blit(text_x, (105, 367))
        self.image.blit(text_y, (210, 367))
        self.image.blit(text_z, (310, 367))"""

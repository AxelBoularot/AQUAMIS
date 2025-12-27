import math
import numpy as np
import pygame


class Cube3D:
    """
    Cube 3D avec rotations basées sur Yaw (Z), Pitch (X), Roll (Y).
    Utilise des matrices de rotation pour transformer les points 3D en 2D.
    """
    
    def __init__(self, screen_pos=(500, 300), size=40, viewer_distance=300):
        """
        Args:
            screen_pos: (x, y) position du cube sur l'écran
            size: taille du cube en unités 3D
            viewer_distance: distance du viewer au repère 3D (pour la perspective)
        """
        self.screen_pos = screen_pos
        self.size = size
        self.viewer_distance = viewer_distance
        
        # Angles en degrés
        self.yaw = 0.0    # Rotation autour de Z (horizontal)
        self.pitch = 0.0  # Rotation autour de X (avant/arrière)
        self.roll = 0.0   # Rotation autour de Y (gauche/droite)
        
        # Sommets du cube en coordonnées 3D (centrés à l'origine)
        self.vertices_local = np.array([
            [-size/2, -size/2, -size/2],  # 0
            [ size/2, -size/2, -size/2],  # 1
            [ size/2,  size/2, -size/2],  # 2
            [-size/2,  size/2, -size/2],  # 3
            [-size/2, -size/2,  size/2],  # 4
            [ size/2, -size/2,  size/2],  # 5
            [ size/2,  size/2,  size/2],  # 6
            [-size/2,  size/2,  size/2],  # 7
        ], dtype=float)
        
        # Arêtes du cube
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]
        
        self.edge_color = (100, 150, 255)
        self.vertex_color = (200, 200, 255)
    
    def _rotation_matrix_x(self, angle_deg):
        """Matrice de rotation autour de l'axe X (Pitch)"""
        a = math.radians(angle_deg)
        c, s = math.cos(a), math.sin(a)
        return np.array([
            [1,  0,  0],
            [0,  c, -s],
            [0,  s,  c],
        ])
    
    def _rotation_matrix_y(self, angle_deg):
        """Matrice de rotation autour de l'axe Y (Roll)"""
        a = math.radians(angle_deg)
        c, s = math.cos(a), math.sin(a)
        return np.array([
            [ c,  0,  s],
            [ 0,  1,  0],
            [-s,  0,  c],
        ])
    
    def _rotation_matrix_z(self, angle_deg):
        """Matrice de rotation autour de l'axe Z (Yaw)"""
        a = math.radians(angle_deg)
        c, s = math.cos(a), math.sin(a)
        return np.array([
            [c, -s,  0],
            [s,  c,  0],
            [0,  0,  1],
        ])
    
    def _project_point(self, point_3d):
        """Projette un point 3D en coordonnées 2D écran."""
        x, y, z = point_3d
        depth = self.viewer_distance + z
        if abs(depth) < 0.1:
            depth = 0.1
        
        scale = self.viewer_distance / depth
        screen_x = self.screen_pos[0] + x * scale
        screen_y = self.screen_pos[1] - y * scale
        
        return (screen_x, screen_y), depth
    
    def get_projected_vertices(self):
        """Retourne les sommets projetés et leurs profondeurs."""
        R_yaw = self._rotation_matrix_y(self.yaw)
        R_pitch = self._rotation_matrix_x(self.pitch)
        R_roll = self._rotation_matrix_z(self.roll)
        
        R = R_yaw @ R_pitch @ R_roll
        vertices_rotated = self.vertices_local @ R.T
        
        vertices_2d = {}
        depths = {}
        for i, vertex_3d in enumerate(vertices_rotated):
            vertex_2d, depth = self._project_point(vertex_3d)
            vertices_2d[i] = vertex_2d
            depths[i] = depth
        
        return vertices_2d, depths
    
    def update(self, yaw, pitch, roll):
        """Mise à jour des angles de rotation"""
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll
    
    def draw(self, surface):
        """Dessine le cube sur la surface"""
        vertices_2d, depths = self.get_projected_vertices()
        
        edges_with_depth = []
        for i, edge in enumerate(self.edges):
            v1_idx, v2_idx = edge
            avg_depth = (depths[v1_idx] + depths[v2_idx]) / 2
            edges_with_depth.append((avg_depth, edge))
        
        edges_with_depth.sort(reverse=True)
        
        for _, (v1_idx, v2_idx) in edges_with_depth:
            p1 = vertices_2d[v1_idx]
            p2 = vertices_2d[v2_idx]
            pygame.draw.line(surface, self.edge_color, p1, p2, 2)
        
        for vertex_2d in vertices_2d.values():
            pygame.draw.circle(surface, self.vertex_color, (int(vertex_2d[0]), int(vertex_2d[1])), 3)
    
    def set_screen_pos(self, x, y):
        """Définit la position du cube sur l'écran"""
        self.screen_pos = (x, y)
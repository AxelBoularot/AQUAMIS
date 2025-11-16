"""
AQUAMIS - Système de Reconstruction 3D en Temps Réel
Utilise la caméra du téléphone (IP Webcam) pour créer un modèle 3D de l'environnement
Basé sur SLAM visuel monoculaire avec estimation de profondeur
"""

import cv2
import numpy as np
import torch
import timm
import trimesh
import pygame
from pygame.locals import *
import threading
import time
import json
from pathlib import Path
from collections import deque
import math

# Configuration
PHONE_IP = "192.168.1.100"
VIDEO_URL = f"http://{PHONE_IP}:8080/videofeed"
MODEL_DEVICE = "cpu"  # Force CPU (RTX 5070 sm_120 non supporté)
MAX_POINTS = 30000  # Limite de points pour la mémoire (réduit pour performance)
DOWNSAMPLE_FACTOR = 4  # Réduction de résolution pour performance (augmenté pour rapidité)
FPS_TARGET = 5  # FPS cible pour reconstruction (réduit pour performance)

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)


class DepthEstimator:
    """Estime la profondeur à partir d'une image monoculaire avec MiDaS"""
    
    def __init__(self, model_type="MiDaS_small"):
        print(f"[DepthEstimator] Chargement du modèle {model_type}...")
        self.device = MODEL_DEVICE
        
        # Charger MiDaS depuis torch hub
        try:
            self.model = torch.hub.load("intel-isl/MiDaS", model_type)
            self.model.to(self.device)
            self.model.eval()
            
            # Charger les transformations
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
                self.transform = midas_transforms.dpt_transform
            else:
                self.transform = midas_transforms.small_transform
            
            print(f"[DepthEstimator] Modèle chargé sur {self.device}")
        except Exception as e:
            print(f"[DepthEstimator] Erreur chargement MiDaS: {e}")
            print("[DepthEstimator] Utilisation du mode sans profondeur")
            self.model = None
    
    def estimate(self, frame):
        """Estime la carte de profondeur depuis une frame RGB"""
        if self.model is None:
            # Retourner une profondeur uniforme si le modèle n'est pas chargé
            h, w = frame.shape[:2]
            return np.ones((h, w), dtype=np.float32) * 5.0
        
        try:
            # Préparer l'image
            input_batch = self.transform(frame).to(self.device)
            
            # Prédire la profondeur
            with torch.no_grad():
                prediction = self.model(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=frame.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            
            depth_map = prediction.cpu().numpy()
            
            # Normaliser entre 0 et 10 mètres (approximation)
            depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
            depth_map = depth_map * 10.0  # Scale à 10m max
            
            return depth_map
        
        except Exception as e:
            print(f"[DepthEstimator] Erreur estimation: {e}")
            h, w = frame.shape[:2]
            return np.ones((h, w), dtype=np.float32) * 5.0


class CameraCalibration:
    """Gère la calibration de la caméra"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Estimation des paramètres intrinsèques (valeurs typiques smartphone)
        # Focale approximative: focal_length = (width * 0.7) pour FOV ~60°
        self.fx = width * 0.7
        self.fy = width * 0.7
        self.cx = width / 2.0
        self.cy = height / 2.0
        
        # Matrice intrinsèque
        self.K = np.array([
            [self.fx, 0, self.cx],
            [0, self.fy, self.cy],
            [0, 0, 1]
        ], dtype=np.float32)
        
        # Coefficients de distorsion (assumés nuls)
        self.dist_coeffs = np.zeros(5)
        
        print(f"[CameraCalibration] Paramètres estimés:")
        print(f"  - Résolution: {width}x{height}")
        print(f"  - Focale: fx={self.fx:.1f}, fy={self.fy:.1f}")
        print(f"  - Centre: cx={self.cx:.1f}, cy={self.cy:.1f}")
    
    def pixel_to_3d(self, u, v, depth):
        """Convertit coordonnées pixel + profondeur en point 3D"""
        x = (u - self.cx) * depth / self.fx
        y = (v - self.cy) * depth / self.fy
        z = depth
        return np.array([x, y, z])
    
    def depth_to_point_cloud(self, depth_map, rgb_image, step=3):
        """Convertit carte de profondeur en nuage de points"""
        points = []
        colors = []
        
        h, w = depth_map.shape
        
        for v in range(0, h, step):
            for u in range(0, w, step):
                depth = depth_map[v, u]
                
                # Filtrer profondeurs invalides
                if depth <= 0 or depth > 10.0:
                    continue
                
                # Point 3D
                point = self.pixel_to_3d(u, v, depth)
                points.append(point)
                
                # Couleur RGB (normalisée 0-1)
                color = rgb_image[v, u] / 255.0
                colors.append(color)
        
        return np.array(points), np.array(colors)


class FeatureTracker:
    """Extrait et suit les features entre frames pour estimer la pose"""
    
    def __init__(self):
        # Détecteur ORB (rapide et efficace)
        self.detector = cv2.ORB_create(nfeatures=300)  # Réduit pour performance
        
        # Matcher FLANN
        FLANN_INDEX_LSH = 6
        index_params = dict(algorithm=FLANN_INDEX_LSH, table_number=6, key_size=12, multi_probe_level=1)
        search_params = dict(checks=50)
        self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        
        self.prev_frame = None
        self.prev_kp = None
        self.prev_desc = None
        
        print("[FeatureTracker] Initialisé avec ORB + FLANN")
    
    def detect_and_compute(self, frame):
        """Détecte les keypoints et calcule les descripteurs"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def match_features(self, desc1, desc2):
        """Match les descripteurs entre deux frames"""
        if desc1 is None or desc2 is None or len(desc1) < 2 or len(desc2) < 2:
            return []
        
        try:
            matches = self.matcher.knnMatch(desc1, desc2, k=2)
            
            # Ratio test de Lowe
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            
            return good_matches
        except Exception as e:
            print(f"[FeatureTracker] Erreur matching: {e}")
            return []
    
    def estimate_pose(self, kp1, kp2, matches, K):
        """Estime la pose relative entre deux frames"""
        if len(matches) < 8:
            return None, None
        
        # Extraire les points correspondants
        pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
        pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])
        
        # Calculer la matrice essentielle
        E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
        
        if E is None:
            return None, None
        
        # Récupérer rotation et translation
        _, R, t, mask = cv2.recoverPose(E, pts1, pts2, K)
        
        return R, t
    
    def process_frame(self, frame, K):
        """Traite une nouvelle frame et retourne la pose relative"""
        kp, desc = self.detect_and_compute(frame)
        
        R, t = None, None
        
        if self.prev_desc is not None:
            matches = self.match_features(self.prev_desc, desc)
            if len(matches) >= 8:
                R, t = self.estimate_pose(self.prev_kp, kp, matches, K)
        
        # Mettre à jour l'état précédent
        self.prev_frame = frame.copy()
        self.prev_kp = kp
        self.prev_desc = desc
        
        return R, t, len(kp) if kp else 0


class PointCloudBuilder:
    """Construit et gère le nuage de points 3D"""
    
    def __init__(self, max_points=MAX_POINTS):
        self.points = np.empty((0, 3), dtype=np.float32)
        self.colors = np.empty((0, 3), dtype=np.float32)
        self.max_points = max_points
        
        # Transformation cumulative (pose globale)
        self.current_pose = np.eye(4)
        
        print(f"[PointCloudBuilder] Initialisé (max {max_points} points)")
    
    def add_points(self, new_points, new_colors, R=None, t=None):
        """Ajoute de nouveaux points au nuage"""
        if len(new_points) == 0:
            return
        
        # Appliquer la transformation de pose si fournie
        if R is not None and t is not None:
            # Mise à jour de la pose cumulative
            pose_delta = np.eye(4)
            pose_delta[:3, :3] = R
            pose_delta[:3, 3] = t.flatten()
            self.current_pose = self.current_pose @ pose_delta
            
            # Transformer les nouveaux points dans le référentiel global
            ones = np.ones((len(new_points), 1))
            homogeneous = np.hstack([new_points, ones])
            transformed = (self.current_pose @ homogeneous.T).T
            new_points = transformed[:, :3]
        
        # Ajouter les points
        self.points = np.vstack([self.points, new_points])
        self.colors = np.vstack([self.colors, new_colors])
        
        # Downsampling si trop de points
        if len(self.points) > self.max_points:
            self.downsample()
    
    def downsample(self):
        """Réduit le nombre de points par échantillonnage aléatoire"""
        indices = np.random.choice(len(self.points), self.max_points, replace=False)
        self.points = self.points[indices]
        self.colors = self.colors[indices]
    
    def voxel_downsample(self, voxel_size=0.05):
        """Downsampling par voxel grid (plus intelligent)"""
        if len(self.points) == 0:
            return
        
        # Quantifier les points en voxels
        voxel_coords = np.floor(self.points / voxel_size).astype(np.int32)
        
        # Créer un dictionnaire de voxels
        voxel_dict = {}
        for i, coord in enumerate(voxel_coords):
            key = tuple(coord)
            if key not in voxel_dict:
                voxel_dict[key] = []
            voxel_dict[key].append(i)
        
        # Moyenner les points dans chaque voxel
        new_points = []
        new_colors = []
        
        for indices in voxel_dict.values():
            new_points.append(self.points[indices].mean(axis=0))
            new_colors.append(self.colors[indices].mean(axis=0))
        
        self.points = np.array(new_points, dtype=np.float32)
        self.colors = np.array(new_colors, dtype=np.float32)
    
    def get_mesh(self):
        """Crée un mesh à partir du nuage de points"""
        if len(self.points) < 10:
            return None
        
        try:
            # Créer mesh avec trimesh
            cloud = trimesh.points.PointCloud(self.points, colors=(self.colors * 255).astype(np.uint8))
            return cloud
        except Exception as e:
            print(f"[PointCloudBuilder] Erreur création mesh: {e}")
            return None
    
    def save_ply(self, filepath):
        """Sauvegarde le nuage de points en format PLY"""
        if len(self.points) == 0:
            print("[PointCloudBuilder] Aucun point à sauvegarder")
            return False
        
        try:
            cloud = self.get_mesh()
            if cloud:
                cloud.export(filepath)
                print(f"[PointCloudBuilder] Sauvegardé: {filepath} ({len(self.points)} points)")
                return True
        except Exception as e:
            print(f"[PointCloudBuilder] Erreur sauvegarde: {e}")
        
        return False
    
    def reset(self):
        """Réinitialise le nuage de points"""
        self.points = np.empty((0, 3), dtype=np.float32)
        self.colors = np.empty((0, 3), dtype=np.float32)
        self.current_pose = np.eye(4)
        print("[PointCloudBuilder] Réinitialisé")


class Reconstruction3D:
    """Pipeline complet de reconstruction 3D"""
    
    def __init__(self, video_url=VIDEO_URL):
        self.video_url = video_url
        self.running = False
        self.paused = False
        
        # Composants
        self.depth_estimator = None
        self.camera_calib = None
        self.feature_tracker = None
        self.point_cloud = PointCloudBuilder()
        
        # Capture vidéo
        self.cap = None
        self.current_frame = None
        self.depth_map = None
        
        # Stats
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()
        self.processing_time = 0
        
        # Thread
        self.thread = None
        self.lock = threading.Lock()
        
        print("[Reconstruction3D] Initialisé")
    
    def start(self):
        """Démarre la reconstruction"""
        if self.running:
            return
        
        print("[Reconstruction3D] Démarrage...")
        
        # Ouvrir le flux vidéo
        self.cap = cv2.VideoCapture(self.video_url)
        
        if not self.cap.isOpened():
            print(f"[Reconstruction3D] Erreur: impossible d'ouvrir {self.video_url}")
            return False
        
        # Lire une frame pour obtenir les dimensions
        ret, frame = self.cap.read()
        if not ret:
            print("[Reconstruction3D] Erreur: impossible de lire la vidéo")
            return False
        
        h, w = frame.shape[:2]
        h, w = h // DOWNSAMPLE_FACTOR, w // DOWNSAMPLE_FACTOR
        
        # Initialiser les composants
        print("[Reconstruction3D] Initialisation des composants...")
        self.depth_estimator = DepthEstimator("MiDaS_small")
        self.camera_calib = CameraCalibration(w, h)
        self.feature_tracker = FeatureTracker()
        
        # Démarrer le thread
        self.running = True
        self.thread = threading.Thread(target=self._reconstruction_loop, daemon=True)
        self.thread.start()
        
        print("[Reconstruction3D] Démarré")
        return True
    
    def stop(self):
        """Arrête la reconstruction"""
        print("[Reconstruction3D] Arrêt...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
        
        print("[Reconstruction3D] Arrêté")
    
    def pause(self):
        """Met en pause"""
        self.paused = not self.paused
        print(f"[Reconstruction3D] {'Pause' if self.paused else 'Reprise'}")
    
    def reset(self):
        """Réinitialise le modèle 3D"""
        with self.lock:
            self.point_cloud.reset()
            if self.feature_tracker:
                self.feature_tracker.prev_frame = None
                self.feature_tracker.prev_kp = None
                self.feature_tracker.prev_desc = None
            self.frame_count = 0
        print("[Reconstruction3D] Modèle réinitialisé")
    
    def _reconstruction_loop(self):
        """Boucle principale de reconstruction (thread)"""
        frame_time = 1.0 / FPS_TARGET
        
        while self.running:
            loop_start = time.time()
            
            if self.paused:
                time.sleep(0.1)
                continue
            
            # Vider le buffer et lire la frame la plus récente
            # Cela évite le lag en sautant les frames en attente
            for _ in range(10):  # Lire et jeter les anciennes frames
                ret = self.cap.grab()
                if not ret:
                    break
            
            # Récupérer la frame la plus récente
            ret, frame = self.cap.retrieve()
            if not ret:
                print("[Reconstruction3D] Fin du flux vidéo")
                break
            
            # Downsampling
            frame = cv2.resize(frame, (frame.shape[1] // DOWNSAMPLE_FACTOR, 
                                      frame.shape[0] // DOWNSAMPLE_FACTOR))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            process_start = time.time()
            
            # Estimation de profondeur
            depth = self.depth_estimator.estimate(frame_rgb)
            
            # Tracking des features et estimation de pose
            R, t, num_features = self.feature_tracker.process_frame(frame_rgb, self.camera_calib.K)
            
            # Générer nuage de points depuis la profondeur
            # Step augmenté à 10 pour meilleure performance
            points, colors = self.camera_calib.depth_to_point_cloud(depth, frame_rgb, step=10)
            
            # Ajouter au modèle global
            with self.lock:
                self.point_cloud.add_points(points, colors, R, t)
                self.current_frame = frame_rgb.copy()
                self.depth_map = depth.copy()
            
            self.processing_time = time.time() - process_start
            
            # Stats FPS
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.last_time >= 1.0:
                self.fps = self.frame_count / (current_time - self.last_time)
                self.frame_count = 0
                self.last_time = current_time
            
            # Attendre pour atteindre FPS cible
            elapsed = time.time() - loop_start
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
    
    def get_status(self):
        """Retourne le statut actuel"""
        with self.lock:
            return {
                "running": self.running,
                "paused": self.paused,
                "fps": self.fps,
                "points": len(self.point_cloud.points),
                "processing_ms": self.processing_time * 1000,
                "pose": self.point_cloud.current_pose.tolist()
            }
    
    def get_visualization(self):
        """Retourne les images pour visualisation"""
        with self.lock:
            frame = self.current_frame.copy() if self.current_frame is not None else None
            depth = self.depth_map.copy() if self.depth_map is not None else None
        
        return frame, depth
    
    def export_model(self, filepath):
        """Exporte le modèle 3D"""
        with self.lock:
            return self.point_cloud.save_ply(filepath)


class Visualizer3D:
    """Visualisation 3D en temps réel avec pygame"""
    
    def __init__(self, width=1600, height=900):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("AQUAMIS - Reconstruction 3D")
        
        # Vue 3D
        self.view_width = width // 2
        self.view_height = height
        
        # Caméra 3D
        self.camera_distance = 5.0
        self.camera_angle_x = 30
        self.camera_angle_y = 45
        self.zoom = 1.0
        
        # Interaction
        self.mouse_down = False
        self.last_mouse_pos = (0, 0)
        
        # Font
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Couleurs
        self.bg_color = (20, 20, 20)
        self.text_color = (255, 255, 255)
        self.grid_color = (50, 50, 50)
        
        print("[Visualizer3D] Initialisé")
    
    def project_3d_to_2d(self, points):
        """Projette points 3D vers 2D pour affichage"""
        if len(points) == 0:
            return np.empty((0, 2))
        
        # Rotation caméra
        angle_x_rad = math.radians(self.camera_angle_x)
        angle_y_rad = math.radians(self.camera_angle_y)
        
        # Matrice de rotation X
        Rx = np.array([
            [1, 0, 0],
            [0, math.cos(angle_x_rad), -math.sin(angle_x_rad)],
            [0, math.sin(angle_x_rad), math.cos(angle_x_rad)]
        ])
        
        # Matrice de rotation Y
        Ry = np.array([
            [math.cos(angle_y_rad), 0, math.sin(angle_y_rad)],
            [0, 1, 0],
            [-math.sin(angle_y_rad), 0, math.cos(angle_y_rad)]
        ])
        
        # Appliquer rotations
        rotated = points @ Rx.T @ Ry.T
        
        # Projection perspective simple
        scale = 200 * self.zoom
        center_x = self.view_width // 2
        center_y = self.view_height // 2
        
        # Distance caméra
        z = rotated[:, 2] + self.camera_distance
        z[z <= 0.1] = 0.1  # Éviter division par zéro
        
        # Projection
        projected = np.zeros((len(points), 2))
        projected[:, 0] = center_x + (rotated[:, 0] * scale) / z
        projected[:, 1] = center_y - (rotated[:, 1] * scale) / z
        
        return projected.astype(int)
    
    def draw_grid(self, surface):
        """Dessine une grille de référence"""
        grid_size = 10
        grid_step = 1.0
        
        # Points de la grille
        grid_points = []
        for i in range(-grid_size, grid_size + 1):
            for j in range(-grid_size, grid_size + 1):
                grid_points.append([i * grid_step, 0, j * grid_step])
        
        grid_points = np.array(grid_points)
        projected = self.project_3d_to_2d(grid_points)
        
        # Dessiner points
        for point in projected:
            if 0 <= point[0] < self.view_width and 0 <= point[1] < self.view_height:
                pygame.draw.circle(surface, self.grid_color, point, 1)
    
    def draw_axes(self, surface):
        """Dessine les axes X, Y, Z"""
        origin = np.array([[0, 0, 0]])
        x_axis = np.array([[2, 0, 0]])
        y_axis = np.array([[0, 2, 0]])
        z_axis = np.array([[0, 0, 2]])
        
        origin_2d = self.project_3d_to_2d(origin)[0]
        x_2d = self.project_3d_to_2d(x_axis)[0]
        y_2d = self.project_3d_to_2d(y_axis)[0]
        z_2d = self.project_3d_to_2d(z_axis)[0]
        
        # X = Rouge
        pygame.draw.line(surface, (255, 0, 0), origin_2d, x_2d, 2)
        # Y = Vert
        pygame.draw.line(surface, (0, 255, 0), origin_2d, y_2d, 2)
        # Z = Bleu
        pygame.draw.line(surface, (0, 0, 255), origin_2d, z_2d, 2)
    
    def render(self, recon, frame_rgb=None, depth_map=None):
        """Render la scène complète"""
        self.screen.fill(self.bg_color)
        
        # Zone 3D (gauche)
        view_3d = pygame.Surface((self.view_width, self.view_height))
        view_3d.fill((10, 10, 10))
        
        # Grille et axes
        self.draw_grid(view_3d)
        self.draw_axes(view_3d)
        
        # Nuage de points
        if recon and len(recon.point_cloud.points) > 0:
            points = recon.point_cloud.points.copy()
            colors = recon.point_cloud.colors.copy()
            
            # Projeter
            projected = self.project_3d_to_2d(points)
            
            # Trier par profondeur (painter's algorithm)
            depths = points[:, 2]
            sorted_indices = np.argsort(depths)
            
            # Dessiner les points (du plus loin au plus proche)
            # Afficher seulement 1 point sur 3 pour performance
            for i, idx in enumerate(sorted_indices):
                if i % 3 != 0:  # Skip 2 points sur 3
                    continue
                x, y = projected[idx]
                if 0 <= x < self.view_width and 0 <= y < self.view_height:
                    color = (colors[idx] * 255).astype(int)
                    color = np.clip(color, 0, 255)
                    pygame.draw.circle(view_3d, tuple(color), (x, y), 2)
        
        self.screen.blit(view_3d, (0, 0))
        
        # Zone info (droite)
        info_x = self.view_width + 10
        
        # Flux vidéo
        if frame_rgb is not None:
            try:
                # Redimensionner pour affichage
                display_width = self.width - self.view_width - 20
                display_height = 300
                frame_resized = cv2.resize(frame_rgb, (display_width, display_height))
                
                # Convertir en surface pygame
                frame_surface = pygame.surfarray.make_surface(np.transpose(frame_resized, (1, 0, 2)))
                self.screen.blit(frame_surface, (info_x, 10))
                
                # Titre
                text = self.font.render("Flux Vidéo", True, self.text_color)
                self.screen.blit(text, (info_x, display_height + 15))
            except Exception as e:
                pass
        
        # Carte de profondeur
        if depth_map is not None:
            try:
                display_width = self.width - self.view_width - 20
                display_height = 300
                
                # Normaliser pour affichage
                depth_normalized = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
                depth_colored = (depth_normalized * 255).astype(np.uint8)
                depth_colored = cv2.applyColorMap(depth_colored, cv2.COLORMAP_JET)
                depth_colored = cv2.cvtColor(depth_colored, cv2.COLOR_BGR2RGB)
                
                depth_resized = cv2.resize(depth_colored, (display_width, display_height))
                depth_surface = pygame.surfarray.make_surface(np.transpose(depth_resized, (1, 0, 2)))
                self.screen.blit(depth_surface, (info_x, 350))
                
                # Titre
                text = self.font.render("Carte de Profondeur", True, self.text_color)
                self.screen.blit(text, (info_x, 655))
            except Exception as e:
                pass
        
        # Stats
        if recon:
            status = recon.get_status()
            y_offset = 700
            
            stats = [
                f"FPS: {status['fps']:.1f}",
                f"Points: {status['points']:,}",
                f"Processing: {status['processing_ms']:.1f} ms",
                f"Status: {'RUNNING' if status['running'] else 'STOPPED'}",
                f"{'PAUSED' if status['paused'] else ''}",
            ]
            
            for i, stat in enumerate(stats):
                if stat.strip():
                    text = self.font_small.render(stat, True, self.text_color)
                    self.screen.blit(text, (info_x, y_offset + i * 25))
        
        # Contrôles
        y_offset = 820
        controls = [
            "Contrôles:",
            "Souris: Rotation caméra",
            "Molette: Zoom",
            "R: Reset",
            "S: Sauvegarder",
            "ESC: Quitter"
        ]
        
        for i, control in enumerate(controls):
            text = self.font_small.render(control, True, (150, 150, 150))
            self.screen.blit(text, (info_x, y_offset + i * 20))
        
        pygame.display.flip()
    
    def handle_events(self, recon):
        """Gère les événements pygame"""
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return False
                elif event.key == K_r:
                    recon.reset()
                elif event.key == K_s:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filepath = f"reconstruction_{timestamp}.ply"
                    recon.export_model(filepath)
                    print(f"Sauvegardé: {filepath}")
                elif event.key == K_SPACE:
                    recon.pause()
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_down = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # Scroll up
                    self.zoom *= 1.1
                elif event.button == 5:  # Scroll down
                    self.zoom *= 0.9
            
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_down = False
            
            elif event.type == MOUSEMOTION:
                if self.mouse_down:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    
                    self.camera_angle_y += dx * 0.5
                    self.camera_angle_x += dy * 0.5
                    
                    # Limiter angle X
                    self.camera_angle_x = max(-89, min(89, self.camera_angle_x))
                    
                    self.last_mouse_pos = event.pos
        
        return True


def main():
    """Fonction principale avec visualisation 3D en temps réel"""
    print("=" * 60)
    print("AQUAMIS - Reconstruction 3D en Temps Réel")
    print("=" * 60)
    print()
    print("Contrôles:")
    print("  Souris: Rotation caméra 3D")
    print("  Molette: Zoom")
    print("  ESPACE: Pause/Reprendre")
    print("  R: Reset modèle")
    print("  S: Sauvegarder .ply")
    print("  ESC: Quitter")
    print("=" * 60)
    print()
    
    # Créer le système de reconstruction
    recon = Reconstruction3D(VIDEO_URL)
    
    # Démarrer la reconstruction
    print("Démarrage de la reconstruction...")
    if not recon.start():
        print("Erreur: Impossible de démarrer")
        return
    
    print("✓ Reconstruction démarrée")
    print("✓ Ouverture de la fenêtre 3D...")
    
    # Créer le visualiseur
    viz = Visualizer3D(1600, 900)
    
    # Boucle principale
    clock = pygame.time.Clock()
    running = True
    
    try:
        while running:
            # Gérer événements
            running = viz.handle_events(recon)
            
            # Obtenir les données de reconstruction
            frame, depth = recon.get_visualization()
            
            # Render
            viz.render(recon, frame, depth)
            
            # Limiter à 30 FPS pour l'affichage
            clock.tick(30)
    
    except KeyboardInterrupt:
        print("\nInterruption clavier")
    
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        recon.stop()
        pygame.quit()
        print("Terminé.")


if __name__ == "__main__":
    main()

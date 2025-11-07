import sys
import pygame
import random
import math
from pygame.locals import *

# Initialisation de Pygame
pygame.init()

# Paramètres de la fenêtre
WIDTH, HEIGHT = 1500, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ciel Étoilé Réaliste")

# Charger les textures pour la Terre et la Lune
earth_texture = pygame.image.load("earth.png")  # Remplacez par le chemin de votre texture
earth_texture = pygame.transform.scale(earth_texture, (100, 100))  # Redimensionner

moon_texture = pygame.image.load("moon.png")  # Remplacez par le chemin de votre texture
moon_texture = pygame.transform.scale(moon_texture, (30, 30))  # Redimensionner

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (10, 10, 30)
YELLOW = (255, 255, 150)

# Classe pour les étoiles
class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)  # Position aléatoire en X
        self.y = random.randint(0, HEIGHT)  # Position aléatoire en Y
        self.size = random.uniform(1, 3)  # Taille aléatoire
        self.brightness = random.randint(100, 255)  # Luminosité initiale
        self.twinkle_speed = random.uniform(0.5, 2)  # Vitesse de scintillement
        self.color = random.choice([WHITE, YELLOW])  # Couleur limitée à blanc et jaune

    def twinkle(self):
        # Faire varier la luminosité pour créer un effet de scintillement
        self.brightness += self.twinkle_speed
        if self.brightness > 255:
            self.brightness = 255
            self.twinkle_speed *= -1
        elif self.brightness < 100:
            self.brightness = 100
            self.twinkle_speed *= -1

    def draw(self):
        # Dessiner l'étoile avec sa luminosité actuelle
        alpha = int(self.brightness)
        color = (*self.color[:3], alpha)  # Ajouter la transparence
        surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (self.size, self.size), self.size)
        screen.blit(surface, (self.x - self.size, self.y - self.size))

# Classe pour les étoiles filantes
class ShootingStar:
    def __init__(self):
        self.reset()
        self.active = False

    def reset(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT // 4)
        self.speed = random.uniform(5, 10)
        self.angle = random.uniform(math.pi / 4, 3 * math.pi / 4)  # Angle aléatoire
        self.length = random.randint(20, 50)
        self.lifetime = random.randint(60, 120)  # Durée de vie plus longue
        self.active = False

    def move(self):
        if self.active:
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
            self.lifetime -= 1
            if self.lifetime <= 0 or self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
                self.reset()

    def draw(self):
        if self.active:
            # Dessiner une traînée lumineuse
            for i in range(self.length):
                alpha = int(255 * (1 - i / self.length))
                pos_x = self.x - math.cos(self.angle) * i
                pos_y = self.y - math.sin(self.angle) * i
                pygame.draw.circle(screen, (255, 255, 255, alpha), (int(pos_x), int(pos_y)), 1)

# Classe pour la Terre et la Lune
class EarthAndMoon:
    def __init__(self):
        self.earth_x = WIDTH - 200  # Déplacée vers la gauche
        self.earth_y = 200  # Déplacée vers le bas
        self.earth_radius = 50
        self.moon_radius = 10
        self.moon_distance = 120
        self.angle = 0
        self.rotation_speed = 0.001  # Vitesse de rotation plus lente
        self.moon_z = 0  # Profondeur de la Lune (simulation 3D)
        self.earth_rotation_angle = 0  # Angle de rotation de la Terre
        self.earth_rotation_speed = 0.0005  # Vitesse de rotation réduite de la Terre

    def update(self):
        self.angle += self.rotation_speed
        self.earth_rotation_angle += self.earth_rotation_speed  # Rotation de la Terre autour de son axe X
        # Simuler la profondeur en 3D
        self.moon_z = math.sin(self.angle) * self.moon_distance

    def draw(self):
        # Dessiner la Terre avec rotation autour de l'axe X
        rotated_earth = pygame.transform.rotate(earth_texture, math.degrees(self.earth_rotation_angle))
        earth_rect = rotated_earth.get_rect(center=(self.earth_x, self.earth_y))
        screen.blit(rotated_earth, earth_rect)

        # Calculer la position de la Lune en 3D
        moon_x = self.earth_x + math.cos(self.angle) * self.moon_distance
        moon_y = self.earth_y + math.sin(self.angle) * self.moon_distance

        # Ajuster la taille et la luminosité de la Lune en fonction de la profondeur
        moon_size = max(5, 30 * (1 - abs(self.moon_z) / self.moon_distance))
        moon_alpha = int(255 * (1 - abs(self.moon_z) / self.moon_distance))

        # Dessiner la Lune avec la texture
        moon_surface = pygame.Surface((moon_size * 2, moon_size * 2), pygame.SRCALPHA)
        moon_surface.blit(pygame.transform.scale(moon_texture, (moon_size * 2, moon_size * 2)), (0, 0))
        moon_surface.set_alpha(moon_alpha)
        screen.blit(moon_surface, (moon_x - moon_size, moon_y - moon_size))

# Créer une liste d'étoiles
stars = [Star() for _ in range(300)]  # 300 étoiles

# Créer une étoile filante
shooting_star = ShootingStar()

# Créer la Terre et la Lune
earth_and_moon = EarthAndMoon()

# Créer deux emplacements pour les galaxies (exemples de position)
galaxy1_position = (100, 100)  # Coordonnée de la première galaxie
galaxy2_position = (1300, 600)  # Coordonnée de la deuxième galaxie

# Boucle principale
running = True
clock = pygame.time.Clock()
shooting_star_timer = 0  # Timer pour l'apparition des étoiles filantes

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Remplir l'écran avec un dégradé de noir à bleu foncé
    for y in range(HEIGHT):
        color = (
            int(DARK_BLUE[0] * (y / HEIGHT)),
            int(DARK_BLUE[1] * (y / HEIGHT)),
            int(DARK_BLUE[2] * (y / HEIGHT))
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    # Animer et afficher les étoiles
    for star in stars:
        star.twinkle()
        star.draw()

    # Gérer l'apparition rare de l'étoile filante
    shooting_star_timer += 1
    if shooting_star_timer > 600:  # Apparition toutes les 10 secondes (60 FPS * 10)
        shooting_star.active = True
        shooting_star_timer = 0

    # Animer et afficher l'étoile filante
    shooting_star.move()
    shooting_star.draw()

    # Animer et afficher la Terre et la Lune
    earth_and_moon.update()
    earth_and_moon.draw()

    # Mettre à jour l'affichage
    pygame.display.flip()

    # Limiter le taux de rafraîchissement à 60 FPS
    clock.tick(60)

# Quitter Pygame
pygame.quit()
sys.exit()
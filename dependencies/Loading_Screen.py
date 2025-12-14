import pygame
import math
import sys
from dependencies.IP_Config import ip_modal_handle_event
from dependencies.Variable import BASE_WIDTH, BASE_HEIGHT


def show_loading_screen(continue_loading, get_current_step,starting_screen):
    width, height = starting_screen.get_size()
    loader_size = 150
    loader_center = loader_size
    base = pygame.Surface((loader_size * 2, loader_size * 2), pygame.SRCALPHA)
    pygame.draw.circle(base, (51, 51, 51), (loader_center, loader_center), loader_size, 1)
    for a in range(0, 360, 18):
        a1 = math.radians(a)
        a2 = math.radians(a + 8)
        x1 = loader_center + (loader_size - 20) * math.cos(a1)
        y1 = loader_center + (loader_size - 20) * math.sin(a1)
        x2 = loader_center + (loader_size - 20) * math.cos(a2)
        y2 = loader_center + (loader_size - 20) * math.sin(a2)
        pygame.draw.line(base, (68, 68, 68), (x1, y1), (x2, y2), 1)
    for a in range(0, 360, 30):
        a1 = math.radians(a)
        a2 = math.radians(a + 12)
        x1 = loader_center + 25 * math.cos(a1)
        y1 = loader_center + 25 * math.sin(a1)
        x2 = loader_center + 25 * math.cos(a2)
        y2 = loader_center + 25 * math.sin(a2)
        pygame.draw.line(base, (68, 68, 68), (x1, y1), (x2, y2), 1)

    glow = pygame.Surface((loader_size * 2, loader_size * 2), pygame.SRCALPHA)
    half = math.radians(55 / 2)
    for layer in range(6, 0, -1):
        r = loader_size * (0.2 + layer * 0.12)
        alpha = int(80 * (layer / 6))
        pts = [
            (loader_center, loader_center),
            (loader_center + r * math.cos(half), loader_center + r * math.sin(half)),
            (loader_center + r * math.cos(-half), loader_center + r * math.sin(-half)),
        ]
        pygame.draw.polygon(glow, (46, 139, 87, alpha), pts)

    shadow = pygame.Surface((loader_size * 2 + 120, loader_size * 2 + 120), pygame.SRCALPHA)
    pygame.draw.circle(shadow, (0, 0, 0, 120), (shadow.get_width() // 2, shadow.get_height() // 2), loader_size)

    loading_font = pygame.font.SysFont('Century Schoolbook', 24)
    step_font = pygame.font.SysFont('Century Schoolbook', 18)
    radar_angle = 0
    clock = pygame.time.Clock()

    while continue_loading():
        for ev in pygame.event.get():
            if 'IP_MODAL' in globals() and ip_modal_handle_event(ev):
                continue
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.VIDEORESIZE:
                starting_screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                width, height = starting_screen.get_size()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()

        starting_screen.fill((0, 0, 0))
        center_x = width // 2
        center_y = height // 2

        sh_x = center_x - shadow.get_width() // 2
        sh_y = center_y - shadow.get_height() // 2
        starting_screen.blit(shadow, (sh_x, sh_y))

        starting_screen.blit(base, (center_x - loader_center, center_y - loader_center))
        radar_angle = (radar_angle + 4) % 360
        rot_glow = pygame.transform.rotate(glow, -radar_angle)
        rg_w, rg_h = rot_glow.get_size()
        starting_screen.blit(rot_glow, (center_x - rg_w // 2, center_y - rg_h // 2))

        rad = math.radians(radar_angle)
        rx = center_x + loader_size * math.cos(rad)
        ry = center_y + loader_size * math.sin(rad)
        pygame.draw.line(starting_screen, (255, 255, 255), (center_x, center_y), (int(rx), int(ry)), 1)

        dots = "." * ((radar_angle // 90) % 4)
        loading_text = loading_font.render(f"Loading{dots}", True, (150, 170, 190))
        starting_screen.blit(loading_text, (center_x - loading_text.get_width() // 2, center_y + loader_size + 20))

        current_step = get_current_step()
        step_text = step_font.render(current_step, True, (46, 139, 87))
        starting_screen.blit(step_text, (center_x - step_text.get_width() // 2, center_y + loader_size + 50))

        pygame.display.flip()
        clock.tick(30)
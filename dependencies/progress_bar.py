import pygame

class ProgressBar:
    def __init__(self, x, y, width, height, speed_min=0, speed_max=255, increment=1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed_min = speed_min
        self.speed_max = speed_max
        self.increment = increment
        self.speed = 0

        self.clock_width = 15  
        self.gray_background = (100, 100, 100)  
        self.black = (0, 0, 0)
        self.red = (139, 0, 0)
        self.font = pygame.font.Font(None, 20)

    def draw(self, screen):
        
        pygame.draw.rect(screen, self.gray_background, (self.x, self.y, self.clock_width + 10, self.height))
        pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.clock_width + 10, self.height), 2)

        clock_height = self.speed / self.speed_max * self.height
        pygame.draw.rect(screen, self.red, (self.x + 5, self.y + self.height - clock_height, self.clock_width, clock_height))

        for i in range(0, self.speed_max + 1, 30):
            if i == 0:
                continue  
            y = self.height - (i / self.speed_max * self.height) + self.y
            pygame.draw.line(screen, (255, 255, 255), (self.x - 5, y), (self.x + self.clock_width + 5, y), 2)
            text = self.font.render(str(i), True, (255, 255, 255))
            screen.blit(text, (self.x + self.clock_width + 10, y - 10))

    def update(self, keys):
        if keys[pygame.K_SPACE] and self.speed < self.speed_max:
            self.speed += self.increment
        if keys[pygame.K_LALT] and self.speed > self.speed_min:
            self.speed -= self.increment

    def set_speed(self, new_speed):
        if self.speed_min <= new_speed <= self.speed_max:
            self.speed = new_speed
        else:
            print("\nError: The value must be between 0 and 255!\n")

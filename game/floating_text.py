"""
This file is for handling floating combat text
"""

import pygame
import random
class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y

        self.text = str(text)
        self.color = color

        self.font = pygame.font.SysFont(None, 20)

        self.vx = random.uniform(-30, 30)
        self.vy = -120

        self.gravity = 300

        self.lifetime = 1.0
        self.timer = 0
        self._alive = True

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.lifetime:
            self._alive = False
            return

        self.vy += self.gravity * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, screen):
        text_surface = self.font.render(self.text, True, self.color)
        rect = text_surface.get_rect(center=(self.x, self.y))
        screen.blit(text_surface, rect)
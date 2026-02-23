"""
This page is to handle projectile animations
"""

import math
import os
import pygame

#Asset cache to prevent multiple loads
_PROJECTILE_ASSET_CACHE = {}

#Initiates the projectile
class Projectile:
    def __init__(self, game, start_x, start_y, target, damage_callback, speed, projectile):
        self.game = game
        self.x = start_x
        self.y = start_y
        self.target = target
        self.damage_callback = damage_callback
        self.speed = speed
        self._alive = True

        match projectile:
            case "Sword":
                asset_path = "towers/Sword.png"
            case "Arrow":
                asset_path = "towers/Arrow.png"
            case "Potion":
                asset_path = "towers/Potion.png"
            case _:
                print("Asset not found")

        if asset_path not in _PROJECTILE_ASSET_CACHE:
            full_path = os.path.join("assets", asset_path)
            image = pygame.image.load(full_path).convert_alpha()
            scaled_image = pygame.transform.smoothscale(image, (image.get_width() * 2, image.get_height() * 2))
            _PROJECTILE_ASSET_CACHE[asset_path] = scaled_image

        self._asset = _PROJECTILE_ASSET_CACHE[asset_path]

    #Update logic as projectile exists
    def update(self, dt):
        if not self._alive or not self.target or not self.target._alive:
            self._alive = False
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.hypot(dx, dy)

        if distance < 5:
            self.damage_callback(self.target)
            self._alive = False
            return

        move_distance = self.speed * dt

        if move_distance >= distance:
            self.x = self.target.x
            self.y = self.target.y
        else:
            self.x += dx / distance * move_distance
            self.y += dy / distance * move_distance

    #Draws the projectile image
    def draw(self, screen):
        rect = self._asset.get_rect(center=(self.x, self.y))
        screen.blit(self._asset, rect)

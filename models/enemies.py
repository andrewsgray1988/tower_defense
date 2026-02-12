"""
This file is for handling all enemy logic
"""

import time
import math
import os
import pygame

from enum import Enum
from gameconfig import (
    ENEMIES,
    SETTINGS
)
from models.towers import Tower

#Asset Storage, to reduce multiple loads for the same asset
_ENEMY_ASSET_CACHE = {}

#Enum setup
class AdventurerState(Enum):
    GOING_TO_GOLD = 1
    CARRYING_GOLD = 2
    RETURNING_TO_EXIT = 3
    DEAD = 4

#Enemy Parent
class Enemy:
    def __init__(self, game, key):
        self.game = game
        self._key = key #Sets the trigger to pull from Constants
        self._wave_modifier = SETTINGS['Wave'] * 1.0 #Multiplicative Modifier to increase strength
        self.set_stats() #Initializes stats on spawn
        self._initialize_visuals()
        self._last_attack = 0 #Initiates flag for attacking and setting cooldown
        self.x = 0
        self.y = 0
        self.path_index = 0
        self._path_direction = 1
        self._moving = False
        self._start_pos = (0, 0)
        self._end_pos = (0, 0)
        self._move_start_time = 0
        self.state = AdventurerState.GOING_TO_GOLD
        self.carrying_gold = False
        self._gold_dropped = False
        self._escaped = False

    """
    Game / Initiate Section
    """
    #Pulls info from ENEMIES
    #ENEMIES stores all info from enemies.json, and is stored in constants to lower json reading
    def set_stats(self):
        enemy_data = ENEMIES[self._key]
        self.name = enemy_data['name']
        self.health = enemy_data['default_health'] * self._wave_modifier
        self.max_health = enemy_data['default_health'] * self._wave_modifier
        self.armor = enemy_data['default_armor'] * self._wave_modifier
        self.damage = enemy_data['default_damage'] * self._wave_modifier
        self.scrap = enemy_data['default_scrap'] * self._wave_modifier
        self.essence = enemy_data['default_essence'] * self._wave_modifier
        self.range = enemy_data['default_range']
        self.armor_pierce = enemy_data['default_armor_pierce']
        self.attack_speed = enemy_data['default_attack_speed']
        self.move_speed = enemy_data['default_move_speed']
        self._alive = True


    def _initialize_visuals(self):
        enemy_data = ENEMIES[self._key]
        asset_path = enemy_data['asset']

        if asset_path not in _ENEMY_ASSET_CACHE:
            full_path = os.path.join("assets", asset_path)
            image = pygame.image.load(full_path).convert_alpha()
            _ENEMY_ASSET_CACHE[asset_path] = image
        base_image = _ENEMY_ASSET_CACHE[asset_path]

        tile_size = self.game.tile_size
        self._asset = pygame.transform.scale(base_image, (tile_size, tile_size))

    #Spawn logic
    def spawn(self):
        self.spawn = self.game.map_data["spawn"]
        spawn_col, spawn_row = self.spawn

        self.x, self.y = self.game.get_tile_center(spawn_col, spawn_row)

        self.path = self.game.map_data["path"][:]
        self.path_index = 0

    #Draw logic
    def draw(self, screen):
        rect = self._asset.get_rect(center=(self.x, self.y))
        screen.blit(self._asset, rect)

        if self.health <= 0:
            return

        BAR_HEIGHT = 6
        BAR_PADDING = 2

        bar_width = rect.width
        bar_x = rect.left
        bar_y = rect.top - BAR_HEIGHT - BAR_PADDING

        # Health ratio
        health_ratio = max(self.health / self.max_health, 0)

        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, BAR_HEIGHT)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)

        # Health fill
        fill_width = int(bar_width * health_ratio)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, BAR_HEIGHT)
            pygame.draw.rect(screen, (200, 0, 0), fill_rect)

        # Border
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, 1)

    """
    Combat Section
    """
    #Death trigger
    def destroy_enemy(self):
        SETTINGS['Essence'] += self.essence
        SETTINGS['Scrap'] += self.scrap
        self._alive = False

    #Escaped trigger
    def get_away(self):
        if self.carrying_gold:
            SETTINGS["Stolen Gold"] += 1
        self._alive = False
        self._escaped = True

    #Damage trigger
    def deal_damage(self, target):
        effective_armor = target.armor * (1 - self.armor_pierce)
        damage_dealt = max(self.damage - effective_armor, 0)
        target.take_damage(damage_dealt)

    #Receive damage trigger
    def take_damage(self, damage_taken):
        self.health -= damage_taken
        if self.health <= 0:
            self.destroy_enemy()

    #Checks distance from target
    def distance_to(self, target):
        return math.hypot(target.x - self.x, target.y - self.y)

    #Decides closest tower target
    def get_closest_tower_in_range(self, towers):
        closest = None
        min_distance = float('inf')

        for tower in towers:
            if not isinstance(tower, Tower):
                continue
            dist = self.distance_to(tower)
            if dist <= self.range and dist < min_distance:
                closest = tower
                min_distance = dist
        return closest

    #Attack trigger
    def attack_closest_tower(self, enemies):
        now = time.time()
        if now - self._last_attack < self.attack_speed:
            return
        target = self.get_closest_tower_in_range(enemies)
        if target:
            self.deal_damage(target)
            self._last_attack = now

    #Takes gold from the pile
    def take_gold(self):
        if self.carrying_gold:
            return

        SETTINGS["Current Gold"] -= 1
        self.carrying_gold = True
        self._path_direction = -1
        self.state = AdventurerState.CARRYING_GOLD

    """
    Movement Logic
    """
    #Reverses movement
    def turn_around(self):
        self._path_direction = -1
        self.state = AdventurerState.RETURNING_TO_EXIT

    #Movement logic
    def move_along_path(self, map_data, dt):
        if not self._alive:
            return

        if self.state == AdventurerState.GOING_TO_GOLD:
            if self.path_index >= len(self.path):
                self.path_end()
                return
            target_col, target_row = self.path[self.path_index]
        else:
            if self.path_index < 0:
                target_col, target_row = self.spawn
            elif self.path_index >= len(self.path):
                target_col, target_row = self.path[-1]
            else:
                target_col, target_row = self.path[self.path_index]

        target_x, target_y = self.game.get_tile_center(target_col, target_row)

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance == 0:
            self.path_index += self._path_direction

            # Reached gold or spawn
            if (self._path_direction == 1 and self.path_index >= len(self.path)) or \
                    (self._path_direction == -1 and self.path_index < 0):
                self.path_end()
            return

        tile_w, tile_h = self.game.get_tile_size()
        speed_per_second = math.hypot(tile_w, tile_h) / self.move_speed
        move_distance = speed_per_second * dt

        if move_distance >= distance:
            self.x = target_x
            self.y = target_y
            self.path_index += self._path_direction

            if (self._path_direction == 1 and self.path_index >= len(self.path)) or \
                    (self._path_direction == -1 and self.path_index < 0):
                self.path_end()
        else:
            self.x += dx / distance * move_distance
            self.y += dy / distance * move_distance

    #Detects which tile the enemy is currently on
    def get_current_tile(self):
        if self._path_direction == 1:
            index = self.path_index - 1
        else:
            index = self.path_index + 1

        if 0 <= index < len(self.path):
            return tuple(self.path[index])

        return None

    #Logic to detect if the tile they're on has gold or not
    def get_drop_tile(self):
        if self.path_index < 0:
            return tuple(self.path[0])
        if self.path_index >= len(self.path):
            return tuple(self.path[-1])
        target_tile = tuple(self.path[self.path_index])
        if list(target_tile) == self.spawn:
            prev_index = self.path_index - self._path_direction
            if 0 <= prev_index < len(self.path):
                return tuple(self.path[prev_index])
        return target_tile

    #Reached the end of the path
    def path_end(self):
        self.path.insert(0, self.spawn)
        if self.state == AdventurerState.GOING_TO_GOLD:
            if SETTINGS["Current Gold"] > 0:
                self.take_gold()
            else:
                self.turn_around()
        elif self.state == AdventurerState.RETURNING_TO_EXIT or self.state == AdventurerState.CARRYING_GOLD:
            self.get_away()

"""
Individual Enemy Types and their unique features
"""
class Fighter(Enemy):
    def __init__(self, game):
        super().__init__(game, "Fighter")
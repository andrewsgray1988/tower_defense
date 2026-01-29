import time
import math
import os
import pygame

from enum import Enum
from constants import (
    ENEMIES,
    SETTINGS
)
from models.towers import Tower

_ENEMY_ASSET_CACHE = {}

class AdventurerState(Enum):
    GOING_TO_GOLD = 1
    RETURNING_TO_EXIT = 2
    DEAD = 3

#Base enemy class
class Enemy:
    def __init__(self, key):
        self._key = key #Sets the trigger to pull from Constants
        self._wave_modifier = SETTINGS['Wave'] * 1.0 #Multiplicative Modifier to increase strength
        self.set_stats() #Initializes stats on spawn
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
        asset_path = enemy_data['asset']

        if asset_path not in _ENEMY_ASSET_CACHE:
            full_path = os.path.join("assets", asset_path)
            _ENEMY_ASSET_CACHE[asset_path] = pygame.image.load(full_path).convert_alpha()

        self._asset = _ENEMY_ASSET_CACHE[asset_path]

    def spawn(self, map_data):
        self.spawn = map_data["spawn"]
        spawn_col, spawn_row = self.spawn

        tile_width = map_data["scaled_width"] / map_data["columns"]
        tile_height = map_data["scaled_height"] / map_data["rows"]

        self._asset = pygame.transform.scale(
            self._asset,
            (int(tile_width), int(tile_height))
        )

        self.x = map_data["draw_x"] + (spawn_col * tile_width) + tile_width / 2
        self.y = map_data["draw_y"] + (spawn_row * tile_height) + tile_height / 2

        self.path = map_data["path"][:]
        self.path_index = 0

    def draw(self, screen):
        rect = self._asset.get_rect(center=(self.x, self.y))
        screen.blit(self._asset, rect)

    #Death trigger, and adds Essence to player's pool
    def destroy_enemy(self):
        SETTINGS['Essence'] += self.essence
        SETTINGS['Scrap'] += self.scrap
        self._alive = False

    def get_away(self):
        if self.carrying_gold:
            SETTINGS["Stolen Gold"] += 1
        self._alive = False

    #Damage trigger, calculating for armor pierce
    def deal_damage(self, target):
        effective_armor = target.armor * (1 - self.armor_pierce)
        damage_dealt = max(self.damage - effective_armor, 0)
        target.take_damage(damage_dealt)

    #Receiving damage trigger
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

    def take_gold(self):
        if self.carrying_gold:
            return

        SETTINGS["Current Gold"] -= 1
        self.carrying_gold = True
        self._path_direction = -1
        self.state = AdventurerState.RETURNING_TO_EXIT

    def turn_around(self):
        self._path_direction = -1
        self.state = AdventurerState.RETURNING_TO_EXIT

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

        tile_width = map_data["scaled_width"] / map_data["columns"]
        tile_height = map_data["scaled_height"] / map_data["rows"]

        target_x = map_data["draw_x"] + target_col * tile_width + tile_width / 2
        target_y = map_data["draw_y"] + target_row * tile_height + tile_height / 2

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

        speed_per_second = math.hypot(tile_width, tile_height) / self.move_speed
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

    def path_end(self):
        self.path.insert(0, self.spawn)
        if self.state == AdventurerState.GOING_TO_GOLD:
            if SETTINGS["Current Gold"] > 0:
                self.take_gold()
            else:
                self.turn_around()
        elif self.state == AdventurerState.RETURNING_TO_EXIT:
            self.get_away()

class Fighter(Enemy):
    def __init__(self):
        super().__init__("Fighter")
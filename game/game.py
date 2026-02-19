"""
This file handles the game play logic for enemy and tower placement
"""

import pygame
import os

from models.enemies import Fighter
from models.towers import Sword, Archer
from functions.mapgeneration import (
    pixel_to_grid,
    grid_to_pixel
)
from gameconfig import (
    SETTINGS,
    TOWERS
)

#Asset Storage, to reduce multiple loads for the same asset
_COIN_ASSET = None

#Game storage class
class Game:
    def __init__(self, map_data):
        self.map_data = map_data
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.gold_drops = {}
        self.stored_gold = SETTINGS['Max Gold']
        self._blocked_tiles = set(tuple(tile) for tile in map_data["path"])
        self._tower_tiles = set()
        self.tile_width = map_data["scaled_width"] / map_data["columns"]
        self.tile_height = map_data["scaled_height"] / map_data["rows"]
        self.tile_size = int(min(self.tile_width, self.tile_height))

        global _COIN_ASSET
        if _COIN_ASSET is None:
            coin_path = os.path.join("assets", "misc", "coin.png")
            _COIN_ASSET = pygame.image.load(coin_path).convert_alpha()
        self.coin_asset = _COIN_ASSET

        tile_width = map_data["scaled_width"] / map_data["columns"]
        tile_height = map_data["scaled_height"] / map_data["rows"]

        coin_size = int(min(tile_width, tile_height) * 0.5)

        self.coin_asset = pygame.transform.scale(
            self.coin_asset,
            (coin_size, coin_size)
        )

    """
    Game Logic
    """

    def update(self, dt):
        #Enemy Logic
        for enemy in self.enemies:
            enemy.move_along_path(self.map_data, dt)
            enemy.update_combat(dt)

            if enemy._alive and not enemy.carrying_gold:
                tile = enemy.get_current_tile()
                if tile and self.has_gold_at(tile):
                    if self.take_gold_from(tile, 1):
                        enemy.path.insert(0, enemy.spawn)
                        enemy.carrying_gold = True
                        enemy._path_direction = -1
                        enemy.state = enemy.state.RETURNING_TO_EXIT

        for enemy in self.enemies:
            if (
                    not enemy._alive
                    and enemy.carrying_gold
                    and not enemy._gold_dropped
                    and not enemy._escaped
            ):
                drop_tile = enemy.get_drop_tile()
                self.drop_gold(drop_tile, 1)
                enemy._gold_dropped = True

        #Tower Logic
        for tower in self.towers:
            if tower._alive:
                tower.update_combat(dt)
            else:
                if tower._current_timer <= 0:
                    tower.revive_tower()
                else:
                    tower._current_timer -= dt

        #Projectile Logic
        for projectile in self.projectiles[:]:
            projectile.update(dt)
            if not projectile._alive:
                self.projectiles.remove(projectile)

        #Cleanup Nonactive
        self.enemies = [e for e in self.enemies if e._alive]
        self.towers = [t for t in self.towers if not t._sold]

    def draw(self, screen):
        #Draw Coins
        tile_width, tile_height = self.get_tile_size()

        for (col, row), count in self.gold_drops.items():
            if count <= 0:
                continue

            x = self.map_data["draw_x"] + col * tile_width + tile_width / 2
            y = self.map_data["draw_y"] + row * tile_height + tile_height / 2

            rect = self.coin_asset.get_rect(center=(x, y))
            screen.blit(self.coin_asset, rect)

        #Draw Enemies
        for tower in self.towers:
            tower.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)
        for projectile in self.projectiles:
            projectile.draw(screen)

    """
    Tile Logic
    """
    def screen_to_tile(self, pos):
        x, y = pos
        return pixel_to_grid(x, y, self.map_data)

    def tile_to_screen(self, col, row):
        return grid_to_pixel(col, row, self.map_data)

    def get_tile_center(self, col, row):
        tile_width = self.map_data["scaled_width"] / self.map_data["columns"]
        tile_height = self.map_data["scaled_height"] / self.map_data["rows"]
        x = self.map_data["draw_x"] + col * tile_width + tile_width / 2
        y = self.map_data["draw_y"] + row * tile_height + tile_height / 2
        return x, y

    def get_tile_size(self):
        return self.tile_width, self.tile_height

    """
    Enemy Logic
    """
    def spawn_enemy(self, enemy_type):
        match enemy_type:
            case "Fighter":
                enemy = Fighter(self)
            case _:
                return

        enemy.spawn()
        self.enemies.append(enemy)

    #Signal to drop gold and store in memory on enemy death
    def drop_gold(self, tile_pos, amount=1):
        if tile_pos not in self.gold_drops:
            self.gold_drops[tile_pos] = 0
        self.gold_drops[tile_pos] += amount

    #Signal for enemies to detect if there is gold at the tile they're on
    def has_gold_at(self, tile_pos):
        return self.gold_drops.get(tile_pos, 0) > 0

    #Signal to remove dropped gold logic
    def take_gold_from(self, tile_pos, amount=1):
        if tile_pos not in self.gold_drops:
            return False
        self.gold_drops[tile_pos] -= amount
        if self.gold_drops[tile_pos] <= 0:
            del self.gold_drops[tile_pos]
        return True

    """
    Tower Logic
    """

    #Make sure that the tiles are buildable and in bounds
    def is_tile_in_bounds(self, col, row):
        return (
            0 <= col < self.map_data["columns"]
            and 0 <= row < self.map_data["rows"]
        )

    def is_tile_buildable(self, col, row):
        return (
            self.is_tile_in_bounds(col, row)
            and (col, row) not in self._blocked_tiles
            and (col, row) not in self._tower_tiles
        )

    def register_tower_tile(self, col, row):
        self._tower_tiles.add((col, row))

    def place_tower(self, tower_key, col, row):
        if not self.is_tile_buildable(col, row):
            return False
        if tower_key not in TOWERS:
            return False

        cost = TOWERS[tower_key]["default_cost"]

        if SETTINGS["Scrap"] < cost:
            return False

        match tower_key:
            case "Sword":
                tower = Sword(self, col, row)
            case "Archer":
                tower = Archer(self, col, row)
            case _:
                return False

        SETTINGS["Scrap"] -= cost

        self.towers.append(tower)
        self.register_tower_tile(col, row)

        return True

    """
    Debug Features
    """
    #Damage or kill the earliest enemy to test damage
    def kill_earliest_enemy(self, amount):
        if not self.enemies:
            return
        enemy = self.enemies[0]
        if amount == "full":
            enemy.take_damage(enemy.health)
        else:
            enemy.take_damage(amount)
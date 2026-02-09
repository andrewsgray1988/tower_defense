"""
This file handles the game play logic for enemy and tower placement
"""

import pygame
import os

from models.enemies import Fighter
from functions.mapgeneration import (
    pixel_to_grid,
    grid_to_pixel
)
from constants import SETTINGS

#Asset Storage, to reduce multiple loads for the same asset
_COIN_ASSET = None

#Game storage class
class Game:
    def __init__(self, map_data):
        self.map_data = map_data
        self.enemies = []
        self.towers = []
        self.gold_drops = {}
        self.stored_gold = SETTINGS['Max Gold']
        self._blocked_tiles = set(tuple(tile) for tile in map_data["path"])
        self._tower_tiles = set()

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
        for enemy in self.enemies:
            enemy.move_along_path(self.map_data, dt)

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

        self.enemies = [e for e in self.enemies if e._alive]

    def draw(self, screen):
        #Draw Coins
        tile_width = self.map_data["scaled_width"] / self.map_data["columns"]
        tile_height = self.map_data["scaled_height"] / self.map_data["rows"]

        for (col, row), count in self.gold_drops.items():
            if count <= 0:
                continue

            x = self.map_data["draw_x"] + col * tile_width + tile_width / 2
            y = self.map_data["draw_y"] + row * tile_height + tile_height / 2

            rect = self.coin_asset.get_rect(center=(x, y))
            screen.blit(self.coin_asset, rect)

        #Draw Enemies
        for enemy in self.enemies:
            enemy.draw(screen)

    def screen_to_tile(self, pos):
        x, y = pos
        return pixel_to_grid(x, y, self.map_data)

    def tile_to_screen(self, col, row):
        return grid_to_pixel(col, row, self.map_data)

    """
    Enemy Logic
    """
    def spawn_enemy(self, enemy_type="Fighter"):
        if enemy_type == "Fighter":
            enemy = Fighter()
        else:
            return

        enemy.spawn(self.map_data)
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

    """
    Debug Features
    """
    def kill_earliest_enemy(self, amount):
        if not self.enemies:
            return
        enemy = self.enemies[0]
        if amount == "full":
            enemy.take_damage(enemy.health)
        else:
            enemy.take_damage(amount)
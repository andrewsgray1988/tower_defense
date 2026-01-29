import pygame
import os

from models.enemies import Fighter
from constants import SETTINGS

_COIN_ASSET = None

class Game:
    def __init__(self, map_data):
        self.map_data = map_data
        self.enemies = []
        self.towers = []
        self.gold_drops = {}
        self.stored_gold = SETTINGS['Max Gold']

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

    #Enemy Features
    def spawn_enemy(self, enemy_type="Fighter"):
        if enemy_type == "Fighter":
            enemy = Fighter()
        else:
            return

        enemy.spawn(self.map_data)
        self.enemies.append(enemy)

    def update(self, dt):
        for enemy in self.enemies:
            enemy.move_along_path(self.map_data, dt)

        for enemy in self.enemies:
            if not enemy._alive and enemy.carrying_gold and not enemy._gold_dropped:
                drop_tile = enemy.get_drop_tile()
                self.drop_gold(drop_tile, 1)
                enemy.gold_dropped = True
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

    #Gold Features
    def drop_gold(self, tile_pos, amount=1):
        if tile_pos not in self.gold_drops:
            self.gold_drops[tile_pos] = 0
        self.gold_drops[tile_pos] += amount

    def has_gold_at(self, tile_pos):
        return self.gold_drops.get(tile_pos, 0) > 0

    def take_gold_from(self, tile_pos, amount=1):
        if tile_pos not in self.gold_drops:
            return False
        self.gold_drops[tile_pos] -= amount
        if self.gold_drops[tile_pos] <= 0:
            del self.gold_drops[tile_pos]
        return True

    #Debug Features
    def kill_earliest_enemy(self):
        if not self.enemies:
            return

        enemy = self.enemies[0]

        enemy.take_damage(enemy.health)
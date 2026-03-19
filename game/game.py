"""
This file handles the game play logic for enemy and tower placement
"""

import pygame
import os
import random

from enum import Enum
from models.enemies import Fighter
from functions.mapgeneration import (
    pixel_to_grid,
    grid_to_pixel
)
from gameconfig import (
    SETTINGS,
    ALL_BUILDABLES,
    ENEMY_LIST,
    TOWER_CHOICES,
    WAVE_TIME_1,
    WAVE_TIME_2,
    INITIAL_TIME,
    BETWEEN_ROUNDS
)
from functions.general import (
    reset_jsons,
    setup_class_map
)

#Asset Storage, to reduce multiple loads for the same asset
_COIN_ASSET = None

#Set up Class Map
CLASS_MAP = setup_class_map(TOWER_CHOICES)

#Sets up Enum states for the Tiles
class TileState(Enum):
    PATH = 1
    BUILDABLE = 2
    TOWER = 3

#Game storage class
class Game:
    def __init__(self, map_data):
        self.map_data = map_data
        self.enemies = []
        self.towers = []
        self.structures = []
        self.projectiles = []
        self.floating_texts = []
        self.gold_drops = {}
        self.stored_gold = SETTINGS['Max Gold']
        self.tile_states = {}
        # Initialize entire grid as BUILDABLE first
        for col in range(map_data["columns"]):
            for row in range(map_data["rows"]):
                self.tile_states[(col, row)] = TileState.BUILDABLE
        # Overwrite path tiles
        for tile in map_data["path"]:
            self.tile_states[tuple(tile)] = TileState.PATH
        self.tile_width = map_data["scaled_width"] / map_data["columns"]
        self.tile_height = map_data["scaled_height"] / map_data["rows"]
        self.tile_size = int(min(self.tile_width, self.tile_height))
        self.wave_count = SETTINGS['Wave Count']
        if self.wave_count == 1 and SETTINGS['Wave Time'] == INITIAL_TIME:
            self._wait_time = INITIAL_TIME
        else:
            self._wait_time = SETTINGS['Wait Time']

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
    #Update checks for the game in progress
    def update(self, dt):
        import gameconfig
        """
        Enemy Logic
        """
        #Enemy Move Logic
        for enemy in self.enemies:
            enemy.update_combat(dt)
            enemy.move_along_path(self.map_data, dt)
            if enemy._is_poisoned:
                enemy.take_damage(enemy._poison_damage)

            #Enemy arrives at end of path
            if enemy._alive and not enemy.carrying_gold:
                tile = enemy.get_current_tile()
                if tile and self.has_gold_at(tile):
                    if self.take_gold_from(tile, 1):
                        enemy.path.insert(0, enemy.spawn)
                        enemy.carrying_gold = True
                        enemy._path_direction = -1
                        enemy.state = enemy.state.RETURNING_TO_EXIT

        #Enemy drops gold when killed
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

        #Cleanup enemies
        self.enemies = [e for e in self.enemies if e._alive]

        """
        Tower Logic
        """
        #Tower Respawn Timer
        for tower in self.towers:
            if tower._alive:
                tower.update_combat(dt)
            else:
                if tower._current_timer <= 0:
                    tower.revive_tower()
                else:
                    tower._current_timer -= dt

        #Cleanup towers
        self.towers = [t for t in self.towers if not t._sold]

        """
        Structure Logic
        """
        #Structure Respawn Timer
        for structure in self.structures:
            if structure._alive:
                structure.update_combat(dt)
            else:
                if structure._current_timer <= 0:
                    structure.revive_structure()
                else:
                    structure._current_timer -= dt

        self.structures = [s for s in self.structures if not s._sold]

        """
        Projectile Logic
        """
        #Update and clean up projectiles
        for projectile in self.projectiles[:]:
            projectile.update(dt)
            if not projectile._alive:
                self.projectiles.remove(projectile)

        """
        Game Logic
        """
        #Wave and Spawn handler
        if self._wait_time <= 0 and self.wave_count > 0:
            spawned_enemy = random.choice(ENEMY_LIST)
            new_time = random.uniform(WAVE_TIME_1, WAVE_TIME_2)
            self._wait_time = new_time
            SETTINGS["Wait Time"] = new_time
            self.spawn_enemy(spawned_enemy)
            self.wave_count -= 1
            SETTINGS["Wave Count"] = self.wave_count
        elif self._wait_time <= 0 and self.wave_count <= 0:
            SETTINGS["Wave"] += 1
            self._wait_time = BETWEEN_ROUNDS
            self.wave_count = 10
            SETTINGS["Wave Count"] = self.wave_count
        elif self._wait_time > 0:
            self._wait_time -= dt
            SETTINGS["Wait Time"] = self._wait_time

        for text in self.floating_texts:
            text.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t._alive]

        #Gameover Trigger
        if SETTINGS["Stolen Gold"] == SETTINGS["Max Gold"]:
            reset_jsons()
            gameconfig.GAME_STATE = "gameover"

    #Draws the appropriate references on screen
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
        for structure in self.structures:
            structure.draw(screen)
        for projectile in self.projectiles:
            projectile.draw(screen)
        for text in self.floating_texts:
            text.draw(screen)

    """
    Tile Logic
    """
    #Checks screen to tile position
    def screen_to_tile(self, pos):
        x, y = pos
        return pixel_to_grid(x, y, self.map_data)

    #Checks tile to screen position
    def tile_to_screen(self, col, row):
        return grid_to_pixel(col, row, self.map_data)

    #Finds the center of the tile
    def get_tile_center(self, col, row):
        tile_width = self.map_data["scaled_width"] / self.map_data["columns"]
        tile_height = self.map_data["scaled_height"] / self.map_data["rows"]
        x = self.map_data["draw_x"] + col * tile_width + tile_width / 2
        y = self.map_data["draw_y"] + row * tile_height + tile_height / 2
        return x, y

    #Finds the size of the tile
    def get_tile_size(self):
        return self.tile_width, self.tile_height

    #Checks the Enum state of the tile
    def get_tile_state(self, col, row):
        return self.tile_states.get((col, row))

    #Sets the Enum state of the tile
    def set_tile_state(self, col, row, state):
        self.tile_states[(col, row)] = state

    """
    Enemy Logic
    """
    #Enemy Spawn cases
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
    Tower and Structure Logic
    """
    #Make sure that the tiles are buildable and in bounds
    def is_tile_in_bounds(self, col, row):
        return (
            0 <= col < self.map_data["columns"]
            and 0 <= row < self.map_data["rows"]
        )

    #Checks to see if the tile is a buildable tile
    def is_tile_buildable(self, col, row):
        if not self.is_tile_in_bounds(col, row):
            return False
        return self.get_tile_state(col, row) == TileState.BUILDABLE

    #Tower placement logic
    def place_tower(self, build_key, col, row, direction=None):
        from gameconfig import TOWERS
        if not self.is_tile_buildable(col, row):
            return False

        if build_key not in ALL_BUILDABLES:
            return False

        if build_key not in CLASS_MAP:
            return False

        build_data = ALL_BUILDABLES[build_key]
        cost = build_data["default_cost"]

        if SETTINGS["Scrap"] < cost:
            return False

        SETTINGS["Scrap"] -= cost

        build_class = CLASS_MAP[build_key]

        if direction is not None:
            obj = build_class(self, col, row, direction)
        else:
            obj = build_class(self, col, row)

        if build_key in TOWERS:
            self.towers.append(obj)
        else:
            self.structures.append(obj)

        self.set_tile_state(col, row, TileState.TOWER)
        return True

    #Checks tower placed at selected tile
    def get_tower_at(self, col, row):
        for t in self.towers:
            if t.col == col and t.row == row:
                return t
        for s in self.structures:
            if s.col == col and s.row == row:
                return s
        return None

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
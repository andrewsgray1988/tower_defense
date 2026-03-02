"""
This file handles the game play logic on the offensive towers
"""

import os
import pygame
import math

from collections import deque
from functions.combat import CombatLogic
from constants import (
    UPGRADE_MODIFIER
)
from models.projectile import Projectile

#Cache images to prevent multiple loads per tower
_TOWER_ASSET_CACHE = {}

#Sets priority list for targeting enemies
priority_order = [
    "CARRYING_GOLD",
    "GOING_TO_GOLD",
    "RETURNING_TO_EXIT"
]

#Tower storage class
class Tower(CombatLogic):
    def __init__(self, game, key, col, row):
        CombatLogic.__init__(self)
        self.game = game
        self._key = key
        self.col = col
        self.row = row
        self.set_stats()
        self._initialize_position_and_asset()
        self._font = pygame.font.SysFont(None, 16)

    """
    Game / Initiate Section
    """
    #Sets initial stats from JSON files
    def set_stats(self):
        from gameconfig import TOWERS, SETTINGS
        tower_data = TOWERS[self._key]
        reuse_queue = deque(sorted(tower_data['reuse_list']))

        #Unique Identifier Number for name
        if not reuse_queue:
            self.num = tower_data['max']
            tower_data['max'] += 1
        else:
            self.num = reuse_queue.popleft()

        tower_data['reuse_list'] = list(reuse_queue)

        #Base Stats
        self.name = f"{self._key} Tower {self.num}"
        self._projectile_asset = tower_data['projectile_asset']
        self.max_health = tower_data['default_health']
        self.health = self.max_health
        if tower_data['default_armor'] >= 100:
            self.armor = 100.0
        else:
            self.armor = tower_data['default_armor']
        self.damage = tower_data['default_damage']
        self.armor_pierce = tower_data['default_armor_pierce']
        self.range = tower_data['default_range'] * 1.2
        self.attack_speed = tower_data['default_attack_speed']
        self._respawn_timer = tower_data['default_respawn_timer']
        self._current_timer = self._respawn_timer
        self._alive = True
        self._sold = False
        self.level = 1

        #Costs
        self.cost = tower_data['default_cost']
        self.sell_amount = self.cost * SETTINGS["Sell Multiplier"]
        self.upgrade_cost = tower_data['default_upgrade_cost']

        #Multipliers
        self._health_multiplier = tower_data['default_health_multiplier']
        self._damage_multiplier = tower_data['default_damage_multiplier']
        self._upgrade_cost_multiplier = tower_data['default_upgrade_cost_multiplier']

    #Records position and visual asset
    def _initialize_position_and_asset(self):
        from gameconfig import TOWERS
        tower_data = TOWERS[self._key]
        asset_path = tower_data['asset']

        if asset_path not in _TOWER_ASSET_CACHE:
            full_path = os.path.join("assets", asset_path)
            image = pygame.image.load(full_path).convert_alpha()
            _TOWER_ASSET_CACHE[asset_path] = image
        base_image = _TOWER_ASSET_CACHE[asset_path]

        tile_size = self.game.tile_size
        self._asset = pygame.transform.scale(base_image, (tile_size, tile_size))

        self.x, self.y = self.game.get_tile_center(self.col, self.row)

    #Draws the tower onto the screen
    def draw(self, screen):
        rect = self._asset.get_rect(center=(self.x, self.y))
        screen.blit(self._asset, rect)

        BAR_HEIGHT = 6
        BAR_PADDING = 2

        bar_width = rect.width
        bar_x = rect.left
        bar_y = rect.top + BAR_PADDING

        #Bar Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, BAR_HEIGHT)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)

        if self.health > 0 and self._alive:
            #Health ratio
            bar_ratio = max(self.health / self.max_health, 0)
            fill_color = (200, 0, 0)

        elif self.health <= 0 and not self._alive:
            #Recharge ratio
            bar_ratio = max(1 - (self._current_timer / self._respawn_timer), 0)
            fill_color = (0, 200, 255)

        fill_width = int(bar_width * bar_ratio)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, BAR_HEIGHT)
            pygame.draw.rect(screen, fill_color, fill_rect)

        #Bar Border
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, 1)

        #Tower Number
        num_surface = self._font.render(str(self.num), True, (255, 255, 255))
        num_rect = num_surface.get_rect()
        num_rect.bottomleft = (rect.left + 4, rect.bottom - 2)
        screen.blit(num_surface, num_rect)

        #Tower Level
        level_surface = self._font.render(str(self.level), True, (255, 255, 0))
        level_rect = level_surface.get_rect()
        level_rect.bottomright = (rect.right - 4, rect.bottom - 2)
        screen.blit(level_surface, level_rect)

    """
    Combat Logic
    """
    #Receiving damage trigger
    def take_damage(self, damage_taken):
        self.health -= damage_taken
        if self.health <= 0:
            self._alive = False

    #Checks for enemies as targets
    def _get_potential_targets(self):
        return self.game.enemies

    #Prioritizes Adventurer states
    def select_targets(self, candidates):
        from models.enemies import AdventurerState
        if not candidates:
            return []

        for state_name in priority_order:
            state_enum = getattr(AdventurerState, state_name)
            filtered = [e for e in candidates if e.state == state_enum]
            if filtered:
                front_most = max(filtered, key=lambda e: (e.path_index * e._path_direction))
                return [front_most]
        return [candidates[0]]

    #Attack trigger
    def attack(self, targets):
        for target in targets:
            projectile = Projectile(self.game, self.x, self.y, target, self._deal_damage, 800, self._projectile_asset)
            self.game.projectiles.append(projectile)

    #Deal damage trigger
    def _deal_damage(self, target):
        effective_armor = max(target.armor - self.armor_pierce, 0)
        reduction = min(effective_armor, 100) / 100
        damage = self.damage * (1 - reduction)
        target.take_damage(damage)

    #Tower revival logic
    def revive_tower(self):
        self.health = self.max_health
        self._current_timer = self._respawn_timer
        self._alive = True

    """
    Maintenance Logic
    """
    #Sell tower for some scrap back
    def sell_tower(self):
        from gameconfig import SETTINGS, UPGRADES
        SETTINGS['Scrap'] += self.cost * (UPGRADES['Sellback Mod'] * 0.01)
        self._sold = True

    #Upgrades the tower's stats
    def upgrade_tower(self):
        from gameconfig import SETTINGS
        health_num = round(max(self.max_health * self._health_multiplier, 1), 2) #Sets up health modifier
        new_cost_amount = round(self.upgrade_cost * UPGRADE_MODIFIER, 2)
        self.cost = round(self.cost + new_cost_amount, 2)
        self.sell_amount = round(self.sell_amount + (new_cost_amount * SETTINGS['Sell Multiplier']), 2)
        self.health += health_num
        self.max_health = round(self.max_health + health_num)
        self.damage = round(self.damage * self._damage_multiplier, 2)
        self.upgrade_cost = round(self.upgrade_cost * self._upgrade_cost_multiplier, 2)
        self.level += 1

"""
Individual Tower Types and their unique features
"""
class Sword(Tower):
    def __init__(self, game, col, row):
        super().__init__(game,"Sword", col, row)

class Archer(Tower):
    def __init__(self, game, col, row):
        super().__init__(game,"Archer", col, row)

class Poison(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Poison", col, row)

    #Poison Damage Override
    def _deal_damage(self, target):
        if not target._is_poisoned:
            target._is_poisoned = True
        target._poison_damage += self.damage

class Spear(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Spear", col, row)

class Sludger(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Sludger", col, row)

    #Splash Override
    def _deal_damage(self, target):
        splash_radius = self.game.tile_size

        for enemy in self.game.enemies:
            dx = enemy.x - target.x
            dy = enemy.y - target.y
            distance = math.hypot(dx, dy)

            if distance <= splash_radius:
                if not enemy._is_poisoned:
                    enemy._is_poisoned = True
                enemy._poison_damage += self.damage

    #Attack override for splash
    def attack(self, targets):
        for target in targets:
            projectile = Projectile(self.game, self.x, self.y, target, self._deal_damage, 800, self._projectile_asset, 1)
            self.game.projectiles.append(projectile)

class Cleaver(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Cleaver", col, row)

    # Hits everything in range
    def select_targets(self, candidates):
        if not candidates:
            return []
        return candidates

class Grenadier(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Grenadier", col, row)

    def _deal_damage(self, target):
        splash_radius = self.game.tile_size

        for enemy in self.game.enemies:
            dx = enemy.x - target.x
            dy = enemy.y - target.y
            distance = math.hypot(dx, dy)

            if distance <= splash_radius:
                effective_armor = max(enemy.armor - self.armor_pierce, 0)
                reduction = min(effective_armor, 100) / 100
                damage = self.damage * (1 - reduction)
                enemy.take_damage(damage)

    def attack(self, targets):
        for target in targets:
            projectile = Projectile(self.game, self.x, self.y, target, self._deal_damage, 800, self._projectile_asset, 1)
            self.game.projectiles.append(projectile)

class Heavy(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Heavy", col, row)

class Sniper(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Sniper", col, row)

class Dagger(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Dagger", col, row)

class Crossbow(Tower):
    def __init__(self, game, col, row):
        super().__init__(game, "Crossbow", col, row)
"""
This file handles the game play logic on the non-offensive towers
"""

import os
import pygame
import math

from collections import deque
from functions.combat import CombatLogic
from gameconfig import (
    STRUCTURES,
    SETTINGS,
    UPGRADES
)
from constants import (
    UPGRADE_MODIFIER
)
from models.projectile import Projectile

#Cache images to prevent multiple loads per structure
_STRUCTURE_ASSET_CACHE = {}

#Structure storage class
class Structure(CombatLogic):
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
        structure_data = STRUCTURES[self._key]
        reuse_queue = deque(sorted(structure_data['reuse_list']))

        #Unique Identifier Number for name
        if not reuse_queue:
            self.num = structure_data['max']
            structure_data['max'] += 1
        else:
            self.num = reuse_queue.popleft()

        structure_data['reuse_list'] = list(reuse_queue)

        #Base Stats
        self.name = f"{self._key} Structure {self.num}"
        self._projectile_asset = structure_data['projectile_asset']
        self.max_health = structure_data['default_health']
        self.health = self.max_health
        self.power = structure_data['default_power']
        self.range = structure_data['default_range']
        self.attack_speed = structure_data['default_attack_speed']
        self._respawn_timer = structure_data['default_respawn_timer']
        self._current_timer = self._respawn_timer
        self._alive = True
        self._sold = False
        self.level = 1
        self._targets = structure_data['targets']

        #Costs
        self.cost = structure_data['default_cost']
        self.sell_amount = self.cost * SETTINGS["Sell Multiplier"]
        self.upgrade_cost = structure_data['default_upgrade_cost']

        #Multipliers
        self._health_multiplier = structure_data['default_health_multiplier']
        self._power_multiplier = structure_data['default_power_multiplier']
        self._upgrade_cost_multiplier = structure_data['default_upgrade_cost_multiplier']

    #Records position and visual asset
    def _initialize_position_and_asset(self):
        structure_data = STRUCTURES[self._key]
        asset_path = structure_data['asset']

        if asset_path not in _STRUCTURE_ASSET_CACHE:
            full_path = os.path.join("assets", asset_path)
            image = pygame.image.load(full_path).convert_alpha()
            _STRUCTURE_ASSET_CACHE[asset_path] = image
        base_image = _STRUCTURE_ASSET_CACHE[asset_path]

        tile_size = self.game.tile_size
        self._asset = pygame.transform.scale(base_image, (tile_size, tile_size))

        self.x, self.y = self.game.get_tile_center(self.col, self.row)

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

        #Structure Number
        num_surface = self._font.render(str(self.num), True, (255, 255, 255))
        num_rect = num_surface.get_rect()
        num_rect.bottomleft = (rect.left +4, rect.bottom -2)
        screen.blit(num_surface, num_rect)

        #Structure Level
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

    #Checks for either Friendly or Enemies as targets
    def _get_potential_targets(self):
        if self._targets == "Friendly":
            return self.game.towers + self.game.structures
        elif self._targets == "Enemies":
            return self.game.enemies
        else:
            return []

    #Selects targets for effects
    def select_targets(self, candidates):
        if not candidates:
            return []
        closest = min(candidates, key=lambda t: math.hypot(self.x - t.x, self.y - t.y))
        return [closest]

    #Action trigger
    def attack(self, targets):
        for target in targets:
            projectile = Projectile(self.game, self.x, self.y, target, self._affect_target, 800, self._projectile_asset)
            self.game.projectiles.append(projectile)

    #Default affect target - Needs to update per subclass
    def _affect_target(self, target):
        return None, None

    #Structure revival logic
    def revive_structure(self):
        self.health = self.max_health
        self._current_timer = self._respawn_timer
        self._alive = True

    """
    Maintenance Logic
    """
    #Sell structure for some scrap back
    def sell_structure(self):
        SETTINGS['Scrap'] += self.cost * (UPGRADES['Sellback Mod'] * 0.01)
        self._sold = True

    def upgrade_structure(self):
        health_num = round(max(self.max_health * self._health_multiplier, 1), 2)
        new_cost_amount = round(self.upgrade_cost * UPGRADE_MODIFIER, 2)
        self.cost = round(self.cost + new_cost_amount, 2)
        self.sell_amount = round(self.sell_amount + (new_cost_amount * SETTINGS['Sell Multiplier']), 2)
        self.health += health_num
        self.max_health = round(self.max_health + health_num)
        self.power = round(self.power * self._power_multiplier, 2)
        self.upgrade_cost = round(self.upgrade_cost * self._upgrade_cost_multiplier, 2)
        self.level += 1

"""
Individual Structure Types and their unique features
"""

class Healer(Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Healer", col, row)

    #Overrides and updates combat per 'attack'
    def update_combat(self, dt):
        if self._attack_timer > 0:
            self._attack_timer -= dt
        self._current_targets = self._acquire_targets()
        if self._current_targets and self._attack_timer <= 0:
            self.attack(self._current_targets)
            self._attack_timer = self.attack_speed
        self._current_targets = []

    #Select and prioritize Most injured > Self
    def select_targets(self, candidates):
        if not candidates:
            return []
        others = [t for t in candidates if t is not self]
        damaged_others = [t for t in others if t.health < t.max_health]
        if damaged_others:
            lowest = min(damaged_others, key=lambda t: t.health / t.max_health)
            return [lowest]
        if self.health < self.max_health:
            return [self]
        return []

    #Heals the target
    def _affect_target(self, target):
        if (self.power + target.health) >= target.max_health:
            heal_amount = target.max_health - target.health
            target.health = target.max_health
        else:
            heal_amount = self.power
            target.health += self.power
        return heal_amount, "heal"


class Producer(Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Producer", col, row)
        self._attack_timer = self.attack_speed

    #Override and generate resources passively
    def update_combat(self, dt):
        if self._attack_timer > 0:
            self._attack_timer -= dt
        else:
            self._attack_timer = self.attack_speed
            self.attack(None)

    #Override and generate scrap
    def attack(self, targets):
        SETTINGS["Scrap"] += self.power

class Drainer(Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Drainer", col, row)
        self._attack_timer = self.attack_speed

    #Override and generate resources over time
    def update_combat(self, dt):
        if self._attack_timer > 0:
            self._attack_timer -= dt
        else:
            self._attack_timer = self.attack_speed
            self.attack(None)

    #Override and generate Essence
    def attack(self, targets):
        SETTINGS["Essence"] += self.power

class Distractor(Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Distractor", col, row)
        self._has_aura = True
        self._aura_targets = "Enemy"
        self._aura_name = "Slow"

    def attack(self, targets):
        return

class Motivator(Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Motivator", col, row)
        self._has_aura = True
        self._aura_targets = "Tower"
        self._aura_name = "Up Damage"

    def attack(self, targets):
        return

class Quicker(Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Quicker", col, row)
        self._has_aura = True
        self._aura_targets = "Tower"
        self._aura_name = "Speed"

class Armor(Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Armor", col, row)
        self._has_aura = True
        self._aura_targets = "Enemy"
        self._aura_name = "Down Damage"

class Defender (Structure):
    def __init__(self, game, col, row):
        super().__init__(game, "Defender", col, row)

    def attack(self, targets):
        return
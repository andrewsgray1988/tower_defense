"""
This file handles the game play logic on the offensive towers
"""

import os
import pygame

from collections import deque
from functions.combat import CombatLogic
from gameconfig import (
    TOWERS,
    SETTINGS,
    UPGRADES
)
from constants import (
    MIN_ATTACK_SPEED,
    UPGRADE_MODIFIER
)
from models.projectile import Projectile

_TOWER_ASSET_CACHE = {}

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
    def set_stats(self):
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
        self.health = tower_data['default_health']
        self.max_health = tower_data['default_health']
        if tower_data['default_armor'] >= 100:
            self.armor = 100.0
        else:
            self.armor = tower_data['default_armor']
        self.damage = tower_data['default_damage']
        self.armor_pierce = tower_data['default_armor_pierce']
        self.range = tower_data['default_range']
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
        self._armor_multiplier = tower_data['default_armor_multiplier']
        self._damage_multiplier = tower_data['default_damage_multiplier']
        self._attack_speed_multiplier = tower_data['default_attack_speed_multiplier']
        self._upgrade_cost_multiplier = tower_data['default_upgrade_cost_multiplier']

    def _initialize_position_and_asset(self):
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

        # Tower Number
        num_surface = self._font.render(str(self.num), True, (255, 255, 255))
        num_rect = num_surface.get_rect()
        num_rect.bottomleft = (rect.left + 4, rect.bottom - 2)
        screen.blit(num_surface, num_rect)

        # Tower Level
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

    def _get_potential_targets(self):
        return self.game.enemies

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

    def attack(self, targets):
        for target in targets:
            projectile = Projectile(
                game=self.game,
                start_x=self.x,
                start_y=self.y,
                target=target,
                damage_callback=self._deal_damage,
                speed=800,
                range=self.range
            )
            self.game.projectiles.append(projectile)

    def _deal_damage(self, target):
        effective_armor = max(target.armor - self.armor_pierce, 0)
        reduction = min(effective_armor, 100) / 100
        damage = self.damage * (1 - reduction)
        target.take_damage(damage)

    def revive_tower(self):
        self.health = self.max_health
        self._current_timer = self._respawn_timer
        self._alive = True

    """
    Maintenance Logic
    """
    #Sell tower for some gold back
    def sell_tower(self):
        SETTINGS['Gold'] += self.cost * (UPGRADES['Sellback Mod'] * 0.01)
        self._sold = True

    #Upgrades the tower's stats
    def upgrade_tower(self):
        health_num = max(self.max_health * self._health_multiplier, 1) #Sets up health modifier
        new_cost_amount = self.upgrade_cost * UPGRADE_MODIFIER
        self.cost += new_cost_amount #Updates the cost based off upgrade cost, to calculate total cost
        self.sell_amount += new_cost_amount * SETTINGS["Sell Multiplier"]
        self.health += health_num #Only heals the amount gained rather than heal to full
        self.max_health += health_num
        self.armor *= self._armor_multiplier
        self.damage *= self._damage_multiplier
        self.attack_speed = max(self.attack_speed * self._attack_speed_multiplier, MIN_ATTACK_SPEED) #Caps attack speed
        self.upgrade_cost *= self._upgrade_cost_multiplier
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
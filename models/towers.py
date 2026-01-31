"""
This file handles the game play logic on the offensive towers
"""

import time
import math

from collections import deque
from constants import (
    TOWERS,
    SETTINGS,
    UPGRADES,
    MIN_ATTACK_SPEED
)

#Tower storage class
class Tower:
    def __init__(self, key, x, y):
        self._key = key
        self.set_stats()
        self._last_attack = 0
        self.x = x
        self.y = y

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

        #Base Stats
        self.name = f"{self._key} Tower {self.num}"
        self.health = tower_data['default_health']
        self.max_health = tower_data['default_health']
        self.armor = tower_data['default_armor']
        self.damage = tower_data['default_damage']
        self.armor_pierce = tower_data['default_armor_pierce'] * 0.01
        self.range = tower_data['default_range']
        self.attack_speed = tower_data['default_attack_speed']

        #Costs
        self.cost = tower_data['default_cost']
        self.upgrade_cost = tower_data['default_upgrade_cost']

        #Multipliers
        self._health_multiplier = tower_data['default_health_multiplier']
        self._armor_multiplier = tower_data['default_armor_multiplier']
        self._damage_multiplier = tower_data['default_damage_multiplier']
        self._attack_speed_multiplier = tower_data['default_attack_speed_multiplier']
        self._upgrade_cost_multiplier = tower_data['default_upgrade_cost_multiplier']

        tower_data['reuse_list'] = list(reuse_queue)

    """
    Combat Logic
    """
    #Death trigger
    def destroy_tower(self):
        tower_data = TOWERS[self._key]
        tower_data['reuse_list'].append(self.num)
        pass

    #Damage trigger, calculating for armor pierce
    def deal_damage(self, target):
        effective_armor = target.armor * (1 - self.armor_pierce)
        damage_dealt = max(self.damage - effective_armor, 0)
        target.take_damage(damage_dealt)

    #Receiving damage trigger
    def take_damage(self, damage_taken):
        self.health -= damage_taken
        if self.health <= 0:
            self.destroy_tower()

    # Checks distance to target
    def distance_to(self, target):
        return math.hypot(target.x - self.x, target.y - self.y)

    # Checks closest target to attack
    def get_closest_enemy_in_range(self, enemies):
        closest = None
        min_distance = float('inf')

        for enemy in enemies:
            if not hasattr(enemy, "x") or not hasattr(enemy, "take_damage"):
                continue

            dist = self.distance_to(enemy)
            if dist <= self.range and dist < min_distance:
                closest = enemy
                min_distance = dist

        return closest

    # Attack trigger
    def attack_closest_enemy(self, enemies):
        now = time.time()
        if now - self._last_attack < self.attack_speed:
            return
        target = self.get_closest_enemy_in_range(enemies)
        if target:
            self.deal_damage(target)
            self._last_attack = now

    """
    Maintenance Logic
    """
    #Sell tower for some gold back
    def sell_tower(self):
        SETTINGS['Gold'] += self.cost * (UPGRADES['Sellback Mod'] * 0.01)

    #Upgrades the tower's stats
    def upgrade_tower(self):
        health_num = max(self.max_health * self._health_multiplier, 1) #Sets up health modifier
        self.cost += self.upgrade_cost #Updates the cost based off upgrade cost, to calculate total cost
        self.health += health_num #Only heals the amount gained rather than heal to full
        self.max_health += health_num
        self.armor *= self._armor_multiplier
        self.damage *= self._damage_multiplier
        self.attack_speed = max(self.attack_speed * self._attack_speed_multiplier, MIN_ATTACK_SPEED) #Caps attack speed
        self.upgrade_cost *= self._upgrade_cost_multiplier


"""
Individual Tower Types and their unique features
"""
class Sword(Tower):
    def __init__(self, x, y):
        super().__init__("Sword", x, y)

class Archer(Tower):
    def __init__(self, x, y):
        super().__init__("archer", x, y)
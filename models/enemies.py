import time
import math

from constants import (
    ENEMIES,
    SETTINGS
)
from models.towers import Tower

#Base enemy class
class Enemy:
    def __init__(self, key, x, y):
        self._key = key #Sets the trigger to pull from Constants
        self._wave_modifier = SETTINGS['Wave'] * 1.0 #Multiplicative Modifier to increase strength
        self.set_stats() #Initializes stats on spawn
        self._last_attack = 0 #Initiates flag for attacking and setting cooldown
        self.x = x
        self.y = y

    def set_stats(self):
        enemy_data = ENEMIES[self._key]
        self.name = enemy_data['name']
        self.health = enemy_data['default_health'] * self._wave_modifier
        self.max_health = enemy_data['default_health'] * self._wave_modifier
        self.armor = enemy_data['default_armor'] * self._wave_modifier
        self.damage = enemy_data['default_damage'] * self._wave_modifier
        self.essence = enemy_data['default_essence'] * self._wave_modifier
        self.range = enemy_data['default_range']
        self.armor_pierce = enemy_data['default_armor_pierce']
        self.attack_speed = enemy_data['default_attack_speed']
        self.move_speed = enemy_data['default_move_speed']

    #Death trigger, and adds Essence to player's pool
    def destroy_enemy(self):
        SETTINGS['Essence'] += self.essence
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
    def attack_closest_enemy(self, enemies):
        now = time.time()
        if now - self._last_attack < self.attack_speed:
            return
        target = self.get_closest_tower_in_range(enemies)
        if target:
            self.deal_damage(target)
            self._last_attack = now
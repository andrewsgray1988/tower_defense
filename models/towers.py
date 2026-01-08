

from collections import deque
from functions.general import (
    load_json,
    save_json
)

MIN_ATTACK_SPEED = 0.1

class Tower:
    def __init__(self, key):
        self._key = key
        self.set_stats()

    def set_stats(self):
        data = load_json('towers.json')
        tower_data = data[self._key]

        reuse_queue = deque(sorted(tower_data['reuse_list']))

        if not reuse_queue:
            self.num = tower_data['max']
            tower_data['max'] += 1
        else:
            self.num = reuse_queue.popleft()

        self.name = f"{self._key} Tower {self.num}"
        self.health = tower_data['default_health']
        self.max_health = tower_data['default_health']
        self.armor = tower_data['default_armor']
        self.damage = tower_data['default_damage']
        self.attack_speed = tower_data['default_attack_speed']

        self.cost = tower_data['default_cost']
        self.upgrade_cost = tower_data['default_upgrade_cost']

        self._health_multiplier = tower_data['default_health_multiplier']
        self._armor_multiplier = tower_data['default_armor_multiplier']
        self._damage_multiplier = tower_data['default_damage_multiplier']
        self._attack_speed_multiplier = tower_data['default_attack_speed_multiplier']
        self._upgrade_cost_multiplier = tower_data['default_upgrade_cost_multiplier']

        tower_data['reuse_list'] = list(reuse_queue)
        save_json("towers.json", data)

    def destroy_tower(self):
        data = load_json('towers.json')
        tower_data = data[self._key]

        tower_data['reuse_list'].append(self.num)
        save_json("towers.json", data)
        pass

    def deal_damage(self, target):
        target.take_damage(self.damage)

    def take_damage(self, target):
        damage_taken = max(target.damage - self.armor, 0)
        self.health -= damage_taken
        if self.health <= 0:
            self.destroy_tower()

    def upgrade_tower(self):
        health_num = self.max_health * self._health_multiplier
        if health_num < 1:
            health_num = 1
        self.health += health_num
        self.max_health += health_num
        self.armor *= self._armor_multiplier
        self.damage *= self._damage_multiplier
        self.attack_speed *= max(self.attack_speed * self._attack_speed_multiplier, MIN_ATTACK_SPEED)
        self.upgrade_cost *= self._upgrade_cost_multiplier
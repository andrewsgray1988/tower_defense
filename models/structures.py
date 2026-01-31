"""
This file handles the game play logic on the non-offensive towers
"""

from collections import deque
from constants import (
    STRUCTURES,
    SETTINGS,
    UPGRADES
)

#Structure storage class
class Structure:
    def __init__(self, key, x, y):
        self._key = key #Sets the trigger to pull from Constants
        self.set_stats() #Initializes stats on spawn
        self.x = x
        self.y = y

    """
    Game / Initiate Section
    """
    def set_stats(self):
        structure_data = STRUCTURES[self._key]
        reuse_queue = deque(sorted(structure_data['reuse_list']))

        # Unique Identifier Number for name
        if not reuse_queue:
            self.num = structure_data['max']
            structure_data['max'] += 1
        else:
            self.num = reuse_queue.popleft()

        #Base Stats
        self.name = f"{self._key} Tower {self.num}"
        self.health = structure_data['default_health']
        self.max_health = structure_data['default_health']
        self.armor = structure_data['default_armor']

        #Costs
        self.cost = structure_data['default_cost']
        self.upgrade_cost = structure_data['default_upgrade_cost']

        #Multipliers
        self._health_multiplier = structure_data['default_health_multiplier']
        self._armor_multiplier = structure_data['default_armor_multiplier']
        self._upgrade_cost_multiplier = structure_data['default_upgrade_cost_multiplier']

        structure_data['reuse_list'] = list(reuse_queue)

    """
    Combat Logic
    """
    #Death trigger
    def destroy_structure(self):
        structure_data = STRUCTURES[self._key]
        structure_data['reuse_list'].append(self.num)
        pass

    #Receiving damage trigger
    def take_damage(self, damage_taken):
        self.health -= damage_taken
        if self.health <= 0:
            self.destroy_structure()

    """
    Maintenance Section
    """
    #Sell tower for some gold back
    def sell_structure(self):
        SETTINGS['Gold'] += self.cost * (UPGRADES['Sellback Mod'] * 0.01)

    #Upgrades the tower's stats
    def upgrade_structure(self):
        health_num = max(self.max_health * self._health_multiplier, 1) #Sets up health modifier
        self.cost += self.upgrade_cost #Updates the cost based off upgrade cost, to calculate total cost
        self.health += health_num #Only heals the amount gained rather than heal to full
        self.max_health += health_num
        self.armor *= self._armor_multiplier
        self.upgrade_cost *= self._upgrade_cost_multiplier

"""
Individual Structure Types and their unique features
"""
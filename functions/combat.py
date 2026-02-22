"""
This page is to form and unify combat mechanics to re-use for various classes
"""

import math

#Sets the combat logic class to implement into other classes
class CombatLogic:
    def __init__(self):
        self._attack_timer = 0
        self._current_targets = []

    #Combat checks
    def update_combat(self, dt):
        #Reduces attack timer if they've already attacked
        if self._attack_timer > 0:
            self._attack_timer -= dt

        self._validate_current_targets()

        #Validates or acquires target(s)
        if not self._current_targets:
            self._current_targets = self._acquire_targets()

        #Attacks if successful
        if self._current_targets and self._attack_timer <= 0:
            self.attack(self._current_targets)
            self._attack_timer = self.attack_speed

    """
    Targeting Logic
    """
    #Sets up target list
    def _acquire_targets(self):
        candidates = self._get_potential_targets()
        in_range = self._get_targets_in_range(candidates)

        if not in_range:
            return []

        selected = self.select_targets(in_range)

        if not isinstance(selected, list):
            raise TypeError("select_targets() must return a list")

        return selected

    #Checks for possible targets in range
    def _get_targets_in_range(self, candidates):
        valid = []
        for target in candidates:
            if not self._is_valid_target(target):
                continue
            if self._is_in_range(target):
                valid.append(target)
        return valid

    #Takes out targets that can't be used
    def _validate_current_targets(self):
        cleaned = []
        for target in self._current_targets:
            if self._is_valid_target(target) and self._is_in_range(target):
                cleaned.append(target)
        self._current_targets = cleaned

    #Checks if the target is valid
    def _is_valid_target(self, target):
        if not target:
            return False
        if hasattr(target, "_alive") and not target._alive:
            return False
        if hasattr(target, "health") and target.health <= 0:
            return False
        return True

    """
    Range Logic
    """
    #Checks to see if target is within range
    def _is_in_range(self, target):
        tile_size = self.game.tile_size

        dx = self.x - target.x
        dy = self.y - target.y

        distance_pixels = math.hypot(dx, dy)
        range_pixels = self.range * tile_size

        return distance_pixels <= range_pixels
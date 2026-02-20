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
        #Processes cooldown timer
        if self._attack_timer > 0:
            self._attack_timer -= dt

        self._validate_current_targets()

        #Validates or acquires target(s)
        if not self._current_targets:
            self._current_targets = self._acquire_targets()

        #Attempt attack
        if self._current_targets and self._attack_timer <= 0:
            self.attack(self._current_targets)
            self._attack_timer = self.attack_speed

    """
    Targeting Logic
    """
    def _acquire_targets(self):
        candidates = self._get_potential_targets()
        in_range = self._get_targets_in_range(candidates)

        if not in_range:
            return []

        selected = self.select_targets(in_range)

        if not isinstance(selected, list):
            raise TypeError("select_targets() must return a list")

        return selected

    def _get_targets_in_range(self, candidates):
        valid = []
        for target in candidates:
            if not self._is_valid_target(target):
                continue
            if self._is_in_range(target):
                valid.append(target)
        return valid

    def _validate_current_targets(self):
        cleaned = []
        for target in self._current_targets:
            if self._is_valid_target(target) and self._is_in_range(target):
                cleaned.append(target)
        self._current_targets = cleaned

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
    def _is_in_range(self, target):
        tile_size = self.game.tile_size

        dx = self.x - target.x
        dy = self.y - target.y

        distance_pixels = math.hypot(dx, dy)
        range_pixels = self.range * tile_size

        return distance_pixels <= range_pixels
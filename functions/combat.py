"""
This page is to form and unify combat mechanics to re-use for various classes
"""

import math

#Sets the combat logic class to implement into other classes
class CombatLogic:
    def __init__(self):
        self._attack_timer = 0
        self._current_target = None

    #Combat checks
    def update_combat(self, dt):
        #Processes cooldown timer
        if self._attack_timer > 0:
            self._attack_timer -= dt

        #Validates or acquires target(s)
        if not self._is_valid_target(self._current_target):
            self._current_target = self._acquire_targets()

        #Attempt attack
        if self._current_target and self._attack_timer <= 0:
            self.perform_attack(self._current_target)
            self._attack_timer = self.attack_speed

    """
    Targeting Logic
    """
    def _acquire_targets(self):
        candidates = self._get_potential_targets()
        in_range = self._get_targets_in_range(candidates)

        if not in_range:
            return None

        return self.select_targets(in_range)

    def _get_targets_in_range(self, candidates):
        valid = []
        for target in candidates:
            if not self._is_valid_target(target):
                continue
            if self._is_in_range(target):
                valid.append(target)
        return valid

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

    def perform_attack(self, targets):
        if not isinstance(targets, list):
            targets = [targets]
        for t in targets:
            self._deal_damage(t)

    def _deal_damage(self, target):
        effective_armor = max(target.armor - self.armor_pierce, 0)

        damage_after_armor = self.damage * (1 - effective_armor)
        target.health -= damage_after_armor

        if target.health <= 0:
            target.health = 0
            if hasattr(target, "_alive"):
                target._alive = False

    """
    Hooks WIP
    """
    def _get_potential_targets(self):
        pass

    def select_targets(self, candidates):
        pass
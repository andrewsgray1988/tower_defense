"""
This page is to form and unify combat mechanics to re-use for various classes
"""

import math

#Sets the combat logic class to implement into other classes
class CombatLogic:
    def __init__(self):
        self._attack_timer = 0
        self._current_targets = []
        self._has_aura = False
        self._aura_targets = None
        self._aura_name = None

    #Combat checks
    def update_combat(self, dt):
        self._apply_aura_effects()
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

    """
    Aura Logic
    """
    #Applies aura affects from Structures with auras
    def _apply_aura_effects(self):
        if hasattr(self, "_base_move_speed"):
            self.move_speed = self._base_move_speed
        if hasattr(self, "_base_attack_speed"):
            self.attack_speed = self._base_attack_speed
        if hasattr(self, "_base_damage"):
            self.damage = self._base_damage

        for structure in self.game.structures:
            if not getattr(structure, "_has_aura", False):
                continue

            if not structure._alive:
                continue

            if not structure._is_in_range(self):
                continue
            structure.apply_aura(self)

    # Aura logic
    def apply_aura(self, unit):
        if self._aura_targets == "Tower":
            from models.towers import Tower
            if not isinstance(unit, Tower):
                return

        elif self._aura_targets == "Enemy":
            from models.enemies import Enemy
            if not isinstance(unit, Enemy):
                return

        match self._aura_name:
            case "Slow":
                unit.move_speed *= self.power
                unit.attack_speed *= self.power
            case "Up Damage":
                unit.damage *= self.power
            case "Speed":
                unit.attack_speed /= self.power
            case "Down Damage":
                unit.damage /= self.power
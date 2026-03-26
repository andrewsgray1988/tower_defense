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
        self._auras = []
        self._aura_immune = False

    #Combat checks
    def update_combat(self, dt):
        self._apply_aura_effects(dt)
        #Reduces attack timer if they've already attacked
        if self._attack_timer > 0:
            self._attack_timer -= dt

        if hasattr(self, "targetable") and not self.targetable:
            self.target_timer -= dt
            if self.target_timer <= 0:
                self.targetable = True

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
        if hasattr(target, "targetable") and not target.targetable:
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
    def _apply_aura_effects(self, dt):
        if hasattr(self, "_base_move_speed"):
            self.move_speed = self._base_move_speed
        if hasattr(self, "_base_attack_speed"):
            self.attack_speed = self._base_attack_speed
        if hasattr(self, "_base_damage"):
            self.power = self._base_damage

        aura_sources = self.game.structures + self.game.enemies

        for source in aura_sources:
            if not getattr(source, "_has_aura", False):
                continue

            if not getattr(source, "_alive", True):
                continue

            if source is self:
                continue

            if not source._is_in_range(self):
                continue
            source.apply_aura(self, dt)

    # Aura logic
    def apply_aura(self, unit, dt):
        if getattr(unit, "_aura_immune", False):
            return

        for aura in self._auras:
            target = aura["target"]
            name = aura["name"]

            if target == "Tower":
                from models.towers import Tower
                from models.structures import Structure
                if not isinstance(unit, (Tower, Structure)):
                    continue

            elif target == "Enemy":
                from models.enemies import Enemy
                if not isinstance(unit, Enemy):
                    continue

            match name:
                case "Slow":
                    unit.move_speed *= self.power
                    unit.attack_speed *= self.power
                case "Up Damage":
                    unit.power *= self.power
                case "Speed":
                    unit.attack_speed /= self.power
                case "Down Damage":
                    unit.power /= self.power
                case "Heal":
                    heal_per_second = self.power * 1.10
                    heal_amount = heal_per_second * dt
                    if unit.health + heal_amount >= unit.max_health:
                        unit.health = unit.max_health
                    else:
                        unit.health += heal_amount
                case "Fear":
                    unit.attack_speed /= self._aura_power
                case "Damage Reduction":
                    unit.power /= self._aura_power
                case _:
                    return
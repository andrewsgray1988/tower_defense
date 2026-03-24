"""
This file is for handling all enemy logic
"""

import math
import os
import pygame

from enum import Enum
from gameconfig import (
    ENEMIES,
    SETTINGS,
    WAVE_MODIFIER,
    UPGRADES
)
from constants import (
    NINJA_RESPAWN
)
from functions.combat import CombatLogic
from models.projectile import Projectile
from functions.general import random_enemy_buff

#Asset Storage, to reduce multiple loads for the same asset
_ENEMY_ASSET_CACHE = {}

#Enum setup
class AdventurerState(Enum):
    GOING_TO_GOLD = 1
    CARRYING_GOLD = 2
    RETURNING_TO_EXIT = 3
    DEAD = 4

#Enemy Parent
class Enemy(CombatLogic):
    def __init__(self, game, key):
        CombatLogic.__init__(self)
        self.game = game
        self._key = key
        if SETTINGS['Wave'] == 1:
            self._wave_modifier = 1
        else:
            self._wave_modifier = SETTINGS['Wave'] * WAVE_MODIFIER
        self._initialize_visuals()
        self.x = 0
        self.y = 0
        self.path_index = 0
        self._path_direction = 1
        self._moving = False
        self._start_pos = (0, 0)
        self._end_pos = (0, 0)
        self._move_start_time = 0
        self.state = AdventurerState.GOING_TO_GOLD
        self.targetable = True
        self.carrying_gold = False
        self._gold_dropped = False
        self._escaped = False
        self._is_poisoned = False
        self._poison_damage = 0
        self._ninja = False
        self._ranger = False
        self._cleric = False
        self._warlock = False
        self._wizard = False

    """
    Game / Initiate Section
    """
    #Pulls info from ENEMIES
    def set_stats(self):
        enemy_data = ENEMIES[self._key]
        self.name = enemy_data['name']
        self._projectile_asset = enemy_data['projectile_asset']
        self.max_health = enemy_data['default_health'] * self._wave_modifier
        self.health = self.max_health
        self.armor = enemy_data['default_armor']
        self._base_damage = enemy_data['default_damage'] * self._wave_modifier
        self.power = self._base_damage
        self.scrap = UPGRADES['Default Scrap'] * self._wave_modifier
        self.essence = UPGRADES['Default Essence'] * self._wave_modifier
        self.range = enemy_data['default_range'] * 1.2
        self._base_attack_speed = enemy_data['default_attack_speed']
        self.attack_speed = self._base_attack_speed
        self._base_move_speed = enemy_data['default_move_speed']
        self.move_speed = self._base_move_speed
        self._alive = True

        if self._cleric:
            self._has_aura = True
            self._auras.append({"name": "Heal", "target": "Enemy"})

        if self._warlock:
            self._has_aura = True
            self._auras.append({"name": "Fear", "target": "Tower"})
            self._aura_power = enemy_data['default_aura_power']

        if self._wizard:
            self._has_aura = True
            self._auras.append({"name": "Damage Reduction", "target": "Tower"})
            self._aura_power = enemy_data['default_aura_power']

    #Visual representation of the enemy
    def _initialize_visuals(self):
        enemy_data = ENEMIES[self._key]
        asset_path = enemy_data['asset']

        if asset_path not in _ENEMY_ASSET_CACHE:
            full_path = os.path.join("assets", asset_path)
            image = pygame.image.load(full_path).convert_alpha()
            _ENEMY_ASSET_CACHE[asset_path] = image
        base_image = _ENEMY_ASSET_CACHE[asset_path]

        tile_size = self.game.tile_size
        self._asset = pygame.transform.scale(base_image, (tile_size, tile_size))

    #Spawn logic
    def spawn(self):
        self.spawn = self.game.map_data["spawn"]
        spawn_col, spawn_row = self.spawn

        self.x, self.y = self.game.get_tile_center(spawn_col, spawn_row)

        self.path = self.game.map_data["path"][:]
        self.path_index = 0

    #Draw logic
    def draw(self, screen):
        rect = self._asset.get_rect(center=(self.x, self.y))
        if not self.targetable:
            self._asset.set_alpha(100)
        else:
            self._asset.set_alpha(255)
        screen.blit(self._asset, rect)

        if self.health <= 0:
            return

        BAR_HEIGHT = 6
        BAR_PADDING = 2

        bar_width = rect.width
        bar_x = rect.left
        bar_y = rect.top - BAR_HEIGHT - BAR_PADDING

        #Health ratio
        health_ratio = max(self.health / self.max_health, 0)

        #Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, BAR_HEIGHT)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)

        #Health fill
        fill_width = int(bar_width * health_ratio)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, BAR_HEIGHT)
            pygame.draw.rect(screen, (200, 0, 0), fill_rect)

        #Border
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, 1)

    """
    Combat Section
    """
    #Death trigger
    def destroy_enemy(self):
        SETTINGS['Essence'] += self.essence
        SETTINGS['Scrap'] += self.scrap

        if self.carrying_gold and not self._gold_dropped:
            drop_tile = self.get_drop_tile()
            self.game.drop_gold(drop_tile, 1)
            self._gold_dropped = True

        self._alive = False

    #Escaped trigger
    def get_away(self):
        if self.carrying_gold:
            SETTINGS["Stolen Gold"] += 1
        self._alive = False
        self._escaped = True

    #Damage trigger
    def _deal_damage(self, target):
        target.take_damage(self.power)
        return self.power, "damage"

    #Receive damage trigger
    def take_damage(self, damage_taken):
        self.health -= damage_taken
        if self.health <= 0:
            self.destroy_enemy()
            return
        if self._ninja:
            self.targetable = False
            self.target_timer = self.reset_timer

    #Takes gold from the pile
    def take_gold(self):
        if self.carrying_gold:
            return

        SETTINGS["Current Gold"] -= 1
        self.carrying_gold = True
        self._path_direction = -1
        self.state = AdventurerState.CARRYING_GOLD

    #Assigns targetables
    def _get_potential_targets(self):
        return self.game.towers + self.game.structures

    #Selects the target to attack
    def select_targets(self, candidates):
        if not candidates:
            return []
        # Prioritize Defenders
        defenders = [c for c in candidates if hasattr(c, "_key") and c._key == "Defender"]
        if defenders:
            target = min(defenders, key=lambda t: math.hypot(self.x - t.x, self.y - t.y))
            return [target]

        if not self._ranger:
            # Prioritize Towers if no Defenders
            from models.towers import Tower
            towers = [c for c in candidates if isinstance(c, Tower)]
            if towers:
                target = min(towers, key=lambda t: math.hypot(self.x - t.x, self.y - t.y))
                return [target]

            # Prioritize Structures if no Defenders or Towers
            from models.structures import Structure
            structures = [c for c in candidates if isinstance(c, Structure)]
            if structures:
                target = min(structures, key=lambda t: math.hypot(self.x - t.x, self.y - t.y))
                return [target]
        else:
            #Prioritize Structures if no Defenders and a Ranger
            from models.structures import Structure
            structures = [c for c in candidates if isinstance(c, Structure)]
            if structures:
                target = min(structures, key=lambda t: math.hypot(self.x - t.x, self.y - t.y))
                return [target]

            #Prioritize Towers if no Defenders or Structures, and a Ranger
            from models.towers import Tower
            towers = [c for c in candidates if isinstance(c, Tower)]
            if towers:
                target = min(towers, key=lambda t: math.hypot(self.x - t.x, self.y - t.y))
                return [target]
        return []

    #Attack function
    def attack(self, targets):
        for target in targets:
            projectile = Projectile(self.game, self.x, self.y, target, self._deal_damage, 800, self._projectile_asset)
            self.game.projectiles.append(projectile)

    """
    Movement Logic
    """
    #Reverses movement
    def turn_around(self):
        self._path_direction = -1
        self.state = AdventurerState.RETURNING_TO_EXIT

    #Movement logic
    def move_along_path(self, map_data, dt):
        if not self._alive:
            return

        if self.state == AdventurerState.GOING_TO_GOLD:
            if self.path_index >= len(self.path):
                self.path_end()
                return
            target_col, target_row = self.path[self.path_index]
        else:
            if self.path_index < 0:
                target_col, target_row = self.spawn
            elif self.path_index >= len(self.path):
                target_col, target_row = self.path[-1]
            else:
                target_col, target_row = self.path[self.path_index]

        target_x, target_y = self.game.get_tile_center(target_col, target_row)

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance == 0:
            self.path_index += self._path_direction

            # Reached gold or spawn
            if (self._path_direction == 1 and self.path_index >= len(self.path)) or \
                    (self._path_direction == -1 and self.path_index < 0):
                self.path_end()
            return

        tile_w, tile_h = self.game.get_tile_size()
        speed_per_second = math.hypot(tile_w, tile_h) / self.move_speed
        move_distance = speed_per_second * dt

        if move_distance >= distance:
            self.x = target_x
            self.y = target_y
            self.path_index += self._path_direction

            if (self._path_direction == 1 and self.path_index >= len(self.path)) or \
                    (self._path_direction == -1 and self.path_index < 0):
                self.path_end()
        else:
            self.x += dx / distance * move_distance
            self.y += dy / distance * move_distance

    #Detects which tile the enemy is currently on
    def get_current_tile(self):
        if self._path_direction == 1:
            index = self.path_index - 1
        else:
            index = self.path_index + 1

        if 0 <= index < len(self.path):
            return tuple(self.path[index])

        return None

    #Logic to detect if the tile they're on has gold or not
    def get_drop_tile(self):
        if self.path_index < 0:
            return tuple(self.path[0])
        if self.path_index >= len(self.path):
            return tuple(self.path[-1])
        target_tile = tuple(self.path[self.path_index])
        if list(target_tile) == self.spawn:
            prev_index = self.path_index - self._path_direction
            if 0 <= prev_index < len(self.path):
                return tuple(self.path[prev_index])
        return target_tile

    #Reached the end of the path
    def path_end(self):
        self.path.insert(0, self.spawn)
        if self.state == AdventurerState.GOING_TO_GOLD:
            if SETTINGS["Current Gold"] > 0:
                self.take_gold()
            else:
                self.turn_around()
        elif self.state == AdventurerState.RETURNING_TO_EXIT or self.state == AdventurerState.CARRYING_GOLD:
            self.get_away()

"""
Individual Enemy Types and their unique features
"""
class Barbarian(Enemy):
    def __init__(self, game):
        super().__init__(game, "Barbarian")
        self.set_stats()

class Bard(Enemy):
    def __init__(self, game):
        super().__init__(game, "Bard")
        first_class, second_class = random_enemy_buff()
        classes = {first_class, second_class}
        if "Cleric" in classes:
            self._cleric = True
        if "Ninja" in classes:
            from gameconfig import UPGRADES
            self.targetable = False
            self.target_timer = 0
            self.reset_timer = NINJA_RESPAWN
            self._ninja = True
        if "Paladin" in classes:
            self._aura_immune = True
        if "Ranger" in classes:
            self._ranger = True
        if "Warlock" in classes:
            self._warlock = True
        if "Wizard" in classes:
            self._wizard = True

        self.set_stats()

        if "Barbarian" in classes:
            self.max_health = self.max_health * 1.4
            self.health = self.max_health
        if "Fighter" in classes:
            self.armor = ENEMIES["Fighter"]["default_armor"]
            self._base_damage = self._base_damage * 1.1
            self.power = self._base_damage
            self.max_health = self.max_health * 1.1
            self.health = self.max_health
        if "Knight" in classes:
            self.armor = ENEMIES["Knight"]["default_armor"]
        if "Monk" in classes:
            self._base_move_speed = self._base_move_speed * 0.7
            self.move_speed = self._base_move_speed
        if "Ranger" in classes:
            self.range = 3 * 1.2
        if "Rogue" in classes:
            self._base_damage = self._base_damage * 0.80
            self.power = self._base_damage
            self._base_attack_speed = self._base_attack_speed * 0.7
            self.attack_speed = self._base_attack_speed
        if "Sorcerer" in classes:
            self._base_damage = self._base_damage * 1.3
            self.power = self._base_damage

class Cleric(Enemy):
    def __init__(self, game):
        super().__init__(game, "Cleric")
        self._cleric = True
        self.set_stats()

class Druid(Enemy):
    def __init__(self, game):
        super().__init__(game, "Druid")

        druid_choice, _ = random_enemy_buff()
        match druid_choice:
            case "Cleric":
                self._cleric = True
            case "Ninja":
                from gameconfig import UPGRADES
                self.targetable = False
                self.target_timer = 0
                self.reset_timer = NINJA_RESPAWN
                self._ninja = True
            case "Paladin":
                self._aura_immune = True
            case "Ranger":
                self._ranger = True
            case "Warlock":
                self._warlock = True
            case "Wizard":
                self._wizard = True

        self.set_stats()

        match druid_choice:
            case "Barbarian":
                self.max_health = self.max_health * 1.7
                self.health = self.max_health
            case "Fighter":
                self.armor = ENEMIES["Fighter"]["default_armor"]
                self._base_damage = self._base_damage * 1.2
                self.power = self._base_damage
                self.max_health = self.max_health * 1.2
                self.health = self.max_health
            case "Knight":
                self.armor = ENEMIES["Knight"]["default_armor"]
            case "Monk":
                self._base_move_speed = ENEMIES["Monk"]['default_move_speed']
                self.move_speed = self._base_move_speed
            case "Ranger":
                self.range = 3 * 1.2
            case "Rogue":
                self._base_damage = self._base_damage * 0.70
                self.power = self._base_damage
                self._base_attack_speed = ENEMIES["Rogue"]['default_attack_speed']
                self.attack_speed = self._base_attack_speed
            case "Sorcerer":
                self._base_damage = self._base_damage * 1.5
                self.power = self._base_damage

class Fighter(Enemy):
    def __init__(self, game):
        super().__init__(game, "Fighter")
        self.set_stats()

class Knight(Enemy):
    def __init__(self, game):
        super().__init__(game, "Knight")
        self.set_stats()

class Monk(Enemy):
    def __init__(self, game):
        super().__init__(game, "Monk")
        self.set_stats()

class Ninja(Enemy):
    def __init__(self, game):
        super().__init__(game, "Ninja")
        from gameconfig import UPGRADES
        self.targetable = False
        self.target_timer = 0
        self.reset_timer = NINJA_RESPAWN
        self._ninja = True
        self.set_stats()

class Paladin(Enemy):
    def __init__(self, game):
        super().__init__(game, "Paladin")
        self._aura_immune = True
        self.set_stats()

class Ranger(Enemy):
    def __init__(self, game):
        super().__init__(game, "Ranger")
        self._ranger = True
        self.set_stats()

class Rogue(Enemy):
    def __init__(self, game):
        super().__init__(game, "Rogue")
        self.set_stats()

class Sorcerer(Enemy):
    def __init__(self, game):
        super().__init__(game, "Sorcerer")
        self.set_stats()

class Warlock(Enemy):
    def __init__(self, game):
        super().__init__(game, "Warlock")
        self._warlock = True
        self.set_stats()

class Wizard(Enemy):
    def __init__(self, game):
        super().__init__(game, "Wizard")
        self._wizard = True
        self.set_stats()
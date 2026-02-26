# Tower Defense WIP

A Python-based tower defense game built using **Pygame**, designed to showcase stateful enemies, dynamic towers, and interactive debugging features. This project is a work-in-progress and demonstrates advanced game logic, object-oriented design, and modular JSON configuration.

---

# Current Release - 0.10

## 📌 Development Roadmap

You can view the full development roadmap here:

👉 [View the Roadmap](ROADMAP.md)

## Features

### Gameplay Mechanics
- **Stateful Enemies**:
  - Move along defined paths to collect gold.
  - Can reverse direction if gold is unavailable.
  - Drop gold when killed, which can be picked up by other enemies.
  - Carry health, damage, armor, and attack stats scaled by wave modifiers.

- **Towers & Structures**:
  - Offensive Towers: Deal damage, track closest enemies, and handle upgrades.
  - Non-offensive Structures: Provide strategic gameplay elements, can be sold/upgraded.
  - Dynamic stats and reuse queues for unique identifiers per tower/structure.

- **Game Loop & Asset Management**:
  - `Game` class manages enemy and tower updates.
  - Gold drops are tracked per-tile and rendered dynamically.
  - Asset caching reduces repeated image loads for enemies and coins.

- **Map Handling**:
  - Grid-based coordinate system for precise placement.
  - Functions to convert between pixel and grid coordinates.
  - Scales maps dynamically based on screen resolution.
  - Optional debug grid overlay.

- **Debugging Tools**:
  - Debug panel using **Tkinter** for spawning enemies, adjusting waves, scrap, and gold.
  - Functions to kill or damage enemies for testing.
  - Print mouse-clicked grid positions to the console.

---

## Project Architecture

```
├── main.py                 # Game loop entry point
├── constants.py            # Settings-wide constants
├── gameconfig.py           # Game-wide constants and JSON loading
├── game/
│   ├── game.py             # Core game logic (enemies, gold, updates)
│   └── ui.py               # Non-offensive structure logic
├── models/
│   ├── enemies.py          # Enemy logic and movement
│   ├── towers.py           # Offensive tower logic
│   ├── projectiles.py      # Handles projectile asset spawning and despawning logic
│   └── structures.py       # Non-offensive structure logic
├── functions/
│   ├── combat.py           # Stores the combat logic for use for towers and enemies
│   ├── general.py          # JSON handling, periodic saving
│   ├── mapgeneration.py    # Map loading and grid functions
│   └── debugfunctions.py   # Debug panel & utilities
├── information/
│   ├── towers.json
│   ├── enemies.json
│   ├── structures.json
│   ├── maps.json
│   ├── upgrades.json
│   ├── game_settings.json
│   └── system_settings.json
└── assets/                 # Images for enemies, maps, and misc items
```

---

## Key JSON Configurations

- `towers.json` — Defines base stats, costs, multipliers, and unique tower types.
- `structures.json` — Stores non-offensive structures, health, armor, and upgrade logic.
- `enemies.json` — Enemy stats, assets, and default behavior.
- `maps.json` — Path tiles, spawn points, map dimensions, and grid layout.
- `upgrades.json` — Global upgrade modifiers (sellback, multipliers).
- `game_settings.json` — Tracks current wave, gold, scrap, and essence.
- `system_settings.json` — Screen resolution and system-level settings.

---

## Gameplay Flow (ASCII Diagram)

```
Spawn Point
    ▼
Enemy moves along Path
    ├─► Reaches Gold Tile?
    │     ├─ Yes: Picks up Gold, reverses path
    │     └─ No: Continues forward
    ▼
Enemy encounters Towers
    ├─► Tower in range?
    │     ├─ Yes: Tower attacks Enemy, Enemy attacks the Tower, and then continues
    │     └─ No: Enemy continues
    ▼
Enemy reaches Spawn/Exit
    ├─► Carrying Gold?
    │     ├─ Yes: Adds to Stolen Gold count
    │     └─ No: Ends movement
    ▼
Enemy dies (health ≤ 0)
    └─► Drops Gold (if carrying) for other Enemies
```

- Gold drops remain on the map and can be picked up by other enemies.
- Towers automatically detect and attack the closest enemy in range, prioritizing gold carrying enemies.
- The wave system dynamically increases enemy stats and strength.

---

## Code Example
Enemy Movement Logic
```python
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
```

Combat Logic
```python
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

        return distance_pixels <= range_pixels```
---

## Technologies & Libraries

- **Python 3.11**
- **Pygame** — Game rendering and main loop.
- **Tkinter** — Debug panel UI.
- **JSON** — External configuration for enemies, towers, and maps.

---
## Notes

- This project is currently **WIP**;
```
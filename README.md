# Tower Defense WIP

A Python-based tower defense game built using **Pygame**, designed to showcase stateful enemies, dynamic towers, and interactive debugging features. This project is a work-in-progress and demonstrates advanced game logic, object-oriented design, and modular JSON configuration.

---

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
├── constants.py            # Game-wide constants and JSON loading
├── game/
│   └── game.py             # Core game logic (enemies, gold, updates)
├── models/
│   ├── enemies.py          # Enemy logic and movement
│   ├── towers.py           # Offensive tower logic
│   └── structures.py       # Non-offensive structure logic
├── functions/
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

        tile_width = map_data["scaled_width"] / map_data["columns"]
        tile_height = map_data["scaled_height"] / map_data["rows"]

        target_x = map_data["draw_x"] + target_col * tile_width + tile_width / 2
        target_y = map_data["draw_y"] + target_row * tile_height + tile_height / 2

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

        speed_per_second = math.hypot(tile_width, tile_height) / self.move_speed
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
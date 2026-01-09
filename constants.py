import atexit

from functions.general import (
    load_json,
    save_json,
    periodic_save
)

TOWERS = load_json("towers.json")
SETTINGS = load_json("settings.json")
ENEMIES = load_json("enemies.json")
UPGRADES = load_json("upgrades.json")
STRUCTURES = load_json("structures.json")

def save_all_jsons():
    save_json("towers.json", TOWERS)
    save_json("settings.json", SETTINGS)
    save_json("enemies.json", ENEMIES)
    save_json("upgrades.json", UPGRADES)
    save_json("structures.json", STRUCTURES)

periodic_save(save_all_jsons)

atexit.register(save_all_jsons)
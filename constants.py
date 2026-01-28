

from functions.general import (
    load_json,
    save_json,
    periodic_save
)

#Constant System Settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
TILE_SIZE = 16

#Constant Game Settings
GAME_STATE = "menu"
CURRENT_GOLD = 0
RUNNING = True

#Persistent Settings, to prevent multiple loadings throughout the game
TOWERS = load_json("towers.json")
SETTINGS = load_json("settings.json")
ENEMIES = load_json("enemies.json")
UPGRADES = load_json("upgrades.json")
STRUCTURES = load_json("structures.json")
MAPS = load_json("maps.json")

#Periodically saves the JSONs to keep data
def save_all_jsons():
    save_json("towers.json", TOWERS)
    save_json("settings.json", SETTINGS)
    save_json("enemies.json", ENEMIES)
    save_json("upgrades.json", UPGRADES)
    save_json("structures.json", STRUCTURES)
    save_json("maps.json", MAPS)
periodic_save(save_all_jsons)

#Debug Code
DEBUG_MODE = True
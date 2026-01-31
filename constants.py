"""
This page is for storing constants throughout other functions, for easy
"""

from functions.general import (
    load_json,
    save_json,
    periodic_save
)

#Initializes json loads to lessen json loading throughout the game
TOWERS = load_json("towers.json")
SETTINGS = load_json("game_settings.json")
SYSTEM = load_json("system_settings.json")
ENEMIES = load_json("enemies.json")
UPGRADES = load_json("upgrades.json")
STRUCTURES = load_json("structures.json")
MAPS = load_json("maps.json")

#Constant System Settings
SCREEN_WIDTH = SYSTEM["Screen Width"]
SCREEN_HEIGHT = SYSTEM["Screen Height"]
TILE_SIZE = 16

#Constant Game Settings
GAME_STATE = "menu"
CURRENT_GOLD = 0
RUNNING = True
MIN_ATTACK_SPEED = 0.1

#Periodically saves the JSONs to keep data
def save_all_jsons():
    save_json("towers.json", TOWERS)
    save_json("game_settings.json", SETTINGS)
    save_json("enemies.json", ENEMIES)
    save_json("upgrades.json", UPGRADES)
    save_json("structures.json", STRUCTURES)
    save_json("maps.json", MAPS)
periodic_save(save_all_jsons)

#Initializes if Debug should be active or not
DEBUG_MODE = True
"""
This page is for storing game specific constants that are being updated throughout the gameplay
"""

from functions.general import (
    load_json,
    save_json,
    periodic_save
)

#Initializes json loads to lessen json loading throughout the game
TOWERS = load_json("towers.json")
SETTINGS = load_json("game_settings.json")
ENEMIES = load_json("enemies.json")
UPGRADES = load_json("upgrades.json")
STRUCTURES = load_json("structures.json")
MAPS = load_json("maps.json")
SYSTEM = load_json("system_settings.json")
ALL_BUILDABLES = {**TOWERS, **STRUCTURES}

#Mutable Game Settings
GAME_STATE = "menu"
RUNNING = False
TOWER_CHOICES = ["Sword", "Healer", "Distractor", "Motivator", "Defender"]
WAVE_MODIFIER = SETTINGS["Wave Modifier"]
WAVE_TIME_1 = SETTINGS["Wave Time 1"]
WAVE_TIME_2 = SETTINGS["Wave Time 2"]
INITIAL_TIME = SETTINGS["Initial Time"]
BETWEEN_ROUNDS = SETTINGS["Between Rounds"]
ENEMY_LIST = ["Bard"]

#Periodically saves the JSONs to keep data
def save_all_jsons():
    save_json("towers.json", TOWERS)
    save_json("game_settings.json", SETTINGS)
    save_json("enemies.json", ENEMIES)
    save_json("upgrades.json", UPGRADES)
    save_json("structures.json", STRUCTURES)
    save_json("maps.json", MAPS)
periodic_save(save_all_jsons)
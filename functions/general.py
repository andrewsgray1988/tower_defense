"""
This file is general functions - functions that may be used universally for general purpose
"""

import os
import json
import threading
import pygame
import sys

from models.towers import Sludger

#Sets up the JSON load path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
JSON_DIR = "information"

#Loads from the JSON file
def load_json(file):
    with open(os.path.join(BASE_DIR, JSON_DIR, file)) as json_file:
        return json.load(json_file)

#Saves to the JSON file
def save_json(file, data):
    full_path = os.path.join(BASE_DIR, JSON_DIR, file)
    with open(full_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

#Sets up periodic saving for the JSON files
def periodic_save(save_func, interval=30):
    save_func() #Save Function
    t = threading.Timer(interval, periodic_save, args=(save_func,))
    t.daemon = True
    t.start()

#Closes the whole program
def close_program():
    import constants
    reset_jsons()

    constants.RUNNING = False
    pygame.quit()
    sys.exit()

#Resets all settings and JSONS to default
def reset_jsons():
    import gameconfig
    from gameconfig import (
        SETTINGS,
        STRUCTURES,
        save_all_jsons
    )
    default_towers = load_json("default_towers.json")
    SETTINGS['Wave'] = 1
    SETTINGS['Scrap'] = 100
    SETTINGS['Essence'] = 0.0
    SETTINGS['Current Gold'] = SETTINGS['Max Gold']
    SETTINGS['Stolen Gold'] = 0
    SETTINGS['Wait Time'] = 10
    SETTINGS['Wave Count'] = 10
    gameconfig.TOWERS = default_towers
    save_all_jsons()

def setup_class_map(choice_list):
    from models.towers import (
        Sword,
        Archer,
        Poison,
        Spear,
        Sludger,
        Cleaver,
        Grenadier,
        Heavy,
        Sniper,
        Dagger,
        Crossbow,
        Quickshot,
        Piercer,
        Precision,
        Mage,
        Flamethrower,
        Expensive,
        Slacker
    )
    from models.structures import (
        Healer
    )
    class_map = {}
    for choice in choice_list:
        match choice:
            case "Sword":
                class_map["Sword"] = Sword
            case "Archer":
                class_map["Archer"] = Archer
            case "Healer":
                class_map["Healer"] = Healer
            case "Poison":
                class_map["Poison"] = Poison
            case "Spear":
                class_map["Spear"] = Spear
            case "Sludger":
                class_map["Sludger"] = Sludger
            case "Cleaver":
                class_map["Cleaver"] = Cleaver
            case "Grenadier":
                class_map["Grenadier"] = Grenadier
            case "Heavy":
                class_map["Heavy"] = Heavy
            case "Sniper":
                class_map["Sniper"] = Sniper
            case "Dagger":
                class_map["Dagger"] = Dagger
            case "Crossbow":
                class_map["Crossbow"] = Crossbow
            case "Quickshot":
                class_map["Quickshot"] = Quickshot
            case "Piercer":
                class_map["Piercer"] = Piercer
            case "Precision":
                class_map["Precision"] = Precision
            case "Mage":
                class_map["Mage"] = Mage
            case "Flamethrower":
                class_map["Flamethrower"] = Flamethrower
            case "Expensive":
                class_map["Expensive"] = Expensive
            case "Slacker":
                class_map["Slacker"] = Slacker
            case _:
                return
    return class_map
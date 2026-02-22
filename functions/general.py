"""
This file is general functions - functions that may be used universally for general purpose
"""

import os
import json
import threading
import pygame
import sys

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
    from gameconfig import (
        SETTINGS,
        TOWERS,
        save_all_jsons
    )
    SETTINGS['Wave'] = 1
    SETTINGS['Scrap'] = 200
    SETTINGS['Essence'] = 0.0
    SETTINGS['Current Gold'] = SETTINGS['Max Gold']
    SETTINGS['Stolen Gold'] = 0
    SETTINGS["Wait Time"] = 20
    SETTINGS["Wave Count"] = 10
    for tower_key, tower_data in TOWERS.items():
        tower_data["max"] = 1
    save_all_jsons()
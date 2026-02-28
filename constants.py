"""
This page is for storing constants throughout other functions, for easy use - typically settings that don't change much
through gameplay
"""
import os
import json

BASE_DIR = os.path.dirname(__file__)
JSON_DIR = "information"

def load_json(file):
    with open(os.path.join(BASE_DIR, JSON_DIR, file)) as json_file:
        return json.load(json_file)

SYSTEM = load_json("system_settings.json")

#Constant System Settings
SCREEN_WIDTH = SYSTEM["Screen Width"]
SCREEN_HEIGHT = SYSTEM["Screen Height"]
TILE_SIZE = 16
BUILD_MENU_BUTTON_WIDTH = 140
BUILD_MENU_BUTTON_HEIGHT = 40

#Constant Game Settings
MIN_ATTACK_SPEED = 0.1
UPGRADE_MODIFIER = 1.1

#Initializes if Debug should be active or not
DEBUG_MODE = True
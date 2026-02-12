"""
This page is for storing constants throughout other functions, for easy use - typically settings that don't change much
through gameplay
"""
import gameconfig

#Constant System Settings
SCREEN_WIDTH = gameconfig.SYSTEM["Screen Width"]
SCREEN_HEIGHT = gameconfig.SYSTEM["Screen Height"]
TILE_SIZE = 16
BUILD_MENU_BUTTON_WIDTH = 140
BUILD_MENU_BUTTON_HEIGHT = 40

#Constant Game Settings
MIN_ATTACK_SPEED = 0.1
UPGRADE_MODIFIER = 1.1

#Initializes if Debug should be active or not
DEBUG_MODE = True
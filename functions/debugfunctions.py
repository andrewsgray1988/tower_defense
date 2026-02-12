"""
This file is for handling the debug window and functions involved with that.
"""

import tkinter as tk
import constants
import gameconfig
import pygame
import sys

from functions.mapgeneration import pixel_to_grid
from gameconfig import (
    SETTINGS,
    save_all_jsons
)

#Prints the tile clicked to output console
def print_grid_position(mouse_x, mouse_y, map_data):
    col, row = pixel_to_grid(mouse_x, mouse_y, map_data)
    if col is None or row is None:
        return
    grid_x = col + 1
    grid_y = row + 1
    print(f"Grid: ({grid_x}, {grid_y})")

#tkinter popup window to handle debug functions within the game
def debug_window(spawn_enemy_callback, kill_enemy_callback):
    #Resets game back to default state
    def close_all():
        SETTINGS['Wave'] = 1
        SETTINGS['Scrap'] = 200
        SETTINGS['Essence'] = 0.0
        SETTINGS['Current Gold'] = SETTINGS['Max Gold']
        SETTINGS['Stolen Gold'] = 0
        save_all_jsons()

        root.destroy()
        constants.RUNNING = False
        pygame.quit()
        sys.exit()

    root = tk.Tk()
    root.title("Debug Panel")
    root.geometry("300x400")

    """
    Wave Section - To adjust Wave strength from the debug panel
    """
    wave_frame = tk.Frame(root)
    wave_frame.pack(pady=5)

    wave_var = tk.StringVar()
    wave_var.set("Wave:")

    wave_label = tk.Label(wave_frame, textvariable=wave_var)
    wave_label.pack(side=tk.LEFT, pady=5)

    #Function to make the wave button update in debug window
    def update_wave(num):
        SETTINGS['Wave'] += num
        wave_var.set("Wave:")

    tk.Button(wave_frame, text="+", command=lambda: update_wave(1)).pack(side=tk.LEFT, padx=5)
    tk.Button(wave_frame, text="-", command=lambda: update_wave(-1)).pack(side=tk.LEFT, padx=5)

    """
    Scrap Section - To adjust Scrap amount from the debug panel
    """
    scrap_frame = tk.Frame(root)
    scrap_frame.pack(pady=5)

    scrap_var = tk.StringVar()
    scrap_var.set(f"Scrap:")

    scrap_label = tk.Label(scrap_frame, textvariable=scrap_var)
    scrap_label.pack(side=tk.LEFT, pady=5)

    #Function to make the scrap button update in debug window
    def update_scrap():
        SETTINGS['Scrap'] += 100
        scrap_var.set(f"Scrap:")

    tk.Button(scrap_frame, text="+100", command=lambda: update_scrap()).pack(side=tk.LEFT,pady=5)

    """
    Enemy Section - To spawn/damage/kill enemies for testing purposes
    """
    #Spawn Frames
    enemy_frames = tk.Frame(root)
    enemy_frames.pack(pady=5)
    enemy_frame(enemy_frames, "Fighter", spawn_enemy_callback)

    damage_frame = tk.Frame(root)
    damage_frame.pack(pady=5)

    tk.Button(damage_frame, text="Damage Front Enemy", command=lambda: kill_enemy_callback(5)).pack(side=tk.LEFT, pady=10)
    tk.Button(damage_frame, text="Kill Front Enemy", command=lambda: kill_enemy_callback("full")).pack(side=tk.LEFT, pady=10)

    tk.Button(root, text="Close Program", command=close_all).pack(pady=5)

    root.mainloop()

#Repeat function to set up multiple enemies for debug panel
def enemy_frame(root, enemy_type, spawn_enemy_callback):
    temp_frame = tk.Frame(root)
    temp_frame.pack(pady=5)
    tk.Button(temp_frame, text=f"Spawn {enemy_type}", command=lambda: spawn_enemy_callback(enemy_type)).pack(side=tk.LEFT, pady=10)
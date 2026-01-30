import tkinter as tk
import constants
import pygame
import sys

from functions.mapgeneration import pixel_to_grid
from constants import (
    SETTINGS,
    save_all_jsons
)

def print_grid_position(mouse_x, mouse_y, map_data):
    col, row = pixel_to_grid(mouse_x, mouse_y, map_data)

    if col is None or row is None:
        return  # Mouse not on grid — do nothing

    grid_x = col + 1
    grid_y = row + 1
    print(f"Grid: ({grid_x}, {grid_y})")

def debug_window(spawn_enemy_callback, kill_enemy_callback):
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

    #Wave Section
    wave_frame = tk.Frame(root)
    wave_frame.pack(pady=5)

    wave_var = tk.StringVar()
    wave_var.set(f"Wave: {SETTINGS['Wave']}")

    wave_label = tk.Label(wave_frame, textvariable=wave_var)
    wave_label.pack(side=tk.LEFT, pady=5)

    def update_wave(num):
        SETTINGS['Wave'] += num
        wave_var.set(f"Wave: {SETTINGS['Wave']}")

    tk.Button(wave_frame, text="+", command=lambda: update_wave(1)).pack(side=tk.LEFT, padx=5)
    tk.Button(wave_frame, text="-", command=lambda: update_wave(-1)).pack(side=tk.LEFT, padx=5)

    #Scrap Section
    scrap_frame = tk.Frame(root)
    scrap_frame.pack(pady=5)

    scrap_var = tk.StringVar()
    scrap_var.set(f"Scrap: {SETTINGS['Scrap']}")

    scrap_label = tk.Label(scrap_frame, textvariable=scrap_var)
    scrap_label.pack(side=tk.LEFT, pady=5)

    def update_scrap():
        SETTINGS['Scrap'] += 1000
        scrap_var.set(f"Scrap: {SETTINGS['Scrap']}")

    tk.Button(scrap_frame, text="+1000", command=lambda: update_scrap()).pack(side=tk.LEFT,pady=5)

    #Fighter Section
    fighter_frame = tk.Frame(root)
    fighter_frame.pack(pady=5)
    tk.Button(fighter_frame, text="Spawn Fighter", command=lambda: spawn_enemy_callback("Fighter")).pack(side=tk.LEFT, pady=10)
    tk.Button(fighter_frame, text="Damage Fighter", command=lambda: kill_enemy_callback(5)).pack(side=tk.LEFT, pady=10)
    tk.Button(fighter_frame, text="Kill Fighter", command=lambda: kill_enemy_callback("full")).pack(side=tk.LEFT, pady=10)


    tk.Button(root, text="Close Program", command=close_all).pack(pady=5)

    root.mainloop()
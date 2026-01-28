import os
import pygame

from constants import (
    MAPS,
    TILE_SIZE
)

def grid_to_pixel(col, row, map_data):
    tile_width = map_data["scaled_width"] / map_data["columns"]
    tile_height = map_data["scaled_height"] / map_data["rows"]

    x = map_data["draw_x"] + col * tile_width
    y = map_data["draw_y"] + row * tile_height

    return int(x), int(y)

def pixel_to_grid(x, y, map_data):
    if x < map_data["draw_x"] or y < map_data["draw_y"]:
        return None, None

    tile_width = map_data["scaled_width"] / map_data["columns"]
    tile_height = map_data["scaled_height"] / map_data["rows"]

    col = int((x - map_data["draw_x"]) // tile_width)
    row = int((y - map_data["draw_y"]) // tile_height)

    if col < 0 or col >= map_data["columns"]:
        return None, None
    if row < 0 or row >= map_data["rows"]:
        return None, None

    return col, row

def load_map(map_name):
    map_data = MAPS[map_name]

    image_path = os.path.join("assets", "maps", map_data["Asset"])

    map_surface = pygame.image.load(image_path).convert_alpha()

    return {
        "surface": map_surface,
        "width": map_data["Width"],
        "height": map_data["Height"],
        "columns": map_data["Columns"],
        "rows": map_data["Rows"],
        "spawn": map_data["Spawn"],
        "cap": map_data["Cap"],
        "path": map_data["Path"]
    }

def draw_grid(screen, map_data):
    tile_width = map_data["scaled_width"] / map_data["columns"]
    tile_height = map_data["scaled_height"] / map_data["rows"]

    for col in range(map_data["columns"] + 1):
        x = map_data["draw_x"] + col * tile_width
        pygame.draw.line(
            screen,
            (255, 255, 255),
            (x, map_data["draw_y"]),
            (x, map_data["draw_y"] + map_data["scaled_height"]),
            1
        )

    for row in range(map_data["rows"] + 1):
        y = map_data["draw_y"] + row * tile_height
        pygame.draw.line(
            screen,
            (255, 255, 255),
            (map_data["draw_x"], y),
            (map_data["draw_x"] + map_data["scaled_width"], y),
            1
        )
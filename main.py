"""
This page is for processing and running the game loop
"""

import pygame
import gameconfig
import threading

from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DEBUG_MODE
)

from gameconfig import (
    SETTINGS
)

from functions.mapgeneration import (
    load_map,
    draw_grid
)

from functions.debugfunctions import (
    print_grid_position,
    debug_window
)

from game.game import Game
from game.ui import UIManager

#Main game loop
def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tower Defense")

    clock = pygame.time.Clock()

    current_map = None
    game = None
    debug_thread_started = False

    gameconfig.RUNNING = True

    while gameconfig.RUNNING:
        dt = clock.tick(60) / 1000  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gameconfig.RUNNING = False

            if event.type == pygame.KEYDOWN:
                if gameconfig.GAME_STATE == "menu" and event.key == pygame.K_RETURN:
                    # -------- LOAD MAP --------
                    current_map = load_map("Testmap")

                    scale_factor = SCREEN_HEIGHT / current_map["height"]
                    new_width = int(current_map["width"] * scale_factor)
                    new_height = SCREEN_HEIGHT

                    scaled_surface = pygame.transform.scale(
                        current_map["surface"],
                        (new_width, new_height)
                    )

                    current_map["scaled_surface"] = scaled_surface
                    current_map["scaled_width"] = new_width
                    current_map["scaled_height"] = new_height
                    current_map["draw_x"] = (SCREEN_WIDTH - new_width) // 2
                    current_map["draw_y"] = 0

                    # -------- CREATE GAME --------
                    game = Game(current_map)
                    ui = UIManager(game)
                    gameconfig.GAME_STATE = "play"

                    # -------- START DEBUG PANEL (ONCE) --------
                    if DEBUG_MODE and not debug_thread_started:
                        threading.Thread(
                            target=debug_window,
                            args=(game.spawn_enemy,
                                  game.kill_earliest_enemy),
                            daemon=True
                        ).start()
                        debug_thread_started = True

            if gameconfig.GAME_STATE == "play":
                ui.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    print_grid_position(mouse_x, mouse_y, current_map)

        # -------- DRAW --------
        screen.fill((30, 30, 30))

        if gameconfig.GAME_STATE == "menu":
            font = pygame.font.SysFont(None, 48)
            text = font.render("Press ENTER to Play", True, (255, 255, 255))
            screen.blit(text, (200, 250))

        elif gameconfig.GAME_STATE == "play":
            screen.blit(
                current_map["scaled_surface"],
                (current_map["draw_x"], current_map["draw_y"])
            )

            game.update(dt)
            game.draw(screen)
            ui.draw(screen)

            if DEBUG_MODE:
                draw_grid(screen, current_map)

            font = pygame.font.SysFont(None, 24)
            gold_text = f"Max Gold: {SETTINGS['Max Gold']}  Current Gold: {SETTINGS['Current Gold']}  Stolen Gold: {SETTINGS['Stolen Gold']}"
            wave_text = f"Wave: {SETTINGS['Wave']}"
            scrap_text = f"Scrap: {int(SETTINGS['Scrap'])}  Essence: {int(SETTINGS['Essence'])}"

            gold_surface = font.render(gold_text, True, (255, 255, 0))
            wave_surface = font.render(wave_text, True, (255, 255, 0))
            scrap_surface = font.render(scrap_text, True, (255, 255, 0))

            screeny = 10
            screen.blit(gold_surface, (10, screeny))
            screeny += gold_surface.get_height() + 4
            screen.blit(wave_surface, (10, screeny))
            screeny += wave_surface.get_height() + 4
            screen.blit(scrap_surface, (10, screeny))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
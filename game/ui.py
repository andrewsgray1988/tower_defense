"""
This file is for handling user interface interaction logic
"""

import pygame

from gameconfig import (
    TOWER_CHOICES,
    TOWERS,
    SETTINGS
)
from constants import (
    BUILD_MENU_BUTTON_WIDTH,
    BUILD_MENU_BUTTON_HEIGHT
)
from game.game import TileState

class UIManager:
    def __init__(self, game):
        self.game = game
        self._build_menu_open = False
        self._menu_tile = None
        self.font = pygame.font.SysFont(None, 20)
        self.build_options = TOWER_CHOICES
        self.button_rects = {}
        self._selected_tower = None
        self._tower_menu_open = False

    """
    Input Logic
    """

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_left_click(event.pos)
            elif event.button == 3:  # right click
                self.handle_right_click()

    def handle_left_click(self, mouse_pos):
        col, row = self.game.screen_to_tile(mouse_pos)
        if col is None or row is None:
            return

        # If build menu already open, handle menu clicks
        if self._build_menu_open:
            self.handle_build_menu_click(mouse_pos)
            return

        if self._tower_menu_open:
            self.handle_tower_menu_click(mouse_pos)
            return

        tile_state = self.game.get_tile_state(col, row)

        #
        if tile_state == TileState.BUILDABLE:
            self.open_build_menu(col, row)

        elif tile_state == TileState.TOWER:
            tower = self.game.get_tower_at(col, row)

            if tower:
               self.open_tower_menu(col, row, tower)


    def handle_right_click(self):
        if self._build_menu_open:
            self.close_build_menu()

    """
    Build Menu Logic
    """

    def open_build_menu(self, col, row):
        self._build_menu_open = True
        self._menu_tile = (col, row)

    def close_build_menu(self):
        self._build_menu_open = False
        self._menu_tile = None
        self.button_rects = {}

    def handle_build_menu_click(self, mouse_pos):
        for tower_key, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                col, row = self._menu_tile
                success = self.game.place_tower(tower_key, col, row)

                if success:
                    self.close_build_menu()
                return

        # Clicked outside buttons → close menu
        self.close_build_menu()

    """
    Tower Menu Logic
    """

    def open_tower_menu(self, col, row, tower):
        self._tower_menu_open = True
        self._selected_tower = tower
        self._menu_tile = (col, row)

    def close_tower_menu(self):
        self._tower_menu_open = False
        self._selected_tower = None
        self._menu_tile = None
        self.button_rects = {}

    def handle_tower_menu_click(self, mouse_pos):
        for action, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):

                tower = self._selected_tower
                if not tower:
                    return

                if action == "upgrade":
                    if SETTINGS["Scrap"] >= tower.upgrade_cost:
                        SETTINGS["Scrap"] -= tower.upgrade_cost
                        tower.upgrade_tower()

                elif action == "sell":
                    SETTINGS["Scrap"] += tower.sell_amount
                    self.game.set_tile_state(tower.col, tower.row, TileState.BUILDABLE)
                    tower._sold = True

                self.close_tower_menu()
                return

        self.close_tower_menu()

    """
    Rendering
    """

    def draw(self, screen):
        if self._build_menu_open:
            self.draw_build_menu(screen)

        elif self._tower_menu_open:
            self.draw_tower_menu(screen)

    def draw_build_menu(self, screen):
        col, row = self._menu_tile
        menu_x, menu_y = self.game.tile_to_screen(col, row)

        button_width = BUILD_MENU_BUTTON_WIDTH
        button_height = BUILD_MENU_BUTTON_HEIGHT
        padding = 5

        self.button_rects = {}

        for i, tower_key in enumerate(self.build_options):
            rect = pygame.Rect(
                menu_x,
                menu_y + i * (button_height + padding),
                button_width,
                button_height
            )
            self.button_rects[tower_key] = rect

            tower_cost = TOWERS[tower_key]["default_cost"]
            can_afford = SETTINGS["Scrap"] >= tower_cost

            bg_color = (80, 80, 80) if can_afford else (40, 40, 40)
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)

            text_color = (255, 255, 255) if can_afford else (150, 150, 150)
            text = self.font.render(
                f"{tower_key} - {tower_cost} Scrap",
                True,
                text_color
            )
            screen.blit(text, (rect.x + 8, rect.y + 8))

    def draw_tower_menu(self, screen):
        tower = self._selected_tower
        if not tower:
            return

        menu_x, menu_y = self.game.tile_to_screen(tower.col, tower.row)

        button_width = BUILD_MENU_BUTTON_WIDTH
        button_height = BUILD_MENU_BUTTON_HEIGHT
        padding = 5

        self.button_rects = {}

        options = [
            ("upgrade", f"Upgrade - {tower.upgrade_cost} Scrap"),
            ("sell", f"Sell - {tower.sell_amount} Scrap")
        ]

        for i, (action, label) in enumerate(options):
            rect = pygame.Rect(
                menu_x,
                menu_y + i * (button_height + padding),
                button_width,
                button_height
            )

            self.button_rects[action] = rect

            # Afford check only applies to upgrade
            if action == "upgrade":
                can_afford = SETTINGS["Scrap"] >= tower.upgrade_cost
            else:
                can_afford = True

            bg_color = (80, 80, 80) if can_afford else (40, 40, 40)
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)

            text_color = (255, 255, 255) if can_afford else (150, 150, 150)

            text = self.font.render(label, True, text_color)
            screen.blit(text, (rect.x + 8, rect.y + 8))
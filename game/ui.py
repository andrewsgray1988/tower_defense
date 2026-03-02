"""
This file is for handling user interface interaction logic
"""

import pygame
import gameconfig

from gameconfig import (
    TOWER_CHOICES,
    TOWERS,
    STRUCTURES,
    SETTINGS
)
from constants import (
    BUILD_MENU_BUTTON_WIDTH,
    BUILD_MENU_BUTTON_HEIGHT
)
from game.game import TileState
from functions.general import close_program, reset_jsons
from models.structures import Structure

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
        self.quit_button_rect = None
        self._mage_primed = False
        self._stored_mage_tower = None
        self._direction_select_open = False
        self._pending_tower_key = None

    """
    Input Logic
    """
    #Click event handler
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            #Left click handler
            if event.button == 1:
                self.handle_left_click(event.pos)
            #Right click handler
            elif event.button == 3:  # right click
                self.handle_right_click()

    #Functions for the left click
    def handle_left_click(self, mouse_pos):
        from models.towers import Mage
        #Quit button handler
        if self.quit_button_rect and self.quit_button_rect.collidepoint(mouse_pos):
            close_program()
            return
        #Restart button handler
        if self.restart_button_rect and self.restart_button_rect.collidepoint(mouse_pos):
            reset_jsons()
            gameconfig.GAME_STATE = "menu"
            return
        #If build menu already open, handle menu clicks
        if self._build_menu_open:
            self.handle_build_menu_click(mouse_pos)
            return
        #If Tower menu already open, handle menu clicks
        if self._tower_menu_open:
            clicked_button = False
            for rect in self.button_rects.values():
                if rect.collidepoint(mouse_pos):
                    clicked_button = True
                    break
            if clicked_button:
                self.handle_tower_menu_click(mouse_pos)
                return
        if self._direction_select_open:
            self.handle_direction_select(mouse_pos)
        #Tile check
        col, row = self.game.screen_to_tile(mouse_pos)
        if col is None or row is None:
            return
        #Handle Mage Tower Click Target
        if self._mage_primed:
            coord = (col, row)
            print("KABOOM!")
            self._stored_mage_tower._deal_damage(coord)
            self._stored_mage_tower._attack_timer = 0
            self._mage_primed = False
            self._stored_mage_tower = None
            self.close_tower_menu()
            return

        tile_state = self.game.get_tile_state(col, row)

        """
        Checks tile state to see how to handle next step on click
        """
        #If tile state is buildable, open the build menu
        if tile_state == TileState.BUILDABLE:
            self.open_build_menu(col, row)

        #If the tile state is a tower, open the tower menu
        elif tile_state == TileState.TOWER:
            tower = self.game.get_tower_at(col, row)
            if tower and isinstance(tower, Mage):
                if tower._attack_timer == tower.attack_speed:
                    self.open_tower_menu(col, row, tower)
                    self._mage_primed = True
                    self._stored_mage_tower = tower
            elif tower:
               self.open_tower_menu(col, row, tower)

    #Functions for the right click
    def handle_right_click(self):
        if self._build_menu_open:
            self.close_build_menu()
        if self._tower_menu_open:
            self.close_tower_menu()
        if self._mage_primed:
            self._mage_primed = False
            self._stored_mage_tower = None

    """
    Build Menu Logic
    """
    #Open the Build Menu
    def open_build_menu(self, col, row):
        self._build_menu_open = True
        self._menu_tile = (col, row)

    #Close the Build Menu
    def close_build_menu(self):
        self._build_menu_open = False
        self._menu_tile = None
        self.button_rects = {}

    #Handlers for the Build Menu
    def handle_build_menu_click(self, mouse_pos):
        for tower_key, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                col, row = self._menu_tile
                if tower_key == "Flamethrower":
                    self._pending_tower_key = tower_key
                    self._direction_select_open = True
                    pending_tile = self._menu_tile
                    self.close_build_menu()
                    self._menu_tile = pending_tile
                    return

                success = self.game.place_tower(tower_key, col, row)
                if success:
                    self.close_build_menu()
                return

        # Clicked outside buttons → close menu
        self.close_build_menu()

    def handle_direction_select(self, mouse_pos):
        for direction, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                col, row = self._menu_tile

                success = self.game.place_tower(self._pending_tower_key, col, row, direction)
                if success:
                    self._direction_select_open = False
                    self._pending_tower_key = None
                    self._menu_tile = None
                    self.button_rects = {}
                return
        self._direction_select_open = False
        self._pending_tower_key = None
        self.button_rects = {}

    """
    Tower Menu Logic
    """
    #Open the Tower Menu
    def open_tower_menu(self, col, row, tower):
        self._tower_menu_open = True
        self._selected_tower = tower
        self._menu_tile = (col, row)

    #Close the Tower Menu
    def close_tower_menu(self):
        self._tower_menu_open = False
        self._selected_tower = None
        self._menu_tile = None
        self.button_rects = {}

    #Handlers for the Tower Menu
    def handle_tower_menu_click(self, mouse_pos):
        for action, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                unit = self._selected_tower
                if not unit:
                    return

                if isinstance(unit, Structure):
                    if action == "upgrade":
                        if SETTINGS["Scrap"] >= unit.upgrade_cost:
                            SETTINGS["Scrap"] -= unit.upgrade_cost
                            unit.upgrade_structure()
                    elif action == "sell":
                        SETTINGS["Scrap"] += unit.sell_amount
                        self.game.set_tile_state(unit.col, unit.row, TileState.BUILDABLE)
                        unit._sold = True
                else:
                    if action == "upgrade":
                        if SETTINGS["Scrap"] >= unit.upgrade_cost:
                            SETTINGS["Scrap"] -= unit.upgrade_cost
                            unit.upgrade_tower()
                    elif action == "sell":
                        SETTINGS["Scrap"] += unit.sell_amount
                        self.game.set_tile_state(unit.col, unit.row, TileState.BUILDABLE)
                        unit._sold = True
                if self._mage_primed:
                    self._mage_primed = False
                    self._stored_mage_tower = None
                self.close_tower_menu()
                return
        if self._mage_primed:
            self._mage_primed = False
            self._stored_mage_tower = None
        self.close_tower_menu()

    """
    Rendering
    """
    #Logic that draw the menus on screen
    def draw(self, screen):
        if self._build_menu_open:
            self.draw_build_menu(screen)

        elif self._tower_menu_open:
            self.draw_tower_menu(screen)

        if self._direction_select_open:
            self.draw_direction_select(screen)

        self.draw_quit_button(screen)
        self.draw_restart_button(screen)

    #Function that draws the build menu on screen
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

            if tower_key in TOWERS:
                tower_cost = TOWERS[tower_key]["default_cost"]
            elif tower_key in STRUCTURES:
                tower_cost = STRUCTURES[tower_key]["default_cost"]
            else:
                continue  # invalid key
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

    #Function that draws the tower menu on screen
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

            #Afford check only applies to upgrade
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

    """
    Quit Button
    """
    #Function that draws the quit button on screen
    def draw_quit_button(self, screen):
        button_width = 120
        button_height = 40
        padding = 20

        x = screen.get_width() - button_width - padding
        y = screen.get_height() - button_height - padding

        rect = pygame.Rect(x, y, button_width, button_height)
        self.quit_button_rect = rect

        pygame.draw.rect(screen, (120, 30, 30), rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)

        text = self.font.render("Quit", True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    def draw_restart_button(self, screen):
        button_width = 120
        button_height = 40

        x = screen.get_width() - button_width - 160
        y = screen.get_height() - button_height - 20

        rect = pygame.Rect(x, y, button_width, button_height)
        self.restart_button_rect = rect

        pygame.draw.rect(screen, (120, 30, 30), rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)

        text = self.font.render("Restart", True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    def draw_direction_select(self, screen):
        col, row = self._menu_tile
        menu_x, menu_y = self.game.tile_to_screen(col, row)

        button_width = BUILD_MENU_BUTTON_WIDTH
        button_height = BUILD_MENU_BUTTON_HEIGHT
        padding = 5

        self.button_rects = {}

        directions = ["North", "South", "East", "West"]

        for i, direction in enumerate(directions):
            rect = pygame.Rect(
                menu_x,
                menu_y + i * (button_height + padding),
                button_width,
                button_height
            )

            self.button_rects[direction] = rect

            pygame.draw.rect(screen, (80, 80, 80), rect)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)

            text = self.font.render(direction, True, (255, 255, 255))
            screen.blit(text, (rect.x + 8, rect.y + 8))
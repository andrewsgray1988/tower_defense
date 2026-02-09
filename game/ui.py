"""
This file is for handling user interface interaction logic
"""

import pygame

#Initiates the detection for user interface mid game
class UIManager:
    def __init__(self, game):
        self.game = game
        self._build_menu_open = False
        self._build_menu_tile = None
        self.font = pygame.font.SysFont(None, 20)

    """
    Input Logic
    """

    #Event Handler
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_left_click(event.pos)

    #Left Click functions
    def handle_left_click(self, mouse_pos):
        col, row = self.game.screen_to_tile(mouse_pos)
        if col is None or row is None:
            return

        if self._build_menu_open:
            self.handle_build_menu_click(mouse_pos)
            return

        if self.game.is_tile_buildable(col, row):
            self.open_build_menu(col, row)

    """
    Build Menu Logic
    """

    #Open the build menu
    def open_build_menu(self, col, row):
        self._build_menu_open = True
        self._build_menu_tile = (col, row)

    #Close the build menu
    def close_build_menu(self):
        self._build_menu_open = False
        self._build_menu_tile = None

    #Build menu handler
    def handle_build_menu_click(self, mouse_pos):
        #Placeholder
        self.close_build_menu()

    """
    Rendering
    """

    def draw(self, screen):
        if self._build_menu_open:
            self.draw_build_menu(screen)

    def draw_build_menu(self, screen):
        col, row = self._build_menu_tile
        x, y = self.game.tile_to_screen(col, row)

        panel_rect = pygame.Rect(x, y - 60, 100, 50)
        pygame.draw.rect(screen, (30, 30, 30), panel_rect)
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)

        text = self.font.render("Build Tower", True, (255, 255, 255))
        screen.blit(text, (panel_rect.x + 8, panel_rect.y + 8))
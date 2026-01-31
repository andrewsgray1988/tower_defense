"""
This file is for handling user interface interaction
"""

import pygame

#Initiates the detection for user interface mid game
class UIManager:
    def __init__(self, game):
        self.game = game
        self._build_menu_open = False
        self._build_menu_tile = None
        self.font = pygame.font.SysFont(None, 20)

    #Event Handler
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.handle_left_click(event.pos)

    #Left Click functions
    def handle_left_click(self, mouse_pos):
        col, row = self.game.screen_to_tile(mouse_pos)
            if col is None or row is None:
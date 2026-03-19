"""
This file is for handling reusable visual functions
"""

from game.floating_text import FloatingText

def spawn_floating_text(game, x, y, amount, text_type):
    if text_type == "damage":
        color = (255, 50, 50)
    elif text_type == "heal":
        color = (50, 255, 50)
    else:
        color = (255, 255, 255)

    text = FloatingText(x, y, amount, color)
    game.floating_texts.append(text)
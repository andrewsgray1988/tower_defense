from models.enemies import Fighter

from constants import SETTINGS

class Game:
    def __init__(self, map_data):
        self.map_data = map_data
        self.enemies = []
        self.towers = []
        self.stored_gold = SETTINGS['Max Gold']

    def spawn_enemy(self, enemy_type="Fighter"):
        if enemy_type == "Fighter":
            enemy = Fighter()
        else:
            return

        enemy.spawn(self.map_data)
        self.enemies.append(enemy)

    def update(self, dt):
        for enemy in self.enemies:
            enemy.move_along_path(self.map_data, dt)
        self.enemies = [e for e in self.enemies if e._alive]

    def draw(self, screen):
        for enemy in self.enemies:
            enemy.draw(screen)
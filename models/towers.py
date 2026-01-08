

class Tower:
    def __init__(self, name, health, cost, armor, upgrade_cost, damage):
        self.name = name
        self.health = health
        self.max_health = health
        self.cost = cost
        self.armor = armor
        self.upgrade_cost = upgrade_cost
        self.damage = damage

    def destroy_tower(self):
        pass

    def deal_damage(self):
        return self.damage

    def take_damage(self, damage):
        self.health -= damage - self.armor
        if self.health <= 0:
            self.destroy_tower()
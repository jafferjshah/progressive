"""
Domain models for Restbucks
"""

class Order:
    def __init__(self, id, drink, size="medium", milk="whole", shots=1):
        self.id = id
        self.drink = drink
        self.size = size
        self.milk = milk
        self.shots = shots
        self.status = "pending"
        self.paid = False
        self.card_last_four = None

    @property
    def cost(self):
        base = {"small": 2.50, "medium": 3.00, "large": 3.50}
        return base.get(self.size, 3.00) + (self.shots - 1) * 0.50

    def to_dict(self):
        return {
            "id": self.id,
            "drink": self.drink,
            "size": self.size,
            "milk": self.milk,
            "shots": self.shots,
            "cost": self.cost,
            "status": self.status,
            "paid": self.paid
        }

    def __str__(self):
        return f"#{self.id}: {self.size} {self.drink}, {self.milk} milk, {self.shots} shots - ${self.cost:.2f}"


class Payment:
    def __init__(self, card_number, amount):
        self.card_number = card_number
        self.amount = amount

    @property
    def last_four(self):
        return self.card_number[-4:]

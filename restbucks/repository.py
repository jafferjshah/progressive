"""
Data access layer - stores orders in memory
"""

from models import Order


class OrderRepository:
    def __init__(self):
        self._orders = {}
        self._next_id = 1

    def create(self, drink, size, milk, shots):
        order = Order(self._next_id, drink, size, milk, shots)
        self._orders[order.id] = order
        self._next_id += 1
        return order

    def get(self, order_id):
        return self._orders.get(order_id)

    def get_all(self):
        return list(self._orders.values())

    def get_pending_paid(self):
        return [o for o in self._orders.values() if o.paid and o.status == "pending"]

    def update(self, order):
        if order.id in self._orders:
            self._orders[order.id] = order
        return order


# single instance for now
order_repo = OrderRepository()

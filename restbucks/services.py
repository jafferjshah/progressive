"""
Business logic layer
"""

from repository import order_repo


class OrderService:
    def place_order(self, drink, size="medium", milk="whole", shots=1):
        order = order_repo.create(drink, size, milk, shots)
        return order

    def update_order(self, order_id, **changes):
        order = order_repo.get(order_id)
        if not order:
            return None, "Order not found"

        if order.status != "pending":
            return None, "Order is already being prepared"

        for key, value in changes.items():
            if hasattr(order, key) and key not in ["id", "status", "paid"]:
                setattr(order, key, value)

        order_repo.update(order)
        return order, None

    def get_order(self, order_id):
        return order_repo.get(order_id)


class PaymentService:
    def pay(self, order_id, card_number, amount):
        order = order_repo.get(order_id)
        if not order:
            return False, "Order not found"

        if order.paid:
            return True, "Already paid"

        if amount < order.cost:
            return False, f"Insufficient amount. Need ${order.cost:.2f}"

        order.paid = True
        order.card_last_four = card_number[-4:]
        order_repo.update(order)

        return True, None


class BaristaService:
    def get_pending_orders(self):
        return order_repo.get_pending_paid()

    def start_preparing(self, order_id):
        order = order_repo.get(order_id)
        if not order:
            return False, "Order not found"

        if not order.paid:
            return False, "Order not paid"

        order.status = "preparing"
        order_repo.update(order)
        return True, None

    def complete_order(self, order_id):
        order = order_repo.get(order_id)
        if not order:
            return False, "Order not found"

        order.status = "ready"
        order_repo.update(order)
        return True, None

    def deliver_order(self, order_id):
        order = order_repo.get(order_id)
        if not order:
            return False, "Order not found"

        if order.status != "ready":
            return False, "Order not ready"

        order.status = "delivered"
        order_repo.update(order)
        return True, None


# service instances
order_service = OrderService()
payment_service = PaymentService()
barista_service = BaristaService()

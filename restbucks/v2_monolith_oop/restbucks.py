"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v2: Now with classes!
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

    def __str__(self):
        return f"#{self.id}: {self.size} {self.drink}, {self.milk} milk, {self.shots} shots - ${self.cost:.2f}"


class Payment:
    def __init__(self, card_number, amount):
        self.card_number = card_number
        self.amount = amount

    @property
    def last_four(self):
        return self.card_number[-4:]


class Shop:
    def __init__(self):
        self.orders = {}
        self.next_id = 1

    def place_order(self, drink, size="medium", milk="whole", shots=1):
        order = Order(self.next_id, drink, size, milk, shots)
        self.orders[order.id] = order
        self.next_id += 1

        print(f"Order placed! {order}")
        return order

    def update_order(self, order_id, **changes):
        order = self.orders.get(order_id)
        if not order:
            print(f"Order #{order_id} not found")
            return None

        if order.status != "pending":
            print(f"Sorry, order #{order_id} is already being prepared. Can't modify it.")
            return None

        for key, value in changes.items():
            if hasattr(order, key) and key not in ["id", "status", "paid"]:
                setattr(order, key, value)

        print(f"Order updated! {order}")
        return order

    def pay(self, order_id, payment):
        order = self.orders.get(order_id)
        if not order:
            print(f"Order #{order_id} not found")
            return False

        if order.paid:
            print(f"Order #{order_id} is already paid")
            return True

        if payment.amount < order.cost:
            print(f"Insufficient amount. Order costs ${order.cost:.2f}")
            return False

        order.paid = True
        order.card_last_four = payment.last_four

        print(f"Payment accepted for order #{order_id} (card ending {payment.last_four})")
        return True

    def get_pending_orders(self):
        pending = [o for o in self.orders.values() if o.paid and o.status == "pending"]

        if not pending:
            print("No orders to prepare")
            return []

        print(f"Orders to prepare: {len(pending)}")
        for o in pending:
            print(f"  {o}")
        return pending

    def start_preparing(self, order_id):
        order = self.orders.get(order_id)
        if not order:
            print(f"Order #{order_id} not found")
            return False

        if not order.paid:
            print(f"Order #{order_id} hasn't been paid yet")
            return False

        order.status = "preparing"
        print(f"Started preparing order #{order_id}")
        return True

    def complete_order(self, order_id):
        order = self.orders.get(order_id)
        if not order:
            print(f"Order #{order_id} not found")
            return False

        order.status = "ready"
        print(f"Order #{order_id} is ready for pickup!")
        return True

    def deliver_order(self, order_id):
        order = self.orders.get(order_id)
        if not order:
            print(f"Order #{order_id} not found")
            return False

        if order.status != "ready":
            print(f"Order #{order_id} is not ready yet")
            return False

        order.status = "delivered"
        print(f"Order #{order_id} delivered. Enjoy your {order.drink}!")
        return True


if __name__ == "__main__":
    print("=== Restbucks Coffee Shop ===\n")

    shop = Shop()

    # Customer places an order
    print("-- Customer: placing order --")
    order = shop.place_order("latte", size="large", milk="semi-skimmed", shots=2)

    print("\n-- Customer: adding an extra shot --")
    shop.update_order(order.id, shots=3)

    print("\n-- Customer: paying --")
    payment = Payment("1234567890123456", 5.00)
    shop.pay(order.id, payment)

    print("\n-- Barista: checking orders --")
    shop.get_pending_orders()

    print("\n-- Barista: making the drink --")
    shop.start_preparing(order.id)

    print("\n-- Customer tries to modify (too late!) --")
    shop.update_order(order.id, shots=1)

    print("\n-- Barista: order done --")
    shop.complete_order(order.id)

    print("\n-- Customer: picking up --")
    shop.deliver_order(order.id)

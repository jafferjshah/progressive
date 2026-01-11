"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/
"""

# our "database"
orders = {}
next_order_id = 1

def place_order(drink, size="medium", milk="whole", shots=1):
    global next_order_id

    order = {
        "id": next_order_id,
        "drink": drink,
        "size": size,
        "milk": milk,
        "shots": shots,
        "status": "pending",
        "cost": calculate_cost(size, shots),
        "paid": False
    }
    orders[next_order_id] = order
    next_order_id += 1

    print(f"Order placed! Order #{order['id']}")
    print(f"  {size} {drink}, {milk} milk, {shots} shot(s)")
    print(f"  Cost: ${order['cost']:.2f}")
    return order

def calculate_cost(size, shots):
    base = {"small": 2.50, "medium": 3.00, "large": 3.50}
    return base.get(size, 3.00) + (shots - 1) * 0.50

def update_order(order_id, **changes):
    if order_id not in orders:
        print(f"Order #{order_id} not found")
        return None

    order = orders[order_id]

    if order["status"] != "pending":
        print(f"Sorry, order #{order_id} is already being prepared. Can't modify it.")
        return None

    for key, value in changes.items():
        if key in order and key not in ["id", "status", "paid"]:
            order[key] = value

    # recalculate cost
    order["cost"] = calculate_cost(order["size"], order["shots"])

    print(f"Order #{order_id} updated!")
    print(f"  {order['size']} {order['drink']}, {order['milk']} milk, {order['shots']} shot(s)")
    print(f"  New cost: ${order['cost']:.2f}")
    return order

def pay_for_order(order_id, card_number, amount):
    if order_id not in orders:
        print(f"Order #{order_id} not found")
        return False

    order = orders[order_id]

    if order["paid"]:
        print(f"Order #{order_id} is already paid")
        return True

    if amount < order["cost"]:
        print(f"Insufficient amount. Order costs ${order['cost']:.2f}")
        return False

    # pretend we're processing the card
    order["paid"] = True
    order["card_last_four"] = card_number[-4:]

    print(f"Payment accepted for order #{order_id}")
    print(f"  Card ending in {order['card_last_four']}")
    return True

def get_pending_orders():
    """Barista checks what orders need to be made"""
    pending = [o for o in orders.values() if o["paid"] and o["status"] == "pending"]

    if not pending:
        print("No orders to prepare")
        return []

    print(f"Orders to prepare: {len(pending)}")
    for o in pending:
        print(f"  #{o['id']}: {o['size']} {o['drink']}, {o['milk']} milk, {o['shots']} shots")
    return pending

def start_preparing(order_id):
    """Barista starts making the order"""
    if order_id not in orders:
        print(f"Order #{order_id} not found")
        return False

    order = orders[order_id]

    if not order["paid"]:
        print(f"Order #{order_id} hasn't been paid yet")
        return False

    order["status"] = "preparing"
    print(f"Started preparing order #{order_id}")
    return True

def complete_order(order_id):
    """Barista finishes the order"""
    if order_id not in orders:
        print(f"Order #{order_id} not found")
        return False

    order = orders[order_id]
    order["status"] = "ready"
    print(f"Order #{order_id} is ready for pickup!")
    return True

def deliver_order(order_id):
    """Customer picks up their drink"""
    if order_id not in orders:
        print(f"Order #{order_id} not found")
        return False

    order = orders[order_id]

    if order["status"] != "ready":
        print(f"Order #{order_id} is not ready yet")
        return False

    order["status"] = "delivered"
    print(f"Order #{order_id} delivered. Enjoy your {order['drink']}!")
    return True


if __name__ == "__main__":
    print("=== Restbucks Coffee Shop ===\n")

    # Customer places an order
    print("-- Customer: placing order --")
    order = place_order("latte", size="large", milk="semi-skimmed", shots=2)

    print("\n-- Customer: adding an extra shot --")
    update_order(order["id"], shots=3)

    print("\n-- Customer: paying --")
    pay_for_order(order["id"], "1234567890123456", 5.00)

    print("\n-- Barista: checking orders --")
    get_pending_orders()

    print("\n-- Barista: making the drink --")
    start_preparing(order["id"])

    print("\n-- Customer tries to modify (too late!) --")
    update_order(order["id"], shots=1)

    print("\n-- Barista: order done --")
    complete_order(order["id"])

    print("\n-- Customer: picking up --")
    deliver_order(order["id"])

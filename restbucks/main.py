"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v3: Layered architecture - models, repository, services
"""

from services import order_service, payment_service, barista_service


def main():
    print("=== Restbucks Coffee Shop ===\n")

    # Customer places an order
    print("-- Customer: placing order --")
    order = order_service.place_order("latte", size="large", milk="semi-skimmed", shots=2)
    print(f"Order placed! {order}")

    print("\n-- Customer: adding an extra shot --")
    order, err = order_service.update_order(order.id, shots=3)
    if err:
        print(f"Error: {err}")
    else:
        print(f"Order updated! {order}")

    print("\n-- Customer: paying --")
    success, err = payment_service.pay(order.id, "1234567890123456", 5.00)
    if success:
        print(f"Payment accepted for order #{order.id}")
    else:
        print(f"Error: {err}")

    print("\n-- Barista: checking orders --")
    pending = barista_service.get_pending_orders()
    if pending:
        print(f"Orders to prepare: {len(pending)}")
        for o in pending:
            print(f"  {o}")
    else:
        print("No orders to prepare")

    print("\n-- Barista: making the drink --")
    success, err = barista_service.start_preparing(order.id)
    if success:
        print(f"Started preparing order #{order.id}")
    else:
        print(f"Error: {err}")

    print("\n-- Customer tries to modify (too late!) --")
    order_id = order.id
    updated, err = order_service.update_order(order_id, shots=1)
    if err:
        print(f"Sorry: {err}")
    else:
        print(f"Order updated! {updated}")

    print("\n-- Barista: order done --")
    barista_service.complete_order(order_id)
    print(f"Order #{order_id} is ready for pickup!")

    print("\n-- Customer: picking up --")
    order = order_service.get_order(order_id)
    barista_service.deliver_order(order_id)
    print(f"Order #{order_id} delivered. Enjoy your {order.drink}!")


if __name__ == "__main__":
    main()

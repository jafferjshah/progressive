"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v5: Basic REST - resource-oriented URLs, but still mostly POST
"""

from fastapi import FastAPI

app = FastAPI()

# our "database"
orders = {}
next_order_id = 1


def calculate_cost(size, shots):
    base = {"small": 2.50, "medium": 3.00, "large": 3.50}
    return base.get(size, 3.00) + (shots - 1) * 0.50


# Customer endpoints

@app.post("/orders")
def create_order(drink: str, size: str = "medium", milk: str = "whole", shots: int = 1):
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

    return {"success": True, "order": order}


@app.post("/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in orders:
        return {"success": False, "error": "Order not found"}

    return {"success": True, "order": orders[order_id]}


@app.post("/orders/{order_id}/update")
def update_order(order_id: int, drink: str = None, size: str = None, milk: str = None, shots: int = None):
    if order_id not in orders:
        return {"success": False, "error": "Order not found"}

    order = orders[order_id]

    if order["status"] != "pending":
        return {"success": False, "error": "Order is already being prepared"}

    if drink:
        order["drink"] = drink
    if size:
        order["size"] = size
    if milk:
        order["milk"] = milk
    if shots:
        order["shots"] = shots

    order["cost"] = calculate_cost(order["size"], order["shots"])

    return {"success": True, "order": order}


@app.post("/orders/{order_id}/payment")
def pay_order(order_id: int, card_number: str, amount: float):
    if order_id not in orders:
        return {"success": False, "error": "Order not found"}

    order = orders[order_id]

    if order["paid"]:
        return {"success": True, "message": "Already paid"}

    if amount < order["cost"]:
        return {"success": False, "error": f"Insufficient amount. Need ${order['cost']:.2f}"}

    order["paid"] = True
    order["card_last_four"] = card_number[-4:]

    return {"success": True, "message": "Payment accepted"}


# Barista endpoints

@app.post("/orders/pending")
def get_pending_orders():
    pending = [o for o in orders.values() if o["paid"] and o["status"] == "pending"]
    return {"success": True, "orders": pending}


@app.post("/orders/{order_id}/prepare")
def start_preparing(order_id: int):
    if order_id not in orders:
        return {"success": False, "error": "Order not found"}

    order = orders[order_id]

    if not order["paid"]:
        return {"success": False, "error": "Order not paid"}

    order["status"] = "preparing"
    return {"success": True, "message": "Started preparing"}


@app.post("/orders/{order_id}/ready")
def complete_order(order_id: int):
    if order_id not in orders:
        return {"success": False, "error": "Order not found"}

    order = orders[order_id]
    order["status"] = "ready"
    return {"success": True, "message": "Order ready"}


@app.post("/orders/{order_id}/deliver")
def deliver_order(order_id: int):
    if order_id not in orders:
        return {"success": False, "error": "Order not found"}

    order = orders[order_id]

    if order["status"] != "ready":
        return {"success": False, "error": "Order not ready"}

    order["status"] = "delivered"
    return {"success": True, "message": "Order delivered"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v6: Proper REST - correct HTTP methods and status codes
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# our "database"
orders = {}
next_order_id = 1


def calculate_cost(size, shots):
    base = {"small": 2.50, "medium": 3.00, "large": 3.50}
    return base.get(size, 3.00) + (shots - 1) * 0.50


class OrderRequest(BaseModel):
    drink: str
    size: str = "medium"
    milk: str = "whole"
    shots: int = 1


class OrderUpdate(BaseModel):
    drink: Optional[str] = None
    size: Optional[str] = None
    milk: Optional[str] = None
    shots: Optional[int] = None


class PaymentRequest(BaseModel):
    card_number: str
    amount: float


# Customer endpoints

@app.post("/orders", status_code=201)
def create_order(order_req: OrderRequest):
    global next_order_id

    order = {
        "id": next_order_id,
        "drink": order_req.drink,
        "size": order_req.size,
        "milk": order_req.milk,
        "shots": order_req.shots,
        "status": "pending",
        "cost": calculate_cost(order_req.size, order_req.shots),
        "paid": False
    }
    orders[next_order_id] = order
    next_order_id += 1

    return order


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    return orders[order_id]


@app.put("/orders/{order_id}")
def update_order(order_id: int, update: OrderUpdate):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["status"] != "pending":
        raise HTTPException(status_code=409, detail="Order is already being prepared")

    if update.drink:
        order["drink"] = update.drink
    if update.size:
        order["size"] = update.size
    if update.milk:
        order["milk"] = update.milk
    if update.shots:
        order["shots"] = update.shots

    order["cost"] = calculate_cost(order["size"], order["shots"])

    return order


@app.put("/orders/{order_id}/payment", status_code=201)
def pay_order(order_id: int, payment: PaymentRequest):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["paid"]:
        return JSONResponse(status_code=200, content={"message": "Already paid", "order": order})

    if payment.amount < order["cost"]:
        raise HTTPException(status_code=400, detail=f"Insufficient amount. Need ${order['cost']:.2f}")

    order["paid"] = True
    order["card_last_four"] = payment.card_number[-4:]

    return order


@app.delete("/orders/{order_id}")
def cancel_order(order_id: int):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["status"] != "pending":
        raise HTTPException(status_code=409, detail="Cannot cancel - order is being prepared")

    if order["paid"]:
        raise HTTPException(status_code=409, detail="Cannot cancel - order is already paid")

    del orders[order_id]
    return {"message": "Order cancelled"}


# Barista endpoints

@app.get("/orders")
def get_all_orders(status: Optional[str] = None, paid: Optional[bool] = None):
    result = list(orders.values())

    if status:
        result = [o for o in result if o["status"] == status]
    if paid is not None:
        result = [o for o in result if o["paid"] == paid]

    return result


@app.put("/orders/{order_id}/status")
def update_status(order_id: int, status: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]
    valid_statuses = ["pending", "preparing", "ready", "delivered"]

    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    if status == "preparing" and not order["paid"]:
        raise HTTPException(status_code=409, detail="Cannot prepare - order not paid")

    order["status"] = status
    return order


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

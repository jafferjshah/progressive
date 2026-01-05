"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v7: HATEOAS - Hypermedia as the Engine of Application State
The response tells the client what actions are available next.
"""

from fastapi import FastAPI, HTTPException, Request
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


def get_order_links(order, base_url):
    """Generate hypermedia links based on order state"""
    links = []
    order_url = f"{base_url}/orders/{order['id']}"

    # self link is always available
    links.append({"rel": "self", "href": order_url, "method": "GET"})

    if order["status"] == "pending" and not order["paid"]:
        # can update, pay, or cancel
        links.append({"rel": "update", "href": order_url, "method": "PUT"})
        links.append({"rel": "payment", "href": f"{order_url}/payment", "method": "PUT"})
        links.append({"rel": "cancel", "href": order_url, "method": "DELETE"})

    elif order["status"] == "pending" and order["paid"]:
        # paid but not started - barista can start preparing
        links.append({"rel": "prepare", "href": f"{order_url}/status?status=preparing", "method": "PUT"})

    elif order["status"] == "preparing":
        # being made - can mark ready
        links.append({"rel": "ready", "href": f"{order_url}/status?status=ready", "method": "PUT"})

    elif order["status"] == "ready":
        # ready - can deliver
        links.append({"rel": "deliver", "href": f"{order_url}/status?status=delivered", "method": "PUT"})

    # delivered = no more actions

    return links


def order_with_links(order, base_url):
    """Return order with hypermedia links"""
    return {
        **order,
        "links": get_order_links(order, base_url)
    }


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
def create_order(order_req: OrderRequest, request: Request):
    global next_order_id
    base_url = str(request.base_url).rstrip("/")

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

    return order_with_links(order, base_url)


@app.get("/orders/{order_id}")
def get_order(order_id: int, request: Request):
    base_url = str(request.base_url).rstrip("/")

    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    return order_with_links(orders[order_id], base_url)


@app.put("/orders/{order_id}")
def update_order(order_id: int, update: OrderUpdate, request: Request):
    base_url = str(request.base_url).rstrip("/")

    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["status"] != "pending":
        raise HTTPException(status_code=409, detail="Order is already being prepared")

    if order["paid"]:
        raise HTTPException(status_code=409, detail="Cannot modify - order is already paid")

    if update.drink:
        order["drink"] = update.drink
    if update.size:
        order["size"] = update.size
    if update.milk:
        order["milk"] = update.milk
    if update.shots:
        order["shots"] = update.shots

    order["cost"] = calculate_cost(order["size"], order["shots"])

    return order_with_links(order, base_url)


@app.put("/orders/{order_id}/payment", status_code=201)
def pay_order(order_id: int, payment: PaymentRequest, request: Request):
    base_url = str(request.base_url).rstrip("/")

    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["paid"]:
        return JSONResponse(
            status_code=200,
            content=order_with_links(order, base_url)
        )

    if payment.amount < order["cost"]:
        raise HTTPException(status_code=400, detail=f"Insufficient amount. Need ${order['cost']:.2f}")

    order["paid"] = True
    order["card_last_four"] = payment.card_number[-4:]

    return order_with_links(order, base_url)


@app.delete("/orders/{order_id}")
def cancel_order(order_id: int, request: Request):
    base_url = str(request.base_url).rstrip("/")

    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["status"] != "pending":
        raise HTTPException(status_code=409, detail="Cannot cancel - order is being prepared")

    if order["paid"]:
        raise HTTPException(status_code=409, detail="Cannot cancel - order is already paid")

    del orders[order_id]

    # return link to create new order
    return {
        "message": "Order cancelled",
        "links": [{"rel": "create_order", "href": f"{base_url}/orders", "method": "POST"}]
    }


# Barista endpoints

@app.get("/orders")
def get_all_orders(request: Request, status: Optional[str] = None, paid: Optional[bool] = None):
    base_url = str(request.base_url).rstrip("/")
    result = list(orders.values())

    if status:
        result = [o for o in result if o["status"] == status]
    if paid is not None:
        result = [o for o in result if o["paid"] == paid]

    return [order_with_links(o, base_url) for o in result]


@app.put("/orders/{order_id}/status")
def update_status(order_id: int, status: str, request: Request):
    base_url = str(request.base_url).rstrip("/")

    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]
    valid_statuses = ["pending", "preparing", "ready", "delivered"]

    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    if status == "preparing" and not order["paid"]:
        raise HTTPException(status_code=409, detail="Cannot prepare - order not paid")

    order["status"] = status
    return order_with_links(order, base_url)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

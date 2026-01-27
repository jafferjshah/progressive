"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v14: Health Probe - liveness endpoint for monitoring

Run with:
  docker-compose up --build

Test health:
  curl http://localhost:8000/health
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import Order
from cache import cache_order, get_cached_order, invalidate_order, r as redis_client
from sqlalchemy import text

app = FastAPI()


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check if database and cache are reachable"""
    health = {"status": "healthy", "db": False, "cache": False}

    # check database
    try:
        db.execute(text("SELECT 1"))
        health["db"] = True
    except:
        health["status"] = "unhealthy"

    # check cache
    try:
        redis_client.ping()
        health["cache"] = True
    except:
        health["status"] = "unhealthy"

    return health

Base.metadata.create_all(bind=engine)


def calculate_cost(size, shots):
    base = {"small": 2.50, "medium": 3.00, "large": 3.50}
    return base.get(size, 3.00) + (shots - 1) * 0.50


def get_order_links(order_dict, base_url):
    links = []
    order_url = f"{base_url}/orders/{order_dict['id']}"

    links.append({"rel": "self", "href": order_url, "method": "GET"})

    if order_dict["status"] == "pending" and not order_dict["paid"]:
        links.append({"rel": "update", "href": order_url, "method": "PUT"})
        links.append({"rel": "payment", "href": f"{order_url}/payment", "method": "PUT"})
        links.append({"rel": "cancel", "href": order_url, "method": "DELETE"})

    elif order_dict["status"] == "pending" and order_dict["paid"]:
        links.append({"rel": "prepare", "href": f"{order_url}/status?status=preparing", "method": "PUT"})

    elif order_dict["status"] == "preparing":
        links.append({"rel": "ready", "href": f"{order_url}/status?status=ready", "method": "PUT"})

    elif order_dict["status"] == "ready":
        links.append({"rel": "deliver", "href": f"{order_url}/status?status=delivered", "method": "PUT"})

    return links


def order_with_links(order_dict, base_url):
    return {**order_dict, "links": get_order_links(order_dict, base_url)}


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


@app.post("/orders", status_code=201)
def create_order(order_req: OrderRequest, request: Request, db: Session = Depends(get_db)):
    base_url = str(request.base_url).rstrip("/")

    order = Order(
        drink=order_req.drink,
        size=order_req.size,
        milk=order_req.milk,
        shots=order_req.shots,
        status="pending",
        cost=calculate_cost(order_req.size, order_req.shots),
        paid=False
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    order_dict = order.to_dict()
    cache_order(order.id, order_dict)

    return order_with_links(order_dict, base_url)


@app.get("/orders/{order_id}")
def get_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    base_url = str(request.base_url).rstrip("/")

    # try cache first
    cached = get_cached_order(order_id)
    if cached:
        return order_with_links(cached, base_url)

    # cache miss - query database
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_dict = order.to_dict()
    cache_order(order_id, order_dict)

    return order_with_links(order_dict, base_url)


@app.put("/orders/{order_id}")
def update_order(order_id: int, update: OrderUpdate, request: Request, db: Session = Depends(get_db)):
    base_url = str(request.base_url).rstrip("/")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(status_code=409, detail="Order is already being prepared")

    if order.paid:
        raise HTTPException(status_code=409, detail="Cannot modify - order is already paid")

    if update.drink:
        order.drink = update.drink
    if update.size:
        order.size = update.size
    if update.milk:
        order.milk = update.milk
    if update.shots:
        order.shots = update.shots

    order.cost = calculate_cost(order.size, order.shots)
    db.commit()
    db.refresh(order)

    order_dict = order.to_dict()
    cache_order(order_id, order_dict)  # update cache

    return order_with_links(order_dict, base_url)


@app.put("/orders/{order_id}/payment", status_code=201)
def pay_order(order_id: int, payment: PaymentRequest, request: Request, db: Session = Depends(get_db)):
    base_url = str(request.base_url).rstrip("/")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.paid:
        return JSONResponse(status_code=200, content=order_with_links(order.to_dict(), base_url))

    if payment.amount < order.cost:
        raise HTTPException(status_code=400, detail=f"Insufficient amount. Need ${order.cost:.2f}")

    order.paid = True
    order.card_last_four = payment.card_number[-4:]
    db.commit()
    db.refresh(order)

    order_dict = order.to_dict()
    cache_order(order_id, order_dict)

    return order_with_links(order_dict, base_url)


@app.delete("/orders/{order_id}")
def cancel_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    base_url = str(request.base_url).rstrip("/")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(status_code=409, detail="Cannot cancel - order is being prepared")

    if order.paid:
        raise HTTPException(status_code=409, detail="Cannot cancel - order is already paid")

    db.delete(order)
    db.commit()
    invalidate_order(order_id)  # remove from cache

    return {
        "message": "Order cancelled",
        "links": [{"rel": "create_order", "href": f"{base_url}/orders", "method": "POST"}]
    }


@app.get("/orders")
def get_all_orders(request: Request, db: Session = Depends(get_db), status: Optional[str] = None, paid: Optional[bool] = None):
    base_url = str(request.base_url).rstrip("/")

    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)
    if paid is not None:
        query = query.filter(Order.paid == paid)

    orders = query.all()
    return [order_with_links(o.to_dict(), base_url) for o in orders]


@app.put("/orders/{order_id}/status")
def update_status(order_id: int, status: str, request: Request, db: Session = Depends(get_db)):
    base_url = str(request.base_url).rstrip("/")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    valid_statuses = ["pending", "preparing", "ready", "delivered"]

    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    if status == "preparing" and not order.paid:
        raise HTTPException(status_code=409, detail="Cannot prepare - order not paid")

    order.status = status
    db.commit()
    db.refresh(order)

    order_dict = order.to_dict()
    cache_order(order_id, order_dict)

    return order_with_links(order_dict, base_url)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v17: Bulkhead - isolate payment service calls

Run with:
  docker-compose up --build

Test bulkhead (max 3 concurrent payment calls):
  1. In browser, open http://localhost:8001/docs
  2. Fire 10 payment requests simultaneously with delay=5
  3. First 3 process, remaining 7 fail fast with 503
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import time
import os
import threading
import requests

from database import engine, get_db, Base

PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8001")


class Bulkhead:
    """Limits concurrent calls to a service"""

    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)

    def acquire(self) -> bool:
        """Try to acquire a slot, returns False if full"""
        return self.semaphore.acquire(blocking=False)

    def release(self):
        """Release a slot"""
        self.semaphore.release()


payment_bulkhead = Bulkhead(max_concurrent=3)


class CircuitBreaker:
    """Simple circuit breaker: closed -> open -> half-open -> closed"""

    def __init__(self, failure_threshold=3, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "closed"
        self.last_failure_time = None

    def can_execute(self):
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        if self.state == "half-open":
            return True
        return False

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"


db_circuit = CircuitBreaker()
from models import Order
from cache import cache_order, get_cached_order, invalidate_order, r as redis_client
from sqlalchemy import text

app = FastAPI()

# Rate limiting: 10 requests per minute per IP
RATE_LIMIT = 10
RATE_WINDOW = 60  # seconds


def check_rate_limit(client_ip: str) -> bool:
    """Returns True if request is allowed, False if rate limited"""
    key = f"rate:{client_ip}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, RATE_WINDOW)
    return count <= RATE_LIMIT


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Try again later."}
        )
    return await call_next(request)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check if database, cache, and payment service are reachable"""
    health = {"status": "healthy", "db": False, "cache": False, "payment": False, "circuit": db_circuit.state}

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

    # check payment service
    try:
        resp = requests.get(f"{PAYMENT_URL}/health", timeout=2)
        health["payment"] = resp.status_code == 200
    except:
        health["status"] = "unhealthy"

    return health


def require_db_circuit():
    """Check circuit breaker before database operations"""
    if not db_circuit.can_execute():
        raise HTTPException(status_code=503, detail="Service unavailable - circuit open")

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
    require_db_circuit()
    base_url = str(request.base_url).rstrip("/")

    try:
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
        db_circuit.record_success()
    except Exception as e:
        db_circuit.record_failure()
        raise HTTPException(status_code=503, detail="Database unavailable")

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
def pay_order(order_id: int, payment: PaymentRequest, request: Request, db: Session = Depends(get_db), delay: int = 0):
    base_url = str(request.base_url).rstrip("/")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.paid:
        return JSONResponse(status_code=200, content=order_with_links(order.to_dict(), base_url))

    if payment.amount < order.cost:
        raise HTTPException(status_code=400, detail=f"Insufficient amount. Need ${order.cost:.2f}")

    # bulkhead: limit concurrent payment calls
    if not payment_bulkhead.acquire():
        raise HTTPException(status_code=503, detail="Payment service busy - try again later")

    try:
        # call payment service
        resp = requests.post(
            f"{PAYMENT_URL}/pay?delay={delay}",
            json={"order_id": order_id, "amount": order.cost, "card_last_four": payment.card_number[-4:]},
            timeout=30
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Payment failed")
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Payment service unavailable")
    finally:
        payment_bulkhead.release()

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

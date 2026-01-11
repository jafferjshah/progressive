"""
Restbucks - A simple coffee ordering system
Based on: https://www.infoq.com/articles/webber-rest-workflow/

v9: SQLite with raw SQL - real database, see the queries
"""

import sqlite3
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

DB_FILE = "restbucks.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # return dicts instead of tuples
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drink TEXT NOT NULL,
            size TEXT NOT NULL,
            milk TEXT NOT NULL,
            shots INTEGER NOT NULL,
            status TEXT NOT NULL,
            cost REAL NOT NULL,
            paid INTEGER NOT NULL DEFAULT 0,
            card_last_four TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def row_to_order(row):
    """Convert database row to order dict"""
    return {
        "id": row["id"],
        "drink": row["drink"],
        "size": row["size"],
        "milk": row["milk"],
        "shots": row["shots"],
        "status": row["status"],
        "cost": row["cost"],
        "paid": bool(row["paid"]),
        "card_last_four": row["card_last_four"]
    }


def calculate_cost(size, shots):
    base = {"small": 2.50, "medium": 3.00, "large": 3.50}
    return base.get(size, 3.00) + (shots - 1) * 0.50


def get_order_links(order, base_url):
    links = []
    order_url = f"{base_url}/orders/{order['id']}"

    links.append({"rel": "self", "href": order_url, "method": "GET"})

    if order["status"] == "pending" and not order["paid"]:
        links.append({"rel": "update", "href": order_url, "method": "PUT"})
        links.append({"rel": "payment", "href": f"{order_url}/payment", "method": "PUT"})
        links.append({"rel": "cancel", "href": order_url, "method": "DELETE"})

    elif order["status"] == "pending" and order["paid"]:
        links.append({"rel": "prepare", "href": f"{order_url}/status?status=preparing", "method": "PUT"})

    elif order["status"] == "preparing":
        links.append({"rel": "ready", "href": f"{order_url}/status?status=ready", "method": "PUT"})

    elif order["status"] == "ready":
        links.append({"rel": "deliver", "href": f"{order_url}/status?status=delivered", "method": "PUT"})

    return links


def order_with_links(order, base_url):
    return {**order, "links": get_order_links(order, base_url)}


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
def create_order(order_req: OrderRequest, request: Request):
    base_url = str(request.base_url).rstrip("/")
    cost = calculate_cost(order_req.size, order_req.shots)

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO orders (drink, size, milk, shots, status, cost, paid) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (order_req.drink, order_req.size, order_req.milk, order_req.shots, "pending", cost, 0)
    )
    order_id = cursor.lastrowid
    conn.commit()

    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()

    return order_with_links(row_to_order(row), base_url)


@app.get("/orders/{order_id}")
def get_order(order_id: int, request: Request):
    base_url = str(request.base_url).rstrip("/")

    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Order not found")

    return order_with_links(row_to_order(row), base_url)


@app.put("/orders/{order_id}")
def update_order(order_id: int, update: OrderUpdate, request: Request):
    base_url = str(request.base_url).rstrip("/")

    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")

    order = row_to_order(row)

    if order["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=409, detail="Order is already being prepared")

    if order["paid"]:
        conn.close()
        raise HTTPException(status_code=409, detail="Cannot modify - order is already paid")

    # update fields
    drink = update.drink or order["drink"]
    size = update.size or order["size"]
    milk = update.milk or order["milk"]
    shots = update.shots or order["shots"]
    cost = calculate_cost(size, shots)

    conn.execute(
        "UPDATE orders SET drink=?, size=?, milk=?, shots=?, cost=? WHERE id=?",
        (drink, size, milk, shots, cost, order_id)
    )
    conn.commit()

    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()

    return order_with_links(row_to_order(row), base_url)


@app.put("/orders/{order_id}/payment", status_code=201)
def pay_order(order_id: int, payment: PaymentRequest, request: Request):
    base_url = str(request.base_url).rstrip("/")

    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")

    order = row_to_order(row)

    if order["paid"]:
        conn.close()
        return JSONResponse(status_code=200, content=order_with_links(order, base_url))

    if payment.amount < order["cost"]:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Insufficient amount. Need ${order['cost']:.2f}")

    conn.execute(
        "UPDATE orders SET paid=1, card_last_four=? WHERE id=?",
        (payment.card_number[-4:], order_id)
    )
    conn.commit()

    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()

    return order_with_links(row_to_order(row), base_url)


@app.delete("/orders/{order_id}")
def cancel_order(order_id: int, request: Request):
    base_url = str(request.base_url).rstrip("/")

    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")

    order = row_to_order(row)

    if order["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=409, detail="Cannot cancel - order is being prepared")

    if order["paid"]:
        conn.close()
        raise HTTPException(status_code=409, detail="Cannot cancel - order is already paid")

    conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    return {
        "message": "Order cancelled",
        "links": [{"rel": "create_order", "href": f"{base_url}/orders", "method": "POST"}]
    }


@app.get("/orders")
def get_all_orders(request: Request, status: Optional[str] = None, paid: Optional[bool] = None):
    base_url = str(request.base_url).rstrip("/")

    conn = get_db()

    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if paid is not None:
        query += " AND paid = ?"
        params.append(1 if paid else 0)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [order_with_links(row_to_order(r), base_url) for r in rows]


@app.put("/orders/{order_id}/status")
def update_status(order_id: int, status: str, request: Request):
    base_url = str(request.base_url).rstrip("/")

    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")

    order = row_to_order(row)
    valid_statuses = ["pending", "preparing", "ready", "delivered"]

    if status not in valid_statuses:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    if status == "preparing" and not order["paid"]:
        conn.close()
        raise HTTPException(status_code=409, detail="Cannot prepare - order not paid")

    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()

    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()

    return order_with_links(row_to_order(row), base_url)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

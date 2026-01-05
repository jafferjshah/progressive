"""
Test client for the HATEOAS REST API
Run the server first: python app.py

Notice how this client follows the links from responses
instead of hardcoding URLs.
"""

import requests

BASE_URL = "http://localhost:8000"


def find_link(links, rel):
    """Find a link by its relation"""
    for link in links:
        if link["rel"] == rel:
            return link
    return None


def follow_link(link, json_data=None):
    """Execute a link"""
    method = link["method"].lower()
    url = link["href"]

    if method == "get":
        return requests.get(url)
    elif method == "put":
        return requests.put(url, json=json_data)
    elif method == "post":
        return requests.post(url, json=json_data)
    elif method == "delete":
        return requests.delete(url)


def main():
    print("=== Restbucks Coffee Shop (HATEOAS) ===\n")

    # Customer places an order
    print("-- Customer: placing order --")
    resp = requests.post(f"{BASE_URL}/orders", json={
        "drink": "latte",
        "size": "large",
        "milk": "semi-skimmed",
        "shots": 2
    })
    print(f"Status: {resp.status_code}")
    order = resp.json()
    print(f"Order: {order['drink']}, {order['size']}, ${order['cost']}")
    print(f"Available actions: {[l['rel'] for l in order['links']]}")

    # Follow the update link
    print("\n-- Customer: adding an extra shot (following 'update' link) --")
    update_link = find_link(order["links"], "update")
    resp = follow_link(update_link, {"shots": 3})
    print(f"Status: {resp.status_code}")
    order = resp.json()
    print(f"Updated cost: ${order['cost']}")
    print(f"Available actions: {[l['rel'] for l in order['links']]}")

    # Follow the payment link
    print("\n-- Customer: paying (following 'payment' link) --")
    payment_link = find_link(order["links"], "payment")
    resp = follow_link(payment_link, {
        "card_number": "1234567890123456",
        "amount": 5.00
    })
    print(f"Status: {resp.status_code}")
    order = resp.json()
    print(f"Paid: {order['paid']}")
    print(f"Available actions: {[l['rel'] for l in order['links']]}")

    # Barista checks orders
    print("\n-- Barista: checking pending paid orders --")
    resp = requests.get(f"{BASE_URL}/orders", params={"status": "pending", "paid": True})
    print(f"Status: {resp.status_code}")
    pending_orders = resp.json()
    print(f"Found {len(pending_orders)} order(s)")

    # Follow the prepare link from the first pending order
    print("\n-- Barista: making the drink (following 'prepare' link) --")
    order = pending_orders[0]
    prepare_link = find_link(order["links"], "prepare")
    resp = follow_link(prepare_link)
    print(f"Status: {resp.status_code}")
    order = resp.json()
    print(f"Order status: {order['status']}")
    print(f"Available actions: {[l['rel'] for l in order['links']]}")

    # Customer tries to modify - no update link available!
    print("\n-- Customer tries to modify (no 'update' link available!) --")
    update_link = find_link(order["links"], "update")
    if update_link:
        resp = follow_link(update_link, {"shots": 1})
        print(f"Status: {resp.status_code}")
    else:
        print("No update link - modification not allowed in this state")

    # Follow the ready link
    print("\n-- Barista: order done (following 'ready' link) --")
    ready_link = find_link(order["links"], "ready")
    resp = follow_link(ready_link)
    print(f"Status: {resp.status_code}")
    order = resp.json()
    print(f"Order status: {order['status']}")
    print(f"Available actions: {[l['rel'] for l in order['links']]}")

    # Follow the deliver link
    print("\n-- Customer: picking up (following 'deliver' link) --")
    deliver_link = find_link(order["links"], "deliver")
    resp = follow_link(deliver_link)
    print(f"Status: {resp.status_code}")
    order = resp.json()
    print(f"Order status: {order['status']}")
    print(f"Available actions: {[l['rel'] for l in order['links']]}")

    print("\n-- Order complete! No more actions available. --")


if __name__ == "__main__":
    main()

"""
Test client for the proper REST API
Run the server first: python app.py
"""

import requests

BASE_URL = "http://localhost:8000"


def main():
    print("=== Restbucks Coffee Shop (Proper REST API) ===\n")

    # Customer places an order
    print("-- Customer: placing order --")
    resp = requests.post(f"{BASE_URL}/orders", json={
        "drink": "latte",
        "size": "large",
        "milk": "semi-skimmed",
        "shots": 2
    })
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    order_id = resp.json()["id"]

    print("\n-- Customer: adding an extra shot --")
    resp = requests.put(f"{BASE_URL}/orders/{order_id}", json={
        "shots": 3
    })
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")

    print("\n-- Customer: paying --")
    resp = requests.put(f"{BASE_URL}/orders/{order_id}/payment", json={
        "card_number": "1234567890123456",
        "amount": 5.00
    })
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")

    print("\n-- Barista: checking pending paid orders --")
    resp = requests.get(f"{BASE_URL}/orders", params={"status": "pending", "paid": True})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")

    print("\n-- Barista: making the drink --")
    resp = requests.put(f"{BASE_URL}/orders/{order_id}/status", params={"status": "preparing"})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")

    print("\n-- Customer tries to modify (too late!) --")
    resp = requests.put(f"{BASE_URL}/orders/{order_id}", json={
        "shots": 1
    })
    print(f"Status: {resp.status_code}")  # Should be 409 Conflict
    print(f"Response: {resp.json()}")

    print("\n-- Barista: order done --")
    resp = requests.put(f"{BASE_URL}/orders/{order_id}/status", params={"status": "ready"})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")

    print("\n-- Customer: picking up --")
    resp = requests.put(f"{BASE_URL}/orders/{order_id}/status", params={"status": "delivered"})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")

    print("\n-- Final order state --")
    resp = requests.get(f"{BASE_URL}/orders/{order_id}")
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")


if __name__ == "__main__":
    main()

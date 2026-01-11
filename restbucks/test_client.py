"""
Test client for the basic REST API
Run the server first: python app.py
"""

import requests

BASE_URL = "http://localhost:8000"


def main():
    print("=== Restbucks Coffee Shop (REST-ish API) ===\n")

    # Customer places an order
    print("-- Customer: placing order --")
    resp = requests.post(f"{BASE_URL}/orders", params={
        "drink": "latte",
        "size": "large",
        "milk": "semi-skimmed",
        "shots": 2
    })
    data = resp.json()
    print(f"Response: {data}")
    order_id = data["order"]["id"]

    print("\n-- Customer: adding an extra shot --")
    resp = requests.post(f"{BASE_URL}/orders/{order_id}/update", params={
        "shots": 3
    })
    print(f"Response: {resp.json()}")

    print("\n-- Customer: paying --")
    resp = requests.post(f"{BASE_URL}/orders/{order_id}/payment", params={
        "card_number": "1234567890123456",
        "amount": 5.00
    })
    print(f"Response: {resp.json()}")

    print("\n-- Barista: checking orders --")
    resp = requests.post(f"{BASE_URL}/orders/pending")
    print(f"Response: {resp.json()}")

    print("\n-- Barista: making the drink --")
    resp = requests.post(f"{BASE_URL}/orders/{order_id}/prepare")
    print(f"Response: {resp.json()}")

    print("\n-- Customer tries to modify (too late!) --")
    resp = requests.post(f"{BASE_URL}/orders/{order_id}/update", params={
        "shots": 1
    })
    print(f"Response: {resp.json()}")

    print("\n-- Barista: order done --")
    resp = requests.post(f"{BASE_URL}/orders/{order_id}/ready")
    print(f"Response: {resp.json()}")

    print("\n-- Customer: picking up --")
    resp = requests.post(f"{BASE_URL}/orders/{order_id}/deliver")
    print(f"Response: {resp.json()}")


if __name__ == "__main__":
    main()

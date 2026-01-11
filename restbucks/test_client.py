"""
Test client for the naive web API
Run the server first: python app.py
"""

import requests

BASE_URL = "http://localhost:8000"


def main():
    print("=== Restbucks Coffee Shop (Web API) ===\n")

    # Customer places an order
    print("-- Customer: placing order --")
    resp = requests.post(f"{BASE_URL}/placeOrder", params={
        "drink": "latte",
        "size": "large",
        "milk": "semi-skimmed",
        "shots": 2
    })
    data = resp.json()
    print(f"Response: {data}")
    order_id = data["order"]["id"]

    print("\n-- Customer: adding an extra shot --")
    resp = requests.post(f"{BASE_URL}/updateOrder", params={
        "order_id": order_id,
        "shots": 3
    })
    print(f"Response: {resp.json()}")

    print("\n-- Customer: paying --")
    resp = requests.post(f"{BASE_URL}/payOrder", params={
        "order_id": order_id,
        "card_number": "1234567890123456",
        "amount": 5.00
    })
    print(f"Response: {resp.json()}")

    print("\n-- Barista: checking orders --")
    resp = requests.post(f"{BASE_URL}/getPendingOrders")
    print(f"Response: {resp.json()}")

    print("\n-- Barista: making the drink --")
    resp = requests.post(f"{BASE_URL}/startPreparing", params={"order_id": order_id})
    print(f"Response: {resp.json()}")

    print("\n-- Customer tries to modify (too late!) --")
    resp = requests.post(f"{BASE_URL}/updateOrder", params={
        "order_id": order_id,
        "shots": 1
    })
    print(f"Response: {resp.json()}")

    print("\n-- Barista: order done --")
    resp = requests.post(f"{BASE_URL}/completeOrder", params={"order_id": order_id})
    print(f"Response: {resp.json()}")

    print("\n-- Customer: picking up --")
    resp = requests.post(f"{BASE_URL}/deliverOrder", params={"order_id": order_id})
    print(f"Response: {resp.json()}")


if __name__ == "__main__":
    main()

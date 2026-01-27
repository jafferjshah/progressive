"""
Payment Service - simulates payment processing

Configurable delay for testing bulkhead pattern.

Usage:
  GET  /health         - health check
  POST /pay            - process payment (with optional delay)

Query param:
  ?delay=2             - add 2 second delay (for testing)
"""

from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI()


class PaymentRequest(BaseModel):
    order_id: int
    amount: float
    card_last_four: str


@app.get("/health")
def health():
    return {"status": "healthy", "service": "payment"}


@app.post("/pay")
def process_payment(payment: PaymentRequest, delay: int = 0):
    if delay > 0:
        time.sleep(delay)

    # simulate payment processing
    return {
        "status": "approved",
        "order_id": payment.order_id,
        "amount": payment.amount,
        "transaction_id": f"TXN-{payment.order_id}-{int(time.time())}"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

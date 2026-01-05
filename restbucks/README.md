# Restbucks - Progressive REST Tutorial

A progressive codebase for learning REST concepts, based on Jim Webber's classic article:
https://www.infoq.com/articles/webber-rest-workflow/

## The Use Case

Restbucks is a coffee ordering system with two actors:
- **Customer**: places order, modifies it, pays for it, picks it up
- **Barista**: sees pending orders, prepares them, marks them ready

## Setup

```bash
conda env create -f environment.yml
conda activate restbucks
```

## Versions

Work through these versions in order. Each builds on the previous.

### v1_monolith_basic
Simple Python script with functions and global state. Run it:
```bash
python v1_monolith_basic/restbucks.py
```

### v2_monolith_oop
Same logic, now with classes (Order, Payment, Shop). Run it:
```bash
python v2_monolith_oop/restbucks.py
```

### v3_monolith_layered
Separated into layers: models, repository, services. Run it:
```bash
cd v3_monolith_layered
python main.py
```

### v4_web_naive
First web version using FastAPI. But it's naive:
- All endpoints use POST
- Always returns 200
- Success/error indicated in response body

```bash
# Terminal 1: start server
python v4_web_naive/app.py

# Terminal 2: run test client
python v4_web_naive/test_client.py
```

### v5_rest_basic
Resource-oriented URLs (`/orders`, `/orders/{id}/payment`), but still all POST.
```bash
python v5_rest_basic/app.py
# then
python v5_rest_basic/test_client.py
```

### v6_rest_proper
Correct HTTP methods and status codes:
- POST to create (201 Created)
- GET to retrieve (200 OK)
- PUT to update (200 OK)
- DELETE to cancel (200 OK)
- 404 Not Found, 409 Conflict, 400 Bad Request

```bash
python v6_rest_proper/app.py
# then
python v6_rest_proper/test_client.py
```

### v7_rest_hateoas
Full REST with hypermedia (HATEOAS). Responses include links telling the client what actions are available:

```json
{
  "id": 1,
  "drink": "latte",
  "status": "pending",
  "links": [
    {"rel": "self", "href": "/orders/1", "method": "GET"},
    {"rel": "update", "href": "/orders/1", "method": "PUT"},
    {"rel": "payment", "href": "/orders/1/payment", "method": "PUT"},
    {"rel": "cancel", "href": "/orders/1", "method": "DELETE"}
  ]
}
```

The client follows links instead of hardcoding URLs.

```bash
python v7_rest_hateoas/app.py
# then
python v7_rest_hateoas/test_client.py
```

## What You Learn

| Version | Concept |
|---------|---------|
| v1 → v2 | Why OOP? Encapsulation, cleaner code |
| v2 → v3 | Why layers? Separation of concerns |
| v3 → v4 | Moving to web (HTTP) |
| v4 → v5 | Resource-oriented thinking |
| v5 → v6 | HTTP semantics matter (methods, status codes) |
| v6 → v7 | HATEOAS - REST as a state machine |

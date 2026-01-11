# Restbucks - Progressive REST Tutorial

Learn REST and backend concepts by following the evolution of a coffee ordering system.

Based on Jim Webber's article: https://www.infoq.com/articles/webber-rest-workflow/

## Setup

```bash
conda env create -f environment.yml
conda activate restbucks
```

## How to Use

Each version is tagged. Start from v1 and progress through v13:

```bash
# Start with v1
git checkout v1
python restbucks.py

# See what changed in v2
git diff v1 v2

# Move to v2
git checkout v2
python restbucks.py

# Continue through all versions...
```

## Versions

| Tag | What Changed |
|-----|--------------|
| v1 | Basic monolith - functions and global state |
| v2 | OOP refactor - Order, Payment, Shop classes |
| v3 | Layered architecture - models, repository, services |
| v4 | Naive web API - all POST, always 200, status in body |
| v5 | Basic REST - resource URLs, but still all POST |
| v6 | Proper REST - correct HTTP methods and status codes |
| v7 | HATEOAS - hypermedia links guide client through workflow |
| v8 | JSON file persistence - data survives restarts |
| v9 | SQLite with raw SQL - see the queries directly |
| v10 | SQLAlchemy ORM - cleaner database code |
| v11 | PostgreSQL - real database server |
| v12 | Redis caching - cache orders for faster reads |
| v13 | Docker - containerized deployment |

## Running Different Versions

**v1-v3 (CLI):**
```bash
python restbucks.py   # or main.py for v3
```

**v4-v12 (Web API):**
```bash
# Terminal 1: start server
python app.py

# Terminal 2: run test client
python test_client.py
```

**v13 (Docker):**
```bash
docker-compose up --build
# Then run test_client.py
```

## The Use Case

Restbucks is a coffee ordering system:

**Customer workflow:**
- Place order
- Modify order (if not yet paid/prepared)
- Pay for order
- Pick up drink

**Barista workflow:**
- Check pending orders
- Prepare order
- Mark as ready
- Deliver to customer

## What You Learn

| Transition | Concept |
|------------|---------|
| v1 → v2 | Why OOP? Encapsulation |
| v2 → v3 | Why layers? Separation of concerns |
| v3 → v4 | Moving to web (HTTP) |
| v4 → v5 | Resource-oriented URLs |
| v5 → v6 | HTTP methods and status codes matter |
| v6 → v7 | HATEOAS - REST as a state machine |
| v7 → v8 | Why persist? Data survives restarts |
| v8 → v9 | Why databases? SQL queries, better concurrency |
| v9 → v10 | Why ORM? Less boilerplate, cleaner code |
| v10 → v11 | Why real database? Scalability, features |
| v11 → v12 | Why cache? Faster reads, reduced DB load |
| v12 → v13 | Why containers? Reproducible deployments |

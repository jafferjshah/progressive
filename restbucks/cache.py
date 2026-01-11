"""
Redis cache for orders
"""

import os
import json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

r = redis.from_url(REDIS_URL)

CACHE_TTL = 300  # 5 minutes


def cache_order(order_id, order_dict):
    """Store order in cache"""
    key = f"order:{order_id}"
    r.setex(key, CACHE_TTL, json.dumps(order_dict))


def get_cached_order(order_id):
    """Get order from cache, returns None if not found"""
    key = f"order:{order_id}"
    data = r.get(key)
    if data:
        return json.loads(data)
    return None


def invalidate_order(order_id):
    """Remove order from cache"""
    key = f"order:{order_id}"
    r.delete(key)

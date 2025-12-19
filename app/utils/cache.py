# app/utils/cache.py
import redis
import json
import hashlib
from functools import wraps
from typing import Callable, Any, Optional
from app.config.settings import get_settings

settings = get_settings()

# Initialize Redis client if enabled
redis_client = None
if settings.REDIS_ENABLED and settings.REDIS_URL:
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as e:
        print(f"Redis connection failed: {e}")


def get_cache_key(func_name: str, *args, **kwargs) -> str:
    """Generate cache key from function name and arguments."""
    key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def cache_result(expiration: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)
            
            cache_key = f"{key_prefix}:{get_cache_key(func.__name__, *args, **kwargs)}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result, default=str))
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not redis_client:
                return func(*args, **kwargs)
            
            cache_key = f"{key_prefix}:{get_cache_key(func.__name__, *args, **kwargs)}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result, default=str))
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern."""
    if not redis_client:
        return
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        print(f"Cache invalidation failed: {e}")


# app/utils/cache.py

import hashlib
import json
import time
from functools import wraps
from datetime import datetime

class CacheManager:
    """Manage caching for performance optimization"""
    
    def __init__(self, redis_url=None):
        self.redis_client = None
        # Local LRU cache as fallback
        self.local_cache = {}  # Dict[str, tuple[Any, float]]
        self.cache_ttl = 300  # 5 minutes default
        self.max_local_items = 100
        self.hits = 0
        self.misses = 0
    
    def get(self, key):
        """Get value from cache"""
        if key in self.local_cache:
            value, expiry = self.local_cache[key]
            if time.time() < expiry:
                self.hits += 1
                return value
            else:
                del self.local_cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache"""
        ttl = ttl or self.cache_ttl
        expiry = time.time() + ttl
        
        # Store in local cache
        self.local_cache[key] = (value, expiry)
        
        # Maintain local cache size
        if len(self.local_cache) > self.max_local_items:
            # Find and remove oldest item
            oldest_key = None
            oldest_time = float('inf')
            for k, (_, exp) in self.local_cache.items():
                if exp < oldest_time:
                    oldest_time = exp
                    oldest_key = k
            if oldest_key:
                del self.local_cache[oldest_key]
    
    def invalidate(self, key):
        """Invalidate cache entry"""
        if key in self.local_cache:
            del self.local_cache[key]
    
    def get_cache_key(self, *args, **kwargs):
        """Generate cache key from arguments"""
        key_data = {
            'args': [str(arg) for arg in args],
            'kwargs': {k: str(v) for k, v in kwargs.items()}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def clear(self):
        """Clear all cache"""
        self.local_cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total': total,
            'hit_rate': f"{hit_rate:.1f}%",
            'local_cache_size': len(self.local_cache)
        }


def cached(ttl=300, key_prefix=''):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Optional prefix for cache keys
    """
    def decorator(func):
        cache_manager = CacheManager()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            base_key = cache_manager.get_cache_key(func.__name__, *args, **kwargs)
            cache_key = f"{key_prefix}:{base_key}" if key_prefix else base_key
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
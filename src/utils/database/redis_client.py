"""Redis client and caching infrastructure."""

import json
from typing import Optional, Any, Dict, Union
import redis.asyncio as redis
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis connection manager with caching utilities."""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._connection_url = settings.redis_url
        self._default_ttl = settings.cache_ttl_seconds
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._redis is not None:
            logger.warning("Redis client already initialized")
            return
            
        try:
            self._redis = redis.from_url(
                self._connection_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair with optional TTL."""
        if not self._redis:
            await self.initialize()
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            ttl = ttl or self._default_ttl
            return await self._redis.set(key, serialized_value, ex=ttl)
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        if not self._redis:
            await self.initialize()
        
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        if not self._redis:
            await self.initialize()
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._redis:
            await self.initialize()
        
        try:
            return bool(await self._redis.exists(key))
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False
    
    async def set_hash(self, key: str, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set a hash with multiple fields."""
        if not self._redis:
            await self.initialize()
        
        try:
            # Serialize complex values in the hash
            serialized_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[field] = json.dumps(value)
                else:
                    serialized_mapping[field] = str(value)
            
            await self._redis.hmset(key, serialized_mapping)
            if ttl:
                await self._redis.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set hash {key}: {e}")
            return False
    
    async def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get all fields of a hash."""
        if not self._redis:
            await self.initialize()
        
        try:
            hash_data = await self._redis.hgetall(key)
            if not hash_data:
                return None
            
            # Deserialize values
            result = {}
            for field, value in hash_data.items():
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = value
            return result
        except Exception as e:
            logger.error(f"Failed to get hash {key}: {e}")
            return None
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value."""
        if not self._redis:
            await self.initialize()
        
        try:
            return await self._redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment key {key}: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            if not self._redis:
                await self.initialize()
            await self._redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global client instance
redis_client = RedisClient()
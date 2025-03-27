from fastapi import Request, Response, HTTPException, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Callable, Optional, Tuple
from app.models.api_key import ApiKey
from loguru import logger
import redis
import os
import time


# Initialize Redis connection for rate limiting
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


async def rate_limit_middleware(request: Request, api_key: str, api_key_obj: ApiKey):
    """
    Rate limit middleware for API requests
    Uses a sliding window algorithm with Redis
    """
    if not api_key_obj:
        return
    
    # Get rate limit for this API key
    rate_limit = api_key_obj.rate_limit
    
    # Create a unique key for this API key in Redis
    key = f"rate_limit:{api_key}"
    
    # Get current timestamp
    current_time = int(time.time())
    
    # Clean up old requests (older than 60 seconds)
    redis_client.zremrangebyscore(key, 0, current_time - 60)
    
    # Add current request to the sorted set with score as timestamp
    redis_client.zadd(key, {str(current_time): current_time})
    
    # Set expiration for the key (to automatically clean up)
    redis_client.expire(key, 120)  # 2 minutes expiration
    
    # Count the number of requests in the last minute
    request_count = redis_client.zcount(key, current_time - 60, current_time)
    
    if request_count > rate_limit:
        logger.warning(f"Rate limit exceeded for API key: {api_key} (name: {api_key_obj.name})")
        raise HTTPException(
            status_code=429, 
            detail="Too many requests. Rate limit exceeded."
        ) 
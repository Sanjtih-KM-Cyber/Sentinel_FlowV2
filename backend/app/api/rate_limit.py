from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.redis import redis_client
import time

_memory_store = {}

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"

def rate_limit_login(request: Request, username: str):
    ip = get_client_ip(request)
    limit = settings.LOGIN_RATE_LIMIT_PER_MINUTE
    
    # We will track both IP and username
    keys = [f"ratelimit:login:ip:{ip}", f"ratelimit:login:user:{username}"]
    
    now = int(time.time())
    window = 60
    
    for key in keys:
        if redis_client:
            pipe = redis_client.pipeline()
            pipe.zadd(key, {str(now): now})
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.expire(key, window)
            results = pipe.execute()
            count = results[2]
            
            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts."
                )
        else:
            # Memory fallback
            if key not in _memory_store:
                _memory_store[key] = []
            
            # Clean up old
            _memory_store[key] = [t for t in _memory_store[key] if t > now - window]
            _memory_store[key].append(now)
            
            if len(_memory_store[key]) > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts."
                )

import redis
from app.core.config import settings

redis_client = None

if settings.REDIS_URL:
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        pass

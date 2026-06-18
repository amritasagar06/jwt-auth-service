import redis
from app.config import settings

# Connect to Redis using the URL in config.py
# decode_responses=True ensures we work with strings, not byte-data
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def blacklist_token(token: str, expire_seconds: int):
    """
    Saves a token to Redis. 
    It will automatically disappear after expire_seconds.
    """
    redis_client.setex(f"blacklist:{token}", expire_seconds, "true")

def is_token_blacklisted(token: str) -> bool:
    """Checks if the token has been banned."""
    return redis_client.exists(f"blacklist:{token}") > 0
from redis import Redis

_redis_conn = None

def get_redis_connection():
    global _redis_conn
    if not _redis_conn:
        from app.env import REDIS_URL
        _redis_conn = Redis(REDIS_URL)
    return _redis_conn

from redis import Redis

_redis_conn = None

def get_redis_connection():
    global _redis_conn
    if not _redis_conn:
        from app.env import REDIS_HOST, REDIS_PORT
        _redis_conn = Redis(REDIS_HOST, REDIS_PORT)
    return _redis_conn

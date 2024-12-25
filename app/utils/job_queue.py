_rq_queue = None

def get_job_queue():
    global _rq_queue
    if _rq_queue is None:
        from rq import Queue
        from app.utils.redis import get_redis_connection
        _rq_queue = Queue(connection=get_redis_connection())
    
    return _rq_queue

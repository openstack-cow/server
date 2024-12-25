_rq_queue = None

def get_job_queue():
    global _rq_queue
    if _rq_queue is None:
        from rq import Queue
        from app.utils.redis import get_redis_connection
        _rq_queue = Queue(connection=get_redis_connection(), default_timeout=3600)
    
    return _rq_queue

# class FakeJobQueue:
#     """A fake job queue that executes jobs immediately"""
#     def __init__(self):
#         self.jobs = []

#     def enqueue(self, job, *args, **kwargs):
#         job(*args, **kwargs)

# def get_job_queue():
#     return FakeJobQueue()

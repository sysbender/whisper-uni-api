from rq import Worker
from redis import Redis
from worker.config import Config
import logging

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

def start_worker():
    """Start RQ worker listening for jobs."""
    
    redis_conn = Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT
    )
    
    worker = Worker(['default'], connection=redis_conn, name=Config.WORKER_NAME)
    logger.info(f"Worker '{Config.WORKER_NAME}' started, listening for jobs...")
    worker.work()

if __name__ == '__main__':
    start_worker()


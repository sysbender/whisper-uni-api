import os

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    WORKER_NAME = os.getenv("WORKER_NAME", "default")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


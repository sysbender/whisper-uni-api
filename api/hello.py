import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads")

print(REDIS_HOST , UPLOAD_DIR)
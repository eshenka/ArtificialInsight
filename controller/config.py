import os
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PIPELINE_QUEUE = "pipeline_creation_queue"
REDIS_JOB_STATUS_PREFIX = "job_status:"

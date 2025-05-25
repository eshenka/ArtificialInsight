import os
from dotenv import load_dotenv

load_dotenv()

CONTROLLER_ADDR = os.getenv("CONTROLLER_ADDR", "localhost:50051")
GATEWAY_HTTP_PORT = int(os.getenv("GATEWAY_HTTP_PORT", "8000"))

# Add timeout configuration (in seconds)
ANSWER_TIMEOUT = int(os.getenv("ANSWER_TIMEOUT", "90"))  # Increased from 30 seconds
PIPELINE_TIMEOUT = int(os.getenv("PIPELINE_TIMEOUT", "1800"))  # Increased from 60 to 30 minutes

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PIPELINE_QUEUE = "pipeline_creation_queue"
REDIS_JOB_STATUS_PREFIX = "job_status:"

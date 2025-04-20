import os
from dotenv import load_dotenv

load_dotenv()

CONTROLLER_ADDR = os.getenv("CONTROLLER_ADDR", "localhost:50051")
GATEWAY_HTTP_PORT = int(os.getenv("GATEWAY_HTTP_PORT", "8000"))

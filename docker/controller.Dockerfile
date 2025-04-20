# ArtificialInsight Controller Service
#
# Configuration options:
# - CONTROLLER_PORT: Port on which the controller service listens (default: 50050)
# - CONTROLLER_HOST: Host interface to bind (default: '[::]', all interfaces)
# - USERDB_SERVICE: Address of the user database service (default: localhost:50051)
# - VECTORDB_SERVICE: Address of the vector database service (default: localhost:50052)
# - SCRAPING_SERVICE: Address of the scraping service (default: localhost:50053)
# - LLM_SERVICE: Address of the LLM service (default: localhost:50054)
# - MAX_WORKERS: Maximum number of worker threads (default: 10)
# - LOG_LEVEL: Logging level (default: INFO)
#
# Example usage:
# docker run -p 50050:50050 \
#   -e USERDB_SERVICE=userdb:50051 \
#   -e VECTORDB_SERVICE=vectordb:50052 \
#   -e SCRAPING_SERVICE=scraper:50053 \
#   -e LLM_SERVICE=llm:50054 \
#   artificialinsight/controller

FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY controller/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy controller code
COPY controller/ ./controller/

# Copy proto files
COPY proto/ ./proto/

# Install dev dependencies for generating protobuf files
RUN pip install --no-cache-dir grpcio-tools

# Generate Python code from .proto files
RUN python -m grpc_tools.protoc \
    --python_out=. \
    --grpc_python_out=. \
    --proto_path=./proto \
    ./proto/*.proto

# Set environment variables with default values
ENV CONTROLLER_PORT=50050 \
    CONTROLLER_HOST="[::]" \
    USERDB_SERVICE="localhost:50051" \
    VECTORDB_SERVICE="localhost:50052" \
    SCRAPING_SERVICE="localhost:50053" \
    LLM_SERVICE="localhost:50054" \
    MAX_WORKERS=10 \
    LOG_LEVEL="INFO"

# Expose the port
EXPOSE 50050

# Run the controller service
CMD ["python", "-m", "controller.server"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('localhost', int(os.environ.get('CONTROLLER_PORT', 50050)))); s.close()" || exit 1

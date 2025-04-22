FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY vectorDB/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install specific dependencies
RUN pip install --no-cache-dir pymilvus sentence-transformers grpcio grpcio-tools requests

# Copy proto files and generate Python code
COPY proto/ /app/proto/
RUN mkdir -p /app/vectorDB
RUN python -m grpc_tools.protoc -I/app/proto --python_out=/app/vectorDB --grpc_python_out=/app/vectorDB /app/proto/vectordb.proto /app/proto/common.proto

# Copy the service code
COPY vectorDB/ /app/vectorDB/

# Configuration options as environment variables
ENV MILVUS_HOST="localhost" \
    MILVUS_PORT=19530 \
    SERVICE_HOST="0.0.0.0" \
    SERVICE_PORT=50051 \
    LOG_LEVEL="INFO" \
    OLLAMA_HOST="" \
    OLLAMA_MODELS=""

# Add configuration documentation as comments
# Configuration Options:
# - MILVUS_HOST: Hostname or IP address of the Milvus server (default: "localhost")
# - MILVUS_PORT: Port number of the Milvus server (default: 19530)
# - SERVICE_HOST: Host address to bind the gRPC server (default: "0.0.0.0")
# - SERVICE_PORT: Port to expose the gRPC server (default: 50051)
# - LOG_LEVEL: Logging level (default: "INFO")
# - OLLAMA_HOST: Ollama API host URL (default: empty, e.g. "http://ollama:11434")
# - OLLAMA_MODELS: JSON object mapping languages to Ollama model names (default: empty)
#                  Format: {"en": ["llama2", "nomic-embed-text"], "ru": ["multilingual-model"]}
#                  Models will be automatically downloaded at startup
#
# Available Embedding Models:
# - English (en): 
#   * sentence-transformers/all-MiniLM-L6-v2
#   * OpenAI/text-embedding-ada-002
#   * ollama/nomic-embed-text (when OLLAMA_MODELS is configured)
# - Russian (ru):
#   * sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
#   * ollama/... (when OLLAMA_MODELS is configured)
#
# Note: When using OpenAI models, you'll need to set OPENAI_API_KEY
# ENV OPENAI_API_KEY="your-api-key"

# Modify the service.py to use environment variables
RUN sed -i 's/milvus_host="localhost"/milvus_host=os.environ.get("MILVUS_HOST", "localhost")/g' /app/vectorDB/main.py
RUN sed -i 's/milvus_port=19530/milvus_port=int(os.environ.get("MILVUS_PORT", 19530))/g' /app/vectorDB/main.py
RUN sed -i 's/host="0.0.0.0"/host=os.environ.get("SERVICE_HOST", "0.0.0.0")/g' /app/vectorDB/main.py
RUN sed -i 's/port=50051/port=int(os.environ.get("SERVICE_PORT", 50051))/g' /app/vectorDB/main.py
RUN sed -i 's/level=logging.INFO/level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO"))/g' /app/vectorDB/main.py
RUN sed -i 's/ollama_host=None/ollama_host=os.environ.get("OLLAMA_HOST", "")/g' /app/vectorDB/main.py

# Create requirements.txt if it doesn't exist
RUN if [ ! -f /app/vectorDB/requirements.txt ]; then \
    echo "pymilvus>=2.3.0" > /app/vectorDB/requirements.txt && \
    echo "sentence-transformers>=2.2.2" >> /app/vectorDB/requirements.txt && \
    echo "grpcio>=1.71.0" >> /app/vectorDB/requirements.txt && \
    echo "grpcio-tools>=1.71.0" >> /app/vectorDB/requirements.txt && \
    echo "requests>=2.28.0" >> /app/vectorDB/requirements.txt && \
    echo "numpy>=1.24.0" >> /app/vectorDB/requirements.txt; \
    fi

# Expose the gRPC port
EXPOSE ${SERVICE_PORT}

# Run the service
CMD ["python", "/app/vectorDB/main.py"]

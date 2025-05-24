FROM python:3.9-slim

WORKDIR /app

# Copy proto files and service implementation 
COPY proto/ /app/proto/
COPY llms/ /app/llms/

# Set working directory to the llms service directory
WORKDIR /app/llms

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir openai

# Default environment variables
ENV OLLAMA_HOST="http://ollama:11434"
ENV USE_OLLAMA_FALLBACK="true"
ENV LLM_KEY=""
ENV GRPC_PORT=50052
ENV REQUIRED_OLLAMA_MODELS="llama2:latest,mistral:latest"
ENV AUTO_PULL_OLLAMA_MODELS="true"

# Expose the gRPC port
EXPOSE 50052

# Run the LLM service
CMD python main.py

# ===========================================
# Configuration Options:
# ===========================================
# 
# Environment Variables:
#
# OLLAMA_HOST: URL of the Ollama API server (default: http://ollama:11434)
#   Example: -e OLLAMA_HOST="http://custom-ollama:11434"
#
# USE_OLLAMA_FALLBACK: Whether to use Ollama models as fallback (default: true)
#   Example: -e USE_OLLAMA_FALLBACK="false"
#
# LLM_KEY: API key for LLM provider
#   Example: -e LLM_KEY="your-api-key-here"
#
# GRPC_PORT: Port on which the gRPC service listens (default: 50052)
#   Example: -e GRPC_PORT=8080
#
# REQUIRED_OLLAMA_MODELS: Comma-separated list of Ollama models to ensure are available
#   Example: -e REQUIRED_OLLAMA_MODELS="llama2:latest,mistral:latest,phi3:latest"
#
# AUTO_PULL_OLLAMA_MODELS: Whether to automatically pull missing Ollama models (default: true)
#   Example: -e AUTO_PULL_OLLAMA_MODELS="false"
#
# ===========================================
# Usage Examples:
# ===========================================
#
# Basic usage:
# docker run -p 50052:50052 artificialinsight/llms-service
#
# With custom configuration:
# docker run -p 8080:8080 \
#   -e GRPC_PORT=8080 \
#   -e OLLAMA_HOST="http://custom-ollama:11434" \
#   -e USE_OLLAMA_FALLBACK="true" \
#   -e LLM_KEY="sk-..." \
#   -e REQUIRED_OLLAMA_MODELS="llama2:latest,mistral:latest" \
#   -e AUTO_PULL_OLLAMA_MODELS="true" \
#   artificialinsight/llms-service
#
# ===========================================
# Notes:
# ===========================================
#
# - The service will automatically use Ollama models as fallback if the primary
#   LLM provider is unavailable or if its API key is not configured
#
# - To disable Ollama fallback functionality, set USE_OLLAMA_FALLBACK="false"
#
# - When AUTO_PULL_OLLAMA_MODELS is set to "true", the service will attempt to
#   download missing models listed in REQUIRED_OLLAMA_MODELS
#
# - The service can work with only Ollama (without external API keys) if
#   you have Ollama running and accessible at the OLLAMA_HOST URL
